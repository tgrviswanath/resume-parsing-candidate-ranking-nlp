from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List
from app.core.service import parse_resume, rank_resumes
import httpx

router = APIRouter(prefix="/api/v1", tags=["resume"])


def _handle(e: Exception):
    if isinstance(e, httpx.ConnectError):
        raise HTTPException(status_code=503, detail="NLP service unavailable")
    if isinstance(e, httpx.HTTPStatusError):
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse")
async def parse(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return await parse_resume(file.filename, content, file.content_type or "application/octet-stream")
    except Exception as e:
        _handle(e)


@router.post("/rank")
async def rank(
    files: List[UploadFile] = File(...),
    job_description: str = Form(...),
):
    try:
        file_tuples = []
        for f in files:
            content = await f.read()
            file_tuples.append((f.filename, content, f.content_type or "application/octet-stream"))
        return await rank_resumes(file_tuples, job_description)
    except Exception as e:
        _handle(e)
