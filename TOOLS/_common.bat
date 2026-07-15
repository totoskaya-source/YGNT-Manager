@echo off
rem =====================================================================
rem  Fichier partage par les scripts numerotes de TOOLS\ - NE PAS lancer
rem  directement (double-clic sans effet visible attendu).
rem
rem  Resout le dossier du projet de facon relative (fonctionne quel que
rem  soit l'emplacement du projet sur le disque), active le venv, et lit
rem  APP_VERSION depuis app\version.py : source UNIQUE de verite pour la
rem  version, jamais recopiee en dur ailleurs dans TOOLS\.
rem
rem  Usage : call "%~dp0_common.bat"
rem  En sortie : PROJECT_ROOT, VERSION sont definis, le venv est actif,
rem  et le repertoire courant est la racine du projet.
rem =====================================================================

set "PROJECT_ROOT=%~dp0.."

cd /d "%PROJECT_ROOT%"
if errorlevel 1 (
    echo [ERREUR] Dossier du projet introuvable : "%PROJECT_ROOT%"
    exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
    echo [ERREUR] Environnement virtuel introuvable : .venv\Scripts\activate.bat
    echo Creez-le avec : python -m venv .venv
    echo Puis installez les dependances : .venv\Scripts\pip install -r requirements.txt
    exit /b 1
)

call ".venv\Scripts\activate.bat" >nul

if not exist "app\version.py" (
    echo [ERREUR] app\version.py introuvable dans "%PROJECT_ROOT%"
    exit /b 1
)

set "VERSION="
for /f "usebackq delims=" %%V in (`python -c "from app.version import APP_VERSION; print(APP_VERSION)"`) do set "VERSION=%%V"

if not defined VERSION (
    echo [ERREUR] Impossible de lire APP_VERSION depuis app\version.py
    exit /b 1
)

exit /b 0
