import os
import json
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from docling.document_converter import DocumentConverter
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 'application' is the industry standard variable for AWS
application = Flask(__name__)
CORS(application)

# Configure DeepSeek
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
client = OpenAI(
    base_url="https://api.deepseek.com",
    api_key=DEEPSEEK_API_KEY
)

EXTRACT_PROMPT = """
Extract structured fields from this German blood product label.
Rules:
- product_type: Erythrozyten | Plasma | Thrombozyten
- blood_group: A, B, AB, O
- rhesus_factor: "+" or "-"
- expiration_date: date after "Verwendbar bis"
Return VALID JSON ONLY.
"""

@application.route('/api/process-ocr', methods=['POST'])
def process_ocr():
    try:
        data = request.json
        image_url = data.get('image_url')
        if not image_url:
            return jsonify({'error': 'No image URL provided'}), 400
        
        # We initialize converter here to ensure it doesn't freeze the build
        converter = DocumentConverter()
        result = converter.convert(image_url)
        ocr_text = result.document.export_to_markdown()
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": f"OCR text: {ocr_text} {EXTRACT_PROMPT}"}],
            temperature=0.0,
        )
        
        content = response.choices[0].message.content
        # Clean the response for potential markdown triple backticks
        json_str = content.replace('```json', '').replace('```', '').strip()
        return jsonify(json.loads(json_str))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@application.route('/api/upload', methods=['POST'])
def upload_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        image = request.files['image']
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            image.save(tmp.name)
            return jsonify({'url': tmp.name, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# This part is ONLY for local testing. AWS ignores this and uses Gunicorn.
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    application.run(host="0.0.0.0", port=port)
