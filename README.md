# Product Scanner Web Application

A Flask-based web application that scans product barcodes and displays comprehensive sustainability and nutrition information using the Open Food Facts API.

## Features

- 📷 **Real-time Barcode Scanning** - Use your device camera to scan barcodes
- ⌨️ **Manual Entry** - Type barcodes manually as an alternative
- 🍎 **Nutrition Facts** - Complete nutritional information per 100g
- 🌱 **Sustainability Scores** - Nutri-Score and Eco-Score ratings
- 🏷️ **Product Details** - Ingredients, labels, certifications, and allergens
- 📱 **Responsive Design** - Works on desktop and mobile devices
- 🎨 **Modern UI** - Clean, gradient interface with smooth animations

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Barcode Detection**: Quagga.js
- **Data Source**: Open Food Facts API
- **Supported Formats**: EAN, UPC, Code 128

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Modern web browser with camera access

## Installation

1. **Clone or download this repository**

2. **Navigate to the project directory**
   ```bash
   cd hackaton-app
   ```

3. **Create a virtual environment (recommended)**
   ```bash
   python3 -m venv venv
   ```

4. **Activate the virtual environment**

   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

   On Windows:
   ```bash
   venv\Scripts\activate
   ```

5. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Start the Flask server**
   ```bash
   python app.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

3. **Grant camera permissions** when prompted (for barcode scanning)

## Usage

### Scanning Barcodes

1. Click the **"📷 Scan Barcode"** button
2. Allow camera access when prompted
3. Point your camera at a product barcode
4. The app will automatically detect and search for the product
5. Click **"⏹️ Stop Camera"** when done

### Manual Entry

1. Type the barcode number into the input field
2. Click **"🔎 Search"** or press Enter
3. View the product information

## Project Structure

```
hackaton-app/
├── app.py                 # Flask backend application
├── templates/
│   └── index.html        # Frontend interface
├── uploads/              # Directory for uploaded images (auto-created)
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## API Information

This application uses the **Open Food Facts API**, a free, open database of food products from around the world.

- API Endpoint: `https://world.openfoodfacts.org/api/v2/product/{barcode}.json`
- No authentication required
- Data is community-contributed and may vary in completeness

## Features Explained

### Nutri-Score (A-E)
- **A (Green)**: Best nutritional quality
- **E (Red)**: Poorest nutritional quality
- Based on nutrients, calories, sugar, salt, etc.

### Eco-Score (A-E)
- **A (Green)**: Best environmental impact
- **E (Red)**: Highest environmental impact
- Considers production, transport, packaging, etc.

### Nutrition Facts
Displays per 100g:
- Energy (kcal)
- Fat (g)
- Carbohydrates (g)
- Proteins (g)
- Salt (g)
- Fiber (g)

## Browser Compatibility

- Chrome/Edge 87+
- Firefox 85+
- Safari 14+
- Mobile browsers with camera support

## Troubleshooting

### Camera Not Working
- Ensure you've granted camera permissions
- Check that no other application is using the camera
- Try refreshing the page
- Use HTTPS (required for camera access on some browsers)

### Product Not Found
- Verify the barcode is correct
- Some products may not be in the Open Food Facts database
- Try entering the barcode manually

### Connection Issues
- Check your internet connection
- The Open Food Facts API might be temporarily unavailable
- Try again in a few moments

## Development

To run in development mode with auto-reload:

```bash
export FLASK_ENV=development  # On Windows: set FLASK_ENV=development
python app.py
```

## Production Deployment

**Important**: Before deploying to production:

1. Set `debug=False` in `app.py`
2. Use a production WSGI server (e.g., Gunicorn)
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```
3. Set up proper security (HTTPS, firewall, etc.)
4. Configure environment variables
5. Set up proper logging

## Contributing

This is an open-source project. Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## License

This project uses data from Open Food Facts, which is licensed under the Open Database License (ODbL).

## Acknowledgments

- [Open Food Facts](https://world.openfoodfacts.org/) for providing the product database
- [Quagga.js](https://github.com/ericblade/quagga2) for barcode scanning functionality
- Flask community for the excellent web framework

## Support

For issues or questions:
- Check the troubleshooting section
- Review the Open Food Facts API documentation
- Open an issue in the repository

---

**Note**: This application requires an internet connection to fetch product data from the Open Food Facts API.
