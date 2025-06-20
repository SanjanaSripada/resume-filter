# PyAutomateAI - Intelligent Resume Analyzer & Job Role Filter

**PyAutomateAI** is an AI-powered application designed to automate and simplify the resume screening and candidate shortlisting process for hiring managers and recruiters.

## Features

- Upload up to 10 resumes (PDF format) at once
- Automatically extract and analyze candidate details
- Filter candidates based on:
  - Institute (IIT, NIT, or Others)
  - Job role title
  - Required skill set
- View candidate suitability score in a structured table
- Get a summarized view of:
  - Name
  - Skills
  - Branch of study
  - Match percentage
- Download matched resumes directly from the dashboard

## Technologies Used

- **Python**
- **FastAPI** - Backend API framework
- **SQLite3** - Lightweight database
- **Jinja2** - Templating engine
- **PDFMiner / PyMuPDF** - For resume text extraction
- **Rule-based scoring algorithm** - To rank resumes
- **HTML/CSS** - For responsive UI

1. Install dependencies
Make sure you have Python 3.9+ and pip installed.
pip install -r requirements.txt

2. Access the app
Open your browser and go to:
http://127.0.0.1:8000

