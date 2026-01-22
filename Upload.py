from flask import Flask, request, jsonify, render_template
from flask_pymongo import PyMongo 
import os
import requests
import io
import mimetypes

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/atherbot_db"
mongo = PyMongo(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'csv', 'xlsx', 'xls', 'docx'}

def allowed_file(filename):
    return '.' in filename and '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        files = request.files.getlist('databaseFile')
        url = request.form.get('databaseUrl')

        if not files and not url:
            return jsonify({'error': 'No files or URL provided'}), 400

        if files and url:
            return jsonify({'error': 'Please provide either files or a URL, not both.'}), 400

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
                        'original_filename': file.filename,
                    })

            return jsonify({'message': 'Files uploaded successfully', 'file_paths': file_paths}), 200

        elif url:
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()

                content_type = response.headers.get('content-type')
                extension = mimetypes.guess_extension(content_type)
                if extension not in ['.txt','.pdf','.csv','.xlsx','.xls','.docx']:
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

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)