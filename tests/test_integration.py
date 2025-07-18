"""
End-to-end integration tests for the flashcard generator.

These tests verify the complete workflow from API calls to CSV output,
using real or mocked API responses to ensure system integration works correctly.
"""

import pytest
import tempfile
import shutil
import os
import csv
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from flashcard_generator.flashcard_generator import FlashcardGenerator
from flashcard_generator.config import ConfigManager
from flashcard_generator.models import Config, WordPair, Flashcard
from flashcard_generator.gemini_client import GeminiClient
from flashcard_generator.image_fetcher import ImageFetcher
from flashcard_generator.csv_exporter import CSVExporter


class TestEndToEndIntegration:
    """End-to-end integration tests for the complete flashcard generation workflow."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config(
            gemini_api_key="test_api_key_12345",
            image_api_key="test_image_key",
            output_directory=self.temp_dir,
            max_flashcards=20,
            image_download_enabled=True
        )
    
    def teardown_method(self):
        """Clean up test environment after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_complete_flashcard_generation_workflow(self):
        """Test the complete workflow from topic input to CSV output."""
        generator = FlashcardGenerator(self.config)
        
        # Mock successful API responses
        mock_word_pairs = [
            WordPair(english="cat", chinese="猫", pinyin="mao1"),
            WordPair(english="dog", chinese="狗", pinyin="gou3"),
            WordPair(english="bird", chinese="鸟", pinyin="niao3")
        ]
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                with patch.object(generator.image_fetcher, 'search_and_download') as mock_image:
                    # Mock image downloads for some words
                    mock_image.side_effect = [
                        str(Path(self.temp_dir) / "images" / "cat.jpg"),  # Success
                        None,  # No image found
                        str(Path(self.temp_dir) / "images" / "bird.jpg")  # Success
                    ]
                    
                    # Create mock image files
                    images_dir = Path(self.temp_dir) / "images"
                    images_dir.mkdir(exist_ok=True)
                    (images_dir / "cat.jpg").write_bytes(b"fake_image_data")
                    (images_dir / "bird.jpg").write_bytes(b"fake_image_data")
                    
                    # Run the complete workflow
                    csv_file_path = generator.run(topic="animals", count=3)
                    
                    # Verify CSV file was created
                    assert os.path.exists(csv_file_path)
                    assert csv_file_path.endswith('.csv')
                    
                    # Verify CSV content
                    with open(csv_file_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                    
                    assert len(rows) == 3
                    
                    # Check first row (cat with image)
                    cat_row = rows[0]
                    assert cat_row['English'] == 'cat'
                    assert cat_row['Chinese'] == '猫'
                    assert cat_row['Pinyin'] == 'mao1'
                    assert cat_row['Topic'] == 'animals'
                    assert 'cat.jpg' in cat_row['Image_Path']
                    
                    # Check second row (dog without image)
                    dog_row = rows[1]
                    assert dog_row['English'] == 'dog'
                    assert dog_row['Chinese'] == '狗'
                    assert dog_row['Pinyin'] == 'gou3'
                    assert dog_row['Image_Path'] == ''
                    
                    # Verify statistics
                    stats = generator.get_stats()
                    assert stats['total_requested'] == 3
                    assert stats['words_generated'] == 3
                    assert stats['flashcards_created'] == 3
                    assert stats['images_downloaded'] == 2
    
    def test_integration_with_no_images(self):
        """Test integration workflow with image downloading disabled."""
        config = Config(
            gemini_api_key="test_api_key",
            output_directory=self.temp_dir,
            image_download_enabled=False
        )
        generator = FlashcardGenerator(config)
        
        mock_word_pairs = [
            WordPair(english="hello", chinese="你好", pinyin="ni3 hao3"),
            WordPair(english="goodbye", chinese="再见", pinyin="zai4 jian4")
        ]
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                csv_file_path = generator.run(topic="greetings", count=2)
                
                # Verify CSV was created without images
                with open(csv_file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                
                assert len(rows) == 2
                for row in rows:
                    assert row['Image_Path'] == ''
                
                # Verify no image fetcher calls were made
                stats = generator.get_stats()
                assert stats['images_downloaded'] == 0
    
    def test_integration_with_partial_failures(self):
        """Test integration workflow when some operations fail."""
        generator = FlashcardGenerator(self.config)
        
        # Mix of valid and invalid word pairs
        mock_word_pairs = [
            WordPair(english="valid1", chinese="有效1", pinyin="you3 xiao4"),
            WordPair(english="valid2", chinese="有效2", pinyin="you3 xiao4")
        ]
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                with patch.object(generator.image_fetcher, 'search_and_download') as mock_image:
                    # First image succeeds, second fails
                    mock_image.side_effect = [
                        str(Path(self.temp_dir) / "images" / "valid1.jpg"),
                        Exception("Image API error")
                    ]
                    
                    # Create mock image file
                    images_dir = Path(self.temp_dir) / "images"
                    images_dir.mkdir(exist_ok=True)
                    (images_dir / "valid1.jpg").write_bytes(b"fake_image_data")
                    
                    csv_file_path = generator.run(topic="test", count=2)
                    
                    # Should still create CSV with both flashcards
                    with open(csv_file_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                    
                    assert len(rows) == 2
                    assert 'valid1.jpg' in rows[0]['Image_Path']
                    assert rows[1]['Image_Path'] == ''  # Failed image download
                    
                    # Check error statistics
                    stats = generator.get_stats()
                    assert stats['image_errors'] == 1
                    assert stats['images_downloaded'] == 1
    
    def test_csv_unicode_handling(self):
        """Test that CSV properly handles Unicode characters (Chinese text)."""
        generator = FlashcardGenerator(self.config)
        
        # Word pairs with various Chinese characters
        mock_word_pairs = [
            WordPair(english="dragon", chinese="龙", pinyin="long2"),
            WordPair(english="phoenix", chinese="凤凰", pinyin="feng4 huang2"),
            WordPair(english="mountain", chinese="山", pinyin="shan1")
        ]
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                with patch.object(generator.image_fetcher, 'search_and_download', return_value=None):
                    csv_file_path = generator.run(topic="mythology", count=3)
                    
                    # Read CSV and verify Unicode handling
                    with open(csv_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        assert '龙' in content
                        assert '凤凰' in content
                        assert '山' in content
                    
                    # Verify proper CSV parsing
                    with open(csv_file_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                    
                    assert rows[0]['Chinese'] == '龙'
                    assert rows[1]['Chinese'] == '凤凰'
                    assert rows[2]['Chinese'] == '山'
    
    def test_file_organization(self):
        """Test that files are properly organized in directories."""
        generator = FlashcardGenerator(self.config)
        
        mock_word_pairs = [WordPair(english="test", chinese="测试", pinyin="ce4 shi4")]
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                with patch.object(generator.image_fetcher, 'search_and_download') as mock_image:
                    mock_image.return_value = str(Path(self.temp_dir) / "images" / "test.jpg")
                    
                    # Create mock image file
                    images_dir = Path(self.temp_dir) / "images"
                    images_dir.mkdir(exist_ok=True)
                    (images_dir / "test.jpg").write_bytes(b"fake_image_data")
                    
                    csv_file_path = generator.run(topic="test", count=1)
                    
                    # Verify directory structure
                    base_dir = Path(self.temp_dir)
                    assert (base_dir / "images").exists()
                    assert (base_dir / "logs").exists()
                    assert Path(csv_file_path).parent == base_dir
                    
                    # Verify log files were created
                    log_files = list((base_dir / "logs").glob("*.log"))
                    assert len(log_files) > 0


class TestAPIIntegration:
    """Test integration with external APIs (mocked for reliability)."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_gemini_client_integration(self):
        """Test GeminiClient integration with mocked responses."""
        client = GeminiClient("test_api_key")
        
        # Mock the model and its response
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = '''[
            {"english": "apple", "chinese": "苹果", "pinyin": "ping2 guo3"},
            {"english": "banana", "chinese": "香蕉", "pinyin": "xiang1 jiao1"}
        ]'''
        mock_model.generate_content.return_value = mock_response
        
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel', return_value=mock_model):
                # Test authentication
                assert client.authenticate() == True
                
                # Test word pair generation
                word_pairs = client.generate_word_pairs("fruits", 2)
                assert len(word_pairs) == 2
                assert word_pairs[0].english == "apple"
                assert word_pairs[0].chinese == "苹果"
                assert word_pairs[1].english == "banana"
    
    def test_image_fetcher_integration(self):
        """Test ImageFetcher integration with mocked API responses."""
        fetcher = ImageFetcher(api_key="test_key", output_directory=self.temp_dir)
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'hits': [{
                'webformatURL': 'https://example.com/test_image.jpg',
                'largeImageURL': 'https://example.com/test_image_large.jpg'
            }]
        }
        mock_response.raise_for_status.return_value = None
        
        # Mock image download
        mock_download_response = Mock()
        mock_download_response.headers = {'content-type': 'image/jpeg'}
        mock_download_response.iter_content.return_value = [b'fake_image_data']
        mock_download_response.raise_for_status.return_value = None
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = [mock_response, mock_download_response]
            
            # Test image search and download
            image_path = fetcher.search_and_download("test_query")
            
            assert image_path is not None
            assert os.path.exists(image_path)
            assert image_path.endswith('.jpg')
    
    def test_csv_exporter_integration(self):
        """Test CSVExporter integration with real file operations."""
        exporter = CSVExporter(self.temp_dir)
        
        # Create test flashcards
        flashcards = [
            Flashcard(
                english_word="test1",
                chinese_translation="测试1",
                pinyin="ce4 shi4",
                topic="testing",
                image_local_path="/path/to/image1.jpg"
            ),
            Flashcard(
                english_word="test2",
                chinese_translation="测试2",
                pinyin="ce4 shi4",
                topic="testing"
            )
        ]
        
        # Export to CSV
        csv_path = exporter.export_flashcards(flashcards, "test_export.csv")
        
        # Verify file was created and has correct content
        assert os.path.exists(csv_path)
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['English'] == 'test1'
        assert rows[0]['Chinese'] == '测试1'
        assert rows[1]['English'] == 'test2'
        assert rows[1]['Image_Path'] == ''


class TestConfigurationIntegration:
    """Test configuration loading and validation integration."""
    
    def test_config_loading_from_environment(self):
        """Test configuration loading from environment variables."""
        test_env = {
            'GEMINI_API_KEY': 'test_gemini_key',
            'IMAGE_API_KEY': 'test_image_key',
            'OUTPUT_DIRECTORY': './test_output',
            'MAX_FLASHCARDS': '25',
            'IMAGE_DOWNLOAD_ENABLED': 'false'
        }
        
        with patch.dict(os.environ, test_env):
            config = ConfigManager.load_config()
            
            assert config.gemini_api_key == 'test_gemini_key'
            assert config.image_api_key == 'test_image_key'
            assert config.output_directory == './test_output'
            assert config.max_flashcards == 25
            assert config.image_download_enabled == False
    
    def test_config_validation_integration(self):
        """Test configuration validation integration."""
        # Valid configuration
        valid_config = Config(
            gemini_api_key="valid_key",
            output_directory="./valid_dir",
            max_flashcards=10
        )
        assert ConfigManager.validate_config(valid_config) == True
        
        # Invalid configuration (empty API key)
        invalid_config = Config(
            gemini_api_key="",
            output_directory="./valid_dir",
            max_flashcards=10
        )
        assert ConfigManager.validate_config(invalid_config) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])