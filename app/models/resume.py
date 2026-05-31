from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    extracted_text = Column(Text, nullable=True)
    ats_score = Column(Float, nullable=True)
    strengths = Column(Text, nullable=True)       # JSON string
    weaknesses = Column(Text, nullable=True)      # JSON string
    missing_keywords = Column(Text, nullable=True) # JSON string
    interview_questions = Column(Text, nullable=True)  # JSON string
    raw_analysis = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending, analyzed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
