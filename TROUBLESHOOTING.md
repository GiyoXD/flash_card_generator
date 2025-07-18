# Troubleshooting Guide

This guide helps you resolve common issues with the AI Flashcard Generator.

## 🚨 Common Error Messages

### API Key Issues

#### ❌ "GEMINI_API_KEY environment variable is required"

**Cause**: The required Google Gemini API key is not set.

**Solutions**:
1. **Set environment variable**:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

2. **Create .env file**:
   ```bash
   echo "GEMINI_API_KEY=your-api-key-here" > .env
   ```

3. **Get API key**:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Sign in and create a new API key
   - Copy the key and use it in your configuration

#### ❌ "Failed to authenticate with Gemini API"

**Possible Causes**:
- Invalid or expired API key
- Network connectivity issues
- API service temporarily down

**Diagnostic Steps**:
1. **Verify API key**:
   ```bash
   curl -H "Authorization: Bearer $GEMINI_API_KEY" \
        "https://generativelanguage.googleapis.com/v1/models"
   ```

2. **Check network connectivity**:
   ```bash
   ping google.com
   ```

3. **Test with a simple request**:
   ```python
   import google.generativeai as genai
   genai.configure(api_key="your-key")
   model = genai.GenerativeModel('gemini-1.5-flash')
   response = model.generate_content("Hello")
   print(response.text)
   ```

**Solutions**:
- Regenerate API key at Google AI Studio
- Check firewall/proxy settings
- Wait and retry (temporary service issues)

### Rate Limiting Issues

#### ❌ "Rate limit exceeded" / "Too many requests"

**Cause**: Exceeded Google Gemini API rate limits.

**Free Tier Limits**:
- 15 requests per minute
- 1,500 requests per day

**Solutions**:
1. **Reduce request frequency**:
   ```bash
   # Generate fewer flashcards at once
   python main.py --topic "animals" --count 5
   ```

2. **Enable caching** to reduce API calls:
   ```bash
   export ENABLE_CACHING=true
   ```

3. **Wait and retry**:
   ```bash
   # Wait 1 minute, then retry
   sleep 60
   python main.py --topic "animals" --count 10
   ```

4. **Upgrade to paid tier** for higher limits

### Image Download Issues

#### ❌ "No image found for query"

**Possible Causes**:
- No Unsplash API key configured
- Unusual or abstract search terms
- Network connectivity issues

**Solutions**:
1. **Set up Unsplash API key**:
   ```bash
   export IMAGE_API_KEY="your-unsplash-key"
   ```

2. **Skip images for faster generation**:
   ```bash
   python main.py --topic "animals" --count 10 --no-images
   ```

3. **Try more common topics**:
   ```bash
   # Instead of abstract topics
   python main.py --topic "emotions" --count 5
   # Try concrete topics
   python main.py --topic "animals" --count 5
   ```

#### ❌ "Image download failed"

**Solutions**:
1. **Check network connectivity**
2. **Verify Unsplash API key**
3. **Reduce concurrent downloads**:
   ```bash
   export MAX_CONCURRENT_IMAGES=2
   ```

### File Permission Issues

#### ❌ "Permission denied"

**Cause**: Insufficient permissions to write to output directory.

**Solutions**:
1. **Fix directory permissions**:
   ```bash
   chmod 755 ./flashcards
   mkdir -p ./flashcards
   ```

2. **Use different output directory**:
   ```bash
   python main.py --topic "animals" --output ~/my_flashcards
   ```

3. **Run with appropriate permissions**:
   ```bash
   sudo python main.py --topic "animals"  # Not recommended
   ```

### Memory and Performance Issues

#### ❌ "Memory error" / Slow performance

**Causes**:
- Large batch sizes
- Memory leaks
- Insufficient system resources

**Solutions**:
1. **Reduce batch size**:
   ```bash
   export BATCH_SIZE=5
   export MAX_FLASHCARDS=20
   ```

2. **Disable caching if memory is limited**:
   ```bash
   export ENABLE_CACHING=false
   ```

3. **Process topics separately**:
   ```bash
   # Instead of one large batch
   python main.py --topic "animals" --count 50
   # Use multiple smaller batches
   python main.py --topic "animals" --count 10
   python main.py --topic "food" --count 10
   ```

4. **Clean up old files**:
   ```bash
   python main.py --topic "test" --cleanup
   ```

## 🔍 Diagnostic Commands

### Check System Status

```bash
# Check Python version (requires 3.8+)
python --version

# Check installed packages
pip list | grep -E "(google-generativeai|requests|pandas)"

# Check environment variables
echo "GEMINI_API_KEY: ${GEMINI_API_KEY:0:10}..."
echo "IMAGE_API_KEY: ${IMAGE_API_KEY:0:10}..."

# Test basic functionality
python -c "from flashcard_generator.config import ConfigManager; print('✅ Import successful')"
```

### Test API Connectivity

```bash
# Test Gemini API
python -c "
import google.generativeai as genai
import os
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content('Hello')
print('✅ Gemini API working:', response.text[:50])
"

# Test image API (if configured)
python -c "
import requests
import os
api_key = os.getenv('IMAGE_API_KEY')
if api_key:
    response = requests.get('https://api.unsplash.com/photos/random', 
                          headers={'Authorization': f'Client-ID {api_key}'})
    print('✅ Unsplash API status:', response.status_code)
else:
    print('ℹ️  No IMAGE_API_KEY configured')
"
```

### Run Diagnostic Tests

```bash
# Run basic functionality tests
python -m pytest tests/test_integration.py::TestEndToEndIntegration::test_complete_flashcard_generation_workflow -v

# Test configuration loading
python -m pytest tests/test_config.py -v

# Test error handling
python -m pytest tests/test_error_scenarios.py -v
```

## 🐛 Debug Mode

### Enable Debug Logging

```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Run with verbose output
python main.py --topic "animals" --count 3 2>&1 | tee debug.log
```

### Check Log Files

```bash
# View recent logs
tail -f ./flashcards/logs/flashcard_generator_$(date +%Y%m%d).log

# View error logs
cat ./flashcards/logs/flashcard_generator_errors_$(date +%Y%m%d).log

# Search for specific errors
grep -i "error\|exception\|failed" ./flashcards/logs/*.log
```

## 🔧 Configuration Issues

### Invalid Configuration Values

#### ❌ "Max flashcards must be greater than 0"

**Solution**:
```bash
export MAX_FLASHCARDS=10  # Set to valid positive number
```

#### ❌ "Count cannot exceed maximum"

**Solution**:
```bash
# Either increase the limit
export MAX_FLASHCARDS=100

# Or reduce the count
python main.py --topic "animals" --count 20
```

### Cache Issues

#### ❌ Cache not working / "Cache miss" always

**Diagnostic**:
```bash
# Check cache directory
ls -la ./flashcards/cache/

# Check cache configuration
python -c "
from flashcard_generator.config import ConfigManager
config = ConfigManager.load_config()
print('Caching enabled:', config.enable_caching)
print('Cache max age:', config.cache_max_age_hours)
"
```

**Solutions**:
1. **Enable caching**:
   ```bash
   export ENABLE_CACHING=true
   ```

2. **Clear corrupted cache**:
   ```bash
   rm -rf ./flashcards/cache/
   ```

3. **Adjust cache settings**:
   ```bash
   export CACHE_MAX_AGE_HOURS=48
   ```

## 🌐 Network Issues

### Proxy/Firewall Problems

**Symptoms**:
- Connection timeouts
- SSL certificate errors
- "Network unreachable" errors

**Solutions**:
1. **Configure proxy** (if required):
   ```bash
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080
   ```

2. **Test direct connectivity**:
   ```bash
   curl -I https://generativelanguage.googleapis.com
   curl -I https://api.unsplash.com
   ```

3. **Use alternative DNS**:
   ```bash
   # Temporarily use Google DNS
   echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
   ```

### SSL Certificate Issues

**Error**: "SSL certificate verification failed"

**Solutions**:
1. **Update certificates**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get update && sudo apt-get install ca-certificates

   # macOS
   brew install ca-certificates
   ```

2. **Temporary workaround** (not recommended for production):
   ```python
   import ssl
   ssl._create_default_https_context = ssl._create_unverified_context
   ```

## 📊 Performance Optimization

### Slow Generation

**Diagnostic Questions**:
- How many flashcards are you generating?
- Is caching enabled?
- Are images being downloaded?
- What's your network speed?

**Optimization Steps**:

1. **Enable all optimizations**:
   ```bash
   export ENABLE_CACHING=true
   export ENABLE_ASYNC_IMAGES=true
   export MAX_CONCURRENT_IMAGES=8
   export ENABLE_BATCH_PROCESSING=true
   ```

2. **Profile performance**:
   ```python
   import time
   from flashcard_generator.flashcard_generator import FlashcardGenerator
   from flashcard_generator.config import ConfigManager
   
   config = ConfigManager.load_config()
   generator = FlashcardGenerator(config)
   
   start_time = time.time()
   flashcards = generator.generate_flashcards("animals", 5)
   end_time = time.time()
   
   print(f"Generation took: {end_time - start_time:.2f} seconds")
   print(f"Stats: {generator.get_stats()}")
   ```

3. **Optimize for your use case**:
   ```bash
   # For speed (no images)
   python main.py --topic "animals" --count 10 --no-images
   
   # For quality (with images, slower)
   python main.py --topic "animals" --count 10
   
   # For large batches (optimized)
   export BATCH_SIZE=20
   python main.py --topic "animals" --count 50
   ```

## 🆘 Getting Help

### Before Asking for Help

1. **Check this troubleshooting guide**
2. **Run diagnostic commands**
3. **Check log files**
4. **Try with minimal configuration**
5. **Test with a simple example**

### Information to Include

When reporting issues, please include:

```bash
# System information
python --version
pip list | grep -E "(google-generativeai|requests|pandas)"
uname -a

# Configuration (without API keys)
echo "Output directory: $OUTPUT_DIRECTORY"
echo "Max flashcards: $MAX_FLASHCARDS"
echo "Caching enabled: $ENABLE_CACHING"

# Error logs
tail -20 ./flashcards/logs/flashcard_generator_errors_*.log

# Minimal reproduction case
python main.py --topic "test" --count 1 --no-images
```

### Support Channels

1. **GitHub Issues**: For bugs and feature requests
2. **GitHub Discussions**: For questions and community help
3. **Documentation**: README.md and inline code comments

### Quick Fixes Checklist

- [ ] API key is set and valid
- [ ] Python version is 3.8 or higher
- [ ] All dependencies are installed
- [ ] Network connectivity is working
- [ ] Output directory has write permissions
- [ ] Not exceeding rate limits
- [ ] Using reasonable batch sizes
- [ ] Log files checked for specific errors

---

**Still having issues?** Create a [GitHub Issue](https://github.com/your-username/ai-flashcard-generator/issues) with the information above.