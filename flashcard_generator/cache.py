"""
Caching mechanism for the AI Flashcard Generator.

This module provides caching functionality to avoid duplicate API calls
and improve performance by storing previously generated word pairs.
"""

import json
import hashlib
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .models import WordPair

logger = logging.getLogger(__name__)


class WordPairCache:
    """Cache for storing and retrieving word pairs to avoid duplicate API calls."""
    
    def __init__(self, cache_dir: str = "./cache", max_age_hours: int = 24):
        """Initialize the cache with specified directory and expiration time."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age_hours = max_age_hours
        self.cache_file = self.cache_dir / "word_pairs_cache.json"
        
        # In-memory cache for faster access
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        
        # Load existing cache
        self._load_cache()
        
        logger.info(f"WordPairCache initialized with cache_dir={cache_dir}, max_age={max_age_hours}h")
    
    def get_cache_key(self, topic: str, count: int) -> str:
        """Generate a cache key for the given topic and count."""
        # Create a consistent key that includes topic and count
        key_data = f"{topic.lower().strip()}:{count}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_word_pairs(self, topic: str, count: int) -> Optional[List[WordPair]]:
        """Retrieve cached word pairs for the given topic and count."""
        cache_key = self.get_cache_key(topic, count)
        
        # Check memory cache first
        if cache_key in self._memory_cache:
            cache_entry = self._memory_cache[cache_key]
            
            # Check if cache entry is still valid
            if self._is_cache_valid(cache_entry):
                logger.info(f"Cache hit for topic='{topic}', count={count}")
                return self._deserialize_word_pairs(cache_entry['word_pairs'])
            else:
                # Remove expired entry
                del self._memory_cache[cache_key]
                logger.info(f"Cache expired for topic='{topic}', count={count}")
        
        logger.info(f"Cache miss for topic='{topic}', count={count}")
        return None
    
    def store_word_pairs(self, topic: str, count: int, word_pairs: List[WordPair]) -> None:
        """Store word pairs in the cache."""
        cache_key = self.get_cache_key(topic, count)
        
        cache_entry = {
            'topic': topic,
            'count': count,
            'word_pairs': self._serialize_word_pairs(word_pairs),
            'timestamp': datetime.now().isoformat(),
            'cache_key': cache_key
        }
        
        # Store in memory cache
        self._memory_cache[cache_key] = cache_entry
        
        # Persist to disk
        self._save_cache()
        
        logger.info(f"Cached {len(word_pairs)} word pairs for topic='{topic}', count={count}")
    
    def clear_cache(self) -> int:
        """Clear all cached entries and return the number of entries cleared."""
        cleared_count = len(self._memory_cache)
        self._memory_cache.clear()
        
        # Remove cache file
        if self.cache_file.exists():
            self.cache_file.unlink()
        
        logger.info(f"Cleared {cleared_count} cache entries")
        return cleared_count
    
    def cleanup_expired_entries(self) -> int:
        """Remove expired cache entries and return the number of entries removed."""
        expired_keys = []
        
        for cache_key, cache_entry in self._memory_cache.items():
            if not self._is_cache_valid(cache_entry):
                expired_keys.append(cache_key)
        
        # Remove expired entries
        for key in expired_keys:
            del self._memory_cache[key]
        
        # Save updated cache
        if expired_keys:
            self._save_cache()
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self._memory_cache)
        valid_entries = sum(1 for entry in self._memory_cache.values() if self._is_cache_valid(entry))
        expired_entries = total_entries - valid_entries
        
        cache_size_bytes = 0
        if self.cache_file.exists():
            cache_size_bytes = self.cache_file.stat().st_size
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_file_size_bytes': cache_size_bytes,
            'cache_dir': str(self.cache_dir),
            'max_age_hours': self.max_age_hours
        }
    
    def _load_cache(self) -> None:
        """Load cache from disk."""
        if not self.cache_file.exists():
            logger.info("No existing cache file found")
            return
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Load entries into memory cache
            for entry in cache_data.get('entries', []):
                cache_key = entry.get('cache_key')
                if cache_key:
                    self._memory_cache[cache_key] = entry
            
            logger.info(f"Loaded {len(self._memory_cache)} cache entries from disk")
            
        except Exception as e:
            logger.error(f"Failed to load cache from disk: {e}")
            self._memory_cache = {}
    
    def _save_cache(self) -> None:
        """Save cache to disk."""
        try:
            cache_data = {
                'version': '1.0',
                'created_at': datetime.now().isoformat(),
                'entries': list(self._memory_cache.values())
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Saved {len(self._memory_cache)} cache entries to disk")
            
        except Exception as e:
            logger.error(f"Failed to save cache to disk: {e}")
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if a cache entry is still valid (not expired)."""
        try:
            timestamp_str = cache_entry.get('timestamp')
            if not timestamp_str:
                return False
            
            entry_time = datetime.fromisoformat(timestamp_str)
            expiry_time = entry_time + timedelta(hours=self.max_age_hours)
            
            return datetime.now() < expiry_time
            
        except Exception as e:
            logger.warning(f"Error checking cache validity: {e}")
            return False
    
    def _serialize_word_pairs(self, word_pairs: List[WordPair]) -> List[Dict[str, str]]:
        """Serialize word pairs for storage."""
        return [
            {
                'english': wp.english,
                'chinese': wp.chinese,
                'pinyin': wp.pinyin,
                'context': wp.context
            }
            for wp in word_pairs
        ]
    
    def _deserialize_word_pairs(self, serialized_pairs: List[Dict[str, str]]) -> List[WordPair]:
        """Deserialize word pairs from storage."""
        word_pairs = []
        
        for pair_data in serialized_pairs:
            try:
                word_pair = WordPair(
                    english=pair_data['english'],
                    chinese=pair_data['chinese'],
                    pinyin=pair_data['pinyin'],
                    context=pair_data.get('context')
                )
                word_pairs.append(word_pair)
            except Exception as e:
                logger.warning(f"Failed to deserialize word pair: {pair_data}, error: {e}")
                continue
        
        return word_pairs


class ImageCache:
    """Cache for storing image URLs and paths to avoid duplicate downloads."""
    
    def __init__(self, cache_dir: str = "./cache", max_age_hours: int = 168):  # 1 week default
        """Initialize the image cache."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age_hours = max_age_hours
        self.cache_file = self.cache_dir / "image_cache.json"
        
        # In-memory cache
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        
        # Load existing cache
        self._load_cache()
        
        logger.info(f"ImageCache initialized with cache_dir={cache_dir}, max_age={max_age_hours}h")
    
    def get_cache_key(self, query: str) -> str:
        """Generate a cache key for the image query."""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def get_image_url(self, query: str) -> Optional[str]:
        """Get cached image URL for the query."""
        cache_key = self.get_cache_key(query)
        
        if cache_key in self._memory_cache:
            cache_entry = self._memory_cache[cache_key]
            
            if self._is_cache_valid(cache_entry):
                logger.info(f"Image cache hit for query='{query}'")
                return cache_entry.get('image_url')
            else:
                del self._memory_cache[cache_key]
        
        return None
    
    def store_image_url(self, query: str, image_url: str) -> None:
        """Store image URL in cache."""
        cache_key = self.get_cache_key(query)
        
        cache_entry = {
            'query': query,
            'image_url': image_url,
            'timestamp': datetime.now().isoformat(),
            'cache_key': cache_key
        }
        
        self._memory_cache[cache_key] = cache_entry
        self._save_cache()
        
        logger.info(f"Cached image URL for query='{query}'")
    
    def _load_cache(self) -> None:
        """Load image cache from disk."""
        if not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            for entry in cache_data.get('entries', []):
                cache_key = entry.get('cache_key')
                if cache_key:
                    self._memory_cache[cache_key] = entry
            
            logger.info(f"Loaded {len(self._memory_cache)} image cache entries")
            
        except Exception as e:
            logger.error(f"Failed to load image cache: {e}")
    
    def _save_cache(self) -> None:
        """Save image cache to disk."""
        try:
            cache_data = {
                'version': '1.0',
                'created_at': datetime.now().isoformat(),
                'entries': list(self._memory_cache.values())
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save image cache: {e}")
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if image cache entry is valid."""
        try:
            timestamp_str = cache_entry.get('timestamp')
            if not timestamp_str:
                return False
            
            entry_time = datetime.fromisoformat(timestamp_str)
            expiry_time = entry_time + timedelta(hours=self.max_age_hours)
            
            return datetime.now() < expiry_time
            
        except Exception:
            return False