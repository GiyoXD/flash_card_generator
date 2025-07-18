"""
Data models for the flashcard generator.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from pathlib import Path
import re


@dataclass
class WordPair:
    """Represents an English-Chinese word pair with pinyin."""
    english: str
    chinese: str
    pinyin: str
    context: Optional[str] = None
    
    def __post_init__(self):
        """Validate the word pair after initialization."""
        self.validate()
    
    def validate(self) -> bool:
        """Validate the word pair data."""
        if not self.english or not self.english.strip():
            raise ValueError("English word cannot be empty")
        
        if not self.chinese or not self.chinese.strip():
            raise ValueError("Chinese translation cannot be empty")
        
        if not self.pinyin or not self.pinyin.strip():
            raise ValueError("Pinyin cannot be empty")
        
        # Check if English contains only valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r'^[a-zA-Z\s\-\']+$', self.english.strip()):
            raise ValueError("English word contains invalid characters")
        
        # Check if Chinese contains Chinese characters
        if not re.search(r'[\u4e00-\u9fff]', self.chinese):
            raise ValueError("Chinese translation must contain Chinese characters")
        
        # Check if pinyin contains only valid characters (letters, spaces, numbers for tones)
        if not re.match(r'^[a-zA-Z\s\d]+$', self.pinyin.strip()):
            raise ValueError("Pinyin contains invalid characters")
        
        return True
    
    def to_dict(self) -> dict:
        """Convert WordPair to dictionary for caching."""
        return {
            'english': self.english,
            'chinese': self.chinese,
            'pinyin': self.pinyin,
            'context': self.context
        }


@dataclass
class Flashcard:
    """Represents a complete flashcard with all required information."""
    english_word: str
    chinese_translation: str
    pinyin: str
    image_url: Optional[str] = None
    image_local_path: Optional[str] = None
    topic: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate the flashcard after initialization."""
        self.validate()
    
    def validate(self) -> bool:
        """Validate the flashcard data."""
        if not self.english_word or not self.english_word.strip():
            raise ValueError("English word cannot be empty")
        
        if not self.chinese_translation or not self.chinese_translation.strip():
            raise ValueError("Chinese translation cannot be empty")
        
        if not self.pinyin or not self.pinyin.strip():
            raise ValueError("Pinyin cannot be empty")
        
        # Validate image path if provided
        if self.image_local_path:
            path = Path(self.image_local_path)
            if not path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                raise ValueError("Invalid image file extension")
        
        return True


@dataclass
class Config:
    """Configuration settings for the flashcard generator."""
    gemini_api_key: str
    image_api_key: Optional[str] = None
    output_directory: str = "./flashcards"
    max_flashcards: int = 50
    image_download_enabled: bool = True
    csv_filename_template: str = "flashcards_{timestamp}.csv"
    
    # Advanced optimization settings
    enable_caching: bool = True
    cache_max_age_hours: int = 24
    enable_async_images: bool = True
    max_concurrent_images: int = 5
    enable_batch_processing: bool = True
    batch_size: int = 10
    
    def __post_init__(self):
        """Validate the configuration after initialization."""
        self.validate()
    
    def validate(self) -> bool:
        """Validate the configuration data."""
        if not self.gemini_api_key or not self.gemini_api_key.strip():
            raise ValueError("Gemini API key cannot be empty")
        
        if self.max_flashcards <= 0:
            raise ValueError("Max flashcards must be greater than 0")
        
        if self.max_flashcards > 100:
            raise ValueError("Max flashcards cannot exceed 100")
        
        # Validate output directory path
        try:
            Path(self.output_directory)
        except Exception:
            raise ValueError("Invalid output directory path")
        
        # Validate optimization settings
        if self.cache_max_age_hours <= 0:
            raise ValueError("Cache max age must be greater than 0")
        
        if self.max_concurrent_images <= 0 or self.max_concurrent_images > 20:
            raise ValueError("Max concurrent images must be between 1 and 20")
        
        if self.batch_size <= 0 or self.batch_size > 50:
            raise ValueError("Batch size must be between 1 and 50")
        
        return True