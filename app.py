from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("No Gemini API key found in environment variables")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400
        
        if not file or not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        img = Image.open(filepath)
        response = model.generate_content([
            "Identify the main object in this image. Respond with only the object name in English. "
            "Be specific (e.g., 'golden retriever' instead of just 'dog').",
            img
        ])
        
        return jsonify({
            'success': True,
            'object_name': response.text.strip(),
            'image_path': f"/static/uploads/{filename}"
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Error processing image: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(debug=True)