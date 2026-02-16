from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from docling.document_converter import DocumentConverter
from openai import OpenAI
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

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
- blood_group: check AB first, then A, B, O, Its usually written in near Rh pos or neg
- rhesus_factor: "+" if Rh pos, "-" if Rh neg
- expiration_date: date after "Verwendbar bis" or "Verfall" or may be around Exp
- If missing → null

Return VALID JSON ONLY:
{
  "product_type": null,
  "blood_group": null,
  "rhesus_factor": null,
  "expiration_date": null
}
"""

@app.route('/api/process-ocr', methods=['POST'])
def process_ocr():
    try:
        data = request.json
        image_url = data.get('image_url')
        
        if not image_url:
            return jsonify({'error': 'No image URL provided'}), 400
        
        # Process with Docling
        converter = DocumentConverter()
        result = converter.convert(image_url)
        
        # Get OCR text
        ocr_text = result.document.export_to_markdown()
        
        # Process with DeepSeek
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "user",
                    "content": f"I have the following OCR text: {ocr_text} {EXTRACT_PROMPT}"
                }
            ],
            stream=False,
            max_tokens=4096,
            temperature=0.0,
        )
        
        content = response.choices[0].message.content
        
        # Parse JSON from response
        import json
        try:
            # Extract JSON from response (in case there's extra text)
            json_str = content
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                json_str = content.split('```')[1].split('```')[0]
            
            extracted_data = json.loads(json_str.strip())
        except:
            # If parsing fails, return raw content
            extracted_data = {'raw_response': content}
        
        return jsonify(extracted_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        image = request.files['image']
        
        # Save temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            image.save(tmp.name)
            
            # In production, upload to cloud storage and return URL
            # For now, return local path
            return jsonify({
                'url': tmp.name,
                'success': True
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)