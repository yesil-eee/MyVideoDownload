# Windows Portable EXE Oluşturma Rehberi

Bu rehber, MyVideoDownload uygulamasının Windows için portable exe dosyasını oluşturmak için adım adım talimatlar içerir.

## Gerekli Yazılımlar

- **Windows 10/11** (64-bit önerilir)
- **Python 3.11+** ([python.org](https://www.python.org/downloads/) adresinden indirin)
- **Git** (isteğe bağlı, repo klonlamak için)

## Adım 1: Python'u Yükleyin

1. [python.org](https://www.python.org/downloads/) adresinden Python 3.11 veya daha yenisini indirin
2. Kurulum sırasında **"Add Python to PATH"** seçeneğini işaretleyin
3. **Install Now** butonuna tıklayın

## Adım 2: Projeyi Klonlayın

### Git kullanarak:
```bash
git clone https://github.com/yesil-eee/MyVideoDownload.git
cd MyVideoDownload/MyVideoDownload
```

### Veya manuel olarak:
1. GitHub'da [MyVideoDownload](https://github.com/yesil-eee/MyVideoDownload) sayfasına gidin
2. **Code** → **Download ZIP** seçin
3. ZIP dosyasını çıkartın ve klasöre girin

## Adım 3: Sanal Ortam Oluşturun

PowerShell veya Command Prompt'ta aşağıdaki komutları çalıştırın:

```bash
# Sanal ortam oluştur
python -m venv venv

# Sanal ortamı etkinleştir (PowerShell)
.\venv\Scripts\Activate.ps1

# Veya Command Prompt için:
venv\Scripts\activate.bat
```

## Adım 4: Gerekli Paketleri Yükleyin

```bash
# PyInstaller yükle
pip install pyinstaller

# Proje bağımlılıklarını yükle
pip install -r requirements.txt
```

## Adım 5: Spec Dosyasını Oluşturun

Proje klasöründe `build.spec` adlı bir dosya oluşturun ve aşağıdaki içeriği yapıştırın:

```python
# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for MyVideoDownload
Generates a portable Windows executable
"""

a = Analysis(
    ['myvideodownload/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'yt_dlp',
        'browser_cookie3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VideoDownload',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../icon_video2.ico',
)
```

## Adım 6: EXE Dosyasını Derleyin

Sanal ortam etkinken aşağıdaki komutu çalıştırın:

```bash
pyinstaller build.spec
```

Derlemesi tamamlanana kadar bekleyin (5-15 dakika, internet hızınıza bağlı).

## Adım 7: EXE Dosyasını Bulun

Derleme tamamlandığında, exe dosyası şu konumda olacaktır:

```
MyVideoDownload\MyVideoDownload\dist\VideoDownload.exe
```

## Adım 8: EXE Dosyasını Test Edin

1. `dist` klasöründe `VideoDownload.exe` dosyasını çift tıklayın
2. Uygulama açılmalı ve normal şekilde çalışmalıdır
3. YouTube URL'si girerek test edin

## Adım 9: EXE Dosyasını Dağıtın

Oluşturulan `VideoDownload.exe` dosyasını:
- Kullanıcılara doğrudan gönderebilirsiniz
- Web sitenizde yayınlayabilirsiniz
- GitHub Releases'te yayınlayabilirsiniz

## Sorun Giderme

### "ModuleNotFoundError: No module named 'PySide6'"
```bash
# Sanal ortamın etkinleştirildiğinden emin olun
pip install PySide6
```

### "PyInstaller not found"
```bash
pip install pyinstaller
```

### "Icon file not found"
- `icon_video2.ico` dosyasının proje klasöründe olduğundan emin olun
- Spec dosyasında icon yolunu kontrol edin

### EXE dosyası çalışmıyor
- Sanal ortamda `python myvideodownload/__main__.py` komutunu çalıştırarak uygulamayı test edin
- Hata mesajlarını kontrol edin

### EXE dosyası çok büyük (75+ MB)
- Bu normal bir durumdur çünkü tüm bağımlılıklar ve Python runtime dahil edilir
- `--onefile` seçeneği kullanıldığında boyut daha da büyük olabilir

## Boyutu Azaltma

EXE dosyasının boyutunu azaltmak için:

1. Spec dosyasında `excludedimports` bölümüne kullanılmayan modülleri ekleyin
2. UPX sıkıştırmasını etkinleştirin (Windows'ta otomatik olarak etkindir)
3. `--onedir` seçeneğini kullanın (daha hızlı yükleme, daha küçük dosya)

## Gelişmiş: Installer Oluşturma

Inno Setup kullanarak Windows installer oluşturmak için:

1. [Inno Setup](https://jrsoftware.org/isdl.php) indirin ve yükleyin
2. Proje klasöründe bulunan `installer.iss` dosyasını açın
3. Gerekli yolları güncelleyin
4. **Build** → **Compile** seçin

## İleri Seviye: Otomatik Derleme

GitHub Actions kullanarak otomatik olarak EXE derlemek için:

`.github/workflows/build-exe.yml` dosyası oluşturun:

```yaml
name: Build Windows EXE

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: |
          cd MyVideoDownload
          pip install pyinstaller -r requirements.txt
          pyinstaller build.spec
      - uses: actions/upload-artifact@v2
        with:
          name: VideoDownload.exe
          path: MyVideoDownload/dist/VideoDownload.exe
```

## Daha Fazla Bilgi

- [PyInstaller Belgeleri](https://pyinstaller.org/)
- [PySide6 Belgeleri](https://doc.qt.io/qtforpython/)
- [yt-dlp Belgeleri](https://github.com/yt-dlp/yt-dlp)
