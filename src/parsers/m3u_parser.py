# src/parsers/m3u_parser.py
import re
import aiohttp
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs, urlencode

@dataclass
class Channel:
    name: str
    url: str
    group: str = ""
    logo: str = ""
    metadata: Dict = None

class M3UParser:
    """M3U ve Xtream Codes playlist parser"""
    
    @staticmethod
    async def parse_url(url: str) -> List[Channel]:
        """URL'den M3U playlist parse et"""
        from src.security.headers import HeaderManager
        
        header_manager = HeaderManager()
        
        async with await header_manager.create_session() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return []
                
                content = await response.text()
                return M3UParser._parse_content(content, base_url=url)
    
    @staticmethod
    def parse_file(filepath: str) -> List[Channel]:
        """Dosyadan M3U parse et"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return M3UParser._parse_content(content)
    
    @staticmethod
    def _parse_content(content: str, base_url: str = "") -> List[Channel]:
        """M3U içeriğini parse et"""
        channels = []
        current_info = {}
        
        lines = content.strip().split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('#EXTINF:'):
                # Channel bilgilerini parse et
                info = M3UParser._parse_extinf(line)
                current_info = info
                
                # Sonraki satır URL olmalı
                if i + 1 < len(lines):
                    url_line = lines[i + 1].strip()
                    if url_line and not url_line.startswith('#'):
                        # URL'yi tamamla (göreceli ise)
                        if not url_line.startswith(('http://', 'https://')):
                            if base_url:
                                # Base URL'den tam URL oluştur
                                base = base_url.rsplit('/', 1)[0]
                                url_line = base + '/' + url_line.lstrip('/')
                        
                        channel = Channel(
                            name=info.get('name', 'Unknown'),
                            url=url_line,
                            group=info.get('group', 'General'),
                            logo=info.get('logo', ''),
                            metadata=info
                        )
                        channels.append(channel)
                        i += 1  # URL satırını atla
            i += 1
        
        return channels
    
    @staticmethod
    def _parse_extinf(line: str) -> Dict:
        """#EXTINF satırını parse et"""
        info = {}
        
        # Format: #EXTINF:-1 tvg-id="" tvg-name="CHANNEL" tvg-logo="" group-title="GROUP",CHANNEL
        match = re.search(r'tvg-name="([^"]*)"', line)
        if match:
            info['name'] = match.group(1)
        else:
            # İsim sonunda virgülden sonra
            name_match = re.search(r',(.+)$', line)
            info['name'] = name_match.group(1).strip() if name_match else "Unknown"
        
        match = re.search(r'group-title="([^"]*)"', line)
        info['group'] = match.group(1) if match else "General"
        
        match = re.search(r'tvg-logo="([^"]*)"', line)
        info['logo'] = match.group(1) if match else ""
        
        return info

class XtreamParser:
    """Xtream Codes API parser"""
    
    @staticmethod
    async def parse(server: str, username: str, password: str) -> List[Channel]:
        """Xtream Codes'dan kanalları çek"""
        base_url = server.rstrip('/')
        
        # API endpoint'leri
        auth_url = f"{base_url}/player_api.php?username={username}&password={password}"
        live_categories_url = f"{auth_url}&action=get_live_categories"
        live_streams_url = f"{auth_url}&action=get_live_streams"
        
        from src.security.headers import HeaderManager
        header_manager = HeaderManager()
        
        async with await header_manager.create_session() as session:
            # Kategorileri al
            async with session.get(live_categories_url) as resp:
                if resp.status != 200:
                    return []
                categories = await resp.json()
            
            # Tüm kanalları al
            async with session.get(live_streams_url) as resp:
                if resp.status != 200:
                    return []
                streams = await resp.json()
            
            # Channel objelerine çevir
            channels = []
            for stream in streams:
                # Stream URL'sini oluştur
                stream_url = (
                    f"{base_url}/live/{username}/{password}/"
                    f"{stream.get('stream_id', '')}.ts"
                )
                
                # Kategori ismini bul
                category_name = "General"
                for cat in categories:
                    if cat.get('category_id') == stream.get('category_id'):
                        category_name = cat.get('category_name', 'General')
                        break
                
                channel = Channel(
                    name=stream.get('name', 'Unknown'),
                    url=stream_url,
                    group=category_name,
                    logo=stream.get('stream_icon', ''),
                    metadata=stream
                )
                channels.append(channel)
            
            return channels
