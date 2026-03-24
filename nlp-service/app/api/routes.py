from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List
from app.core.loader import extract_text
from app.core.extractor import parse
from app.core.ranker import rank

router = APIRouter(prefix="/api/v1/nlp", tags=["resume"])

ALLOWED = {"pdf", "docx", "doc", "txt"}


def _validate_file(filename: str):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")


@router.post("/parse")
async def parse_resume(file: UploadFile = File(...)):
    _validate_file(file.filename)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    text = extract_text(file.filename, content)
    return {"filename": file.filename, "parsed": parse(text)}


@router.post("/rank")
async def rank_resumes(
    files: List[UploadFile] = File(...),
    job_description: str = Form(...),
):
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty")
    if len(files) < 1:
        raise HTTPException(status_code=400, detail="Upload at least one resume")

    candidates = []
    for f in files:
        _validate_file(f.filename)
        content = await f.read()
        text = extract_text(f.filename, content)
        candidates.append({"filename": f.filename, "parsed": parse(text)})

    ranked = rank(candidates, job_description)
    return {"job_description": job_description, "total": len(ranked), "candidates": ranked}
