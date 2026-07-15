@echo off
setlocal
title YGNT Manager - Release

rem =====================================================================
rem  Bouton principal du Build Center.
rem  Enchaine : venv -> nettoyage build/dist -> PyInstaller -> verification
rem  EXE -> Inno Setup -> verification installateur -> publication dans
rem  releases\<version>\ (installateur + CHANGELOG.md) -> ouverture du
rem  dossier. La version vient uniquement de app\version.py (_common.bat) :
rem  aucune valeur de version n'est ecrite en dur dans ce script.
rem =====================================================================

set "YGNT_RELEASE_CHAIN=1"

call "%~dp0_common.bat"
if errorlevel 1 (
    echo.
    pause
    exit /b 1
)

echo ============================================
echo   YGNT Manager - RELEASE v%VERSION%
echo ============================================
echo.

echo [1/7] Nettoyage build\, dist\, __pycache__, *.pyc...
call "%~dp02_Clean.bat"
if errorlevel 1 goto :fail
echo   OK
echo.

echo [2/7] Compilation PyInstaller...
call "%~dp03_Build_EXE.bat"
if errorlevel 1 goto :fail
echo   OK
echo.

echo [3/7] Generation de l'installateur Inno Setup...
call "%~dp04_Build_Installateur.bat"
if errorlevel 1 goto :fail
echo   OK
echo.

echo [4/7] Creation de releases\%VERSION%\...

if not exist "releases" mkdir "releases"

set "RELEASE_DIR=releases\%VERSION%"
if not exist "%RELEASE_DIR%" mkdir "%RELEASE_DIR%"
echo   OK
echo.

echo [5/7] Copie des livrables...

set "INSTALLER_EXE=installer\YGNT_Manager_Setup_%VERSION%.exe"

copy /y "%INSTALLER_EXE%" "%RELEASE_DIR%\" >nul
if errorlevel 1 (
    echo [ERREUR] Echec de la copie de l'installateur vers %RELEASE_DIR%
    goto :fail
)
echo   - Installateur copie  : %RELEASE_DIR%\YGNT_Manager_Setup_%VERSION%.exe

copy /y "CHANGELOG.md" "%RELEASE_DIR%\" >nul
if errorlevel 1 (
    echo [ERREUR] Echec de la copie de CHANGELOG.md vers %RELEASE_DIR%
    goto :fail
)
echo   - CHANGELOG.md copie  : %RELEASE_DIR%\CHANGELOG.md

if exist "README.md" (
    copy /y "README.md" "%RELEASE_DIR%\" >nul
    if errorlevel 1 (
        echo [ERREUR] Echec de la copie de README.md vers %RELEASE_DIR%
        goto :fail
    )
    echo   - README.md copie     : %RELEASE_DIR%\README.md
) else (
    echo   - README.md absent du projet, ignore
)
echo   OK
echo.

echo [6/7] ============================================
echo         RELEASE TERMINEE
echo         YGNT Manager v%VERSION%
echo         %RELEASE_DIR%
echo       ============================================
echo.

echo [7/7] Ouverture du dossier de release...
start "" "%RELEASE_DIR%"

echo.
pause
exit /b 0

:fail
echo.
echo ============================================
echo   ECHEC de la release v%VERSION%.
echo   Voir le message d'erreur ci-dessus.
echo ============================================
pause
exit /b 1
