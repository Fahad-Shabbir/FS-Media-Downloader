# FS Media Downloader - Liquid Glass Edition

**Author & Creator:** Fahad Shabbir  
A modern Windows desktop application to download videos and audio from **YouTube, X (Twitter), Facebook, Instagram, TikTok, Reddit, Twitch, Vimeo, SoundCloud, and 1,000+ popular websites** wrapped in a pure **Liquid Glass (Glassmorphic)** user interface.

---

## ✨ Features

### 🪟 Authentic Liquid Glass UI & Swift Animations
- **Hardware-Accelerated Frosted Glass**: True `backdrop-filter: blur(28px) saturate(180%)` with 1px luminous specular refraction borders.
- **Organic Metaball Fluid Canvas**: Background pulsating glowing aurora orbs that morph asymmetrically with viscous fluid blending.
- **🍮 Jelly-Elastic Glider Pills**: Snappy rubber-band spring curves (`cubic-bezier(0.34, 1.56, 0.64, 1)`) for tab and format selectors.
- **💎 3D Glass Tilt & Caustic Glare**: Interactive perspective tilt and specular light tracking your mouse.
- **🏄 Sloshing Liquid Wave Progress Bar**: Dual-layer sinusoidal wave crests with horizontal surface shimmer.
- **🌓 Dual Mode Switching**: One-click toggle between **Liquid Cosmic Midnight** (Dark) and **Frosted Ice Opal** (Light).

### 🎬 Media Engine
- **Multi-Platform Support**: YouTube, X (Twitter), Facebook, Instagram, TikTok, Reddit, Twitch, Vimeo, SoundCloud, and 1000+ sites.
- **Single URL Mode**: Full preview card (thumbnail, duration, platform chip), dynamic resolutions up to 4K / 2K / 1080p, MP3 (320 kbps), and lossless WAV (PCM).
- **Playlist & Bulk Queue**: Paste full playlists or multi-URL lists across multiple platforms into a single unified queue.
- **⚡ Turbo 8x Accelerator**: Parallel multi-threaded fragment download acceleration.
- **⏸️ Pause / Resume & 🛑 Cancel**: Live in-progress streaming controls with paused amber state and immediate safe abort.
- **🍪 Anti-Bot Bypass**: Quick importer for `cookies.txt` to bypass YouTube's *"Sign in to confirm you're not a bot"*.
- **🔄 In-App Updates**: One-click updates for the yt-dlp core engine from PyPI wheels and the application from GitHub releases.

---

## 💻 Installation & Running from Source

```powershell
# 1. Clone repository
git clone https://github.com/Fahad-Shabbir/FS-Media-Downloader.git
cd "FS-Media-Downloader"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch App
python app.py
```

---

## 📦 Building Standalone Executable & Installer

### 1. Build Standalone Executable (.exe)
To bundle the entire app into a single standalone `.exe` (includes Python, FFmpeg, and all Liquid Glass UI assets):
```powershell
build_exe.bat
```
The output file will be generated in `dist\FS Media Downloader.exe`.

### 2. Build Windows Installer (Inno Setup)
To generate the Windows Setup installer:
```powershell
build_installer.bat
```
The output file will be generated in `installer_output\FS_Media_Downloader_Setup_v1.0.0.exe`.

---

## 📄 License & Attribution
Designed & Developed with ❤️ by **Fahad Shabbir**.
