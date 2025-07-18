#!/usr/bin/env python3
"""
Basic usage example for the AI Flashcard Generator.

This example demonstrates the simplest way to generate flashcards
using the FlashcardGenerator class directly.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flashcard_generator.config import ConfigManager
from flashcard_generator.flashcard_generator import FlashcardGenerator


def main():
    """Basic usage example."""
    print("🚀 AI Flashcard Generator - Basic Usage Example")
    print("=" * 50)
    
    try:
        # Load configuration from environment variables
        # Make sure you have set GEMINI_API_KEY in your environment
        config = ConfigManager.load_config()
        print(f"✅ Configuration loaded successfully")
        print(f"   Output directory: {config.output_directory}")
        print(f"   Max flashcards: {config.max_flashcards}")
        print(f"   Images enabled: {config.image_download_enabled}")
        print()
        
        # Initialize the flashcard generator
        generator = FlashcardGenerator(config)
        print("✅ FlashcardGenerator initialized")
        print()
        
        # Generate flashcards for a simple topic
        topic = "animals"
        count = 5
        
        print(f"🎯 Generating {count} flashcards for topic: '{topic}'")
        print("This may take a few moments...")
        print()
        
        # Run the complete generation process
        csv_file_path = generator.run(topic=topic, count=count)
        
        print()
        print("🎉 Success! Flashcards generated successfully!")
        print(f"📄 CSV file saved to: {csv_file_path}")
        print()
        
        # Display generation statistics
        stats = generator.get_stats()
        print("📊 Generation Statistics:")
        print(f"   Requested: {stats['total_requested']}")
        print(f"   Generated: {stats['flashcards_created']}")
        print(f"   Images downloaded: {stats['images_downloaded']}")
        print(f"   Errors: {stats['errors']}")
        
        if stats['start_time'] and stats['end_time']:
            duration = stats['end_time'] - stats['start_time']
            print(f"   Duration: {duration.total_seconds():.1f} seconds")
        
        print()
        print("💡 Next steps:")
        print(f"   1. Open the CSV file: {csv_file_path}")
        print("   2. Import it into your favorite flashcard app (Anki, Quizlet, etc.)")
        print("   3. Start learning!")
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print()
        print("💡 Make sure you have set the GEMINI_API_KEY environment variable:")
        print("   export GEMINI_API_KEY='your-api-key-here'")
        print()
        print("   Or create a .env file with your API key:")
        print("   echo 'GEMINI_API_KEY=your-api-key-here' > .env")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please check the logs for more details.")


if __name__ == "__main__":
    main()