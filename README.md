Aşağıda metnin Türkçe çevirisi yer alıyor:


---

MyVideoDownload

MyVideoDownload, Python ve PySide6 ile geliştirilmiş, yt-dlp altyapısını kullanan bir Windows masaüstü YouTube video/playlist indiricisidir.
Temiz bir devam etme (resume) mantığı sunar (mevcut öğe baştan başlar, tamamlananlar arşiv sayesinde atlanır), maksimum çözünürlük seçimi, çerez (cookies) desteği ve ffmpeg içeren taşınabilir/kurulumlu paketler sağlar.

Özellikler

Maksimum çözünürlük seçici (2160p .. 144p)

Video (MP4) veya Ses (MP3) indirme

Durdur ve Devam Et butonları
(Devam et: mevcut öğeyi baştan başlatır; tamamlananlar .download-archive.txt sayesinde atlanır)

Sağlam format seçimi ve istemci (client) yedekleri ile yt-dlp kullanımı

Dosyadan çerez kullanımı veya tarayıcıdan içe aktarma (opsiyonel)

ffmpeg otomatik algılama (derleme paketleriyle birlikte gelir)

Kalıcı loglar: %LOCALAPPDATA%/MyVideoDownload/logs/app.log

Taşınabilir ve Kurulum paketleri (PyInstaller + Inno Setup)


Proje Yapısı

MyVideoDownload/myvideodownload/ — uygulama kaynak kodu (UI ve indirici)

MyVideoDownload/dist/ — taşınabilir derleme çıktısı (gitignored)

MyVideoDownload/Output/ — kurulum çıktısı (gitignored)

ffmpeg/ — paketleme için yerel ffmpeg ikilileri (gitignored)


Geliştirme

Windows üzerinde Python 3.10+ gerektirir.

# (opsiyonel) sanal ortam oluştur
python -m venv .venv
.venv\Scripts\Activate.ps1

# bağımlılıkları kur
pip install -U pip
pip install PySide6 yt-dlp browser-cookie3

# uygulamayı çalıştır
python -m MyVideoDownload.myvideodownload

Derleme (Taşınabilir ve Kurulum)

# Taşınabilir (PyInstaller)
.venv\Scripts\python.exe -m PyInstaller -y -n MyVideoDownload -w -i icon_video.ico --onedir MyVideoDownload\myvideodownload\__main__.py
# Gerekirse ffmpeg ve ikonları EXE’nin yanına kopyala
# Ardından Inno Setup ile kurulum paketini oluştur
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" MyVideoDownload\installer.iss

Kullanım İpuçları

Varsayılan indirme klasörü: C:\Video Download

Arşiv dosyası: seçilen kök klasör altında .download-archive.txt

Özel/listelenmemiş videolar için geçerli çerezler sağlayın
(cookies.txt veya tarayıcıdan içe aktarma)


Lisans

Tercih ettiğiniz lisansı (ör. MIT) LICENSE dosyası olarak ekleyin.

Katkıda Bulunanlar

Geliştirici: İlyas YEŞİL
PySide6 ve yt-dlp ile geliştirilmiştir.


---