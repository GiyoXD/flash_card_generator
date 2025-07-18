#!/usr/bin/env python3
"""
Advanced usage example for the AI Flashcard Generator.

This example demonstrates advanced features like:
- Custom configuration
- Error handling and recovery
- Batch processing
- Statistics analysis
- File management
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flashcard_generator.config import ConfigManager
from flashcard_generator.flashcard_generator import FlashcardGenerator
from flashcard_generator.models import Config
from flashcard_generator.exceptions import PartialResultsError, ValidationError


def create_custom_config():
    """Create a custom configuration for advanced usage."""
    return Config(
        gemini_api_key=os.getenv('GEMINI_API_KEY', 'your_api_key_here'),
        image_api_key=os.getenv('IMAGE_API_KEY'),
        output_directory="./advanced_flashcards",
        max_flashcards=30,
        image_download_enabled=True,
        csv_filename_template="flashcards_{timestamp}.csv"
    )


def generate_with_error_handling(generator, topic, count):
    """Generate flashcards with comprehensive error handling."""
    print(f"🎯 Generating {count} flashcards for '{topic}'...")
    
    try:
        start_time = time.time()
        csv_file_path = generator.run(topic, count)
        end_time = time.time()
        
        # Success case
        stats = generator.get_stats()
        duration = end_time - start_time
        
        print(f"✅ Success! Generated in {duration:.1f} seconds")
        print(f"   📄 File: {csv_file_path}")
        print(f"   📊 Created: {stats['flashcards_created']}/{stats['total_requested']}")
        print(f"   🖼️  Images: {stats['images_downloaded']}")
        print(f"   ⚠️  Errors: {stats['errors']}")
        
        return csv_file_path, stats
        
    except PartialResultsError as e:
        # Partial success - some flashcards were created
        print(f"⚠️  Partial success: {e.details['successful_count']}/{e.details['total_requested']} flashcards created")
        print(f"   Reason: {e.message}")
        
        if hasattr(e, 'partial_results') and e.partial_results:
            print(f"   💾 Partial results available: {len(e.partial_results)} flashcards")
        
        return None, e.details
        
    except ValidationError as e:
        print(f"❌ Validation error: {e.message}")
        if e.details:
            print(f"   Details: {e.details}")
        return None, None
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return None, None


def analyze_generation_statistics(all_stats):
    """Analyze statistics from multiple generation runs."""
    print("\n📈 GENERATION ANALYSIS")
    print("=" * 40)
    
    if not all_stats:
        print("No statistics to analyze.")
        return
    
    total_requested = sum(stats.get('total_requested', 0) for stats in all_stats if stats)
    total_created = sum(stats.get('flashcards_created', 0) for stats in all_stats if stats)
    total_images = sum(stats.get('images_downloaded', 0) for stats in all_stats if stats)
    total_errors = sum(stats.get('errors', 0) for stats in all_stats if stats)
    
    success_rate = (total_created / total_requested * 100) if total_requested > 0 else 0
    image_rate = (total_images / total_created * 100) if total_created > 0 else 0
    
    print(f"Total flashcards requested: {total_requested}")
    print(f"Total flashcards created: {total_created}")
    print(f"Overall success rate: {success_rate:.1f}%")
    print(f"Images downloaded: {total_images}")
    print(f"Image success rate: {image_rate:.1f}%")
    print(f"Total errors: {total_errors}")
    
    # Error analysis
    if total_errors > 0:
        print(f"\n⚠️  Error Analysis:")
        api_errors = sum(stats.get('api_errors', 0) for stats in all_stats if stats)
        image_errors = sum(stats.get('image_errors', 0) for stats in all_stats if stats)
        validation_errors = sum(stats.get('validation_errors', 0) for stats in all_stats if stats)
        
        print(f"   API errors: {api_errors}")
        print(f"   Image errors: {image_errors}")
        print(f"   Validation errors: {validation_errors}")


def batch_process_topics(generator, topics_config):
    """Process multiple topics in batch with progress tracking."""
    print(f"\n🔄 BATCH PROCESSING")
    print("=" * 40)
    print(f"Processing {len(topics_config)} topics...")
    
    results = []
    all_stats = []
    
    for i, (topic, count) in enumerate(topics_config, 1):
        print(f"\n[{i}/{len(topics_config)}] Processing '{topic}'...")
        
        csv_file, stats = generate_with_error_handling(generator, topic, count)
        
        results.append({
            'topic': topic,
            'count': count,
            'csv_file': csv_file,
            'success': csv_file is not None
        })
        
        if stats:
            all_stats.append(stats)
        
        # Small delay between batches to be respectful to APIs
        if i < len(topics_config):
            time.sleep(2)
    
    return results, all_stats


def demonstrate_file_management(generator):
    """Demonstrate file management features."""
    print(f"\n🗂️  FILE MANAGEMENT")
    print("=" * 40)
    
    # Show current files
    output_dir = Path(generator.config.output_directory)
    if output_dir.exists():
        csv_files = list(output_dir.glob("*.csv"))
        image_files = list((output_dir / "images").glob("*")) if (output_dir / "images").exists() else []
        log_files = list((output_dir / "logs").glob("*.log")) if (output_dir / "logs").exists() else []
        
        print(f"Current files:")
        print(f"   CSV files: {len(csv_files)}")
        print(f"   Image files: {len(image_files)}")
        print(f"   Log files: {len(log_files)}")
        
        # Demonstrate cleanup
        print(f"\n🧹 Running cleanup (files older than 0 days for demo)...")
        cleanup_stats = generator.cleanup_old_files(max_age_days=0)
        
        print(f"Cleanup results:")
        for file_type, count in cleanup_stats.items():
            print(f"   {file_type}: {count} files cleaned")
    else:
        print("Output directory doesn't exist yet.")


def main():
    """Advanced usage demonstration."""
    print("🚀 AI Flashcard Generator - Advanced Usage Example")
    print("=" * 60)
    
    try:
        # Create custom configuration
        config = create_custom_config()
        print(f"✅ Custom configuration created")
        print(f"   Output directory: {config.output_directory}")
        print(f"   Max flashcards: {config.max_flashcards}")
        print(f"   Filename template: {config.csv_filename_template}")
        
        # Validate configuration
        if not ConfigManager.validate_config(config):
            raise ValueError("Invalid configuration")
        
        # Initialize generator
        generator = FlashcardGenerator(config)
        print(f"✅ FlashcardGenerator initialized with custom config")
        
        # Define topics for batch processing
        topics_config = [
            ("travel", 8),
            ("business", 6),
            ("technology", 7),
            ("cooking", 5),
        ]
        
        # Batch process topics
        results, all_stats = batch_process_topics(generator, topics_config)
        
        # Analyze results
        analyze_generation_statistics(all_stats)
        
        # Show successful generations
        successful_results = [r for r in results if r['success']]
        print(f"\n🎉 SUCCESSFUL GENERATIONS")
        print("=" * 40)
        print(f"Successfully generated {len(successful_results)}/{len(results)} topics:")
        
        for result in successful_results:
            print(f"   ✅ {result['topic']}: {result['count']} cards → {Path(result['csv_file']).name}")
        
        # Show failed generations
        failed_results = [r for r in results if not r['success']]
        if failed_results:
            print(f"\n❌ FAILED GENERATIONS")
            print("=" * 40)
            for result in failed_results:
                print(f"   ❌ {result['topic']}: {result['count']} cards (failed)")
        
        # Demonstrate file management
        demonstrate_file_management(generator)
        
        print(f"\n💡 TIPS FOR PRODUCTION USE:")
        print("   1. Monitor API rate limits and add delays between requests")
        print("   2. Implement retry logic for transient failures")
        print("   3. Regularly clean up old files to save disk space")
        print("   4. Use custom configurations for different use cases")
        print("   5. Analyze statistics to optimize generation parameters")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\n💡 Make sure to set your GEMINI_API_KEY environment variable")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("   Check the logs for more details")


if __name__ == "__main__":
    main()