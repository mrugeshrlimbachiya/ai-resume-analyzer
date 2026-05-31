import os
import uuid
import json
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models.resume import Resume
from app.models.schemas import ResumeAnalysisResponse, ResumeUploadResponse, ErrorResponse
from app.utils.pdf_parser import PDFParser
from app.services.gemini_service import gemini_service

router = APIRouter(prefix="/api/v1/resume", tags=["Resume"])

MAX_FILE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post(
    "/analyze",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and analyze a resume PDF",
    description=(
        "Upload a PDF resume. The endpoint will extract the text, "
        "send it to Gemini 2.5 Flash, and return a full ATS analysis."
    ),
)
async def analyze_resume(
    file: UploadFile = File(..., description="PDF resume file"),
    db: AsyncSession = Depends(get_db),
):
    # ── 1. Validate file type ──────────────────────────────────────────────
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted. Please upload a .pdf file.",
        )

    # ── 2. Read file bytes & size check ───────────────────────────────────
    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds the {settings.MAX_FILE_SIZE_MB} MB limit.",
        )

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # ── 3. Validate it's actually a PDF ───────────────────────────────────
    if not PDFParser.validate_pdf(file_bytes):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File does not appear to be a valid PDF.",
        )

    # ── 4. Save to disk ───────────────────────────────────────────────────
    safe_filename = f"{uuid.uuid4().hex}.pdf"
    upload_path = Path(settings.UPLOAD_DIR) / safe_filename
    upload_path.write_bytes(file_bytes)

    # ── 5. Create DB record (status = pending) ────────────────────────────
    resume_record = Resume(
        filename=safe_filename,
        original_filename=file.filename,
        status="pending",
    )
    db.add(resume_record)
    await db.flush()  # get the auto-generated id
    resume_id = resume_record.id

    # ── 6. Extract text from PDF ──────────────────────────────────────────
    try:
        extracted_text, page_count = PDFParser.extract_text(str(upload_path))
    except (FileNotFoundError, ValueError) as e:
        resume_record.status = "failed"
        resume_record.error_message = str(e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"PDF text extraction failed: {str(e)}",
        )

    resume_record.extracted_text = extracted_text

    # ── 7. Analyze with Gemini ────────────────────────────────────────────
    try:
        analysis = await gemini_service.analyze_resume(extracted_text)
    except ValueError as e:
        resume_record.status = "failed"
        resume_record.error_message = str(e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI analysis parsing error: {str(e)}",
        )
    except Exception as e:
        resume_record.status = "failed"
        resume_record.error_message = str(e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI analysis failed: {str(e)}",
        )

    # ── 8. Persist analysis results ───────────────────────────────────────
    resume_record.ats_score = analysis["ats_score"]
    resume_record.strengths = json.dumps(analysis["strengths"])
    resume_record.weaknesses = json.dumps(analysis["weaknesses"])
    resume_record.missing_keywords = json.dumps(analysis["missing_keywords"])
    resume_record.interview_questions = json.dumps(analysis["interview_questions"])
    resume_record.raw_analysis = json.dumps(analysis)
    resume_record.status = "analyzed"

    # ── 9. Build response ─────────────────────────────────────────────────
    analysis_response = ResumeAnalysisResponse(
        id=resume_id,
        filename=file.filename,
        ats_score=analysis["ats_score"],
        strengths=analysis["strengths"],
        weaknesses=analysis["weaknesses"],
        missing_keywords=analysis["missing_keywords"],
        interview_questions=analysis["interview_questions"],
        status="analyzed",
        created_at=resume_record.created_at,
    )

    return ResumeUploadResponse(
        message="Resume analyzed successfully.",
        resume_id=resume_id,
        filename=file.filename,
        analysis=analysis_response,
    )


@router.get(
    "/{resume_id}",
    response_model=ResumeAnalysisResponse,
    summary="Retrieve a past analysis by resume ID",
)
async def get_resume_analysis(resume_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No resume found with id={resume_id}.",
        )

    if resume.status != "analyzed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Resume analysis status is '{resume.status}'. Analysis may have failed.",
        )

    return ResumeAnalysisResponse(
        id=resume.id,
        filename=resume.original_filename,
        ats_score=resume.ats_score,
        strengths=json.loads(resume.strengths),
        weaknesses=json.loads(resume.weaknesses),
        missing_keywords=json.loads(resume.missing_keywords),
        interview_questions=json.loads(resume.interview_questions),
        status=resume.status,
        created_at=resume.created_at,
    )


@router.get(
    "/",
    summary="List all analyzed resumes (IDs + filenames + scores)",
)
async def list_resumes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Resume.id, Resume.original_filename, Resume.ats_score, Resume.status, Resume.created_at)
        .order_by(Resume.created_at.desc())
        .limit(50)
    )
    rows = result.all()
    return {
        "total": len(rows),
        "resumes": [
            {
                "id": r.id,
                "filename": r.original_filename,
                "ats_score": r.ats_score,
                "status": r.status,
                "created_at": r.created_at,
            }
            for r in rows
        ],
    }
