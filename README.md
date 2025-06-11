# Resume Parser API

This is a simple Flask-based API for parsing resumes (PDF/DOCX) and extracting structured data such as:

- Name
- Contact Info (Email & Phone)
- Summary
- Skills
- Experience
- Education
- Certifications

## Features

- Upload resume via form or API
- Parse and extract key sections using basic NLP and regex
- Download structured JSON output

## Setup Instructions

1. Clone the repository
2. Install dependencies:

```bash
pip install flask python-docx PyPDF2 spacy
python -m spacy download en_core_web_sm
```

3. Run the Flask server:

```bash
python app.py
```

4. Open `index.html` in browser to upload a resume.

## Folder Structure

- `app.py` – Main backend script
- `uploads/` – Folder to save resumes and output JSONs
- `templates/index.html` – Simple frontend for uploading

## License

MIT
