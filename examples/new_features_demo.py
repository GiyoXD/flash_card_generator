#!/usr/bin/env python3
"""
Demonstration of new features: Context parameter and Sentence field.

This script shows how to use the context parameter to influence AI generation
and how the sentence field provides example usage for each word.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd):
    """Run a command and display the output."""
    print(f"🔧 Running: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def main():
    """Demonstrate the new features with command-line examples."""
    print("🚀 New Features Demonstration")
    print("=" * 60)
    print("Features:")
    print("1. Context Parameter (-c/--context) - Influence AI word selection")
    print("2. Sentence Field - Example sentences for each word")
    print()
    
    # Get the main.py path
    main_script = Path(__file__).parent.parent / "main.py"
    
    # Example 1: Basic usage with context for beginners
    print("📝 Example 1: Beginner-level animals with context")
    cmd1 = [
        sys.executable, str(main_script),
        "--topic", "animals",
        "--count", "5",
        "--context", "beginner level, simple words for children learning English",
        "--filename", "demo_beginner_animals"
    ]
    
    if not run_command(cmd1):
        print("❌ Example 1 failed")
        return False
    
    print("\n" + "="*60 + "\n")
    
    # Example 2: Business context
    print("📝 Example 2: Business technology terms")
    cmd2 = [
        sys.executable, str(main_script),
        "--topic", "technology",
        "--count", "5",
        "--context", "business and professional terms, corporate environment",
        "--filename", "demo_business_tech"
    ]
    
    if not run_command(cmd2):
        print("❌ Example 2 failed")
        return False
    
    print("\n" + "="*60 + "\n")
    
    # Example 3: Academic context
    print("📝 Example 3: Academic science vocabulary")
    cmd3 = [
        sys.executable, str(main_script),
        "--topic", "science",
        "--count", "5",
        "--context", "academic level, university science terminology",
        "--filename", "demo_academic_science"
    ]
    
    if not run_command(cmd3):
        print("❌ Example 3 failed")
        return False
    
    print("\n" + "="*60 + "\n")
    
    # Example 4: Daily conversation context
    print("📝 Example 4: Daily conversation food terms")
    cmd4 = [
        sys.executable, str(main_script),
        "--topic", "food",
        "--count", "5",
        "--context", "daily conversation, common food items used in everyday speech",
        "--filename", "demo_daily_food"
    ]
    
    if not run_command(cmd4):
        print("❌ Example 4 failed")
        return False
    
    print("\n🎉 All demonstrations completed successfully!")
    print("\n📋 Summary of generated files:")
    print("- demo_beginner_animals.csv (beginner-level animal words)")
    print("- demo_business_tech.csv (business technology terms)")
    print("- demo_academic_science.csv (academic science vocabulary)")
    print("- demo_daily_food.csv (daily conversation food terms)")
    print("\n💡 Each CSV file includes:")
    print("- English word")
    print("- Chinese translation")
    print("- Pinyin pronunciation")
    print("- Example sentence (NEW!)")
    print("- Image path")
    print("- Topic and creation date")
    
    print("\n🔧 Command-line usage examples:")
    print("python main.py --topic animals --count 10 --context 'beginner level'")
    print("python main.py --topic business --count 15 -c 'professional terms'")
    print("python main.py --topic travel --count 20 --context 'daily conversation'")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)