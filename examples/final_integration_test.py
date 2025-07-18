#!/usr/bin/env python3
"""
Final integration test for the AI Flashcard Generator.

This script performs comprehensive testing of the complete system
to verify all components work together correctly.
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


def test_basic_functionality():
    """Test basic flashcard generation without images."""
    print("🧪 Testing basic functionality (no images)...")
    
    try:
        # Create test configuration
        config = Config(
            gemini_api_key=os.getenv('GEMINI_API_KEY', 'test_key'),
            output_directory="./test_output",
            max_flashcards=5,
            image_download_enabled=False
        )
        
        generator = FlashcardGenerator(config)
        
        # Test with a simple topic
        csv_file = generator.run(topic="colors", count=3)
        
        if csv_file and Path(csv_file).exists():
            print(f"✅ Basic test passed: {Path(csv_file).name}")
            return True
        else:
            print("❌ Basic test failed: No CSV file created")
            return False
            
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False


def test_configuration_loading():
    """Test configuration loading from environment."""
    print("🧪 Testing configuration loading...")
    
    try:
        # Test with environment variables
        os.environ['GEMINI_API_KEY'] = 'test_key_123'
        os.environ['MAX_FLASHCARDS'] = '25'
        os.environ['OUTPUT_DIRECTORY'] = './config_test'
        
        config = ConfigManager.load_config()
        
        if (config.gemini_api_key == 'test_key_123' and 
            config.max_flashcards == 25 and 
            config.output_directory == './config_test'):
            print("✅ Configuration test passed")
            return True
        else:
            print("❌ Configuration test failed: Values not loaded correctly")
            return False
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_error_handling():
    """Test error handling with invalid configuration."""
    print("🧪 Testing error handling...")
    
    try:
        # Test with invalid API key
        config = Config(
            gemini_api_key="invalid_key",
            output_directory="./error_test",
            max_flashcards=3,
            image_download_enabled=False
        )
        
        generator = FlashcardGenerator(config)
        
        # This should fail gracefully
        try:
            csv_file = generator.run(topic="test", count=1)
            print("❌ Error handling test failed: Should have thrown an error")
            return False
        except Exception as expected_error:
            print(f"✅ Error handling test passed: {type(expected_error).__name__}")
            return True
            
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def test_file_organization():
    """Test that files are organized correctly."""
    print("🧪 Testing file organization...")
    
    try:
        test_dir = Path("./organization_test")
        
        config = Config(
            gemini_api_key=os.getenv('GEMINI_API_KEY', 'test_key'),
            output_directory=str(test_dir),
            max_flashcards=3,
            image_download_enabled=False
        )
        
        generator = FlashcardGenerator(config)
        
        # Check if directories are created
        expected_dirs = [
            test_dir,
            test_dir / "cache",
            test_dir / "logs"
        ]
        
        # Initialize generator to create directories
        generator.initialize_directories()
        
        all_dirs_exist = all(d.exists() for d in expected_dirs)
        
        if all_dirs_exist:
            print("✅ File organization test passed")
            return True
        else:
            missing = [str(d) for d in expected_dirs if not d.exists()]
            print(f"❌ File organization test failed: Missing directories: {missing}")
            return False
            
    except Exception as e:
        print(f"❌ File organization test failed: {e}")
        return False


def test_csv_format():
    """Test CSV format and encoding."""
    print("🧪 Testing CSV format...")
    
    try:
        from flashcard_generator.csv_exporter import CSVExporter
        from flashcard_generator.models import Flashcard
        
        # Create test flashcards with Chinese characters
        test_flashcards = [
            Flashcard(
                english="test",
                chinese="测试",
                pinyin="ce4 shi4",
                topic="testing",
                created_at=datetime.now()
            )
        ]
        
        exporter = CSVExporter("./csv_test")
        csv_file = exporter.export_flashcards(test_flashcards, "test_format.csv")
        
        if Path(csv_file).exists():
            # Read and verify content
            with open(csv_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "测试" in content and "ce4 shi4" in content:
                    print("✅ CSV format test passed")
                    return True
                else:
                    print("❌ CSV format test failed: Chinese characters not found")
                    return False
        else:
            print("❌ CSV format test failed: CSV file not created")
            return False
            
    except Exception as e:
        print(f"❌ CSV format test failed: {e}")
        return False


def test_caching_mechanism():
    """Test caching functionality."""
    print("🧪 Testing caching mechanism...")
    
    try:
        from flashcard_generator.cache import WordPairCache
        from flashcard_generator.models import WordPair
        
        cache = WordPairCache("./cache_test", max_age_hours=1)
        
        # Test cache miss
        result = cache.get_cached_word_pairs("test_topic", 3)
        if result is not None:
            print("❌ Caching test failed: Should be cache miss")
            return False
        
        # Test cache store
        test_pairs = [
            WordPair(english="test", chinese="测试", pinyin="ce4 shi4")
        ]
        cache.cache_word_pairs("test_topic", 3, test_pairs)
        
        # Test cache hit
        cached_result = cache.get_cached_word_pairs("test_topic", 3)
        if cached_result and len(cached_result) == 1:
            print("✅ Caching test passed")
            return True
        else:
            print("❌ Caching test failed: Cache hit failed")
            return False
            
    except Exception as e:
        print(f"❌ Caching test failed: {e}")
        return False


def run_comprehensive_test():
    """Run all integration tests."""
    print("🚀 AI Flashcard Generator - Final Integration Test")
    print("=" * 60)
    
    tests = [
        ("Configuration Loading", test_configuration_loading),
        ("File Organization", test_file_organization),
        ("CSV Format", test_csv_format),
        ("Caching Mechanism", test_caching_mechanism),
        ("Error Handling", test_error_handling),
        # Note: Basic functionality test requires valid API key
        # ("Basic Functionality", test_basic_functionality),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n📊 TEST RESULTS SUMMARY")
    print("=" * 40)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All integration tests passed!")
        print("The AI Flashcard Generator is ready for production use.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        print("Please review the failed tests before deployment.")
    
    return passed == total


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)