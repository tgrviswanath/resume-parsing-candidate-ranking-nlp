"""
Candidate ranker.
- Embeds each resume's skills + education + experience text
- Embeds the job description
- Ranks by cosine similarity (sentence-transformers)
"""
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from app.core.config import settings

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBED_MODEL)
    return _model


def _resume_repr(parsed: dict) -> str:
    """Build a compact text representation of a parsed resume for embedding."""
    parts = []
    if parsed.get("skills"):
        parts.append("Skills: " + ", ".join(parsed["skills"]))
    if parsed.get("education"):
        parts.append("Education: " + " | ".join(parsed["education"]))
    if parsed.get("experience_dates"):
        parts.append("Experience: " + " | ".join(parsed["experience_dates"]))
    return " ".join(parts) if parts else "No structured content found"


def rank(candidates: list[dict], job_description: str) -> list[dict]:
    """
    candidates: list of {filename, parsed}
    Returns candidates sorted by match_score descending.
    """
    model = _get_model()
    jd_vec = model.encode([job_description], normalize_embeddings=True)

    results = []
    for c in candidates:
        resume_text = _resume_repr(c["parsed"])
        res_vec = model.encode([resume_text], normalize_embeddings=True)
        score = float(cosine_similarity(jd_vec, res_vec)[0][0])
        results.append({
            "filename": c["filename"],
            "parsed": c["parsed"],
            "match_score": round(score * 100, 2),   # 0-100 scale
            "resume_repr": resume_text,
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1
    return results
