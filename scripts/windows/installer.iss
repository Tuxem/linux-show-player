; Inno Setup script for Linux Show Player (Windows installer).
;
; Built by scripts/windows/build.ps1, which passes the variables below:
;   ISCC /DAppVersion=0.6.5 /DSourceDir=...\dist\LinuxShowPlayer /DOutputDir=...
;
; Produces: LinuxShowPlayer-<version>-setup.exe

#ifndef AppVersion
  #define AppVersion "0.6.5"
#endif
#ifndef SourceDir
  #define SourceDir "..\..\build\windows\dist\LinuxShowPlayer"
#endif
#ifndef OutputDir
  #define OutputDir "..\..\build\windows\installer"
#endif

#define AppName "Linux Show Player"
#define AppPublisher "Francesco Ceruti"
#define AppExeName "LinuxShowPlayer.exe"
#define AppURL "https://www.linux-show-player.org/"

[Setup]
AppId={{8B0E5D9C-3F2A-4B1E-9C4D-LSP00000001}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=LinuxShowPlayer-{#AppVersion}-setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; Allow 64-bit install on x64/arm64; refuse 32-bit hosts.
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Recursively pull in the entire PyInstaller one-dir bundle.
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
