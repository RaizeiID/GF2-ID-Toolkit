"""Kembalikan file game ke bahasa Inggris aslinya dari cadangan."""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import setup_paths

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)

cad = os.path.join(BASE, "cadangan", "LangPackageTableCnData.INGGRIS.bytes")
if not os.path.isfile(cad):
    raise SystemExit(
        "  Tidak ada cadangan di folder 'cadangan'.\n"
        "  Berarti terjemahan belum pernah dipasang dari folder ini.\n"
        "  Cara lain mengembalikan bahasa Inggris: verifikasi/perbaiki file game\n"
        "  lewat launcher, atau pasang ulang game.")

dest = setup_paths.cari_game(BASE)

shutil.copyfile(cad, dest)
stamp = os.path.join(BASE, "cadangan", "terpasang.sha1")
if os.path.isfile(stamp):
    os.remove(stamp)
print(f"  Dikembalikan ke bahasa Inggris -> {dest}")
print(f"  ({os.path.getsize(dest):,} bytes)")
