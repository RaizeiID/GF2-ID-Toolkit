# Terjemahan Bahasa Indonesia — Girls' Frontline 2: Exilium

Alih bahasa tidak resmi untuk GF2: Exilium. **Bukan mod, bukan injeksi, bukan
DLL** — hanya satu berkas data (tabel teks) yang diganti isinya.

## Pasang — pilih salah satu

### Cara 1 — Instan (paling banyak dipakai)

Unduh `LangPackageTableCnData.bytes` dari [**Releases**](../../releases), lalu
**timpa** berkas dengan nama sama di:

```
<folder game>\GF2_Exilium_Data\LocalCache\Data\Table\
```

Selesai. Tutup game dulu, dan **salin berkas aslimu ke tempat aman lebih dulu**
supaya bisa dikembalikan.

Berkas ini dibangun dari berkas game versi **29 Juli 2026**. Kalau versi game-mu
lebih baru, pakai Cara 2 — hasilnya menyesuaikan sendiri.

> Ada juga `Pasang-Cepat-Tanpa-Python.bat` yang melakukan hal yang sama tapi
> otomatis: mencari folder game, mencadangkan berkas aslimu, lalu menimpa.

### Cara 2 — Bangun dari berkasmu sendiri

1. Unduh repo ini (**Code → Download ZIP**), ekstrak **di luar folder game**.
2. Tutup game.
3. Klik dua kali **`Pasang-Terjemahan.bat`**.

Butuh [Python](https://www.python.org/downloads/) — saat memasang, centang
**"Add python.exe to PATH"**.

> ⏱ **Butuh sekitar 10–15 menit.** Ada persentase kemajuan di layar. Jangan tutup
> jendelanya sampai muncul kata **TERPASANG** — kalau ditutup di tengah jalan,
> berkas game tidak berubah sama sekali (aman, tapi harus diulang).

Lebih lambat, tapi **tahan update game**: hasilnya tetap benar walau versi
game-mu berbeda dari versi rilis ini.

Membatalkan (kedua cara): **`Kembalikan-Bahasa-Inggris.bat`**, atau kembalikan
sendiri salinan berkas aslimu.

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
