from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ResumeAnalysisResponse(BaseModel):
    id: int
    filename: str
    ats_score: float = Field(..., ge=0, le=100, description="ATS compatibility score out of 100")
    strengths: List[str] = Field(..., description="List of resume strengths")
    weaknesses: List[str] = Field(..., description="List of resume weaknesses")
    missing_keywords: List[str] = Field(..., description="Important keywords missing from the resume")
    interview_questions: List[str] = Field(..., description="Likely interview questions based on the resume")
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResumeUploadResponse(BaseModel):
    message: str
    resume_id: int
    filename: str
    analysis: ResumeAnalysisResponse


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str = "1.0.0"
