# 🖼️ How to Import Flashcards WITH Images

This guide shows you exactly how to get your generated flashcards with images working in popular flashcard apps.

## Understanding the Generated Files

When you run:
```bash
python main.py --topic "animals" --count 5
```

You get these files:
```
flashcards/
├── flashcards_20240115_143022.csv    ← The flashcard data
└── images/                           ← The downloaded images
    ├── cat_a1b2c3d4.jpg
    ├── dog_e5f6g7h8.jpg
    └── bird_i9j0k1l2.jpg
```

## CSV Content Example
```csv
English,Chinese,Pinyin,Image_Path,Topic,Created_Date
cat,猫,mao1,./images/cat_a1b2c3d4.jpg,animals,2024-01-15 14:30:22
dog,狗,gou3,./images/dog_e5f6g7h8.jpg,animals,2024-01-15 14:30:25
bird,鸟,niao3,./images/bird_i9j0k1l2.jpg,animals,2024-01-15 14:30:28
```

## Method 1: Anki (Recommended for Images)

### Step 1: Prepare Images
1. Find your Anki media folder:
   - **Windows**: `C:\Users\[username]\AppData\Roaming\Anki2\[profile]\collection.media\`
   - **Mac**: `~/Library/Application Support/Anki2/[profile]/collection.media/`
   - **Linux**: `~/.local/share/Anki2/[profile]/collection.media/`

2. Copy ALL images from `flashcards/images/` to your Anki media folder

### Step 2: Modify CSV for Anki
Create a new CSV file with just the image filenames (not full paths):
```csv
English,Chinese,Pinyin,Image
cat,猫,mao1,cat_a1b2c3d4.jpg
dog,狗,gou3,dog_e5f6g7h8.jpg
bird,鸟,niao3,bird_i9j0k1l2.jpg
```

### Step 3: Import to Anki
1. Open Anki
2. **File** → **Import**
3. Select your modified CSV
4. **Field Mapping**:
   - Field 1 → **Front**
   - Field 2 → **Back**
   - Field 3 → **Extra** (for pinyin)
   - Field 4 → **Add to field** → Create new field called "Image"
5. **Import**

### Step 4: Edit Card Template
1. Go to **Browse** → Select your deck
2. Click **Cards...**
3. In the **Front Template**, add:
```html
{{Front}}
<br>
{{#Image}}<img src="{{Image}}" style="max-width: 300px;">{{/Image}}
```

4. In the **Back Template**, add:
```html
{{Front}}
<br>
{{#Image}}<img src="{{Image}}" style="max-width: 300px;">{{/Image}}
<hr>
{{Back}}
<br>
<small>{{Extra}}</small>
```

## Method 2: Quizlet (Limited Image Support)

Quizlet has limited image support, but you can:

1. Upload images manually to Quizlet
2. Import the text content from CSV
3. Add images one by one to each card

## Method 3: AnkiDroid/Mobile

For mobile Anki:
1. Sync your desktop Anki (with images) to AnkiWeb
2. Download to your mobile device
3. Images will sync automatically

## Method 4: Simple HTML Flashcards

Create a simple HTML file for web-based studying:

```html
<!DOCTYPE html>
<html>
<head>
    <title>My Flashcards</title>
    <style>
        .card { border: 1px solid #ccc; margin: 10px; padding: 20px; }
        .image { max-width: 200px; }
        .chinese { font-size: 24px; color: #d32f2f; }
        .pinyin { color: #666; font-style: italic; }
    </style>
</head>
<body>
    <div class="card">
        <h3>cat</h3>
        <img src="images/cat_a1b2c3d4.jpg" class="image">
        <p class="chinese">猫</p>
        <p class="pinyin">mao1</p>
    </div>
    <!-- Add more cards... -->
</body>
</html>
```

## Automated Image Import Script

Here's a Python script to help prepare your files for Anki:

```python
import csv
import shutil
from pathlib import Path

def prepare_for_anki(csv_file, anki_media_folder):
    """Prepare flashcard files for Anki import."""
    
    # Read the original CSV
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        cards = list(reader)
    
    # Copy images and create new CSV
    new_cards = []
    for card in cards:
        if card['Image_Path']:
            # Copy image to Anki media folder
            image_path = Path(card['Image_Path'])
            if image_path.exists():
                dest = Path(anki_media_folder) / image_path.name
                shutil.copy2(image_path, dest)
                
                # Update card with just filename
                card['Image'] = image_path.name
        
        new_cards.append({
            'English': card['English'],
            'Chinese': card['Chinese'], 
            'Pinyin': card['Pinyin'],
            'Image': card.get('Image', '')
        })
    
    # Write new CSV
    output_file = csv_file.replace('.csv', '_anki.csv')
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['English', 'Chinese', 'Pinyin', 'Image'])
        writer.writeheader()
        writer.writerows(new_cards)
    
    print(f"✅ Prepared for Anki: {output_file}")
    print(f"✅ Images copied to: {anki_media_folder}")

# Usage
prepare_for_anki(
    'flashcards/flashcards_20240115_143022.csv',
    'C:/Users/YourName/AppData/Roaming/Anki2/User 1/collection.media/'
)
```

## Quick Test

To test if everything works:

1. Generate a small set:
```bash
python main.py --topic "colors" --count 3
```

2. Check that you have:
   - CSV file with image paths
   - Images in the images folder
   - Images display correctly when opened

3. Import to your flashcard app following the steps above

## Troubleshooting Images

### Images not showing?
- Check that image files exist in the specified paths
- Verify image file extensions (.jpg, .png, etc.)
- Make sure images are copied to the correct media folder

### Images too large?
- The generator downloads web-optimized images
- You can resize them if needed using any image editor

### No images generated?
- Check if you have an IMAGE_API_KEY set
- Try with `--no-images` first to test the basic functionality
- Some topics may have fewer available images

---

**Pro Tip**: Start with a small batch (3-5 cards) to test your import process before generating larger sets!