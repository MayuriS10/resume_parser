
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
    clean_text = text.replace('\n', ' ').replace('\r', ' ')
    clean_text = re.sub(r'\s+', '', clean_text)  # remove all whitespace
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", clean_text)
    return match.group() if match else None


def extract_phone(text):
    clean_text = text.replace('\n', ' ')
    match = re.search(r"(\+?\d[\d\s\-()]{9,})", clean_text)
    if match:
        number = match.group()
        number = re.sub(r"[\s\-()]", "", number)  # CORRECTED HERE
        return number
    return None



def extract_summary(text):
    # Normalize line breaks and spacing
    clean = text.replace('\n', ' ').replace('\r', ' ')
    clean = re.sub(r'-\s+', '', clean)  # remove hyphen line breaks
    clean = re.sub(r'\s+', ' ', clean)  # collapse whitespace
    clean = re.sub(r'[^\x00-\x7F]+', ' ', clean)  # remove weird chars
    
    # Try to locate "Summary" or "About" section
    match = re.search(r"(summary|about)[\s:\-]*([^.]{20,300})", clean, re.IGNORECASE)
    return match.group(2).strip() if match else clean[:300].strip()


def extract_skills(text):
    lines = text.split('\\n')
    skills = []
    skill_keywords = ["skills", "technical skills", "core skills"]
    stop_keywords = ["experience", "education", "certification", "projects"]

    for i, line in enumerate(lines):
        if any(k in line.lower() for k in skill_keywords):
            # Grab next 3–8 lines until next header or blank
            for j in range(i+1, min(i+8, len(lines))):
                next_line = lines[j].strip()
                if any(k in next_line.lower() for k in stop_keywords):
                    break
                if next_line:
                    skills.extend([s.strip("•- ") for s in re.split(r'[|,•]', next_line) if len(s.strip()) > 1])
            break

    return sorted(list(set(skills)))


def extract_experience(text):
    lines = text.split('\\n')
    experience = []
    current = {}

    for i, line in enumerate(lines):
        # Match job line with pipe or two capital words
        if "|" in line or re.match(r"[A-Z][A-Z\\s&]+", line.strip()):
            current["company_role"] = line.strip()
        
        # Match date format
        if re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).*\\d{4}", line):
            current["duration"] = line.strip()

        # If both are found, append and reset
        if "company_role" in current and "duration" in current:
            experience.append({
                "company_role": current["company_role"],
                "duration": current["duration"]
            })
            current = {}

    return experience

    
def extract_education(text):
    lines = text.split('\\n')
    education = []
    capture = False

    for i, line in enumerate(lines):
        lower = line.lower().strip()
        if "education" in lower or "academic" in lower:
            capture = True
            continue

        if capture:
            if any(stop in lower for stop in ["experience", "certification", "project", "skills"]):
                break  # stop capturing when next section starts

            if re.search(r"(B\\.?Tech|M\\.?Tech|MBA|MSc|BSc|Bachelor|Master|PhD)", line, re.IGNORECASE):
                degree = line.strip()
                institute = lines[i+1].strip() if i+1 < len(lines) else ""
                duration = lines[i+2].strip() if i+2 < len(lines) and re.search(r"\\d{4}", lines[i+2]) else ""
                education.append({
                    "degree": degree,
                    "institute": institute,
                    "duration": duration
                })

    return education



def extract_certifications(text):
    lines = text.split('\\n')
    certifications = []

    for i, line in enumerate(lines):
        if "certification" in line.lower() or "certifications" in line.lower() or "certified" in line.lower():
            # Get next 3-6 lines as possible certificates
            for j in range(1, 6):
                if i + j < len(lines):
                    candidate = lines[i + j].strip()
                    if len(candidate) > 6 and not re.match(r"^[-•\\s]*$", candidate):
                        certifications.append(candidate)
            break  # Only first block

    return certifications



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
