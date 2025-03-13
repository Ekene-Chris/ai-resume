# app/services/cv_analysis.py
from app.core.azure_blob import get_blob_url
from app.core.cosmos_db import cosmos_service
from app.core.azure_openai import analyze_cv_with_openai
from app.core.document_intelligence import document_intelligence
from app.services.email_service import send_analysis_completion_email
from app.services.role_analyzers import get_role_analyzer
from app.config import settings
from typing import Dict, Any
import json
import os
from datetime import datetime
import asyncio
import logging

# Configure logging
logger = logging.getLogger(__name__)

async def analyze_cv_background(
    analysis_id: str,
    blob_name: str,
    name: str,
    email: str,
    target_role: str,
    experience_level: str
):
    """
    Background task to analyze a CV.
    
    1. Get the CV from Azure Blob Storage
    2. Extract structured data with Document Intelligence
    3. Create role-specific analysis payload
    4. Call Azure OpenAI to analyze it
    5. Process the results
    6. Update the status and save the results to Cosmos DB
    """
    try:
        logger.info(f"Starting analysis for {analysis_id}")
        
        # Update status to processing
        await update_analysis_status(analysis_id, "processing", 0.1, 45)
        
        # Get the blob URL
        blob_url = await get_blob_url(blob_name)
        logger.info(f"Got blob URL: {blob_url}")
        
        # Extract structured data using Document Intelligence
        logger.info(f"Extracting document data with Document Intelligence")
        try:
            resume_data = await document_intelligence.analyze_document(blob_url)
            logger.info(f"Successfully extracted structured data from resume")
        except Exception as doc_error:
            logger.error(f"Error extracting document data: {str(doc_error)}")
            # If Document Intelligence fails, create a minimal resume_data structure
            resume_data = {
                "raw_text": f"Error extracting document data: {str(doc_error)}",
                "contact_info": {"name": name, "email": email},
                "skills": [],
                "work_experience": [],
                "education": [],
                "sections": {}
            }
        
        # Update status
        await update_analysis_status(analysis_id, "processing", 0.3, 30)
        
        # Get the appropriate role analyzer
        role_analyzer = get_role_analyzer(target_role, experience_level)
        
        # Create a structured analysis payload
        analysis_payload = role_analyzer.create_analysis_payload(resume_data)
        
        # Get the role-specific prompts
        system_prompt = role_analyzer.get_system_prompt()
        user_prompt = role_analyzer.get_user_prompt(resume_data)
        
        # Update status
        await update_analysis_status(analysis_id, "processing", 0.5, 25)
        
        # Call OpenAI to analyze the CV
        logger.info(f"Calling Azure OpenAI for analysis")
        try:
            analysis_result = await analyze_cv_with_openai(
                cv_url=blob_url,
                name=name,
                email=email, 
                target_role=target_role,
                experience_level=experience_level,
                role_requirements=role_analyzer.role_requirements,
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
        except Exception as ai_error:
            logger.error(f"Error in OpenAI analysis: {str(ai_error)}")
            analysis_result = create_fallback_analysis(target_role, experience_level)
        
        # Update status
        await update_analysis_status(analysis_id, "processing", 0.8, 10)
        
        # Enrich the result with additional metadata
        analysis_result["completed_at"] = datetime.utcnow().isoformat()
        analysis_result["role"] = target_role
        analysis_result["experience_level"] = experience_level
        
        # Store the structured resume data for reference
        analysis_result["structured_resume"] = resume_data
        
        # Store the analysis payload
        analysis_result["analysis_payload"] = analysis_payload
        
        # Update the analysis record with results
        update_data = {
            "status": "completed",
            "results": analysis_result,
            "updated_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat()
        }
        
        # Save the analysis results to Cosmos DB
        await cosmos_service.update_analysis_record(analysis_id, update_data)
            
        logger.info(f"Analysis completed and saved for {analysis_id}")
        
        # Send email notification if enabled
        if settings.EMAIL_ENABLED:
            overall_score = analysis_result.get("overall_score", 0)
            email_sent = await send_analysis_completion_email(
                to_email=email,
                name=name,
                analysis_id=analysis_id,
                target_role=target_role,
                overall_score=overall_score
            )
            
            if email_sent:
                logger.info(f"Email notification sent to {email}")
            else:
                logger.warning(f"Failed to send email notification to {email}")
        
    except Exception as e:
        logger.error(f"Error analyzing CV {analysis_id}: {str(e)}")
        
        # Update status to failed
        try:
            error_update = {
                "status": "failed",
                "error": str(e),
                "updated_at": datetime.utcnow().isoformat()
            }
            await cosmos_service.update_analysis_record(analysis_id, error_update)
        except Exception as inner_e:
            logger.error(f"Error updating failure status: {str(inner_e)}")

async def update_analysis_status(
    analysis_id: str, 
    status: str, 
    progress: float, 
    estimated_time_remaining: int
):
    """Update the status of an analysis in Cosmos DB"""
    try:
        update_data = {
            "status": status,
            "progress": progress,
            "estimated_time_remaining": estimated_time_remaining,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await cosmos_service.update_analysis_record(analysis_id, update_data)
            
    except Exception as e:
        logger.error(f"Error updating analysis status: {str(e)}")

def create_fallback_analysis(target_role: str, experience_level: str) -> Dict[str, Any]:
    """
    Create a fallback analysis in case the OpenAI API fails
    """
    return {
        "overall_score": 50,
        "categories": [
            {
                "name": "Technical Skills",
                "score": 50,
                "feedback": "Unable to perform detailed analysis. Please review the CV manually.",
                "suggestions": ["Ensure skills match the core requirements for the role."]
            },
            {
                "name": "Experience",
                "score": 50,
                "feedback": "Unable to perform detailed analysis. Please review the CV manually.",
                "suggestions": ["Focus on relevant experience for the target role."]
            },
            {
                "name": "Overall Presentation",
                "score": 50,
                "feedback": "Unable to perform detailed analysis. Please review the CV manually.",
                "suggestions": ["Ensure the CV is well-structured and tailored to the role."]
            }
        ],
        "keyword_analysis": {
            "present": [],
            "missing": [],
            "recommended": ["Review manually to identify relevant keywords."]
        },
        "matrix_alignment": {
            "current_level": "unknown",
            "target_level": experience_level,
            "gap_areas": ["Unable to determine gaps automatically."]
        },
        "summary": "Automatic analysis failed. Please review the CV manually against the requirements for a " 
                  f"{target_role} position at {experience_level} level."
    }