#!/usr/bin/env python3
"""
NexusDownloader için EXE build script
CI/CD için optimize edilmiş versiyon
"""

import os
import sys
import shutil
import subprocess
import json
import argparse
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description='Build NexusDownloader')
    parser.add_argument('--mode', choices=['dev', 'ci', 'portable'], 
                       default='dev', help='Build mode')
    parser.add_argument('--output', type=str, default='dist',
                       help='Output directory')
    return parser.parse_args()

def setup_environment():
    """Build ortamını hazırla"""
    print("Setting up build environment...")
    
    # Gerekli dizinleri oluştur
    Path("data").mkdir(exist_ok=True)
    Path("Config").mkdir(exist_ok=True)
    Path("Downloads").mkdir(exist_ok=True)
    
    # Gerekli dosyaları oluştur
    create_default_files()

def create_default_files():
    """Varsayılan dosyaları oluştur"""
    
    # user_agents.json
    default_agents = {
        "custom": [],
        "default": [
            {
                "name": "Windows Chrome",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "platform": "Windows",
                "accept_language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
            }
        ]
    }
    
    agents_file = Path("data/user_agents.json")
    if not agents_file.exists():
        with open(agents_file, 'w', encoding='utf-8') as f:
            json.dump(default_agents, f, indent=2, ensure_ascii=False)
    
    # config.json
    default_config = {
        "theme": "dark",
        "concurrent_downloads": 4,
        "version": "1.0.0"
    }
    
    config_file = Path("data/config.json")
    if not config_file.exists():
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)

def clean_build_dirs():
    """Build dizinlerini temizle"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path, ignore_errors=True)
            print(f"Cleaned: {dir_name}")

def build_with_pyinstaller(mode='dev'):
    """PyInstaller ile build yap"""
    
    print(f"\nBuilding with PyInstaller (mode: {mode})...")
    
    # PyInstaller komutunu oluştur
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=NexusDownloader",
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
    ]
    
    # Icon ekle (varsa)
    if Path("icon.ico").exists():
        cmd.append("--icon=icon.ico")
    
    # Data files
    cmd.extend(["--add-data", "data;data"])
    cmd.extend(["--add-data", "src;src"])
    
    # Hidden imports
    hidden_imports = [
        'yt_dlp', 'aiohttp', 'aiohttp.client', 'aiohttp.client_reqrep',
        'PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
        'libtorrent', 'cryptography', 'requests', 'bs4', 'lxml',
        'm3u8', 'psutil', 'pythonmagic', 'Crypto', 'socks'
    ]
    
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])
    
    # Collect all for large packages
    cmd.extend(["--collect-all", "yt_dlp"])
    cmd.extend(["--collect-all", "aiohttp"])
    
    # Main script
    cmd.append("main.py")
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Build output:", result.stdout)
        
        if result.returncode == 0:
            print("\n✓ Build successful!")
            return True
        else:
            print("\n✗ Build failed!")
            print("Error:", result.stderr)
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build error: {e}")
        print("Stdout:", e.stdout)
        print("Stderr:", e.stderr)
        return False

def create_portable_package(exe_path, output_dir='.'):
    """Portable paket oluştur"""
    
    print("\nCreating portable package...")
    
    portable_dir = Path(output_dir) / "NexusDownloader_Portable"
    
    # Eski paketi temizle
    if portable_dir.exists():
        shutil.rmtree(portable_dir, ignore_errors=True)
    
    portable_dir.mkdir(parents=True, exist_ok=True)
    
    # EXE'yi kopyala
    if exe_path.exists():
        shutil.copy2(exe_path, portable_dir / "NexusDownloader.exe")
        print(f"✓ Copied EXE to portable package")
    else:
        print(f"✗ EXE not found: {exe_path}")
        return None
    
    # Gerekli dosyaları oluştur
    create_readme(portable_dir)
    create_license(portable_dir)
    create_ffmpeg_notes(portable_dir)
    
    # ZIP oluştur
    zip_path = Path(output_dir) / "NexusDownloader_Portable.zip"
    
    # Eski ZIP'i sil
    if zip_path.exists():
        zip_path.unlink()
    
    # Yeni ZIP oluştur
    shutil.make_archive(
        str(zip_path.with_suffix('')),  # .zip extension olmadan
        'zip',
        portable_dir
    )
    
    # Temizlik
    shutil.rmtree(portable_dir, ignore_errors=True)
    
    print(f"✓ Portable package created: {zip_path}")
    print(f"  Size: {zip_path.stat().st_size / (1024*1024):.2f} MB")
    
    return zip_path

def create_readme(output_dir):
    """README.txt oluştur"""
    readme_content = """NEXUSDOWNLOADER v1.0
====================

Portable Video Downloader

ÖZELLİKLER:
✓ Tamamen portable (kurulum gerekmez)
✓ HTTP/HTTPS/M3U8/Torrent desteği
✓ YouTube indirme
✓ User-Agent rotasyonu
✓ Anti-detection sistemi
✓ Gece/Gündüz modu

KULLANIM:
1. NexusDownloader.exe'yi çalıştırın
2. URL ekleyin veya dosya seçin
3. İndirmeyi başlatın

NOTLAR:
- FFmpeg kurulu değilse video birleştirme çalışmaz
- Config klasörü otomatik oluşur
- İndirmeler Downloads klasörüne kaydedilir

GitHub: https://github.com/yourusername/NexusDownloader
"""
    
    with open(output_dir / "README.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)

def create_license(output_dir):
    """LICENSE.txt oluştur"""
    license_content = """MIT License

Copyright (c) 2024 NexusDownloader

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    
    with open(output_dir / "LICENSE.txt", "w", encoding="utf-8") as f:
        f.write(license_content)

def create_ffmpeg_notes(output_dir):
    """FFmpeg notlarını oluştur"""
    notes = """FFMPEG KURULUMU
===============

NexusDownloader video birleştirme için FFmpeg'e ihtiyaç duyar.

1. FFmpeg'i indirin: https://ffmpeg.org/download.html
2. ffmpeg.exe'yi şuraya kopyalayın:
   - NexusDownloader.exe ile aynı dizine
   VEYA
   - Sistem PATH'inize ekleyin

Windows için:
- https://github.com/BtbN/FFmpeg-Builds/releases adresinden
- ffmpeg-master-latest-win64-gpl.zip indirin
- ZIP'i açın, bin klasöründeki ffmpeg.exe'yi kopyalayın
"""
    
    with open(output_dir / "FFMPEG_NOTES.txt", "w", encoding="utf-8") as f:
        f.write(notes)

def main():
    """Ana fonksiyon"""
    args = parse_args()
    
    print("="*60)
    print("NEXUSDOWNLOADER BUILD SCRIPT")
    print("="*60)
    
    # Ortamı hazırla
    setup_environment()
    
    # Temizlik
    clean_build_dirs()
    
    # Build
    success = build_with_pyinstaller(args.mode)
    
    if success:
        exe_path = Path("dist") / "NexusDownloader.exe"
        
        if exe_path.exists():
            print(f"\n✓ EXE created successfully!")
            print(f"  Location: {exe_path}")
            print(f"  Size: {exe_path.stat().st_size / (1024*1024):.2f} MB")
            
            # Portable paket oluştur
            if args.mode in ['ci', 'portable']:
                zip_path = create_portable_package(exe_path, ".")
                if zip_path:
                    print(f"\n✓ Build completed!")
                    print(f"  EXE: {exe_path}")
                    print(f"  Portable: {zip_path}")
        else:
            print(f"\n✗ EXE not found at: {exe_path}")
            return 1
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
