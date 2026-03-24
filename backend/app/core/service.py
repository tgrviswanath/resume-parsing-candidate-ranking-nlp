import httpx
from app.core.config import settings

NLP_URL = settings.NLP_SERVICE_URL


async def parse_resume(filename: str, content: bytes, content_type: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{NLP_URL}/api/v1/nlp/parse",
            files={"file": (filename, content, content_type)},
            timeout=60.0,
        )
        r.raise_for_status()
        return r.json()


async def rank_resumes(files: list[tuple], job_description: str) -> dict:
    """files: list of (filename, content, content_type)"""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{NLP_URL}/api/v1/nlp/rank",
            files=[("files", (fn, ct, ctype)) for fn, ct, ctype in files],
            data={"job_description": job_description},
            timeout=120.0,
        )
        r.raise_for_status()
        return r.json()
