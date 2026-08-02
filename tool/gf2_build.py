"""Build an Indonesian LangPackageTableCnData.bytes from the pristine backup.

Always rebuilds from LangPackageTableCnData.ORIGINAL.bytes, so it is idempotent:
re-running never double-translates and never compounds errors.

Glossary files: glossary/*.tsv   ->  <english>\t<indonesian>
  - lines starting with '#' are comments
  - a line '#range <lo> <hi>' limits that file to string-ids in [lo, hi)
  - \n in a cell means a real newline
Matching is exact, on the whole string (never substring), so placeholders
like {0} and <color=...> tags can only survive if you copy them verbatim.

Usage:  python build.py            # build + validate, write to the game
        python build.py --dry-run  # build + validate, write nothing
"""
import os, sys, glob, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from langpack import LangPack, newest_baseline

HERE = os.path.dirname(os.path.abspath(__file__))
# Baseline = the pristine English file for the CURRENT game version. The 2026-07-29
# update reshuffled every string id, so an older baseline would rebuild stale text.
# The highest ORIGINAL_v<N> wins (see langpack.newest_baseline). Keep the older
# baselines around; they cost nothing and document past versions.
import setup_paths
ORIG, DEST, OUT = setup_paths.resolve(HERE)
CAD_DIR = os.path.dirname(ORIG)


def unescape(s):
    r"""Decode a glossary TSV field.

    \n  -> a real newline (game strings that genuinely wrap)
    \\n -> the two characters backslash+n, which some game strings carry
           literally and the engine renders as a break (character bios do this)
    Any other backslash is left alone, so ordinary text needs no escaping.
    """
    out = []
    i, n = 0, len(s)
    while i < n:
        if s[i] == "\\" and i + 1 < n:
            nxt = s[i + 1]
            if nxt == "n":
                out.append("\n")
                i += 2
                continue
            if nxt == "\\":
                out.append("\\")
                i += 2
                continue
        out.append(s[i])
        i += 1
    return "".join(out)


def load_glossaries():
    """-> list of (lo, hi, {src: dst}, label), one entry per #range SECTION.

    #range is positional: it applies to the rows that follow it, until the next
    #range in the same file. It used to be file-global (last one wins), which made
    a second #range silently kill every row above it -- rows that checksrc still
    reported as fine, because their text does exist. One section per range keeps
    what the file looks like and what the build does in agreement.
    """
    sets = []
    for path in sorted(glob.glob(os.path.join(HERE, "glossary", "*.tsv"))):
        name = os.path.basename(path)
        lo, hi = 0, 10 ** 9
        table = {}

        def flush():
            if table:
                sets.append((lo, hi, dict(table), name))
                table.clear()

        with open(path, encoding="utf-8-sig") as f:   # tolerate a BOM
            for ln, line in enumerate(f, 1):
                line = line.rstrip("\n").rstrip("\r")
                if not line.strip():
                    continue
                if line.startswith("#"):
                    if line.startswith("#range"):
                        flush()
                        _, a, b = line.split()
                        lo, hi = int(a), int(b)
                    continue
                if "\t" not in line:
                    raise SystemExit(f"{name}:{ln}: no TAB separator")
                src, dst = line.split("\t", 1)
                src = unescape(src)
                dst = unescape(dst)
                if src in table and table[src] != dst:
                    raise SystemExit(f"{name}:{ln}: conflicting entry for {src!r}")
                table[src] = dst
        flush()
    return sets


def load_rules(subdir="rules"):
    """<subdir>/*.tsv -> list of (lo, hi, compiled_regex, replacement, name, raw)"""
    import re
    out = []
    for path in sorted(glob.glob(os.path.join(HERE, subdir, "*.tsv"))):
        lo, hi = 0, 10 ** 9
        with open(path, encoding="utf-8-sig") as f:
            for ln, line in enumerate(f, 1):
                line = line.rstrip("\n").rstrip("\r")
                if not line.strip():
                    continue
                if line.startswith("#"):
                    if line.startswith("#range"):
                        _, a, b = line.split()
                        lo, hi = int(a), int(b)
                    continue
                if "\t" not in line:
                    raise SystemExit(f"{os.path.basename(path)}:{ln}: no TAB separator")
                pat, rep = line.split("\t", 1)
                if pat.startswith("="):
                    # Literal mode: paste the sentence verbatim, no regex escaping and
                    # no backslash interpretation -- some game strings contain a literal
                    # two-character "\n" that the engine renders as a break, and a
                    # segment can never hold a real newline (that is a separator).
                    pat = re.escape(pat[1:])
                    rep = rep.replace("\\", "\\\\")
                try:
                    rx = re.compile(pat)
                except re.error as e:
                    raise SystemExit(f"{os.path.basename(path)}:{ln}: bad regex: {e}")
                out.append((lo, hi, rx, rep, f"{os.path.basename(path)}:{ln}", pat))
    return out


SEG_SPLIT = None


def translate_segments(s, sid, segs, stat):
    """Split a description into sentences and translate each one.

    All-or-nothing: returns None unless EVERY sentence matched a rule, so a
    tooltip is never left half Indonesian and half English.
    """
    global SEG_SPLIT
    import re
    if SEG_SPLIT is None:
        # split after a full stop followed by space, or on line breaks;
        # the separator is captured so it can be put back verbatim
        SEG_SPLIT = re.compile(r'((?<=\.)[ \t]+|[\r\n]+)')
    parts = SEG_SPLIT.split(s)           # a single sentence is just a 1-part split
    out = []
    used = []                            # only credited if the whole string succeeds
    for i, part in enumerate(parts):
        if i % 2 or not part.strip():    # separator, or blank -> keep verbatim
            out.append(part)
            continue
        # a sentence often carries stray padding (e.g. a space before a newline);
        # match on the trimmed core and put the padding back untouched
        core = part.strip()
        lead = part[:len(part) - len(part.lstrip())]
        trail = part[len(part.rstrip()):]
        for lo, hi, rx, rep, name, raw in segs:
            if not (lo <= sid < hi):
                continue
            m = rx.fullmatch(core)
            if m:
                out.append(lead + m.expand(rep) + trail)
                used.append(name)
                break
        else:
            return None                  # one unknown sentence -> skip the whole thing
    for name in used:
        stat[name] += 1
    return "".join(out)


TOKEN_RX = None


def tokens_of(s):
    """Placeholders, markup tags and numbers that MUST survive translation."""
    global TOKEN_RX
    import re
    if TOKEN_RX is None:
        # numbers must not swallow trailing punctuation: "ke-8," is still the number 8,
        # so require a digit at both ends (or a lone digit) -- keeps "19,200" and "0.6"
        TOKEN_RX = re.compile(r"\{[^{}]*\}|\[VAL\d+\]|<[^<>]+>|\d[\d,.]*\d|\d")
    return sorted(TOKEN_RX.findall(s))


def check_placeholders(sets):
    """A translation must keep every {n}, [VALn] and <tag> from the source."""
    import re
    tok = re.compile(r"\{[^{}]*\}|\[VAL\d+\]|<[^<>]+>")
    bad = []
    for _, _, table, name in sets:
        for src, dst in table.items():
            a, b = sorted(tok.findall(src)), sorted(tok.findall(dst))
            if a != b:
                bad.append((name, src, dst, a, b))
    return bad


def main():
    dry = "--dry-run" in sys.argv
    sets = load_glossaries()
    total_terms = sum(len(t) for _, _, t, _ in sets)
    for lo, hi, t, name in sets:
        print(f"  glossary {name:<24} {len(t):>6} terms   range [{lo}, {hi})")
    print(f"  total: {total_terms} terms")

    bad = check_placeholders(sets)
    if bad:
        print("\n!! placeholder mismatch — refusing to build:")
        for name, src, dst, a, b in bad[:20]:
            print(f"   {name}: {src!r} -> {dst!r}\n       src{a} vs dst{b}")
        sys.exit(1)

    rules = load_rules()
    segs = load_rules("segments")
    if rules:
        print(f"  regex rules: {len(rules)}")
    if segs:
        print(f"  sentence rules: {len(segs)}")

    lp = LangPack(ORIG)

    hits = collections.Counter()
    rule_hits = collections.Counter()
    seg_hits = collections.Counter()
    rule_example = {}
    seg_example = []
    seg_desc = 0
    changed_entries = 0
    # Menyusuri ~454.000 string dengan belasan ribu aturan makan beberapa menit.
    # Tanpa tanda apa pun di layar, jendela yang diam terlihat seperti macet --
    # pemakai toolkit menutupnya sebelum selesai. Jadi laporkan kemajuannya.
    total_chunks = len(lp.chunks)
    langkah = max(1, total_chunks // 50)
    print(f"\n  menerjemahkan {total_chunks:,} chunk — perlu beberapa menit,")
    print("  JANGAN tutup jendela ini sampai muncul kata TERPASANG/installed.")
    for n, (cid, ents) in enumerate(lp.chunks.items(), 1):
        if n % langkah == 0 or n == total_chunks:
            sys.stdout.write(f"\r  {n * 100 // total_chunks:3d}%  "
                             f"({n:,}/{total_chunks:,})")
            sys.stdout.flush()
        new = []
        for sid, txt in ents:
            if txt:
                s = txt.decode("utf-8")
                d = None
                for lo, hi, table, _ in sets:              # exact match wins
                    if lo <= sid < hi and s in table:
                        d = table[s]
                        if d != s:
                            hits[s] += 1
                        break
                if d is None:                              # then regex rules
                    for lo, hi, rx, rep, name, raw in rules:
                        if not (lo <= sid < hi):
                            continue
                        m = rx.fullmatch(s)
                        if not m:
                            continue
                        cand = m.expand(rep)
                        if tokens_of(cand) != tokens_of(s):
                            raise SystemExit(
                                f"\n!! rule {name} loses a number/placeholder:\n"
                                f"   {raw}\n   {s!r}\n-> {cand!r}\n"
                                f"   src{tokens_of(s)} vs dst{tokens_of(cand)}")
                        d = cand
                        rule_hits[name] += 1
                        rule_example.setdefault(name, (s, cand))
                        break
                if d is None and segs:                     # then sentence-by-sentence
                    cand = translate_segments(s, sid, segs, seg_hits)
                    if cand is not None and cand != s:
                        if tokens_of(cand) != tokens_of(s):
                            raise SystemExit(
                                f"\n!! segment engine loses a number/placeholder:\n"
                                f"   {s!r}\n-> {cand!r}\n"
                                f"   src{tokens_of(s)} vs dst{tokens_of(cand)}")
                        d = cand
                        seg_desc += 1
                        if len(seg_example) < 3:
                            seg_example.append((s, cand))
                if d is not None and d != s:
                    txt = d.encode("utf-8")
                    changed_entries += 1
            new.append((sid, txt))
        lp.chunks[cid] = new

    print(f"\n\n  translated entries: {changed_entries:,}"
          f"  (glossary {sum(hits.values()):,} + rules {sum(rule_hits.values()):,}"
          f" + multi-sentence {seg_desc:,})")
    print(f"  distinct terms used: {len(hits):,} / {total_terms}")
    unused = [s for _, _, t, _ in sets for s in t if s not in hits]
    if unused:
        print(f"  terms that matched nothing ({len(unused)}): "
              + ", ".join(repr(u[:30]) for u in unused[:12]))
    if rules:
        dead = [n for _, _, _, _, n, _ in rules if n not in rule_hits]
        print(f"  rules that fired: {len(rule_hits)}/{len(rules)}"
              + (f"  | never matched: {', '.join(dead)}" if dead else ""))
        for name, c in rule_hits.most_common(5):
            a, b = rule_example[name]
            print(f"     {c:>5}x  {a!r}\n            -> {b!r}")
    if segs:
        dead = [raw for _, _, _, _, n, raw in segs if n not in seg_hits]
        print(f"  sentence rules that fired: {len(seg_hits)}/{len(segs)}"
              + (f"  | never matched: {len(dead)}" if dead else ""))
        for raw in dead[:40]:
            print(f"       dead: {raw[:96]}")
        for a, b in seg_example[:2]:
            print(f"     {a[:110]!r}\n       -> {b[:110]!r}")

    lp.save(OUT)
    print(f"\n  wrote {OUT} ({os.path.getsize(OUT):,} bytes)")

    if not validate(ORIG, OUT):
        sys.exit(1)

    if dry:
        print("  --dry-run: game file left untouched")
        return
    import shutil
    shutil.copyfile(OUT, DEST)
    setup_paths.tandai(DEST, CAD_DIR)
    print(f"  TERPASANG -> {DEST}")
    print("\n  Selesai. Jalankan game seperti biasa.")


def validate(orig_path, new_path):
    """Structural equivalence: same chunks, same string-ids, decodable, gapless."""
    print("\n  validating...")
    a, b = LangPack(orig_path), LangPack(new_path)
    ok = True

    def chk(cond, msg):
        nonlocal ok
        print(("   OK   " if cond else "   FAIL ") + msg)
        ok = ok and cond

    chk(a.f1 == b.f1 and a.f2 == b.f2, f"header fields preserved ({b.f1}, {b.f2})")
    chk([r[0] for r in a.refs] == [r[0] for r in b.refs],
        f"chunk ids and order preserved ({len(b.refs):,} chunks)")

    sa = [(s, len(t)) for c in a.refs for s, t in a.chunks[c[0]]]
    sb = [(s, len(t)) for c in b.refs for s, t in b.chunks[c[0]]]
    chk([x[0] for x in sa] == [x[0] for x in sb],
        f"string ids and order preserved ({len(sb):,} strings)")

    # index must exactly describe the body: gapless, no overlap, covers all
    pairs = sorted((o, l) for _, o, l in b.refs)
    cur = 0; gap = 0
    for o, l in pairs:
        if o != cur:
            gap += 1
        cur = max(cur, o + l)
    body = os.path.getsize(new_path) - b.body_start
    chk(gap == 0 and cur == body, f"offset index gapless and covers body ({body:,} bytes)")

    dec = True
    for c in b.refs:
        for _, t in b.chunks[c[0]]:
            try:
                t.decode("utf-8")
            except UnicodeDecodeError:
                dec = False
                break
    chk(dec, "all strings valid UTF-8")

    # A greedy regex can eat past a clause boundary and emit half-translated text.
    # The number/markup checks CANNOT see that -- every token survives, only the
    # language breaks -- so look for English mechanic phrases left inside a
    # string we claim to have translated.
    import re
    LEFTOVER = re.compile(r"\b(?:is increased by|is reduced by|damage dealt to"
                          r"|will be converted into|per turn|of the target)\b")
    sa = {s: t for c in a.refs for s, t in a.chunks[c[0]]}
    mixed = []
    for c in b.refs:
        for s, t in b.chunks[c[0]]:
            if t != sa.get(s) and LEFTOVER.search(t.decode("utf-8", "replace")):
                mixed.append((s, sa[s].decode("utf-8", "replace")))
    chk(not mixed, f"no half-translated strings ({len(mixed)} suspect)")
    for sid, src in mixed[:3]:
        print(f"        id {sid}: {src[:110]}")
    return ok


if __name__ == "__main__":
    main()
