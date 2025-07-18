"""
Image fetching and downloading functionality.
"""

import os
import time
import logging
import requests
from typing import Optional, Dict, Any, List
from pathlib import Path
import hashlib
import re

logger = logging.getLogger(__name__)


class ImageFetcher:
    """Handles image searching and downloading from various APIs."""
    
    def __init__(self, api_key: Optional[str] = None, output_directory: str = "./images"):
        """Initialize the image fetcher with optional API key and output directory."""
        self.api_key = api_key
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.max_retries = 3
        self.base_delay = 1.0
        self.timeout = 10
        self.max_file_size = 5 * 1024 * 1024  # 5MB limit
        
        # Supported image formats
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        
        # API endpoints and configurations
        self.apis = {
            'unsplash': {
                'search_url': 'https://api.unsplash.com/search/photos',
                'headers': {'Authorization': f'Client-ID {api_key}'} if api_key else {},
                'params_template': {'query': '', 'per_page': 5, 'orientation': 'landscape'}
            },
            'pixabay': {
                'search_url': 'https://pixabay.com/api/',
                'headers': {},
                'params_template': {'key': api_key or '', 'q': '', 'image_type': 'photo', 'per_page': 5, 'safesearch': 'true'}
            }
        }
    
    def search_image(self, query: str) -> Optional[str]:
        """Search for an image URL based on the query."""
        if not query or not query.strip():
            logger.warning("Empty query provided for image search")
            return None
        
        clean_query = self._sanitize_query(query.strip())
        logger.info(f"Searching for image with query: '{clean_query}'")
        
        # Try different APIs in order of preference
        api_order = ['unsplash', 'pixabay'] if self.api_key else ['pixabay', 'unsplash']
        
        for api_name in api_order:
            try:
                image_url = self._search_with_api(api_name, clean_query)
                if image_url:
                    logger.info(f"Found image URL using {api_name}: {image_url}")
                    return image_url
            except Exception as e:
                logger.warning(f"Failed to search with {api_name}: {e}")
                continue
        
        logger.warning(f"No image found for query: '{clean_query}'")
        return None
    
    def download_image(self, url: str, filename: str) -> Optional[str]:
        """Download an image from URL and save to local path."""
        if not url or not filename:
            raise ValueError("URL and filename cannot be empty")
        
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        file_path = self.output_directory / safe_filename
        
        # Check if file already exists
        if file_path.exists():
            logger.info(f"Image already exists: {file_path}")
            return str(file_path)
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Downloading image from {url} (attempt {attempt + 1})")
                
                # Download with streaming to handle large files
                response = requests.get(
                    url, 
                    stream=True, 
                    timeout=self.timeout,
                    headers={'User-Agent': 'FlashcardGenerator/1.0'}
                )
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                if not any(img_type in content_type for img_type in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']):
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
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
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
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    logger.error(f"Failed to download image after {self.max_retries} attempts")
                    
            except Exception as e:
                logger.error(f"Unexpected error during download: {e}")
                file_path.unlink(missing_ok=True)
                break
        
        return None
    
    def search_and_download(self, query: str) -> Optional[str]:
        """Search for an image and download it in one operation."""
        image_url = self.search_image(query)
        if not image_url:
            return None
        
        # Generate filename based on query and URL hash
        url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
        safe_query = self._sanitize_filename(query)
        filename = f"{safe_query}_{url_hash}.jpg"
        
        return self.download_image(image_url, filename)
    
    def _search_with_api(self, api_name: str, query: str) -> Optional[str]:
        """Search for images using a specific API."""
        if api_name not in self.apis:
            raise ValueError(f"Unsupported API: {api_name}")
        
        api_config = self.apis[api_name]
        
        # Skip if API key is required but not provided
        if api_name == 'unsplash' and not self.api_key:
            logger.info("Skipping Unsplash API - no API key provided")
            return None
        
        # Prepare request parameters
        params = api_config['params_template'].copy()
        if api_name == 'unsplash':
            params['query'] = query
        elif api_name == 'pixabay':
            params['q'] = query
            if not self.api_key:
                # Use demo key for testing (limited functionality)
                params['key'] = ''
        
        try:
            response = requests.get(
                api_config['search_url'],
                params=params,
                headers=api_config['headers'],
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            return self._extract_image_url(api_name, data)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {api_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing {api_name} response: {e}")
            raise
    
    def _extract_image_url(self, api_name: str, data: Dict[Any, Any]) -> Optional[str]:
        """Extract image URL from API response data."""
        try:
            if api_name == 'unsplash':
                results = data.get('results', [])
                if results:
                    # Get regular size image URL
                    return results[0]['urls']['regular']
                    
            elif api_name == 'pixabay':
                hits = data.get('hits', [])
                if hits:
                    # Get web format URL (good quality, reasonable size)
                    return hits[0].get('webformatURL') or hits[0].get('largeImageURL')
            
            return None
            
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Error extracting URL from {api_name} response: {e}")
            return None
    
    def _sanitize_query(self, query: str) -> str:
        """Sanitize search query for API calls."""
        # Remove special characters and normalize spaces
        sanitized = re.sub(r'[^\w\s-]', '', query)
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        return sanitized
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system storage."""
        # Remove or replace invalid characters (hyphen at end to avoid range issues)
        sanitized = re.sub(r'[^\w\s.-]', '', filename)
        sanitized = re.sub(r'\s+', '_', sanitized).strip('_')
        
        # Ensure it has a valid extension
        if not any(sanitized.lower().endswith(ext) for ext in self.supported_formats):
            sanitized += '.jpg'
        
        # Limit length
        if len(sanitized) > 100:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:95] + ext
        
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
    
    def cleanup_old_images(self, max_age_days: int = 30) -> int:
        """Clean up old downloaded images."""
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