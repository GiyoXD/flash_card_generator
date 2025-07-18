"""
Unit tests for CSVExporter class.
"""

import pytest
import tempfile
import shutil
import csv
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch
from flashcard_generator.csv_exporter import CSVExporter
from flashcard_generator.models import Flashcard


class TestCSVExporter:
    """Test cases for CSVExporter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.exporter = CSVExporter(output_directory=self.temp_dir)
        
        # Create sample flashcards for testing
        self.sample_flashcards = [
            Flashcard(
                english_word="cat",
                chinese_translation="猫",
                pinyin="mao1",
                image_local_path="./images/cat.jpg",
                topic="animals",
                created_at=datetime(2024, 1, 15, 10, 30, 0)
            ),
            Flashcard(
                english_word="dog",
                chinese_translation="狗",
                pinyin="gou3",
                image_url="https://example.com/dog.jpg",
                topic="animals",
                created_at=datetime(2024, 1, 15, 11, 0, 0)
            ),
            Flashcard(
                english_word="apple",
                chinese_translation="苹果",
                pinyin="ping2guo3",
                topic="fruits",
                created_at=datetime(2024, 1, 15, 12, 0, 0)
            )
        ]
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_creates_output_directory(self):
        """Test that initialization creates output directory."""
        new_dir = Path(self.temp_dir) / "new_csv_output"
        exporter = CSVExporter(output_directory=str(new_dir))
        assert new_dir.exists()
        assert exporter.output_directory == new_dir
    
    def test_export_flashcards_success(self):
        """Test successful flashcard export."""
        result_path = self.exporter.export_flashcards(self.sample_flashcards)
        
        # Check that file was created
        assert Path(result_path).exists()
        assert result_path.endswith('.csv')
        
        # Read and verify CSV content
        csv_data = self.exporter.read_csv_file(result_path)
        assert len(csv_data) == 3
        
        # Check first row
        first_row = csv_data[0]
        assert first_row['English'] == 'cat'
        assert first_row['Chinese'] == '猫'
        assert first_row['Pinyin'] == 'mao1'
        assert first_row['Image_Path'] == './images/cat.jpg'
        assert first_row['Topic'] == 'animals'
        assert first_row['Created_Date'] == '2024-01-15 10:30:00'
    
    def test_export_flashcards_with_custom_filename(self):
        """Test export with custom filename."""
        custom_filename = "my_flashcards.csv"
        result_path = self.exporter.export_flashcards(self.sample_flashcards, custom_filename)
        
        assert Path(result_path).name == custom_filename
        assert Path(result_path).exists()
    
    def test_export_flashcards_filename_without_extension(self):
        """Test export with filename without .csv extension."""
        filename_without_ext = "my_flashcards"
        result_path = self.exporter.export_flashcards(self.sample_flashcards, filename_without_ext)
        
        assert result_path.endswith('.csv')
        assert Path(result_path).exists()
    
    def test_export_flashcards_empty_list(self):
        """Test export with empty flashcard list."""
        with pytest.raises(ValueError, match="Cannot export empty flashcard list"):
            self.exporter.export_flashcards([])
    
    def test_export_flashcards_with_unicode_characters(self):
        """Test export with various Unicode characters."""
        unicode_flashcards = [
            Flashcard(
                english_word="hello",
                chinese_translation="你好",
                pinyin="ni3hao3",
                topic="greetings"
            ),
            Flashcard(
                english_word="thank you",
                chinese_translation="谢谢",
                pinyin="xie4xie4",
                topic="greetings"
            )
        ]
        
        result_path = self.exporter.export_flashcards(unicode_flashcards)
        
        # Read and verify Unicode handling
        csv_data = self.exporter.read_csv_file(result_path)
        assert len(csv_data) == 2
        assert csv_data[0]['Chinese'] == '你好'
        assert csv_data[1]['Chinese'] == '谢谢'
    
    def test_export_flashcards_with_special_characters(self):
        """Test export with special characters that need CSV escaping."""
        special_flashcards = [
            Flashcard(
                english_word='word with "quotes"',
                chinese_translation="带引号的词",
                pinyin="dai4yin3hao4de5ci2",
                topic="test, with comma"
            ),
            Flashcard(
                english_word="word\nwith\nnewlines",
                chinese_translation="带换行的词",
                pinyin="dai4huan4hang2de5ci2",
                topic="test"
            )
        ]
        
        result_path = self.exporter.export_flashcards(special_flashcards)
        
        # Read and verify special character handling
        csv_data = self.exporter.read_csv_file(result_path)
        assert len(csv_data) == 2
        assert 'quotes' in csv_data[0]['English']
        assert 'newlines' in csv_data[1]['English']
    
    def test_validate_csv_format_valid_data(self):
        """Test CSV format validation with valid data."""
        valid_data = [
            {
                'English': 'cat',
                'Chinese': '猫',
                'Pinyin': 'mao1',
                'Image_Path': './images/cat.jpg',
                'Topic': 'animals',
                'Created_Date': '2024-01-15 10:30:00'
            }
        ]
        
        result = self.exporter.validate_csv_format(valid_data)
        assert result is True
    
    def test_validate_csv_format_empty_data(self):
        """Test CSV format validation with empty data."""
        result = self.exporter.validate_csv_format([])
        assert result is False
    
    def test_validate_csv_format_missing_columns(self):
        """Test CSV format validation with missing required columns."""
        invalid_data = [
            {
                'English': 'cat',
                'Chinese': '猫'
                # Missing other required columns
            }
        ]
        
        result = self.exporter.validate_csv_format(invalid_data)
        assert result is False
    
    def test_validate_csv_format_invalid_chinese(self):
        """Test CSV format validation with invalid Chinese characters."""
        invalid_data = [
            {
                'English': 'cat',
                'Chinese': 'not chinese',  # No Chinese characters
                'Pinyin': 'mao1',
                'Image_Path': '',
                'Topic': '',
                'Created_Date': '2024-01-15 10:30:00'
            }
        ]
        
        result = self.exporter.validate_csv_format(invalid_data)
        assert result is False
    
    def test_validate_csv_format_invalid_date(self):
        """Test CSV format validation with invalid date format."""
        invalid_data = [
            {
                'English': 'cat',
                'Chinese': '猫',
                'Pinyin': 'mao1',
                'Image_Path': '',
                'Topic': '',
                'Created_Date': 'invalid-date'
            }
        ]
        
        result = self.exporter.validate_csv_format(invalid_data)
        assert result is False
    
    def test_validate_csv_format_empty_required_fields(self):
        """Test CSV format validation with empty required fields."""
        invalid_data = [
            {
                'English': '',  # Empty English
                'Chinese': '猫',
                'Pinyin': 'mao1',
                'Image_Path': '',
                'Topic': '',
                'Created_Date': '2024-01-15 10:30:00'
            }
        ]
        
        result = self.exporter.validate_csv_format(invalid_data)
        assert result is False
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test normal filename
        result = self.exporter._sanitize_filename("flashcards.csv")
        assert result == "flashcards.csv"
        
        # Test filename with spaces
        result = self.exporter._sanitize_filename("my flashcards.csv")
        assert result == "my_flashcards.csv"
        
        # Test filename with special characters
        result = self.exporter._sanitize_filename("flash@cards!.csv")
        assert result == "flashcards.csv"
        
        # Test filename without extension
        result = self.exporter._sanitize_filename("flashcards")
        assert result == "flashcards.csv"
        
        # Test very long filename
        long_name = "a" * 200 + ".csv"
        result = self.exporter._sanitize_filename(long_name)
        assert len(result) <= 100
        assert result.endswith(".csv")
    
    def test_escape_csv_value(self):
        """Test CSV value escaping."""
        # Test normal value
        result = self.exporter._escape_csv_value("normal text")
        assert result == "normal text"
        
        # Test None value
        result = self.exporter._escape_csv_value(None)
        assert result == ""
        
        # Test numeric value
        result = self.exporter._escape_csv_value(123)
        assert result == "123"
        
        # Test value with whitespace
        result = self.exporter._escape_csv_value("  text with spaces  ")
        assert result == "text with spaces"
    
    def test_flashcards_to_csv_data(self):
        """Test conversion of flashcards to CSV data."""
        csv_data = self.exporter._flashcards_to_csv_data(self.sample_flashcards)
        
        assert len(csv_data) == 3
        assert all(isinstance(row, dict) for row in csv_data)
        assert all(set(self.exporter.required_columns).issubset(set(row.keys())) for row in csv_data)
        
        # Check specific values
        first_row = csv_data[0]
        assert first_row['English'] == 'cat'
        assert first_row['Chinese'] == '猫'
        assert first_row['Pinyin'] == 'mao1'
    
    def test_flashcards_to_csv_data_with_invalid_flashcard(self):
        """Test conversion with invalid flashcard (should be skipped)."""
        # Create a mix of valid and invalid flashcards
        mixed_flashcards = self.sample_flashcards.copy()
        
        # Add an invalid flashcard by mocking validation to fail
        invalid_flashcard = Mock(spec=Flashcard)
        invalid_flashcard.validate.side_effect = ValueError("Invalid flashcard")
        mixed_flashcards.append(invalid_flashcard)
        
        csv_data = self.exporter._flashcards_to_csv_data(mixed_flashcards)
        
        # Should only have the valid flashcards
        assert len(csv_data) == 3
    
    def test_flashcards_to_csv_data_all_invalid(self):
        """Test conversion with all invalid flashcards."""
        invalid_flashcard = Mock(spec=Flashcard)
        invalid_flashcard.validate.side_effect = ValueError("Invalid flashcard")
        
        with pytest.raises(ValueError, match="No valid flashcards to export"):
            self.exporter._flashcards_to_csv_data([invalid_flashcard])
    
    def test_read_csv_file_success(self):
        """Test reading a CSV file."""
        # First create a CSV file
        csv_path = self.exporter.export_flashcards(self.sample_flashcards)
        
        # Then read it back
        csv_data = self.exporter.read_csv_file(csv_path)
        
        assert len(csv_data) == 3
        assert csv_data[0]['English'] == 'cat'
        assert csv_data[0]['Chinese'] == '猫'
    
    def test_read_csv_file_not_found(self):
        """Test reading a non-existent CSV file."""
        with pytest.raises(FileNotFoundError):
            self.exporter.read_csv_file("nonexistent.csv")
    
    def test_get_csv_stats(self):
        """Test getting CSV file statistics."""
        # Create a CSV file
        csv_path = self.exporter.export_flashcards(self.sample_flashcards)
        
        # Get stats
        stats = self.exporter.get_csv_stats(csv_path)
        
        assert stats['total_rows'] == 3
        assert set(self.exporter.required_columns).issubset(set(stats['columns']))
        assert stats['has_required_columns'] is True
        assert stats['file_size_bytes'] > 0
        assert stats['encoding'] == 'utf-8'
        assert 'column_stats' in stats
        
        # Check column stats
        english_stats = stats['column_stats']['English']
        assert english_stats['non_empty_count'] == 3
        assert english_stats['empty_count'] == 0
    
    def test_get_csv_stats_file_not_found(self):
        """Test getting stats for non-existent file."""
        with pytest.raises(RuntimeError):
            self.exporter.get_csv_stats("nonexistent.csv")
    
    def test_export_with_missing_optional_fields(self):
        """Test export with flashcards missing optional fields."""
        minimal_flashcard = Flashcard(
            english_word="test",
            chinese_translation="测试",
            pinyin="ceshi4"
            # No image_path, image_url, or topic
        )
        
        result_path = self.exporter.export_flashcards([minimal_flashcard])
        
        # Read and verify
        csv_data = self.exporter.read_csv_file(result_path)
        assert len(csv_data) == 1
        assert csv_data[0]['English'] == 'test'
        assert csv_data[0]['Chinese'] == '测试'
        assert csv_data[0]['Image_Path'] == ''
        assert csv_data[0]['Topic'] == ''
    
    def test_export_handles_image_url_fallback(self):
        """Test that export uses image_url when image_local_path is not available."""
        flashcard_with_url = Flashcard(
            english_word="test",
            chinese_translation="测试",
            pinyin="ceshi4",
            image_url="https://example.com/test.jpg"
            # No image_local_path
        )
        
        result_path = self.exporter.export_flashcards([flashcard_with_url])
        
        # Read and verify
        csv_data = self.exporter.read_csv_file(result_path)
        assert csv_data[0]['Image_Path'] == 'https://example.com/test.jpg'
    
    def test_csv_file_encoding(self):
        """Test that CSV files are properly encoded for Unicode."""
        unicode_flashcard = Flashcard(
            english_word="complex",
            chinese_translation="复杂的中文字符：测试",
            pinyin="fu4za2de5zhong1wen2zi4fu2"
        )
        
        result_path = self.exporter.export_flashcards([unicode_flashcard])
        
        # Read file directly to check encoding
        with open(result_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "复杂的中文字符：测试" in content
    
    def test_csv_delimiter_and_quoting(self):
        """Test CSV delimiter and quoting behavior."""
        flashcard_with_comma = Flashcard(
            english_word="word, with comma",
            chinese_translation="带逗号的词",
            pinyin="dai4dou4hao4de5ci2",
            topic="test, topic"
        )
        
        result_path = self.exporter.export_flashcards([flashcard_with_comma])
        
        # Read using csv module to verify proper parsing
        with open(result_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert row['English'] == "word, with comma"
            assert row['Topic'] == "test, topic"