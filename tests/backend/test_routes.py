from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app

client = TestClient(app)

MOCK_PARSE = {
    "filename": "resume.txt",
    "parsed": {
        "name": "John Smith", "email": "john@email.com", "phone": "+1-555-123",
        "linkedin": "linkedin.com/in/johnsmith", "github": "github.com/johnsmith",
        "skills": ["python", "docker", "nlp"], "education": ["BSc Computer Science"],
        "experience_dates": ["Jan 2020 - Present"], "raw_text_length": 300,
    },
}

MOCK_RANK = {
    "job_description": "Python developer",
    "total": 1,
    "candidates": [{**MOCK_PARSE, "match_score": 72.5, "rank": 1, "resume_repr": "Skills: python"}],
}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200


@patch("app.core.service.parse_resume", new_callable=AsyncMock, return_value=MOCK_PARSE)
def test_parse_endpoint(mock_parse):
    r = client.post(
        "/api/v1/parse",
        files={"file": ("resume.txt", b"John Smith python developer", "text/plain")},
    )
    assert r.status_code == 200
    assert r.json()["parsed"]["name"] == "John Smith"


@patch("app.core.service.rank_resumes", new_callable=AsyncMock, return_value=MOCK_RANK)
def test_rank_endpoint(mock_rank):
    r = client.post(
        "/api/v1/rank",
        files=[("files", ("resume.txt", b"John Smith python developer", "text/plain"))],
        data={"job_description": "Python developer"},
    )
    assert r.status_code == 200
    assert r.json()["total"] == 1
    assert r.json()["candidates"][0]["rank"] == 1
