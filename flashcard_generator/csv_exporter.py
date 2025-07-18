"""
CSV export functionality for flashcard data.
"""

import csv
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import re
from .models import Flashcard

logger = logging.getLogger(__name__)


class CSVExporter:
    """Handles CSV export of flashcard data with proper Unicode support."""
    
    def __init__(self, output_directory: str = "./flashcards"):
        """Initialize the CSV exporter with output directory."""
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        # CSV configuration
        self.encoding = 'utf-8'
        self.delimiter = ','
        self.quotechar = '"'
        self.quoting = csv.QUOTE_MINIMAL
        
        # Required CSV columns
        self.required_columns = [
            'English',
            'Chinese', 
            'Pinyin',
            'Image_Path',
            'Topic',
            'Created_Date'
        ]
    
    def export_flashcards(self, flashcards: List[Flashcard], filename: Optional[str] = None) -> str:
        """Export flashcards to CSV file."""
        if not flashcards:
            raise ValueError("Cannot export empty flashcard list")
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"flashcards_{timestamp}.csv"
        
        # Ensure filename has .csv extension
        if not filename.lower().endswith('.csv'):
            filename += '.csv'
        
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        file_path = self.output_directory / safe_filename
        
        try:
            # Convert flashcards to CSV data
            csv_data = self._flashcards_to_csv_data(flashcards)
            
            # Validate CSV data
            if not self.validate_csv_format(csv_data):
                raise ValueError("Generated CSV data failed validation")
            
            # Write CSV file
            with open(file_path, 'w', newline='', encoding=self.encoding) as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=self.required_columns,
                    delimiter=self.delimiter,
                    quotechar=self.quotechar,
                    quoting=self.quoting
                )
                
                # Write header
                writer.writeheader()
                
                # Write data rows
                writer.writerows(csv_data)
            
            logger.info(f"Successfully exported {len(flashcards)} flashcards to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to export flashcards to CSV: {e}")
            raise RuntimeError(f"CSV export failed: {e}")
    
    def validate_csv_format(self, data: List[Dict[str, Any]]) -> bool:
        """Validate CSV data format."""
        if not data:
            logger.warning("CSV data is empty")
            return False
        
        # Check that all required columns are present in each row
        for i, row in enumerate(data):
            if not isinstance(row, dict):
                logger.error(f"Row {i} is not a dictionary")
                return False
            
            # Check for required columns
            missing_columns = set(self.required_columns) - set(row.keys())
            if missing_columns:
                logger.error(f"Row {i} missing required columns: {missing_columns}")
                return False
            
            # Validate data types and content
            if not self._validate_row_content(row, i):
                return False
        
        logger.info(f"CSV data validation passed for {len(data)} rows")
        return True
    
    def _flashcards_to_csv_data(self, flashcards: List[Flashcard]) -> List[Dict[str, Any]]:
        """Convert flashcard objects to CSV data format."""
        csv_data = []
        
        for flashcard in flashcards:
            try:
                # Validate flashcard
                flashcard.validate()
                
                row = {
                    'English': self._escape_csv_value(flashcard.english_word),
                    'Chinese': self._escape_csv_value(flashcard.chinese_translation),
                    'Pinyin': self._escape_csv_value(flashcard.pinyin),
                    'Image_Path': self._escape_csv_value(flashcard.image_local_path or flashcard.image_url or ''),
                    'Topic': self._escape_csv_value(flashcard.topic or ''),
                    'Created_Date': flashcard.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                csv_data.append(row)
                
            except Exception as e:
                logger.warning(f"Skipping invalid flashcard: {e}")
                continue
        
        if not csv_data:
            raise ValueError("No valid flashcards to export")
        
        return csv_data
    
    def _validate_row_content(self, row: Dict[str, Any], row_index: int) -> bool:
        """Validate the content of a CSV row."""
        try:
            # Check English word
            english = row.get('English', '')
            if not english or not isinstance(english, str) or not english.strip():
                logger.error(f"Row {row_index}: English word is empty or invalid")
                return False
            
            # Check Chinese translation
            chinese = row.get('Chinese', '')
            if not chinese or not isinstance(chinese, str) or not chinese.strip():
                logger.error(f"Row {row_index}: Chinese translation is empty or invalid")
                return False
            
            # Validate Chinese contains Chinese characters
            if not re.search(r'[\u4e00-\u9fff]', chinese):
                logger.error(f"Row {row_index}: Chinese translation does not contain Chinese characters")
                return False
            
            # Check Pinyin
            pinyin = row.get('Pinyin', '')
            if not pinyin or not isinstance(pinyin, str) or not pinyin.strip():
                logger.error(f"Row {row_index}: Pinyin is empty or invalid")
                return False
            
            # Check Created_Date format
            created_date = row.get('Created_Date', '')
            if created_date:
                try:
                    datetime.strptime(created_date, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    logger.error(f"Row {row_index}: Invalid date format: {created_date}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating row {row_index}: {e}")
            return False
    
    def _escape_csv_value(self, value: Any) -> str:
        """Escape and sanitize CSV values."""
        if value is None:
            return ''
        
        # Convert to string
        str_value = str(value).strip()
        
        # Handle special characters that might cause CSV parsing issues
        # The csv module will handle proper quoting, but we ensure clean data
        return str_value
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system storage."""
        # Remove or replace invalid characters
        sanitized = re.sub(r'[^\w\s.-]', '', filename)
        sanitized = re.sub(r'\s+', '_', sanitized).strip('_')
        
        # Ensure it has .csv extension
        if not sanitized.lower().endswith('.csv'):
            sanitized += '.csv'
        
        # Limit length
        if len(sanitized) > 100:
            name, ext = sanitized.rsplit('.', 1)
            sanitized = name[:95] + '.' + ext
        
        return sanitized
    
    def read_csv_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Read and validate a CSV file (utility method for testing)."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        try:
            csv_data = []
            with open(file_path, 'r', encoding=self.encoding) as csvfile:
                reader = csv.DictReader(
                    csvfile,
                    delimiter=self.delimiter,
                    quotechar=self.quotechar
                )
                
                for row in reader:
                    csv_data.append(dict(row))
            
            logger.info(f"Successfully read {len(csv_data)} rows from {file_path}")
            return csv_data
            
        except Exception as e:
            logger.error(f"Failed to read CSV file {file_path}: {e}")
            raise RuntimeError(f"CSV read failed: {e}")
    
    def get_csv_stats(self, file_path: str) -> Dict[str, Any]:
        """Get statistics about a CSV file."""
        try:
            csv_data = self.read_csv_file(file_path)
            
            stats = {
                'total_rows': len(csv_data),
                'columns': list(csv_data[0].keys()) if csv_data else [],
                'has_required_columns': set(self.required_columns).issubset(set(csv_data[0].keys())) if csv_data else False,
                'file_size_bytes': Path(file_path).stat().st_size,
                'encoding': self.encoding
            }
            
            # Count non-empty values per column
            if csv_data:
                column_stats = {}
                for column in stats['columns']:
                    non_empty_count = sum(1 for row in csv_data if row.get(column, '').strip())
                    column_stats[column] = {
                        'non_empty_count': non_empty_count,
                        'empty_count': len(csv_data) - non_empty_count
                    }
                stats['column_stats'] = column_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get CSV stats for {file_path}: {e}")
            raise RuntimeError(f"Failed to get CSV stats: {e}")