"""
Unit tests for Gemini API client.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flashcard_generator.gemini_client import GeminiClient
from flashcard_generator.models import WordPair


class TestGeminiClient:
    """Test cases for GeminiClient."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.client = GeminiClient(self.api_key)
    
    @patch('flashcard_generator.gemini_client.genai.configure')
    @patch('flashcard_generator.gemini_client.genai.GenerativeModel')
    def test_authenticate_success(self, mock_model_class, mock_configure):
        """Test successful authentication."""
        # Mock the model and response
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Hello response"
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        # Test authentication
        result = self.client.authenticate()
        
        # Assertions
        assert result is True
        mock_configure.assert_called_once_with(api_key=self.api_key)
        mock_model_class.assert_called_once()
        mock_model.generate_content.assert_called_once_with("Hello")
    
    @patch('flashcard_generator.gemini_client.genai.configure')
    @patch('flashcard_generator.gemini_client.genai.GenerativeModel')
    def test_authenticate_failure(self, mock_model_class, mock_configure):
        """Test authentication failure."""
        # Mock the model to raise an exception
        mock_configure.side_effect = Exception("API key invalid")
        
        # Test authentication
        result = self.client.authenticate()
        
        # Assertions
        assert result is False
    
    @patch('flashcard_generator.gemini_client.genai.configure')
    @patch('flashcard_generator.gemini_client.genai.GenerativeModel')
    def test_generate_word_pairs_success(self, mock_model_class, mock_configure):
        """Test successful word pair generation."""
        # Mock the model and response
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = '''[
            {"english": "cat", "chinese": "猫", "pinyin": "mao1"},
            {"english": "dog", "chinese": "狗", "pinyin": "gou3"},
            {"english": "bird", "chinese": "鸟", "pinyin": "niao3"}
        ]'''
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        # Set up the client with the mocked model
        self.client._model = mock_model
        
        # Test word pair generation
        result = self.client.generate_word_pairs("animals", 3)
        
        # Assertions
        assert len(result) == 3
        assert isinstance(result[0], WordPair)
        assert result[0].english == "cat"
        assert result[0].chinese == "猫"
        assert result[0].pinyin == "mao1"
        assert result[1].english == "dog"
        assert result[1].chinese == "狗"
        assert result[1].pinyin == "gou3"
        assert result[2].english == "bird"
        assert result[2].chinese == "鸟"
        assert result[2].pinyin == "niao3"
    
    @patch('flashcard_generator.gemini_client.genai.configure')
    @patch('flashcard_generator.gemini_client.genai.GenerativeModel')
    def test_generate_word_pairs_with_markdown(self, mock_model_class, mock_configure):
        """Test word pair generation with markdown formatting in response."""
        # Mock the model and response with markdown
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = '''```json
        [
            {"english": "apple", "chinese": "苹果", "pinyin": "ping2guo3"},
            {"english": "banana", "chinese": "香蕉", "pinyin": "xiang1jiao1"}
        ]
        ```'''
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        # Set up the client with the mocked model
        self.client._model = mock_model
        
        # Test word pair generation
        result = self.client.generate_word_pairs("fruits", 2)
        
        # Assertions
        assert len(result) == 2
        assert result[0].english == "apple"
        assert result[0].chinese == "苹果"
        assert result[1].english == "banana"
        assert result[1].chinese == "香蕉"
    
    @patch('flashcard_generator.gemini_client.genai.configure')
    @patch('flashcard_generator.gemini_client.genai.GenerativeModel')
    def test_generate_word_pairs_invalid_json(self, mock_model_class, mock_configure):
        """Test word pair generation with invalid JSON response."""
        # Mock the model and response with invalid JSON
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Invalid JSON response"
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        # Set up the client with the mocked model
        self.client._model = mock_model
        
        # Test word pair generation should raise an exception after retries
        with pytest.raises(RuntimeError, match="Failed to generate word pairs after 3 attempts"):
            self.client.generate_word_pairs("animals", 3)
    
    @patch('flashcard_generator.gemini_client.genai.configure')
    @patch('flashcard_generator.gemini_client.genai.GenerativeModel')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_generate_word_pairs_retry_logic(self, mock_sleep, mock_model_class, mock_configure):
        """Test retry logic for word pair generation."""
        # Mock the model to fail twice then succeed
        mock_model = Mock()
        mock_model.generate_content.side_effect = [
            Exception("First failure"),
            Exception("Second failure"),
            Mock(text='[{"english": "test", "chinese": "测试", "pinyin": "ceshi4"}]')
        ]
        mock_model_class.return_value = mock_model
        
        # Set up the client with the mocked model
        self.client._model = mock_model
        
        # Test word pair generation
        result = self.client.generate_word_pairs("test", 1)
        
        # Assertions
        assert len(result) == 1
        assert result[0].english == "test"
        assert result[0].chinese == "测试"
        assert mock_model.generate_content.call_count == 3
        assert mock_sleep.call_count == 2  # Two retries with sleep
    
    @patch('flashcard_generator.gemini_client.genai.configure')
    @patch('flashcard_generator.gemini_client.genai.GenerativeModel')
    def test_translate_to_chinese_success(self, mock_model_class, mock_configure):
        """Test successful translation to Chinese."""
        # Mock the model and response
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "猫"
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        # Set up the client with the mocked model
        self.client._model = mock_model
        
        # Test translation
        result = self.client.translate_to_chinese("cat")
        
        # Assertions
        assert result == "猫"
        mock_model.generate_content.assert_called_once()
    
    @patch('flashcard_generator.gemini_client.genai.configure')
    @patch('flashcard_generator.gemini_client.genai.GenerativeModel')
    def test_translate_to_chinese_failure(self, mock_model_class, mock_configure):
        """Test translation failure."""
        # Mock the model to always fail
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("Translation failed")
        mock_model_class.return_value = mock_model
        
        # Set up the client with the mocked model
        self.client._model = mock_model
        
        # Test translation should raise an exception
        with pytest.raises(RuntimeError, match="Failed to translate 'cat' after 3 attempts"):
            self.client.translate_to_chinese("cat")
    
    def test_create_word_generation_prompt(self):
        """Test word generation prompt creation."""
        prompt = self.client._create_word_generation_prompt("animals", 5)
        
        # Assertions
        assert "animals" in prompt
        assert "5" in prompt
        assert "JSON" in prompt
        assert "english" in prompt
        assert "chinese" in prompt
    
    def test_parse_word_pairs_response_valid(self):
        """Test parsing valid word pairs response."""
        response = '[{"english": "cat", "chinese": "猫", "pinyin": "mao1"}, {"english": "dog", "chinese": "狗", "pinyin": "gou3"}]'
        
        result = self.client._parse_word_pairs_response(response)
        
        # Assertions
        assert len(result) == 2
        assert result[0].english == "cat"
        assert result[0].chinese == "猫"
        assert result[0].pinyin == "mao1"
        assert result[1].english == "dog"
        assert result[1].chinese == "狗"
        assert result[1].pinyin == "gou3"
    
    def test_parse_word_pairs_response_invalid_format(self):
        """Test parsing invalid word pairs response."""
        response = '{"not": "an array"}'
        
        result = self.client._parse_word_pairs_response(response)
        
        # Assertions
        assert len(result) == 0
    
    def test_parse_word_pairs_response_missing_fields(self):
        """Test parsing response with missing fields."""
        response = '[{"english": "cat"}, {"chinese": "狗"}, {"english": "bird", "chinese": "鸟"}]'
        
        result = self.client._parse_word_pairs_response(response)
        
        # Assertions - should skip invalid entries
        assert len(result) == 0
    
    def test_parse_word_pairs_response_empty_values(self):
        """Test parsing response with empty values."""
        response = '[{"english": "", "chinese": "猫"}, {"english": "dog", "chinese": ""}]'
        
        result = self.client._parse_word_pairs_response(response)
        
        # Assertions - should skip entries with empty values
        assert len(result) == 0
    
    def test_generate_word_pairs_input_validation(self):
        """Test input validation for generate_word_pairs method."""
        # Test empty topic
        with pytest.raises(ValueError, match="Topic cannot be empty"):
            self.client.generate_word_pairs("", 5)
        
        with pytest.raises(ValueError, match="Topic cannot be empty"):
            self.client.generate_word_pairs("   ", 5)
        
        # Test invalid count
        with pytest.raises(ValueError, match="Count must be greater than 0"):
            self.client.generate_word_pairs("animals", 0)
        
        with pytest.raises(ValueError, match="Count must be greater than 0"):
            self.client.generate_word_pairs("animals", -1)
        
        # Test count too large
        with pytest.raises(ValueError, match="Count cannot exceed 50"):
            self.client.generate_word_pairs("animals", 51)
    
    def test_translate_to_chinese_input_validation(self):
        """Test input validation for translate_to_chinese method."""
        # Test empty word
        with pytest.raises(ValueError, match="English word cannot be empty"):
            self.client.translate_to_chinese("")
        
        with pytest.raises(ValueError, match="English word cannot be empty"):
            self.client.translate_to_chinese("   ")