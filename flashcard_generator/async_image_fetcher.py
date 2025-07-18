"""
Asynchronous image fetching for concurrent processing.

This module provides async image downloading capabilities to improve
performance when fetching multiple images simultaneously.
"""

import asyncio
import aiohttp
import logging
import hashlib
import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import time

from .cache import ImageCache

logger = logging.getLogger(__name__)


class AsyncImageFetcher:
    """Asynchronous image fetcher for concurrent downloads."""
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 output_directory: str = "./images",
                 max_concurrent: int = 5,
                 enable_cache: bool = True):
        """Initialize the async image fetcher."""
        self.api_key = api_key
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        self.max_concurrent = max_concurrent
        
        # Configuration
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.max_file_size = 5 * 1024 * 1024  # 5MB limit
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        
        # Caching
        self.enable_cache = enable_cache
        if enable_cache:
            self.image_cache = ImageCache(
                cache_dir=str(self.output_directory.parent / "cache"),
                max_age_hours=168  # 1 week
            )
        
        # API configurations
        self.apis = {
            'unsplash': {
                'search_url': 'https://api.unsplash.com/search/photos',
                'headers': {'Authorization': f'Client-ID {api_key}'} if api_key else {},
                'params_template': {'query': '', 'per_page': 3, 'orientation': 'landscape'}
            },
            'pixabay': {
                'search_url': 'https://pixabay.com/api/',
                'headers': {},
                'params_template': {
                    'key': api_key or '', 
                    'q': '', 
                    'image_type': 'photo', 
                    'per_page': 3, 
                    'safesearch': 'true'
                }
            }
        }
        
        logger.info(f"AsyncImageFetcher initialized with max_concurrent={max_concurrent}, cache={enable_cache}")
    
    async def fetch_images_concurrent(self, queries: List[str]) -> List[Tuple[str, Optional[str]]]:
        """Fetch images for multiple queries concurrently."""
        if not queries:
            return []
        
        logger.info(f"Starting concurrent image fetch for {len(queries)} queries")
        start_time = time.time()
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Create tasks for all queries
        tasks = []
        for query in queries:
            task = self._fetch_single_image_with_semaphore(semaphore, query)
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        processed_results = []
        successful_downloads = 0
        
        for i, result in enumerate(results):
            query = queries[i]
            
            if isinstance(result, Exception):
                logger.error(f"Error fetching image for '{query}': {result}")
                processed_results.append((query, None))
            else:
                processed_results.append((query, result))
                if result:
                    successful_downloads += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Concurrent image fetch completed: {successful_downloads}/{len(queries)} successful in {duration:.2f}s")
        
        return processed_results
    
    async def _fetch_single_image_with_semaphore(self, semaphore: asyncio.Semaphore, query: str) -> Optional[str]:
        """Fetch a single image with semaphore control."""
        async with semaphore:
            return await self._fetch_single_image(query)
    
    async def _fetch_single_image(self, query: str) -> Optional[str]:
        """Fetch a single image asynchronously."""
        if not query or not query.strip():
            return None
        
        clean_query = self._sanitize_query(query.strip())
        
        # Check cache first
        if self.enable_cache:
            cached_url = self.image_cache.get_image_url(clean_query)
            if cached_url:
                # Try to download the cached URL
                downloaded_path = await self._download_image(cached_url, clean_query)
                if downloaded_path:
                    return downloaded_path
        
        # Try different APIs
        api_order = ['unsplash', 'pixabay'] if self.api_key else ['pixabay', 'unsplash']
        
        for api_name in api_order:
            try:
                image_url = await self._search_with_api(api_name, clean_query)
                if image_url:
                    # Cache the URL
                    if self.enable_cache:
                        self.image_cache.store_image_url(clean_query, image_url)
                    
                    # Download the image
                    downloaded_path = await self._download_image(image_url, clean_query)
                    if downloaded_path:
                        logger.info(f"Successfully fetched image for '{query}' using {api_name}")
                        return downloaded_path
                        
            except Exception as e:
                logger.warning(f"Failed to fetch image from {api_name} for '{query}': {e}")
                continue
        
        logger.warning(f"No image found for query: '{query}'")
        return None
    
    async def _search_with_api(self, api_name: str, query: str) -> Optional[str]:
        """Search for images using a specific API asynchronously."""
        if api_name not in self.apis:
            raise ValueError(f"Unsupported API: {api_name}")
        
        api_config = self.apis[api_name]
        
        # Skip if API key is required but not provided
        if api_name == 'unsplash' and not self.api_key:
            return None
        
        # Prepare request parameters
        params = api_config['params_template'].copy()
        if api_name == 'unsplash':
            params['query'] = query
        elif api_name == 'pixabay':
            params['q'] = query
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            try:
                async with session.get(
                    api_config['search_url'],
                    params=params,
                    headers=api_config['headers']
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return self._extract_image_url(api_name, data)
                    
            except Exception as e:
                logger.error(f"API request failed for {api_name}: {e}")
                raise
    
    async def _download_image(self, url: str, query: str) -> Optional[str]:
        """Download an image from URL asynchronously."""
        if not url:
            return None
        
        # Generate filename
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        safe_query = self._sanitize_filename(query)
        filename = f"{safe_query}_{url_hash}.jpg"
        file_path = self.output_directory / filename
        
        # Check if file already exists
        if file_path.exists():
            return str(file_path)
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            try:
                async with session.get(
                    url,
                    headers={'User-Agent': 'FlashcardGenerator/1.0'}
                ) as response:
                    response.raise_for_status()
                    
                    # Check content type
                    content_type = response.headers.get('content-type', '').lower()
                    if not any(img_type in content_type for img_type in 
                              ['image/jpeg', 'image/png', 'image/gif', 'image/webp']):
                        logger.warning(f"Invalid content type: {content_type}")
                        return None
                    
                    # Check file size
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > self.max_file_size:
                        logger.warning(f"File too large: {content_length} bytes")
                        return None
                    
                    # Download and save
                    total_size = 0
                    with open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            total_size += len(chunk)
                            if total_size > self.max_file_size:
                                logger.warning("File size exceeded during download")
                                file_path.unlink(missing_ok=True)
                                return None
                            f.write(chunk)
                    
                    # Verify the downloaded file
                    if self._verify_image_file(file_path):
                        logger.info(f"Successfully downloaded image: {file_path}")
                        return str(file_path)
                    else:
                        logger.warning("Downloaded file is not a valid image")
                        file_path.unlink(missing_ok=True)
                        return None
                        
            except Exception as e:
                logger.error(f"Error downloading image from {url}: {e}")
                if file_path.exists():
                    file_path.unlink(missing_ok=True)
                return None
    
    def _extract_image_url(self, api_name: str, data: Dict[Any, Any]) -> Optional[str]:
        """Extract image URL from API response data."""
        try:
            if api_name == 'unsplash':
                results = data.get('results', [])
                if results:
                    return results[0]['urls']['regular']
                    
            elif api_name == 'pixabay':
                hits = data.get('hits', [])
                if hits:
                    return hits[0].get('webformatURL') or hits[0].get('largeImageURL')
            
            return None
            
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Error extracting URL from {api_name} response: {e}")
            return None
    
    def _sanitize_query(self, query: str) -> str:
        """Sanitize search query for API calls."""
        sanitized = re.sub(r'[^\w\s-]', '', query)
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        return sanitized
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system storage."""
        sanitized = re.sub(r'[^\w\s.-]', '', filename)
        sanitized = re.sub(r'\s+', '_', sanitized).strip('_')
        
        # Limit length
        if len(sanitized) > 50:
            sanitized = sanitized[:50]
        
        return sanitized
    
    def _verify_image_file(self, file_path: Path) -> bool:
        """Verify that the downloaded file is a valid image."""
        try:
            # Check file size
            if file_path.stat().st_size == 0:
                return False
            
            # Check file extension
            if file_path.suffix.lower() not in self.supported_formats:
                return False
            
            # Basic file header check
            with open(file_path, 'rb') as f:
                header = f.read(16)
                
            # Check for common image file signatures
            if header.startswith(b'\xff\xd8\xff'):  # JPEG
                return True
            elif header.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
                return True
            elif header.startswith(b'GIF8'):  # GIF
                return True
            elif header.startswith(b'RIFF') and b'WEBP' in header:  # WebP
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying image file: {e}")
            return False
    
    async def cleanup_old_images(self, max_age_days: int = 30) -> int:
        """Clean up old downloaded images asynchronously."""
        if not self.output_directory.exists():
            return 0
        
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        cleaned_count = 0
        
        try:
            for file_path in self.output_directory.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        cleaned_count += 1
                        logger.info(f"Cleaned up old image: {file_path}")
            
            logger.info(f"Cleaned up {cleaned_count} old images")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0