"""
ScarletScanner - Rutgers Product Sustainability Scanner
Flask web application for scanning product barcodes
Displays Nutri-Score, Eco-Score, and HowGood sustainability metrics
"""

from flask import Flask, render_template, request, jsonify
import requests
import os
from werkzeug.utils import secure_filename
from groq import Groq
import json

app = Flask(__name__)
app.secret_key = 'scarletscanner-rutgers-2025'

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
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def allowed_file(filename):
    """Check if uploaded file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_score_summary(score_type, grade, product_name):
    """
    Generate AI-powered summary for Nutri-Score or Eco-Score
    """
    if not client:
        return f"{score_type}: {grade}"

    try:
        prompt = f"""Provide a brief 2-sentence summary for this product's {score_type}.
Product: {product_name}
{score_type}: {grade}

Explain what this grade means and why it matters. Be concise and helpful."""

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=150,
        )

        return chat_completion.choices[0].message.content.strip()

    except Exception as e:
        print(f"AI summary error: {e}")
        return f"{score_type}: {grade}"


def generate_waste_reduction_tips(product_info):
    """
    Generate personalized waste reduction and recycling tips based on product
    """
    if not client:
        return None

    try:
        prompt = f"""Based on this product, provide practical waste reduction and recycling tips for consumers.

Product Information:
- Name: {product_info.get('name', 'Unknown')}
- Brand: {product_info.get('brand', 'Unknown')}
- Categories: {product_info.get('categories', 'Unknown')}
- Packaging: {product_info.get('packaging', 'Unknown')}
- Labels: {product_info.get('labels', 'None')}

Provide 3-4 specific, actionable tips. Focus on the most relevant ones for this product.

Respond in JSON format with an array of tips:
{{
  "tips": [
    {{"icon": "♻️", "title": "Recycle", "description": "brief instruction"}},
    {{"icon": "🔄", "title": "Reuse", "description": "brief idea"}},
    {{"icon": "🛒", "title": "Buy Better", "description": "brief alternative"}}
  ]
}}

Keep each description very concise (one sentence, max 12 words) and actionable."""

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON generator. Only respond with valid JSON. Never include markdown formatting or explanations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.4,
            max_tokens=800,
            response_format={"type": "json_object"}
        )

        response_text = chat_completion.choices[0].message.content.strip()

        # Extract JSON from response if it has code blocks
        if '```json' in response_text:
            json_start = response_text.find('```json') + 7
            json_end = response_text.find('```', json_start)
            response_text = response_text[json_start:json_end].strip()
        elif '```' in response_text:
            json_start = response_text.find('```') + 3
            json_end = response_text.find('```', json_start)
            response_text = response_text[json_start:json_end].strip()

        tips_data = json.loads(response_text)
        return tips_data.get('tips', [])

    except Exception as e:
        print(f"Waste reduction tips error: {e}")
        import traceback
        print(traceback.format_exc())
        return None


def generate_product_alternatives(product_info):
    """
    Generate healthier and more sustainable product alternatives
    """
    if not client:
        return None

    try:
        prompt = f"""Based on this product, recommend 3 alternative products that are healthier and more sustainable.

Product Information:
- Name: {product_info.get('name', 'Unknown')}
- Brand: {product_info.get('brand', 'Unknown')}
- Categories: {product_info.get('categories', 'Unknown')}
- Nutri-Score: {product_info.get('nutriscore_grade', 'N/A')}
- Eco-Score: {product_info.get('ecoscore_grade', 'N/A')}

Provide 3 specific alternative products that:
1. Have better nutritional profiles (lower in sugar, salt, saturated fat, or higher in nutrients)
2. Are more environmentally sustainable (organic, local, less packaging, better sourcing)
3. Are realistic alternatives that consumers can actually find in stores

Respond in JSON format:
{{
  "alternatives": [
    {{
      "name": "Product name",
      "brand": "Brand name",
      "reason": "Brief explanation why it's better (max 15 words)",
      "health_benefit": "Key health improvement",
      "sustainability_benefit": "Key environmental improvement"
    }}
  ]
}}

Keep each field concise and actionable."""

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON generator. Only respond with valid JSON. Never include markdown formatting or explanations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.4,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        response_text = chat_completion.choices[0].message.content.strip()

        # Extract JSON from response if it has code blocks
        if '```json' in response_text:
            json_start = response_text.find('```json') + 7
            json_end = response_text.find('```', json_start)
            response_text = response_text[json_start:json_end].strip()
        elif '```' in response_text:
            json_start = response_text.find('```') + 3
            json_end = response_text.find('```', json_start)
            response_text = response_text[json_start:json_end].strip()

        alternatives_data = json.loads(response_text)
        return alternatives_data.get('alternatives', [])

    except Exception as e:
        print(f"Product alternatives error: {e}")
        import traceback
        print(traceback.format_exc())
        return None


def generate_sustainability_metrics(product_info):
    """
    Generate HowGood-style sustainability metrics analysis for the product
    Returns scores (0-10) for 8 core sustainability metrics
    """
    if not client:
        return None

    try:
        prompt = f"""Analyze this food product using HowGood's 8 core sustainability metrics. Based on publicly available data about typical products in this category, provide scores from 0-10 (10 being best) for each metric.

Product Information:
- Name: {product_info.get('name', 'Unknown')}
- Brand: {product_info.get('brand', 'Unknown')}
- Categories: {product_info.get('categories', 'Unknown')}
- Ingredients: {product_info.get('ingredients', 'Not available')}
- Labels: {product_info.get('labels', 'None')}

Provide scores (0-10) and brief explanations for:

1. **Greenhouse Gas Emissions**: Carbon footprint (cradle-to-farm gate) of ingredients
2. **Processing**: Energy used to process the ingredients
3. **Blue Water Usage**: Water required to grow the ingredients
4. **Land Occupation**: Land required to produce the ingredients
5. **Soil Health**: Impact on soil from growing ingredients
6. **Labor Risk**: Overall labor risk in ingredient production
7. **Animal Welfare**: How animals are treated (if applicable)
8. **Biodiversity**: Impact on biodiversity from growing ingredients

Respond in JSON format:
{{
  "greenhouse_gas": {{"score": 7, "explanation": "Low emissions due to..."}},
  "processing": {{"score": 6, "explanation": "Moderate processing..."}},
  "water_usage": {{"score": 5, "explanation": "Average water use..."}},
  "land_use": {{"score": 8, "explanation": "Efficient land use..."}},
  "soil_health": {{"score": 7, "explanation": "Minimal soil impact..."}},
  "labor_risk": {{"score": 6, "explanation": "Moderate labor standards..."}},
  "animal_welfare": {{"score": 5, "explanation": "Standard practices..." or "N/A - plant-based"}},
  "biodiversity": {{"score": 6, "explanation": "Neutral biodiversity impact..."}}
}}"""

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON generator. Only respond with valid JSON. Never include markdown formatting or explanations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        response_text = chat_completion.choices[0].message.content.strip()

        # Extract JSON from response if it has code blocks
        if '```json' in response_text:
            json_start = response_text.find('```json') + 7
            json_end = response_text.find('```', json_start)
            response_text = response_text[json_start:json_end].strip()
        elif '```' in response_text:
            json_start = response_text.find('```') + 3
            json_end = response_text.find('```', json_start)
            response_text = response_text[json_start:json_end].strip()

        metrics = json.loads(response_text)
        return metrics

    except Exception as e:
        print(f"Sustainability metrics error: {e}")
        import traceback
        print(traceback.format_exc())
        return None




@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')


@app.route('/scan', methods=['POST'])
def scan_barcode():
    """
    Handle barcode scan requests and return product information with Nutri-Score and Eco-Score
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

        # Fetch product data from Open Food Facts
        url = OPEN_FOOD_FACTS_API.format(barcode)
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        api_data = response.json()

        if api_data.get('status') != 1:
            return jsonify({
                'success': False,
                'error': 'Product not found in database'
            }), 404

        product = api_data.get('product', {})

        # Helper function to round nutrient values
        def round_nutrient(value):
            if value == 'N/A' or value is None:
                return 'N/A'
            try:
                return round(float(value), 2)
            except (ValueError, TypeError):
                return 'N/A'

        # Extract product information
        product_info = {
            'success': True,
            'barcode': barcode,
            'name': product.get('product_name', 'Unknown Product'),
            'brand': product.get('brands', 'Unknown Brand'),
            'image': product.get('image_url', ''),
            'categories': product.get('categories', ''),
            'ingredients': product.get('ingredients_text', 'Not available'),
            'labels': product.get('labels', ''),
            'packaging': product.get('packaging', 'Unknown'),
            'allergens': product.get('allergens', 'None specified'),
            'nutriments': {
                'energy': round_nutrient(product.get('nutriments', {}).get('energy-kcal_100g')),
                'fat': round_nutrient(product.get('nutriments', {}).get('fat_100g')),
                'carbohydrates': round_nutrient(product.get('nutriments', {}).get('carbohydrates_100g')),
                'proteins': round_nutrient(product.get('nutriments', {}).get('proteins_100g')),
                'salt': round_nutrient(product.get('nutriments', {}).get('salt_100g')),
                'fiber': round_nutrient(product.get('nutriments', {}).get('fiber_100g'))
            }
        }

        # Get Nutri-Score and Eco-Score
        nutriscore_grade = product.get('nutriscore_grade', '').upper()
        ecoscore_grade = product.get('ecoscore_grade', '').upper()

        # Generate AI summaries for both scores
        nutriscore_summary = generate_score_summary('Nutri-Score', nutriscore_grade or 'Not Available', product_info['name'])
        ecoscore_summary = generate_score_summary('Eco-Score', ecoscore_grade or 'Not Available', product_info['name'])

        product_info['nutriscore_grade'] = nutriscore_grade or 'N/A'
        product_info['ecoscore_grade'] = ecoscore_grade or 'N/A'
        product_info['nutriscore_summary'] = nutriscore_summary
        product_info['ecoscore_summary'] = ecoscore_summary

        # Generate HowGood sustainability metrics
        sustainability_metrics = generate_sustainability_metrics(product_info)
        if sustainability_metrics:
            product_info['sustainability_metrics'] = sustainability_metrics

            # Calculate overall sustainability score (average of all 8 metrics)
            scores = [
                sustainability_metrics.get('greenhouse_gas', {}).get('score', 0),
                sustainability_metrics.get('processing', {}).get('score', 0),
                sustainability_metrics.get('water_usage', {}).get('score', 0),
                sustainability_metrics.get('land_use', {}).get('score', 0),
                sustainability_metrics.get('soil_health', {}).get('score', 0),
                sustainability_metrics.get('labor_risk', {}).get('score', 0),
                sustainability_metrics.get('animal_welfare', {}).get('score', 0),
                sustainability_metrics.get('biodiversity', {}).get('score', 0)
            ]
            overall_score = round(sum(scores) / len(scores), 1) if scores else 0
            product_info['overall_sustainability_score'] = overall_score

        # Generate waste reduction tips
        waste_tips = generate_waste_reduction_tips(product_info)
        if waste_tips:
            product_info['waste_reduction_tips'] = waste_tips

        # Generate product alternatives
        alternatives = generate_product_alternatives(product_info)
        if alternatives:
            product_info['product_alternatives'] = alternatives

        return jsonify(product_info), 200

    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Request timed out. Please try again.'
        }), 500
    except requests.exceptions.RequestException:
        return jsonify({
            'success': False,
            'error': 'Network error: Unable to fetch product data'
        }), 500
    except Exception as e:
        import traceback
        print(f"Error in scan_barcode: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
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
    app.run(debug=True, host='0.0.0.0', port=5001)