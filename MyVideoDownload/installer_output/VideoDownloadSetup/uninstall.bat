@echo off
REM Video Download Uninstaller

setlocal enabledelayedexpansion

set "INSTALL_DIR=%ProgramFiles%\Video Download"
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Video Download"
set "DESKTOP=%USERPROFILE%\Desktop"

echo Removing Video Download...

REM Remove Start Menu shortcuts
if exist "!START_MENU!" (
    rmdir /S /Q "!START_MENU!"
    echo Removed Start Menu shortcuts
)

REM Remove Desktop shortcut
if exist "!DESKTOP!\Video Download.lnk" (
    del "!DESKTOP!\Video Download.lnk"
    echo Removed Desktop shortcut
)

REM Remove installation directory
if exist "!INSTALL_DIR!" (
    rmdir /S /Q "!INSTALL_DIR!"
    echo Removed installation directory
)

echo.
echo ✓ Uninstallation complete!
echo.
pause
