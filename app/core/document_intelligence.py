# app/core/document_intelligence.py
import logging
import json
import os
from typing import Dict, Any, List, Optional
import aiohttp
from datetime import datetime, timedelta
import asyncio
from app.config import settings

logger = logging.getLogger(__name__)

class DocumentIntelligenceService:
    """Service for extracting structured data from resumes using Azure Document Intelligence"""
    
    def __init__(self):
        self.endpoint = settings.DOCUMENT_INTELLIGENCE_ENDPOINT
        self.key = settings.DOCUMENT_INTELLIGENCE_KEY
        self.model_id = settings.DOCUMENT_INTELLIGENCE_MODEL_ID  # Using the prebuilt resume model
    
    async def analyze_document(self, document_url: str) -> Dict[str, Any]:
        """
        Analyze a resume document using Azure Document Intelligence
        
        Args:
            document_url: The URL to the document in Azure Blob Storage
            
        Returns:
            Structured JSON data extracted from the resume
        """
        try:
            logger.info(f"Analyzing document at URL: {document_url}")
            
            # Set up the API request
            headers = {
                "Content-Type": "application/json",
                "Ocp-Apim-Subscription-Key": self.key
            }
            
            body = {
                "urlSource": document_url
            }
            
            # Define the API endpoint URL
            api_url = f"{self.endpoint}/documentintelligence/documentModels/{self.model_id}:analyze?api-version=2023-07-31"
            
            # Submit the document for analysis
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, headers=headers, json=body) as response:
                    if response.status in (200, 202):
                        operation_location = response.headers.get("Operation-Location")
                        if not operation_location:
                            raise Exception("No Operation-Location header in response")
                        
                        # Poll the operation until it's complete
                        result = await self._poll_operation_result(session, operation_location, headers)
                        return self._process_analysis_result(result)
                    else:
                        error_text = await response.text()
                        logger.error(f"Document Intelligence API error: {response.status}, {error_text}")
                        raise Exception(f"Document Intelligence API error: {response.status}, {error_text}")
        
        except Exception as e:
            logger.error(f"Error analyzing document with Document Intelligence: {str(e)}")
            raise
    
    async def _poll_operation_result(self, session: aiohttp.ClientSession, operation_location: str, 
                                    headers: Dict[str, str], max_retries: int = 10) -> Dict[str, Any]:
        """
        Poll the Document Intelligence operation until it completes
        
        Args:
            session: The active aiohttp session
            operation_location: The URL to poll for results
            headers: Request headers
            max_retries: Maximum number of polling attempts
            
        Returns:
            The analysis result
        """
        n_tries = 0
        wait_time = 2  # Start with 2 seconds wait time
        
        while n_tries < max_retries:
            try:
                async with session.get(operation_location, headers=headers) as response:
                    response_json = await response.json()
                    
                    status = response_json.get("status")
                    if status == "succeeded":
                        return response_json
                    elif status == "failed":
                        error_info = response_json.get("error", {})
                        error_message = error_info.get("message", "Unknown error")
                        raise Exception(f"Document analysis failed: {error_message}")
                    
                    # Wait and retry with exponential backoff
                    n_tries += 1
                    await asyncio.sleep(wait_time)
                    wait_time = min(wait_time * 2, 30)  # Double wait time, max 30 seconds
            
            except Exception as e:
                if n_tries >= max_retries - 1:
                    logger.error(f"Max retries exceeded for document analysis: {str(e)}")
                    raise
                logger.warning(f"Error polling document analysis (retry {n_tries+1}/{max_retries}): {str(e)}")
                await asyncio.sleep(wait_time)
                wait_time = min(wait_time * 2, 30)
                n_tries += 1
        
        raise Exception("Document analysis timed out")
    
    def _process_analysis_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and structure the raw Document Intelligence analysis result
        
        Args:
            result: The raw analysis result
            
        Returns:
            A structured and normalized representation of the resume
        """
        try:
            # Extract the analyzed document
            analyzed_document = result.get("analyzeResult", {})
            document = analyzed_document.get("documents", [{}])[0] if analyzed_document.get("documents") else {}
            
            if not document:
                # Fallback to extracting content from pages
                return self._extract_from_pages(analyzed_document.get("pages", []))
            
            # Initialize the structured resume
            structured_resume = {
                "metadata": {
                    "extracted_at": datetime.utcnow().isoformat(),
                    "model_id": self.model_id,
                    "confidence": document.get("confidence", 0)
                },
                "contact_info": {},
                "skills": [],
                "work_experience": [],
                "education": [],
                "sections": {},
                "raw_text": ""
            }
            
            # Extract fields from the document
            fields = document.get("fields", {})
            
            # Extract contact information
            contact_info = fields.get("contactInfo", {}).get("valueObject", {})
            structured_resume["contact_info"] = {
                "name": self._extract_field_value(contact_info.get("name", {})),
                "email": self._extract_field_value(contact_info.get("email", {})),
                "phone": self._extract_field_value(contact_info.get("phone", {})),
                "linkedin": self._extract_field_value(contact_info.get("linkedIn", {})),
                "location": self._extract_field_value(contact_info.get("location", {}))
            }
            
            # Extract skills
            skills = fields.get("skills", {}).get("valueArray", [])
            structured_resume["skills"] = [
                {
                    "name": self._extract_field_value(skill.get("valueObject", {}).get("name", {})),
                    "confidence": skill.get("confidence", 0)
                }
                for skill in skills
            ]
            
            # Extract work experience
            work_experiences = fields.get("workExperiences", {}).get("valueArray", [])
            structured_resume["work_experience"] = [
                self._process_work_experience(exp.get("valueObject", {}))
                for exp in work_experiences
            ]
            
            # Extract education
            educations = fields.get("educationDetails", {}).get("valueArray", [])
            structured_resume["education"] = [
                self._process_education(edu.get("valueObject", {}))
                for edu in educations
            ]
            
            # Extract raw text from pages for additional processing
            structured_resume["raw_text"] = self._extract_raw_text(analyzed_document.get("pages", []))
            
            # Extract sections based on the raw text and page layout
            structured_resume["sections"] = self._extract_sections(analyzed_document)
            
            return structured_resume
            
        except Exception as e:
            logger.error(f"Error processing Document Intelligence result: {str(e)}")
            # Fallback to a simpler extraction if structured parsing fails
            return self._extract_fallback(result)
    
    def _extract_field_value(self, field: Dict[str, Any]) -> str:
        """Extract the content value from a Document Intelligence field"""
        return field.get("content", "") if field else ""
    
    def _process_work_experience(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        """Process a work experience entry from Document Intelligence"""
        return {
            "company": self._extract_field_value(experience.get("company", {})),
            "job_title": self._extract_field_value(experience.get("jobTitle", {})),
            "location": self._extract_field_value(experience.get("location", {})),
            "start_date": self._extract_field_value(experience.get("startDate", {})),
            "end_date": self._extract_field_value(experience.get("endDate", {})),
            "description": self._extract_field_value(experience.get("jobDescription", {})),
            "responsibilities": [
                self._extract_field_value(resp) for resp in 
                experience.get("jobResponsibilities", {}).get("valueArray", [])
            ]
        }
    
    def _process_education(self, education: Dict[str, Any]) -> Dict[str, Any]:
        """Process an education entry from Document Intelligence"""
        return {
            "institution": self._extract_field_value(education.get("institution", {})),
            "degree": self._extract_field_value(education.get("degree", {})),
            "field_of_study": self._extract_field_value(education.get("fieldOfStudy", {})),
            "start_date": self._extract_field_value(education.get("startDate", {})),
            "end_date": self._extract_field_value(education.get("endDate", {})),
            "gpa": self._extract_field_value(education.get("gpa", {}))
        }
    
    def _extract_raw_text(self, pages: List[Dict[str, Any]]) -> str:
        """Extract the raw text content from all pages"""
        text = ""
        for page in pages:
            content = page.get("content", "")
            if content:
                text += content + "\n\n"
        return text.strip()
    
    def _extract_sections(self, analyzed_document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract resume sections based on paragraph and heading structure
        
        This is a more advanced extraction that tries to identify distinct
        sections in the resume based on headings and text layout
        """
        sections = {}
        current_section = None
        section_content = []
        
        # Extract paragraphs and try to identify sections
        paragraphs = analyzed_document.get("paragraphs", [])
        
        for paragraph in paragraphs:
            content = paragraph.get("content", "").strip()
            if not content:
                continue
                
            # Check if this paragraph looks like a heading
            role_name = paragraph.get("role", "")
            is_heading = (
                role_name == "heading" or 
                role_name == "title" or
                (len(content) < 50 and content.upper() == content) or  # ALL CAPS short text
                content.endswith(":")  # Ends with colon
            )
            
            if is_heading:
                # Save the previous section if it exists
                if current_section and section_content:
                    sections[current_section] = "\n".join(section_content)
                
                # Start a new section
                current_section = content.rstrip(":").strip()
                section_content = []
            elif current_section:
                # Add content to the current section
                section_content.append(content)
            
        # Save the last section
        if current_section and section_content:
            sections[current_section] = "\n".join(section_content)
            
        # Try to identify common resume sections if they're not already identified
        if not any(key.lower() in ["skill", "skills", "technical skills"] for key in sections.keys()):
            self._identify_skills_section(sections, analyzed_document)
            
        if not any(key.lower() in ["experience", "work experience", "employment"] for key in sections.keys()):
            self._identify_experience_section(sections, analyzed_document)
            
        if not any(key.lower() in ["education", "academic", "qualification"] for key in sections.keys()):
            self._identify_education_section(sections, analyzed_document)
            
        return sections
    
    def _identify_skills_section(self, sections: Dict[str, str], analyzed_document: Dict[str, Any]) -> None:
        """Try to identify a skills section from raw content if it wasn't found by headings"""
        raw_text = self._extract_raw_text(analyzed_document.get("pages", []))
        
        # Look for lists and patterns that might indicate skills
        # This is a simplified approach - in production, more sophisticated 
        # pattern matching would be used
        skills_text = ""
        
        # Look for bullet lists of short items
        for paragraph in analyzed_document.get("paragraphs", []):
            content = paragraph.get("content", "").strip()
            if content.startswith("•") or content.startswith("-") or content.startswith("*"):
                if len(content) < 100:  # Likely a skill item
                    skills_text += content + "\n"
                    
        if skills_text:
            sections["Skills"] = skills_text.strip()
    
    def _identify_experience_section(self, sections: Dict[str, str], analyzed_document: Dict[str, Any]) -> None:
        """Try to identify an experience section if it wasn't found by headings"""
        # Simplified approach - look for paragraphs with company names or job titles
        # In production, more sophisticated entity recognition would be used
        pass
    
    def _identify_education_section(self, sections: Dict[str, str], analyzed_document: Dict[str, Any]) -> None:
        """Try to identify an education section if it wasn't found by headings"""
        # Simplified approach - look for paragraphs with education keywords
        # In production, more sophisticated entity recognition would be used
        pass
    
    def _extract_from_pages(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback method to extract content from pages if structured extraction fails"""
        raw_text = self._extract_raw_text(pages)
        
        return {
            "metadata": {
                "extracted_at": datetime.utcnow().isoformat(),
                "model_id": self.model_id,
                "confidence": 0,
                "extraction_method": "fallback"
            },
            "contact_info": {},
            "skills": [],
            "work_experience": [],
            "education": [],
            "sections": {},
            "raw_text": raw_text
        }
    
    def _extract_fallback(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Ultimate fallback method if all other extraction methods fail"""
        try:
            analyzed_result = result.get("analyzeResult", {})
            content = ""
            
            # Try to extract content from pages
            for page in analyzed_result.get("pages", []):
                page_content = page.get("content", "")
                if page_content:
                    content += page_content + "\n\n"
            
            # If no content from pages, try to get content from document
            if not content and analyzed_result.get("content"):
                content = analyzed_result.get("content")
            
            return {
                "metadata": {
                    "extracted_at": datetime.utcnow().isoformat(),
                    "model_id": self.model_id,
                    "confidence": 0,
                    "extraction_method": "emergency_fallback"
                },
                "raw_text": content.strip()
            }
        except Exception as e:
            logger.error(f"Emergency fallback extraction failed: {str(e)}")
            return {
                "metadata": {
                    "extracted_at": datetime.utcnow().isoformat(),
                    "error": str(e)
                },
                "raw_text": "Failed to extract content from document."
            }

# Create singleton instance
document_intelligence = DocumentIntelligenceService()