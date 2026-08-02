"""Cari folder game, siapkan cadangan, tentukan sumber build.

Dipakai oleh gf2_build.py. Semua logika "di mana file game" dan "mana yang boleh
dipakai sebagai sumber" ada di sini supaya gf2_build.py tetap sama persis dengan
build.py milik proyek.

Aturan sumber (ini yang membuat toolkit tahan update game):

  cadangan ada, dan file game == cadangan       -> file game masih Inggris murni
  cadangan ada, dan file game == yang KITA pasang -> bangun ulang dari cadangan
  selain itu                                    -> file game adalah versi Inggris
                                                   yang BARU, jadikan cadangan baru

Memasang dua kali karena itu tidak pernah menerjemahkan hasil terjemahan, dan
setelah game update, file Inggris yang baru otomatis menjadi cadangan yang baru.

Cabang terakhir dijaga PENANDA_ID: kalau file game ternyata sudah berbahasa
Indonesia (mis. pengguna menyalinnya manual, atau berkas penanda terhapus),
menjadikannya cadangan akan merusak tombol "kembalikan" selamanya. Lebih baik
berhenti dan minta pengguna memulihkan bahasa Inggris lebih dulu.
"""
import hashlib
import os
import shutil

NAME = "LangPackageTableCnData.bytes"
EKOR = os.path.join("GF2_Exilium_Data", "LocalCache", "Data", "Table", NAME)

# Frasa yang HANYA ada di berkas hasil terjemahan ini, tidak pernah di versi
# Inggris. Dipakai untuk mengenali berkas yang sudah diterjemahkan.
PENANDA_ID = [
    "medan pertempuran".encode("utf-8"),
    "unit sekutu".encode("utf-8"),
    "giliran berikutnya".encode("utf-8"),
]

TEBAKAN = [
    r"D:\Games\Room\GF2_Exilium",
    r"C:\Program Files\GF2_Exilium",
    r"C:\Program Files (x86)\GF2_Exilium",
    r"D:\GF2_Exilium",
    r"E:\GF2_Exilium",
    r"C:\Games\GF2_Exilium",
    r"D:\Games\GF2_Exilium",
    r"C:\Program Files\Girls' Frontline 2 Exilium",
    r"D:\Girls' Frontline 2 Exilium",
]


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def sudah_indonesia(path):
    """True kalau berkas ini jelas-jelas hasil terjemahan, bukan Inggris asli."""
    sisa = b""
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 22), b""):
            buf = sisa + blk
            for p in PENANDA_ID:
                if p in buf:
                    return True
            sisa = buf[-64:]
    return False


def temukan(kandidat):
    """Terima path apa pun yang masuk akal -> path lengkap ke berkas game.

    Diterima: berkas itu sendiri, folder Table-nya, folder instalasi, atau folder
    di atasnya (beberapa pemasangan menaruh game di subfolder 'Games').
    """
    kandidat = kandidat.strip().strip('"').rstrip("\\/")
    if not kandidat:
        return None
    if os.path.isfile(kandidat) and os.path.basename(kandidat) == NAME:
        return kandidat
    if not os.path.isdir(kandidat):
        return None

    langsung = os.path.join(kandidat, NAME)
    if os.path.isfile(langsung):
        return langsung

    for antara in ("", "Games", "Game"):
        p = os.path.join(kandidat, antara, EKOR) if antara \
            else os.path.join(kandidat, EKOR)
        if os.path.isfile(p):
            return p

    # terakhir: telusuri terbatas 4 tingkat, jangan pernah menyapu seluruh disk
    akar_dalam = kandidat.rstrip("\\/").count(os.sep)
    for dirpath, dirnames, filenames in os.walk(kandidat):
        if dirpath.count(os.sep) - akar_dalam >= 4:
            dirnames[:] = []
            continue
        if NAME in filenames and dirpath.endswith("Table"):
            return os.path.join(dirpath, NAME)
    return None


def cari_game(base):
    """-> path lengkap berkas game. Urutan: gamepath.txt, tebakan, tanya pengguna."""
    simpan = os.path.join(base, "gamepath.txt")
    if os.path.isfile(simpan):
        p = temukan(open(simpan, encoding="utf-8").read())
        if p:
            return p
        print("  ! gamepath.txt tidak sah lagi, mencari ulang...")

    for root in TEBAKAN:
        p = temukan(root)
        if p:
            print(f"  game ditemukan: {p}")
            open(simpan, "w", encoding="utf-8").write(p)
            return p

    print("\n  Folder game tidak ketemu otomatis.")
    print("  Tempelkan path folder instalasi GF2 Exilium (atau berkas")
    print(f"  {NAME} itu sendiri) di bawah ini.")
    print(r"  Contoh: D:\Games\Room\GF2_Exilium")
    print()
    while True:
        try:
            jwb = input("  Path: ")
        except EOFError:
            raise SystemExit("\n  Tidak ada masukan — dibatalkan.")
        if not jwb.strip():
            raise SystemExit("  Dibatalkan.")
        p = temukan(jwb)
        if p:
            open(simpan, "w", encoding="utf-8").write(p)
            print(f"  dipakai: {p}")
            print("  tersimpan di gamepath.txt, lain kali tidak ditanya lagi.")
            return p
        print(f"  ! {NAME} tidak ada di bawah path itu — coba lagi.\n")


def resolve(here):
    """-> (sumber, tujuan, keluaran). Membuat cadangan bila perlu."""
    base = os.path.dirname(here)                 # folder toolkit, bukan tool/
    dest = cari_game(base)

    cad_dir = os.path.join(base, "cadangan")
    os.makedirs(cad_dir, exist_ok=True)
    cad = os.path.join(cad_dir, "LangPackageTableCnData.INGGRIS.bytes")
    stamp = os.path.join(cad_dir, "terpasang.sha1")

    terakhir = ""
    if os.path.isfile(stamp):
        terakhir = open(stamp, encoding="utf-8").read().strip()

    if os.path.isfile(cad):
        h = sha1(dest)
        if h == sha1(cad):
            print("  berkas game masih Inggris murni")
            return cad, dest, os.path.join(base, "LangPackageTableCnData.id.bytes")
        if terakhir and h == terakhir:
            print("  berkas game = hasil pasang sebelumnya, dibangun ulang dari cadangan")
            return cad, dest, os.path.join(base, "LangPackageTableCnData.id.bytes")

    if sudah_indonesia(dest):
        raise SystemExit(
            "\n  BERHENTI — berkas game sudah berbahasa Indonesia, tapi tidak cocok\n"
            "  dengan cadangan mana pun di folder ini.\n\n"
            "  Kalau dijadikan cadangan, tombol 'Kembalikan Bahasa Inggris' tidak akan\n"
            "  pernah bisa mengembalikan bahasa Inggris lagi.\n\n"
            "  Kembalikan dulu berkas Inggris aslinya (verifikasi berkas lewat\n"
            "  launcher, atau salin cadangan lamamu), lalu jalankan ini lagi.")

    shutil.copyfile(dest, cad)
    print(f"  cadangan Inggris disimpan: {cad} ({os.path.getsize(cad):,} bytes)")
    return cad, dest, os.path.join(base, "LangPackageTableCnData.id.bytes")


def tandai(dest, stamp_dir):
    """Catat sidik jari berkas yang baru dipasang, supaya build berikutnya idempoten."""
    open(os.path.join(stamp_dir, "terpasang.sha1"), "w",
         encoding="utf-8").write(sha1(dest))
