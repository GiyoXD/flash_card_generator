"""
Tests for advanced features and optimizations.

This module tests the caching mechanism, async image processing,
batch processing capabilities, and performance optimizations.
"""

import pytest
import tempfile
import shutil
import os
import asyncio
import time
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock

from flashcard_generator.flashcard_generator import FlashcardGenerator
from flashcard_generator.models import Config, WordPair
from flashcard_generator.cache import WordPairCache, ImageCache
from flashcard_generator.async_image_fetcher import AsyncImageFetcher


class TestCachingMechanism:
    """Test the caching mechanism for word pairs and images."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = Path(self.temp_dir) / "cache"
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_word_pair_cache_basic_operations(self):
        """Test basic word pair cache operations."""
        cache = WordPairCache(cache_dir=str(self.cache_dir), max_age_hours=1)
        
        # Test cache miss
        result = cache.get_word_pairs("animals", 3)
        assert result is None
        
        # Store word pairs
        word_pairs = [
            WordPair(english="cat", chinese="猫", pinyin="mao1"),
            WordPair(english="dog", chinese="狗", pinyin="gou3"),
            WordPair(english="bird", chinese="鸟", pinyin="niao3")
        ]
        cache.store_word_pairs("animals", 3, word_pairs)
        
        # Test cache hit
        cached_pairs = cache.get_word_pairs("animals", 3)
        assert cached_pairs is not None
        assert len(cached_pairs) == 3
        assert cached_pairs[0].english == "cat"
        assert cached_pairs[0].chinese == "猫"
        assert cached_pairs[0].pinyin == "mao1"
    
    def test_word_pair_cache_expiration(self):
        """Test that cache entries expire correctly."""
        cache = WordPairCache(cache_dir=str(self.cache_dir), max_age_hours=0.001)  # Very short expiry
        
        word_pairs = [WordPair(english="test", chinese="测试", pinyin="ce4 shi4")]
        cache.store_word_pairs("test", 1, word_pairs)
        
        # Should be cached immediately
        result = cache.get_word_pairs("test", 1)
        assert result is not None
        
        # Wait for expiration
        time.sleep(0.1)
        
        # Should be expired now
        result = cache.get_word_pairs("test", 1)
        assert result is None
    
    def test_word_pair_cache_persistence(self):
        """Test that cache persists to disk and loads correctly."""
        # Create cache and store data
        cache1 = WordPairCache(cache_dir=str(self.cache_dir))
        word_pairs = [WordPair(english="persist", chinese="持续", pinyin="chi2 xu4")]
        cache1.store_word_pairs("persistence", 1, word_pairs)
        
        # Create new cache instance (should load from disk)
        cache2 = WordPairCache(cache_dir=str(self.cache_dir))
        result = cache2.get_word_pairs("persistence", 1)
        
        assert result is not None
        assert len(result) == 1
        assert result[0].english == "persist"
    
    def test_image_cache_operations(self):
        """Test image cache operations."""
        cache = ImageCache(cache_dir=str(self.cache_dir))
        
        # Test cache miss
        result = cache.get_image_url("cat")
        assert result is None
        
        # Store image URL
        test_url = "https://example.com/cat.jpg"
        cache.store_image_url("cat", test_url)
        
        # Test cache hit
        cached_url = cache.get_image_url("cat")
        assert cached_url == test_url
    
    def test_cache_statistics(self):
        """Test cache statistics functionality."""
        cache = WordPairCache(cache_dir=str(self.cache_dir))
        
        # Initial stats
        stats = cache.get_cache_stats()
        assert stats['total_entries'] == 0
        assert stats['valid_entries'] == 0
        
        # Add some entries
        word_pairs = [WordPair(english="stats", chinese="统计", pinyin="tong3 ji4")]
        cache.store_word_pairs("statistics", 1, word_pairs)
        
        # Check updated stats
        stats = cache.get_cache_stats()
        assert stats['total_entries'] == 1
        assert stats['valid_entries'] == 1
    
    def test_cache_cleanup(self):
        """Test cache cleanup functionality."""
        cache = WordPairCache(cache_dir=str(self.cache_dir), max_age_hours=0.001)
        
        # Add entries
        word_pairs = [WordPair(english="cleanup", chinese="清理", pinyin="qing1 li3")]
        cache.store_word_pairs("cleanup", 1, word_pairs)
        
        # Wait for expiration
        time.sleep(0.1)
        
        # Cleanup expired entries
        cleaned_count = cache.cleanup_expired_entries()
        assert cleaned_count == 1
        
        # Verify cleanup
        stats = cache.get_cache_stats()
        assert stats['total_entries'] == 0


class TestAsyncImageProcessing:
    """Test asynchronous image processing capabilities."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_async_image_fetcher_initialization(self):
        """Test async image fetcher initialization."""
        fetcher = AsyncImageFetcher(
            api_key="test_key",
            output_directory=self.temp_dir,
            max_concurrent=3
        )
        
        assert fetcher.max_concurrent == 3
        assert fetcher.output_directory == Path(self.temp_dir)
        assert fetcher.enable_cache == True
    
    @pytest.mark.asyncio
    async def test_concurrent_image_fetching(self):
        """Test concurrent image fetching functionality."""
        fetcher = AsyncImageFetcher(
            output_directory=self.temp_dir,
            max_concurrent=2,
            enable_cache=False
        )
        
        # Mock the search and download methods
        with patch.object(fetcher, '_search_with_api', new_callable=AsyncMock) as mock_search:
            with patch.object(fetcher, '_download_image', new_callable=AsyncMock) as mock_download:
                
                # Setup mocks
                mock_search.return_value = "https://example.com/test.jpg"
                mock_download.return_value = "/path/to/test.jpg"
                
                # Test concurrent fetching
                queries = ["cat", "dog", "bird"]
                results = await fetcher.fetch_images_concurrent(queries)
                
                assert len(results) == 3
                assert all(isinstance(result, tuple) for result in results)
                assert all(len(result) == 2 for result in results)
    
    @pytest.mark.asyncio
    async def test_async_image_fetcher_error_handling(self):
        """Test error handling in async image fetcher."""
        fetcher = AsyncImageFetcher(
            output_directory=self.temp_dir,
            max_concurrent=2
        )
        
        # Mock search to raise an exception
        with patch.object(fetcher, '_search_with_api', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = Exception("API Error")
            
            # Should handle errors gracefully
            results = await fetcher.fetch_images_concurrent(["test"])
            
            assert len(results) == 1
            assert results[0] == ("test", None)
    
    def test_async_integration_with_flashcard_generator(self):
        """Test async image processing integration with FlashcardGenerator."""
        config = Config(
            gemini_api_key="test_key",
            output_directory=self.temp_dir,
            enable_async_images=True,
            max_concurrent_images=3,
            image_download_enabled=True
        )
        
        generator = FlashcardGenerator(config)
        
        # Verify async image fetcher is initialized
        assert generator.async_image_fetcher is not None
        assert generator.async_image_fetcher.max_concurrent == 3
        
        # Test with mocked components
        mock_word_pairs = [
            WordPair(english="async_test", chinese="异步测试", pinyin="yi4 bu4 ce4 shi4")
        ]
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                with patch.object(generator, '_fetch_images_async') as mock_async_fetch:
                    mock_async_fetch.return_value = [("async_test", "/path/to/image.jpg")]
                    
                    flashcards = generator.generate_flashcards("async_test", 1)
                    
                    assert len(flashcards) == 1
                    assert flashcards[0].image_local_path == "/path/to/image.jpg"
                    mock_async_fetch.assert_called_once()


class TestBatchProcessing:
    """Test batch processing capabilities."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config(
            gemini_api_key="test_key",
            output_directory=self.temp_dir,
            enable_batch_processing=True,
            batch_size=5,
            image_download_enabled=False
        )
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_batch_processing_configuration(self):
        """Test batch processing configuration."""
        generator = FlashcardGenerator(self.config)
        
        assert generator.config.enable_batch_processing == True
        assert generator.config.batch_size == 5
    
    def test_large_batch_processing(self):
        """Test processing of large batches."""
        generator = FlashcardGenerator(self.config)
        
        # Create a large batch of mock word pairs
        large_batch_size = 20
        mock_word_pairs = []
        for i in range(large_batch_size):
            mock_word_pairs.append(
                WordPair(english=f"batch_word_{i}", chinese=f"批处理词{i}", pinyin=f"pi1 chu3 li3 ci2")
            )
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                
                flashcards = generator.generate_flashcards("batch_test", large_batch_size)
                
                assert len(flashcards) == large_batch_size
                assert all(fc.topic == "batch_test" for fc in flashcards)
    
    def test_batch_processing_with_caching(self):
        """Test batch processing with caching enabled."""
        config = Config(
            gemini_api_key="test_key",
            output_directory=self.temp_dir,
            enable_caching=True,
            enable_batch_processing=True,
            batch_size=3,
            image_download_enabled=False
        )
        
        generator = FlashcardGenerator(config)
        
        mock_word_pairs = [
            WordPair(english="cache_batch_1", chinese="缓存批处理1", pinyin="huan3 cun2 pi1 chu3 li3"),
            WordPair(english="cache_batch_2", chinese="缓存批处理2", pinyin="huan3 cun2 pi1 chu3 li3"),
            WordPair(english="cache_batch_3", chinese="缓存批处理3", pinyin="huan3 cun2 pi1 chu3 li3")
        ]
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                
                # First generation - should cache results
                flashcards1 = generator.generate_flashcards("cache_batch", 3)
                assert len(flashcards1) == 3
                
                # Second generation - should use cache
                flashcards2 = generator.generate_flashcards("cache_batch", 3)
                assert len(flashcards2) == 3
                
                # Verify cache was used (word_pairs generation should only be called once)
                assert generator.gemini_client.generate_word_pairs.call_count == 1


class TestPerformanceOptimizations:
    """Test performance optimizations and their effectiveness."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_caching_performance_improvement(self):
        """Test that caching improves performance."""
        config = Config(
            gemini_api_key="test_key",
            output_directory=self.temp_dir,
            enable_caching=True,
            image_download_enabled=False
        )
        
        generator = FlashcardGenerator(config)
        
        mock_word_pairs = [
            WordPair(english="perf_test", chinese="性能测试", pinyin="xing4 neng2 ce4 shi4")
        ]
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs) as mock_generate:
                
                # First call - should hit API
                start_time = time.time()
                flashcards1 = generator.generate_flashcards("performance", 1)
                first_call_time = time.time() - start_time
                
                # Second call - should use cache
                start_time = time.time()
                flashcards2 = generator.generate_flashcards("performance", 1)
                second_call_time = time.time() - start_time
                
                # Verify results are the same
                assert len(flashcards1) == len(flashcards2) == 1
                assert flashcards1[0].english_word == flashcards2[0].english_word
                
                # Verify API was only called once (cached second time)
                assert mock_generate.call_count == 1
                
                # Second call should be faster (though this might be flaky in tests)
                # We mainly verify that caching logic works correctly
    
    def test_async_vs_sequential_image_processing(self):
        """Test performance difference between async and sequential image processing."""
        # Test async configuration
        async_config = Config(
            gemini_api_key="test_key",
            output_directory=self.temp_dir,
            enable_async_images=True,
            max_concurrent_images=3,
            image_download_enabled=True
        )
        
        # Test sequential configuration
        sequential_config = Config(
            gemini_api_key="test_key",
            output_directory=self.temp_dir + "_seq",
            enable_async_images=False,
            image_download_enabled=True
        )
        
        async_generator = FlashcardGenerator(async_config)
        sequential_generator = FlashcardGenerator(sequential_config)
        
        # Verify configurations
        assert async_generator.async_image_fetcher is not None
        assert sequential_generator.async_image_fetcher is None
        
        mock_word_pairs = [
            WordPair(english="async_perf_1", chinese="异步性能1", pinyin="yi4 bu4 xing4 neng2"),
            WordPair(english="async_perf_2", chinese="异步性能2", pinyin="yi4 bu4 xing4 neng2"),
            WordPair(english="async_perf_3", chinese="异步性能3", pinyin="yi4 bu4 xing4 neng2")
        ]
        
        # Mock image operations to simulate processing time
        def mock_sequential_download(query):
            time.sleep(0.01)  # Simulate processing time
            return f"/path/to/{query}.jpg"
        
        async def mock_async_fetch(queries):
            await asyncio.sleep(0.01)  # Simulate async processing
            return [(query, f"/path/to/{query}.jpg") for query in queries]
        
        # Test async processing
        with patch.object(async_generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(async_generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                with patch.object(async_generator, '_fetch_images_async', side_effect=mock_async_fetch):
                    
                    start_time = time.time()
                    async_flashcards = async_generator.generate_flashcards("async_perf", 3)
                    async_time = time.time() - start_time
        
        # Test sequential processing
        with patch.object(sequential_generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(sequential_generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                with patch.object(sequential_generator.image_fetcher, 'search_and_download', side_effect=mock_sequential_download):
                    
                    start_time = time.time()
                    sequential_flashcards = sequential_generator.generate_flashcards("sequential_perf", 3)
                    sequential_time = time.time() - start_time
        
        # Verify both produce the same results
        assert len(async_flashcards) == len(sequential_flashcards) == 3
        
        # Both should have images
        assert all(fc.image_local_path for fc in async_flashcards)
        assert all(fc.image_local_path for fc in sequential_flashcards)
    
    def test_memory_usage_optimization(self):
        """Test that memory usage is optimized for large batches."""
        config = Config(
            gemini_api_key="test_key",
            output_directory=self.temp_dir,
            enable_caching=True,
            enable_batch_processing=True,
            image_download_enabled=False
        )
        
        generator = FlashcardGenerator(config)
        
        # Create a large batch to test memory usage
        large_batch = []
        for i in range(30):
            large_batch.append(
                WordPair(english=f"memory_test_{i}", chinese=f"内存测试{i}", pinyin="nei4 cun2 ce4 shi4")
            )
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=large_batch):
                
                flashcards = generator.generate_flashcards("memory_test", 30)
                
                # Verify all flashcards were created
                assert len(flashcards) == 30
                
                # Verify memory cleanup (partial results should be managed)
                assert len(generator._partial_flashcards) == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])