"""
Main orchestrator class for the AI Flashcard Generator.

This module coordinates all components to generate flashcards with English words,
Chinese translations, pinyin, and relevant images.
"""

import logging
import time
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from .models import Flashcard, WordPair, Config
from .gemini_client import GeminiClient
from .image_fetcher import ImageFetcher
from .csv_exporter import CSVExporter
from .cache import WordPairCache, ImageCache
from .async_image_fetcher import AsyncImageFetcher
from .exceptions import (
    FlashcardGeneratorError, ConfigurationError, PartialResultsError,
    FileOperationError, ValidationError
)
from .logging_config import FlashcardLogger, get_user_friendly_error_message, log_system_info

logger = logging.getLogger(__name__)


class FlashcardGenerator:
    """Main orchestrator class that coordinates all flashcard generation components."""
    
    def __init__(self, config: Config):
        """Initialize the flashcard generator with configuration."""
        self.config = config
        
        # Setup enhanced logging first
        self.flashcard_logger = FlashcardLogger(
            "flashcard_generator", 
            str(Path(config.output_directory) / "logs")
        )
        self.logger = self.flashcard_logger.get_logger()
        
        # Log system information for debugging
        log_system_info(self.logger)
        
        try:
            # Initialize components with error handling
            self.gemini_client = GeminiClient(config.gemini_api_key)
            self.image_fetcher = ImageFetcher(
                api_key=config.image_api_key,
                output_directory=str(Path(config.output_directory) / "images")
            )
            self.csv_exporter = CSVExporter(config.output_directory)
            
            # Initialize advanced features
            if config.enable_caching:
                self.word_cache = WordPairCache(
                    cache_dir=str(Path(config.output_directory) / "cache"),
                    max_age_hours=config.cache_max_age_hours
                )
                self.image_cache = ImageCache(
                    cache_dir=str(Path(config.output_directory) / "cache"),
                    max_age_hours=config.cache_max_age_hours * 7  # Images cached longer
                )
            else:
                self.word_cache = None
                self.image_cache = None
            
            # Initialize async image fetcher if enabled
            if config.enable_async_images:
                self.async_image_fetcher = AsyncImageFetcher(
                    api_key=config.image_api_key,
                    output_directory=str(Path(config.output_directory) / "images"),
                    max_concurrent=config.max_concurrent_images,
                    enable_cache=config.enable_caching
                )
            else:
                self.async_image_fetcher = None
            
            self.logger.info("FlashcardGenerator initialized successfully")
            self.logger.info(f"Advanced features: caching={config.enable_caching}, async_images={config.enable_async_images}, batch_processing={config.enable_batch_processing}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize FlashcardGenerator: {e}")
            raise ConfigurationError(f"Initialization failed: {e}")
        
        # Statistics tracking with error details
        self.stats = {
            'total_requested': 0,
            'words_generated': 0,
            'images_downloaded': 0,
            'flashcards_created': 0,
            'errors': 0,
            'api_errors': 0,
            'image_errors': 0,
            'validation_errors': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Partial results storage
        self._partial_flashcards = []
    
    def generate_flashcards(self, topic: str, count: int, context: Optional[str] = None) -> List[Flashcard]:
        """Generate flashcards for a given topic and count with comprehensive error handling."""
        # Input validation with detailed error messages
        if not topic or not topic.strip():
            raise ValidationError("Topic cannot be empty", field="topic", value=topic)
        if count <= 0:
            raise ValidationError("Count must be greater than 0", field="count", value=str(count))
        if count > self.config.max_flashcards:
            raise ValidationError(
                f"Count cannot exceed {self.config.max_flashcards}", 
                field="count", 
                value=str(count),
                details={"max_allowed": self.config.max_flashcards}
            )
        
        self.stats['total_requested'] = count
        self.stats['start_time'] = datetime.now()
        self._partial_flashcards = []  # Reset partial results
        
        self.logger.info(f"Starting flashcard generation for topic: '{topic}', count: {count}")
        
        try:
            # Step 1: Authenticate with Gemini API
            print("🔐 Authenticating with Google Gemini API...")
            try:
                if not self.gemini_client.authenticate():
                    raise ConfigurationError("Failed to authenticate with Gemini API")
                print("✅ Authentication successful")
                self.logger.info("Gemini API authentication successful")
            except Exception as e:
                self.stats['api_errors'] += 1
                self.flashcard_logger.log_error_with_context(e, {"step": "authentication", "api": "gemini"})
                raise ConfigurationError(f"Authentication failed: {e}")
            
            # Step 2: Generate word pairs (with caching)
            print(f"🧠 Generating {count} word pairs for topic: '{topic}'...")
            try:
                word_pairs = None
                
                # Check cache first if enabled
                if self.word_cache:
                    word_pairs = self.word_cache.get_word_pairs(topic, count)
                    if word_pairs:
                        print(f"✅ Retrieved {len(word_pairs)} word pairs from cache")
                        self.logger.info(f"Cache hit: Retrieved {len(word_pairs)} word pairs for topic: {topic}")
                
                # Generate new word pairs if not cached
                if not word_pairs:
                    word_pairs = self.gemini_client.generate_word_pairs(topic, count, context)
                    
                    # Store in cache if enabled
                    if self.word_cache and word_pairs:
                        self.word_cache.store_word_pairs(topic, count, word_pairs)
                    
                    print(f"✅ Generated {len(word_pairs)} word pairs")
                    self.logger.info(f"Generated {len(word_pairs)} word pairs for topic: {topic}")
                
                self.stats['words_generated'] = len(word_pairs)
                
                if not word_pairs:
                    raise ValidationError("No word pairs were generated", field="word_pairs", details={"topic": topic})
                    
            except Exception as e:
                self.stats['api_errors'] += 1
                self.flashcard_logger.log_error_with_context(e, {"step": "word_generation", "topic": topic, "count": count})
                raise
            
            # Step 3: Create flashcards with images
            flashcards = []
            failed_words = []
            print(f"🖼️  Fetching images and creating flashcards...")
            
            # Create basic flashcards first
            basic_flashcards = []
            for word_pair in word_pairs:
                try:
                    flashcard = Flashcard(
                        english_word=word_pair.english,
                        chinese_translation=word_pair.chinese,
                        pinyin=word_pair.pinyin,
                        sentence=word_pair.sentence,
                        topic=topic
                    )
                    basic_flashcards.append(flashcard)
                except Exception as e:
                    self.stats['validation_errors'] += 1
                    self.logger.warning(f"Validation failed for word pair '{word_pair.english}': {e}")
                    failed_words.append(word_pair.english)
                    continue
            
            # Fetch images (async if enabled, otherwise sequential)
            if self.config.image_download_enabled and basic_flashcards:
                if self.config.enable_async_images and self.async_image_fetcher:
                    # Use async image fetching for better performance
                    print(f"  🚀 Using concurrent image fetching...")
                    import asyncio
                    image_results = asyncio.run(self._fetch_images_async([fc.english_word for fc in basic_flashcards]))
                    
                    # Apply image results to flashcards
                    for i, (query, image_path) in enumerate(image_results):
                        if i < len(basic_flashcards):
                            if image_path:
                                basic_flashcards[i].image_local_path = image_path
                                self.stats['images_downloaded'] += 1
                                print(f"    ✅ Image downloaded: {Path(image_path).name}")
                            else:
                                print(f"    ⚠️  No image found for: {query}")
                else:
                    # Use sequential image fetching
                    for i, flashcard in enumerate(basic_flashcards, 1):
                        print(f"  Processing {i}/{len(basic_flashcards)}: {flashcard.english_word}")
                        try:
                            image_path = self.image_fetcher.search_and_download(flashcard.english_word)
                            if image_path:
                                flashcard.image_local_path = image_path
                                self.stats['images_downloaded'] += 1
                                print(f"    ✅ Image downloaded: {Path(image_path).name}")
                                self.logger.debug(f"Image downloaded for '{flashcard.english_word}': {image_path}")
                            else:
                                print(f"    ⚠️  No image found for: {flashcard.english_word}")
                                self.logger.warning(f"No image found for: {flashcard.english_word}")
                        except Exception as e:
                            self.stats['image_errors'] += 1
                            self.flashcard_logger.log_error_with_context(
                                e, {"step": "image_fetch", "word": flashcard.english_word}
                            )
                            print(f"    ⚠️  Image fetch failed: {flashcard.english_word}")
                        
                        # Small delay to be respectful to APIs (only for sequential)
                        time.sleep(0.5)
            
            # Add all successfully created flashcards
            for flashcard in basic_flashcards:
                flashcards.append(flashcard)
                self._partial_flashcards.append(flashcard)
                self.stats['flashcards_created'] += 1
            
            self.stats['end_time'] = datetime.now()
            
            # Log generation statistics
            self.flashcard_logger.log_generation_stats(self.stats)
            
            # Handle partial success scenarios
            if not flashcards:
                raise PartialResultsError(
                    "No flashcards were successfully created",
                    successful_count=0,
                    failed_count=len(word_pairs),
                    details={"failed_words": failed_words, "topic": topic}
                )
            elif len(flashcards) < count:
                success_count = len(flashcards)
                failed_count = count - success_count
                self.logger.warning(f"Partial success: {success_count}/{count} flashcards created")
                
                # If less than 50% success, raise partial results error
                if success_count < count * 0.5:
                    raise PartialResultsError(
                        f"Only {success_count} out of {count} flashcards were created successfully",
                        successful_count=success_count,
                        failed_count=failed_count,
                        partial_results=flashcards,
                        details={"failed_words": failed_words, "topic": topic}
                    )
            
            print(f"✅ Created {len(flashcards)} flashcards successfully")
            self.logger.info(f"Successfully created {len(flashcards)} flashcards for topic: {topic}")
            return flashcards
            
        except Exception as e:
            self.stats['end_time'] = datetime.now()
            self.flashcard_logger.log_error_with_context(e, {"topic": topic, "count": count, "stats": self.stats})
            
            # Save partial results if any were created
            if self._partial_flashcards:
                try:
                    self._save_partial_results(topic)
                except Exception as save_error:
                    self.logger.error(f"Failed to save partial results: {save_error}")
            
            raise
    
    def run(self, topic: str, count: int, output_filename: Optional[str] = None, context: Optional[str] = None) -> str:
        """Run the complete flashcard generation process and return CSV file path."""
        try:
            # Generate flashcards
            flashcards = self.generate_flashcards(topic, count, context)
            
            # Export to CSV
            print("📄 Exporting flashcards to CSV...")
            csv_file_path = self.csv_exporter.export_flashcards(flashcards, output_filename)
            print(f"✅ CSV exported: {csv_file_path}")
            
            # Print summary
            self._print_summary(csv_file_path)
            
            return csv_file_path
            
        except Exception as e:
            logger.error(f"Flashcard generation process failed: {e}")
            
            # Try to save partial results if any flashcards were created
            if hasattr(self, '_partial_flashcards') and self._partial_flashcards:
                try:
                    print("💾 Saving partial results...")
                    partial_filename = f"partial_flashcards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    partial_path = self.csv_exporter.export_flashcards(self._partial_flashcards, partial_filename)
                    print(f"✅ Partial results saved: {partial_path}")
                except Exception as save_error:
                    logger.error(f"Failed to save partial results: {save_error}")
            
            raise RuntimeError(f"Flashcard generation failed: {e}")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        # Create logs directory
        logs_dir = Path(self.config.output_directory) / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        log_filename = logs_dir / f"flashcard_generator_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def _print_summary(self, csv_file_path: str):
        """Print generation summary statistics."""
        duration = None
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
        
        print("\n" + "="*50)
        print("📊 GENERATION SUMMARY")
        print("="*50)
        print(f"Requested flashcards: {self.stats['total_requested']}")
        print(f"Word pairs generated: {self.stats['words_generated']}")
        print(f"Images downloaded: {self.stats['images_downloaded']}")
        print(f"Flashcards created: {self.stats['flashcards_created']}")
        print(f"Errors encountered: {self.stats['errors']}")
        if duration:
            print(f"Total time: {duration.total_seconds():.1f} seconds")
        print(f"Output file: {csv_file_path}")
        
        # Success rate
        if self.stats['total_requested'] > 0:
            success_rate = (self.stats['flashcards_created'] / self.stats['total_requested']) * 100
            print(f"Success rate: {success_rate:.1f}%")
        
        print("="*50)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get generation statistics."""
        return self.stats.copy()
    
    def _save_partial_results(self, topic: str) -> Optional[str]:
        """Save partial results when generation fails."""
        if not self._partial_flashcards:
            return None
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            partial_filename = f"partial_{topic}_{timestamp}.csv"
            
            self.logger.info(f"Saving {len(self._partial_flashcards)} partial results to {partial_filename}")
            
            partial_path = self.csv_exporter.export_flashcards(self._partial_flashcards, partial_filename)
            
            print(f"💾 Partial results saved: {partial_path}")
            print(f"   {len(self._partial_flashcards)} flashcards were successfully created before the error occurred.")
            
            return partial_path
            
        except Exception as e:
            self.logger.error(f"Failed to save partial results: {e}")
            self.flashcard_logger.log_error_with_context(e, {"partial_count": len(self._partial_flashcards)})
            return None
    
    async def _fetch_images_async(self, queries: List[str]) -> List[tuple]:
        """Fetch images asynchronously for multiple queries."""
        if not self.async_image_fetcher:
            return [(query, None) for query in queries]
        
        try:
            return await self.async_image_fetcher.fetch_images_concurrent(queries)
        except Exception as e:
            self.logger.error(f"Async image fetching failed: {e}")
            return [(query, None) for query in queries]
    
    def cleanup_old_files(self, max_age_days: int = 30) -> Dict[str, int]:
        """Clean up old generated files."""
        cleanup_stats = {
            'images_cleaned': 0,
            'logs_cleaned': 0,
            'csv_cleaned': 0
        }
        
        try:
            # Clean up old images
            cleanup_stats['images_cleaned'] = self.image_fetcher.cleanup_old_images(max_age_days)
            
            # Clean up old log files
            logs_dir = Path(self.config.output_directory) / "logs"
            if logs_dir.exists():
                current_time = time.time()
                max_age_seconds = max_age_days * 24 * 60 * 60
                
                for log_file in logs_dir.glob("*.log"):
                    if log_file.is_file():
                        file_age = current_time - log_file.stat().st_mtime
                        if file_age > max_age_seconds:
                            log_file.unlink()
                            cleanup_stats['logs_cleaned'] += 1
            
            # Clean up old CSV files
            csv_dir = Path(self.config.output_directory)
            if csv_dir.exists():
                current_time = time.time()
                max_age_seconds = max_age_days * 24 * 60 * 60
                
                for csv_file in csv_dir.glob("*.csv"):
                    if csv_file.is_file():
                        file_age = current_time - csv_file.stat().st_mtime
                        if file_age > max_age_seconds:
                            csv_file.unlink()
                            cleanup_stats['csv_cleaned'] += 1
            
            logger.info(f"Cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return cleanup_stats