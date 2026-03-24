# Project 13 - Resume Parsing + Candidate Ranking

Parse resumes (PDF/DOCX/TXT) and rank candidates against a job description using semantic similarity.

## Architecture

```
Frontend :3000  →  Backend :8000  →  NLP Service :8001
  React/MUI        FastAPI/httpx      spaCy + sentence-transformers
```

## What It Does

| Feature | Method | Tools |
|---|---|---|
| Text extraction | PDF/DOCX/TXT parsing | PyMuPDF, python-docx |
| Name extraction | spaCy PERSON NER | spaCy en_core_web_sm |
| Email / Phone | Regex | re |
| LinkedIn / GitHub | Regex | re |
| Skills detection | PhraseMatcher (50+ skills) | spaCy PhraseMatcher |
| Education | Degree keyword regex + ORG entities | spaCy + re |
| Experience | Date-range regex | re |
| Candidate ranking | Cosine similarity | sentence-transformers + scikit-learn |

## Local Run

```bash
# Terminal 1 - NLP Service
cd nlp-service && python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --reload --port 8001

# Terminal 2 - Backend
cd backend && python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 3 - Frontend
cd frontend && npm install && npm start
```

- NLP Service docs: http://localhost:8001/docs
- Backend docs: http://localhost:8000/docs
- UI: http://localhost:3000

## Docker

```bash
docker-compose up --build
```

## Dataset

Use any PDF/DOCX resumes — try Kaggle Resume Dataset or create sample `.txt` files.
