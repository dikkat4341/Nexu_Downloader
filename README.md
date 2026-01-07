# NexusDownloader - Portable Video Downloader

![GitHub Actions Workflow](https://github.com/dikkat4341/NexusDownloader/actions/workflows/build-release.yml/badge.svg)
![GitHub release](https://img.shields.io/github/v/release/dikkat4341/NexusDownloader)
![License](https://img.shields.io/github/license/dikkat4341/NexusDownloader)

Tamamen portable, anti-detection özellikli video indirme programı.

## 📥 Download

[![Download EXE](https://img.shields.io/badge/Download-EXE-blue)](https://github.com/dikkat4341/NexusDownloader/releases/latest/download/NexusDownloader.exe)
[![Download Portable](https://img.shields.io/badge/Download-Portable_ZIP-green)](https://github.com/dikkat4341/NexusDownloader/releases/latest/download/NexusDownloader_Portable.zip)

**Latest Release:** [v1.0.0](https://github.com/dikkat4341/NexusDownloader/releases/latest)

## ✨ Özellikler

- ✅ **Portable**: Tek EXE, kurulum gerekmez
- ✅ **Multi-protocol**: HTTP/HTTPS/M3U8/Torrent/YouTube
- ✅ **Anti-detection**: User-Agent rotasyonu, header spoofing
- ✅ **Smart**: Gece modu, hız sınırlama
- ✅ **Modern UI**: Koyu/açık tema, system tray
- ✅ **Batch download**: Çoklu indirme, kuyruk yönetimi

## 🚀 Kullanım

1. [Releases](https://github.com/dikkat4341/NexusDownloader/releases) sayfasından indirin
2. `NexusDownloader.exe` çalıştırın
3. URL ekleyin veya dosya seçin
4. İndirmeyi başlatın

## 🔧 Geliştirme

### Gereksinimler
- Python 3.10+
- FFmpeg (video birleştirme için)

### Kurulum
```bash
# Repository'yi klonla
git clone https://github.com/dikkat4341/NexusDownloader.git
cd NexusDownloader

# Gereksinimleri yükle
pip install -r requirements.txt

# Çalıştır
python main.py
