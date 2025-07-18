"""
Unit tests for configuration management.
"""

import os
import pytest
from unittest.mock import patch
from flashcard_generator.config import ConfigManager
from flashcard_generator.models import Config


class TestConfigManager:
    """Test cases for ConfigManager."""
    
    @patch.dict(os.environ, {
        'GEMINI_API_KEY': 'test_gemini_key',
        'IMAGE_API_KEY': 'test_image_key',
        'OUTPUT_DIRECTORY': './test_output',
        'MAX_FLASHCARDS': '25',
        'IMAGE_DOWNLOAD_ENABLED': 'false',
        'CSV_FILENAME_TEMPLATE': 'test_{timestamp}.csv'
    })
    def test_load_config_with_all_env_vars(self):
        """Test loading configuration with all environment variables set."""
        config = ConfigManager.load_config()
        
        assert config.gemini_api_key == 'test_gemini_key'
        assert config.image_api_key == 'test_image_key'
        assert config.output_directory == './test_output'
        assert config.max_flashcards == 25
        assert config.image_download_enabled is False
        assert config.csv_filename_template == 'test_{timestamp}.csv'
    
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'}, clear=True)
    def test_load_config_with_minimal_env_vars(self):
        """Test loading configuration with only required environment variables."""
        config = ConfigManager.load_config()
        
        assert config.gemini_api_key == 'test_key'
        assert config.image_api_key is None
        assert config.output_directory == './flashcards'
        assert config.max_flashcards == 50
        assert config.image_download_enabled is True
        assert config.csv_filename_template == 'flashcards_{timestamp}.csv'
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('flashcard_generator.config.load_dotenv')
    def test_load_config_missing_required_key(self, mock_load_dotenv):
        """Test that missing required API key raises ValueError."""
        mock_load_dotenv.return_value = None  # Prevent loading .env file
        with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable is required"):
            ConfigManager.load_config()
    
    @patch.dict(os.environ, {'GEMINI_API_KEY': ''}, clear=True)
    def test_load_config_empty_api_key(self):
        """Test that empty API key raises ValueError."""
        with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable is required"):
            ConfigManager.load_config()
    
    @patch.dict(os.environ, {
        'GEMINI_API_KEY': 'test_key',
        'IMAGE_DOWNLOAD_ENABLED': 'true'
    }, clear=True)
    def test_image_download_enabled_true(self):
        """Test that IMAGE_DOWNLOAD_ENABLED=true is parsed correctly."""
        config = ConfigManager.load_config()
        assert config.image_download_enabled is True
    
    @patch.dict(os.environ, {
        'GEMINI_API_KEY': 'test_key',
        'IMAGE_DOWNLOAD_ENABLED': 'TRUE'
    }, clear=True)
    def test_image_download_enabled_case_insensitive(self):
        """Test that IMAGE_DOWNLOAD_ENABLED is case insensitive."""
        config = ConfigManager.load_config()
        assert config.image_download_enabled is True
    
    @patch.dict(os.environ, {
        'GEMINI_API_KEY': 'test_key',
        'MAX_FLASHCARDS': 'invalid'
    }, clear=True)
    def test_invalid_max_flashcards_format(self):
        """Test that invalid MAX_FLASHCARDS format raises ValueError."""
        with pytest.raises(ValueError):
            ConfigManager.load_config()
    
    def test_validate_api_keys_valid(self):
        """Test API key validation with valid key."""
        config = Config(gemini_api_key="valid_key")
        assert ConfigManager.validate_api_keys(config) is True
    
    def test_validate_api_keys_empty(self):
        """Test API key validation with empty key."""
        # This should raise an error during Config creation due to validation
        with pytest.raises(ValueError):
            config = Config(gemini_api_key="")
    
    def test_validate_config_valid(self):
        """Test full configuration validation with valid config."""
        config = Config(gemini_api_key="valid_key")
        assert ConfigManager.validate_config(config) is True
    
    def test_validate_config_invalid(self):
        """Test full configuration validation with invalid config."""
        # Create a config that will fail validation
        with pytest.raises(ValueError):
            Config(gemini_api_key="valid_key", max_flashcards=0)