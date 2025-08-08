import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# Load environment variables from a .env file
load_dotenv()

# --- Flask App Setup ---
# Tell Flask where to find static files (JS, CSS) and templates (HTML)
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# --- Gemini AI Configuration ---
# This setup allows the app to get the API key from Render's environment variables
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- Frontend Routes ---

@app.route('/')
def home():
    """Serves the main search page (Home.html)."""
    return render_template('Home.html')

@app.route('/programs')
def home():
    """Serves the main search page (index.html)."""
    return render_template('Programs.html')
    
@app.route('/results')
def results_page():
    """Serves the results page."""
    return render_template('results.html')

# --- API Route ---

@app.route('/find-universities', methods=['POST'])
def find_universities():
    """API endpoint that receives user criteria and returns AI-generated university list."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON payload'}), 400

        required_fields = ['student_country', 'course', 'degree', 'target_country', 'fees']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        prompt = generate_prompt(
            data['student_country'],
            data['course'],
            data['degree'],
            data['target_country'],
            data['fees']
        )
        
        # Call the Gemini API
        response = model.generate_content(prompt)
        
        # Parse the AI's response
        universities = parse_gemini_response(response.text)

        if not universities:
            return jsonify({
                'error': 'Could not find any universities matching your criteria. The AI may have been unable to generate a valid response. Please try again.',
                'raw_response': response.text
            }), 404

        # Return the successful response
        return jsonify({
            'disclaimer': "The data provided is AI-generated and for guidance only. Please verify all information on the official university websites.",
            'universities': universities
        })

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'An internal server error occurred. Please try again later.'}), 500

# --- Helper Functions ---

def generate_prompt(student_country, course, degree, target_country, fees):
    """Creates a detailed prompt for the Gemini AI model."""
    return f"""
    You are an expert international university admissions counselor. A student has provided their preferences. Your task is to recommend 10 universities that best match their criteria.

    Student's Criteria:
    - Student's Home Country: {student_country}
    - Desired Course/Field of Study: {course}
    - Desired Degree Level: {degree}
    - Target Country for Study: {target_country}
    - Preferred Annual Tuition Fee Range: {fees}

    Your Instructions:
    1.  Strict Output Format: You MUST respond with ONLY a Python-style list of strings. Do not add any other text, explanation, or introductory sentences. Each string in the list must contain four pieces of information separated by a semicolon ';'.
        - Format for each item: "University Name; City; Estimated Annual Tuition Fees; Website URL"
        - The Website URL must be the official university admissions page if possible, otherwise the homepage. Ensure it starts with https://.
    2.  Find 10 universities in the '{target_country}' that match the criteria.
    3.  Do NOT recommend any universities from the student's home country, '{student_country}'.
    """

def parse_gemini_response(response_text: str):
    """Parses the raw text response from Gemini to extract university data."""
    universities = []
    pattern = r'"([^"]+)"'
    matches = re.findall(pattern, response_text)

    for item in matches:
        parts = [p.strip() for p in item.split(';')]
        if len(parts) == 4:
            universities.append({
                'name': parts[0],
                'city': parts[1],
                'tuition': parts[2],
                'website': parts[3]
            })
    return universities

if __name__ == '__main__':
    # This part is for local development. Render will use the Gunicorn command instead.
    app.run(debug=True, host='0.0.0.0', port=5000)

