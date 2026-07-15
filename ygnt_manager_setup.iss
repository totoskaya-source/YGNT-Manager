; Script Inno Setup - YGNT Manager
; Genere YGNT_Manager_Setup_1.0.3.exe a partir du build PyInstaller
; (dist\YGNT Manager\ - voir ygnt_manager.spec, Sprint 13.0).
;
; Procedure de generation :
;   1) pyinstaller ygnt_manager.spec --noconfirm   (produit dist\YGNT Manager\)
;   2) ISCC ygnt_manager_setup.iss                 (produit installer\YGNT_Manager_Setup_1.0.3.exe)

#define MyAppName "YGNT Manager"
#define MyAppVersion "1.0.3"
#define MyAppPublisher "YGNT"
#define MyAppExeName "YGNT Manager.exe"
#define MyAppSourceDir "dist\YGNT Manager"

[Setup]
; GUID fixe : identifie l'application entre les versions pour que les mises a
; jour ecrasent proprement une installation existante au lieu d'en creer une
; seconde. Ne jamais changer cette valeur pour une mise a jour de YGNT Manager.
AppId={{39D3663D-5C6C-49EE-90B8-9D2619B5B68C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

; Ressource de version Windows de l'installateur lui-meme (Proprietes >
; Details de YGNT_Manager_Setup_1.0.3.exe) - independante de AppVersion, qui
; ne concerne que l'application installee (Programmes et fonctionnalites).
VersionInfoVersion={#MyAppVersion}
VersionInfoProductVersion={#MyAppVersion}

; Installation par utilisateur (pas d'elevation UAC requise) dans un dossier
; ecrit par l'utilisateur courant : YGNT Manager cree data/, exports/ et
; backup/ a cote de son executable des le premier lancement (voir
; app/paths.py, Sprint 13.0). Installer dans Program Files empecherait ces
; ecritures sans privileges administrateur - a ne jamais faire pour cette
; application. Ce choix est deliberement documente ici.
DefaultDirName={localappdata}\{#MyAppName}
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=installer
OutputBaseFilename=YGNT_Manager_Setup_1.0.3
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Aucune icone .ico dans le projet a ce jour : l'installateur et le
; raccourci utilisent l'icone par defaut de l'executable PyInstaller.
; SetupIconFile=assets\ygnt.ico

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Tous les fichiers produits par PyInstaller (dossier onedir complet,
; executable + _internal/). Rien d'autre : data/, exports/, backup/ ne sont
; jamais installes ici, ils sont crees par l'application elle-meme au
; premier lancement - l'installateur n'en a donc jamais connaissance et ne
; peut pas les supprimer par megarde a la desinstallation.
Source: "{#MyAppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Code]
// Les dossiers de donnees utilisateur ne sont jamais listes dans [Files] :
// le desinstallateur genere par Inno Setup ne connait donc que les fichiers
// du programme et ne les touche jamais de lui-meme. Ce gestionnaire ajoute
// UNIQUEMENT la possibilite explicite de les supprimer en plus, toujours
// desactivee par defaut (MB_DEFBUTTON2 = "Non" pre-selectionne, y compris
// en desinstallation silencieuse ou les boites de dialogue sont auto-
// repondues avec le bouton par defaut).
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir, ExportsDir, BackupDir: String;
  Response: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataDir := ExpandConstant('{app}\data');
    ExportsDir := ExpandConstant('{app}\exports');
    BackupDir := ExpandConstant('{app}\backup');

    if DirExists(DataDir) or DirExists(ExportsDir) or DirExists(BackupDir) then
    begin
      Response := MsgBox(
        'YGNT Manager a ete desinstalle.' + #13#10 + #13#10 +
        'Vos donnees (base de donnees, documents generes, sauvegardes) ont ete conservees dans :' + #13#10 +
        ExpandConstant('{app}') + #13#10 + #13#10 +
        'Voulez-vous AUSSI supprimer definitivement ces donnees ?' + #13#10 +
        'Cette action est IRREVERSIBLE.',
        mbConfirmation, MB_YESNO or MB_DEFBUTTON2);

      if Response = IDYES then
      begin
        DelTree(DataDir, True, True, True);
        DelTree(ExportsDir, True, True, True);
        DelTree(BackupDir, True, True, True);
      end;
    end;
  end;
end;
