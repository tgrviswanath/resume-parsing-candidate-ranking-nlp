"""
Resume entity extractor.
- Name        : spaCy PERSON entity (first match)
- Email       : regex
- Phone       : regex
- LinkedIn    : regex
- GitHub      : regex
- Skills      : PhraseMatcher against 50+ skills vocabulary
- Education   : degree keywords + ORG entities near them
- Experience  : date-range regex sections
"""
import re
import spacy
from spacy.matcher import PhraseMatcher
from app.core.config import settings

_nlp = None
_matcher = None

SKILLS_DB = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "kotlin", "swift",
    "react", "angular", "vue", "node.js", "django", "flask", "fastapi", "spring boot",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "docker", "kubernetes", "aws", "azure", "gcp", "terraform", "ci/cd", "github actions",
    "machine learning", "deep learning", "nlp", "computer vision", "pytorch", "tensorflow",
    "scikit-learn", "pandas", "numpy", "spark", "kafka", "airflow",
    "rest api", "graphql", "microservices", "agile", "scrum", "git",
    "linux", "bash", "html", "css", "figma",
]

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\s\-().]{7,}\d)")
LINKEDIN_RE = re.compile(r"linkedin\.com/in/[\w\-]+", re.I)
GITHUB_RE = re.compile(r"github\.com/[\w\-]+", re.I)
DEGREE_RE = re.compile(
    r"\b(bachelor|master|phd|b\.?sc|m\.?sc|b\.?e|m\.?e|b\.?tech|m\.?tech|mba|doctorate)\b",
    re.I,
)
DATE_RANGE_RE = re.compile(
    r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|june|"
    r"july|august|september|october|november|december)[\s,]*\d{4}\s*[-–—to]+\s*"
    r"(present|current|now|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
    r"january|february|march|april|june|july|august|september|october|november|december"
    r"|[\d]{4})",
    re.I,
)


def _get_nlp_and_matcher():
    global _nlp, _matcher
    if _nlp is None:
        _nlp = spacy.load(settings.SPACY_MODEL)
        _matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")
        patterns = [_nlp.make_doc(s) for s in SKILLS_DB]
        _matcher.add("SKILLS", patterns)
    return _nlp, _matcher


def parse(text: str) -> dict:
    nlp, matcher = _get_nlp_and_matcher()
    doc = nlp(text)

    # Name — first PERSON entity
    name = next((e.text for e in doc.ents if e.label_ == "PERSON"), "")

    # Contact
    emails = EMAIL_RE.findall(text)
    phones = PHONE_RE.findall(text)
    linkedin = LINKEDIN_RE.findall(text)
    github = GITHUB_RE.findall(text)

    # Skills via PhraseMatcher (deduplicated, preserve order)
    matches = matcher(doc)
    seen, skills = set(), []
    for _, start, end in matches:
        skill = doc[start:end].text.lower()
        if skill not in seen:
            seen.add(skill)
            skills.append(skill)

    # Education — lines containing degree keywords
    education = []
    for line in text.splitlines():
        if DEGREE_RE.search(line):
            education.append(line.strip())

    # Experience — date ranges found in text
    experience = [m.group(0) for m in DATE_RANGE_RE.finditer(text)]

    return {
        "name": name,
        "email": emails[0] if emails else "",
        "phone": phones[0].strip() if phones else "",
        "linkedin": linkedin[0] if linkedin else "",
        "github": github[0] if github else "",
        "skills": skills,
        "education": education[:5],
        "experience_dates": experience[:10],
        "raw_text_length": len(text),
    }
