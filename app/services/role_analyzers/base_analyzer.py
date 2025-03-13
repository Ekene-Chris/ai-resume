# app/services/role_analyzers/base_analyzer.py
from typing import Dict, Any, List, Optional
import logging
import json
import re
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseRoleAnalyzer(ABC):
    """Base class for role-specific resume analyzers"""
    
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
    
    def extract_years_of_experience(self, experiences: List[Dict[str, Any]]) -> float:
        """
        Attempt to calculate total years of experience from work history
        Returns a float representing years of experience
        """
        import re
        from datetime import datetime
        
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
        # Start with extracted skills
        tech_keywords = set([skill.get("name", "").lower() for skill in resume_data.get("skills", []) if skill.get("name")])
        
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