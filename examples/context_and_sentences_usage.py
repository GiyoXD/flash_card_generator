#!/usr/bin/env python3
"""
Example demonstrating how to use the context parameter and sentence generation features.

This example shows:
1. How to use the -c/--context parameter in CLI
2. How sentences are automatically generated and included
3. Different context examples for various use cases
"""

import subprocess
import sys
from pathlib import Path

def run_example_commands():
    """Run example commands demonstrating context and sentence features."""
    
    print("🚀 Context Parameter and Sentence Generation Examples")
    print("=" * 60)
    
    examples = [
        {
            "description": "Basic usage with beginner context",
            "command": [
                "python", "main.py",
                "--topic", "food",
                "--count", "5",
                "--context", "beginner level, common everyday foods"
            ]
        },
        {
            "description": "Business vocabulary with professional context",
            "command": [
                "python", "main.py", 
                "--topic", "business",
                "--count", "5",
                "--context", "professional business terms, office environment"
            ]
        },
        {
            "description": "Travel vocabulary with practical context",
            "command": [
                "python", "main.py",
                "--topic", "travel", 
                "--count", "5",
                "--context", "practical travel phrases, airport and hotel vocabulary"
            ]
        },
        {
            "description": "Academic vocabulary with formal context",
            "command": [
                "python", "main.py",
                "--topic", "education",
                "--count", "5", 
                "--context", "academic terms, university level vocabulary"
            ]
        }
    ]
    
    print("Here are example commands you can run:\n")
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['description']}")
        print(f"   Command: {' '.join(example['command'])}")
        print()
    
    print("Key Features Demonstrated:")
    print("✅ Context parameter (-c or --context) guides AI word selection")
    print("✅ Sentences are automatically generated for each word")
    print("✅ Context influences both word choice and sentence complexity")
    print("✅ All data is exported to CSV including the sentence field")
    
    print("\nCSV Output Format:")
    print("The generated CSV will include these columns:")
    print("- English: The English word")
    print("- Chinese: Chinese translation")
    print("- Pinyin: Pronunciation guide")
    print("- Image_Path: Image reference for flashcard apps")
    print("- Topic: The topic used for generation")
    print("- Created_Date: When the flashcard was created")
    print("- Sentence: Example sentence using the English word")
    
    print("\nContext Examples by Use Case:")
    print("🎓 Learning: 'beginner level', 'intermediate vocabulary', 'advanced terms'")
    print("💼 Business: 'professional terms', 'meeting vocabulary', 'email language'")
    print("✈️  Travel: 'tourist phrases', 'restaurant vocabulary', 'transportation terms'")
    print("🏥 Medical: 'basic health terms', 'hospital vocabulary', 'symptoms and conditions'")
    print("🏠 Daily Life: 'household items', 'family conversations', 'shopping vocabulary'")
    
    print("\nTip: The more specific your context, the better the AI can tailor")
    print("     the vocabulary and sentences to your learning needs!")


if __name__ == "__main__":
    run_example_commands()