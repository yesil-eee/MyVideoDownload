from __future__ import annotations

import os
import sys
import shutil
import logging
import tempfile
from typing import Optional, Dict, Any

from PySide6.QtCore import QObject, Signal, QThread

import yt_dlp


class DownloadWorker(QThread):
    progress = Signal(float, str, str, str)  # percent, speed, eta, title
    file_done = Signal(str)  # absolute filename saved by yt-dlp
    skipped = Signal(str)  # human-readable reason for a skipped entry
    finished = Signal(bool, str)  # success, output_path or error message

    def __init__(
        self,
        url: str,
        mode: str,
        root_dir: str,
        max_height: int = 1080,
        cookies_path: Optional[str] = None,
        cookies_from_browser: Optional[str] = None,
        ignore_archive: bool = False,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.url = url.strip()
        self.mode = mode  # 'mp4' or 'mp3'
        self.root_dir = root_dir
        self.max_height = max_height
        self.cookies_path = cookies_path
        self.cookies_from_browser = cookies_from_browser
        self.ignore_archive = ignore_archive
        self._stop = False
        self._logger = logging.getLogger("myvideodownload")
        self._ensure_logging()
        self._saw_download = False
        self._temp_handler = None

    def stop(self):
        self._stop = True
        try:
            self._logger.info("stop requested by user")
        except Exception:
            pass

    def _ensure_logging(self):
        log_path = self.get_log_path()
        log_dir = os.path.dirname(log_path)
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception:
            # As a last resort, use temp directory
            log_dir = os.path.join(tempfile.gettempdir(), "myvideodownload")
            try:
                os.makedirs(log_dir, exist_ok=True)
            except Exception:
                pass
            log_path = os.path.join(log_dir, "app.log")
        if not any(isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', '') == log_path for h in self._logger.handlers):
            self._logger.setLevel(logging.INFO)
            fh = logging.FileHandler(log_path, encoding="utf-8")
            fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            fh.setFormatter(fmt)
            self._logger.addHandler(fh)

    @staticmethod
    def get_log_path() -> str:
        # Prefer per-user writable directory
        try:
            base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
            app_dir = os.path.join(base, "MyVideoDownload", "logs")
            os.makedirs(app_dir, exist_ok=True)
            return os.path.join(app_dir, "app.log")
        except Exception:
            # Fallback to alongside executable/package (may fail under Program Files)
            return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs", "app.log"))

    def _detect_ffmpeg(self) -> Optional[str]:
        candidates = []
        here = os.path.dirname(os.path.abspath(__file__))
        # 1) Next to executable (installed/portable)
        try:
            exe_dir = os.path.dirname(sys.executable)
            candidates.append(os.path.join(exe_dir, "ffmpeg", "bin"))
        except Exception:
            pass
        # 2) PyInstaller temporary dir (MEIPASS)
        try:
            meipass = getattr(sys, "_MEIPASS", None)
            if meipass:
                candidates.append(os.path.join(meipass, "ffmpeg", "bin"))
        except Exception:
            pass
        # 3) Package-relative (dev/portable)
        candidates.append(os.path.join(here, "..", "ffmpeg", "bin"))
        candidates.append(os.path.join(here, "..", "..", "ffmpeg", "bin"))
        # 4) Env PATH
        path_ffmpeg = shutil.which("ffmpeg")
        if path_ffmpeg:
            return os.path.dirname(path_ffmpeg)
        for c in candidates:
            if os.path.exists(os.path.join(c, "ffmpeg.exe")) or os.path.exists(os.path.join(c, "ffmpeg")):
                return os.path.abspath(c)
        return None

    def _build_opts(self) -> Dict[str, Any]:
        os.makedirs(self.root_dir, exist_ok=True)

        # Output template: use autonumber to avoid missing playlist_index on single videos
        outtmpl = os.path.join(
            self.root_dir,
            "%(playlist_title|Video)s",
            "%(playlist_index|autonumber)03d - %(playlist_title|Video)s - %(title)s.%(ext)s",
        )

        ffmpeg_loc = self._detect_ffmpeg()

        # New resolution logic:
        # Priority: Selected (max_height) -> 720p -> 480p -> 360p -> best
        mh = max(144, min(int(self.max_height or 1080), 2160))
        
        # Build format string based on priority
        # We use a list of formats and join them with '/' which means "try in order"
        formats = []
        # 1. Try exact selected height (or best below it if not available)
        formats.append(f"bestvideo[height={mh}][vcodec~='^(avc1|avc|h264)']+bestaudio[ext=m4a]")
        formats.append(f"bestvideo[height={mh}]+bestaudio")
        
        # 2. Fallbacks in order: 720, 480, 360
        for fallback in [720, 480, 360]:
            if fallback < mh:
                formats.append(f"bestvideo[height={fallback}][vcodec~='^(avc1|avc|h264)']+bestaudio[ext=m4a]")
                formats.append(f"bestvideo[height={fallback}]+bestaudio")
        
        # 3. General best below max height
        formats.append(f"bestvideo[height<={mh}][vcodec~='^(avc1|avc|h264)']+bestaudio[ext=m4a]")
        formats.append(f"bestvideo[height<={mh}]+bestaudio")
        
        # 4. Absolute best as last resort
        formats.append("bestvideo+bestaudio/best")
        
        video_format_pref = "/".join(formats)

        # Archive file to record finished video IDs
        archive_path = os.path.join(self.root_dir, ".download-archive.txt")

        ydl_opts: Dict[str, Any] = {
            "outtmpl": outtmpl,
            "noplaylist": False,
            "ignoreerrors": True,
            "continuedl": True,
            "overwrites": False, # Changed to False to allow resuming partial downloads
            "merge_output_format": "mp4",
            "progress_hooks": [self._hook],
            "logger": self._logger,
            "concurrent_fragment_downloads": 5, # Increased for better speed
            "retries": 30, # Increased retries
            "fragment_retries": 20,
            "quiet": True,
            "no_warnings": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["web", "ios", "android", "tvhtml5"],
                    "skip": ["dash", "hls"], # Optimization: skip manifests if possible
                }
            },
            "geo_bypass": True,
            "http_chunk_size": 10 * 1024 * 1024,  # 10 MiB for better throughput
            "format_sort": [f"res:{mh}", "vcodec:h264", "acodec:m4a"],
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                ),
                "Referer": "https://www.google.com/",
                "Origin": "https://www.youtube.com",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Connection": "keep-alive",
            },
        }
        
        if not self.ignore_archive:
            ydl_opts["download_archive"] = archive_path
        if ffmpeg_loc:
            ydl_opts["ffmpeg_location"] = ffmpeg_loc
        if self.cookies_path and os.path.exists(self.cookies_path):
            ydl_opts["cookiefile"] = self.cookies_path
        elif self.cookies_from_browser:
            ydl_opts["cookiesfrombrowser"] = (self.cookies_from_browser,)
            
        ydl_opts["autonumber_start"] = 1

        if self.mode == "mp4":
            ydl_opts["format"] = video_format_pref
        else:  # mp3
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ]
        return ydl_opts

    def _attach_temp_log_handler(self):
        if self._temp_handler:
            return
        worker = self
        class _TempHandler(logging.Handler):
            def emit(self, record: logging.LogRecord):
                try:
                    msg = record.getMessage()
                    if record.levelno >= logging.ERROR and (
                        "[youtube]" in msg or "This video" in msg or "Private" in msg or "No video formats" in msg or "Members only" in msg or "HTTP Error 403" in msg or "Sign in" in msg
                    ):
                        worker.skipped.emit(msg)
                except Exception:
                    pass
        self._temp_handler = _TempHandler()
        self._temp_handler.setLevel(logging.ERROR)
        self._logger.addHandler(self._temp_handler)

    def _detach_temp_log_handler(self):
        if self._temp_handler:
            try:
                self._logger.removeHandler(self._temp_handler)
            except Exception:
                pass
            self._temp_handler = None

    def _hook(self, d: Dict[str, Any]) -> None:
        if self._stop:
            raise KeyboardInterrupt("Cancelled by user")
        status = d.get("status")
        title = d.get("info_dict", {}).get("title") or d.get("filename") or ""
        if status == "downloading":
            self._saw_download = True
            percent = d.get("_percent_str") or "0%"
            try:
                percent = float(percent.strip().strip('%'))
            except Exception:
                percent = 0.0
            speed = d.get("_speed_str") or ""
            eta = d.get("_eta_str") or ""
            self.progress.emit(percent, speed, eta, title)
            self._logger.info("downloading: %s %.1f%% %s ETA %s", title, percent, speed, eta)
        elif status == "finished":
            self._saw_download = True
            self.progress.emit(100.0, "", "", title)
            self._logger.info("finished download stage: %s", title)
            try:
                fn = d.get("filename")
                if fn:
                    self.file_done.emit(fn)
            except Exception:
                pass

    def run(self) -> None:
        self._logger.info("Starting download: %s", self.url)
        self._attach_temp_log_handler()
        
        # Main attempt with all clients
        try:
            opts = self._build_opts()
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([self.url])
            
            if not self._saw_download and not self._stop:
                # Check if it was just already downloaded (archive)
                archive_path = os.path.join(self.root_dir, ".download-archive.txt")
                if os.path.exists(archive_path) and not self.ignore_archive:
                    self._logger.info("No new downloads, but archive exists. Likely already downloaded.")
                    self.finished.emit(True, self.root_dir)
                    return
                raise Exception("No media downloaded. Possibly unavailable formats or all entries skipped.")
            
            if self._stop:
                self.finished.emit(False, "Cancelled by user")
            else:
                self.finished.emit(True, self.root_dir)
            return
            
        except KeyboardInterrupt:
            self.finished.emit(False, "Cancelled by user")
            return
        except Exception as e:
            msg = str(e)
            self._logger.error("Main attempt error: %s", msg)
            
            if self._stop:
                self.finished.emit(False, "Cancelled by user")
                return

            # Fallback for 403/Sign-in: Try iOS client specifically as it often bypasses some restrictions
            if "403" in msg or "Forbidden" in msg or "Sign in" in msg or "confirm your age" in msg:
                try:
                    self._logger.info("Attempting fallback with iOS client...")
                    opts = self._build_opts()
                    opts["extractor_args"]["youtube"]["player_client"] = ["ios"]
                    opts["http_chunk_size"] = 0 # Disable chunking for fallback
                    
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        ydl.download([self.url])
                    
                    if self._saw_download:
                        self.finished.emit(True, self.root_dir)
                        return
                except Exception as fe:
                    self._logger.error("Fallback error: %s", fe)
            
            self.finished.emit(False, msg)
        finally:
            self._detach_temp_log_handler()
