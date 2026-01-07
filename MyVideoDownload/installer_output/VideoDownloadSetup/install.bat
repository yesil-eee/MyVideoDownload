@echo off
REM Video Download Installer
REM This script installs Video Download to Program Files

setlocal enabledelayedexpansion

REM Get the installation directory
set "INSTALL_DIR=%ProgramFiles%\Video Download"

REM Create installation directory
if not exist "!INSTALL_DIR!" (
    mkdir "!INSTALL_DIR!"
    echo Created installation directory: !INSTALL_DIR!
)

REM Copy application files
echo Installing application files...
xcopy /E /I /Y "%~dp0app\*" "!INSTALL_DIR!\"

REM Create Start Menu shortcut
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Video Download"
if not exist "!START_MENU!" (
    mkdir "!START_MENU!"
)

REM Create VBScript to create shortcut
set "VBS_FILE=%TEMP%\create_shortcut.vbs"
(
    echo Set oWS = WScript.CreateObject("WScript.Shell"^)
    echo sLinkFile = "!START_MENU!\Video Download.lnk"
    echo Set oLink = oWS.CreateShortcut(sLinkFile^)
    echo oLink.TargetPath = "!INSTALL_DIR!\VideoDownload.exe"
    echo oLink.WorkingDirectory = "!INSTALL_DIR!"
    echo oLink.Description = "YouTube videolarını indirin"
    echo oLink.IconLocation = "!INSTALL_DIR!\VideoDownload.exe,0"
    echo oLink.Save
) > "!VBS_FILE!"

cscript.exe "!VBS_FILE!"
del "!VBS_FILE!"

REM Create desktop shortcut (optional)
set "DESKTOP=%USERPROFILE%\Desktop"
if exist "!DESKTOP!" (
    set "VBS_FILE=%TEMP%\create_desktop_shortcut.vbs"
    (
        echo Set oWS = WScript.CreateObject("WScript.Shell"^)
        echo sLinkFile = "!DESKTOP!\Video Download.lnk"
        echo Set oLink = oWS.CreateShortcut(sLinkFile^)
        echo oLink.TargetPath = "!INSTALL_DIR!\VideoDownload.exe"
        echo oLink.WorkingDirectory = "!INSTALL_DIR!"
        echo oLink.Description = "YouTube videolarını indirin"
        echo oLink.IconLocation = "!INSTALL_DIR!\VideoDownload.exe,0"
        echo oLink.Save
    ) > "!VBS_FILE!"
    
    cscript.exe "!VBS_FILE!"
    del "!VBS_FILE!"
)

echo.
echo ✓ Installation complete!
echo.
echo You can now run Video Download from:
echo - Start Menu: Video Download
echo - Desktop shortcut (if created)
echo - Installation folder: !INSTALL_DIR!
echo.
pause
