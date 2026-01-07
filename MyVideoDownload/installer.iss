; Inno Setup script for Video Download
; Requires: Inno Setup 6+
; 
; This script creates a professional Windows installer for the Video Download application.
; 
; Steps to build:
; 1) First, build the portable EXE with PyInstaller:
;    pyinstaller build.spec
; 
; 2) Download and install Inno Setup from: https://jrsoftware.org/isdl.php
; 
; 3) Open this file (installer.iss) in Inno Setup IDE
; 
; 4) Click Build > Compile
; 
; 5) The installer will be created in the Output folder

#define AppName "Video Download"
#define AppVersion "0.2.0"
#define AppPublisher "İlyas YEŞİL"
#define AppURL "https://github.com/yesil-eee/MyVideoDownload"
#define AppExeName "VideoDownload.exe"

[Setup]
; Unique App ID (do not change)
AppId={{4A0B6B7E-30C2-4C20-9B5F-7D7EFA60F7C7}}

; Application Information
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
AppCopyright=© 2024 {#AppPublisher}

; Installation Directory
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}

; UI Settings
DisableDirPage=no
DisableProgramGroupPage=no
AllowNoIcons=no
ShowLanguageDialog=yes

; Compression Settings
Compression=lzma2/ultra64
SolidCompression=yes
InternalCompressLevel=ultra64

; Architecture Settings
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64

; Icons and Display
SetupIconFile=..\icon_video2.ico
UninstallDisplayIcon={app}\{#AppExeName}
WizardStyle=modern
WizardResizable=yes

; Permissions
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=yes

; Other Settings
ChangesAssociations=no
CreateUninstallRegKey=yes
Uninstallable=yes
UninstallDisplayName={#AppName}

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstü kısayolu oluştur"; GroupDescription: "Kısayollar:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Hızlı Başlat çubuğuna kısayol ekle"; GroupDescription: "Kısayollar:"; Flags: unchecked; OnlyBelowVersion: 0,6.1

[Files]
; Include the main executable from PyInstaller output
Source: "dist\VideoDownload\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
; Start Menu shortcut
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; Comment: "YouTube videolarını indirin"
Name: "{group}\{#AppName} - Kaldır"; Filename: "{uninstallexe}"; IconFilename: "{app}\{#AppExeName}"

; Desktop shortcut (optional task)
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; Tasks: desktopicon; Comment: "YouTube videolarını indirin"

; Quick Launch shortcut (optional task, Windows XP/Vista/7 only)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; Tasks: quicklaunchicon

[Run]
; Run the application after installation (optional)
Filename: "{app}\{#AppExeName}"; Description: "{#AppName} uygulamasını şimdi başlat"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up any temporary files created by the application
Type: filesandordirs; Name: "{userappdata}\{#AppName}"
Type: filesandordirs; Name: "{localappdata}\{#AppName}"

[Code]
// Custom code for installer behavior
procedure InitializeWizard;
begin
  // Initialization code if needed
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  // Page change code if needed
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  // Step change code if needed
end;
