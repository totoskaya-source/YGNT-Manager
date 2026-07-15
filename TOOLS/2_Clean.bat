@echo off
setlocal
title YGNT Manager - Nettoyage build/dist

call "%~dp0_common.bat"
if errorlevel 1 (
    echo.
    if not defined YGNT_RELEASE_CHAIN pause
    exit /b 1
)

echo ============================================
echo   Nettoyage des artefacts de build (v%VERSION%)
echo ============================================
echo.

if exist "build" (
    echo   - Suppression de build\  ^(temporaires PyInstaller^)
    rmdir /s /q "build"
) else (
    echo   - build\ deja absent
)

if exist "dist" (
    echo   - Suppression de dist\
    rmdir /s /q "dist"
) else (
    echo   - dist\ deja absent
)

rem --- __pycache__\ et *.pyc, partout dans le projet SAUF .venv\ et .git\
rem     (jamais touches : environnement virtuel et historique Git). ---

set "PYCACHE_COUNT=0"
for /f "delims=" %%D in ('dir /ad /b /s "__pycache__*" 2^>nul ^| findstr /v /i "\.venv\ \.git\"') do (
    if exist "%%D" (
        rmdir /s /q "%%D" 2>nul
        set /a PYCACHE_COUNT+=1
    )
)
echo   - %PYCACHE_COUNT% dossier(s) __pycache__ supprime(s)

set "PYC_COUNT=0"
for /f "delims=" %%F in ('dir /a-d /b /s "*.pyc" 2^>nul ^| findstr /v /i "\.venv\ \.git\"') do (
    if exist "%%F" (
        del /f /q "%%F" 2>nul
        set /a PYC_COUNT+=1
    )
)
echo   - %PYC_COUNT% fichier(s) *.pyc supprime(s)

echo.
echo Nettoyage termine.

if not defined YGNT_RELEASE_CHAIN pause
exit /b 0
