# -*- mode: python ; coding: utf-8 -*-
"""Spec PyInstaller pour YGNT Manager.

Build recommande (onedir - voir points d'attention livres avec ce sprint) :
    pyinstaller ygnt_manager.spec

Donnees UTILISATEUR (base SQLite, exports/, backup/) : jamais embarquees ici.
Elles sont creees a cote de l'executable au premier lancement, via
app/paths.py (BASE_DIR) - inchange par ce fichier.

Ressources EN LECTURE SEULE embarquees : uniquement templates/ (les 3
modeles DOCX), resolues au runtime via app.paths.resource_path().
"""

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("templates", "templates"),
    ],
    hiddenimports=[
        # pywin32 : win32com.client resout Word.Application dynamiquement
        # (early binding via gen_py) - ces modules ne sont pas toujours
        # detectes par l'analyse statique des imports de PyInstaller.
        "win32com",
        "win32com.client",
        "win32timezone",
        "pythoncom",
        "pywintypes",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Dependances installees dans l'environnement de dev mais non
        # importees par app/ ou main.py (verifie par recherche statique) :
        # ne pas les embarquer inutilement alourdit et fragilise le build.
        "customtkinter",
        "docx2pdf",
        "docxtpl",
        "fitz",
        "PyMuPDF",
        "tkinter",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="YGNT Manager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # application graphique : pas de console
    icon=None,  # aucune icone .ico dans le projet actuellement - voir livrable
    disable_windowed_traceback=False,
    argv_emulation=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="YGNT Manager",
)
