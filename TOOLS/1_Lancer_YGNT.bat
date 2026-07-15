@echo off
setlocal
title YGNT Manager - Lancement

call "%~dp0_common.bat"
if errorlevel 1 (
    echo.
    pause
    exit /b 1
)

echo ============================================
echo   YGNT Manager v%VERSION%
echo ============================================
echo.

python main.py
set "APP_EXIT=%ERRORLEVEL%"

if not "%APP_EXIT%"=="0" (
    echo.
    echo [ERREUR] YGNT Manager s'est arrete avec le code %APP_EXIT%.
    pause
)

exit /b %APP_EXIT%
