@echo off
setlocal
title YGNT Manager - Build Installateur (Inno Setup)

call "%~dp0_common.bat"
if errorlevel 1 (
    echo.
    if not defined YGNT_RELEASE_CHAIN pause
    exit /b 1
)

echo ============================================
echo   Build Installateur - YGNT Manager v%VERSION%
echo ============================================
echo.

set "APP_EXE=dist\YGNT Manager\YGNT Manager.exe"
if not exist "%APP_EXE%" (
    echo [ERREUR] Aucun build PyInstaller trouve :
    echo   %APP_EXE%
    echo Lancez d'abord 3_Build_EXE.bat.
    if not defined YGNT_RELEASE_CHAIN pause
    exit /b 1
)

if not exist "ygnt_manager_setup.iss" (
    echo [ERREUR] ygnt_manager_setup.iss introuvable dans "%PROJECT_ROOT%"
    if not defined YGNT_RELEASE_CHAIN pause
    exit /b 1
)

rem --- Localisation d'ISCC.exe (compilateur Inno Setup), dans cet ordre :
rem     1. PATH Windows
rem     2. %LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe (install. utilisateur, sans admin)
rem     3. C:\Program Files\Inno Setup 6\ISCC.exe
rem     4. C:\Program Files (x86)\Inno Setup 6\ISCC.exe
set "ISCC="

for /f "usebackq delims=" %%I in (`where ISCC.exe 2^>nul`) do (
    if not defined ISCC set "ISCC=%%I"
)

if not defined ISCC if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 5\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 5\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 5\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 5\ISCC.exe"

if not defined ISCC (
    echo [ERREUR] Inno Setup ^(ISCC.exe^) introuvable.
    echo Installez Inno Setup ^(https://jrsoftware.org/isinfo.php^), ou ajoutez
    echo ISCC.exe au PATH, puis relancez ce script.
    if not defined YGNT_RELEASE_CHAIN pause
    exit /b 1
)

echo Compilateur Inno Setup : %ISCC%
echo.

"%ISCC%" "ygnt_manager_setup.iss"
if errorlevel 1 (
    echo.
    echo [ERREUR] La compilation Inno Setup a echoue.
    if not defined YGNT_RELEASE_CHAIN pause
    exit /b 1
)

set "INSTALLER_EXE=installer\YGNT_Manager_Setup_%VERSION%.exe"
if not exist "%INSTALLER_EXE%" (
    echo.
    echo [ERREUR] Installateur attendu introuvable :
    echo   %INSTALLER_EXE%
    echo Verifiez que MyAppVersion dans ygnt_manager_setup.iss correspond
    echo bien a APP_VERSION dans app\version.py ^(v%VERSION%^).
    if not defined YGNT_RELEASE_CHAIN pause
    exit /b 1
)

echo.
echo Installateur genere : %INSTALLER_EXE%

if not defined YGNT_RELEASE_CHAIN pause
exit /b 0
