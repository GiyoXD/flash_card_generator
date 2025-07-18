"""
Tests for CSV compatibility with popular flashcard applications.

This module tests that generated CSV files can be successfully imported
into various flashcard applications like Anki, Quizlet, and others.
"""

import pytest
import tempfile
import shutil
import os
import csv
from pathlib import Path
from unittest.mock import patch

from flashcard_generator.flashcard_generator import FlashcardGenerator
from flashcard_generator.models import Config, WordPair
from flashcard_generator.csv_exporter import CSVExporter


class TestAnkiCompatibility:
    """Test compatibility with Anki flashcard application."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config(
            gemini_api_key="test_key",
            output_directory=self.temp_dir,
            image_download_enabled=False
        )
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_anki_basic_import_format(self):
        """Test basic Anki import format compatibility."""
        generator = FlashcardGenerator(self.config)
        
        mock_word_pairs = [
            WordPair(english="hello", chinese="你好", pinyin="ni3 hao3"),
            WordPair(english="goodbye", chinese="再见", pinyin="zai4 jian4"),
            WordPair(english="thank you", chinese="谢谢", pinyin="xie4 xie4"),
        ]
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                
                csv_file_path = generator.run("greetings", 3)
                
                # Test Anki-style import
                self._verify_anki_format(csv_file_path)
    
    def test_anki_with_images(self):
        """Test Anki compatibility with image references."""
        config = Config(
            gemini_api_key="test_key",
            output_directory=self.temp_dir,
            image_download_enabled=True
        )
        generator = FlashcardGenerator(config)
        
        mock_word_pairs = [
            WordPair(english="cat", chinese="猫", pinyin="mao1"),
        ]
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                with patch.object(generator.image_fetcher, 'search_and_download') as mock_image:
                    mock_image.return_value = str(Path(self.temp_dir) / "images" / "cat.jpg")
                    
                    # Create mock image
                    images_dir = Path(self.temp_dir) / "images"
                    images_dir.mkdir(exist_ok=True)
                    (images_dir / "cat.jpg").write_bytes(b"fake_image")
                    
                    csv_file_path = generator.run("animals", 1)
                    
                    # Verify Anki can handle image references
                    with open(csv_file_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                    
                    assert len(rows) == 1
                    assert 'cat.jpg' in rows[0]['Image_Path']
    
    def test_anki_special_characters(self):
        """Test Anki compatibility with special characters."""
        generator = FlashcardGenerator(self.config)
        
        # Characters that might cause issues in Anki
        mock_word_pairs = [
            WordPair(english="it's", chinese="它是", pinyin="ta1 shi4"),
            WordPair(english="don't", chinese="不要", pinyin="bu4 yao4"),
            WordPair(english="café", chinese="咖啡馆", pinyin="ka1 fei1 guan3"),
        ]
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                
                csv_file_path = generator.run("special", 3)
                
                # Verify special characters are handled correctly
                with open(csv_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    assert "it's" in content
                    assert "don't" in content
                    assert "café" in content
    
    def _verify_anki_format(self, csv_file_path):
        """Verify CSV format is compatible with Anki."""
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Anki requirements
        assert len(rows) > 0, "CSV must have data rows"
        
        # Check required fields for flashcards
        for row in rows:
            assert row['English'], "English field cannot be empty"
            assert row['Chinese'], "Chinese field cannot be empty"
            assert row['Pinyin'], "Pinyin field cannot be empty"
            
            # Verify no problematic characters that break Anki import
            for field_value in row.values():
                # Should not have unescaped quotes or newlines that break CSV
                if '"' in field_value:
                    # If quotes exist, they should be properly escaped
                    assert field_value.count('"') % 2 == 0 or '""' in field_value


class TestQuizletCompatibility:
    """Test compatibility with Quizlet flashcard application."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config(
            gemini_api_key="test_key",
            output_directory=self.temp_dir,
            image_download_enabled=False
        )
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_quizlet_basic_format(self):
        """Test basic Quizlet import format."""
        generator = FlashcardGenerator(self.config)
        
        mock_word_pairs = [
            WordPair(english="red", chinese="红色", pinyin="hong2 se4"),
            WordPair(english="blue", chinese="蓝色", pinyin="lan2 se4"),
        ]
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                
                csv_file_path = generator.run("colors", 2)
                
                # Verify Quizlet compatibility
                self._verify_quizlet_format(csv_file_path)
    
    def test_quizlet_term_definition_mapping(self):
        """Test that CSV can be mapped to Quizlet's term/definition format."""
        generator = FlashcardGenerator(self.config)
        
        mock_word_pairs = [
            WordPair(english="water", chinese="水", pinyin="shui3"),
        ]
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                
                csv_file_path = generator.run("elements", 1)
                
                # Create Quizlet-style mapping
                quizlet_data = self._convert_to_quizlet_format(csv_file_path)
                
                assert len(quizlet_data) == 1
                assert quizlet_data[0]['term'] == 'water'
                assert quizlet_data[0]['definition'] == '水 (shui3)'
    
    def _verify_quizlet_format(self, csv_file_path):
        """Verify CSV format works with Quizlet."""
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            # Quizlet should be able to parse standard CSV
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) > 0
        
        # Verify UTF-8 encoding works (Quizlet supports Unicode)
        for row in rows:
            # Should be able to encode/decode properly
            english = row['English'].encode('utf-8').decode('utf-8')
            chinese = row['Chinese'].encode('utf-8').decode('utf-8')
            assert english == row['English']
            assert chinese == row['Chinese']
    
    def _convert_to_quizlet_format(self, csv_file_path):
        """Convert our CSV format to Quizlet's expected format."""
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        quizlet_data = []
        for row in rows:
            quizlet_data.append({
                'term': row['English'],
                'definition': f"{row['Chinese']} ({row['Pinyin']})"
            })
        
        return quizlet_data


class TestGenericCSVCompatibility:
    """Test generic CSV compatibility for various applications."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config(
            gemini_api_key="test_key",
            output_directory=self.temp_dir,
            image_download_enabled=False
        )
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_csv_standard_compliance(self):
        """Test compliance with CSV standards (RFC 4180)."""
        generator = FlashcardGenerator(self.config)
        
        # Test with various challenging content
        mock_word_pairs = [
            WordPair(english='comma, test', chinese='逗号，测试', pinyin='dou4 hao2'),
            WordPair(english='quote "test"', chinese='引号"测试"', pinyin='yin3 hao4'),
            WordPair(english='newline\ntest', chinese='换行\n测试', pinyin='huan4 hang2'),
        ]
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                
                csv_file_path = generator.run("special_chars", 3)
                
                # Test that CSV can be parsed by standard parsers
                with open(csv_file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                
                assert len(rows) == 3
                
                # Verify special characters are preserved
                assert 'comma, test' in rows[0]['English']
                assert 'quote "test"' in rows[1]['English']
                assert 'newline\ntest' in rows[2]['English']
    
    def test_excel_compatibility(self):
        """Test compatibility with Microsoft Excel CSV import."""
        generator = FlashcardGenerator(self.config)
        
        mock_word_pairs = [
            WordPair(english="number", chinese="数字", pinyin="shu4 zi4"),
            WordPair(english="letter", chinese="字母", pinyin="zi4 mu3"),
        ]
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                
                csv_file_path = generator.run("symbols", 2)
                
                # Test Excel-style parsing
                with open(csv_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Should not start with BOM (which can cause issues)
                    assert not content.startswith('\ufeff')
                    
                    # Should have proper line endings
                    assert '\n' in content


if __name__ == "__main__":
    pytest.main([__file__])