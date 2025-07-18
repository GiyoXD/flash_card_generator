# 🚀 Quick Start Guide - AI Flashcard Generator

**Generate flashcards with English words, Chinese translations, and images in 5 minutes!**

## Step 1: Get Your API Key (2 minutes)

### Required: Google Gemini API Key (FREE)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key (starts with `AIza...`)

### Optional: Unsplash API Key (for better images)
1. Go to [Unsplash Developers](https://unsplash.com/developers)
2. Create account → New Application
3. Copy your **Access Key**

## Step 2: Setup (1 minute)

### Option A: Environment Variables (Recommended)
```bash
# Windows (Command Prompt)
set GEMINI_API_KEY=your_gemini_api_key_here
set IMAGE_API_KEY=your_unsplash_key_here

# Windows (PowerShell)
$env:GEMINI_API_KEY="your_gemini_api_key_here"
$env:IMAGE_API_KEY="your_unsplash_key_here"

# Mac/Linux
export GEMINI_API_KEY="your_gemini_api_key_here"
export IMAGE_API_KEY="your_unsplash_key_here"
```

### Option B: Create .env File
Create a file called `.env` in the project folder:
```
GEMINI_API_KEY=your_gemini_api_key_here
IMAGE_API_KEY=your_unsplash_key_here
```

## Step 3: Generate Flashcards (30 seconds)

### Basic Usage
```bash
# Generate 10 animal flashcards with images
python main.py --topic "animals" --count 10

# Generate 15 food flashcards
python main.py --topic "food" --count 15

# Generate without images (faster)
python main.py --topic "travel" --count 8 --no-images
```

### Popular Topics
- `animals` - cat, dog, bird, fish...
- `food` - apple, rice, tea, bread...
- `travel` - hotel, airport, taxi, map...
- `family` - mother, father, sister, brother...
- `colors` - red, blue, green, yellow...
- `numbers` - one, two, three, four...
- `body` - head, hand, foot, eye...
- `weather` - sunny, rainy, cloudy, hot...

## Step 4: Import to Flashcard Apps

### 📱 Anki (Most Popular)
1. Open Anki
2. Click **File** → **Import**
3. Select your CSV file (in `./flashcards/` folder)
4. **Field Mapping**:
   - Field 1 (English) → **Front**
   - Field 2 (Chinese) → **Back** 
   - Field 3 (Pinyin) → **Extra** (optional)
   - Field 4 (Image_Path) → **Add Media** (for images)
5. Click **Import**
6. Start studying! 🎓

### 📚 Quizlet
1. Go to [Quizlet.com](https://quizlet.com)
2. Create **New Study Set**
3. Click **Import from Word, Excel, etc.**
4. Upload your CSV file
5. Map columns: English → Term, Chinese → Definition
6. Save and study!

### 🧠 Other Apps
- **Memrise**: Direct CSV import
- **StudyBlue**: Copy-paste from CSV
- **Brainscape**: CSV import feature

## Example Output

Your CSV file will look like this:
```csv
English,Chinese,Pinyin,Image_Path,Topic,Created_Date
cat,猫,mao1,./images/cat_a1b2c3d4.jpg,animals,2024-01-15 14:30:22
dog,狗,gou3,./images/dog_e5f6g7h8.jpg,animals,2024-01-15 14:30:25
bird,鸟,niao3,,animals,2024-01-15 14:30:28
```

## File Organization

After generation, you'll have:
```
flashcards/
├── flashcards_20240115_143022.csv    ← Import this file
├── images/                           ← Images for your cards
│   ├── cat_a1b2c3d4.jpg
│   └── dog_e5f6g7h8.jpg
└── logs/                            ← Error logs (if needed)
```

## 🎯 Pro Tips

### For Better Results
```bash
# More specific topics work better
python main.py --topic "kitchen utensils" --count 12
python main.py --topic "office supplies" --count 10

# Custom output location
python main.py --topic "animals" --count 15 --output ./my_cards

# Clean up old files first
python main.py --topic "food" --count 20 --cleanup
```

### Performance Tips
```bash
# Set these for faster generation
set ENABLE_CACHING=true
set ENABLE_ASYNC_IMAGES=true
set MAX_CONCURRENT_IMAGES=8
```

## 🆘 Common Issues & Solutions

### "GEMINI_API_KEY environment variable is required"
**Solution**: Make sure you set your API key (see Step 2)

### "Rate limit exceeded"
**Solution**: Wait 1 minute, then try again. Free tier has limits.

### "No images found"
**Solutions**:
- Add Unsplash API key for better images
- Use `--no-images` flag for faster generation
- Try more common topics

### Images not showing in Anki
**Solution**: 
1. Copy the entire `images/` folder to your Anki media folder
2. Or use absolute paths in the CSV

## 🎓 Ready to Study!

1. **Generate**: `python main.py --topic "animals" --count 10`
2. **Import**: Open your flashcard app → Import CSV
3. **Study**: Start learning with AI-generated flashcards!

---

**Need help?** Check `TROUBLESHOOTING.md` for detailed solutions to common problems.

**Want advanced features?** See `README.md` for batch processing, optimizations, and more options.