@echo off
setlocal
title Kembalikan Bahasa Inggris - GF2 Exilium
cd /d "%~dp0"

echo.
echo   Ini akan mengembalikan berkas game ke bahasa Inggris aslinya
echo   dari cadangan di folder "cadangan".
echo.
set "JWB="
set /p JWB=  Lanjutkan? (y/n):
if /i not "%JWB%"=="y" goto batal

set "PY="
where py >nul 2>nul
if %errorlevel%==0 set "PY=py -3"
if defined PY goto run
where python >nul 2>nul
if %errorlevel%==0 set "PY=python"
if defined PY goto run

rem Tanpa Python: salin langsung dari cadangan, baca tujuan dari gamepath.txt
if not exist "cadangan\LangPackageTableCnData.INGGRIS.bytes" goto nocad
if not exist "gamepath.txt" goto nopath
set "TGT="
set /p TGT=<gamepath.txt
if not exist "%TGT%" goto nopath
copy /y "cadangan\LangPackageTableCnData.INGGRIS.bytes" "%TGT%" >nul
if errorlevel 1 goto gagal
if exist "cadangan\terpasang.sha1" del "cadangan\terpasang.sha1"
echo   Dikembalikan ke bahasa Inggris.
goto akhir

:run
%PY% "tool\restore.py"
if errorlevel 1 goto gagal
goto akhir

:nocad
echo   Tidak ada cadangan - terjemahan belum pernah dipasang dari folder ini.
goto akhir

:nopath
echo   gamepath.txt tidak ada dan Python tidak terpasang,
echo   jadi lokasi game tidak bisa ditentukan.
goto akhir

:batal
echo   Dibatalkan.
goto akhir

:gagal
echo   GAGAL menyalin. Tutup game lebih dulu, lalu coba lagi.

:akhir
echo.
pause
exit /b 0
