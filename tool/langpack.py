"""Reader/writer for GF2 Exilium LangPackageTable*Data.bytes

Layout:
  uint32_le  header_len
  bytes      header   (protobuf: 1=varint, 2=varint, 3=repeated ChunkRef)
                      ChunkRef { 1: chunk_id, 2: Loc { 1: offset, 2: length } }
  bytes      body     (chunks concatenated, gapless, in offset order)

  chunk (protobuf): repeated field 1 = Entry { 1: string_id, 2: text }
"""
import glob
import os
import re
import struct

BASE_GLOB = "LangPackageTableCnData.ORIGINAL*.bytes"


def newest_baseline(folder=None):
    """Pick the pristine English baseline for the CURRENT game version.

    Chosen by the _v<N> suffix, not by file time: dropping an OLD dump into the
    folder gives it a fresh mtime and would otherwise silently become 'newest',
    rebuilding the whole translation against stale text. Plain ORIGINAL = v1.
    """
    folder = folder or os.path.dirname(os.path.abspath(__file__))
    best, best_n = None, -1
    for p in glob.glob(os.path.join(folder, BASE_GLOB)):
        m = re.search(r"ORIGINAL_v(\d+)\.bytes$", p)
        n = int(m.group(1)) if m else 1
        if n > best_n:
            best, best_n = p, n
    return best


def rvarint(b, i):
    r = 0; s = 0
    while True:
        c = b[i]; i += 1
        r |= (c & 0x7F) << s
        if not (c & 0x80):
            return r, i
        s += 7


def wvarint(v):
    out = bytearray()
    while True:
        c = v & 0x7F
        v >>= 7
        if v:
            out.append(c | 0x80)
        else:
            out.append(c)
            return bytes(out)


def parse_chunk(blob):
    """-> list of (string_id, text_bytes)"""
    out = []
    i = 0
    while i < len(blob):
        key, i = rvarint(blob, i)
        assert key == 0x0A, (key, i)          # field 1, LEN
        ln, i = rvarint(blob, i)
        sub = blob[i:i + ln]; i += ln
        j = 0; sid = 0; txt = b''
        while j < len(sub):
            k2, j = rvarint(sub, j)
            fn, wt = k2 >> 3, k2 & 7
            if wt == 0:
                v, j = rvarint(sub, j)
                assert fn == 1, fn
                sid = v
            else:
                assert wt == 2 and fn == 2, (fn, wt)
                l2, j = rvarint(sub, j)
                txt = sub[j:j + l2]; j += l2
        out.append((sid, txt))
    return out


def build_chunk(entries):
    """entries: list of (string_id, text_bytes) -> chunk bytes"""
    out = bytearray()
    for sid, txt in entries:
        inner = b'\x08' + wvarint(sid)
        if txt:                                # empty text: field 2 omitted, as in source
            inner += b'\x12' + wvarint(len(txt)) + txt
        out += b'\x0A' + wvarint(len(inner)) + inner
    return bytes(out)


class LangPack:
    def __init__(self, path):
        raw = open(path, 'rb').read()
        hdr_len = struct.unpack_from('<I', raw, 0)[0]
        hdr = raw[4:4 + hdr_len]
        self.body_start = 4 + hdr_len
        body = raw[self.body_start:]

        self.f1 = None
        self.f2 = None
        self.refs = []           # list of [chunk_id, offset, length] in header order
        i = 0
        while i < len(hdr):
            key, i = rvarint(hdr, i)
            fn, wt = key >> 3, key & 7
            if wt == 0:
                v, i = rvarint(hdr, i)
                if fn == 1: self.f1 = v
                elif fn == 2: self.f2 = v
                else: raise ValueError(f'hdr field {fn}')
                continue
            assert wt == 2 and fn == 3, (fn, wt)
            ln, i = rvarint(hdr, i)
            sub = hdr[i:i + ln]; i += ln
            j = 0; cid = 0; off = 0; length = 0
            while j < len(sub):
                k2, j = rvarint(sub, j)
                f2, w2 = k2 >> 3, k2 & 7
                if w2 == 0:
                    v, j = rvarint(sub, j)
                    assert f2 == 1, f2
                    cid = v
                else:
                    l2, j = rvarint(sub, j)
                    s2 = sub[j:j + l2]; j += l2
                    m = 0
                    while m < len(s2):
                        k3, m = rvarint(s2, m)
                        f3, w3 = k3 >> 3, k3 & 7
                        assert w3 == 0, w3
                        v3, m = rvarint(s2, m)
                        if f3 == 1: off = v3
                        elif f3 == 2: length = v3
                        else: raise ValueError(f'loc field {f3}')
            self.refs.append([cid, off, length])

        # chunk_id -> entries, keeping body order for rebuild
        self.body_order = sorted(range(len(self.refs)), key=lambda k: self.refs[k][1])
        self.chunks = {}
        for k in range(len(self.refs)):
            cid, off, ln = self.refs[k]
            self.chunks[cid] = parse_chunk(body[off:off + ln])

    # ---------- writing ----------
    @staticmethod
    def _enc_ref(cid, off, length):
        loc = b''
        if off:    loc += b'\x08' + wvarint(off)
        if length: loc += b'\x10' + wvarint(length)
        sub = b'\x08' + wvarint(cid) + b'\x12' + wvarint(len(loc)) + loc
        return b'\x1A' + wvarint(len(sub)) + sub

    def save(self, path):
        blobs = {cid: build_chunk(ents) for cid, ents in self.chunks.items()}
        body = bytearray()
        locs = {}
        for k in self.body_order:
            cid = self.refs[k][0]
            b = blobs[cid]
            locs[cid] = (len(body), len(b))
            body += b

        hdr = bytearray()
        if self.f1 is not None: hdr += b'\x08' + wvarint(self.f1)
        if self.f2 is not None: hdr += b'\x10' + wvarint(self.f2)
        for cid, _, _ in self.refs:
            o, l = locs[cid]
            hdr += self._enc_ref(cid, o, l)

        with open(path, 'wb') as f:
            f.write(struct.pack('<I', len(hdr)))
            f.write(hdr)
            f.write(body)
