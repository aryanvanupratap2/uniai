import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from langgraph.graph import StateGraph, END

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Gemini AI
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_input_from_request(data):
    """Extract input data from request and format for LangGraph"""
    uni = []
    uni.append(data.get('student_country', ''))
    uni.append(data.get('course', ''))
    uni.append(data.get('degree', ''))
    uni.append(data.get('target_country', ''))
    return uni

def fetch_data(uni: list) -> str:
    """Fetch university data using Gemini AI"""
    try:
        response = model.generate_content(f"""
You are a highly knowledgeable educational consultant specializing in global university admissions. Your task is to recommend a list of top universities to a student based on their specified requirements.

The student's details are provided in a list named 'state':
state: {uni}

The list contains five elements in this order:
[Student's Country of Origin, Desired Course, Desired Degree Type, Target Country for Study, Fees(Annual)]

Your instructions are as follows:

1.  **Identify and Exclude:** Identify the student's country of origin (the first element in the 'state' list) and **do not** include any universities from that country in your response.

2.  **Research and Apply Country-Specific Rules:** Based on the 'Target Country for Study' (the last element in the 'state' list), you must dynamically apply the correct educational and financial rules for that country.
    * For example, if the target country is Germany, you should know that most public universities charge minimal to no tuition fees for international students in certain programs.
    * If the target country is the USA, you should know that tuition fees are generally high and provide a wide but realistic range.
    * also stick to the fees range given as fifth element in the list

3.  **Generate a List of Top 10 Universities:** Create a list of 10 university recommendations that fit the student's requirements and are located in the target country.

4.  **Format the Response:** Respond with a single Python list. Each item in the list should be a string containing four pieces of information separated by commas, in this exact order:
    * University Name
    * City
    * Estimated Annual Tuition Fees (or a clear note about tuition fees, e.g., "No Tuition Fee (Semester Fee: 100-400 Euros)") also the fees number must not contain any commas
    * Estimated Annual Living Expenses
    * Example format for each item: "University Name, City, Tuition, Living Expenses"

5.  **Include a Disclaimer:** At the beginning of your response, include a brief disclaimer acknowledging that the data provided is not real-time and is for guidance only. Emphasize that the student should verify all information on official university websites.

6.  **Provide a Final Output:** Present the final list without any additional conversational text or explanations outside of the initial disclaimer just the disclaimer aaaand the list.
""")
        return response.text
    except Exception as e:
        raise Exception(f"Error generating content with Gemini: {str(e)}")

def parse_gemini_response(response_text: str):
    """Parse the Gemini response to extract disclaimer and universities"""
    lines = response_text.strip().split('\n')
    
    disclaimer = ""
    university_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this line starts a Python list
        if line.startswith('[') or (in_list and line.startswith('"')):
            in_list = True
            university_lines.append(line)
        elif in_list and (line.startswith('"') or line.endswith('",') or line.endswith('"]') or line.endswith('"')):
            university_lines.append(line)
        elif in_list and line == ']':
            university_lines.append(line)
            break
        elif not in_list and not line.startswith('['):
            disclaimer += line + " "
    
    # Clean up disclaimer
    disclaimer = disclaimer.strip()
    if not disclaimer:
        disclaimer = "The data provided is not real-time and is for guidance only. Please verify all information on official university websites."
    
    # Parse universities from the list format
    universities = []
    list_content = ' '.join(university_lines)
    
    # Extract strings from the list format
    string_pattern = r'"([^"]+)"'
    university_strings = re.findall(string_pattern, list_content)
    
    # If no proper list format found, try to extract from plain text
    if not university_strings:
        # Look for numbered items or bullet points
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\.', line) or line.startswith('-') or line.startswith('•'):
                # Remove numbering and clean
                clean_line = re.sub(r'^\d+\.\s*', '', line)
                clean_line = clean_line.lstrip('- •').strip()
                if ',' in clean_line:
                    university_strings.append(clean_line)
    
    for i, uni_str in enumerate(university_strings[:10]):  # Limit to 10
        parts = [part.strip() for part in uni_str.split(',')]
        if len(parts) >= 4:
            universities.append({
                'name': parts[0],
                'city': parts[1],
                'tuition': parts[2],
                'living_expenses': parts[3]
            })
        elif len(parts) == 3:
            universities.append({
                'name': parts[0],
                'city': parts[1],
                'tuition': parts[2],
                'living_expenses': 'Contact university for details'
            })
        elif len(parts) >= 2:
            universities.append({
                'name': parts[0],
                'city': parts[1] if len(parts) > 1 else 'Not specified',
                'tuition': parts[2] if len(parts) > 2 else 'Contact university',
                'living_expenses': 'Contact university for details'
            })
    
    return disclaimer, universities

# Build LangGraph
builder = StateGraph(list)

def langgraph_get_input(uni: list) -> list:
    """LangGraph node - this will be replaced by API input"""
    return uni

def langgraph_fetch_data(uni: list) -> list:
    """LangGraph node for fetching data"""
    response = fetch_data(uni)
    uni.append(response)
    return uni

# Define the nodes
builder.set_entry_point("get_input")
builder.add_node("get_input", langgraph_get_input)
builder.add_node("fetch_data", langgraph_fetch_data)

# Add edges
builder.add_edge("get_input", "fetch_data")
builder.add_edge("fetch_data", END)

# Compile graph
graph = builder.compile()

@app.route('/find-universities', methods=['POST'])
def find_universities():
    """Main endpoint to find universities using LangGraph"""
    try:
        # Get data from request
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['student_country', 'course', 'degree', 'target_country']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Prepare input for LangGraph
        uni_data = get_input_from_request(data)
        
        # Run LangGraph
        final_output = graph.invoke(uni_data)
        
        # The last item in the output should be the LLM response
        if len(final_output) > 4:
            llm_response = final_output[-1]  # Get the response added by fetch_data
        else:
            return jsonify({'error': 'No response generated from AI'}), 500
        
        # Parse the response
        disclaimer, universities = parse_gemini_response(llm_response)
        
        if not universities:
            return jsonify({
                'error': 'No universities found. Please try different search criteria.',
                'raw_response': llm_response[:500] + '...' if len(llm_response) > 500 else llm_response
            }), 404
        
        return jsonify({
            'disclaimer': disclaimer,
            'universities': universities,
            'student_info': {
                'student_country': data['student_country'],
                'course': data['course'],
                'degree': data['degree'],
                'target_country': data['target_country']
            },
            'total_found': len(universities)
        })
    
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/test-gemini', methods=['GET'])
def test_gemini():
    """Test endpoint to verify Gemini AI is working"""
    try:
        response = model.generate_content("Tell me a fun fact about giraffes.")
        return jsonify({
            'status': 'success',
            'message': 'Gemini AI is working correctly',
            'test_response': response.text
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Gemini AI test failed: {str(e)}'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'message': 'University Finder API is running',
        'gemini_configured': bool(api_key)
    })

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        'message': 'University Finder API with LangGraph',
        'endpoints': {
            'POST /find-universities': 'Find university recommendations',
            'GET /test-gemini': 'Test Gemini AI connection',
            'GET /health': 'Health check',
            'GET /': 'This endpoint'
        },
        'version': '2.0',
        'powered_by': 'Gemini 2.5 Flash + LangGraph'
    })

if __name__ == '__main__':
    # Test Gemini connection on startup
    try:
        test_response = model.generate_content("Hello, this is a test.")
        print("✅ Gemini AI connection successful!")
        print(f"Test response: {test_response.text[:100]}...")
    except Exception as e:
        print(f"❌ Gemini AI connection failed: {e}")
        print("Please check your GEMINI_API_KEY in the .env file")
    
    print("\n🚀 Starting University Finder API server...")
    print("📊 API endpoints available at: http://localhost:5000")
    print("🌐 Frontend should connect to: http://localhost:5000")
    print("🧪 Test Gemini at: http://localhost:5000/test-gemini")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
