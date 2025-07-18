# Design Document

## Overview

The AI Flashcard Generator is a Python script that leverages Google Gemini 2.5 API to generate educational flashcards with English words, Chinese translations, and relevant images. The system will fetch images from the internet and output structured data in CSV format for easy import into flashcard applications.

## Architecture

The system follows a modular architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Main Script   │───▶│  AI Generator   │───▶│ Image Fetcher   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  CSV Exporter   │    │ Gemini API      │    │ Image Search    │
│                 │    │ Client          │    │ Service         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components and Interfaces

### 1. FlashcardGenerator (Main Orchestrator)
- **Purpose**: Coordinates the entire flashcard generation process
- **Methods**:
  - `generate_flashcards(topic: str, count: int) -> List[Flashcard]`
  - `run(config: Config) -> str` (returns CSV file path)

### 2. GeminiClient
- **Purpose**: Handles communication with Google Gemini 2.5 API
- **Methods**:
  - `authenticate(api_key: str) -> bool`
  - `generate_word_pairs(topic: str, count: int) -> List[WordPair]`
  - `translate_to_chinese(english_word: str) -> str`
- **Dependencies**: google-generativeai library

### 3. ImageFetcher
- **Purpose**: Searches and downloads relevant images from the internet
- **Methods**:
  - `search_image(query: str) -> Optional[str]` (returns image URL)
  - `download_image(url: str, filename: str) -> str` (returns local path)
- **Implementation**: Uses Unsplash API or Google Custom Search API for image retrieval

### 4. CSVExporter
- **Purpose**: Formats and exports flashcard data to CSV
- **Methods**:
  - `export_flashcards(flashcards: List[Flashcard], filename: str) -> str`
  - `validate_csv_format(data: List[Dict]) -> bool`

### 5. Configuration Manager
- **Purpose**: Handles configuration and environment variables
- **Methods**:
  - `load_config() -> Config`
  - `validate_api_keys() -> bool`

## Data Models

### Flashcard
```python
@dataclass
class Flashcard:
    english_word: str
    chinese_translation: str
    image_url: Optional[str] = None
    image_local_path: Optional[str] = None
    topic: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
```

### WordPair
```python
@dataclass
class WordPair:
    english: str
    chinese: str
    context: Optional[str] = None
```

### Config
```python
@dataclass
class Config:
    gemini_api_key: str
    image_api_key: Optional[str] = None
    output_directory: str = "./flashcards"
    max_flashcards: int = 50
    image_download_enabled: bool = True
    csv_filename_template: str = "flashcards_{timestamp}.csv"
```

## Error Handling

### API Error Handling
- **Rate Limiting**: Implement exponential backoff with jitter
- **Authentication Errors**: Clear error messages with setup instructions
- **Network Timeouts**: Configurable timeout values with retry logic
- **Invalid Responses**: Validation and fallback mechanisms

### Image Processing Errors
- **Download Failures**: Continue processing without image, log warning
- **Invalid URLs**: Skip invalid images, attempt alternative sources
- **Storage Issues**: Handle disk space and permission errors gracefully

### Data Validation
- **Input Validation**: Sanitize user inputs and topic strings
- **Output Validation**: Ensure CSV format compliance
- **Character Encoding**: Handle Unicode characters properly for Chinese text

## Testing Strategy

### Unit Tests
- **GeminiClient**: Mock API responses, test authentication flow
- **ImageFetcher**: Mock HTTP requests, test download logic
- **CSVExporter**: Test CSV formatting with various character sets
- **Configuration**: Test config loading and validation

### Integration Tests
- **End-to-End**: Generate sample flashcards with test API keys
- **Error Scenarios**: Test behavior with invalid API keys and network issues
- **File Operations**: Test CSV creation and image storage

### Manual Testing
- **API Integration**: Verify actual Gemini API responses
- **Image Quality**: Manually review fetched images for relevance
- **CSV Import**: Test CSV files in popular flashcard applications

## Implementation Notes

### Google Gemini 2.5 Integration
- Use the official `google-generativeai` Python library
- Implement structured prompts for consistent word generation
- Handle rate limits (15 requests per minute for free tier)

### Image Search Strategy
1. **Primary**: Unsplash API (free, high-quality images)
2. **Fallback**: Pixabay API or Pexels API
3. **Local Storage**: Download images to avoid broken links

### CSV Format Specification
```csv
English,Chinese,Image_Path,Topic,Created_Date
apple,苹果,./images/apple.jpg,fruits,2024-01-15
```

### Performance Considerations
- **Batch Processing**: Process multiple words in single API calls when possible
- **Concurrent Downloads**: Use asyncio for parallel image downloads
- **Caching**: Cache translations to avoid duplicate API calls
- **Progress Tracking**: Display progress bar for long-running operations