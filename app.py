"""
Product Scanner Flask Application
Provides barcode scanning functionality with Open Food Facts API integration
"""

from flask import Flask, render_template, request, jsonify
import requests
import os
from werkzeug.utils import secure_filename
from groq import Groq
import json

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Open Food Facts API base URL
OPEN_FOOD_FACTS_API = "https://world.openfoodfacts.org/api/v2/product/{}.json"

# Initialize Groq client
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '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')
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def allowed_file(filename):
    """Check if uploaded file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_ai_scores(product_info):
    """
    Use AI to generate Nutri-Score and Eco-Score ratings with summaries
    when they're not available from the API

    Args:
        product_info (dict): Product information including nutrients and ingredients

    Returns:
        dict: AI-generated scores and summaries
    """
    if not client:
        return {
            'nutriscore': 'C',
            'nutriscore_summary': 'AI analysis unavailable - API key not configured',
            'ecoscore': 'C',
            'ecoscore_summary': 'AI analysis unavailable - API key not configured'
        }

    try:
        # Prepare product data for AI analysis
        prompt = f"""Analyze this food product and provide:
1. A Nutri-Score rating (A=healthiest to E=least healthy)
2. A brief summary explaining the Nutri-Score (2-3 sentences)
3. An Eco-Score rating (A=most sustainable to E=least sustainable)
4. A brief summary explaining the Eco-Score (2-3 sentences)

Product Information:
- Name: {product_info.get('name', 'Unknown')}
- Brand: {product_info.get('brand', 'Unknown')}
- Categories: {product_info.get('categories', 'Unknown')}
- Ingredients: {product_info.get('ingredients', 'Not available')}
- Nutrition per 100g:
  * Energy: {product_info['nutriments'].get('energy', 'N/A')} kcal
  * Fat: {product_info['nutriments'].get('fat', 'N/A')} g
  * Carbohydrates: {product_info['nutriments'].get('carbohydrates', 'N/A')} g
  * Proteins: {product_info['nutriments'].get('proteins', 'N/A')} g
  * Salt: {product_info['nutriments'].get('salt', 'N/A')} g
  * Fiber: {product_info['nutriments'].get('fiber', 'N/A')} g
- Labels: {product_info.get('labels', 'None')}

Please respond in JSON format:
{{
  "nutriscore": "A/B/C/D/E",
  "nutriscore_summary": "explanation here",
  "ecoscore": "A/B/C/D/E",
  "ecoscore_summary": "explanation here"
}}"""

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.1-70b-versatile",
            temperature=0.5,
            max_tokens=1024,
        )

        # Parse AI response
        response_text = chat_completion.choices[0].message.content

        # Extract JSON from response (handle potential markdown formatting)
        if '```json' in response_text:
            json_start = response_text.find('```json') + 7
            json_end = response_text.find('```', json_start)
            response_text = response_text[json_start:json_end].strip()
        elif '```' in response_text:
            json_start = response_text.find('```') + 3
            json_end = response_text.find('```', json_start)
            response_text = response_text[json_start:json_end].strip()

        ai_scores = json.loads(response_text)

        return {
            'nutriscore': ai_scores.get('nutriscore', 'C').upper(),
            'nutriscore_summary': ai_scores.get('nutriscore_summary', 'Analysis completed'),
            'ecoscore': ai_scores.get('ecoscore', 'C').upper(),
            'ecoscore_summary': ai_scores.get('ecoscore_summary', 'Analysis completed'),
            'ai_generated': True
        }

    except Exception as e:
        print(f"AI analysis error: {e}")
        return {
            'nutriscore': 'C',
            'nutriscore_summary': 'Unable to generate detailed analysis',
            'ecoscore': 'C',
            'ecoscore_summary': 'Unable to generate detailed analysis',
            'ai_generated': True
        }


def fetch_product_data(barcode):
    """
    Fetch product information from Open Food Facts API

    Args:
        barcode (str): Product barcode number

    Returns:
        dict: Product data or error information
    """
    try:
        # Make API request
        url = OPEN_FOOD_FACTS_API.format(barcode)
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Check if product exists
        if data.get('status') != 1:
            return {
                'success': False,
                'error': 'Product not found in database'
            }

        product = data.get('product', {})

        # Extract and format product information
        product_info = {
            'success': True,
            'barcode': barcode,
            'name': product.get('product_name', 'Unknown Product'),
            'brand': product.get('brands', 'Unknown Brand'),
            'image': product.get('image_url', ''),
            'nutriscore': product.get('nutriscore_grade', '').upper(),
            'ecoscore': product.get('ecoscore_grade', '').upper(),
            'categories': product.get('categories', ''),
            'ingredients': product.get('ingredients_text', 'Not available'),
            'labels': product.get('labels', ''),
            'allergens': product.get('allergens', 'None specified'),
            'nutriments': {
                'energy': product.get('nutriments', {}).get('energy-kcal_100g', 'N/A'),
                'fat': product.get('nutriments', {}).get('fat_100g', 'N/A'),
                'carbohydrates': product.get('nutriments', {}).get('carbohydrates_100g', 'N/A'),
                'proteins': product.get('nutriments', {}).get('proteins_100g', 'N/A'),
                'salt': product.get('nutriments', {}).get('salt_100g', 'N/A'),
                'fiber': product.get('nutriments', {}).get('fiber_100g', 'N/A')
            }
        }

        # Generate AI scores if either score is missing
        if not product_info['nutriscore'] or not product_info['ecoscore']:
            ai_scores = generate_ai_scores(product_info)

            # Use AI scores only if original scores are missing
            if not product_info['nutriscore']:
                product_info['nutriscore'] = ai_scores['nutriscore']
                product_info['nutriscore_summary'] = ai_scores['nutriscore_summary']
                product_info['nutriscore_ai'] = True

            if not product_info['ecoscore']:
                product_info['ecoscore'] = ai_scores['ecoscore']
                product_info['ecoscore_summary'] = ai_scores['ecoscore_summary']
                product_info['ecoscore_ai'] = True

        return product_info

    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request timed out. Please try again.'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Network error: Unable to fetch product data'
        }
    except Exception as e:
        return {
            'success': False,
            'error': 'An unexpected error occurred'
        }


@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')


@app.route('/scan', methods=['POST'])
def scan_barcode():
    """
    Handle barcode scan requests

    Expects JSON with 'barcode' field
    Returns product information from Open Food Facts
    """
    try:
        data = request.get_json()

        if not data or 'barcode' not in data:
            return jsonify({
                'success': False,
                'error': 'No barcode provided'
            }), 400

        barcode = data['barcode'].strip()

        if not barcode:
            return jsonify({
                'success': False,
                'error': 'Barcode cannot be empty'
            }), 400

        # Fetch product data
        product_data = fetch_product_data(barcode)

        if not product_data['success']:
            return jsonify(product_data), 404

        return jsonify(product_data), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Server error processing request'
        }), 500


@app.route('/upload', methods=['POST'])
def upload_image():
    """
    Handle image upload for barcode detection

    Future feature: Extract barcode from uploaded image
    """
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400

        file = request.files['file']

        # Check if filename is empty
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Only PNG, JPG, JPEG, and GIF are allowed.'
            }), 400

        # Save file securely
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'filename': filename,
            'note': 'Barcode extraction from images is not yet implemented'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Error uploading file'
        }), 500


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size is 16MB.'
    }), 413


if __name__ == '__main__':
    # Run the application
    # Debug mode enabled for development - disable in production
    app.run(debug=True, host='0.0.0.0', port=5000)
