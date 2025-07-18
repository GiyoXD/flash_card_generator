# AI Flashcard Generator

🚀 **Generate educational flashcards with AI-powered English-Chinese translations and relevant images**

The AI Flashcard Generator is a Python application that uses Google Gemini AI to create bilingual flashcards with English words, Chinese translations, pinyin pronunciation, and relevant images. Perfect for language learners, educators, and anyone looking to create high-quality study materials.

## ✨ Features

### Core Features
- 🧠 **AI-Powered Generation**: Uses Google Gemini 2.5 for accurate translations and word selection
- 🖼️ **Automatic Image Fetching**: Downloads relevant images from Unsplash and other sources
- 📄 **CSV Export**: Compatible with Anki, Quizlet, and other flashcard applications
- 🎯 **Topic-Based Generation**: Generate flashcards for specific topics or themes
- 🔤 **Pinyin Support**: Includes accurate pinyin pronunciation for Chinese characters

### Advanced Features
- ⚡ **Async Image Processing**: Concurrent image downloads for faster generation
- 🗄️ **Smart Caching**: Avoid duplicate API calls with intelligent caching
- 📦 **Batch Processing**: Efficient handling of large flashcard sets
- 🛡️ **Error Recovery**: Graceful handling of API failures with partial results
- 📊 **Performance Monitoring**: Detailed statistics and progress tracking

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key (free tier available)
- Optional: Unsplash API key for high-quality images

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/ai-flashcard-generator.git
   cd ai-flashcard-generator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API keys**
   
   **Option A: Environment Variables**
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key-here"
   export IMAGE_API_KEY="your-unsplash-api-key-here"  # Optional
   ```
   
   **Option B: .env File**
   ```bash
   cp examples/example_config.env .env
   # Edit .env file with your API keys
   ```

4. **Generate your first flashcards**
   ```bash
   python main.py --topic "animals" --count 10
   ```

## 🔑 API Key Setup

### Google Gemini API Key (Required)

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key and set it as `GEMINI_API_KEY`

**Free Tier Limits:**
- 15 requests per minute
- 1,500 requests per day
- Perfect for personal use and learning

### Unsplash API Key (Optional)

1. Visit [Unsplash Developers](https://unsplash.com/developers)
2. Create a developer account
3. Create a new application
4. Copy your Access Key and set it as `IMAGE_API_KEY`

**Without Unsplash API:**
- The system will still work but with limited image sources
- Some images may not be available

## 📖 Usage

### Command Line Interface

```bash
# Basic usage
python main.py --topic "food" --count 15

# Advanced options
python main.py --topic "travel" --count 20 \
  --output ./my_flashcards \
  --filename "travel_cards.csv" \
  --cleanup

# Skip image downloads for faster generation
python main.py --topic "business" --count 10 --no-images
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--topic` | Topic for flashcard generation (required) | - |
| `--count` | Number of flashcards to generate | 10 |
| `--output` | Output directory for files | ./flashcards |
| `--filename` | Custom CSV filename | auto-generated |
| `--cleanup` | Clean up old files before generation | false |
| `--no-images` | Skip image downloading | false |

### Programmatic Usage

```python
from flashcard_generator.config import ConfigManager
from flashcard_generator.flashcard_generator import FlashcardGenerator

# Load configuration
config = ConfigManager.load_config()

# Initialize generator
generator = FlashcardGenerator(config)

# Generate flashcards
csv_file = generator.run(topic="science", count=12)
print(f"Flashcards saved to: {csv_file}")

# Get statistics
stats = generator.get_stats()
print(f"Success rate: {stats['flashcards_created']}/{stats['total_requested']}")
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | - | ✅ |
| `IMAGE_API_KEY` | Unsplash API key | - | ❌ |
| `OUTPUT_DIRECTORY` | Output directory | ./flashcards | ❌ |
| `MAX_FLASHCARDS` | Maximum cards per generation | 50 | ❌ |
| `IMAGE_DOWNLOAD_ENABLED` | Enable image downloads | true | ❌ |

### Advanced Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_CACHING` | Enable word pair caching | true |
| `CACHE_MAX_AGE_HOURS` | Cache expiration time | 24 |
| `ENABLE_ASYNC_IMAGES` | Enable concurrent image downloads | true |
| `MAX_CONCURRENT_IMAGES` | Max concurrent downloads | 5 |
| `ENABLE_BATCH_PROCESSING` | Enable batch optimizations | true |
| `BATCH_SIZE` | Batch processing size | 10 |

### Configuration File Example

```bash
# .env file
GEMINI_API_KEY=your_gemini_api_key_here
IMAGE_API_KEY=your_unsplash_api_key_here
OUTPUT_DIRECTORY=./my_flashcards
MAX_FLASHCARDS=30
IMAGE_DOWNLOAD_ENABLED=true

# Advanced optimizations
ENABLE_CACHING=true
CACHE_MAX_AGE_HOURS=48
ENABLE_ASYNC_IMAGES=true
MAX_CONCURRENT_IMAGES=8
```

## 📁 Output Format

### CSV Structure

The generated CSV files are compatible with popular flashcard applications:

```csv
English,Chinese,Pinyin,Image_Path,Topic,Created_Date
cat,猫,mao1,./images/cat_a1b2c3d4.jpg,animals,2024-01-15 14:30:22
dog,狗,gou3,./images/dog_e5f6g7h8.jpg,animals,2024-01-15 14:30:25
```

### File Organization

```
flashcards/
├── flashcards_20240115_143022.csv    # Generated flashcards
├── images/                           # Downloaded images
│   ├── cat_a1b2c3d4.jpg
│   └── dog_e5f6g7h8.jpg
├── logs/                            # Application logs
│   ├── flashcard_generator_20240115.log
│   └── flashcard_generator_errors_20240115.log
└── cache/                           # Performance cache
    ├── word_pairs_cache.json
    └── image_cache.json
```

## 🎯 Flashcard App Integration

### Anki Import

1. Open Anki
2. File → Import
3. Select your CSV file
4. Map fields: English → Front, Chinese → Back, Pinyin → Extra
5. Import and start studying!

### Quizlet Import

1. Create a new study set
2. Choose "Import from Word, Excel, Google Docs, etc."
3. Upload your CSV file
4. Map columns appropriately
5. Save and study!

### Other Applications

The CSV format is compatible with:
- **Memrise**: Direct CSV import
- **StudyBlue**: Copy-paste from CSV
- **Brainscape**: CSV import feature
- **Excel/Google Sheets**: For custom study tools

## 🔧 Advanced Usage

### Batch Processing

```python
from flashcard_generator.flashcard_generator import FlashcardGenerator
from flashcard_generator.models import Config

# Create optimized configuration
config = Config(
    gemini_api_key="your_key",
    enable_caching=True,
    enable_async_images=True,
    max_concurrent_images=8,
    batch_size=20
)

generator = FlashcardGenerator(config)

# Process multiple topics
topics = ["science", "history", "geography", "literature"]
for topic in topics:
    csv_file = generator.run(topic, 15)
    print(f"Generated {topic} flashcards: {csv_file}")
```

### Performance Optimization

```python
# Enable all optimizations for maximum performance
config = Config(
    gemini_api_key="your_key",
    enable_caching=True,           # Cache API responses
    cache_max_age_hours=48,        # Cache for 2 days
    enable_async_images=True,      # Concurrent image downloads
    max_concurrent_images=10,      # Higher concurrency
    enable_batch_processing=True,  # Batch optimizations
    batch_size=25                  # Larger batches
)
```

### Error Handling and Recovery

```python
from flashcard_generator.exceptions import PartialResultsError

try:
    flashcards = generator.generate_flashcards("topic", 20)
except PartialResultsError as e:
    print(f"Partial success: {e.details['successful_count']} cards created")
    # Partial results are automatically saved
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest tests/test_integration.py -v
python -m pytest tests/test_performance.py -v
python -m pytest tests/test_advanced_features.py -v

# Run with coverage
python -m pytest --cov=flashcard_generator
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Batch processing and optimization testing
- **Compatibility Tests**: CSV format compatibility with flashcard apps

## 🐛 Troubleshooting

### Common Issues

#### "GEMINI_API_KEY environment variable is required"
**Solution**: Set your Gemini API key
```bash
export GEMINI_API_KEY="your-api-key-here"
# Or create a .env file with the key
```

#### "Failed to authenticate with Gemini API"
**Possible causes:**
- Invalid API key
- Network connectivity issues
- API service temporarily unavailable

**Solutions:**
1. Verify your API key at [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Check your internet connection
3. Try again in a few minutes

#### "Rate limit exceeded"
**Solution**: The free tier has limits. Either:
- Wait a few minutes and try again
- Reduce the number of flashcards per request
- Upgrade to a paid plan for higher limits

#### "No images found for words"
**Possible causes:**
- No Unsplash API key provided
- Network issues
- Unusual or abstract words

**Solutions:**
1. Set up an Unsplash API key for better image results
2. Try more common topics
3. Use `--no-images` flag to skip image downloads

#### "Permission denied" errors
**Solution**: Check file permissions
```bash
chmod 755 ./flashcards  # Make output directory writable
```

### Performance Issues

#### Slow generation
**Solutions:**
1. Enable caching: `ENABLE_CACHING=true`
2. Enable async images: `ENABLE_ASYNC_IMAGES=true`
3. Increase concurrency: `MAX_CONCURRENT_IMAGES=8`
4. Use smaller batch sizes for testing

#### High memory usage
**Solutions:**
1. Reduce batch size: `BATCH_SIZE=5`
2. Disable caching if not needed: `ENABLE_CACHING=false`
3. Process topics separately instead of large batches

### Getting Help

1. **Check the logs**: Look in `./flashcards/logs/` for detailed error information
2. **Enable debug logging**: Set `LOG_LEVEL=DEBUG` in your environment
3. **Run tests**: `python -m pytest tests/` to verify your setup
4. **Check API status**: Verify Gemini API service status
5. **Update dependencies**: `pip install -r requirements.txt --upgrade`

## 📊 Performance Benchmarks

### Typical Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Single flashcard | 2-5 seconds | Including image download |
| 10 flashcards | 15-30 seconds | With async processing |
| 50 flashcards | 2-4 minutes | Maximum batch size |
| Cached generation | 1-3 seconds | Subsequent runs |

### Optimization Impact

| Feature | Performance Improvement |
|---------|------------------------|
| Caching | 5-10x faster for repeated topics |
| Async images | 3-5x faster image downloads |
| Batch processing | Linear scaling up to 50 cards |

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone and setup
git clone https://github.com/your-username/ai-flashcard-generator.git
cd ai-flashcard-generator

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
python -m pytest

# Run linting
flake8 flashcard_generator/
black flashcard_generator/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Gemini AI** for powerful language generation
- **Unsplash** for high-quality images
- **The open-source community** for inspiration and tools

## 📞 Support

- **Documentation**: This README and inline code comments
- **Issues**: [GitHub Issues](https://github.com/your-username/ai-flashcard-generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/ai-flashcard-generator/discussions)

---

**Happy Learning! 🎓**

*Generate smarter, study better, learn faster with AI-powered flashcards.*# flash_card_generator
