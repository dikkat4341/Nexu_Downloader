#!/usr/bin/env python3
"""
NexusDownloader - Portable Video Downloader
Tamamen portable, anti-detection özellikli indirme programı
"""

import sys
import os
import asyncio
from pathlib import Path

# Portable olması için
if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys.executable).parent
else:
    APP_DIR = Path(__file__).parent

os.chdir(APP_DIR)

# Config klasörleri oluştur
for folder in ['Config', 'Downloads', 'Temp', 'Logs']:
    (APP_DIR / folder).mkdir(exist_ok=True)

from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.core.downloader import DownloadManager
from src.utils.config import ConfigManager

class NexusDownloader:
    def __init__(self):
        self.config = ConfigManager()
        self.download_manager = DownloadManager()
        self.app = QApplication(sys.argv)
        self.window = MainWindow(self.download_manager, self.config)
        
    def run(self):
        self.window.show()
        return self.app.exec()

if __name__ == "__main__":
    downloader = NexusDownloader()
    sys.exit(downloader.run())
