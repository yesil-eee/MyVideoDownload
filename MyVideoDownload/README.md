# My Video Download

Türkçe arayüzlü basit bir YouTube/Playlist indirici.

Özellikler:
- MP4 video veya MP3 ses indirme
- Çözünürlük kuralı: 1080p > 720p > 480p; 480p altı ve 1080p üstü indirilmeyecek
- Playlist veya tek video desteği
- Klasörleme: Playlist adı alt klasör; tek video için `Video/`
- Dosya adı şablonu: `%(autonumber)03d - %(playlist_title|Video)s - %(title)s`
- Son 5 öğe listesi (bitti: yeşil onay, hata: kırmızı) ve aktif indirme ilerlemesi
- Cookies desteği: `cookies.txt` seçilebilir (isteğe bağlı)

Gereksinimler (geliştirme):
- Python 3.10+
- `pip install -r requirements.txt`

Çalıştırma:
```bash
python -m myvideodownload
```

Notlar:
- ffmpeg sistemde yoksa, uygulama içindeki `ffmpeg` klasörünü (exe dosyaları) kullanmayı dener.
- Portable EXE ve Setup paketleri sonraki adımda hazırlanacaktır (PyInstaller + Inno Setup).
