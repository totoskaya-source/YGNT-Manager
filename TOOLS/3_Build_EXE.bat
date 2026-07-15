@echo off
setlocal
title YGNT Manager - Build EXE (PyInstaller)

call "%~dp0_common.bat"
if errorlevel 1 (
    echo.
    if not defined YGNT_RELEASE_CHAIN pause
    exit /b 1
)

echo ============================================
echo   Build EXE - YGNT Manager v%VERSION%
echo ============================================
echo.

if not exist "ygnt_manager.spec" (
    echo [ERREUR] ygnt_manager.spec introuvable dans "%PROJECT_ROOT%"
    if not defined YGNT_RELEASE_CHAIN pause
    exit /b 1
)

pyinstaller ygnt_manager.spec --noconfirm
if errorlevel 1 (
    echo.
    echo [ERREUR] PyInstaller a echoue.
    if not defined YGNT_RELEASE_CHAIN pause
    exit /b 1
)

set "APP_EXE=dist\YGNT Manager\YGNT Manager.exe"
if not exist "%APP_EXE%" (
    echo.
    echo [ERREUR] Build termine mais l'executable est introuvable :
    echo   %APP_EXE%
    if not defined YGNT_RELEASE_CHAIN pause
    exit /b 1
)

echo.
echo Executable genere : %APP_EXE%

if not defined YGNT_RELEASE_CHAIN pause
exit /b 0
