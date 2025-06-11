
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

# Initialize DB
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

# Extract functions
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    return " ".join([page.extract_text() for page in reader.pages if page.extract_text()])

def extract_text_from_docx(file):
    return docx2txt.process(file)

def extract_email(text):
    match = re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", text)
    return match.group() if match else None

def extract_phone(text):
    match = re.search(r"\+?\d[\d\s\-()]{9,}", text)
    return match.group().strip() if match else None

def extract_summary(text):
    match = re.search(r"(summary|about)[\s:\-]*([\s\S]{0,300})", text, re.IGNORECASE)
    return match.group(2).strip() if match else text.strip().split("\n")[0]

def extract_skills(text):
    skills_list = ["python", "sql", "excel", "machine learning", "data analysis", "communication", "deep learning", "flask", "streamlit"]
    return list({skill for skill in skills_list if skill.lower() in text.lower()})

def extract_experience(text):
    lines = text.split("\n")
    return [line.strip() for line in lines if re.search(r"(\b\d{4}\b)", line)]

def extract_education(text):
    lines = text.split("\n")
    return [line.strip() for line in lines if re.search(r"(B\.Tech|M\.Tech|BSc|MSc|MBA|Bachelor|Master|PhD)", line, re.IGNORECASE)]

def extract_certifications(text):
    return [line.strip() for line in text.split("\n") if "certificat" in line.lower() and len(line.strip()) > 10]

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

    if uploaded_file.name.endswith(".pdf"):
        text = extract_text_from_pdf(uploaded_file)
    else:
        text = extract_text_from_docx(uploaded_file)

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

    # Extract name using NLP
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
