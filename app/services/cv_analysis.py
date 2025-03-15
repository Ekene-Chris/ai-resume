# app/services/cv_analysis.py - Update
from app.core.azure_blob import get_blob_url
from app.core.cosmos_db import cosmos_service
from app.core.azure_openai import analyze_cv_with_openai
from app.core.document_intelligence import document_intelligence
from app.services.role_analyzers import get_role_analyzer
from app.file_utils import download_file, extract_text_from_pdf_bytes, extract_text_from_docx_bytes
from app.core.blob_access_handler import blob_access_handler
from app.config import settings
from typing import Dict, Any, BinaryIO, Optional, Tuple
import json
import os
from datetime import datetime
import asyncio
import logging
from fastapi import Response

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
    Background task to analyze a CV with improved blob access handling.
    
    1. Get the CV from Azure Blob Storage with access diagnostics
    2. Extract text using Document Intelligence with fallback
    3. Create role-specific analysis payload
    4. Call Azure OpenAI to analyze it
    5. Process the results
    6. Update the status and save the results to Cosmos DB
    """
    try:
        logger.info(f"Starting analysis for {analysis_id}")
        
        # Update status to processing
        await update_analysis_status(analysis_id, "processing", 0.1, 45)
        
        # Get the blob URL with access check
        try:
            blob_url = await get_blob_url(blob_name)
            logger.info(f"Got initial blob URL: {blob_url}")
            
            # Check if the blob URL is accessible - if not, try to get an accessible URL
            accessible_url = await blob_access_handler.get_accessible_url(blob_name, blob_url)
            
            if accessible_url != blob_url:
                logger.info(f"Using SAS URL for better access")
                blob_url = accessible_url
            
        except Exception as blob_error:
            logger.error(f"Error getting blob URL: {str(blob_error)}")
            
            # Try to diagnose the issue
            error_message, is_fixable = await blob_access_handler.diagnose_blob_access_error(
                blob_name=blob_name,
                error=blob_error
            )
            
            if is_fixable:
                # Try to generate a SAS URL
                logger.info(f"Attempting to generate SAS URL for blob")
                sas_url = await blob_access_handler.generate_sas_url(blob_name)
                
                if sas_url:
                    blob_url = sas_url
                    logger.info(f"Successfully generated SAS URL")
                else:
                    raise Exception(f"Could not access blob: {error_message}")
            else:
                raise Exception(f"Blob access error: {error_message}")
        
        # Extract structured data from the document
        try:
            logger.info(f"Extracting document data using Document Intelligence")
            resume_data = await document_intelligence.analyze_document(blob_url)
            logger.info(f"Successfully extracted structured data from resume")
            
            # Validate we got useful content
            if not resume_data.get("raw_text", "").strip():
                raise Exception("Document Intelligence returned empty text content")
                
        except Exception as doc_error:
            logger.error(f"CRITICAL: Error extracting document data: {str(doc_error)}", exc_info=True)
            
            # Check if this is a network/access issue
            error_message, is_fixable = await blob_access_handler.diagnose_blob_access_error(
                blob_name=blob_name,
                error=doc_error
            )
            
            if is_fixable:
                # Try directly downloading and processing the file
                logger.info(f"Attempting direct file processing as fallback")
                
                try:
                    # Try with a SAS token URL
                    sas_url = await blob_access_handler.generate_sas_url(blob_name)
                    if sas_url:
                        blob_url = sas_url
                        logger.info(f"Using SAS URL for direct download: {blob_url}")
                    
                    # Download and process the file directly
                    file_content = await download_file(blob_url)
                    
                    if not file_content:
                        raise Exception(f"Failed to download file content: {error_message}")
                    
                    # Extract text based on file type
                    if blob_name.lower().endswith('.pdf'):
                        text = await extract_text_from_pdf_bytes(file_content)
                    elif blob_name.lower().endswith('.docx') or blob_name.lower().endswith('.doc'):
                        text = await extract_text_from_docx_bytes(file_content)
                    else:
                        # Assume it's plain text
                        text = file_content.decode('utf-8', errors='replace')
                    
                    # Create basic structured data
                    resume_data = {
                        "metadata": {
                            "extracted_at": datetime.utcnow().isoformat(),
                            "extraction_method": "direct_extraction",
                            "original_error": str(doc_error)
                        },
                        "raw_text": text,
                        "contact_info": {},
                        "skills": [],
                        "work_experience": [],
                        "education": [],
                        "sections": {}
                    }
                    
                    logger.info(f"Successfully extracted text via direct method: {len(text)} characters")
                except Exception as direct_error:
                    logger.error(f"Direct processing also failed: {str(direct_error)}")
                    error_update = {
                        "status": "failed",
                        "error": f"Document extraction failed: {error_message}. Direct extraction also failed: {str(direct_error)}",
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    await cosmos_service.update_analysis_record(analysis_id, error_update)
                    return  # Stop processing this job
            else:
                error_update = {
                    "status": "failed",
                    "error": f"Document extraction failed: {error_message}",
                    "updated_at": datetime.utcnow().isoformat()
                }
                await cosmos_service.update_analysis_record(analysis_id, error_update)
                return  # Stop processing this job
        
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
        try:
            logger.info(f"Calling Azure OpenAI for analysis")
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
            logger.error(f"CRITICAL: Error in OpenAI analysis: {str(ai_error)}", exc_info=True)
            error_update = {
                "status": "failed",
                "error": f"AI analysis failed: {str(ai_error)}",
                "updated_at": datetime.utcnow().isoformat()
            }
            await cosmos_service.update_analysis_record(analysis_id, error_update)
            return  # Stop processing this job
        
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
        
        # Add Teleios/Ekene Chris branding to the summary
        if "summary" in analysis_result:
            original_summary = analysis_result["summary"]
            branded_summary = f"{original_summary}\n\nThis analysis is powered by Ekene Chris's Global DevOps Competency Matrix. For targeted improvement in the identified gap areas, consider exploring Teleios - our exclusive tech learning platform designed for ambitious engineers looking to compete on the global stage."
            analysis_result["summary"] = branded_summary
        
        # Add Teleios recommendations to missing skills
        if "matrix_alignment" in analysis_result and "gap_areas" in analysis_result["matrix_alignment"]:
            gap_areas = analysis_result["matrix_alignment"]["gap_areas"]
            teleios_opportunities = []
            
            if gap_areas and len(gap_areas) > 0:
                teleios_opportunities = [
                    f"Teleios offers advanced modules specifically designed to address {gap}" 
                    for gap in gap_areas[:3]  # Limit to top 3 gaps
                ]
                
                analysis_result["teleios_opportunities"] = teleios_opportunities
        
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
        
        # Send email notification with PDF if enabled
        if settings.EMAIL_ENABLED:
            try:
                # Import services here to avoid circular imports
                from app.services.pdf_generator import pdf_generator
                from app.services.email_service import email_service
                
                logger.info(f"Generating PDF report for analysis {analysis_id}")
                pdf_report = pdf_generator.generate_analysis_report(
                    analysis_data=analysis_result,
                    name=name,
                    email=email,
                    target_role=target_role
                )
                
                # Send email with PDF attachment
                logger.info(f"Sending email with PDF report to {email}")
                email_sent = await email_service.send_analysis_completion_email(
                    to_email=email,
                    name=name,
                    analysis_id=analysis_id,
                    target_role=target_role,
                    pdf_attachment=pdf_report
                )
                
                if email_sent:
                    logger.info(f"Email with PDF report sent to {email}")
                else:
                    logger.warning(f"Failed to send email with PDF report to {email}")
            except Exception as email_error:
                logger.error(f"Error in email process: {str(email_error)}", exc_info=True)
                # Continue execution even if email fails
        
    except Exception as e:
        logger.error(f"Error analyzing CV {analysis_id}: {str(e)}", exc_info=True)
        
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
        logger.info(f"Updated analysis status: {status}, progress: {progress}")
            
    except Exception as e:
        logger.error(f"Error updating analysis status: {str(e)}", exc_info=True)
        raise