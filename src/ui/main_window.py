# src/ui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QProgressBar,
    QLabel, QFileDialog, QMenu, QSystemTrayIcon,
    QMessageBox, QGroupBox, QCheckBox, QSpinBox,
    QListWidget, QSplitter, QHeaderView, QStyleFactory
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QIcon, QAction, QFont
import asyncio
import json
from pathlib import Path

class DownloadWorker(QThread):
    """İndirme işlemleri için worker thread"""
    progress_signal = Signal(dict)
    finished_signal = Signal(dict)
    
    def __init__(self, download_manager, task_id):
        super().__init__()
        self.download_manager = download_manager
        self.task_id = task_id
    
    def run(self):
        # Asenkron işlem için event loop
        asyncio.run(self._download_task())
    
    async def _download_task(self):
        task = self.download_manager.get_task(self.task_id)
        if not task:
            return
        
        async for progress in task.download():
            self.progress_signal.emit(progress)
        
        self.finished_signal.emit({
            'task_id': self.task_id,
            'status': 'completed'
        })

class MainWindow(QMainWindow):
    def __init__(self, download_manager, config_manager):
        super().__init__()
        self.download_manager = download_manager
        self.config = config_manager
        self.download_workers = {}
        
        self.setup_ui()
        self.setup_tray()
        self.load_settings()
        
        # Auto-save timer
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_settings)
        self.save_timer.start(30000)  # 30 saniyede bir
        
    def setup_ui(self):
        self.setWindowTitle("NexusDownloader v1.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana layout
        main_layout = QVBoxLayout(central_widget)
        
        # Üst toolbar
        toolbar = self.create_toolbar()
        main_layout.addLayout(toolbar)
        
        # Splitter (sol panel + ana alan)
        splitter = QSplitter(Qt.Horizontal)
        
        # Sol panel (Favoriler/Kaydedilenler)
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Ana tab widget
        self.tab_widget = QTabWidget()
        
        # İndirme sekmesi
        download_tab = self.create_download_tab()
        self.tab_widget.addTab(download_tab, "İndirme")
        
        # Playlist sekmesi
        playlist_tab = self.create_playlist_tab()
        self.tab_widget.addTab(playlist_tab, "Playlist")
        
        # Ayarlar sekmesi
        settings_tab = self.create_settings_tab()
        self.tab_widget.addTab(settings_tab, "Ayarlar")
        
        splitter.addWidget(self.tab_widget)
        splitter.setSizes([250, 950])
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_label = QLabel("Hazır")
        self.status_bar.addPermanentWidget(self.status_label)
        
        # Tema
        self.apply_theme()
    
    def create_toolbar(self):
        """Üst toolbar oluştur"""
        layout = QHBoxLayout()
        
        # URL input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("URL girin (HTTP, HTTPS, M3U8, magnet, torrent)")
        self.url_input.returnPressed.connect(self.add_download)
        layout.addWidget(self.url_input, 3)
        
        # Dosya seç butonu
        file_btn = QPushButton("Dosya Seç")
        file_btn.clicked.connect(self.browse_file)
        layout.addWidget(file_btn)
        
        # Ekle butonu
        add_btn = QPushButton("Ekle")
        add_btn.clicked.connect(self.add_download)
        layout.addWidget(add_btn)
        
        # Yeni pencere butonu
        new_window_btn = QPushButton("Yeni Pencere")
        new_window_btn.clicked.connect(self.new_window)
        layout.addWidget(new_window_btn)
        
        return layout
    
    def create_download_tab(self):
        """İndirme sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Kontrol butonları
        control_layout = QHBoxLayout()
        
        self.start_all_btn = QPushButton("Tümünü Başlat")
        self.start_all_btn.clicked.connect(self.start_all_downloads)
        control_layout.addWidget(self.start_all_btn)
        
        self.pause_all_btn = QPushButton("Tümünü Duraklat")
        self.pause_all_btn.clicked.connect(self.pause_all_downloads)
        control_layout.addWidget(self.pause_all_btn)
        
        self.remove_completed_btn = QPushButton("Tamamlananları Temizle")
        self.remove_completed_btn.clicked.connect(self.remove_completed)
        control_layout.addWidget(self.remove_completed_btn)
        
        layout.addLayout(control_layout)
        
        # İndirme tablosu
        self.download_table = QTableWidget()
        self.download_table.setColumnCount(8)
        self.download_table.setHorizontalHeaderLabels([
            "Dosya Adı", "Boyut", "İndirilen", "Hız", 
            "Kalan Süre", "İlerleme", "Durum", "İşlemler"
        ])
        self.download_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.download_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.download_table)
        
        # Alt bilgi
        info_layout = QHBoxLayout()
        
        self.total_downloads_label = QLabel("Toplam: 0")
        info_layout.addWidget(self.total_downloads_label)
        
        self.active_downloads_label = QLabel("Aktif: 0")
        info_layout.addWidget(self.active_downloads_label)
        
        self.speed_label = QLabel("Hız: 0 MB/s")
        info_layout.addWidget(self.speed_label)
        
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        
        return widget
    
    def create_left_panel(self):
        """Sol panel (favoriler/kaydedilenler)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Favoriler listesi
        fav_group = QGroupBox("Favoriler")
        fav_layout = QVBoxLayout()
        
        self.favorites_list = QListWidget()
        self.favorites_list.itemDoubleClicked.connect(self.load_favorite)
        fav_layout.addWidget(self.favorites_list)
        
        fav_buttons = QHBoxLayout()
        add_fav_btn = QPushButton("Ekle")
        add_fav_btn.clicked.connect(self.add_favorite)
        fav_buttons.addWidget(add_fav_btn)
        
        remove_fav_btn = QPushButton("Kaldır")
        remove_fav_btn.clicked.connect(self.remove_favorite)
        fav_buttons.addWidget(remove_fav_btn)
        
        fav_layout.addLayout(fav_buttons)
        fav_group.setLayout(fav_layout)
        
        layout.addWidget(fav_group)
        
        # Kaydedilen URL'ler
        saved_group = QGroupBox("Kaydedilenler")
        saved_layout = QVBoxLayout()
        
        self.saved_list = QListWidget()
        self.saved_list.itemDoubleClicked.connect(self.load_saved)
        saved_layout.addWidget(self.saved_list)
        
        saved_buttons = QHBoxLayout()
        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self.save_current_url)
        saved_buttons.addWidget(save_btn)
        
        saved_layout.addLayout(saved_buttons)
        saved_group.setLayout(saved_layout)
        
        layout.addWidget(saved_group)
        
        # RSS Feed'ler
        rss_group = QGroupBox("RSS Feed'ler")
        rss_layout = QVBoxLayout()
        
        self.rss_list = QListWidget()
        rss_layout.addWidget(self.rss_list)
        
        rss_buttons = QHBoxLayout()
        add_rss_btn = QPushButton("Ekle")
        add_rss_btn.clicked.connect(self.add_rss)
        rss_buttons.addWidget(add_rss_btn)
        
        check_rss_btn = QPushButton("Kontrol Et")
        check_rss_btn.clicked.connect(self.check_rss)
        rss_buttons.addWidget(check_rss_btn)
        
        rss_layout.addLayout(rss_buttons)
        rss_group.setLayout(rss_layout)
        
        layout.addWidget(rss_group)
        
        layout.addStretch()
        
        return widget
    
    def create_settings_tab(self):
        """Ayarlar sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tema ayarları
        theme_group = QGroupBox("Görünüm")
        theme_layout = QVBoxLayout()
        
        theme_combo = QComboBox()
        theme_combo.addItems(["Koyu", "Açık", "Sistem"])
        theme_combo.currentTextChanged.connect(self.change_theme)
        theme_layout.addWidget(QLabel("Tema:"))
        theme_layout.addWidget(theme_combo)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # İndirme ayarları
        download_group = QGroupBox("İndirme Ayarları")
        download_layout = QVBoxLayout()
        
        # Concurrent downloads
        concurrent_layout = QHBoxLayout()
        concurrent_layout.addWidget(QLabel("Eşzamanlı İndirme:"))
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 20)
        self.concurrent_spin.setValue(4)
        concurrent_layout.addWidget(self.concurrent_spin)
        download_layout.addLayout(concurrent_layout)
        
        # Hız limiti
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Hız Limiti (KB/s):"))
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(0, 100000)
        self.speed_spin.setValue(0)
        self.speed_spin.setSpecialValueText("Sınırsız")
        speed_layout.addWidget(self.speed_spin)
        download_layout.addLayout(speed_layout)
        
        # Gece modu
        self.night_mode_check = QCheckBox("Gece Modu")
        self.night_mode_check.toggled.connect(self.toggle_night_mode)
        download_layout.addWidget(self.night_mode_check)
        
        download_group.setLayout(download_layout)
        layout.addWidget(download_group)
        
        # User-Agent ayarları
        ua_group = QGroupBox("User-Agent Yönetimi")
        ua_layout = QVBoxLayout()
        
        self.ua_list = QListWidget()
        self.load_user_agents()
        ua_layout.addWidget(self.ua_list)
        
        ua_buttons = QHBoxLayout()
        add_ua_btn = QPushButton("Ekle")
        add_ua_btn.clicked.connect(self.add_user_agent)
        ua_buttons.addWidget(add_ua_btn)
        
        remove_ua_btn = QPushButton("Kaldır")
        remove_ua_btn.clicked.connect(self.remove_user_agent)
        ua_buttons.addWidget(remove_ua_btn)
        
        edit_ua_btn = QPushButton("Düzenle")
        edit_ua_btn.clicked.connect(self.edit_user_agent)
        ua_buttons.addWidget(edit_ua_btn)
        
        ua_layout.addLayout(ua_buttons)
        ua_group.setLayout(ua_layout)
        layout.addWidget(ua_group)
        
        # Export/Import
        export_group = QGroupBox("Veri Yönetimi")
        export_layout = QHBoxLayout()
        
        export_btn = QPushButton("Ayarları Dışa Aktar")
        export_btn.clicked.connect(self.export_settings)
        export_layout.addWidget(export_btn)
        
        import_btn = QPushButton("Ayarları İçe Aktar")
        import_btn.clicked.connect(self.import_settings)
        export_layout.addWidget(import_btn)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        layout.addStretch()
        
        return widget
    
    def setup_tray(self):
        """System tray icon oluştur"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        tray_menu = QMenu()
        
        show_action = QAction("Göster", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("Gizle", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction("Çıkış", self)
        exit_action.triggered.connect(self.close)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Tray ikonuna tıklama
        self.tray_icon.activated.connect(self.tray_icon_activated)
    
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()
    
    def apply_theme(self):
        """Temayı uygula"""
        if self.config.get('theme', 'dark') == 'dark':
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QTableWidget {
                    background-color: #2d2d30;
                    alternate-background-color: #252526;
                    color: #ffffff;
                    gridline-color: #3e3e42;
                }
                QHeaderView::section {
                    background-color: #323234;
                    color: #ffffff;
                    padding: 5px;
                    border: 1px solid #3e3e42;
                }
                QPushButton {
                    background-color: #0e639c;
                    color: white;
                    border: none;
                    padding: 5px 15px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #1177bb;
                }
                QLineEdit, QComboBox {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #3e3e42;
                    padding: 5px;
                    border-radius: 3px;
                }
                QGroupBox {
                    color: #ffffff;
                    border: 2px solid #3e3e42;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
                QListWidget {
                    background-color: #2d2d30;
                    color: #ffffff;
                    border: 1px solid #3e3e42;
                }
            """)
        else:
            self.setStyleSheet("")
    
    # Diğer metodlar...
