#ifndef AppVersion
  #define AppVersion "1.1.5"
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
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
arabic.WelcomeLabel1=مرحبًا بك في Share4AI
arabic.WelcomeLabel2=ثبّت التطبيق وابدأ استخدام الذكاء الاصطناعي من جهازك.%n%nلا تحتاج إلى أدوات إضافية أو كتابة أوامر. سيختار التطبيق النموذج المناسب وينزله بعد موافقتك.%n%nهذه نسخة تجريبية للاختبار.
english.WelcomeLabel2=Install the app and start using AI on your computer.%n%nNo additional tools or commands are needed. The app selects a suitable model and downloads it after your confirmation.%n%nThis is a trial build.

[Files]
Source: "..\dist\Share4AI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[CustomMessages]
arabic.DesktopShortcut=إنشاء اختصار على سطح المكتب
english.DesktopShortcut=Create a desktop shortcut

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopShortcut}"

[Icons]
Name: "{userdesktop}\Share4AI"; Filename: "{app}\Share4AI.exe"; Tasks: desktopicon
Name: "{userprograms}\Share4AI"; Filename: "{app}\Share4AI.exe"

[Run]
Filename: "{app}\Share4AI.exe"; Description: "{cm:LaunchProgram,Share4AI}"; Flags: nowait postinstall skipifsilent

; Deliberately no UninstallDelete: user models and preferences live outside {app}.
