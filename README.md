# 📄 Streamlit Resume Parser

This is a simple resume parser built with **Streamlit** that extracts structured information (name, contact, skills, experience, education, certifications) from uploaded resumes in PDF or DOCX format.

## 🚀 Features
- Upload resumes (PDF or DOCX)
- Extract:
  - Name
  - Email
  - Phone
  - Summary
  - Skills
  - Education
  - Experience
  - Certifications
- Download parsed result as JSON

## 🛠️ Requirements

Create a virtual environment and install dependencies:

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## ▶️ Run the app

```bash
streamlit run streamlit_resume_parser.py
```

## 🌐 Deploy on Streamlit Cloud

Push this project to GitHub, then go to [https://streamlit.io/cloud](https://streamlit.io/cloud), and deploy by selecting:
- File: `streamlit_resume_parser.py`
