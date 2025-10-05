;
; Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.
;
; PROPRIETARY AND CONFIDENTIAL
;
; LALO AI Platform - Windows Installer Script
; Built with Inno Setup 6.x
;

#define MyAppName "LALO AI Platform"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "LALO AI SYSTEMS, LLC"
#define MyAppURL "https://laloai.com"
#define MyAppExeName "start.bat"

[Setup]
; Application identity
AppId={{B3F5A7D2-8C4E-4A1F-9D2B-6E8F9A1C3B5D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright=Copyright (C) 2025 LALO AI SYSTEMS, LLC

; Installation paths
DefaultDirName={autopf}\LALO AI
DefaultGroupName=LALO AI Platform
AllowNoIcons=yes
DisableProgramGroupPage=yes

; Output
OutputDir=..\..\dist
OutputBaseFilename=LALO-AI-Setup-{#MyAppVersion}
SetupIconFile=lalo-icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Requirements
MinVersion=10.0.17763
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; License
LicenseFile=..\..\LICENSE
InfoBeforeFile=readme-before-install.txt
InfoAfterFile=readme-after-install.txt

; Privileges
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Python embeddable package (downloaded separately)
Source: "python-3.11.9-embed-amd64\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs

; Backend application
Source: "..\..\core\*"; DestDir: "{app}\core"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\app.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

; Frontend build
Source: "..\..\lalo-frontend\build\*"; DestDir: "{app}\lalo-frontend\build"; Flags: ignoreversion recursesubdirs createallsubdirs

; Scripts
Source: "..\..\scripts\*"; DestDir: "{app}\scripts"; Flags: ignoreversion recursesubdirs createallsubdirs

; Batch files for Windows
Source: "start.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "first_run.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "install_deps.bat"; DestDir: "{app}"; Flags: ignoreversion

; Documentation
Source: "..\..\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "..\..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs; Tasks: ; Languages:

; Configuration templates
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion

; NOTE: Models directory is NOT included (too large)
; Models will be downloaded on first run

[Dirs]
Name: "{app}\models"; Permissions: users-full
Name: "{app}\data"; Permissions: users-full
Name: "{app}\logs"; Permissions: users-full

[Icons]
Name: "{group}\LALO AI Platform"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\lalo-icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\LALO AI Platform"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\lalo-icon.ico"; Tasks: desktopicon

[Run]
; First run setup - install dependencies and configure
Filename: "{app}\first_run.bat"; Description: "Install dependencies and download AI models"; Flags: postinstall runhidden
Filename: "{app}\start.bat"; Description: "Launch LALO AI Platform"; Flags: postinstall nowait skipifsilent

[Code]
var
  DownloadModelsCheckBox: TNewCheckBox;

procedure InitializeWizard;
begin
  // Add custom page with model download option
end;

function GetPythonPath(Param: String): String;
begin
  Result := ExpandConstant('{app}\python\python.exe');
end;

function GetAppDir(Param: String): String;
begin
  Result := ExpandConstant('{app}');
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}\models"
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\python\Lib\site-packages"
