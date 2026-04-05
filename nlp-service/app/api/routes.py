import asyncio
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List
from app.core.loader import extract_text
from app.core.extractor import parse
from app.core.ranker import rank

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTS = {"pdf", "docx", "doc", "txt"}

router = APIRouter(prefix="/api/v1/nlp", tags=["resume"])


def _validate_file(filename: str, content: bytes):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max 10MB")


@router.post("/parse")
async def parse_resume(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    _validate_file(file.filename, content)
    try:
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, extract_text, file.filename, content)
        result = await loop.run_in_executor(None, parse, text)
        return {"filename": file.filename, "parsed": result}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rank")
async def rank_resumes(files: List[UploadFile] = File(...), job_description: str = Form(...)):
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty")
    if len(files) < 1:
        raise HTTPException(status_code=400, detail="Upload at least one resume")
    try:
        loop = asyncio.get_running_loop()
        candidates = []
        for f in files:
            content = await f.read()
            _validate_file(f.filename, content)
            text = await loop.run_in_executor(None, extract_text, f.filename, content)
            parsed = await loop.run_in_executor(None, parse, text)
            candidates.append({"filename": f.filename, "parsed": parsed})
        ranked = await loop.run_in_executor(None, rank, candidates, job_description)
        return {"job_description": job_description, "total": len(ranked), "candidates": ranked}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
