import os
import fitz  # PyMuPDF
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import sqlite3
from flask import send_from_directory

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
ALLOWED_EXTENSIONS = {'pdf'}

# Create uploads folder if not exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_info(text):
    text_lower = text.lower()
    info = {}

    # Extract name from the first few lines (ignoring generic headers)
    lines = text.strip().split('\n')
    for line in lines[:5]:
        if line.strip() and all(kw not in line.lower() for kw in ['resume', 'cv', 'curriculum', 'email', 'phone']):
            info['name'] = line.strip()
            break
    else:
        info['name'] = "Unknown"

    # Extract academic score: CGPA ≥ 9.0 or Percentage ≥ 90
    import re
    cgpa_match = re.search(r'cgpa[:\s]*([0-9.]+)', text_lower)
    percent_match = re.search(r'(\d{2,3})\s*%', text_lower)

    if cgpa_match and float(cgpa_match.group(1)) >= 9.0:
        info['score'] = f"{cgpa_match.group(1)} CGPA"
    elif percent_match and int(percent_match.group(1)) >= 90:
        info['score'] = f"{percent_match.group(1)}%"
    else:
        return None  # Does not meet score requirement

    # Data Analyst-specific skills
    data_analyst_skills = [
        'excel', 'sql', 'tableau', 'power bi', 'python', 'r', 'data visualization',
        'statistics', 'machine learning', 'data analysis', 'pandas', 'numpy',
        'matplotlib', 'seaborn', 'dash', 'regression', 'predictive modeling',
        'business intelligence', 'data mining', 'data wrangling'
    ]

    found_skills = []
    for skill in data_analyst_skills:
        if skill in text_lower:
            found_skills.append(skill.title())

    if len(found_skills) < 2:
        return None  # Not enough relevant skills

    info['skills'] = ", ".join(found_skills)
    info['branch'] = "Data Analyst"
    info['institute'] = "Unknown"  # Optional: add logic if needed

    return info




# ✅ Add this function at the top level (not inside a route)
def insert_resume(filename, category, score, branch, skills):
    conn = sqlite3.connect('resumes.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO resumes (filename, category, score, branch, skills)
        VALUES (?, ?, ?, ?, ?)
    ''', (filename, category, score, branch, skills))
    conn.commit()
    conn.close()

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
            info = extract_info(text)

            if info:
                # Save to database
                insert_resume(filename, info['institute'], info['score'], info['branch'], info['skills'])

                # Categorize for template
                if info['institute'] == 'IIT':
                    iit_list.append(info)
                elif info['institute'] == 'NIT':
                    nit_list.append(info)
                else:
                    other_list.append(info)

    return render_template('result.html', iits=iit_list, nits=nit_list, others=other_list)

# Add this route for Data Analyst filtering in app.py
@app.route('/evaluate_upload', methods=['GET', 'POST'])
def evaluate_upload():
    if request.method == 'POST':
        files = request.files.getlist('resumes')
        matched_candidates = []

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                text = extract_text_from_pdf(filepath)
                info = extract_info_for_analyst(text)

                if info:
                    matched_candidates.append(info)

        return render_template('evaluate_result.html', candidates=matched_candidates)

    return render_template('evaluate_upload.html')

# New extract_info_for_analyst function for JD-based filtering
def extract_info_for_analyst(text):
    text_lower = text.lower()
    info = {}

    # Extract name
    lines = text.strip().split('\n')
    for line in lines[:5]:
        if line.strip() and all(kw not in line.lower() for kw in ['resume', 'cv', 'curriculum', 'email', 'phone']):
            info['name'] = line.strip()
            break
    else:
        info['name'] = "Unknown"

    # Score
    import re
    cgpa_match = re.search(r'cgpa[:\s]*([0-9.]+)', text_lower)
    percent_match = re.search(r'(\d{2,})\s*%', text_lower)

    if cgpa_match and float(cgpa_match.group(1)) >= 9:
        info['score'] = f"{cgpa_match.group(1)} CGPA"
    elif percent_match and int(percent_match.group(1)) >= 90:
        info['score'] = f"{percent_match.group(1)}%"
    else:
        return None

    # Skills required for data analyst
    required_skills = ['sql', 'excel', 'python', 'tableau', 'power bi', 'statistics', 'data analysis', 'analytics']
    found_skills = [skill for skill in required_skills if skill in text_lower]

    if not found_skills:
        return None

    info['skills'] = ", ".join(found_skills)
    return info


@app.route('/history')
def history():
    conn = sqlite3.connect('resumes.db')
    c = conn.cursor()
    c.execute('SELECT name, filename, category, score, branch, skills, upload_time FROM resumes ORDER BY upload_time DESC')
    resumes = c.fetchall()
    conn.close()
    return render_template('history.html', resumes=resumes)



@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
