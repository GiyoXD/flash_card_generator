"""
Unit tests for data models.
"""

import pytest
from datetime import datetime
from flashcard_generator.models import WordPair, Flashcard, Config


class TestWordPair:
    """Test cases for WordPair model."""
    
    def test_valid_word_pair_creation(self):
        """Test creating a valid word pair."""
        word_pair = WordPair(english="cat", chinese="猫", pinyin="mao1")
        assert word_pair.english == "cat"
        assert word_pair.chinese == "猫"
        assert word_pair.pinyin == "mao1"
        assert word_pair.context is None
    
    def test_word_pair_with_context(self):
        """Test creating a word pair with context."""
        word_pair = WordPair(english="cat", chinese="猫", pinyin="mao1", context="animal")
        assert word_pair.context == "animal"
    
    def test_empty_english_word_raises_error(self):
        """Test that empty English word raises ValueError."""
        with pytest.raises(ValueError, match="English word cannot be empty"):
            WordPair(english="", chinese="猫", pinyin="mao1")
    
    def test_empty_chinese_word_raises_error(self):
        """Test that empty Chinese word raises ValueError."""
        with pytest.raises(ValueError, match="Chinese translation cannot be empty"):
            WordPair(english="cat", chinese="", pinyin="mao1")
    
    def test_whitespace_only_english_raises_error(self):
        """Test that whitespace-only English word raises ValueError."""
        with pytest.raises(ValueError, match="English word cannot be empty"):
            WordPair(english="   ", chinese="猫", pinyin="mao1")
    
    def test_invalid_english_characters_raises_error(self):
        """Test that invalid characters in English word raise ValueError."""
        with pytest.raises(ValueError, match="English word contains invalid characters"):
            WordPair(english="cat123", chinese="猫", pinyin="mao1")
    
    def test_valid_english_with_hyphen_and_apostrophe(self):
        """Test that hyphens and apostrophes are allowed in English words."""
        word_pair = WordPair(english="mother-in-law", chinese="岳母", pinyin="yue4mu3")
        assert word_pair.english == "mother-in-law"
        
        word_pair2 = WordPair(english="don't", chinese="不要", pinyin="bu4yao4")
        assert word_pair2.english == "don't"
    
    def test_chinese_without_chinese_characters_raises_error(self):
        """Test that Chinese translation without Chinese characters raises ValueError."""
        with pytest.raises(ValueError, match="Chinese translation must contain Chinese characters"):
            WordPair(english="cat", chinese="mao", pinyin="mao1")


class TestFlashcard:
    """Test cases for Flashcard model."""
    
    def test_valid_flashcard_creation(self):
        """Test creating a valid flashcard."""
        flashcard = Flashcard(english_word="dog", chinese_translation="狗", pinyin="gou3")
        assert flashcard.english_word == "dog"
        assert flashcard.chinese_translation == "狗"
        assert flashcard.pinyin == "gou3"
        assert flashcard.image_url is None
        assert flashcard.image_local_path is None
        assert flashcard.topic is None
        assert isinstance(flashcard.created_at, datetime)
    
    def test_flashcard_with_all_fields(self):
        """Test creating a flashcard with all fields."""
        created_time = datetime.now()
        flashcard = Flashcard(
            english_word="dog",
            chinese_translation="狗",
            pinyin="gou3",
            image_url="https://example.com/dog.jpg",
            image_local_path="./images/dog.jpg",
            topic="animals",
            created_at=created_time
        )
        assert flashcard.topic == "animals"
        assert flashcard.image_url == "https://example.com/dog.jpg"
        assert flashcard.image_local_path == "./images/dog.jpg"
        assert flashcard.created_at == created_time
    
    def test_empty_english_word_raises_error(self):
        """Test that empty English word raises ValueError."""
        with pytest.raises(ValueError, match="English word cannot be empty"):
            Flashcard(english_word="", chinese_translation="狗", pinyin="gou3")
    
    def test_empty_chinese_translation_raises_error(self):
        """Test that empty Chinese translation raises ValueError."""
        with pytest.raises(ValueError, match="Chinese translation cannot be empty"):
            Flashcard(english_word="dog", chinese_translation="", pinyin="gou3")
    
    def test_invalid_image_extension_raises_error(self):
        """Test that invalid image file extension raises ValueError."""
        with pytest.raises(ValueError, match="Invalid image file extension"):
            Flashcard(
                english_word="dog",
                chinese_translation="狗",
                pinyin="gou3",
                image_local_path="./images/dog.txt"
            )
    
    def test_valid_image_extensions(self):
        """Test that valid image extensions are accepted."""
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        for ext in valid_extensions:
            flashcard = Flashcard(
                english_word="dog",
                chinese_translation="狗",
                pinyin="gou3",
                image_local_path=f"./images/dog{ext}"
            )
            assert flashcard.image_local_path == f"./images/dog{ext}"


class TestConfig:
    """Test cases for Config model."""
    
    def test_valid_config_creation(self):
        """Test creating a valid configuration."""
        config = Config(gemini_api_key="test_key_123")
        assert config.gemini_api_key == "test_key_123"
        assert config.image_api_key is None
        assert config.output_directory == "./flashcards"
        assert config.max_flashcards == 50
        assert config.image_download_enabled is True
        assert config.csv_filename_template == "flashcards_{timestamp}.csv"
    
    def test_config_with_all_fields(self):
        """Test creating a configuration with all fields."""
        config = Config(
            gemini_api_key="test_key_123",
            image_api_key="image_key_456",
            output_directory="./custom_output",
            max_flashcards=25,
            image_download_enabled=False,
            csv_filename_template="custom_{timestamp}.csv"
        )
        assert config.image_api_key == "image_key_456"
        assert config.output_directory == "./custom_output"
        assert config.max_flashcards == 25
        assert config.image_download_enabled is False
        assert config.csv_filename_template == "custom_{timestamp}.csv"
    
    def test_empty_gemini_api_key_raises_error(self):
        """Test that empty Gemini API key raises ValueError."""
        with pytest.raises(ValueError, match="Gemini API key cannot be empty"):
            Config(gemini_api_key="")
    
    def test_whitespace_only_api_key_raises_error(self):
        """Test that whitespace-only API key raises ValueError."""
        with pytest.raises(ValueError, match="Gemini API key cannot be empty"):
            Config(gemini_api_key="   ")
    
    def test_zero_max_flashcards_raises_error(self):
        """Test that zero max flashcards raises ValueError."""
        with pytest.raises(ValueError, match="Max flashcards must be greater than 0"):
            Config(gemini_api_key="test_key", max_flashcards=0)
    
    def test_negative_max_flashcards_raises_error(self):
        """Test that negative max flashcards raises ValueError."""
        with pytest.raises(ValueError, match="Max flashcards must be greater than 0"):
            Config(gemini_api_key="test_key", max_flashcards=-1)
    
    def test_too_many_max_flashcards_raises_error(self):
        """Test that too many max flashcards raises ValueError."""
        with pytest.raises(ValueError, match="Max flashcards cannot exceed 100"):
            Config(gemini_api_key="test_key", max_flashcards=101)
    
    def test_boundary_max_flashcards_values(self):
        """Test boundary values for max flashcards."""
        # Test minimum valid value
        config1 = Config(gemini_api_key="test_key", max_flashcards=1)
        assert config1.max_flashcards == 1
        
        # Test maximum valid value
        config2 = Config(gemini_api_key="test_key", max_flashcards=100)
        assert config2.max_flashcards == 100