# app/models/cv.py
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional
from datetime import datetime

class CVUploadResponse(BaseModel):
    """Response model for CV upload endpoint"""
    analysis_id: str
    status: str
    estimated_time_seconds: int

class AnalysisStatusResponse(BaseModel):
    """Response model for analysis status endpoint"""
    analysis_id: str
    status: str
    progress: float
    estimated_time_remaining: int

class AnalysisCategory(BaseModel):
    """Model for an analysis category with score and feedback"""
    name: str
    score: int
    feedback: str
    suggestions: List[str]

class KeywordAnalysis(BaseModel):
    """Model for keyword analysis"""
    present: List[str]
    missing: List[str]
    recommended: List[str]

class MatrixAlignment(BaseModel):
    """Model for competency matrix alignment"""
    current_level: str
    target_level: str
    gap_areas: List[str]

class AnalysisResponse(BaseModel):
    """Complete analysis response model"""
    analysis_id: str
    overall_score: int
    categories: List[AnalysisCategory]
    keyword_analysis: KeywordAnalysis
    matrix_alignment: MatrixAlignment
    summary: str
    completed_at: str

class AnalysisSummary(BaseModel):
    """Summary model for listing analyses"""
    analysis_id: str
    name: str
    email: str
    target_role: str
    experience_level: str
    status: str
    created_at: str