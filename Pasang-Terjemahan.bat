@echo off
setlocal
title Terjemahan Indonesia - GF2 Exilium
cd /d "%~dp0"

echo.
echo   ============================================
echo    Terjemahan Bahasa Indonesia - GF2 Exilium
echo   ============================================
echo.

set "PY="
where py >nul 2>nul
if %errorlevel%==0 set "PY=py -3"
if defined PY goto run
where python >nul 2>nul
if %errorlevel%==0 set "PY=python"
if defined PY goto run
goto nopy

:run
%PY% "tool\gf2_build.py"
if errorlevel 1 goto gagal
echo.
echo   Tekan tombol apa saja untuk menutup.
pause >nul
exit /b 0

:nopy
echo   Python tidak ditemukan di komputer ini.
echo.
echo   Ada dua pilihan:
echo.
echo     1. Pasang Python dari  https://www.python.org/downloads/
echo        Saat memasang, CENTANG "Add python.exe to PATH".
echo        Lalu jalankan lagi berkas ini.
echo.
echo     2. Atau pakai  Pasang-Cepat-Tanpa-Python.bat  (kalau tersedia),
echo        yang memasang berkas jadi tanpa membangun ulang.
echo.
pause
exit /b 1

:gagal
echo.
echo   GAGAL - tidak ada yang diubah pada berkas game.
echo   Salin pesan merah di atas kalau ingin melaporkan masalah.
echo.
pause
exit /b 1
