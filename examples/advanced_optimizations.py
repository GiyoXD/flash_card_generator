#!/usr/bin/env python3
"""
Advanced optimizations example for the AI Flashcard Generator.

This example demonstrates the advanced features:
- Caching mechanism for improved performance
- Asynchronous image processing for concurrent downloads
- Batch processing capabilities
- Performance monitoring and statistics
"""

import os
import sys
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flashcard_generator.config import ConfigManager
from flashcard_generator.flashcard_generator import FlashcardGenerator
from flashcard_generator.models import Config


def create_optimized_config():
    """Create a configuration with all optimizations enabled."""
    return Config(
        gemini_api_key=os.getenv('GEMINI_API_KEY', 'your_api_key_here'),
        image_api_key=os.getenv('IMAGE_API_KEY'),
        output_directory="./optimized_flashcards",
        max_flashcards=50,
        image_download_enabled=True,
        
        # Advanced optimizations
        enable_caching=True,
        cache_max_age_hours=48,  # Cache for 2 days
        enable_async_images=True,
        max_concurrent_images=8,  # Higher concurrency
        enable_batch_processing=True,
        batch_size=15
    )


def demonstrate_caching_benefits(generator):
    """Demonstrate the benefits of caching."""
    print("🗄️  CACHING DEMONSTRATION")
    print("=" * 40)
    
    topic = "technology"
    count = 5
    
    # First generation (no cache)
    print(f"First generation for '{topic}' (no cache)...")
    start_time = time.time()
    
    try:
        csv_file1 = generator.run(topic, count, f"{topic}_first.csv")
        first_time = time.time() - start_time
        print(f"✅ First generation completed in {first_time:.2f} seconds")
        
        # Second generation (with cache)
        print(f"\nSecond generation for '{topic}' (with cache)...")
        start_time = time.time()
        csv_file2 = generator.run(topic, count, f"{topic}_second.csv")
        second_time = time.time() - start_time
        print(f"✅ Second generation completed in {second_time:.2f} seconds")
        
        # Show cache benefits
        if second_time < first_time:
            speedup = first_time / second_time
            print(f"🚀 Cache speedup: {speedup:.2f}x faster!")
        else:
            print("📊 Cache performance: Similar timing (cache overhead minimal)")
        
        # Show cache statistics
        if generator.word_cache:
            cache_stats = generator.word_cache.get_cache_stats()
            print(f"\n📈 Cache Statistics:")
            print(f"   Total entries: {cache_stats['total_entries']}")
            print(f"   Valid entries: {cache_stats['valid_entries']}")
            print(f"   Cache file size: {cache_stats['cache_file_size_bytes']} bytes")
        
        return [csv_file1, csv_file2]
        
    except Exception as e:
        print(f"❌ Caching demonstration failed: {e}")
        return []


def demonstrate_async_processing(generator):
    """Demonstrate asynchronous image processing."""
    print("\n⚡ ASYNC PROCESSING DEMONSTRATION")
    print("=" * 40)
    
    if not generator.async_image_fetcher:
        print("❌ Async processing not enabled")
        return None
    
    print(f"Max concurrent downloads: {generator.config.max_concurrent_images}")
    
    # Generate flashcards with images
    topic = "nature"
    count = 8
    
    print(f"Generating {count} flashcards with concurrent image processing...")
    start_time = time.time()
    
    try:
        csv_file = generator.run(topic, count, f"{topic}_async.csv")
        async_time = time.time() - start_time
        
        stats = generator.get_stats()
        images_downloaded = stats['images_downloaded']
        
        print(f"✅ Async processing completed in {async_time:.2f} seconds")
        print(f"📊 Images downloaded: {images_downloaded}/{count}")
        
        if images_downloaded > 0:
            avg_time_per_image = async_time / images_downloaded
            print(f"⚡ Average time per image: {avg_time_per_image:.2f} seconds")
        
        return csv_file
        
    except Exception as e:
        print(f"❌ Async processing demonstration failed: {e}")
        return None


def demonstrate_batch_processing(generator):
    """Demonstrate batch processing capabilities."""
    print("\n📦 BATCH PROCESSING DEMONSTRATION")
    print("=" * 40)
    
    print(f"Batch size: {generator.config.batch_size}")
    print(f"Batch processing enabled: {generator.config.enable_batch_processing}")
    
    # Process multiple topics in batches
    batch_topics = [
        ("science", 6),
        ("history", 4),
        ("geography", 5),
        ("literature", 3)
    ]
    
    print(f"Processing {len(batch_topics)} topics in batches...")
    
    batch_results = []
    total_start_time = time.time()
    
    for i, (topic, count) in enumerate(batch_topics, 1):
        print(f"\n[{i}/{len(batch_topics)}] Processing '{topic}' ({count} cards)...")
        
        try:
            start_time = time.time()
            csv_file = generator.run(topic, count, f"batch_{topic}.csv")
            processing_time = time.time() - start_time
            
            stats = generator.get_stats()
            
            batch_results.append({
                'topic': topic,
                'count': count,
                'time': processing_time,
                'csv_file': csv_file,
                'success_rate': (stats['flashcards_created'] / stats['total_requested']) * 100
            })
            
            print(f"✅ Completed in {processing_time:.2f}s, success rate: {batch_results[-1]['success_rate']:.1f}%")
            
        except Exception as e:
            print(f"❌ Failed to process '{topic}': {e}")
            batch_results.append({
                'topic': topic,
                'count': count,
                'error': str(e),
                'success': False
            })
    
    total_time = time.time() - total_start_time
    
    # Summary
    successful_batches = [r for r in batch_results if 'csv_file' in r]
    total_cards = sum(r['count'] for r in successful_batches)
    
    print(f"\n📊 Batch Processing Summary:")
    print(f"   Total batches: {len(batch_topics)}")
    print(f"   Successful batches: {len(successful_batches)}")
    print(f"   Total cards generated: {total_cards}")
    print(f"   Total time: {total_time:.2f} seconds")
    print(f"   Average time per card: {total_time / total_cards:.2f} seconds")
    
    return batch_results


def analyze_performance_optimizations(generator):
    """Analyze the effectiveness of performance optimizations."""
    print("\n📈 PERFORMANCE ANALYSIS")
    print("=" * 40)
    
    # Get final statistics
    stats = generator.get_stats()
    
    print("Optimization Features:")
    print(f"   ✅ Caching: {'Enabled' if generator.word_cache else 'Disabled'}")
    print(f"   ✅ Async Images: {'Enabled' if generator.async_image_fetcher else 'Disabled'}")
    print(f"   ✅ Batch Processing: {'Enabled' if generator.config.enable_batch_processing else 'Disabled'}")
    
    if generator.word_cache:
        cache_stats = generator.word_cache.get_cache_stats()
        print(f"\nCache Performance:")
        print(f"   Cache entries: {cache_stats['valid_entries']}")
        print(f"   Cache hit rate: Improved subsequent generations")
    
    if generator.async_image_fetcher:
        print(f"\nAsync Processing:")
        print(f"   Max concurrent: {generator.config.max_concurrent_images}")
        print(f"   Concurrent downloads: Improved image fetch speed")
    
    print(f"\nBatch Processing:")
    print(f"   Batch size: {generator.config.batch_size}")
    print(f"   Optimized for: Large-scale generation")


def main():
    """Advanced optimizations demonstration."""
    print("🚀 AI Flashcard Generator - Advanced Optimizations Demo")
    print("=" * 60)
    
    try:
        # Create optimized configuration
        config = create_optimized_config()
        print("✅ Optimized configuration created")
        print(f"   Caching: {config.enable_caching}")
        print(f"   Async images: {config.enable_async_images} (max concurrent: {config.max_concurrent_images})")
        print(f"   Batch processing: {config.enable_batch_processing} (batch size: {config.batch_size})")
        
        # Initialize generator
        generator = FlashcardGenerator(config)
        print("✅ FlashcardGenerator initialized with optimizations")
        
        # Demonstrate caching benefits
        cache_files = demonstrate_caching_benefits(generator)
        
        # Demonstrate async processing
        async_file = demonstrate_async_processing(generator)
        
        # Demonstrate batch processing
        batch_results = demonstrate_batch_processing(generator)
        
        # Analyze performance
        analyze_performance_optimizations(generator)
        
        # Final summary
        print(f"\n🎉 OPTIMIZATION DEMO COMPLETE")
        print("=" * 40)
        
        all_files = cache_files + ([async_file] if async_file else [])
        all_files += [r['csv_file'] for r in batch_results if 'csv_file' in r]
        
        print(f"Generated {len(all_files)} CSV files with optimizations:")
        for file_path in all_files:
            if file_path:
                print(f"   • {Path(file_path).name}")
        
        print(f"\n💡 OPTIMIZATION BENEFITS:")
        print("   • Caching: Faster repeated generations")
        print("   • Async processing: Concurrent image downloads")
        print("   • Batch processing: Efficient large-scale generation")
        print("   • Performance monitoring: Detailed statistics")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\n💡 Make sure to set your GEMINI_API_KEY environment variable")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("   Check the logs for more details")


if __name__ == "__main__":
    main()