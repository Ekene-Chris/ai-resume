# app/services/role_analyzers/base_analyzer.py
from typing import Dict, Any, List, Optional
import logging
import json
import re
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseRoleAnalyzer(ABC):
    """Base class for role-specific resume analyzers with improved raw text handling"""
    
    def __init__(self, role_name: str, experience_level: str):
        self.role_name = role_name
        self.experience_level = experience_level
        self.role_requirements = self._load_role_requirements()
    
    @abstractmethod
    def _load_role_requirements(self) -> Dict[str, Any]:
        """Load role-specific requirements"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for the role-specific analysis"""
        pass
    
    @abstractmethod
    def get_user_prompt(self, resume_data: Dict[str, Any]) -> str:
        """Get the user prompt for the role-specific analysis"""
        pass
    
    @abstractmethod
    def create_analysis_payload(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a structured payload for AI analysis"""
        pass
    
    def format_skills_list(self, skills: List[Dict[str, Any]]) -> str:
        """Format extracted skills into a string"""
        if not skills:
            return "No specific skills data available in resume."
            
        return ", ".join([skill.get("name", "") for skill in skills if skill.get("name")])
    
    def format_work_experience(self, experiences: List[Dict[str, Any]]) -> str:
        """Format work experiences into a structured string"""
        if not experiences:
            return "No work experience data available."
            
        experience_text = ""
        
        for idx, exp in enumerate(experiences):
            job_title = exp.get("job_title", "")
            company = exp.get("company", "")
            start_date = exp.get("start_date", "")
            end_date = exp.get("end_date", "Present") if not exp.get("end_date") else exp.get("end_date")
            description = exp.get("description", "")
            responsibilities = exp.get("responsibilities", [])
            
            experience_text += f"Position {idx + 1}: {job_title} at {company}\n"
            experience_text += f"Duration: {start_date} to {end_date}\n\n"
            
            if description:
                experience_text += f"Description: {description}\n\n"
                
            if responsibilities:
                experience_text += "Responsibilities:\n"
                for resp in responsibilities:
                    experience_text += f"- {resp}\n"
                    
            experience_text += "\n" + "-" * 40 + "\n\n"
        
        return experience_text
    
    def format_education(self, education: List[Dict[str, Any]]) -> str:
        """Format education into a structured string"""
        if not education:
            return "No education data available."
            
        education_text = ""
        
        for idx, edu in enumerate(education):
            institution = edu.get("institution", "")
            degree = edu.get("degree", "")
            field = edu.get("field_of_study", "")
            start_date = edu.get("start_date", "")
            end_date = edu.get("end_date", "")
            
            education_text += f"Education {idx + 1}: {degree} in {field}\n"
            education_text += f"Institution: {institution}\n"
            
            if start_date or end_date:
                education_text += f"Duration: {start_date} to {end_date}\n"
                
            education_text += "\n"
        
        return education_text
    
    def extract_raw_text_for_prompt(self, resume_data: Dict[str, Any], max_length: int = 3000) -> str:
        """Extract and format raw text for the prompt, considering token limits"""
        raw_text = resume_data.get("raw_text", "")
        
        if not raw_text:
            return "No resume text available for analysis."
        
        # Trim to maximum length
        if len(raw_text) > max_length:
            trimmed_text = raw_text[:max_length]
            return trimmed_text + f"\n\n[Note: Resume text has been truncated to {max_length} characters for analysis]"
        
        return raw_text
    
    def extract_years_of_experience(self, experiences: List[Dict[str, Any]]) -> float:
        """
        Attempt to calculate total years of experience from work history
        Returns a float representing years of experience
        """
        import re
        from datetime import datetime
        
        if not experiences:
            # Try to extract from raw text if no structured data
            return 0.0
        
        total_months = 0
        current_year = datetime.now().year
        
        for exp in experiences:
            start_date = exp.get("start_date", "")
            end_date = exp.get("end_date", "Present")
            
            # If end date is "Present" or empty, use current date
            if not end_date or end_date.lower() == "present":
                end_date = f"{current_year}"
            
            # Try to extract years from dates
            start_year_match = re.search(r'(\d{4})', start_date)
            end_year_match = re.search(r'(\d{4})', end_date)
            
            if start_year_match and end_year_match:
                start_year = int(start_year_match.group(1))
                end_year = int(end_year_match.group(1))
                
                # Get months if available
                start_month = 1  # Default to January
                end_month = 12   # Default to December
                
                # Try to extract months
                start_month_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', start_date)
                end_month_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', end_date)
                
                month_map = {
                    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                }
                
                if start_month_match:
                    start_month = month_map.get(start_month_match.group(1), 1)
                    
                if end_month_match:
                    end_month = month_map.get(end_month_match.group(1), 12)
                
                # Calculate months between dates
                months = (end_year - start_year) * 12 + (end_month - start_month)
                total_months += max(0, months)
        
        # Convert months to years
        return round(total_months / 12, 1)
    
    def extract_years_of_experience_from_text(self, raw_text: str) -> float:
        """
        Attempt to calculate years of experience from raw text
        Returns a float representing estimated years of experience
        """
        import re
        
        # Look for common experience indicators
        experience_patterns = [
            r'(\d+)\s*(?:\+)?\s*years?\s+(?:of\s+)?experience',
            r'experience\s*(?:of|:)?\s*(\d+)\s*(?:\+)?\s*years?',
            r'(?:with|having)\s+(\d+)\s*(?:\+)?\s*years?\s+(?:of\s+)?experience',
            r'career\s+(?:spanning|of)\s+(\d+)\s*(?:\+)?\s*years?'
        ]
        
        for pattern in experience_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                try:
                    years = float(match.group(1))
                    return years
                except ValueError:
                    continue
        
        # If no explicit mention, try to estimate from date ranges
        date_ranges = re.findall(r'((?:19|20)\d{2})\s*(?:-|–|to)\s*((?:19|20)\d{2}|present|current|now)', 
                               raw_text, re.IGNORECASE)
        
        if date_ranges:
            total_years = 0
            current_year = datetime.now().year
            
            for start, end in date_ranges:
                try:
                    start_year = int(start)
                    if end.lower() in ['present', 'current', 'now']:
                        end_year = current_year
                    else:
                        end_year = int(end)
                    
                    years = end_year - start_year
                    if 0 < years < 50:  # Sanity check
                        total_years += years
                except ValueError:
                    continue
            
            if total_years > 0:
                return round(total_years, 1)
        
        # If all else fails, make a rough estimate based on content
        # More junior resumes tend to be shorter and mention education more prominently
        education_prominence = raw_text.lower().count('education') / max(1, len(raw_text)) * 10000
        text_length = len(raw_text)
        
        if education_prominence > 20 and text_length < 2000:
            return 1.0  # Likely junior
        elif text_length > 5000:
            return 7.0  # Likely senior
        else:
            return 3.0  # Assume mid-level
    
    def estimate_experience_level(self, years_of_experience: float) -> str:
        """
        Estimate experience level based on years of experience
        Returns "junior", "mid", or "senior"
        """
        if years_of_experience < 2:
            return "junior"
        elif years_of_experience < 5:
            return "mid"
        else:
            return "senior"
    
    def extract_technologies(self, resume_data: Dict[str, Any]) -> List[str]:
        """
        Extract technology keywords from the resume
        Uses both extracted skills and raw text analysis
        """
        # Start with extracted skills if available
        tech_keywords = set()
        
        # Get skills from structured data if available
        skills = resume_data.get("skills", [])
        if skills:
            tech_keywords.update([skill.get("name", "").lower() for skill in skills if skill.get("name")])
        
        # Add common technology keywords from raw text
        raw_text = resume_data.get("raw_text", "").lower()
        
        # Common technology keywords to look for
        common_tech = self._get_common_tech_keywords()
        
        for tech in common_tech:
            if re.search(r'\b' + re.escape(tech.lower()) + r'\b', raw_text):
                tech_keywords.add(tech.lower())
        
        return sorted(list(tech_keywords))
    
    def _get_common_tech_keywords(self) -> List[str]:
        """Get a list of common technology keywords to extract from raw text"""
        return [
            # Languages
            "Python", "JavaScript", "TypeScript", "Java", "C#", "C++", "Go", "Rust",
            "PHP", "Ruby", "Swift", "Kotlin", "Scala", "R", "Perl", "Bash", "Shell",
            
            # Frontend
            "React", "Angular", "Vue", "Next.js", "Redux", "HTML5", "CSS3", "SASS",
            "LESS", "Bootstrap", "Tailwind", "jQuery", "D3.js", "WebGL", "Three.js",
            "Material UI", "Chakra UI", "Styled Components", "Webpack", "Babel",
            "ESLint", "Prettier", "Jest", "Cypress", "Playwright", "Storybook",
            
            # Backend
            "Node.js", "Express", "Django", "Flask", "Spring", "ASP.NET", "Laravel",
            "Rails", "FastAPI", "GraphQL", "REST", "SOAP", "gRPC", "WebSockets",
            
            # Databases
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "DynamoDB", "Cassandra", "Redis",
            "Elasticsearch", "Neo4j", "SQLite", "MariaDB", "Oracle", "MS SQL Server",
            
            # DevOps & Cloud
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Ansible",
            "Jenkins", "CircleCI", "GitHub Actions", "Travis CI", "ArgoCD", "Helm",
            "Prometheus", "Grafana", "ELK", "Datadog", "New Relic", "CI/CD",
            "Infrastructure as Code", "Linux", "Apache", "Nginx", "Serverless",
            "Lambda", "EC2", "S3", "RDS", "EKS", "ECS", "CloudFormation",
            
            # Misc
            "Git", "SVN", "Jira", "Confluence", "Scrum", "Agile", "Kanban",
            "TDD", "BDD", "Microservices", "API Gateway", "Service Mesh", "Istio",
            "OAuth", "JWT", "SAML", "Security", "Performance", "Scalability",
            "High Availability", "Fault Tolerance", "Caching", "Load Balancing",
            "CDN", "Monitoring", "Logging", "Analytics", "Big Data", "Machine Learning"
        ]