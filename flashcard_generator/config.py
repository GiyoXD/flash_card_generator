"""
Configuration management for the flashcard generator.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from .models import Config


class ConfigManager:
    """Handles configuration loading and validation."""
    
    @staticmethod
    def load_config() -> Config:
        """Load configuration from environment variables."""
        # Load environment variables from .env file
        load_dotenv()
        
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        return Config(
            gemini_api_key=gemini_api_key,
            image_api_key=os.getenv('IMAGE_API_KEY'),
            output_directory=os.getenv('OUTPUT_DIRECTORY', './flashcards'),
            max_flashcards=int(os.getenv('MAX_FLASHCARDS', '50')),
            image_download_enabled=os.getenv('IMAGE_DOWNLOAD_ENABLED', 'true').lower() == 'true',
            csv_filename_template=os.getenv('CSV_FILENAME_TEMPLATE', 'flashcards_{timestamp}.csv'),
            
            # Advanced optimization settings
            enable_caching=os.getenv('ENABLE_CACHING', 'true').lower() == 'true',
            cache_max_age_hours=int(os.getenv('CACHE_MAX_AGE_HOURS', '24')),
            enable_async_images=os.getenv('ENABLE_ASYNC_IMAGES', 'true').lower() == 'true',
            max_concurrent_images=int(os.getenv('MAX_CONCURRENT_IMAGES', '5')),
            enable_batch_processing=os.getenv('ENABLE_BATCH_PROCESSING', 'true').lower() == 'true',
            batch_size=int(os.getenv('BATCH_SIZE', '10'))
        )
    
    @staticmethod
    def validate_api_keys(config: Config) -> bool:
        """Validate that required API keys are present."""
        return bool(config.gemini_api_key)
    
    @staticmethod
    def validate_config(config: Config) -> bool:
        """Validate the entire configuration."""
        try:
            config.validate()
            return True
        except ValueError:
            return False