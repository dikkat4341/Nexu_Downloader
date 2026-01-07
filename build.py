#!/usr/bin/env python3
"""
NexusDownloader için EXE build script
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def build_exe():
    """PyInstaller ile EXE oluştur"""
    print("NexusDownloader EXE oluşturuluyor...")
    
    # Gereksinimleri kontrol et
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller kurulu değil! Kuruluyor...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Build klasörünü temizle
    build_dir = Path("build")
    dist_dir = Path("dist")
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # Spec dosyası oluştur
    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data/*.json', 'data'),
        ('src/**/*.py', 'src'),
    ],
    hiddenimports=[
        'yt_dlp',
        'aiohttp',
        'PySide6',
        'm3u8',
        'libtorrent',
        'cryptography',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NexusDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI uygulaması için False
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
"""
    
    # Spec dosyasını kaydet
    with open("nexus.spec", "w") as f:
        f.write(spec_content)
    
    # Build komutu
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "nexus.spec",
        "--onefile",  # Tek EXE dosyası
        "--noconsole",  # Console penceresi olmasın
        "--add-data", "data;data",  # Windows için
        "--add-data", "src;src",
        "--hidden-import", "yt_dlp",
        "--hidden-import", "aiohttp",
        "--hidden-import", "PySide6",
        "--hidden-import", "libtorrent",
        "--collect-all", "yt_dlp",
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✓ EXE oluşturuldu: dist/NexusDownloader.exe")
        
        # Portable yapı oluştur
        create_portable_package()
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build hatası: {e}")
        return False
    
    return True

def create_portable_package():
    """Portable paket oluştur"""
    print("\nPortable paket oluşturuluyor...")
    
    dist_dir = Path("dist")
    portable_dir = Path("NexusDownloader_Portable")
    
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    
    portable_dir.mkdir()
    
    # EXE'yi kopyala
    exe_src = dist_dir / "NexusDownloader.exe"
    exe_dest = portable_dir / "NexusDownloader.exe"
    shutil.copy2(exe_src, exe_dest)
    
    # Config klasörü oluştur
    config_dir = portable_dir / "Config"
    config_dir.mkdir()
    
    # Örnek config dosyaları
    default_config = {
        "theme": "dark",
        "concurrent_downloads": 4,
        "speed_limit": 0,
        "download_path": "Downloads",
        "night_mode": False,
        "night_hours": [23, 7]
    }
    
    import json
    with open(config_dir / "config.json", "w") as f:
        json.dump(default_config, f, indent=2)
    
    # User agents dosyası
    default_agents = {
        "custom": []
    }
    with open(config_dir / "user_agents.json", "w") as f:
        json.dump(default_agents, f, indent=2)
    
    # README dosyası
    readme = """# NexusDownloader Portable

Tamamen taşınabilir video indirme programı.

## Kullanım:
1. NexusDownloader.exe'yi çalıştırın
2. URL veya dosya ekleyin
3. İndirmeyi başlatın

## Özellikler:
- HTTP/HTTPS/M3U8/Torrent indirme
- Anti-detection sistemi
- Gece modu
- User-Agent rotasyonu
- Portable (kurulum gerekmez)

## Not:
- İlk çalıştırmada Config klasörü otomatik oluşur
- Downloads klasörü otomatik oluşur
- Tüm ayarlar Config klasöründe saklanır

GitHub: https://github.com/username/NexusDownloader
"""
    
    with open(portable_dir / "README.txt", "w", encoding="utf-8") as f:
        f.write(readme)
    
    # ZIP oluştur
    shutil.make_archive("NexusDownloader_Portable", "zip", portable_dir)
    
    print(f"✓ Portable paket oluşturuldu: NexusDownloader_Portable.zip")
    print(f"  Boyut: {os.path.getsize('NexusDownloader_Portable.zip') / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    build_exe()
