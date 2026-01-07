#!/usr/bin/env python3
"""
Simple Windows Installer Creator for MyVideoDownload
This script creates a basic Windows installer without requiring Inno Setup.
It packages the application with a simple batch file installer.
"""

import os
import shutil
import zipfile
from pathlib import Path


def create_installer():
    """Create a simple Windows installer package."""
    
    # Define paths
    project_root = Path(__file__).parent
    dist_dir = project_root / "dist"
    exe_file = dist_dir / "VideoDownload"
    output_dir = project_root / "installer_output"
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Check if dist directory exists
    if not exe_file.exists():
        print(f"❌ Error: {exe_file} not found!")
        print("Please run 'pyinstaller build.spec' first to create the portable EXE.")
        return False
    
    print("📦 Creating Windows installer package...")
    print(f"📁 Source EXE: {exe_file}")
    
    # Create installer batch file (for Windows)
    installer_script = """@echo off
REM Video Download Installer
REM This script installs Video Download to Program Files

setlocal enabledelayedexpansion

REM Get the installation directory
set "INSTALL_DIR=%ProgramFiles%\\Video Download"

REM Create installation directory
if not exist "!INSTALL_DIR!" (
    mkdir "!INSTALL_DIR!"
    echo Created installation directory: !INSTALL_DIR!
)

REM Copy application files
echo Installing application files...
xcopy /E /I /Y "%~dp0app\\*" "!INSTALL_DIR!\\"

REM Create Start Menu shortcut
set "START_MENU=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Video Download"
if not exist "!START_MENU!" (
    mkdir "!START_MENU!"
)

REM Create VBScript to create shortcut
set "VBS_FILE=%TEMP%\\create_shortcut.vbs"
(
    echo Set oWS = WScript.CreateObject("WScript.Shell"^)
    echo sLinkFile = "!START_MENU!\\Video Download.lnk"
    echo Set oLink = oWS.CreateShortcut(sLinkFile^)
    echo oLink.TargetPath = "!INSTALL_DIR!\\VideoDownload.exe"
    echo oLink.WorkingDirectory = "!INSTALL_DIR!"
    echo oLink.Description = "YouTube videolarını indirin"
    echo oLink.IconLocation = "!INSTALL_DIR!\\VideoDownload.exe,0"
    echo oLink.Save
) > "!VBS_FILE!"

cscript.exe "!VBS_FILE!"
del "!VBS_FILE!"

REM Create desktop shortcut (optional)
set "DESKTOP=%USERPROFILE%\\Desktop"
if exist "!DESKTOP!" (
    set "VBS_FILE=%TEMP%\\create_desktop_shortcut.vbs"
    (
        echo Set oWS = WScript.CreateObject("WScript.Shell"^)
        echo sLinkFile = "!DESKTOP!\\Video Download.lnk"
        echo Set oLink = oWS.CreateShortcut(sLinkFile^)
        echo oLink.TargetPath = "!INSTALL_DIR!\\VideoDownload.exe"
        echo oLink.WorkingDirectory = "!INSTALL_DIR!"
        echo oLink.Description = "YouTube videolarını indirin"
        echo oLink.IconLocation = "!INSTALL_DIR!\\VideoDownload.exe,0"
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
"""
    
    # Create uninstaller batch file (for Windows)
    uninstaller_script = """@echo off
REM Video Download Uninstaller

setlocal enabledelayedexpansion

set "INSTALL_DIR=%ProgramFiles%\\Video Download"
set "START_MENU=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Video Download"
set "DESKTOP=%USERPROFILE%\\Desktop"

echo Removing Video Download...

REM Remove Start Menu shortcuts
if exist "!START_MENU!" (
    rmdir /S /Q "!START_MENU!"
    echo Removed Start Menu shortcuts
)

REM Remove Desktop shortcut
if exist "!DESKTOP!\\Video Download.lnk" (
    del "!DESKTOP!\\Video Download.lnk"
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
"""
    
    # Create installer zip structure
    installer_dir = output_dir / "VideoDownloadSetup"
    if installer_dir.exists():
        shutil.rmtree(installer_dir)
    installer_dir.mkdir()
    
    # Copy application files
    app_dir = installer_dir / "app"
    app_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(exe_file, app_dir / "VideoDownload.exe")
    
    # Create installer scripts
    (installer_dir / "install.bat").write_text(installer_script)
    (installer_dir / "uninstall.bat").write_text(uninstaller_script)
    
    # Create README
    readme = """# Video Download Installer

## Installation

1. Extract this folder to a temporary location
2. Run `install.bat` to install Video Download
3. Follow the installation wizard

## Uninstallation

Run `uninstall.bat` to remove Video Download from your system.

## System Requirements

- Windows 7 or later (64-bit)
- 100 MB free disk space

## Support

For issues and feature requests, visit:
https://github.com/yesil-eee/MyVideoDownload
"""
    (installer_dir / "README.txt").write_text(readme)
    
    # Create ZIP archive
    zip_path = output_dir / "VideoDownloadSetup.zip"
    if zip_path.exists():
        zip_path.unlink()
    
    print(f"Creating ZIP archive: {zip_path.name}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(installer_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(output_dir)
                zipf.write(file_path, arcname)
    
    print(f"✓ Installer package created successfully!")
    print(f"✓ File: {zip_path.name}")
    print(f"✓ Size: {zip_path.stat().st_size / (1024*1024):.1f} MB")
    print(f"✓ Location: {output_dir}")
    
    return True


if __name__ == "__main__":
    success = create_installer()
    exit(0 if success else 1)
