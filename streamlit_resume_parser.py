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

# Setup SQLite DB
conn = sqlite3.connect("resumes.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    phone TEXT,
    skills TEXT,
    experience TEXT,
    education TEXT,
    certifications TEXT,
    created_at TEXT
)
""")
conn.commit()

# Extract text
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    return " ".join([page.extract_text() for page in reader.pages if page.extract_text()])

def extract_text_from_docx(file):
    return docx2txt.process(file)

# Helpers
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
    
def extract_email(text):
    lines = re.split(r'\n|\r|\r\n', text)
    for line in lines:
        line = line.strip()
        match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", line)
        if match:
            return match.group()
    return None


def extract_phone(text):
    text = text.replace('\n', ' ')
    match = re.search(r"(\+?\d[\d\s\-()]{9,})", text)
    return re.sub(r"[\s\-()]", "", match.group()) if match else None

    
def extract_skills(text):
    skill_lines = extract_section(
        text,
        section_names=["skills", "programming", "technology"],
        stop_names=["experience", "education", "certification", "projects"],
        max_lines=20
    )
    skills = []
    for line in skill_lines:
        # Remove time durations like '3+ years:', '1 year:', etc.
        if re.search(r"\d+\s*\+?\s*(year|yr|yrs)", line.lower()):
            continue
        parts = re.split(r"[•|,;–\-•\n\t]", line)
        for part in parts:
            part = part.strip()
            if len(part) > 1 and not re.match(r"\d+\+?", part):
                skills.append(part)
    return sorted(set(skills))



def extract_experience(text):
    lines = extract_section(text, ["experience", "work history"], ["education", "certification", "projects"], max_lines=25)
    experience = []
    current = {}

    for i in range(len(lines) - 1):
        line = lines[i].strip()
        next_line = lines[i + 1].strip()

        if "|" in line and re.search(r"\d{4}", next_line):
            current = {
                "company_role": line,
                "duration": next_line
            }
            experience.append(current)
            current = {}

    return experience


def extract_education(text):
    lines = extract_section(text, ["education"], ["experience", "skills", "certification"], max_lines=15)

    # Join broken lines like "INSTI" and "TUTE." → "INSTI TUTE."
    cleaned_lines = []
    i = 0
    while i < len(lines):
        if i+1 < len(lines) and not re.search(r"(Master|Bachelor|MBA|B\.?Tech|M\.?Tech|PhD|MSc|BSc)", lines[i], re.IGNORECASE):
            merged = lines[i].strip() + " " + lines[i+1].strip()
            cleaned_lines.append(merged)
            i += 2
        else:
            cleaned_lines.append(lines[i].strip())
            i += 1

    education = []
    for i in range(len(cleaned_lines) - 2):
        if re.search(r"(Master|Bachelor|MBA|B\.?Tech|M\.?Tech|PhD|MSc|BSc)", cleaned_lines[i+1], re.IGNORECASE):
            education.append({
                "degree": cleaned_lines[i+1],
                "institute": cleaned_lines[i],
                "duration": cleaned_lines[i+2] if re.search(r"\d{4}", cleaned_lines[i+2]) else ""
            })
    return education



def extract_certifications(text):
    return extract_section(text, ["certifications", "certification", "courses"], ["experience", "education", "projects"])

def save_to_db(data):
    c.execute("""
    INSERT INTO resumes (name, email, phone, skills, experience, education, certifications, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["Name"], data["Email"], data["Phone"],
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
        st.markdown(f"**🛠 Skills:** {', '.join(resume_data['Skills'])}")

    with st.expander("📌 Experience"):
        st.json(resume_data["Experience"])

    with st.expander("🎓 Education"):
        st.json(resume_data["Education"])

    with st.expander("🏅 Certifications"):
        st.write(resume_data["Certifications"])

    st.download_button(
        label="📥 Download JSON",
        data=json.dumps(resume_data, indent=2),
        file_name="parsed_resume.json",
        mime="application/json"
    )
