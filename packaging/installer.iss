; Attribo - Inno Setup 6 script
; (c) 2026 Ayush Gupta (Attribo). All rights reserved.
; Build the app first:  powershell -File packaging\build.ps1

#define MyAppName "Attribo"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "Ayush Gupta"
#define MyAppExeName "Attribo.exe"

[Setup]
AppId={{8E4F2B8A-9C3D-4E5F-A6B7-C8D9E0F1A2B3}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppCopyright=Copyright (c) 2026 Ayush Gupta (Attribo)
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=..\dist\installer
OutputBaseFilename=Attribo_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
SetupIconFile=appicon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\Attribo\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Registry]
; Explorer integration: right-click a document -> "Scan with Attribo"
; (per-user keys, removed again on uninstall)
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.docx\shell\AttriboScan"; ValueType: string; ValueName: ""; ValueData: "Scan with Attribo"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.docx\shell\AttriboScan"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#MyAppExeName}"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.docx\shell\AttriboScan\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --scan ""%1"""
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\AttriboScan"; ValueType: string; ValueName: ""; ValueData: "Scan with Attribo"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\AttriboScan"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#MyAppExeName}"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\AttriboScan\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --scan ""%1"""
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.txt\shell\AttriboScan"; ValueType: string; ValueName: ""; ValueData: "Scan with Attribo"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.txt\shell\AttriboScan"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#MyAppExeName}"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.txt\shell\AttriboScan\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --scan ""%1"""

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
