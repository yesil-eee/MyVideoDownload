from __future__ import annotations

import os
from typing import Optional
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QBrush, QColor, QAction
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

import tempfile
from .downloader import DownloadWorker
from . import __app_name__, __version__


DEFAULT_ROOT = r"C:\\Video Download"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(__app_name__)
        self.setMinimumSize(760, 420)

        # Try to set window icon if exists (frozen/dev)
        icon = self._resolve_app_icon()
        if icon:
            self.setWindowIcon(icon)

        central = QWidget(self)
        self.setCentralWidget(central)
        main = QVBoxLayout(central)

        # Remove Help menu; we use a footer in the status bar instead

        # URL input
        main.addWidget(QLabel("YouTube Playlist / Video Linki:"))
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://...")
        main.addWidget(self.url_edit)

        # Mode
        main.addWidget(QLabel("İndirme Türü:"))
        self.mode_group = QButtonGroup(self)
        rb_video = QRadioButton("Video (MP4)")
        rb_audio = QRadioButton("Ses (MP3)")
        rb_video.setChecked(True)
        self.mode_group.addButton(rb_video, 1)
        self.mode_group.addButton(rb_audio, 2)
        row = QHBoxLayout()
        row.addWidget(rb_video)
        row.addWidget(rb_audio)
        row.addStretch(1)
        main.addLayout(row)

        # Max resolution
        res_row = QHBoxLayout()
        res_row.addWidget(QLabel("Maks. Çözünürlük:"))
        self.maxres_combo = QComboBox()
        # label, value pairs
        for label, val in [("2160p (4K)", 2160), ("1440p", 1440), ("1080p", 1080), ("720p", 720), ("480p", 480), ("360p", 360), ("144p", 144)]:
            self.maxres_combo.addItem(label, val)
        # default 1080p
        idx = max(0, self.maxres_combo.findData(1080))
        self.maxres_combo.setCurrentIndex(idx)
        res_row.addWidget(self.maxres_combo)
        res_row.addStretch(1)
        main.addLayout(res_row)

        # Root folder
        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("Kayıt Klasörü:"))
        self.root_edit = QLineEdit(DEFAULT_ROOT)
        btn_browse = QPushButton("Gözat")
        folder_row.addWidget(self.root_edit)
        folder_row.addWidget(btn_browse)
        main.addLayout(folder_row)

        # Recent list
        main.addWidget(QLabel("İşlemler:"))
        self.recent_list = QListWidget()
        self.recent_list.setAlternatingRowColors(True)
        main.addWidget(self.recent_list)

        # Skipped list
        main.addWidget(QLabel("Atlananlar:"))
        self.skipped_list = QListWidget()
        self.skipped_list.setAlternatingRowColors(True)
        main.addWidget(self.skipped_list)

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        main.addWidget(self.progress)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_clear = QPushButton("Temizle")
        self.btn_download = QPushButton("İndir")
        self.btn_stop = QPushButton("Durdur")
        self.btn_resume = QPushButton("Devam Et")
        self.btn_exit = QPushButton("Çıkış")
        # Style IDs
        self.btn_clear.setObjectName("btnSecondary")
        self.btn_download.setObjectName("btnPrimary")
        self.btn_stop.setObjectName("btnDanger")
        self.btn_resume.setObjectName("btnAccent")
        self.btn_exit.setObjectName("btnExit")
        # Archive toggle
        self.chk_ignore_archive = QCheckBox("Arşivi yoksay (yeniden indir)")
        self.chk_ignore_archive.setToolTip("İşaretlenirse daha önce arşive kaydedilmiş videolar da yeniden indirilir")
        btn_row.addWidget(self.btn_clear)
        btn_row.addWidget(self.btn_download)
        btn_row.addWidget(self.btn_stop)
        btn_row.addWidget(self.btn_resume)
        btn_row.addWidget(self.btn_exit)
        btn_row.addWidget(self.chk_ignore_archive)
        btn_row.addStretch(1)
        main.addLayout(btn_row)

        # Footer: show version (left) and developer (right) in the status bar
        sb = self.statusBar()
        self.lbl_version = QLabel(f"Sürüm: {__version__}")
        self.lbl_dev = QLabel("Developed by İlyas YEŞİL")
        sb.addWidget(self.lbl_version)           # left side
        sb.addPermanentWidget(self.lbl_dev)      # right side

        # Cookies button (optional)
        cookies_row = QHBoxLayout()
        self.cookies_path: Optional[str] = None
        self.cookies_browser: Optional[str] = None
        self.btn_cookies = QPushButton("cookies.txt Yükle")
        self.btn_cookies_auto = QPushButton("Tarayıcıdan Cookies Al")
        self.btn_open_log = QPushButton("Logu Aç")
        # Style IDs for utility buttons
        self.btn_cookies.setObjectName("btnSecondary")
        self.btn_cookies_auto.setObjectName("btnSecondary")
        self.btn_open_log.setObjectName("btnSecondary")
        cookies_row.addWidget(self.btn_cookies)
        cookies_row.addWidget(self.btn_cookies_auto)
        cookies_row.addWidget(self.btn_open_log)
        cookies_row.addStretch(1)
        main.addLayout(cookies_row)

        # State
        self.worker: Optional[DownloadWorker] = None
        self._run_stats = {"completed": 0, "skipped": []}  # list of dicts: {id, reason, raw}
        self._last_params: Optional[dict] = None  # for resume
        self.btn_stop.setEnabled(False)
        self.btn_resume.setEnabled(False)

        # Connects
        btn_browse.clicked.connect(self._choose_root)
        self.btn_download.clicked.connect(self._start_download)
        self.btn_stop.clicked.connect(self._stop_download)
        self.btn_resume.clicked.connect(self._resume_download)
        self.btn_clear.clicked.connect(self._clear)
        self.btn_exit.clicked.connect(self.close)
        self.btn_cookies.clicked.connect(self._choose_cookies)
        self.btn_cookies_auto.clicked.connect(self._import_cookies_from_browser)
        self.btn_open_log.clicked.connect(self._open_log)

        # Apply UI styles
        self._apply_styles()

    def _choose_root(self):
        d = QFileDialog.getExistingDirectory(self, "Klasör Seç", self.root_edit.text() or DEFAULT_ROOT)
        if d:
            self.root_edit.setText(d)

    def _choose_cookies(self):
        path, _ = QFileDialog.getOpenFileName(self, "cookies.txt seç", "", "Text Files (*.txt);;All Files (*)")
        if path:
            self.cookies_path = path
            self.statusBar().showMessage("Cookies eklendi", 3000)

    def _import_cookies_from_browser(self):
        # Let user choose the browser
        options = ["brave", "firefox", "chrome", "edge"]
        choice, ok = QInputDialog.getItem(self, "Tarayıcı Seç", "Cookies alınacak tarayıcı:", options, 0, False)
        if not ok or not choice:
            return
        self.cookies_browser = choice
        # Try to fetch cookies into a temp file using browser_cookie3 as primary method
        try:
            import browser_cookie3 as bc3
            getter = {
                "brave": bc3.brave,
                "chrome": bc3.chrome,
                "edge": bc3.edge,
                "firefox": bc3.firefox,
            }.get(choice)
            cj = getter() if getter else None  # get all cookies to avoid domain filtering issues
            # If empty, try specific domains
            if (not cj) or len(cj) == 0:
                for domain in ("youtube.com", "google.com"):  # consent checks may hit google
                    try:
                        cj = getter(domain_name=domain)
                        if cj and len(cj) > 0:
                            break
                    except Exception:
                        continue
            if cj and len(cj) > 0:
                tmp = tempfile.NamedTemporaryFile(prefix="cookies_", suffix=".txt", delete=False)
                cj.save(tmp.name)
                tmp.close()
                self.cookies_path = tmp.name
                self.statusBar().showMessage(f"Cookies alındı: {choice}", 4000)
            else:
                self.cookies_path = None
                self.statusBar().showMessage(f"{choice} için cookie bulunamadı, yine de deneyebilirsiniz", 5000)
        except Exception as e:
            # Fall back to yt-dlp cookiesfrombrowser only
            self.cookies_path = None
            self.statusBar().showMessage(f"Cookies okunamadı ({choice}): {e}", 6000)

    def _clear(self):
        self.url_edit.clear()
        self.progress.setValue(0)

    def _append_recent(self, text: str, status: str = "pending"):
        # status: pending/success/error/active
        item = QListWidgetItem(text)
        if status == "success":
            item.setForeground(QBrush(QColor("#1a7f37")))
            item.setText("✓ " + text)
        elif status == "error":
            item.setForeground(QBrush(QColor("#b3261e")))
            item.setText("✗ " + text)
        elif status == "active":
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            item.setText("▶ " + text)
        self.recent_list.insertItem(0, item)
        # remove cap: keep all items, enable scrolling

    def _update_active_item(self, title: str, percent: float):
        if self.recent_list.count() == 0:
            return
        item = self.recent_list.item(0)
        base = title or item.text().lstrip("▶ ✓ ✗ ")
        item.setText(f"▶ {base} ({percent:.0f}%)")

    def _start_download(self):
        if self.worker and self.worker.isRunning():
            return
        url = self.url_edit.text().strip()
        # Basic validation to avoid accidentally pasting error text
        if not (url.startswith("http://") or url.startswith("https://")):
            self.statusBar().showMessage("Geçerli bir bağlantı girin (http/https)", 4000)
            return
        if url.lower().startswith("error:"):
            self.statusBar().showMessage("Hata metni URL değildir, lütfen gerçek bağlantıyı girin", 5000)
            return
        # Optional domain guard for YouTube links
        allowed = ("youtube.com/", "youtu.be/")
        if not any(p in url.lower() for p in allowed):
            self.statusBar().showMessage("YouTube bağlantısı bekleniyor", 4000)
            return
        if not url:
            self.statusBar().showMessage("Lütfen bir bağlantı girin", 3000)
            return
        mode = "mp4" if self.mode_group.checkedId() == 1 else "mp3"
        root = self.root_edit.text().strip() or DEFAULT_ROOT
        title_for_list = url
        self._begin_download(url, mode, root)

    def _begin_download(self, url: str, mode: str, root: str):
        # Save params for resume
        selected_max = int(self.maxres_combo.currentData()) if self.maxres_combo.currentData() is not None else 1080
        self._last_params = {
            "url": url,
            "mode": mode,
            "root": root,
            "max_height": selected_max,
            "cookies_path": self.cookies_path,
            "cookies_browser": self.cookies_browser,
            "ignore_archive": self.chk_ignore_archive.isChecked(),
        }
        self._append_recent(url, status="active")
        self.progress.setValue(0)
        self._run_stats = {"completed": 0, "skipped": []}
        self.worker = DownloadWorker(
            url,
            mode,
            root,
            self._last_params["max_height"],
            self._last_params["cookies_path"],
            self._last_params["cookies_browser"],
            ignore_archive=self._last_params["ignore_archive"],
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.file_done.connect(self._on_file_done)
        self.worker.finished.connect(self._on_finished)
        self.worker.skipped.connect(self._on_skipped)
        self.btn_download.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_resume.setEnabled(False)
        self.worker.start()

    def _stop_download(self):
        if self.worker and self.worker.isRunning():
            try:
                self.worker.stop()
                self.statusBar().showMessage("Durduruluyor...", 3000)
                # User will be able to resume once finished signal arrives
                self.btn_stop.setEnabled(False)
            except Exception:
                pass

    def _resume_download(self):
        if self.worker and self.worker.isRunning():
            self.statusBar().showMessage("Devam etmek için önce indirmeyi durdurun", 4000)
            return
        if not self._last_params:
            self.statusBar().showMessage("Devam edecek bir işlem bulunamadı", 4000)
            return
        self.btn_resume.setEnabled(False)
        self.btn_download.setEnabled(False)
        self.statusBar().showMessage("Devam başlatılıyor... (bitmişler atlanacak)", 4000)
        # Force using archive (do NOT ignore) so bitenler atlanır, yarım kalan baştan başlar
        old_ignore = self.chk_ignore_archive.isChecked()
        try:
            if old_ignore:
                self.chk_ignore_archive.setChecked(False)
            self._begin_download(
                self._last_params["url"],
                self._last_params["mode"],
                self._last_params["root"],
            )
        finally:
            # Restore user's checkbox preference in UI (worker already took a snapshot)
            if old_ignore:
                self.chk_ignore_archive.setChecked(True)

    def _on_progress(self, percent: float, speed: str, eta: str, title: str):
        self.progress.setValue(int(percent))
        self._update_active_item(title or "İndiriliyor", percent)
        self.statusBar().showMessage(f"{speed} | ETA: {eta}")

    def _on_file_done(self, filename: str):
        # Insert the saved filename just under the active item
        base = os.path.basename(filename)
        item = QListWidgetItem("✓ " + base)
        item.setForeground(QBrush(QColor("#1a7f37")))
        insert_at = 1 if self.recent_list.count() > 0 else 0
        self.recent_list.insertItem(insert_at, item)
        # remove cap: keep all items, enable scrolling
        # update stats
        try:
            self._run_stats["completed"] += 1
        except Exception:
            pass

    def _on_finished(self, success: bool, message: str):
        if self.recent_list.count() > 0:
            item0 = self.recent_list.takeItem(0)
            base = item0.text().lstrip("▶ ✓ ✗ ")
            if success:
                self._append_recent(base, status="success")
                self.statusBar().showMessage("Tamamlandı", 4000)
            else:
                if (message or "").lower().startswith("cancelled by user"):
                    self._append_recent(base, status="error")
                    self.statusBar().showMessage("Durduruldu", 4000)
                else:
                    self._append_recent(base, status="error")
                    self.statusBar().showMessage(f"Hata: {message}", 7000)
                    # Show full copyable error dialog and copy to clipboard
                    try:
                        from PySide6.QtGui import QGuiApplication
                        QGuiApplication.clipboard().setText(message or "")
                    except Exception:
                        pass
                    mb = QMessageBox(self)
                    mb.setWindowTitle("İndirme Hatası")
                    mb.setIcon(QMessageBox.Critical)
                    mb.setText("Bir hata oluştu.")
                    # Read log tail and attach to details
                    log_tail = self._read_log_tail(60)
                    info_text = "Hata metni panoya kopyalandı. Son log satırları aşağıda."
                    details = (message or "")
                    if log_tail:
                        details += "\n\n--- Log (son 60 satır) ---\n" + log_tail
                    mb.setInformativeText(info_text)
                    mb.setDetailedText(details)
                    mb.addButton("Tamam", QMessageBox.AcceptRole)
                    mb.exec()
        # Reset states
        self.progress.setValue(0)
        self.worker = None
        # buttons state after finish
        self.btn_download.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_resume.setEnabled(self._last_params is not None)
        # Show summary dialog for this run
        self._show_summary_dialog()

    def _on_skipped(self, msg: str):
        # Show last 10 skipped reasons; color as error
        text = msg.strip()
        if not text:
            return
        item = QListWidgetItem(text)
        item.setForeground(QBrush(QColor("#b3261e")))
        self.skipped_list.insertItem(0, item)
        while self.skipped_list.count() > 10:
            self.skipped_list.takeItem(self.skipped_list.count() - 1)
        # record to stats (parsed)
        parsed = self._parse_skip_message(text)
        self._run_stats["skipped"].append(parsed)

    def _read_log_tail(self, max_lines: int = 60) -> str:
        """Read last max_lines from the persistent log file safely."""
        try:
            path = DownloadWorker.get_log_path()
            if not os.path.exists(path):
                return ""
            # Efficient tail: read whole file since it's a small app log; okay for now
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            tail = "".join(lines[-max_lines:])
            return tail.strip()
        except Exception:
            return ""

    # --- helpers for summary ---
    def _parse_skip_message(self, text: str) -> dict:
        try:
            import re
            vid = None
            reason = text
            m = re.search(r"\[youtube\]\s+([A-Za-z0-9_-]{6,})[: ]\s*(.*)", text)
            if m:
                vid = m.group(1)
                if m.group(2):
                    reason = m.group(2)
            # normalize some common reasons
            lowers = reason.lower()
            if "private" in lowers:
                reason = "Private video"
            elif "members only" in lowers:
                reason = "Members only"
            elif "no video formats" in lowers or "no formats" in lowers:
                reason = "No downloadable formats"
            elif "http error 403" in lowers:
                reason = "HTTP 403"
            elif "unavailable" in lowers:
                reason = "Unavailable"
            return {"id": vid or "?", "reason": reason, "raw": text}
        except Exception:
            return {"id": "?", "reason": text, "raw": text}

    def _show_summary_dialog(self):
        try:
            total_completed = int(self._run_stats.get("completed", 0))
            skipped_list = list(self._run_stats.get("skipped", []))
            total_skipped = len(skipped_list)
            if total_completed == 0 and total_skipped == 0:
                return
            # Build summary text
            summary = []
            summary.append(f"Tamamlanan: {total_completed}")
            summary.append(f"Atlanan: {total_skipped}")
            # show up to 10 skipped with id + reason
            if total_skipped:
                summary.append("")
                summary.append("Atlanan örnekleri (ilk 10):")
                for s in skipped_list[:10]:
                    summary.append(f"- {s.get('id')} : {s.get('reason')}")
            # path to archive
            from .downloader import DownloadWorker
            arch_path = os.path.join(os.path.dirname(DownloadWorker.get_log_path()), "download_archive.txt")
            summary.append("")
            summary.append(f"Arşiv: {arch_path}")

            mb = QMessageBox(self)
            mb.setWindowTitle("Özet")
            mb.setIcon(QMessageBox.Information)
            mb.setText("İndirme Özeti")
            mb.setInformativeText("Bu oturumun kısa özeti aşağıda.")
            mb.setDetailedText("\n".join(summary))
            mb.addButton("Tamam", QMessageBox.AcceptRole)
            mb.exec()
        except Exception:
            pass

    def _open_log(self):
        import subprocess, sys
        log_path = DownloadWorker.get_log_path()
        # Ensure file exists
        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            if not os.path.exists(log_path):
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write("")
        except Exception:
            pass
        # Open with default editor
        try:
            if sys.platform == "win32":
                os.startfile(log_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", log_path])
            else:
                subprocess.Popen(["xdg-open", log_path])
        except Exception:
            try:
                subprocess.Popen([sys.executable, "-m", "pydoc", log_path])
            except Exception:
                QMessageBox.information(self, "Log", f"Log dosyası: {log_path}")


    def _apply_styles(self):
        # Global button base + hover/pressed; then role-based overrides
        self.setStyleSheet(
            """
            QPushButton {
                background-color: #293133;
                color: #ffffff;
                border: 1px solid #3a3f41;
                border-radius: 8px;
                padding: 7px 14px;
            }
            QPushButton:hover {
                background-color: #323a3c;
                border-color: #4a5457;
            }
            QPushButton:pressed {
                background-color: #202628;
                border-color: #5a666a;
            }

            /* Primary (Download) - professional green */
            #btnPrimary { background-color: #2e7d32; border-color: #276b2b; }
            #btnPrimary:hover { background-color: #276b2b; border-color: #225e26; }
            #btnPrimary:pressed { background-color: #1f5822; border-color: #1a4a1d; }

            /* Accent (Resume) - lighter green */
            #btnAccent { background-color: #27ae60; border-color: #219653; }
            #btnAccent:hover { background-color: #219653; border-color: #1e874b; }
            #btnAccent:pressed { background-color: #1e874b; border-color: #1a7742; }

            /* Danger (Stop) */
            #btnDanger { background-color: #dc3545; border-color: #bb2d3b; }
            #btnDanger:hover { background-color: #bb2d3b; border-color: #a52834; }
            #btnDanger:pressed { background-color: #a52834; border-color: #8f222d; }

            /* Secondary / Utility */
            #btnSecondary { background-color: #4b5a4e; border-color: #425044; }
            #btnSecondary:hover { background-color: #425044; border-color: #3b473d; }
            #btnSecondary:pressed { background-color: #39463c; border-color: #333e35; }

            /* Exit */
            #btnExit { background-color: #5f6f61; border-color: #55645a; }
            #btnExit:hover { background-color: #55645a; border-color: #4d5a51; }
            #btnExit:pressed { background-color: #4c5a50; border-color: #455148; }
            """
        )

    def _resolve_app_icon(self) -> Optional[QIcon]:
        try:
            # 1) PyInstaller bundle temp
            meipass = getattr(sys, "_MEIPASS", None)
            if meipass:
                p1 = os.path.join(meipass, "icon_video.ico")
                p2 = os.path.join(meipass, "icon_video.png")
                if os.path.exists(p1):
                    return QIcon(p1)
                if os.path.exists(p2):
                    return QIcon(p2)
            # 2) Next to executable
            exe_dir = os.path.dirname(sys.executable) if hasattr(sys, "executable") else None
            if exe_dir:
                p1 = os.path.join(exe_dir, "icon_video.ico")
                p2 = os.path.join(exe_dir, "icon_video.png")
                if os.path.exists(p1):
                    return QIcon(p1)
                if os.path.exists(p2):
                    return QIcon(p2)
            # 3) Package relative (dev)
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            p1 = os.path.join(base, "icon_video.ico")
            p2 = os.path.join(base, "icon_video.png")
            if os.path.exists(p1):
                return QIcon(p1)
            if os.path.exists(p2):
                return QIcon(p2)
        except Exception:
            pass
        return None


def run_app():
    app = QApplication.instance() or QApplication([])
    # Set a global app icon so the taskbar also shows it
    try:
        from PySide6.QtGui import QIcon as _QIcon
        # Build-time/package-time paths
        meipass = getattr(sys, "_MEIPASS", None)
        candidates = []
        if meipass:
            candidates += [os.path.join(meipass, "icon_video.ico"), os.path.join(meipass, "icon_video.png")]
        exe_dir = os.path.dirname(sys.executable) if hasattr(sys, "executable") else None
        if exe_dir:
            candidates += [os.path.join(exe_dir, "icon_video.ico"), os.path.join(exe_dir, "icon_video.png")]
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        candidates += [os.path.join(base, "icon_video.ico"), os.path.join(base, "icon_video.png")]
        for p in candidates:
            if os.path.exists(p):
                app.setWindowIcon(_QIcon(p))
                break
    except Exception:
        pass
    w = MainWindow()
    w.show()
    return app.exec()
