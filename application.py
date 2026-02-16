import os
import json
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from docling.document_converter import DocumentConverter
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# AWS App Runner expects the variable name 'application'
application = Flask(__name__)
CORS(application)

# DeepSeek Configuration
client = OpenAI(
    base_url="https://api.deepseek.com",
    api_key=os.environ.get("DEEPSEEK_API_KEY")
)

@application.route('/')
def health_check():
    """Critical for AWS App Runner to know the server is alive"""
    return "OK", 200

@application.route('/api/process-ocr', methods=['POST'])
def process_ocr():
    try:
        data = request.json
        image_url = data.get('image_url')
        if not image_url:
            return jsonify({'error': 'No image URL provided'}), 400
        
        # Process OCR
        converter = DocumentConverter()
        result = converter.convert(image_url)
        ocr_text = result.document.export_to_markdown()
        
        # DeepSeek extraction logic...
        # (Keep your existing prompt and parsing logic here)
        return jsonify({"text": ocr_text}) # Simplified for example
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use the port AWS provides or default to 8080
    port = int(os.environ.get("PORT", 8080))
    application.run(host="0.0.0.0", port=port)
