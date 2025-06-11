# 📄 Streamlit Resume Parser with Database

A smart resume parser built with Streamlit that:
- Parses PDF/DOCX resumes
- Extracts structured data: Name, Email, Phone, Summary, Skills, etc.
- Saves parsed data into a local SQLite database
- Offers polished UI and downloadable JSON output

## 🔧 Setup Instructions
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
streamlit run streamlit_resume_parser.py
```
