# app/api/routes/cv.py
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from uuid import uuid4
import json
import os
from datetime import datetime

from app.core.azure_blob import upload_to_blob, get_blob_url
from app.models.cv import CVUploadResponse, AnalysisStatusResponse
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
        
        # Store analysis metadata (in a real app, this would go to a database)
        analysis_dir = "app/data/analyses"
        os.makedirs(analysis_dir, exist_ok=True)
        
        metadata = {
            "analysis_id": analysis_id,
            "name": name,
            "email": email,
            "target_role": target_role,
            "experience_level": experience_level,
            "original_filename": file.filename,
            "blob_name": blob_name,
            "status": "processing",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        with open(f"{analysis_dir}/{analysis_id}.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
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
        # In a real app, this would query a database
        analysis_file = f"app/data/analyses/{analysis_id}.json"
        
        if not os.path.exists(analysis_file):
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        with open(analysis_file, "r") as f:
            metadata = json.load(f)
        
        # Return status response
        return AnalysisStatusResponse(
            analysis_id=analysis_id,
            status=metadata.get("status", "processing"),
            progress=metadata.get("progress", 0.5),
            estimated_time_remaining=metadata.get("estimated_time_remaining", 15)
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analysis status: {str(e)}")