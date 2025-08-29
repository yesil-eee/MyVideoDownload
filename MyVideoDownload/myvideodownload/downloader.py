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

        # Prefer H.264 MP4 streams within max_height..480; avoid >max & <480
        # Prefer mp4/h264; first leg prefers m4a audio for faster remux
        mh = max(144, min(int(self.max_height or 1080), 2160))
        video_format_pref = (
            f"bestvideo*[height<={mh}][height>=480][vcodec~='^(avc1|avc|h264)']+bestaudio[ext=m4a]/"
            f"bestvideo*[height<={mh}][height>=480][vcodec~='^(avc1|avc|h264)']+bestaudio/"
            f"bestvideo*[height<={mh}][height>=480]+bestaudio/"
            f"best[height<={mh}][height>=480]/"
            "bestvideo*+bestaudio/best"
        )

        # Archive file to record finished video IDs (helps skipping already downloaded entries)
        archive_path = os.path.join(self.root_dir, ".download-archive.txt")

        ydl_opts: Dict[str, Any] = {
            "outtmpl": outtmpl,
            "noplaylist": False,
            # Continue playlist on individual entry errors
            "ignoreerrors": True,
            # restart entries from scratch on next runs; rely on archive to skip finished ones
            "continuedl": False,
            # ensure we re-download/overwrite any partial or existing targets on restart
            "overwrites": True,
            # Track downloaded IDs to avoid re-download and aid diagnostics (unless ignored by user)
            "merge_output_format": "mp4",
            "progress_hooks": [self._hook],
            "logger": self._logger,
            "concurrent_fragment_downloads": 3,
            "retries": 20,
            "fragment_retries": 10,
            "quiet": True,
            "no_warnings": True,
            # Prefer Web client first (android may cause 403 per yt-dlp warning)
            "extractor_args": {
                "youtube": {
                    # Try multiple clients as fallbacks (web first)
                    "player_client": ["web", "ios", "android", "tvhtml5"],
                }
            },
            "geo_bypass": True,
            # Chunked downloads can avoid some 403 issues
            "http_chunk_size": 2 * 1024 * 1024,  # 2 MiB
            # Sort resolutions preferring at/below selected max height
            "format_sort": [self._build_res_sort(), "vcodec:h264"],
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                ),
                "Referer": self.url,
                "Origin": "https://www.youtube.com",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Connection": "keep-alive",
            },
        }
        # Respect archive usage unless user asked to ignore
        if not self.ignore_archive:
            ydl_opts["download_archive"] = archive_path
        if ffmpeg_loc:
            ydl_opts["ffmpeg_location"] = ffmpeg_loc
        if self.cookies_path and os.path.exists(self.cookies_path):
            ydl_opts["cookiefile"] = self.cookies_path
        elif self.cookies_from_browser:
            # e.g., 'brave', 'chrome', 'edge', 'firefox' -- must be a tuple
            ydl_opts["cookiesfrombrowser"] = (self.cookies_from_browser,)
        # Ensure autonumber starts at 1
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

    def _build_res_sort(self) -> str:
        order = [2160, 1440, 1080, 720, 480, 360, 240, 144]
        mh = max(144, min(int(self.max_height or 1080), 2160))
        # Keep only entries <= mh, in descending order, but yt-dlp likes highest first when sorting
        kept = [str(h) for h in order if h <= mh]
        if not kept:
            kept = ["144"]
        return "res:" + ",".join(kept)

    # --- temporary in-memory error capture ---
    def _attach_temp_log_handler(self):
        if self._temp_handler:
            return
        worker = self
        class _TempHandler(logging.Handler):
            def emit(self, record: logging.LogRecord):
                try:
                    msg = record.getMessage()
                    # Heuristic: per-entry errors from yt-dlp often look like
                    # "ERROR: [youtube] <id>: <reason>" or contain known phrases
                    if record.levelno >= logging.ERROR and (
                        "[youtube]" in msg or "This video" in msg or "Private" in msg or "No video formats" in msg or "Members only" in msg or "HTTP Error 403" in msg
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
        # cooperative cancel
        if self._stop:
            # Use KeyboardInterrupt to ensure yt-dlp aborts the whole playlist immediately
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
            # will be merged/extracted next
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
        self._logger.info(
            "start: url=%s mode=%s root=%s max=%sp ignore_archive=%s cookies_file=%s cookies_browser=%s",
            self.url, self.mode, self.root_dir, self.max_height, self.ignore_archive, self.cookies_path, getattr(self, 'cookies_from_browser', None)
        )
        # Attempt 1
        self._attach_temp_log_handler()
        try:
            with yt_dlp.YoutubeDL(self._build_opts()) as ydl:
                ydl.download([self.url])
            if not self._saw_download:
                raise Exception("No media downloaded. Possibly unavailable formats or all entries skipped.")
            self.finished.emit(True, self.root_dir)
            self._logger.info("success: %s", self.url)
            return
        except KeyboardInterrupt as ki:
            self._logger.info("cancelled during attempt1: %s", ki)
            self.finished.emit(False, "Cancelled by user")
            return
        except Exception as e1:
            msg = str(e1)
            self._logger.error("attempt1 error: %s", msg, exc_info=True)
            # If user pressed stop, don't attempt fallbacks
            if self._stop:
                self.finished.emit(False, "Cancelled by user")
                return
            # Fallback only for common HTTP 403 / forbidden / sign-in gate
            if "403" not in msg and "Forbidden" not in msg and "Sign in" not in msg:
                self.finished.emit(False, msg)
                return
        # Attempt 2: relax format, change client to iOS and disable chunking
        try:
            opts = self._build_opts()
            # Switch to iOS client explicitly
            opts.setdefault("extractor_args", {}).setdefault("youtube", {})["player_client"] = ["ios"]
            # Looser format but keep max..360 bound
            if self.mode == "mp4":
                mh = max(144, min(int(self.max_height or 1080), 2160))
                opts["format"] = (
                    f"bestvideo*[height<={mh}][height>=360]+bestaudio/"
                    f"best[height<={mh}]/best"
                )
            # Smaller chunks or disable
            opts["http_chunk_size"] = 0  # let yt-dlp decide
            self._logger.info("fallback attempt: iOS client, relaxed format")
            self._saw_download = False
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([self.url])
            if not self._saw_download:
                raise Exception("No media downloaded in fallback attempt.")
            self.finished.emit(True, self.root_dir)
            self._logger.info("success (fallback/iOS): %s", self.url)
        except KeyboardInterrupt as ki2:
            self._logger.info("cancelled during attempt2: %s", ki2)
            self.finished.emit(False, "Cancelled by user")
            return
        except Exception as e2:
            self._logger.error("attempt2 error: %s", e2, exc_info=True)
            if self._stop:
                self.finished.emit(False, "Cancelled by user")
                return
            # If still a format error, one last try with plain 'best'
            msg2 = str(e2)
            if "Requested format is not available" in msg2 or "No video formats" in msg2:
                try:
                    opts = self._build_opts()
                    opts["format"] = "best"
                    # Try android as last option
                    opts.setdefault("extractor_args", {}).setdefault("youtube", {})["player_client"] = ["android"]
                    self._logger.info("final attempt: format=best, client=android")
                    self._saw_download = False
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        ydl.download([self.url])
                    if not self._saw_download:
                        raise Exception("No media downloaded in final attempt.")
                    self.finished.emit(True, self.root_dir)
                    self._logger.info("success (final/android): %s", self.url)
                    return
                except KeyboardInterrupt as ki3:
                    self._logger.info("cancelled during final attempt: %s", ki3)
                    self.finished.emit(False, "Cancelled by user")
                    return
                except Exception as e3:
                    self._logger.error("final attempt error: %s", e3, exc_info=True)
                    if self._stop:
                        self.finished.emit(False, "Cancelled by user")
                    else:
                        self.finished.emit(False, str(e3))
            else:
                if self._stop:
                    self.finished.emit(False, "Cancelled by user")
                else:
                    self.finished.emit(False, msg2)
        finally:
            self._detach_temp_log_handler()
