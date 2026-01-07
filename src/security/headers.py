# src/security/headers.py
import json
import random
import aiohttp
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class UserAgentProfile:
    name: str
    user_agent: str
    platform: str
    accept_language: str
    headers: Dict[str, str]
    port_range: tuple
    is_custom: bool = False

class HeaderManager:
    """Anti-detection için header yönetimi"""
    
    def __init__(self, config_path: Path = None):
        self.config_path = config_path or Path("Config/user_agents.json")
        self.profiles: List[UserAgentProfile] = []
        self.current_index = 0
        self._load_profiles()
        
    def _load_profiles(self):
        """Varsayılan ve özel user agent'ları yükle"""
        default_profiles = self._get_default_profiles()
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    custom_data = json.load(f)
                    custom_profiles = [
                        UserAgentProfile(**profile, is_custom=True) 
                        for profile in custom_data.get('custom', [])
                    ]
                    self.profiles = default_profiles + custom_profiles
            except:
                self.profiles = default_profiles
        else:
            self.profiles = default_profiles
            self._save_profiles()
    
    def _get_default_profiles(self) -> List[UserAgentProfile]:
        """20 adet gerçekçi user agent profili"""
        return [
            UserAgentProfile(
                name="Windows Chrome",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                platform="Windows",
                accept_language="tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "DNT": "1",
                    "Pragma": "no-cache",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1"
                },
                port_range=(49152, 65535)
            ),
            UserAgentProfile(
                name="Android TV",
                user_agent="Dalvik/2.1.0 (Linux; U; Android 11; Android TV Build/RTT0.210618.002)",
                platform="Android",
                accept_language="tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                headers={
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip",
                    "Connection": "Keep-Alive",
                    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; Android TV Build/RTT0.210618.002)"
                },
                port_range=(32768, 61000)
            ),
            # 18 tane daha profil eklenebilir
        ]
    
    def get_random_profile(self) -> UserAgentProfile:
        """Rastgele bir profil seç"""
        profile = random.choice(self.profiles)
        return self._spoof_profile(profile)
    
    def get_next_profile(self) -> UserAgentProfile:
        """Sıradaki profili al (rotasyon)"""
        profile = self.profiles[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.profiles)
        return self._spoof_profile(profile)
    
    def _spoof_profile(self, profile: UserAgentProfile) -> UserAgentProfile:
        """Profili spoof et (rastgele varyasyonlar ekle)"""
        spoofed = UserAgentProfile(**profile.__dict__)
        
        # Rastgele Accept-Language varyasyonu
        languages = ["tr-TR", "tr", "en-US", "en", "de-DE", "fr-FR"]
        selected = random.sample(languages, random.randint(1, 3))
        spoofed.accept_language = ", ".join(selected)
        
        # Rastgele port seç
        min_port, max_port = spoofed.port_range
        spoofed.headers["X-Forwarded-Port"] = str(random.randint(min_port, max_port))
        
        # Rastgele Referer ekle (opsiyonel)
        if random.random() > 0.5:
            spoofed.headers["Referer"] = random.choice([
                "https://www.google.com/",
                "https://www.youtube.com/",
                "https://www.netflix.com/",
                ""
            ])
        
        return spoofed
    
    async def create_session(self) -> aiohttp.ClientSession:
        """Spoof edilmiş header'larla aiohttp session oluştur"""
        profile = self.get_random_profile()
        
        connector = aiohttp.TCPConnector(
            limit=0,  # No limit
            ttl_dns_cache=300,
            family=0,  # Auto
            ssl=False
        )
        
        timeout = aiohttp.ClientTimeout(
            total=None,
            connect=30,
            sock_read=60
        )
        
        return aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=profile.headers
        )
    
    def add_custom_profile(self, profile: Dict):
        """Özel profil ekle"""
        custom_profile = UserAgentProfile(**profile, is_custom=True)
        self.profiles.append(custom_profile)
        self._save_profiles()
    
    def _save_profiles(self):
        """Profilleri JSON'a kaydet"""
        data = {
            "custom": [
                {k: v for k, v in profile.__dict__.items() 
                 if not k.startswith('_') and profile.is_custom}
                for profile in self.profiles if profile.is_custom
            ]
        }
        
        self.config_path.parent.mkdir(exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
