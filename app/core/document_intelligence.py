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
            
            # Import necessary modules
            from azure.core.credentials import AzureKeyCredential
            from azure.ai.formrecognizer import DocumentAnalysisClient  # Try older client
            
            # Log endpoint and key prefix for debugging
            logger.info(f"Using endpoint: {self.endpoint}")
            logger.info(f"Key prefix: {self.key[:4]}...")
            
            # Create client
            document_client = DocumentAnalysisClient(
                endpoint=self.endpoint, 
                credential=AzureKeyCredential(self.key)
            )
            
            # Try to analyze the document with the Read model
            logger.info(f"Analyzing document with read model")
            poller = document_client.begin_analyze_document_from_url(
                "prebuilt-read",  # Basic OCR capabilities
                document_url
            )
            
            # Wait for the operation to complete
            result = poller.result()
            
            # Process the results into our expected format
            structured_resume = {
                "metadata": {
                    "extracted_at": datetime.utcnow().isoformat(),
                    "model_id": "prebuilt-read",
                    "confidence": 0.0
                },
                "contact_info": {},
                "skills": [],
                "work_experience": [],
                "education": [],
                "sections": {},
                "raw_text": ""
            }
            
            # Extract text content from the document
            text_content = []
            for page in result.pages:
                for line in page.lines:
                    text_content.append(line.content)
            
            structured_resume["raw_text"] = "\n".join(text_content)
            
            # If no text was extracted, that's an error
            if not structured_resume["raw_text"].strip():
                raise Exception("No text content could be extracted from the document")
            
            logger.info(f"Successfully extracted {len(text_content)} lines of text")
            return structured_resume
        
        except Exception as e:
            logger.error(f"Error analyzing document with Document Intelligence: {str(e)}", exc_info=True)
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
                        logger.error(f"Document analysis failed with error: {error_message}")
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
        
        logger.error("Document analysis timed out after maximum retries")
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
                logger.error("Document Intelligence returned no document structure")
                raise Exception("Document Intelligence failed to extract document structure")
            
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
            
            # Check if raw text is empty
            if not structured_resume["raw_text"].strip():
                logger.error("Document Intelligence extracted empty text content from pages")
                if analyzed_document.get("content"):
                    structured_resume["raw_text"] = analyzed_document.get("content")
                else:
                    raise Exception("No text content could be extracted from the document")
            
            # Extract sections based on the raw text and page layout
            structured_resume["sections"] = self._extract_sections(analyzed_document)
            
            return structured_resume
            
        except Exception as e:
            logger.error(f"Error processing Document Intelligence result: {str(e)}", exc_info=True)
            raise
    
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
        for i, page in enumerate(pages):
            content = page.get("content", "")
            if content:
                text += content + "\n\n"
            else:
                logger.warning(f"Page {i+1} has no content")
        
        if not text.strip():
            logger.error("No text content found in any page of the document")
        
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
        pass
    
    def _identify_education_section(self, sections: Dict[str, str], analyzed_document: Dict[str, Any]) -> None:
        """Try to identify an education section if it wasn't found by headings"""
        pass

    def _process_layout_result(self, result) -> Dict[str, Any]:
        """Process results from the layout model"""
        structured_resume = {
            "metadata": {
                "extracted_at": datetime.utcnow().isoformat(),
                "model_id": "prebuilt-layout",
                "confidence": 0.0
            },
            "contact_info": {},
            "skills": [],
            "work_experience": [],
            "education": [],
            "sections": {},
            "raw_text": ""
        }
        
        # Extract text from all pages
        raw_text = ""
        for page in result.pages:
            if page.lines:
                for line in page.lines:
                    raw_text += line.content + "\n"
        
        structured_resume["raw_text"] = raw_text.strip()
        
        # Extract tables as potential sections
        if result.tables:
            for table_idx, table in enumerate(result.tables):
                section_name = f"Table_{table_idx+1}"
                section_content = []
                
                for cell in table.cells:
                    section_content.append(cell.content)
                
                structured_resume["sections"][section_name] = "\n".join(section_content)
        
        logger.info(f"Extracted {len(structured_resume['raw_text'])} characters using layout model")
        return structured_resume

    def _process_read_result(self, result) -> Dict[str, Any]:
        """Process results from the read model"""
        structured_resume = {
            "metadata": {
                "extracted_at": datetime.utcnow().isoformat(),
                "model_id": "prebuilt-read",
                "confidence": 0.0
            },
            "contact_info": {},
            "skills": [],
            "work_experience": [],
            "education": [],
            "sections": {},
            "raw_text": ""
        }
        
        # Extract text from all pages
        raw_text = ""
        for page in result.pages:
            if page.lines:
                for line in page.lines:
                    raw_text += line.content + "\n"
        
        structured_resume["raw_text"] = raw_text.strip()
        
        # Extract paragraphs as potential sections
        if result.paragraphs:
            for idx, paragraph in enumerate(result.paragraphs):
                if paragraph.role and paragraph.role != "default":
                    section_name = f"{paragraph.role}_{idx+1}"
                    structured_resume["sections"][section_name] = paragraph.content
        
        logger.info(f"Extracted {len(structured_resume['raw_text'])} characters using read model")
        return structured_resume

# Create singleton instance
document_intelligence = DocumentIntelligenceService()