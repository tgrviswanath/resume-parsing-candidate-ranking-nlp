from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

SAMPLE_RESUME = b"""
John Smith
john.smith@email.com  |  +1-555-123-4567
linkedin.com/in/johnsmith  |  github.com/johnsmith

SKILLS
Python, FastAPI, Docker, PostgreSQL, Machine Learning, NLP, scikit-learn, AWS

EDUCATION
Bachelor of Science in Computer Science, MIT, 2018

EXPERIENCE
Senior Developer  |  Jan 2020 - Present
Software Engineer  |  Jun 2018 - Dec 2019
"""


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_parse_txt():
    r = client.post(
        "/api/v1/nlp/parse",
        files={"file": ("resume.txt", SAMPLE_RESUME, "text/plain")},
    )
    assert r.status_code == 200
    data = r.json()
    assert "parsed" in data
    p = data["parsed"]
    assert "skills" in p
    assert "python" in p["skills"]
    assert p["email"] == "john.smith@email.com"
    assert "johnsmith" in p["linkedin"]
    assert "johnsmith" in p["github"]


def test_parse_unsupported():
    r = client.post(
        "/api/v1/nlp/parse",
        files={"file": ("resume.csv", b"a,b,c", "text/csv")},
    )
    assert r.status_code == 400


def test_rank_single():
    with patch("app.core.ranker.SentenceTransformer") as mock_st:
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.5] * 384]
        mock_st.return_value = mock_model
        r = client.post(
            "/api/v1/nlp/rank",
            files=[("files", ("resume.txt", SAMPLE_RESUME, "text/plain"))],
            data={"job_description": "Python developer with NLP and Docker experience"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert data["candidates"][0]["rank"] == 1
        assert "match_score" in data["candidates"][0]


def test_rank_empty_jd():
    r = client.post(
        "/api/v1/nlp/rank",
        files=[("files", ("resume.txt", SAMPLE_RESUME, "text/plain"))],
        data={"job_description": "   "},
    )
    assert r.status_code == 400
