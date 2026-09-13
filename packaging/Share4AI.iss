#ifndef AppVersion
  #define AppVersion "1.1.3"
#endif
[Setup]
AppId={{A9FDF7E6-C713-4BDB-9E40-97E82454E0EE}
AppName=Share4AI
AppVersion={#AppVersion}
AppPublisher=Share4AI
DefaultDirName={localappdata}\Programs\Share4AI
DefaultGroupName=Share4AI
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableWelcomePage=no
DisableReadyPage=yes
WizardStyle=modern
LanguageDetectionMethod=none
ShowLanguageDialog=no
OutputDir=..\dist\installer
OutputBaseFilename=Share4AI-Setup-{#AppVersion}-windows-x64
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\Share4AI.exe
CloseApplications=yes
RestartApplications=no
SetupLogging=yes

[Languages]
Name: "arabic"; MessagesFile: "compiler:Languages\\Arabic.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
