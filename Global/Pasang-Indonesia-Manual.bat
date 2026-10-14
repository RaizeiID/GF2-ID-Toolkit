@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 goto :use_py
where python >nul 2>nul
if not errorlevel 1 goto :use_python
echo Python tidak ditemukan. Pasang Python 3.10+ dan aktifkan Add Python to PATH.
pause
exit /b 1
:use_py
py -3 "%~dp0tool\install_global.py" install %*
goto :finished
:use_python
python "%~dp0tool\install_global.py" install %*
:finished
set "RESULT=%ERRORLEVEL%"
echo.
pause
exit /b %RESULT%
