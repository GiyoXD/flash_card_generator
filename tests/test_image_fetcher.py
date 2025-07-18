"""
Unit tests for ImageFetcher class.
"""

import pytest
import json
import tempfile
import shutil
import os
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import requests
from flashcard_generator.image_fetcher import ImageFetcher


class TestImageFetcher:
    """Test cases for ImageFetcher."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.api_key = "test_api_key"
        self.fetcher = ImageFetcher(api_key=self.api_key, output_directory=self.temp_dir)
        self.fetcher_no_key = ImageFetcher(output_directory=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        fetcher = ImageFetcher(api_key="test_key", output_directory=self.temp_dir)
        assert fetcher.api_key == "test_key"
        assert fetcher.output_directory == Path(self.temp_dir)
        assert fetcher.output_directory.exists()
    
    def test_init_without_api_key(self):
        """Test initialization without API key."""
        fetcher = ImageFetcher(output_directory=self.temp_dir)
        assert fetcher.api_key is None
        assert fetcher.output_directory.exists()
    
    def test_init_creates_output_directory(self):
        """Test that initialization creates output directory."""
        new_dir = Path(self.temp_dir) / "new_images"
        fetcher = ImageFetcher(output_directory=str(new_dir))
        assert new_dir.exists()
    
    @patch('flashcard_generator.image_fetcher.requests.get')
    def test_search_image_unsplash_success(self, mock_get):
        """Test successful image search with Unsplash API."""
        # Mock successful Unsplash response
        mock_response = Mock()
        mock_response.json.return_value = {
            'results': [
                {
                    'urls': {
                        'regular': 'https://example.com/image.jpg'
                    }
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.fetcher.search_image("cat")
        
        assert result == 'https://example.com/image.jpg'
        mock_get.assert_called_once()
    
    @patch('flashcard_generator.image_fetcher.requests.get')
    def test_search_image_pixabay_success(self, mock_get):
        """Test successful image search with Pixabay API."""
        # Mock successful Pixabay response
        mock_response = Mock()
        mock_response.json.return_value = {
            'hits': [
                {
                    'webformatURL': 'https://example.com/image.jpg'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.fetcher_no_key.search_image("dog")
        
        assert result == 'https://example.com/image.jpg'
        mock_get.assert_called_once()
    
    @patch('flashcard_generator.image_fetcher.requests.get')
    def test_search_image_no_results(self, mock_get):
        """Test image search with no results."""
        # Mock empty response
        mock_response = Mock()
        mock_response.json.return_value = {'results': []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.fetcher.search_image("nonexistent")
        
        assert result is None
    
    @patch('flashcard_generator.image_fetcher.requests.get')
    def test_search_image_api_failure(self, mock_get):
        """Test image search with API failure."""
        # Mock API failure
        mock_get.side_effect = requests.exceptions.RequestException("API Error")
        
        result = self.fetcher.search_image("cat")
        
        assert result is None
    
    def test_search_image_empty_query(self):
        """Test image search with empty query."""
        result = self.fetcher.search_image("")
        assert result is None
        
        result = self.fetcher.search_image("   ")
        assert result is None
    
    @patch('flashcard_generator.image_fetcher.requests.get')
    def test_download_image_success(self, mock_get):
        """Test successful image download."""
        # Mock successful download response
        mock_response = Mock()
        mock_response.headers = {
            'content-type': 'image/jpeg',
            'content-length': '1024'
        }
        mock_response.iter_content.return_value = [b'fake_image_data']
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Mock file verification
        with patch.object(self.fetcher, '_verify_image_file', return_value=True):
            result = self.fetcher.download_image("https://example.com/image.jpg", "test.jpg")
        
        assert result is not None
        assert result.endswith("test.jpg")
        assert Path(result).exists()
    
    @patch('flashcard_generator.image_fetcher.requests.get')
    def test_download_image_file_exists(self, mock_get):
        """Test download when file already exists."""
        # Create existing file
        existing_file = Path(self.temp_dir) / "existing.jpg"
        existing_file.write_bytes(b'existing_data')
        
        result = self.fetcher.download_image("https://example.com/image.jpg", "existing.jpg")
        
        assert result == str(existing_file)
        # Should not make HTTP request
        mock_get.assert_not_called()
    
    @patch('flashcard_generator.image_fetcher.requests.get')
    def test_download_image_invalid_content_type(self, mock_get):
        """Test download with invalid content type."""
        # Mock response with invalid content type
        mock_response = Mock()
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.fetcher.download_image("https://example.com/image.jpg", "test.jpg")
        
        assert result is None
    
    @patch('flashcard_generator.image_fetcher.requests.get')
    def test_download_image_file_too_large(self, mock_get):
        """Test download with file too large."""
        # Mock response with large file size
        mock_response = Mock()
        mock_response.headers = {
            'content-type': 'image/jpeg',
            'content-length': str(10 * 1024 * 1024)  # 10MB
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.fetcher.download_image("https://example.com/image.jpg", "test.jpg")
        
        assert result is None
    
    @patch('flashcard_generator.image_fetcher.requests.get')
    def test_download_image_network_error(self, mock_get):
        """Test download with network error."""
        # Mock network error
        mock_get.side_effect = requests.exceptions.RequestException("Network Error")
        
        result = self.fetcher.download_image("https://example.com/image.jpg", "test.jpg")
        
        assert result is None
    
    def test_download_image_invalid_input(self):
        """Test download with invalid input."""
        with pytest.raises(ValueError, match="URL and filename cannot be empty"):
            self.fetcher.download_image("", "test.jpg")
        
        with pytest.raises(ValueError, match="URL and filename cannot be empty"):
            self.fetcher.download_image("https://example.com/image.jpg", "")
    
    @patch.object(ImageFetcher, 'search_image')
    @patch.object(ImageFetcher, 'download_image')
    def test_search_and_download_success(self, mock_download, mock_search):
        """Test successful search and download operation."""
        mock_search.return_value = "https://example.com/image.jpg"
        mock_download.return_value = "/path/to/downloaded/image.jpg"
        
        result = self.fetcher.search_and_download("cat")
        
        assert result == "/path/to/downloaded/image.jpg"
        mock_search.assert_called_once_with("cat")
        mock_download.assert_called_once()
    
    @patch.object(ImageFetcher, 'search_image')
    def test_search_and_download_no_image_found(self, mock_search):
        """Test search and download when no image is found."""
        mock_search.return_value = None
        
        result = self.fetcher.search_and_download("nonexistent")
        
        assert result is None
        mock_search.assert_called_once_with("nonexistent")
    
    def test_sanitize_query(self):
        """Test query sanitization."""
        # Test normal query
        result = self.fetcher._sanitize_query("cat dog")
        assert result == "cat dog"
        
        # Test query with special characters
        result = self.fetcher._sanitize_query("cat & dog!")
        assert result == "cat dog"
        
        # Test query with extra spaces
        result = self.fetcher._sanitize_query("  cat   dog  ")
        assert result == "cat dog"
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test normal filename
        result = self.fetcher._sanitize_filename("cat.jpg")
        assert result == "cat.jpg"
        
        # Test filename with spaces
        result = self.fetcher._sanitize_filename("cat dog.jpg")
        assert result == "cat_dog.jpg"
        
        # Test filename with special characters
        result = self.fetcher._sanitize_filename("cat & dog!.jpg")
        assert result == "cat_dog.jpg"
        
        # Test filename without extension
        result = self.fetcher._sanitize_filename("cat")
        assert result == "cat.jpg"
        
        # Test very long filename
        long_name = "a" * 200
        result = self.fetcher._sanitize_filename(long_name)
        assert len(result) <= 100
        assert result.endswith(".jpg")
    
    def test_verify_image_file_jpeg(self):
        """Test image file verification for JPEG."""
        # Create fake JPEG file
        jpeg_file = Path(self.temp_dir) / "test.jpg"
        jpeg_file.write_bytes(b'\xff\xd8\xff\xe0\x00\x10JFIF')
        
        result = self.fetcher._verify_image_file(jpeg_file)
        assert result is True
    
    def test_verify_image_file_png(self):
        """Test image file verification for PNG."""
        # Create fake PNG file
        png_file = Path(self.temp_dir) / "test.png"
        png_file.write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR')
        
        result = self.fetcher._verify_image_file(png_file)
        assert result is True
    
    def test_verify_image_file_gif(self):
        """Test image file verification for GIF."""
        # Create fake GIF file
        gif_file = Path(self.temp_dir) / "test.gif"
        gif_file.write_bytes(b'GIF89a\x01\x00\x01\x00')
        
        result = self.fetcher._verify_image_file(gif_file)
        assert result is True
    
    def test_verify_image_file_invalid(self):
        """Test image file verification for invalid file."""
        # Create fake text file
        text_file = Path(self.temp_dir) / "test.txt"
        text_file.write_bytes(b'This is not an image')
        
        result = self.fetcher._verify_image_file(text_file)
        assert result is False
    
    def test_verify_image_file_empty(self):
        """Test image file verification for empty file."""
        # Create empty file
        empty_file = Path(self.temp_dir) / "empty.jpg"
        empty_file.write_bytes(b'')
        
        result = self.fetcher._verify_image_file(empty_file)
        assert result is False
    
    def test_cleanup_old_images(self):
        """Test cleanup of old images."""
        import time
        
        # Create some test image files with different ages
        old_file = Path(self.temp_dir) / "old.jpg"
        new_file = Path(self.temp_dir) / "new.jpg"
        
        old_file.write_bytes(b'\xff\xd8\xff\xe0\x00\x10JFIF')
        new_file.write_bytes(b'\xff\xd8\xff\xe0\x00\x10JFIF')
        
        # Make old file appear old by modifying its timestamp
        old_time = time.time() - (35 * 24 * 60 * 60)  # 35 days ago
        os.utime(old_file, (old_time, old_time))
        
        # Clean up files older than 30 days
        cleaned_count = self.fetcher.cleanup_old_images(max_age_days=30)
        
        assert cleaned_count == 1
        assert not old_file.exists()
        assert new_file.exists()
    
    def test_extract_image_url_unsplash(self):
        """Test URL extraction from Unsplash response."""
        data = {
            'results': [
                {
                    'urls': {
                        'regular': 'https://example.com/image.jpg'
                    }
                }
            ]
        }
        
        result = self.fetcher._extract_image_url('unsplash', data)
        assert result == 'https://example.com/image.jpg'
    
    def test_extract_image_url_pixabay(self):
        """Test URL extraction from Pixabay response."""
        data = {
            'hits': [
                {
                    'webformatURL': 'https://example.com/image.jpg'
                }
            ]
        }
        
        result = self.fetcher._extract_image_url('pixabay', data)
        assert result == 'https://example.com/image.jpg'
    
    def test_extract_image_url_empty_results(self):
        """Test URL extraction with empty results."""
        data = {'results': []}
        
        result = self.fetcher._extract_image_url('unsplash', data)
        assert result is None
    
    def test_extract_image_url_invalid_data(self):
        """Test URL extraction with invalid data."""
        data = {'invalid': 'data'}
        
        result = self.fetcher._extract_image_url('unsplash', data)
        assert result is None