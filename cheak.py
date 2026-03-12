from flask import Flask, request, jsonify, render_template
import requests
import json
import PyPDF2
import pandas as pd
import docx
from bs4 import BeautifulSoup
import validators
import os
import datetime
from flask_cors import CORS
from pymongo import MongoClient
import os
import requests
import random
import string
import re

#from flask_pymongo import PyMongo 


app = Flask(__name__)
CORS(app)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'csv', 'xlsx', 'xls', 'docx'}

# MongoDB Connection
MONGO_URI = "uri"
client = MongoClient(MONGO_URI)
mongo = client
#mongo = PyMongo(app)
db = client.your_database_name
files_collection = db.files

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'csv', 'xlsx', 'xls', 'docx'}

memory = {"interactions": []}  # Store conversation history
context = []  # Store user queries
context_window = 5  # Limit context size


app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

API_KEY = "api_key"  # Replace with your actual API key
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
headers = {"Content-Type": "application/json"}
memory = {"interactions": []}  # Initialize memory as a dictionary with an interactions list
context = []  # Initialize context list
context_window = 3  # Set context window size

def read_file(file_path):
    try:
        ext = file_path.lower().split('.')[-1]
        if ext == "txt":
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        elif ext == "pdf":
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        elif ext in ["csv", "xlsx", "xls"]:
            df = pd.read_excel(file_path) if ext in ["xlsx", "xls"] else pd.read_csv(file_path)
            return df.to_string()
        elif ext == "docx":
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs if para.text])
        else:
            return f"Unsupported file type: {file_path}"
    except Exception as e:
        return f"Error reading {file_path}: {e}"

def fetch_web_content(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            return BeautifulSoup(response.text, "html.parser").get_text(separator="\n")[:5000]
        else:
            return f"Failed to fetch URL {url}. HTTP Status: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Error fetching {url}: {e}"

def ask_ai(content, operation):
    system_prompt = "You are an AI chatbot with a provided knowledge base. You must answer questions outside the knowledge base only if it is related to the topic. If the user asks anything way outside knowledge base, you should say sorry and ask the user to ask another question. Also avoid unnecessary punctuations like asterisks. Make the usage of new lines and make it look easy to read."
    temperature = 0.5

    data = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{operation}\n\n{content}"}]
            }
        ],
        "generationConfig": {
            "temperature": 1,
            "topP": 0.95,
            "topK": 40,
            "maxOutputTokens": 8192,
            "responseMimeType": "text/plain"
        },
        "safetySettings": [],
        "systemInstruction": {
            "parts": [{
                "text": "You are an AI chatbot with a provided knowledge base. You must answer questions outside the knowledge base only if it is related to the topic. If the user asks anything way outside knowledge base, you should say sorry and ask the user to ask another question. Also avoid unnecessary punctuations like asterisks. Make the usage of new lines and make it look easy to read."
            }]
        }
    }
    try:
        response = requests.post(URL, headers=headers, json=data)
        candidates = response.json().get("candidates", [])
        return candidates[0]["content"].get("parts", [{}])[0].get("text", "No response found.") if candidates else "API Error."
    except requests.exceptions.RequestException as e:
        return "API request failed: " + str(e)

def allowed_file(filename):
    return '.' in filename and '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    

# Store API keys in memory (for now; you can later use MongoDB)
api_keys = {}

def create_api_key():
    return "API-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))

@app.route('/generate_api_key', methods=['POST'])
def generate_api_key():
    """
    Request: { "user_id": "some_identifier" }
    Response: { "api_key": "API-..." }
    """
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        # If no user_id is provided, generate a generic one or handle as needed
        user_id = "anonymous_user" + datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

    new_key = create_api_key()
    api_keys[user_id] = new_key
    print(f"Generated API key '{new_key}' for user '{user_id}'") # Optional logging

    return jsonify({'message': 'API key generated', 'api_key': new_key}), 200



@app.route('/chatb')
def chatb():
    return render_template('chatbot.html')

@app.route('/chat', methods=['GET', 'POST'])
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    global memory, context  # Access the global memory and context
    
    # Extract and validate API key
    #api_key = request.headers.get("X-API-KEY")
    #if api_key not in api_keys.values():
     #   return jsonify({'error': 'Invalid or missing API key'}), 403


    if request.method == 'POST':
        data = request.get_json()
        user_input = data.get('message', '').strip()
        api_key = data.get('api_key', '')

        if api_key != "AIzaSyDzvY-_3mx16gPVeJvlKoHUyWyQ9vLoNao":  # Secure check
            return jsonify({'error': 'Invalid or missing API key'}), 403

    else:  # Handle GET request from frontend
        user_input = request.args.get('message', '').strip()

    if not user_input:
        return jsonify({'error': 'Message is empty'}), 400

    memory["interactions"].append({"query": user_input, "timestamp": datetime.datetime.now().isoformat()})  # Save to memory

    if os.path.exists(user_input):
        memory[user_input] = read_file(user_input)
        available_sources = "\nAvailable Sources:\n" + "\n".join(
            [f"{idx+1}. {key}" for idx, key in enumerate(memory.keys()) if key != "interactions"]
        )
        result = f"File loaded. {available_sources}"
    elif validators.url(user_input):
        memory[user_input] = fetch_web_content(user_input)
        available_sources = "\nAvailable Sources:\n" + "\n".join(
            [f"{idx+1}. {key}" for idx, key in enumerate(memory.keys()) if key != "interactions"]
        )
        result = f"URL loaded. {available_sources}"
    elif any(key != "interactions" for key in memory):
        combined_content = "\n\n".join(value for key, value in memory.items() if key != "interactions")
        context.append(user_input)
        context = context[-context_window:]
        response = ask_ai(combined_content, user_input)
        cleaned_text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', response)
        result = cleaned_text
        
        
        
    else:
        result = ask_ai("", user_input)

    return jsonify({'response': result})
    


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = file.filename.replace("..", "")
        filename = filename.replace("/", "")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        memory[filename] = read_file(filepath)
        available_sources = "\nAvailable Sources:\n" + "\n".join([f"{idx}. {key}" for idx, key in enumerate(memory.keys()) if key != "interactions"])

        return jsonify({'filename': filename, 'message': f"File '{filename}' uploaded. {available_sources}\n\nplease enter your question."})
    else:
        return jsonify({'error': 'Upload failed'}), 500
        
        
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('index2.html')
    
@app.route('/login')
def login():
    return render_template('login.html')
    
@app.route('/signup')
def signup():
    return render_template('signup.html')
    

@app.route('/API')
def API():
    return render_template('API.html')
    
    
@app.route('/uploadB')
def uploadB():
    return render_template('upload.html')
    
    
@app.route('/uploadDB', methods=['POST'])
def upload_files():
    try:
        files = request.files.getlist('databaseFile')
        url = request.form.get('databaseUrl')

        if not files and not url:
            return jsonify({'error': 'No files or URL provided'}), 400

        if files:
            if len(files) > 3:
                return jsonify({'error': 'You can upload a maximum of 3 files.'}), 400

            file_paths = []
            for file in files:
                if file and allowed_file(file.filename):
                    filename = file.filename
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    file_paths.append(filepath)

                    mongo.db.files.insert_one({
                        'filename': filename,
                        'filepath': filepath,
                        'original_filename': file.filename
                    })

            return jsonify({'message': 'Files uploaded successfully', 'file_paths': file_paths}), 200

        elif url:
            data = request.get_json()
            url = data.get('url', '').strip()

            if not url:
                return jsonify({'error': 'URL is empty'}), 400

            if not validators.url(url):
                return jsonify({'error': 'Invalid URL'}), 400

            try:
                content = fetch_web_content(url)
                filename = f"web_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
                memory[filename] = content
                return jsonify({'filename': filename, 'message': f"Web content from '{url}' uploaded."})
            except Exception as e:
                return jsonify({'error': f'URL processing failed: {e}'}), 500



    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)

