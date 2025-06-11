# 📄 Smart Resume Parser with Section-based Extraction

This Streamlit app extracts structured resume data from:
- 📌 Skills (under 'Skills' section only)
- 📌 Experience (under 'Experience' section)
- 📌 Education (under 'Education' section)
- 📌 Certifications (under 'Certifications' section)

Also includes:
- Email and phone cleanup
- SQLite DB storage
- JSON download

## 🚀 To Run
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
streamlit run streamlit_resume_parser.py
```
