# MyVideoDownload

A Windows desktop YouTube playlist/video downloader built with Python and PySide6, powered by yt-dlp. Provides clean resume behavior (restart current item from scratch, skip finished via archive), max resolution selection, cookies support, and packaged portable/installer builds with ffmpeg.

## Features
- Max resolution selector (2160p .. 144p)
- Video (MP4) or Audio (MP3) download
- Stop and Resume buttons (resume restarts current item; finished ones are skipped via `.download-archive.txt`)
- Uses yt-dlp with robust format selection and client fallbacks
- Cookies from file or imported from browser (optional)
- ffmpeg auto-detection (bundled with builds)
- Persistent logs under `%LOCALAPPDATA%/MyVideoDownload/logs/app.log`
- Portable and Installer builds (PyInstaller + Inno Setup)

## Project Structure
- `MyVideoDownload/myvideodownload/` — app source code (UI and downloader)
- `MyVideoDownload/dist/` — portable build output (gitignored)
- `MyVideoDownload/Output/` — installer output (gitignored)
- `ffmpeg/` — local ffmpeg binaries for packaging (gitignored)

## Development
Requires Python 3.10+ on Windows.

```powershell
# (optional) create venv
python -m venv .venv
.venv\Scripts\Activate.ps1

# install deps
pip install -U pip
pip install PySide6 yt-dlp browser-cookie3

# run app
python -m MyVideoDownload.myvideodownload
```

## Build (Portable and Installer)
```powershell
# Portable (PyInstaller)
.venv\Scripts\python.exe -m PyInstaller -y -n MyVideoDownload -w -i icon_video.ico --onedir MyVideoDownload\myvideodownload\__main__.py
# Copy ffmpeg & icons next to EXE (if needed)
# Then run Inno Setup to build installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" MyVideoDownload\installer.iss
```

## Usage Tips
- Default download folder: `C:\\Video Download`
- Archive file: `.download-archive.txt` in the chosen root folder
- For private/unlisted videos, provide valid cookies (`cookies.txt` or import from browser)

## License
Add your preferred license (e.g., MIT) as `LICENSE`.

## Credits
Developed by İlyas YEŞİL. Built with PySide6 and yt-dlp.
