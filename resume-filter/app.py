import os
import fitz  # PyMuPDF
import re
import sqlite3
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'uploads/'
ALLOWED_EXTENSIONS = {'pdf'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Predefined skills for job roles
ROLE_SKILLS = {
    'data analyst': [
        'excel', 'sql', 'tableau', 'power bi', 'python', 'r', 'data visualization',
        'statistics', 'machine learning', 'data analysis', 'pandas', 'numpy',
        'matplotlib', 'seaborn', 'dash', 'regression', 'predictive modeling',
        'business intelligence', 'data mining', 'data wrangling'
    ],
    'python developer': [
        'python', 'flask', 'django', 'pandas', 'numpy', 'sqlalchemy',
        'rest api', 'oop', 'unit testing', 'json', 'regex', 'git'
    ],
    'front-end developer': [
        'html', 'css', 'javascript', 'react', 'angular', 'vue', 'bootstrap',
        'jquery', 'responsive design', 'figma'
    ],
    'back-end developer': [
        'node.js', 'express', 'django', 'flask', 'sql', 'mongodb', 'rest api',
        'authentication', 'jwt', 'mvc', 'python', 'java'
    ]
}

# --- Helpers ---

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_candidate_info(text):
    text_lower = text.lower()
    name = "Unknown"
    for line in text.strip().split('\n')[:5]:
        if line.strip() and all(x not in line.lower() for x in ['resume', 'cv', 'email', 'phone']):
            name = line.strip()
            break

    institute = "Other"
    if re.search(r'\b(iit|indian institute of technology)\b', text_lower):
        institute = "IIT"
    elif re.search(r'\b(nit|national institute of technology)\b', text_lower):
        institute = "NIT"

    cgpa_match = re.search(r'cgpa[:\s]*([0-9.]+)', text_lower)
    percent_match = re.search(r'(\d{2,3})\s*%', text_lower)
    score = "N/A"
    if cgpa_match:
        score = f"{cgpa_match.group(1)} CGPA"
    elif percent_match:
        score = f"{percent_match.group(1)}%"

    return {'name': name, 'institute': institute, 'score': score}

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/filter', methods=['POST'])
def filter_resumes():
    files = request.files.getlist('resumes')
    iit_list, nit_list, other_list = [], [], []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            text = extract_text_from_pdf(filepath)
            info = extract_candidate_info(text)

            candidate = {
                'name': info['name'],
                'score': info['score'],
                'filename': filename
            }

            if info['institute'] == 'IIT':
                iit_list.append(candidate)
            elif info['institute'] == 'NIT':
                nit_list.append(candidate)
            else:
                other_list.append(candidate)

    return render_template('result.html', iits=iit_list, nits=nit_list, others=other_list)

@app.route('/match_form')
def match_form():
    return render_template('match_form.html')

@app.route('/match_upload', methods=['POST'])
def match_upload():
    job_title = request.form.get('job_title', '').lower()
    custom_skills = request.form.get('skills', '')
    required_skills = [s.strip().lower() for s in custom_skills.split(',') if s.strip()]

    # Append predefined skills if job title matches known roles
    required_skills += ROLE_SKILLS.get(job_title, [])

    session['job_title'] = job_title
    session['required_skills'] = required_skills

    files = request.files.getlist('resumes')
    matched_candidates = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            text = extract_text_from_pdf(filepath)
            text_lower = text.lower()
            name = extract_candidate_info(text)['name']

            matched_skills = [skill for skill in required_skills if skill in text_lower]
            match_percentage = round(len(matched_skills) / len(required_skills) * 100, 2) if required_skills else 0

            if match_percentage > 0:
                matched_candidates.append({
                    'name': name,
                    'matched_skills': ", ".join(matched_skills),
                    'match_percentage': match_percentage,
                    'filename': filename
                })

    return render_template('match_result.html', candidates=matched_candidates)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/history')
def history():
    conn = sqlite3.connect('resumes.db')
    c = conn.cursor()
    c.execute('SELECT name, filename, category, score, branch, skills, upload_time FROM resumes ORDER BY upload_time DESC')
    resumes = c.fetchall()
    conn.close()
    return render_template('history.html', resumes=resumes)

if __name__ == '__main__':
    app.run(debug=True)
