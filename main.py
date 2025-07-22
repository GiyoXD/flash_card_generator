#!/usr/bin/env python3
"""
Main entry point for the AI Flashcard Generator.

This script generates educational flashcards using Google Gemini 2.5 API
with English words, Chinese translations, and relevant images.
"""

import argparse
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from flashcard_generator.config import ConfigManager
from flashcard_generator.flashcard_generator import FlashcardGenerator


def main():
    """Main entry point for the flashcard generator."""
    parser = argparse.ArgumentParser(
        description="Generate AI-powered flashcards with English-Chinese translations and images"
    )
    parser.add_argument(
        "--topic",
        type=str,
        required=True,
        help="Topic or theme for flashcard generation (e.g., 'animals', 'food', 'travel')"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of flashcards to generate (default: 10)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory for generated files"
    )
    parser.add_argument(
        "--filename",
        type=str,
        help="Custom filename for the CSV output"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up old files before generation"
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Skip image downloading"
    )
    parser.add_argument(
        "-c", "--context",
        type=str,
        help="Additional context for AI generation (e.g., 'beginner level', 'business terms', 'daily conversation')"
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = ConfigManager.load_config()
        
        # Override configuration with command line arguments
        if args.output:
            config.output_directory = args.output
        
        if args.no_images:
            config.image_download_enabled = False
        
        # Validate configuration
        if not ConfigManager.validate_api_keys(config):
            print("❌ Error: Invalid API key configuration.")
            print("Please ensure GEMINI_API_KEY is set in your environment variables.")
            print("You can also create a .env file with your API keys.")
            sys.exit(1)
        
        # Validate count
        if args.count <= 0:
            print("❌ Error: Count must be greater than 0")
            sys.exit(1)
        
        if args.count > config.max_flashcards:
            print(f"❌ Error: Count cannot exceed {config.max_flashcards}")
            sys.exit(1)
        
        # Print startup information
        print("🚀 AI Flashcard Generator")
        print("=" * 40)
        print(f"Topic: {args.topic}")
        print(f"Count: {args.count}")
        print(f"Output directory: {config.output_directory}")
        print(f"Images enabled: {'Yes' if config.image_download_enabled else 'No'}")
        if args.filename:
            print(f"Custom filename: {args.filename}")
        print()
        
        # Initialize the flashcard generator
        generator = FlashcardGenerator(config)
        
        # Clean up old files if requested
        if args.cleanup:
            print("🧹 Cleaning up old files...")
            cleanup_stats = generator.cleanup_old_files()
            total_cleaned = sum(cleanup_stats.values())
            if total_cleaned > 0:
                print(f"✅ Cleaned up {total_cleaned} old files")
            else:
                print("✅ No old files to clean up")
            print()
        
        # Generate flashcards
        csv_file_path = generator.run(
            topic=args.topic,
            count=args.count,
            output_filename=args.filename,
            context=args.context
        )
        
        print(f"\n🎉 Success! Flashcards generated and saved to:")
        print(f"   {csv_file_path}")
        print("\nYou can now import this CSV file into your favorite flashcard app!")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"❌ Generation error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("Please check the logs for more details.")
        sys.exit(1)


if __name__ == "__main__":
    main()