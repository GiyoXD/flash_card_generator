"""
Integration tests for error scenarios in the flashcard generator.

These tests verify that the system handles various error conditions gracefully
and provides appropriate error messages and partial results.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import os

from flashcard_generator.flashcard_generator import FlashcardGenerator
from flashcard_generator.config import ConfigManager
from flashcard_generator.models import Config
from flashcard_generator.exceptions import (
    ConfigurationError, ValidationError, PartialResultsError,
    GeminiAPIError, AuthenticationError, ImageFetchError
)


class TestErrorScenarios:
    """Test various error scenarios and recovery mechanisms."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config(
            gemini_api_key="test_key",
            output_directory=self.temp_dir,
            max_flashcards=10,
            image_download_enabled=True
        )
    
    def teardown_method(self):
        """Clean up test environment after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_invalid_api_key_error(self):
        """Test handling of invalid API key."""
        with patch('flashcard_generator.gemini_client.genai.configure') as mock_configure:
            mock_configure.side_effect = Exception("Invalid API key")
            
            generator = FlashcardGenerator(self.config)
            
            with pytest.raises(ConfigurationError) as exc_info:
                generator.generate_flashcards("animals", 5)
            
            assert "Authentication failed" in str(exc_info.value)
    
    def test_network_connection_error(self):
        """Test handling of network connection errors."""
        generator = FlashcardGenerator(self.config)
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs') as mock_generate:
                mock_generate.side_effect = Exception("Network connection failed")
                
                with pytest.raises(Exception) as exc_info:
                    generator.generate_flashcards("animals", 5)
                
                assert "Network connection failed" in str(exc_info.value)
    
    def test_validation_errors(self):
        """Test input validation error handling."""
        generator = FlashcardGenerator(self.config)
        
        # Test empty topic
        with pytest.raises(ValidationError) as exc_info:
            generator.generate_flashcards("", 5)
        assert "Topic cannot be empty" in str(exc_info.value)
        
        # Test invalid count
        with pytest.raises(ValidationError) as exc_info:
            generator.generate_flashcards("animals", 0)
        assert "Count must be greater than 0" in str(exc_info.value)
        
        # Test count exceeding maximum
        with pytest.raises(ValidationError) as exc_info:
            generator.generate_flashcards("animals", 100)
        assert "Count cannot exceed" in str(exc_info.value)
    
    def test_partial_results_saving(self):
        """Test that partial results are saved when generation partially fails."""
        generator = FlashcardGenerator(self.config)
        
        # Mock successful authentication
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            # Mock word pairs generation with some valid data
            mock_word_pairs = [
                Mock(english="cat", chinese="猫", pinyin="mao1"),
                Mock(english="dog", chinese="狗", pinyin="gou3"),
                Mock(english="invalid", chinese="", pinyin="")  # This will cause validation error
            ]
            
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                with patch.object(generator.image_fetcher, 'search_and_download', return_value=None):
                    # This should create some flashcards but fail on the invalid one
                    flashcards = generator.generate_flashcards("animals", 3)
                    
                    # Should have 2 successful flashcards (cat and dog)
                    assert len(flashcards) == 2
                    assert generator.stats['validation_errors'] == 1
    
    def test_image_fetch_errors_dont_stop_generation(self):
        """Test that image fetch errors don't stop flashcard generation."""
        generator = FlashcardGenerator(self.config)
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            mock_word_pairs = [
                Mock(english="cat", chinese="猫", pinyin="mao1"),
                Mock(english="dog", chinese="狗", pinyin="gou3")
            ]
            
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                # Mock image fetcher to always fail
                with patch.object(generator.image_fetcher, 'search_and_download', side_effect=Exception("Image API error")):
                    flashcards = generator.generate_flashcards("animals", 2)
                    
                    # Should still create flashcards despite image errors
                    assert len(flashcards) == 2
                    assert generator.stats['image_errors'] == 2
                    
                    # Flashcards should not have image paths
                    for flashcard in flashcards:
                        assert flashcard.image_local_path is None
    
    def test_csv_export_error_handling(self):
        """Test CSV export error handling."""
        generator = FlashcardGenerator(self.config)
        
        # Create a mock flashcard
        mock_flashcard = Mock()
        mock_flashcard.english_word = "cat"
        mock_flashcard.chinese_translation = "猫"
        mock_flashcard.pinyin = "mao1"
        mock_flashcard.topic = "animals"
        mock_flashcard.image_local_path = None
        mock_flashcard.image_url = None
        mock_flashcard.created_at = Mock()
        mock_flashcard.created_at.strftime.return_value = "2024-01-01 12:00:00"
        mock_flashcard.validate.return_value = True
        
        # Mock CSV exporter to fail
        with patch.object(generator.csv_exporter, 'export_flashcards', side_effect=Exception("Permission denied")):
            with pytest.raises(RuntimeError) as exc_info:
                generator.run("animals", 1)
            
            assert "Flashcard generation failed" in str(exc_info.value)
    
    def test_partial_results_error_with_low_success_rate(self):
        """Test PartialResultsError when success rate is too low."""
        generator = FlashcardGenerator(self.config)
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            # Create mostly invalid word pairs (only 1 out of 5 valid)
            mock_word_pairs = [
                Mock(english="cat", chinese="猫", pinyin="mao1"),  # Valid
                Mock(english="", chinese="", pinyin=""),  # Invalid
                Mock(english="", chinese="", pinyin=""),  # Invalid
                Mock(english="", chinese="", pinyin=""),  # Invalid
                Mock(english="", chinese="", pinyin=""),  # Invalid
            ]
            
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                with patch.object(generator.image_fetcher, 'search_and_download', return_value=None):
                    with pytest.raises(PartialResultsError) as exc_info:
                        generator.generate_flashcards("animals", 5)
                    
                    error = exc_info.value
                    assert error.details['successful_count'] == 1
                    assert error.details['failed_count'] == 4
                    assert len(error.partial_results) == 1
    
    def test_file_permission_errors(self):
        """Test handling of file permission errors."""
        # Create a read-only directory
        readonly_dir = Path(self.temp_dir) / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only
        
        config = Config(
            gemini_api_key="test_key",
            output_directory=str(readonly_dir),
            max_flashcards=10
        )
        
        try:
            generator = FlashcardGenerator(config)
            
            with patch.object(generator.gemini_client, 'authenticate', return_value=True):
                mock_word_pairs = [Mock(english="cat", chinese="猫", pinyin="mao1")]
                
                with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                    with patch.object(generator.image_fetcher, 'search_and_download', return_value=None):
                        with pytest.raises(RuntimeError):
                            generator.run("animals", 1)
        
        finally:
            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)
    
    def test_logging_error_scenarios(self):
        """Test that errors are properly logged."""
        generator = FlashcardGenerator(self.config)
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', side_effect=Exception("API Error")):
                with pytest.raises(Exception):
                    generator.generate_flashcards("animals", 5)
                
                # Check that error statistics were updated
                assert generator.stats['api_errors'] > 0
    
    def test_cleanup_with_errors(self):
        """Test cleanup functionality when errors occur."""
        generator = FlashcardGenerator(self.config)
        
        # Create some test files
        logs_dir = Path(self.temp_dir) / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        test_log = logs_dir / "test.log"
        test_log.write_text("test log content")
        
        # Test cleanup
        cleanup_stats = generator.cleanup_old_files(max_age_days=0)  # Clean everything
        
        assert isinstance(cleanup_stats, dict)
        assert 'logs_cleaned' in cleanup_stats
    
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_environment_variables(self):
        """Test handling of missing environment variables."""
        with pytest.raises(ValueError) as exc_info:
            ConfigManager.load_config()
        
        assert "GEMINI_API_KEY environment variable is required" in str(exc_info.value)
    
    def test_malformed_api_response(self):
        """Test handling of malformed API responses."""
        generator = FlashcardGenerator(self.config)
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            # Mock malformed response that can't be parsed
            with patch.object(generator.gemini_client, '_make_api_call', return_value="invalid json"):
                with patch.object(generator.gemini_client, '_parse_word_pairs_response', return_value=[]):
                    with pytest.raises(ValidationError) as exc_info:
                        generator.generate_flashcards("animals", 5)
                    
                    assert "No word pairs were generated" in str(exc_info.value)


class TestUserFriendlyErrorMessages:
    """Test user-friendly error message generation."""
    
    def test_api_key_error_message(self):
        """Test user-friendly message for API key errors."""
        from flashcard_generator.logging_config import get_user_friendly_error_message
        
        error = Exception("GEMINI_API_KEY environment variable is required")
        message = get_user_friendly_error_message(error)
        
        assert "Missing API Key" in message
        assert "GEMINI_API_KEY" in message
        assert "export GEMINI_API_KEY" in message
    
    def test_authentication_error_message(self):
        """Test user-friendly message for authentication errors."""
        from flashcard_generator.logging_config import get_user_friendly_error_message
        
        error = Exception("Failed to authenticate with Gemini API")
        message = get_user_friendly_error_message(error)
        
        assert "Authentication Failed" in message
        assert "API key is valid" in message
    
    def test_rate_limit_error_message(self):
        """Test user-friendly message for rate limit errors."""
        from flashcard_generator.logging_config import get_user_friendly_error_message
        
        error = Exception("rate limit exceeded")
        message = get_user_friendly_error_message(error)
        
        assert "Rate Limited" in message
        assert "wait a moment" in message
    
    def test_generic_error_message(self):
        """Test generic error message for unknown errors."""
        from flashcard_generator.logging_config import get_user_friendly_error_message
        
        error = Exception("Some unknown error")
        message = get_user_friendly_error_message(error)
        
        assert "Unexpected Error" in message
        assert "Some unknown error" in message


if __name__ == "__main__":
    pytest.main([__file__])