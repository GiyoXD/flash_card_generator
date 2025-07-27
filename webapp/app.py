from flask import Flask, render_template, request, jsonify, send_file
import os
from flashcard_generator.config import ConfigManager
from flashcard_generator.flashcard_generator import FlashcardGenerator
import zipfile
import re

app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_flashcards():
    data = request.json
    topic = data.get('word')
    include_images = data.get('include_images', True)
    count = data.get('count', 10)
    context = data.get('context')
    filename = data.get('filename') or None
    try:
        config = ConfigManager.load_config()
        config.image_download_enabled = include_images
        # Set output directory to a flat path in the project root
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'flashcards', 'web'))
        os.makedirs(output_dir, exist_ok=True)
        config.output_directory = output_dir
        generator = FlashcardGenerator(config)
        csv_file_path = generator.run(topic=topic, count=count, output_filename=filename, context=context)
        # Log the actual CSV path for debugging
        print(f"[DEBUG] CSV generated at: {csv_file_path}")
        # Check if the file exists before sending
        if not os.path.isfile(csv_file_path):
            return jsonify({'status': 'error', 'message': f'CSV file not found at {csv_file_path}'}), 500

        # Collect image paths from the CSV
        image_paths = set()
        image_dir = os.path.join(output_dir, 'images')
        image_pattern = re.compile(r'images/[^,\s]+\.(jpg|jpeg|png|gif)')
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                for match in image_pattern.findall(line):
                    # match is just the filename, so join with image_dir
                    image_path = os.path.join(output_dir, 'images', match)
                    if os.path.isfile(image_path):
                        image_paths.add(image_path)

        # Create a ZIP file containing the CSV and images
        import tempfile
        zip_basename = os.path.splitext(os.path.basename(csv_file_path))[0]
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
            with zipfile.ZipFile(tmp_zip, 'w') as zipf:
                zipf.write(csv_file_path, arcname=os.path.basename(csv_file_path))
                for img_path in image_paths:
                    arcname = os.path.relpath(img_path, output_dir)
                    zipf.write(img_path, arcname=arcname)
            zip_path = tmp_zip.name
        print(f"[DEBUG] ZIP created at: {zip_path}")
        return send_file(zip_path, as_attachment=True, download_name=f'{zip_basename}.zip')
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 