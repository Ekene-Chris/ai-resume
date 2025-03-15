# app/api/routes/cv.py
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks, Depends, Response
from fastapi.responses import JSONResponse
from typing import Optional, List
from uuid import uuid4
import json
import os
from datetime import datetime

from app.core.azure_blob import upload_to_blob, get_blob_url
from app.core.cosmos_db import cosmos_service
from app.models.cv import CVUploadResponse, AnalysisStatusResponse, AnalysisResponse, AnalysisSummary
from app.services.cv_analysis import analyze_cv_background

router = APIRouter()

@router.post("/upload", response_model=CVUploadResponse)
async def upload_cv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: str = Form(...),
    email: str = Form(...),
    target_role: str = Form(...),
    experience_level: str = Form(...)
):
    """
    Upload a CV/resume for analysis.
    
    This endpoint:
    1. Accepts the uploaded file and user information
    2. Stores the file in Azure Blob Storage
    3. Creates a unique analysis ID
    4. Starts a background task to analyze the CV
    5. Returns the analysis ID and status
    """
    try:
        # Validate the file
        valid_extensions = ['.pdf', '.doc', '.docx']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in valid_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file format. Supported formats: {', '.join(valid_extensions)}"
            )
        
        # Upload file to Azure Blob Storage
        blob_name = await upload_to_blob(file)
        
        # Generate unique analysis ID
        analysis_id = str(uuid4())
        
        # Store analysis metadata in Cosmos DB
        metadata = {
            "id": analysis_id,  # Cosmos DB requires an 'id' field
            "analysis_id": analysis_id,
            "name": name,
            "email": email,
            "target_role": target_role,
            "experience_level": experience_level,
            "original_filename": file.filename,
            "blob_name": blob_name,
            "status": "processing",
            "progress": 0.1,
            "estimated_time_remaining": 30,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await cosmos_service.create_analysis_record(metadata)
        
        # Start background analysis task
        background_tasks.add_task(
            analyze_cv_background,
            analysis_id=analysis_id,
            blob_name=blob_name,
            name=name,
            email=email,
            target_role=target_role,
            experience_level=experience_level
        )
        
        # Return response
        return CVUploadResponse(
            analysis_id=analysis_id,
            status="processing",
            estimated_time_seconds=30
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in CV upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: str):
    """
    Get the status of a CV analysis.
    
    Args:
        analysis_id: The unique ID of the analysis
        
    Returns:
        The current status of the analysis
    """
    try:
        # Get the analysis record from Cosmos DB
        analysis_record = await cosmos_service.get_analysis_record(analysis_id)
        
        if not analysis_record:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Return status response
        return AnalysisStatusResponse(
            analysis_id=analysis_id,
            status=analysis_record.get("status", "processing"),
            progress=analysis_record.get("progress", 0.5),
            estimated_time_remaining=analysis_record.get("estimated_time_remaining", 15)
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analysis status: {str(e)}")

@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_results(analysis_id: str):
    """
    Get the complete results of a CV analysis.
    
    Args:
        analysis_id: The unique ID of the analysis
        
    Returns:
        The complete analysis results
    """
    try:
        # Get the analysis record from Cosmos DB
        analysis_record = await cosmos_service.get_analysis_record(analysis_id)
        
        if not analysis_record:
            raise HTTPException(status_code=404, detail="Analysis not found")
            
        if analysis_record.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Analysis not yet completed")
            
        # Return the complete analysis response
        results = analysis_record.get("results", {})
        return AnalysisResponse(
            analysis_id=analysis_id,
            overall_score=results.get("overall_score", 0),
            categories=results.get("categories", []),
            keyword_analysis=results.get("keyword_analysis", {}),
            matrix_alignment=results.get("matrix_alignment", {}),
            summary=results.get("summary", ""),
            completed_at=analysis_record.get("completed_at", "")
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analysis results: {str(e)}")

@router.get("/", response_model=List[AnalysisSummary])
async def list_analyses():
    """
    List all CV analyses.
    
    Returns:
        A list of all analyses with basic information
    """
    try:
        # Query to get just the necessary fields
        query = """
        SELECT 
            c.analysis_id, 
            c.name, 
            c.email, 
            c.target_role, 
            c.experience_level,
            c.status,
            c.created_at
        FROM c
        ORDER BY c.created_at DESC
        """
        
        analyses = await cosmos_service.list_analyses(query)
        
        return [
            AnalysisSummary(
                analysis_id=item["analysis_id"],
                name=item["name"],
                email=item["email"],
                target_role=item["target_role"],
                experience_level=item["experience_level"],
                status=item["status"],
                created_at=item["created_at"]
            )
            for item in analyses
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing analyses: {str(e)}")

@router.get("/{analysis_id}/pdf", response_class=Response)
async def get_analysis_pdf(analysis_id: str):
    """
    Get the CV analysis as a downloadable PDF report.
    
    Args:
        analysis_id: The unique ID of the analysis
        
    Returns:
        PDF report as a downloadable file
    """
    try:
        # Get the analysis record from Cosmos DB
        analysis_record = await cosmos_service.get_analysis_record(analysis_id)
        
        if not analysis_record:
            raise HTTPException(status_code=404, detail="Analysis not found")
            
        if analysis_record.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Analysis not yet completed")
            
        # Get necessary information
        results = analysis_record.get("results", {})
        name = analysis_record.get("name", "")
        email = analysis_record.get("email", "")
        target_role = analysis_record.get("target_role", "")
        
        # Import PDF generator
        from app.services.pdf_generator import pdf_generator
        
        # Generate PDF report
        pdf_report = pdf_generator.generate_analysis_report(
            analysis_data=results,
            name=name,
            email=email,
            target_role=target_role
        )
        
        # Create response with PDF
        pdf_content = pdf_report.read()
        
        filename = f"resume_analysis_{analysis_id}.pdf"
        
        # Create response with PDF content
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException as e:
        raise e
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"PDF generation not available: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF report: {str(e)}")