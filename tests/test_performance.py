"""
Performance tests for batch processing scenarios.

These tests verify that the system performs well under various load conditions
and can handle batch processing efficiently.
"""

import pytest
import tempfile
import shutil
import os
import time
import threading
from pathlib import Path
from unittest.mock import patch, Mock
import csv

from flashcard_generator.flashcard_generator import FlashcardGenerator
from flashcard_generator.models import Config, WordPair


class TestBatchProcessingPerformance:
    """Test performance with different batch sizes."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config(
            gemini_api_key="test_key",
            output_directory=self.temp_dir,
            max_flashcards=50,
            image_download_enabled=False  # Disable for performance tests
        )
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_single_flashcard_generation_time(self):
        """Test time to generate a single flashcard."""
        generator = FlashcardGenerator(self.config)
        
        mock_word_pairs = [
            WordPair(english="test", chinese="测试", pinyin="ce4 shi4")
        ]
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                
                start_time = time.time()
                csv_file_path = generator.run("test", 1)
                end_time = time.time()
                
                generation_time = end_time - start_time
                
                # Should complete quickly for a single flashcard
                assert generation_time < 10.0, f"Single flashcard took {generation_time:.2f}s (too slow)"
                assert os.path.exists(csv_file_path)
                
                print(f"Single flashcard generation time: {generation_time:.3f}s")
    
    def test_batch_processing_scalability(self):
        """Test performance scaling with different batch sizes."""
        generator = FlashcardGenerator(self.config)
        
        batch_sizes = [5, 10, 15, 20]
        performance_data = []
        
        for batch_size in batch_sizes:
            # Generate mock word pairs
            mock_word_pairs = []
            for i in range(batch_size):
                mock_word_pairs.append(
                    WordPair(english=f"word{i}", chinese=f"词{i}", pinyin=f"ci{i}")
                )
            
            with patch.object(generator.gemini_client, 'authenticate', return_value=True):
                with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                    
                    start_time = time.time()
                    csv_file_path = generator.run(f"batch_{batch_size}", batch_size)
                    end_time = time.time()
                    
                    generation_time = end_time - start_time
                    time_per_card = generation_time / batch_size
                    
                    performance_data.append({
                        'batch_size': batch_size,
                        'total_time': generation_time,
                        'time_per_card': time_per_card
                    })
                    
                    # Verify results
                    assert os.path.exists(csv_file_path)
                    stats = generator.get_stats()
                    assert stats['flashcards_created'] == batch_size
                    
                    print(f"Batch {batch_size}: {generation_time:.3f}s total, {time_per_card:.3f}s per card")
        
        # Analyze scaling
        self._analyze_scaling_performance(performance_data)
    
    def test_maximum_batch_size_performance(self):
        """Test performance with maximum allowed batch size."""
        generator = FlashcardGenerator(self.config)
        
        max_batch_size = self.config.max_flashcards
        
        # Generate maximum number of mock word pairs
        mock_word_pairs = []
        for i in range(max_batch_size):
            mock_word_pairs.append(
                WordPair(english=f"max_word_{i}", chinese=f"最大词{i}", pinyin=f"zui4 da4 ci2")
            )
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                
                start_time = time.time()
                csv_file_path = generator.run("max_batch", max_batch_size)
                end_time = time.time()
                
                generation_time = end_time - start_time
                
                # Should complete within reasonable time (2 minutes for max batch)
                assert generation_time < 120, f"Max batch took {generation_time:.2f}s (too slow)"
                
                # Verify all flashcards were created
                with open(csv_file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                
                assert len(rows) == max_batch_size
                
                print(f"Maximum batch ({max_batch_size} cards): {generation_time:.2f}s")
    
    def test_concurrent_generation_performance(self):
        """Test performance when running multiple generations concurrently."""
        def generate_flashcards(topic, count, results_list):
            """Generate flashcards in a separate thread."""
            try:
                temp_dir = tempfile.mkdtemp()
                config = Config(
                    gemini_api_key="test_key",
                    output_directory=temp_dir,
                    image_download_enabled=False
                )
                generator = FlashcardGenerator(config)
                
                mock_word_pairs = [
                    WordPair(english=f"{topic}_word", chinese=f"{topic}_词", pinyin=f"{topic}_ci")
                    for _ in range(count)
                ]
                
                with patch.object(generator.gemini_client, 'authenticate', return_value=True):
                    with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                        
                        start_time = time.time()
                        csv_file_path = generator.run(topic, count)
                        end_time = time.time()
                        
                        results_list.append({
                            'topic': topic,
                            'count': count,
                            'time': end_time - start_time,
                            'success': os.path.exists(csv_file_path),
                            'temp_dir': temp_dir
                        })
                        
            except Exception as e:
                results_list.append({
                    'topic': topic,
                    'count': count,
                    'error': str(e),
                    'success': False
                })
        
        # Run multiple concurrent generations
        threads = []
        results = []
        
        topics_and_counts = [
            ("animals", 3),
            ("food", 4),
            ("colors", 2),
            ("numbers", 5),
        ]
        
        concurrent_start_time = time.time()
        
        # Start threads
        for topic, count in topics_and_counts:
            thread = threading.Thread(target=generate_flashcards, args=(topic, count, results))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=60)  # 60 second timeout
        
        concurrent_end_time = time.time()
        total_concurrent_time = concurrent_end_time - concurrent_start_time
        
        # Verify results
        assert len(results) == len(topics_and_counts)
        
        successful_results = [r for r in results if r['success']]
        assert len(successful_results) == len(topics_and_counts), "Some concurrent generations failed"
        
        # Calculate total sequential time for comparison
        total_sequential_time = sum(r['time'] for r in successful_results)
        
        print(f"Concurrent processing:")
        print(f"  Total concurrent time: {total_concurrent_time:.2f}s")
        print(f"  Total sequential time: {total_sequential_time:.2f}s")
        print(f"  Speedup: {total_sequential_time / total_concurrent_time:.2f}x")
        
        # Clean up temporary directories
        for result in results:
            if 'temp_dir' in result and os.path.exists(result['temp_dir']):
                shutil.rmtree(result['temp_dir'])
    
    def test_memory_usage_with_large_batches(self):
        """Test that memory usage doesn't grow excessively with large batches."""
        generator = FlashcardGenerator(self.config)
        
        # Test with a reasonably large batch
        batch_size = 25
        mock_word_pairs = []
        for i in range(batch_size):
            mock_word_pairs.append(
                WordPair(
                    english=f"memory_test_word_{i:03d}",
                    chinese=f"内存测试词{i:03d}",
                    pinyin=f"nei4 cun2 ce4 shi4 ci2"
                )
            )
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                
                csv_file_path = generator.run("memory_test", batch_size)
                
                # Verify all flashcards were processed
                with open(csv_file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                
                assert len(rows) == batch_size
                
                # Verify statistics
                stats = generator.get_stats()
                assert stats['flashcards_created'] == batch_size
                
                print(f"Memory test completed: {batch_size} flashcards processed")
    
    def test_file_io_performance(self):
        """Test file I/O performance with different file sizes."""
        generator = FlashcardGenerator(self.config)
        
        file_sizes = [5, 15, 30]  # Different numbers of flashcards
        
        for size in file_sizes:
            mock_word_pairs = []
            for i in range(size):
                mock_word_pairs.append(
                    WordPair(
                        english=f"io_test_word_{i:03d}",
                        chinese=f"输入输出测试词{i:03d}",
                        pinyin=f"shu1 ru4 shu1 chu1 ce4 shi4 ci2"
                    )
                )
            
            with patch.object(generator.gemini_client, 'authenticate', return_value=True):
                with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                    
                    start_time = time.time()
                    csv_file_path = generator.run(f"io_test_{size}", size)
                    end_time = time.time()
                    
                    io_time = end_time - start_time
                    file_size_bytes = os.path.getsize(csv_file_path)
                    
                    print(f"File I/O test - {size} cards: {io_time:.3f}s, {file_size_bytes} bytes")
                    
                    # Verify file integrity
                    with open(csv_file_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                    
                    assert len(rows) == size
    
    def _analyze_scaling_performance(self, performance_data):
        """Analyze performance scaling characteristics."""
        print("\nPerformance Scaling Analysis:")
        print("Batch Size | Total Time | Time/Card | Efficiency")
        print("-" * 50)
        
        baseline_time_per_card = performance_data[0]['time_per_card']
        
        for data in performance_data:
            efficiency = baseline_time_per_card / data['time_per_card'] * 100
            print(f"{data['batch_size']:9d} | {data['total_time']:9.3f}s | {data['time_per_card']:8.3f}s | {efficiency:8.1f}%")
        
        # Check that scaling is reasonable (time per card shouldn't increase dramatically)
        max_time_per_card = max(d['time_per_card'] for d in performance_data)
        min_time_per_card = min(d['time_per_card'] for d in performance_data)
        scaling_ratio = max_time_per_card / min_time_per_card
        
        assert scaling_ratio < 5.0, f"Performance degrades too much with scale (ratio: {scaling_ratio:.2f})"


class TestResourceManagement:
    """Test resource management during batch processing."""
    
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
    
    def test_file_handle_management(self):
        """Test that file handles are properly managed during batch processing."""
        generator = FlashcardGenerator(self.config)
        
        mock_word_pairs = [
            WordPair(english="handle_test", chinese="句柄测试", pinyin="ju4 bing3 ce4 shi4")
        ]
        
        # Generate multiple files to test file handle management
        for i in range(10):
            with patch.object(generator.gemini_client, 'authenticate', return_value=True):
                with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                    
                    csv_file_path = generator.run(f"handle_test_{i}", 1)
                    assert os.path.exists(csv_file_path)
        
        # Verify all files were created successfully
        csv_files = list(Path(self.temp_dir).glob("*.csv"))
        assert len(csv_files) == 10
    
    def test_temporary_file_cleanup(self):
        """Test that temporary files are properly cleaned up."""
        generator = FlashcardGenerator(self.config)
        
        mock_word_pairs = [
            WordPair(english="cleanup_test", chinese="清理测试", pinyin="qing1 li3 ce4 shi4")
        ]
        
        # Count files before
        output_dir = Path(self.temp_dir)
        initial_file_count = len(list(output_dir.rglob("*"))) if output_dir.exists() else 0
        
        with patch.object(generator.gemini_client, 'authenticate', return_value=True):
            with patch.object(generator.gemini_client, 'generate_word_pairs', return_value=mock_word_pairs):
                
                csv_file_path = generator.run("cleanup_test", 1)
                assert os.path.exists(csv_file_path)
        
        # Count files after
        final_file_count = len(list(output_dir.rglob("*")))
        
        # Should only have expected files (CSV, logs, directories)
        expected_increase = 5  # CSV file + log files + directories
        actual_increase = final_file_count - initial_file_count
        
        print(f"Files created: {actual_increase} (expected: ~{expected_increase})")
        
        # Should not create excessive temporary files
        assert actual_increase <= expected_increase + 3, f"Too many files created: {actual_increase}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])