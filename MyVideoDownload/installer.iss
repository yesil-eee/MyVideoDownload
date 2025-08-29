; Inno Setup script for My Video Download
; Requires: Inno Setup 6+
; Steps:
; 1) Build the app with PyInstaller to create the dist folder, e.g.
;    dist\MyVideoDownload\MyVideoDownload.exe and all dependencies.
; 2) Open this installer.iss in Inno Setup and click Build.

#define AppName "My Video Download"
#define AppVersion "0.1.0"
#define Publisher "İlyas YEŞİL"

[Setup]
AppId={{4A0B6B7E-30C2-4C20-9B5F-7D7EFA60F7C7}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#Publisher}
AppCopyright=Developed by {#Publisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableDirPage=no
DisableProgramGroupPage=no
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

; Use the app icon from the repository root (relative to this .iss file)
SetupIconFile=..\icon_video.ico
UninstallDisplayIcon={app}\MyVideoDownload.exe

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstü kısayolu oluştur"; GroupDescription: "Kısayollar:"; Flags: unchecked

[Files]
; Include everything under the PyInstaller output folder
Source: "dist\MyVideoDownload\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
; Start Menu shortcut
Name: "{group}\{#AppName}"; Filename: "{app}\MyVideoDownload.exe"; IconFilename: "{app}\MyVideoDownload.exe"
; Desktop shortcut (optional task)
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\MyVideoDownload.exe"; Tasks: desktopicon; IconFilename: "{app}\MyVideoDownload.exe"

[Run]
; Optionally run the app after install
Filename: "{app}\MyVideoDownload.exe"; Description: "{#AppName} uygulamasını başlat"; Flags: nowait postinstall skipifsilent
