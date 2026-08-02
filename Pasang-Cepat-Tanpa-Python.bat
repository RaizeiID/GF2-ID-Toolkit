@echo off
setlocal
title Pasang Cepat (tanpa Python) - GF2 Exilium
cd /d "%~dp0"

echo.
echo   ==========================================================
echo    Pasang Cepat - memakai berkas jadi di folder "siap-pakai"
echo   ==========================================================
echo.
echo   PERHATIAN: berkas jadi ini terikat pada SATU versi game.
echo   Kalau game sudah diperbarui sejak rilis ini dibuat, pakai
echo   Pasang-Terjemahan.bat (butuh Python) supaya dibangun ulang
echo   dari berkas game milikmu sendiri.
echo.

if not exist "siap-pakai\LangPackageTableCnData.bytes" goto nofile

rem gamepath.txt menyimpan path LENGKAP ke berkasnya, sama seperti jalur Python
set "TGT="
if exist "gamepath.txt" set /p TGT=<gamepath.txt
if defined TGT if exist "%TGT%" goto punya
set "TGT="

rem Sebagian pemasangan menaruh game di subfolder "Games", sebagian tidak.
set "EKOR=GF2_Exilium_Data\LocalCache\Data\Table\LangPackageTableCnData.bytes"
for %%D in (
  "D:\Games\Room\GF2_Exilium"
  "C:\Program Files\GF2_Exilium"
  "C:\Program Files (x86)\GF2_Exilium"
  "D:\GF2_Exilium"
  "E:\GF2_Exilium"
  "C:\Games\GF2_Exilium"
  "D:\Games\GF2_Exilium"
) do (
  if not defined TGT if exist "%%~D\%EKOR%" set "TGT=%%~D\%EKOR%"
  if not defined TGT if exist "%%~D\Games\%EKOR%" set "TGT=%%~D\Games\%EKOR%"
)
if defined TGT goto simpan

echo   Folder game tidak ketemu otomatis.
echo   Tempelkan path folder instalasi GF2 Exilium.
echo   Contoh: D:\Games\Room\GF2_Exilium
echo.
set "ROOT="
set /p ROOT=  Path:
set ROOT=%ROOT:"=%
if exist "%ROOT%\%EKOR%" set "TGT=%ROOT%\%EKOR%"
if not defined TGT if exist "%ROOT%\Games\%EKOR%" set "TGT=%ROOT%\Games\%EKOR%"
if not defined TGT goto salah

:simpan
echo|set /p="%TGT%">gamepath.txt

:punya
echo   Berkas game : %TGT%
echo.

if not exist "cadangan" mkdir "cadangan"
if exist "cadangan\LangPackageTableCnData.INGGRIS.bytes" goto adacad
copy /y "%TGT%" "cadangan\LangPackageTableCnData.INGGRIS.bytes" >nul
if errorlevel 1 goto gagal
echo   Cadangan bahasa Inggris disimpan di folder "cadangan".
goto pasang

:adacad
echo   Cadangan bahasa Inggris sudah ada, tidak ditimpa.

:pasang
copy /y "siap-pakai\LangPackageTableCnData.bytes" "%TGT%" >nul
if errorlevel 1 goto gagal
echo   TERPASANG. Jalankan game seperti biasa.
echo.
echo   Untuk membatalkan: Kembalikan-Bahasa-Inggris.bat
goto akhir

:nofile
echo   Folder "siap-pakai" kosong pada rilis ini.
echo   Pakai Pasang-Terjemahan.bat (butuh Python).
goto akhir

:salah
echo   Di path itu tidak ada %EKOR%
goto akhir

:gagal
echo   GAGAL menyalin. Tutup game lebih dulu, lalu coba lagi.

:akhir
echo.
pause
exit /b 0
