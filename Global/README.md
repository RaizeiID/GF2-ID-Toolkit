# GF2-ID Toolkit — Global

Pembaruan **14 Oktober 2026** memuat paket Global Indonesia yang telah disahkan, termasuk Mityl, Koleda, dan perbaikan teks pendukung. Toolkit memperbarui paket utama pada slot Thai, Builtin, dan lima label menu bahasa.

> [!WARNING]
> ❗ Penggunaan bahasa Indonesia melalui perubahan file game termasuk modifikasi. Tetap ada risiko terkena BAN; tidak ada jaminan bebas risiko.

## Memasang melalui BAT

1. Unduh repositori ini melalui **Code → Download ZIP**, lalu ekstrak di luar folder game.
2. Pasang Python 3.10 atau lebih baru dan aktifkan opsi **Add Python to PATH**.
3. Pilih bahasa **Thai/Thailand** di Global, selesaikan unduhan bahasa, lalu tutup game dan launcher.
4. Buka folder `Global`, lalu jalankan **Pasang-Indonesia-Manual.bat**.
5. Tempel lokasi instalasi Global atau folder `GF2_Exilium_Data\LocalCache\Data\Table` saat diminta.
6. Setelah versi dinyatakan cocok, ketik **PASANG**. Tunggu pesan **TERPASANG**, lalu pilih **Bahasa Indonesia** dalam game.

Pemasang memeriksa baseline English/metadata, checksum payload, preimage, struktur paket, backup, dan readback. File baru disiapkan terlebih dahulu; pemasangan memakai penggantian atomik per file dan rollback bila gagal. Game/launcher harus ditutup. Backup tersimpan di `Global/cadangan`.

Untuk mengembalikan file sebelum transaksi, jalankan **Kembalikan-Bahasa-Thailand.bat** dan ketik **PULIHKAN**. Bila game telah update atau file berubah, toolkit berhenti agar backup lama tidak menimpa data baru. Jika yang dipasang sebelumnya adalah mod lama, pemulihan mengembalikan mod lama tersebut sesuai backup.

## Pilihan metode timpa

- [**Repositori file .bytes Global**](https://github.com/RaizeiID/GFL2-Bahasa-Indonesia-Global-)
- [**Unduh LangPackageTableThthData.bytes**](https://raw.githubusercontent.com/RaizeiID/GFL2-Bahasa-Indonesia-Global-/refs/heads/main/LangPackageTableThthData.bytes)

Metode timpa pada tautan tersebut menggunakan satu file utama; ikuti README repositorinya. Metode BAT di sini memasang tujuh file sehingga Builtin dan label bahasa ikut diperbarui.

## Kecocokan versi

Rilis ini diverifikasi pada **Global PC Windows/Steam**, dengan paket utama 430.226 slot / 46.780 chunk. Nama resmi tetap mengikuti keputusan terjemahan sebelumnya. Angka tersebut adalah struktur paket, bukan klaim seluruh konten 100% Indonesia atau bukti semua tampilan telah diuji.

Toolkit memakai `rilis-global.json` untuk memeriksa baseline. Setelah update game, jangan menganggap rilis lama otomatis cocok: bila pemeriksaan gagal, gunakan pembaruan toolkit yang telah direbase. Tidak ada terjemahan baru yang ditebak saat instalasi.
