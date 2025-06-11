import streamlit as st
import json
import re
import docx2txt
import PyPDF2
import spacy
import sqlite3
from datetime import datetime

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Database setup
conn = sqlite3.connect("resumes.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    phone TEXT,
    summary TEXT,
    skills TEXT,
    experience TEXT,
    education TEXT,
    certifications TEXT,
    created_at TEXT
)
""")
conn.commit()

# File extraction
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    return " ".join([page.extract_text() for page in reader.pages if page.extract_text()])

def extract_text_from_docx(file):
    return docx2txt.process(file)

# Field extractors
def extract_email(text):
    cleaned = re.sub(r'\s+', '', text.replace('\n', ' ').replace('\r', ' '))
    matches = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", cleaned)
    return matches[0] if matches else None

def extract_phone(text):
    text = text.replace('\n', ' ')
    match = re.search(r"(\+?\d[\d\s\-()]{9,})", text)
    return re.sub(r"[\s\-()]", "", match.group()) if match else None

def extract_summary(text):
    lines = re.split(r'\n|\r|\r\n', text)
    for i, line in enumerate(lines):
        if 'summary' in line.lower() or 'about' in line.lower():
            return lines[i+1].strip() if i+1 < len(lines) else line.strip()
    return ""

def extract_section(text, section_names, stop_names, max_lines=12):
    lines = re.split(r'\n|\r|\r\n', text)
    section_lines = []
    capture = False

    for i, raw in enumerate(lines):
        line = raw.strip().lower()
        if any(section in line for section in section_names):
            capture = True
            continue
        if capture:
            if any(stop in line for stop in stop_names):
                break
            if raw.strip():
                section_lines.append(raw.strip())
        if len(section_lines) >= max_lines:
            break

    return section_lines

def extract_skills(text):
    skill_lines = extract_section(text, ["skills", "technical skills"], ["experience", "education", "certification"])
    return sorted({s.strip("•- ") for line in skill_lines for s in re.split(r'[|,•]', line) if s.strip()})

def extract_experience(text):
    lines = extract_section(text, ["experience", "work history"], ["education", "certification", "projects"], 20)
    experience = []
    current = {}
    for line in lines:
        if "|" in line:
            current["company_role"] = line.strip()
        elif re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).*?\d{4}", line):
            current["duration"] = line.strip()
        if "company_role" in current and "duration" in current:
            experience.append(current)
            current = {}
    return experience

def extract_education(text):
    lines = extract_section(text, ["education", "academic background"], ["experience", "certification", "skills"])
    education = []
    for i in range(len(lines)):
        if re.search(r"(B\.?Tech|M\.?Tech|MBA|MSc|BSc|Bachelor|Master|PhD)", lines[i], re.IGNORECASE):
            degree = lines[i].strip()
            next_line = lines[i+1].strip() if i+1 < len(lines) else ""
            next_next = lines[i+2].strip() if i+2 < len(lines) else ""
            if re.search(r"\d{4}", next_line):
                institute, duration = "", next_line
            else:
                institute, duration = next_line, next_next if re.search(r"\d{4}", next_next) else ""
            education.append({
                "degree": degree,
                "institute": institute,
                "duration": duration
            })
    return education

def extract_certifications(text):
    return extract_section(text, ["certifications", "certification", "courses"], ["experience", "education"])

def save_to_db(data):
    c.execute("""
    INSERT INTO resumes (name, email, phone, summary, skills, experience, education, certifications, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["Name"], data["Email"], data["Phone"], data["Summary"],
        ", ".join(data["Skills"]),
        json.dumps(data["Experience"]),
        json.dumps(data["Education"]),
        json.dumps(data["Certifications"]),
        datetime.now().isoformat()
    ))
    conn.commit()

# Streamlit UI
st.set_page_config(page_title="📄 Resume Parser", layout="centered")
st.title("📄 Smart Resume Parser")

uploaded_file = st.file_uploader("📤 Upload your resume (PDF or DOCX)", type=["pdf", "docx"])

if uploaded_file:
    st.info("Parsing your resume...")

    text = extract_text_from_pdf(uploaded_file) if uploaded_file.name.endswith(".pdf") else extract_text_from_docx(uploaded_file)

    resume_data = {
        "Name": None,
        "Email": extract_email(text),
        "Phone": extract_phone(text),
        "Summary": extract_summary(text),
        "Skills": extract_skills(text),
        "Experience": extract_experience(text),
        "Education": extract_education(text),
        "Certifications": extract_certifications(text)
    }

    doc = nlp(text[:500])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            resume_data["Name"] = ent.text
            break

    save_to_db(resume_data)
    st.success("✅ Resume parsed and saved to database!")

    st.subheader("📋 Parsed Information")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**👤 Name:** {resume_data['Name']}")
        st.markdown(f"**✉️ Email:** {resume_data['Email']}")
        st.markdown(f"**📞 Phone:** {resume_data['Phone']}")
    with col2:
        st.markdown(f"**📝 Summary:** {resume_data['Summary']}")
        st.markdown(f"**🛠 Skills:** {', '.join(resume_data['Skills'])}")

    with st.expander("📌 Experience"):
        st.write(resume_data["Experience"])

    with st.expander("🎓 Education"):
        st.write(resume_data["Education"])

    with st.expander("🏅 Certifications"):
        st.write(resume_data["Certifications"])

    st.download_button(
        label="📥 Download JSON",
        data=json.dumps(resume_data, indent=2),
        file_name="parsed_resume.json",
        mime="application/json"
    )
