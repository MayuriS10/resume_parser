
import streamlit as st
import json
import os
import re
import docx2txt
import PyPDF2
import spacy

nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(file):
    return docx2txt.process(file)

def extract_resume_data(text):
    data = {}

    # Name (first entity of type PERSON)
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            data["Name"] = ent.text
            break

    # Email
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    data["Email"] = email.group() if email else None

    # Phone
    phone = re.search(r"\+?\d[\d\s\-()]{7,}\d", text)
    data["Phone"] = phone.group() if phone else None

    # Summary: First 3 lines
    summary_lines = text.strip().split("\n")[:3]
    data["Summary"] = " ".join(summary_lines)

    # Skills
    skills_list = ["python", "sql", "excel", "machine learning", "data analysis", "communication", "deep learning", "flask", "streamlit"]
    found_skills = [skill for skill in skills_list if skill.lower() in text.lower()]
    data["Skills"] = found_skills

    # Experience, Education, Certifications (basic placeholders)
    data["Experience"] = re.findall(r"(\b\d{4}\b).*?(?=\n)", text)
    data["Education"] = re.findall(r"(B\.Tech|M\.Tech|BSc|MSc|MBA|Bachelor|Master).*", text, re.I)
    data["Certifications"] = re.findall(r"Certified.*|Certification.*", text, re.I)

    return data

st.title("📄 Resume Parser (Streamlit Edition)")

uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])

if uploaded_file is not None:
    if uploaded_file.name.endswith(".pdf"):
        text = extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".docx"):
        text = extract_text_from_docx(uploaded_file)
    else:
        st.error("Unsupported file format.")
        st.stop()

    st.success("✅ File uploaded and processed.")
    resume_data = extract_resume_data(text)
    st.subheader("📋 Extracted Resume Data")
    st.json(resume_data)

    # Download button
    json_data = json.dumps(resume_data, indent=2)
    st.download_button("📥 Download JSON", data=json_data, file_name="parsed_resume.json", mime="application/json")
