; Inno Setup 6 — se compila desde release.yml:
;   iscc /DAppVersion=1.2.3 packaging\windows\installer.iss
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
; El AppId identifica la instalación para actualizaciones y desinstalación: no debe cambiar nunca.
AppId={{6F2C9A1E-3B7D-4E58-9C0A-5D1B2E7F8A34}
AppName=pycronk
AppVersion={#AppVersion}
AppPublisher=pycronk
DefaultDirName={autopf}\pycronk
DefaultGroupName=pycronk
UninstallDisplayIcon={app}\pycronk.exe
OutputDir=..\..\dist
OutputBaseFilename=pycronk-{#AppVersion}-windows-x64-setup
SetupIconFile=..\icons\pycronk.ico
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Permite instalar solo para el usuario actual sin permisos de administrador.
PrivilegesRequiredOverridesAllowed=dialog
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\pycronk\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\pycronk"; Filename: "{app}\pycronk.exe"
Name: "{group}\{cm:UninstallProgram,pycronk}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\pycronk"; Filename: "{app}\pycronk.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\pycronk.exe"; Description: "{cm:LaunchProgram,pycronk}"; Flags: nowait postinstall skipifsilent
