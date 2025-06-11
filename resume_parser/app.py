from flask import Flask, request, jsonify, send_from_directory
import docx2txt
import PyPDF2
import os
import re
import spacy
import uuid
import json
from werkzeug.utils import secure_filename

nlp = spacy.load("en_core_web_sm")

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def extract_text_from_docx(path):
    return docx2txt.process(path)

def extract_text_from_pdf(path):
    text = ""
    with open(path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_email(text):
    match = re.search(r'[\w\.-]+@[\w\.-]+', text)
    return match.group(0) if match else ""

def extract_phone(text):
    match = re.search(r'\+?\d[\d\s\-]{8,}', text)
    return match.group(0).strip() if match else ""

def extract_name(text):
    doc = nlp(text[:500])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return ""

def extract_skills(text):
    skills_list = ["Python", "SQL", "R", "Power BI", "Tableau", "Machine Learning", "Excel", "Deep Learning"]
    found = [skill for skill in skills_list if skill.lower() in text.lower()]
    return list(set(found))

def extract_experience(text):
    experience = []
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if re.search(r"(experience|work history)", line, re.IGNORECASE):
            for j in range(i+1, min(i+10, len(lines))):
                if re.search(r"\bat\b|\bfor\b|\bfrom\b.*\bto\b", lines[j], re.IGNORECASE):
                    experience.append(lines[j].strip())
    return experience

def extract_education(text):
    education = []
    lines = text.split('\n')
    keywords = ["bachelor", "master", "b.tech", "m.tech", "mba", "bsc", "msc", "phd", "degree", "university", "college"]
    for line in lines:
        if any(keyword in line.lower() for keyword in keywords):
            education.append(line.strip())
    return education

def extract_certifications(text):
    cert_keywords = ["certified", "certificate", "certification"]
    certifications = []
    for line in text.split('\n'):
        if any(keyword in line.lower() for keyword in cert_keywords):
            certifications.append(line.strip())
    return certifications

@app.route("/upload", methods=["POST"])
def upload_resume():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif filename.endswith(".docx"):
        text = extract_text_from_docx(file_path)
    else:
        return jsonify({"error": "Unsupported file format"}), 400

    result = {
        "name": extract_name(text),
        "contact": {
            "email": extract_email(text),
            "phone": extract_phone(text)
        },
        "summary": text[:300],
        "skills": extract_skills(text),
        "experience": extract_experience(text),
        "education": extract_education(text),
        "certifications": extract_certifications(text)
    }

    json_id = str(uuid.uuid4())
    json_filename = f"{json_id}.json"
    json_path = os.path.join(app.config["UPLOAD_FOLDER"], json_filename)
    with open(json_path, 'w') as f:
        json.dump(result, f, indent=4)

    return jsonify({
        "data": result,
        "download_url": f"/download/{json_filename}"
    })

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
