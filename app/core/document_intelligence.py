# app/core/document_intelligence.py
import logging
import json
import os
from typing import Dict, Any, List, Optional
import aiohttp
from datetime import datetime, timedelta
import asyncio
from app.config import settings
from app.core.blob_access_handler import blob_access_handler
from app.file_utils import download_file, extract_text_from_pdf_bytes, extract_text_from_docx_bytes

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
            # Extract blob name from URL
            blob_name = document_url.split('/')[-1].split('?')[0]  # Remove query params
            logger.info(f"Analyzing document at URL: {document_url}")
            
            try:
                # Import necessary modules
                from azure.core.credentials import AzureKeyCredential
                from azure.ai.formrecognizer import DocumentAnalysisClient
                
                # Log endpoint and key prefix for debugging
                logger.info(f"Using Document Intelligence endpoint: {self.endpoint}")
                
                # Create client
                document_client = DocumentAnalysisClient(
                    endpoint=self.endpoint, 
                    credential=AzureKeyCredential(self.key)
                )
                
                # Try to analyze the document with the document intelligence model
                logger.info(f"Analyzing document with Document Intelligence")
                
                try:
                    # First attempt with original URL
                    poller = document_client.begin_analyze_document_from_url(
                        "prebuilt-read",  # Basic OCR capabilities
                        document_url
                    )
                    result = poller.result()
                    logger.info(f"Successfully analyzed document with Document Intelligence")
                    
                except Exception as di_error:
                    logger.warning(f"Initial Document Intelligence analysis failed: {str(di_error)}")
                    
                    # Check if this is an access issue
                    error_message, is_fixable = await blob_access_handler.diagnose_blob_access_error(
                        blob_name=blob_name, 
                        error=di_error
                    )
                    
                    if is_fixable:
                        # Try to get an accessible URL (with SAS token)
                        logger.info(f"Attempting to get accessible URL for blob {blob_name}")
                        accessible_url = await blob_access_handler.get_accessible_url(
                            blob_name=blob_name,
                            original_url=document_url
                        )
                        
                        if accessible_url != document_url:
                            logger.info(f"Generated accessible URL, retrying Document Intelligence")
                            
                            # Retry with SAS URL
                            poller = document_client.begin_analyze_document_from_url(
                                "prebuilt-read",
                                accessible_url
                            )
                            result = poller.result()
                            logger.info(f"Successfully analyzed document with SAS URL")
                        else:
                            raise Exception(f"Could not generate accessible URL: {error_message}")
                    else:
                        # If it's not fixable, raise the error
                        raise Exception(f"Document access error: {error_message}")
                
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
                
                # Attempt to extract more structured data
                try:
                    structured_resume["contact_info"] = self._extract_contact_info(structured_resume["raw_text"])
                    structured_resume["skills"] = self._extract_skills(structured_resume["raw_text"])
                    structured_resume["sections"] = self._extract_sections(structured_resume["raw_text"])
                    
                    # Only log, don't break if these extractions fail
                    logger.info("Successfully extracted additional structured data")
                except Exception as extraction_error:
                    logger.warning(f"Error during additional data extraction: {str(extraction_error)}")
                
                return structured_resume
                
            except Exception as di_error:
                # Log the Document Intelligence error
                logger.error(f"Document Intelligence error: {str(di_error)}")
                
                # Fall back to direct file processing
                logger.info("Falling back to direct file processing")
                
                # Try to get an accessible URL for the blob
                try:
                    accessible_url = await blob_access_handler.get_accessible_url(
                        blob_name=blob_name,
                        original_url=document_url
                    )
                except Exception as access_error:
                    logger.warning(f"Error getting accessible URL: {str(access_error)}")
                    accessible_url = document_url  # Fall back to original URL
                
                # Download the file
                file_content = await download_file(accessible_url)
                
                if not file_content:
                    raise Exception("Failed to download document content")
                
                # Determine file type and extract text
                if blob_name.lower().endswith('.pdf'):
                    logger.info("Processing PDF document with direct extraction")
                    raw_text = await extract_text_from_pdf_bytes(file_content)
                elif blob_name.lower().endswith('.docx') or blob_name.lower().endswith('.doc'):
                    logger.info("Processing DOCX document with direct extraction")
                    raw_text = await extract_text_from_docx_bytes(file_content)
                else:
                    logger.info("Processing text document")
                    raw_text = file_content.decode('utf-8', errors='replace')
                
                # If we got no text, that's an error
                if not raw_text or len(raw_text.strip()) < 50:
                    raise Exception("Extracted text is too short or empty")
                
                # Create a basic structure
                structured_resume = {
                    "metadata": {
                        "extracted_at": datetime.utcnow().isoformat(),
                        "extraction_method": "direct_extraction",
                        "reason": str(di_error)
                    },
                    "contact_info": self._extract_contact_info(raw_text),
                    "skills": self._extract_skills(raw_text),
                    "work_experience": self._extract_work_experience(raw_text),
                    "education": self._extract_education(raw_text),
                    "sections": self._extract_sections(raw_text),
                    "raw_text": raw_text
                }
                
                logger.info(f"Successfully extracted {len(raw_text)} characters with direct method")
                return structured_resume
        
        except Exception as e:
            logger.error(f"Error analyzing document: {str(e)}", exc_info=True)
            
            # Return a minimal structure with whatever we have
            raw_text = ""
            if 'raw_text' in locals() and raw_text:
                pass
            elif 'text_content' in locals() and text_content:
                raw_text = "\n".join(text_content)
            else:
                raw_text = "Failed to extract any text from document"
            
            return {
                "metadata": {
                    "extracted_at": datetime.utcnow().isoformat(),
                    "extraction_method": "error_fallback",
                    "error": str(e)
                },
                "contact_info": {},
                "skills": [],
                "work_experience": [],
                "education": [],
                "sections": {},
                "raw_text": raw_text
            }
    
    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information from text"""
        import re
        
        # Initialize contact info
        contact_info = {
            "name": "",
            "email": "",
            "phone": "",
            "linkedin": "",
            "location": ""
        }
        
        # Extract email
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        email_match = re.search(email_pattern, text)
        if email_match:
            contact_info["email"] = email_match.group(0)
        
        # Extract phone (simple pattern)
        phone_pattern = r'(?:\+\d{1,3}[-\.\s]?)?(?:\(?\d{3}\)?[-\.\s]?)?\d{3}[-\.\s]?\d{4}'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            contact_info["phone"] = phone_match.group(0)
        
        # Extract LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_match:
            contact_info["linkedin"] = linkedin_match.group(0)
        
        # Try to extract name (first 100 chars, first line that's not too long)
        first_100 = text[:100]
        lines = first_100.split('\n')
        for line in lines:
            line = line.strip()
            if 2 < len(line) < 40 and not any(c in line for c in ['@', '/', ':', 'http']):
                contact_info["name"] = line
                break
                
        return contact_info
    
    def _extract_skills(self, text: str) -> List[Dict[str, Any]]:
        """Extract skills from resume text"""
        import re
        
        # Common tech skills to look for
        tech_skills = [
            # Programming languages
            "Python", "JavaScript", "TypeScript", "Java", "C#", "C\\+\\+", "Go", "Ruby", "PHP",
            "Rust", "Swift", "Kotlin", "Scala", "R", "Bash", "Perl", "Shell", "PowerShell",
            
            # Web technologies
            "HTML", "CSS", "React", "Angular", "Vue", "Next.js", "Gatsby", "Node.js", "Express",
            "Django", "Flask", "Spring", "Laravel", "Rails", "ASP.NET", 
            
            # DevOps tools and platforms
            "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform", "Ansible", "Chef",
            "Puppet", "Jenkins", "GitHub Actions", "CircleCI", "Travis CI", "ArgoCD", "GitLab CI",
            "YAML", "GitHub", "Git", "Prometheus", "Grafana", "ELK", "Elasticsearch", "Logstash", 
            "Kibana", "Datadog", "New Relic", "Nagios", "Zabbix",
            
            # Databases
            "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "Cassandra", "DynamoDB", 
            "Oracle", "MS SQL Server", "SQLite", "Neo4j", "Couchbase", "Firebase",
            
            # Cloud services
            "Lambda", "S3", "EC2", "ECS", "EKS", "RDS", "CloudFormation", "Azure Functions",
            "App Service", "Azure DevOps", "Google Cloud Run", "Serverless", "Microservices",
            "API Gateway", "Service Mesh", "Istio", "Linkerd", "Cloudflare",
            
            # Other tech
            "CI/CD", "TDD", "BDD", "Agile", "Scrum", "Kanban", "REST", "GraphQL", "gRPC",
            "WebSockets", "OAuth", "JWT", "SAML", "SSO", "GDPR", "CCPA"
        ]
        
        found_skills = []
        
        # Create a combined pattern to find skills
        pattern = r'\b(?:' + '|'.join(tech_skills) + r')\b'
        
        # Find all skills in the text
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            skill = match.group(0)
            # Check if we already found this skill
            if not any(s["name"].lower() == skill.lower() for s in found_skills):
                found_skills.append({
                    "name": skill,
                    "confidence": 0.9  # Default confidence
                })
        
        return found_skills
    
    def _extract_work_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience from resume text"""
        import re
        
        # Split the text into sections
        sections = self._extract_sections(text)
        
        # Look for a work experience section
        work_text = ""
        for section_name, section_content in sections.items():
            section_name_lower = section_name.lower()
            if any(kw in section_name_lower for kw in ["experience", "employment", "work", "professional"]):
                work_text = section_content
                break
        
        # If no specific section found, use the whole text
        if not work_text:
            work_text = text
        
        # Find date patterns that likely indicate work experiences
        date_pattern = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*(?:-|–|to)\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*(?:-|–|to)\s*(?:Present|Current|Now)|(?:19|20)\d{2}\s*(?:-|–|to)\s*(?:19|20)\d{2}|(?:19|20)\d{2}\s*(?:-|–|to)\s*(?:Present|Current|Now)'
        date_matches = re.finditer(date_pattern, work_text, re.IGNORECASE)
        
        experiences = []
        for match in date_matches:
            # Extract the date range
            date_range = match.group(0)
            
            # Try to find company and title around the date
            context_start = max(0, match.start() - 100)
            context_end = min(len(work_text), match.end() + 300)
            context = work_text[context_start:context_end]
            
            # Extract title and company using heuristics
            title = ""
            company = ""
            
            # Find company - often near the date with common indicators
            company_indicators = ["at", "with", "-", "–", "|", ","]
            for indicator in company_indicators:
                if indicator in context:
                    parts = context.split(indicator, 1)
                    if len(parts) > 1:
                        company_candidates = parts[1].split('\n', 1)[0].strip()
                        if len(company_candidates) < 50:  # Reasonable company name length
                            company = company_candidates
                            break
            
            # Try to extract job title - often before company
            if company and "at" in context:
                title_parts = context.split("at " + company)[0].split('\n')
                if title_parts:
                    title = title_parts[-1].strip()
            
            # If we couldn't extract it, try other methods
            if not title:
                # Look for title indicators
                title_indicators = ["Senior", "Lead", "Principal", "Engineer", "Developer", "Architect", 
                                   "Manager", "Director", "Consultant", "Specialist", "Analyst"]
                for indicator in title_indicators:
                    if indicator in context:
                        # Find the line containing the indicator
                        lines = context.split('\n')
                        for line in lines:
                            if indicator in line and len(line.strip()) < 60:
                                title = line.strip()
                                break
                        if title:
                            break
            
            # Process the date range
            start_date = ""
            end_date = ""
            if "-" in date_range or "–" in date_range or "to" in date_range:
                split_char = "-" if "-" in date_range else "–" if "–" in date_range else "to"
                dates = date_range.split(split_char)
                if len(dates) == 2:
                    start_date = dates[0].strip()
                    end_date = dates[1].strip()
            
            # Extract job description - text after the title and company, before next date
            description = ""
            if title and company:
                # Try to find where the description starts
                title_company = f"{title} at {company}"
                if title_company in context:
                    desc_start = context.find(title_company) + len(title_company)
                    # Try to find where it ends (next date or job title)
                    next_match = re.search(date_pattern, context[desc_start:])
                    if next_match:
                        desc_end = desc_start + next_match.start()
                        description = context[desc_start:desc_end].strip()
                    else:
                        description = context[desc_start:].strip()
            
            # If we have at least some basic info, add it
            if (title or company) and (start_date or description):
                experiences.append({
                    "job_title": title,
                    "company": company,
                    "start_date": start_date,
                    "end_date": end_date,
                    "description": description[:500],  # Limit description length
                    "responsibilities": []  # We won't try to parse individual responsibilities
                })
        
        return experiences
    
    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        """Extract education from resume text"""
        import re
        
        # Split the text into sections
        sections = self._extract_sections(text)
        
        # Look for an education section
        education_text = ""
        for section_name, section_content in sections.items():
            section_name_lower = section_name.lower()
            if any(kw in section_name_lower for kw in ["education", "academic", "university", "college", "degree"]):
                education_text = section_content
                break
        
        # If no specific section found, use the whole text
        if not education_text:
            education_text = text
        
        # Look for education indicators
        education_indicators = [
            "Bachelor", "Master", "PhD", "Doctor", "BSc", "MSc", "BA", "MA", "MBA", "B.S.", "M.S.",
            "University", "College", "Institute", "School of", "Academy"
        ]
        
        # Find degree patterns
        degree_pattern = r'(?:Bachelor|Master|PhD|Doctor|BSc|MSc|BA|MA|MBA|B\.S\.|M\.S\.|B\.A\.|M\.A\.|Associate)(?:\s+(?:of|in))?\s+(?:Science|Arts|Engineering|Business|Administration|Computer Science|Information Technology|IT|CS)'
        degree_matches = re.finditer(degree_pattern, education_text, re.IGNORECASE)
        
        education_entries = []
        
        for match in degree_matches:
            # Extract the degree
            degree = match.group(0)
            
            # Look for context around the degree
            context_start = max(0, match.start() - 100)
            context_end = min(len(education_text), match.end() + 200)
            context = education_text[context_start:context_end]
            
            # Try to extract institution
            institution = ""
            for indicator in education_indicators:
                if indicator in context:
                    # Find the line containing the indicator
                    lines = context.split('\n')
                    for line in lines:
                        if indicator in line and "degree" not in line.lower() and len(line.strip()) < 100:
                            institution = line.strip()
                            break
                    if institution:
                        break
            
            # Look for dates in the context
            date_pattern = r'(?:19|20)\d{2}\s*(?:-|–|to)\s*(?:19|20)\d{2}|(?:19|20)\d{2}\s*(?:-|–|to)\s*(?:Present|Current|Now)|(?:19|20)\d{2}'
            date_match = re.search(date_pattern, context)
            
            start_date = ""
            end_date = ""
            
            if date_match:
                date_str = date_match.group(0)
                if "-" in date_str or "–" in date_str or "to" in date_str:
                    split_char = "-" if "-" in date_str else "–" if "–" in date_str else "to"
                    dates = date_str.split(split_char)
                    if len(dates) == 2:
                        start_date = dates[0].strip()
                        end_date = dates[1].strip()
                else:
                    # Single year, probably graduation year
                    end_date = date_str.strip()
            
            # Try to extract field of study
            field_of_study = ""
            if degree:
                # Try to extract field from degree
                degree_parts = degree.split(" in ", 1)
                if len(degree_parts) > 1:
                    field_of_study = degree_parts[1].strip()
                elif "of " in degree:
                    degree_parts = degree.split(" of ", 1)
                    if len(degree_parts) > 1:
                        field_of_study = degree_parts[1].strip()
            
            # If we have at least a degree or institution, add it
            if degree or institution:
                education_entries.append({
                    "institution": institution,
                    "degree": degree,
                    "field_of_study": field_of_study,
                    "start_date": start_date,
                    "end_date": end_date,
                    "gpa": ""  # We won't try to extract GPA
                })
        
        return education_entries
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract sections from resume text"""
        import re
        
        # Common section headings in resumes
        section_keywords = [
            "Education", "Experience", "Employment", "Work Experience", "Professional Experience",
            "Skills", "Technical Skills", "Projects", "Professional Projects", "Certifications",
            "Awards", "Achievements", "Languages", "Interests", "Volunteer", "Publications",
            "Summary", "Profile", "Objective", "References", "Additional Information"
        ]
        
        # Create regex pattern for section headings
        section_pattern = r'(?:^|\n)(?:\s*)((?:' + '|'.join(section_keywords) + r')(?:\s*):?)(?:\s*)(?:\n|$)'
        
        # Find all potential section headings
        matches = list(re.finditer(section_pattern, text, re.IGNORECASE))
        
        sections = {}
        
        # Process each section
        for i, match in enumerate(matches):
            # Section name is the matched text
            section_name = match.group(1).strip()
            
            # Section start is right after the heading
            section_start = match.end()
            
            # Section end is either the start of the next section or the end of the text
            if i < len(matches) - 1:
                section_end = matches[i + 1].start()
            else:
                section_end = len(text)
            
            # Extract the section content
            section_content = text[section_start:section_end].strip()
            
            # Save the section
            sections[section_name] = section_content
        
        # If no sections were found, create a single section with all text
        if not sections:
            sections["Full Text"] = text
            
        return sections
# Create singleton instance
document_intelligence = DocumentIntelligenceService()