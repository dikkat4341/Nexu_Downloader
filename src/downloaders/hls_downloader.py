# src/downloaders/hls_downloader.py
import asyncio
import aiohttp
import aiofiles
import hashlib
import subprocess
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse, urljoin
import m3u8

class HLSDownloader:
    """HLS stream indirme ve birleştirme"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("Downloads")
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir = Path("Temp/hls")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    async def download(self, url: str, filename: str = None) -> Path:
        """M3U8 URL'sinden video indir"""
        if not filename:
            filename = self._generate_filename(url)
        
        # M3U8 playlist'ini parse et
        playlist = await self._fetch_playlist(url)
        
        if not playlist:
            raise ValueError("Playlist yüklenemedi")
        
        # Segmentleri indir
        segments = await self._download_segments(playlist, url)
        
        # Segmentleri birleştir
        output_path = await self._merge_segments(segments, filename)
        
        # Temp dosyalarını temizle
        self._cleanup_temp()
        
        return output_path
    
    async def _fetch_playlist(self, url: str) -> Optional[m3u8.M3U8]:
        """Playlist'i indir ve parse et"""
        from src.security.headers import HeaderManager
        
        header_manager = HeaderManager()
        
        async with await header_manager.create_session() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                content = await response.text()
                base_uri = url.rsplit('/', 1)[0]
                
                return m3u8.M3U8(content, base_uri=base_uri)
    
    async def _download_segments(self, playlist, base_url: str) -> List[Path]:
        """Tüm segmentleri paralel indir"""
        from src.core.downloader import DownloadTask
        
        tasks = []
        semaphore = asyncio.Semaphore(6)  # Max 6 concurrent
        
        for i, segment in enumerate(playlist.segments):
            if not segment.uri:
                continue
                
            segment_url = segment.uri
            if not segment_url.startswith(('http://', 'https://')):
                segment_url = urljoin(base_url, segment_url)
            
            task = asyncio.create_task(
                self._download_segment(segment_url, i, semaphore)
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    async def _download_segment(self, url: str, index: int, 
                                semaphore: asyncio.Semaphore) -> Path:
        """Tek bir segment indir"""
        async with semaphore:
            from src.security.headers import HeaderManager
            
            header_manager = HeaderManager()
            segment_path = self.temp_dir / f"segment_{index:06d}.ts"
            
            async with await header_manager.create_session() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        async with aiofiles.open(segment_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        return segment_path
            
            raise ConnectionError(f"Segment {index} indirilemedi: {url}")
    
    async def _merge_segments(self, segments: List[Path], 
                             filename: str) -> Path:
        """Segmentleri FFmpeg ile birleştir"""
        # Segment listesi oluştur
        list_file = self.temp_dir / "segments.txt"
        async with aiofiles.open(list_file, 'w') as f:
            for segment in sorted(segments):
                await f.write(f"file '{segment.absolute()}'\n")
        
        # FFmpeg ile birleştir
        output_path = self.output_dir / f"{filename}.mp4"
        
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            "-movflags", "+faststart",
            str(output_path),
            "-y"  # Overwrite without asking
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        await process.wait()
        
        if process.returncode != 0:
            stderr = await process.stderr.read()
            raise Exception(f"FFmpeg hatası: {stderr.decode()}")
        
        return output_path
    
    def _generate_filename(self, url: str) -> str:
        """URL'den dosya adı oluştur"""
        import time
        import re
        
        # URL'den isim çıkar
        name = urlparse(url).path.split('/')[-1]
        if not name or len(name) > 100:
            # Hash kullan
            name_hash = hashlib.md5(url.encode()).hexdigest()[:10]
            timestamp = int(time.time())
            name = f"video_{timestamp}_{name_hash}"
        
        # Geçersiz karakterleri temizle
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        name = name[:150]  # Max uzunluk
        
        return name
    
    def _cleanup_temp(self):
        """Temp dosyalarını temizle"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
