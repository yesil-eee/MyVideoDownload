# Windows Installer (Setup.exe) Oluşturma Rehberi

Bu rehber, MyVideoDownload uygulamasının Windows installer dosyasını Inno Setup kullanarak oluşturmak için adım adım talimatlar içerir.

## Gerekli Yazılımlar

- **Windows 10/11** (64-bit)
- **Python 3.11+** ([python.org](https://www.python.org/downloads/))
- **Inno Setup 6+** ([jrsoftware.org](https://jrsoftware.org/isdl.php))

## Adım 1: Portable EXE Dosyasını Oluşturun

Öncelikle, portable EXE dosyasını oluşturmanız gerekir. `BUILD_EXE_WINDOWS.md` dosyasındaki talimatları izleyin.

```bash
cd MyVideoDownload
python -m venv venv
.\venv\Scripts\activate.ps1
pip install pyinstaller -r requirements.txt
pyinstaller build.spec
```

Tamamlandığında, `dist\VideoDownload\` klasöründe tüm dosyalar olmalıdır.

## Adım 2: Inno Setup'ı Yükleyin

1. [Inno Setup](https://jrsoftware.org/isdl.php) adresinden **Inno Setup 6.3.3** veya daha yenisini indirin
2. Setup dosyasını çalıştırın ve kurulum talimatlarını izleyin
3. Kurulum tamamlandığında, Inno Setup IDE başlatılacaktır

## Adım 3: Installer Script'ini Açın

1. Inno Setup IDE'de **File** → **Open** seçin
2. `MyVideoDownload\MyVideoDownload\installer.iss` dosyasını açın
3. Script dosyası IDE'de açılacaktır

## Adım 4: Installer'ı Derleyin

1. **Build** menüsünü açın
2. **Compile** seçin (veya **Ctrl+F9** tuşlarına basın)
3. Derlemesi başlayacaktır

**Not:** Derleme sırasında aşağıdaki uyarıları görebilirsiniz:
- "Warning: File not found: dist\VideoDownload\*" - Bu normal, dosyalar daha sonra eklenir
- "Warning: Icon file not found" - Icon dosyası bulunmazsa bu uyarı görülür

## Adım 5: Installer Dosyasını Bulun

Derleme tamamlandığında, installer dosyası şu konumda olacaktır:

```
MyVideoDownload\MyVideoDownload\Output\VideoDownloadSetup.exe
```

## Adım 6: Installer'ı Test Edin

1. `VideoDownloadSetup.exe` dosyasını çift tıklayın
2. Installer sihirbazı başlayacaktır
3. Kurulum adımlarını takip edin
4. Uygulama kurulduktan sonra, Başlat Menüsünde `Video Download` uygulamasını bulabilirsiniz

## Adım 7: Installer'ı Dağıtın

Oluşturulan `VideoDownloadSetup.exe` dosyasını:
- Kullanıcılara doğrudan gönderebilirsiniz
- Web sitenizde yayınlayabilirsiniz
- GitHub Releases'te yayınlayabilirsiniz

## Installer Özellikleri

Oluşturulan installer aşağıdaki özellikleri içerir:

| Özellik | Açıklama |
|---------|----------|
| **Dil Desteği** | Türkçe ve İngilizce |
| **Kurulum Konumu** | `C:\Program Files\Video Download` (varsayılan) |
| **Masaüstü Kısayolu** | İsteğe bağlı |
| **Başlat Menüsü** | Otomatik oluşturulur |
| **Kaldırma** | Kontrol Paneli'nden kaldırılabilir |
| **Sıkıştırma** | LZMA2 Ultra64 (en yüksek sıkıştırma) |

## Installer Dosyasını Özelleştirme

`installer.iss` dosyasını düzenleyerek installer'ı özelleştirebilirsiniz:

### Uygulama Bilgilerini Değiştirme

```ini
#define AppName "Video Download"
#define AppVersion "0.2.0"
#define AppPublisher "İlyas YEŞİL"
#define AppURL "https://github.com/yesil-eee/MyVideoDownload"
```

### Varsayılan Kurulum Konumunu Değiştirme

```ini
DefaultDirName={autopf}\{#AppName}
```

Seçenekler:
- `{autopf}` - Program Files (64-bit sistemlerde)
- `{pf}` - Program Files (32-bit)
- `{localappdata}` - AppData\Local
- `{userappdata}` - AppData\Roaming

### Kısayolları Değiştirme

```ini
[Tasks]
Name: "desktopicon"; Description: "Masaüstü kısayolu oluştur"; ...
```

### İkon Dosyasını Değiştirme

```ini
SetupIconFile=..\icon_video2.ico
UninstallDisplayIcon={app}\{#AppExeName}
```

## Sorun Giderme

### "File not found" Hatası

Eğer derleme sırasında "File not found" hatası alırsanız:

1. `dist\VideoDownload\` klasörünün var olduğundan emin olun
2. PyInstaller ile EXE dosyasını başarıyla derledikten sonra tekrar deneyin

### Installer Çalışmıyor

1. Installer dosyasını başka bir klasöre taşıyın
2. Yönetici olarak çalıştırmayı deneyin
3. Virüs tarayıcısının installer'ı engellemediğini kontrol edin

### Kurulum Sırasında Hata

1. Kurulum konumunun yazılabilir olduğundan emin olun
2. Yeterli disk alanı olduğunu kontrol edin
3. Antivirus yazılımını geçici olarak devre dışı bırakın

## İleri Seviye: Otomatik Derleme

GitHub Actions kullanarak otomatik installer derlemek için `.github/workflows/build-installer.yml` dosyası oluşturun:

```yaml
name: Build Windows Installer

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
      - name: Build EXE
        run: |
          cd MyVideoDownload
          python -m venv venv
          .\venv\Scripts\activate.ps1
          pip install pyinstaller -r requirements.txt
          pyinstaller build.spec
      - name: Build Installer
        uses: Miniontoby/Inno-Setup-Action@v1.2.2
        with:
          path: MyVideoDownload/installer.iss
      - name: Upload Installer
        uses: actions/upload-artifact@v2
        with:
          name: VideoDownloadSetup.exe
          path: MyVideoDownload/Output/VideoDownloadSetup.exe
```

## Installer Boyutu

Oluşturulan installer dosyası yaklaşık **50-80 MB** boyutunda olacaktır. Bu boyut:
- Python runtime (~30 MB)
- PySide6 kütüphanesi (~30 MB)
- yt-dlp ve diğer bağımlılıklar (~10 MB)
- Sıkıştırma ile azaltılmıştır

## Daha Fazla Bilgi

- [Inno Setup Belgeleri](https://jrsoftware.org/ishelp/)
- [Inno Setup Betik Referansı](https://jrsoftware.org/isinfo.php)
- [Inno Setup Örnekleri](https://jrsoftware.org/files/is/Example%20Scripts/)

## Lisans ve Telif Hakkı

Inno Setup ücretsiz yazılımdır ve ticari kullanım için de uygundur. Daha fazla bilgi için [Inno Setup Lisansı](https://jrsoftware.org/files/is/license.txt) sayfasını ziyaret edin.
