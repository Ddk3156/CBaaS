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
import shutil
import zipfile
from flask import send_file


#from flask_pymongo import PyMongo 


app = Flask(__name__)
CORS(app)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'csv', 'xlsx', 'xls', 'docx'}

# MongoDB Connection
MONGO_URI = "mongodb+srv://xyz:sYeyohvGhqF67jEg@trialcluster.b5jsb.mongodb.net/?retryWrites=true&w=majority&appName=trialCluster"
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

API_KEY = "AIzaSyDzvY-_3mx16gPVeJvlKoHUyWyQ9vLoNao"  # Replace with your actual API key
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
    system_prompt = "You are an AI chatbot with a provided knowledge base. You must answer questions outside the knowledge base only if it is related to the topic. If the user asks anything way outside knowledge base, you should say sorry and ask the user to ask another question. Format your responses using markdown: use **bold** for emphasis, *italic* for subtle emphasis, `code` for inline code, ```code blocks``` for multi-line code with language specification, - or * for bullet lists, 1. for numbered lists, and proper line breaks between paragraphs. Make responses visually structured and easy to read."
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
                "text": "You are an AI chatbot with a provided knowledge base. You must answer questions outside the knowledge base only if it is related to the topic. If the user asks anything way outside knowledge base, you should say sorry and ask the user to ask another question. Format your responses using markdown: use **bold** for emphasis, *italic* for subtle emphasis, `code` for inline code, ```code blocks``` for multi-line code with language specification, - or * for bullet lists, 1. for numbered lists, and proper line breaks between paragraphs. Make responses visually structured and easy to read."
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

# Store knowledge bases per user/session
user_knowledge_bases = {}  # {user_id: {"files": [...], "content": "combined_content"}}

def create_api_key():
    return "API-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))
    

def prepare_user_files(api_key, user_id, knowledge_base_content=""):
    """
    Copies template chatbot files, injects API key, saves knowledge base as JSON, and returns a zip path.
    """
    # Ensure temp directory exists
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    template_dir = "templates/chatbot_template"
    user_dir = os.path.join(temp_dir, user_id)

    # Clean old temp folder if exists
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)
    shutil.copytree(template_dir, user_dir)

    # Inject the API key into JS
    js_path = os.path.join(user_dir, "script.js")
    with open(js_path, "r", encoding="utf-8") as f:
        js_content = f.read()
        
    # Replace API key
    js_content = js_content.replace("{{API_KEY}}", api_key)
    # Define system prompt to embed into the chatbot
    system_prompt = (
    "You are an AI chatbot with a provided knowledge base. "
    "You must answer questions outside the knowledge base only if it is related to the topic. "
    "If the user asks anything way outside knowledge base, you should say sorry and ask the user to ask another question. "
    "Format your responses using markdown: use **bold** for emphasis, *italic* for subtle emphasis, "
    "`code` for inline code, ```code blocks``` for multi-line code with language specification, "
    "- or * for bullet lists, 1. for numbered lists, and proper line breaks between paragraphs. "
    "Make responses visually structured and easy to read."
    )

# Inject the system prompt placeholder in JS (if found)
    js_content = js_content.replace("{{SYSTEM_PROMPT}}", system_prompt)


    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js_content)

    # Save knowledge base as an external JSON file to avoid huge inline JS
    if knowledge_base_content:
        kb_path = os.path.join(user_dir, "knowledge_base.json")
        with open(kb_path, "w", encoding="utf-8") as kb_file:
            json.dump({"content": knowledge_base_content}, kb_file, ensure_ascii=False)

    # Zip the directory
    zip_path = f"{user_dir}.zip"
    if os.path.exists(zip_path):
        os.remove(zip_path)
    shutil.make_archive(user_dir, 'zip', user_dir)

    return zip_path
    


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
        # Preserve markdown formatting - don't strip asterisks
        result = response
        
        
        
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
        
        # Generate or get session ID from cookie or create one
        session_id = request.cookies.get('session_id') or ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        
        if not files and not url:
            return jsonify({'error': 'No files or URL provided'}), 400

        file_contents = []
        file_names = []
        
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
                    file_names.append(filename)
                    
                    # Read and store file content
                    content = read_file(filepath)
                    file_contents.append(content)

                    # Best-effort DB insert; do not fail upload if DB is unavailable
                    try:
                        files_collection.insert_one({
                            'filename': filename,
                            'filepath': filepath,
                            'original_filename': file.filename
                        })
                    except Exception as db_err:
                        # Log and proceed; avoid causing upload failure due to DB connectivity
                        print(f"Warning: DB insert failed for {filename}: {db_err}")
            
            # Combine all file contents
            combined_content = "\n\n".join(file_contents)
            user_knowledge_bases[session_id] = {
                "files": file_names,
                "content": combined_content
            }
            
            response = jsonify({
                'message': 'Files uploaded successfully', 
                'file_paths': file_paths,
                'session_id': session_id,
                'ready_for_download': True
            })
            response.set_cookie('session_id', session_id, max_age=3600*24)  # 24 hours
            return response, 200

        elif url:
            '''
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()

                content_type = response.headers.get('content-type')
                extension = mimetypes.guess_extension(content_type)
                if extension not in ['.txt','.pdf','.csv','.xlsx','.xls','.docx',]:
                  return jsonify({'error': 'URL does not point to an allowed file type.'}), 400

                filename = f"url_file{extension}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                mongo.db.urls.insert_one({
                    'url': url,
                    'filepath': filepath,
                    'filename': filename,
                })

                return jsonify({'message': 'URL content saved successfully', 'file_path': filepath}), 200

            except requests.exceptions.RequestException as e:
                return jsonify({'error': f'Failed to fetch URL: {e}'}), 400
                '''
               
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
                
                # Store in knowledge base
                session_id = request.cookies.get('session_id') or ''.join(random.choices(string.ascii_letters + string.digits, k=16))
                user_knowledge_bases[session_id] = {
                    "files": [url],
                    "content": content
                }
                
                response = jsonify({
                    'filename': filename, 
                    'message': f"Web content from '{url}' uploaded.",
                    'session_id': session_id,
                    'ready_for_download': True
                })
                response.set_cookie('session_id', session_id, max_age=3600*24)
                return response
            except Exception as e:
                return jsonify({'error': f'URL processing failed: {e}'}), 500



    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/generate_chatbot', methods=['POST'])
def generate_chatbot():
    """
    Generates a complete chatbot ZIP file with embedded API key and knowledge base.
    Returns the ZIP file for download.
    """
    try:
        # Get session ID
        session_id = request.cookies.get('session_id') or request.json.get('session_id') if request.is_json else None
        
        if not session_id:
            return jsonify({'error': 'No session ID found. Please upload files first.'}), 400
        
        # Check if knowledge base exists for this session
        if session_id not in user_knowledge_bases:
            return jsonify({'error': 'No knowledge base found for this session. Please upload files first.'}), 400
        
        kb_data = user_knowledge_bases[session_id]
        knowledge_base_content = kb_data.get('content', '')
        
        # Use the configured Google API key for plug-and-play
        api_key = API_KEY
        
        # Generate user ID for file naming
        user_id = f"chatbot_{session_id}"
        
        # Prepare chatbot files with embedded API key and knowledge base
        zip_path = prepare_user_files(api_key, user_id, knowledge_base_content)
        
        if not os.path.exists(zip_path):
            return jsonify({'error': 'Failed to generate chatbot ZIP file.'}), 500

        # Send the ZIP file
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f'chatbot_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate chatbot: {str(e)}'}), 500


@app.route('/check_ready', methods=['GET'])
def check_ready():
    """
    Check if a knowledge base is ready for chatbot generation.
    """
    session_id = request.cookies.get('session_id')
    if session_id and session_id in user_knowledge_bases:
        return jsonify({
            'ready': True,
            'files_count': len(user_knowledge_bases[session_id].get('files', []))
        })
    return jsonify({'ready': False})


if __name__ == '__main__':
    app.run(debug=True)
