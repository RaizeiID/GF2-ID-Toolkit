# Terjemahan Bahasa Indonesia — Girls' Frontline 2: Exilium

Alih bahasa tidak resmi untuk GF2: Exilium. **Bukan mod, bukan injeksi, bukan
DLL** — hanya satu berkas data (tabel teks) yang diganti isinya.

## Pasang

1. Unduh repo ini (**Code → Download ZIP**), ekstrak ke mana saja **di luar
   folder game**.
2. Tutup game.
3. Klik dua kali **`Pasang-Terjemahan.bat`**.

> ⏱ **Butuh sekitar 10–15 menit.** Ada persentase kemajuan di layar. Jangan tutup
> jendelanya sampai muncul kata **TERPASANG** — kalau ditutup di tengah jalan,
> berkas game tidak berubah sama sekali (aman, tapi harus diulang).

Butuh [Python](https://www.python.org/downloads/) — saat memasang, centang
**"Add python.exe to PATH"**.

Membatalkan: **`Kembalikan-Bahasa-Inggris.bat`**.

> Tanpa Python? Ada `Pasang-Cepat-Tanpa-Python.bat` yang memakai berkas jadi dari
> [Releases](../../releases). Berkas jadi terikat pada satu versi game — kalau
> game-mu lebih baru, pakai cara utama di atas.

## Kenapa membangun ulang, bukan sekadar menimpa berkas jadi

Terjemahan disimpan sebagai pasangan **teks Inggris → teks Indonesia**, bukan
`id → teks`. Ini penting karena setiap update GF2 mengacak seluruh string id:
pada lompatan versi 8 Mei → 29 Juli 2026, hanya **46 dari 391.275 id** yang
isinya tetap sama (0,01%) — tapi **91,5% teks unik bertahan**.

Artinya, membangun dari berkas game **milikmu sendiri** tetap menghasilkan
terjemahan yang benar walau versimu berbeda dari versi saat rilis ini dibuat.
Berkas jadi tidak punya sifat itu sama sekali.

## Apa yang terjadi saat memasang

1. Berkas Inggris aslimu disalin ke `cadangan/` (sekali saja, tidak pernah
   ditimpa).
2. Berkas baru dibangun dari cadangan itu + data terjemahan.
3. Strukturnya diverifikasi: jumlah chunk, seluruh string id dan urutannya,
   indeks offset yang rapat tanpa celah, UTF-8, dan tidak ada string yang
   setengah diterjemahkan. **Satu saja gagal → berhenti, berkas game tidak
   disentuh.**
4. Barulah berkas game diganti.

Build bersifat idempoten: sumbernya selalu cadangan Inggris, tidak pernah hasil
terjemahan. Menjalankannya dua kali aman.

**Setelah game update:** jalankan lagi `Pasang-Terjemahan.bat`. Ia mengenali
bahwa berkas game sudah berganti, menjadikannya cadangan baru, lalu membangun
ulang. Tidak perlu menghapus apa pun.

## Cakupan

| Bagian | |
|---|---|
| Bio & kutipan karakter | 100% |
| Panduan build | 100% |
| Deskripsi skill (karakter, musuh, HOC, summon) | ~100% |
| Deskripsi item | 52% |
| Antarmuka (UI) | 50% |
| Cerita | 6% |

Nama diri **sengaja tetap bahasa Inggris**: nama karakter, nama skill, nama
buff/debuff, dan istilah tempur (Attack, Defense, Stability, Critical Rate,
Cover, Confectance Index, dll.). Ini pilihan gaya supaya cocok dengan panduan,
video, dan obrolan komunitas.

Cacat pada teks sumber (salah ketik, kata terduplikasi, markup rusak, spasi
hilang) disalin apa adanya dan didokumentasikan di kepala setiap berkas `.tsv`
yang bersangkutan.

## Struktur

```
Pasang-Terjemahan.bat            pemasang utama
Pasang-Cepat-Tanpa-Python.bat    pemasang berkas jadi
Kembalikan-Bahasa-Inggris.bat    pembatal
tool/glossary/                   pencocokan string utuh
tool/rules/                      pola regex
tool/segments/                   pencocokan per kalimat
tool/gf2_build.py                pembangun + pemvalidasi
tool/setup_paths.py              deteksi game, cadangan, pemilihan sumber
cadangan/                        berkas Inggris ASLIMU — jangan dihapus
```

`cadangan/`, `gamepath.txt`, dan berkas hasil build tidak masuk repo.

## Peringatan

Mengubah berkas game dapat melanggar ketentuan layanan penerbit. Risiko ada pada
penggunanya. Proyek ini tidak berafiliasi dengan Sunborn/Darkwinter.
