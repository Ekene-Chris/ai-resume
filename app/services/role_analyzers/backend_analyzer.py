# app/services/role_analyzers/backend_analyzer.py
from app.services.role_analyzers.base_analyzer import BaseRoleAnalyzer
from typing import Dict, Any, List
import os
import json
import logging
import re

logger = logging.getLogger(__name__)

class BackendRoleAnalyzer(BaseRoleAnalyzer):
    """Analyzer specifically for Backend Developer roles"""
    
    def __init__(self, experience_level: str):
        super().__init__("Backend Developer", experience_level)
    
    def _load_role_requirements(self) -> Dict[str, Any]:
        """Load backend role-specific requirements"""
        try:
            # First try to load from file
            role_file = f"app/data/roles/backend_developer.json"
            
            if os.path.exists(role_file):
                with open(role_file, "r") as f:
                    role_data = json.load(f)
                    return role_data.get(self.experience_level, {})
        except Exception as e:
            logger.warning(f"Could not load role file: {str(e)}")
        
        # Fallback to hardcoded requirements
        return {
            "junior": {
                "core_skills": [
                    "Python/JavaScript/Java/.NET", "Basic API Development",
                    "SQL Fundamentals", "Git Version Control",
                    "Basic Authentication", "Data Validation",
                    "Basic Testing", "HTTP/REST"
                ],
                "preferred_skills": [
                    "Node.js/Django/Spring/Express", "NoSQL Databases",
                    "Docker Basics", "CI/CD Fundamentals",
                    "Basic Cloud (AWS/Azure/GCP)", "Agile Methodologies"
                ],
                "responsibilities": [
                    "Develop basic API endpoints",
                    "Implement database queries and operations",
                    "Debug and fix issues in code",
                    "Write unit tests for code",
                    "Document code and functionalities",
                    "Collaborate with frontend and other developers"
                ]
            },
            "mid": {
                "core_skills": [
                    "Advanced Language Proficiency", "Database Design",
                    "API Architecture", "Authentication/Authorization",
                    "Caching Strategies", "Error Handling",
                    "Performance Optimization", "Message Queues",
                    "Containerization", "CI/CD"
                ],
                "preferred_skills": [
                    "Microservices", "Cloud Services",
                    "Infrastructure as Code", "Event-Driven Architecture",
                    "GraphQL", "Monitoring Tools",
                    "Security Best Practices", "Agile/Scrum"
                ],
                "responsibilities": [
                    "Design and implement complex APIs",
                    "Optimize database performance",
                    "Develop scalable backend services",
                    "Implement security best practices",
                    "Create comprehensive test suites",
                    "Review code and mentor junior developers",
                    "Deploy and monitor applications",
                    "Collaborate with cross-functional teams"
                ]
            },
            "senior": {
                "core_skills": [
                    "System Architecture", "Scalability Patterns",
                    "Distributed Systems", "Advanced Database Design",
                    "Performance Tuning", "Security Architecture",
                    "Technical Leadership", "DevOps Integration",
                    "API Gateway/Service Mesh"
                ],
                "preferred_skills": [
                    "Multiple Programming Paradigms", "Cloud-Native Development",
                    "Serverless Architecture", "Data Engineering",
                    "Chaos Engineering", "SRE Practices",
                    "Technical Mentorship", "System Design"
                ],
                "responsibilities": [
                    "Architect complex backend systems",
                    "Lead technical implementation of major features",
                    "Establish coding standards and best practices",
                    "Make key technology decisions",
                    "Design for performance, scalability, and reliability",
                    "Mentor and grow engineering teams",
                    "Collaborate with product and business stakeholders",
                    "Drive technical vision and innovation"
                ]
            }
        }.get(self.experience_level, {})
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for backend role analysis"""
        return f"""You are an expert technical recruiter specializing in Backend Developer roles with deep knowledge of server-side technologies, APIs, databases, and system architecture.

Your task is to analyze a resume for a {self.experience_level}-level Backend Developer position and provide detailed, actionable feedback.

For a {self.experience_level}-level Backend Developer, evaluate for these key areas:
1. Programming language proficiency and backend frameworks
2. Database knowledge and experience
3. API design and implementation expertise
4. System architecture and scalability understanding
5. DevOps and deployment knowledge
6. Security practices and implementation
7. Performance optimization experience
8. Testing and quality assurance approach

When analyzing the resume, consider:
- For junior roles: Focus on fundamentals, basic API implementation, and database skills
- For mid-level roles: Look for architecture decisions, complex implementations, and performance considerations
- For senior roles: Evaluate system design, scalability solutions, and technical leadership

Your analysis should be thorough, constructive, and tailored to backend development specifically.

The expected JSON format for your response must be:
{{
  "overall_score": <0-100 integer>,
  "categories": [
    {{
      "name": "Programming & Frameworks",
      "score": <0-100 integer>,
      "feedback": "<specific feedback on backend programming skills>",
      "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
    }},
    {{
      "name": "Database & Data Management",
      "score": <0-100 integer>,
      "feedback": "<specific feedback on database experience>",
      "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
    }},
    {{
      "name": "API Design & Implementation",
      "score": <0-100 integer>,
      "feedback": "<specific feedback on API experience>",
      "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
    }},
    {{
      "name": "Architecture & Scalability",
      "score": <0-100 integer>,
      "feedback": "<specific feedback on architecture experience>",
      "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
    }},
    {{
      "name": "DevOps & Deployment",
      "score": <0-100 integer>,
      "feedback": "<specific feedback on DevOps experience>",
      "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
    }}
  ],
  "keyword_analysis": {{
    "present": ["<backend keyword 1>", "<backend keyword 2>", ...],
    "missing": ["<missing backend keyword 1>", "<missing backend keyword 2>", ...],
    "recommended": ["<recommended backend keyword 1>", "<recommended backend keyword 2>", ...]
  }},
  "matrix_alignment": {{
    "current_level": "<current backend skill level assessment>",
    "target_level": "{self.experience_level}",
    "gap_areas": ["<gap area 1>", "<gap area 2>", ...]
  }},
  "summary": "<concise summary of overall backend developer analysis>"
}}"""
    
    def get_user_prompt(self, resume_data: Dict[str, Any]) -> str:
        """Get the user prompt for the backend role analysis"""
        # Extract relevant data from the resume
        contact_info = resume_data.get("contact_info", {})
        name = contact_info.get("name", "")
        work_experience = self.format_work_experience(resume_data.get("work_experience", []))
        education = self.format_education(resume_data.get("education", []))
        skills = self.format_skills_list(resume_data.get("skills", []))
        raw_text = resume_data.get("raw_text", "")
        years_exp = self.extract_years_of_experience(resume_data.get("work_experience", []))
        
        # Get backend-specific technologies
        backend_techs = [tech for tech in self.extract_technologies(resume_data) 
                         if self._is_backend_tech(tech)]
        
        # Extract backend specific information
        database_experience = self._extract_database_experience(resume_data)
        architecture_experience = self._extract_architecture_experience(resume_data)
        
        # Format the role requirements
        role_req_text = self._format_role_requirements()
        
        return f"""Analyze this resume for a {self.role_name} position at {self.experience_level} level:

CANDIDATE INFO:
Name: {name}
Estimated Years of Experience: {years_exp}
Identified Backend Technologies: {', '.join(backend_techs)}

TARGET ROLE: {self.role_name}
EXPERIENCE LEVEL: {self.experience_level}

ROLE REQUIREMENTS:
{role_req_text}

SKILLS FROM RESUME:
{skills}

WORK EXPERIENCE:
{work_experience}

EDUCATION:
{education}

DATABASE EXPERIENCE:
{database_experience}

ARCHITECTURE EXPERIENCE:
{architecture_experience}

ADDITIONAL RESUME CONTENT:
{raw_text[:2000]}  # Limiting to first 2000 chars of raw text to avoid token limits

Based on this information, provide a comprehensive analysis of this candidate for a {self.experience_level}-level {self.role_name} position. Focus specifically on backend development skills, API design, database knowledge, system architecture, and scalability experience.

Provide your analysis in the specified JSON format only. No additional text or explanations outside the JSON structure.
"""
    
    def create_analysis_payload(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a structured payload for backend developer analysis"""
        # Extract core data
        contact_info = resume_data.get("contact_info", {})
        name = contact_info.get("name", "")
        email = contact_info.get("email", "")
        
        # Extract experience metrics
        years_exp = self.extract_years_of_experience(resume_data.get("work_experience", []))
        detected_level = self.estimate_experience_level(years_exp)
        
        # Extract technologies with focus on backend
        all_techs = self.extract_technologies(resume_data)
        backend_techs = [tech for tech in all_techs if self._is_backend_tech(tech)]
        frontend_techs = [tech for tech in all_techs if self._is_frontend_tech(tech)]
        
        # Identify languages and frameworks
        languages = self._identify_programming_languages(all_techs, resume_data.get("raw_text", ""))
        frameworks = self._identify_backend_frameworks(all_techs, resume_data.get("raw_text", ""))
        databases = self._identify_databases(all_techs, resume_data.get("raw_text", ""))
        
        # Create structured payload
        return {
            "candidate": {
                "name": name,
                "email": email,
                "years_experience": years_exp,
                "detected_level": detected_level
            },
            "role": {
                "title": self.role_name,
                "target_level": self.experience_level,
                "requirements": self.role_requirements
            },
            "skills_analysis": {
                "backend_technologies": backend_techs,
                "frontend_technologies": frontend_techs,
                "programming_languages": languages,
                "frameworks": frameworks,
                "databases": databases,
                "missing_core_skills": self._identify_missing_skills(backend_techs)
            },
            "experience_analysis": {
                "has_api_experience": self._has_api_experience(resume_data),
                "has_database_experience": bool(databases),
                "has_cloud_experience": self._has_cloud_experience(resume_data),
                "has_microservices_experience": self._has_microservices_experience(resume_data),
                "has_security_experience": self._has_security_experience(resume_data),
                "database_experience": self._extract_database_experience(resume_data),
                "architecture_experience": self._extract_architecture_experience(resume_data)
            }
        }
    
    def _format_role_requirements(self) -> str:
        """Format backend role requirements into readable text"""
        text = ""
        
        if "core_skills" in self.role_requirements:
            text += "Core Backend Skills Required:\n"
            for skill in self.role_requirements["core_skills"]:
                text += f"- {skill}\n"
            text += "\n"
        
        if "preferred_skills" in self.role_requirements:
            text += "Preferred Backend Skills:\n"
            for skill in self.role_requirements["preferred_skills"]:
                text += f"- {skill}\n"
            text += "\n"
        
        if "responsibilities" in self.role_requirements:
            text += "Backend Developer Responsibilities:\n"
            for resp in self.role_requirements["responsibilities"]:
                text += f"- {resp}\n"
            text += "\n"
        
        return text
    
    def _is_backend_tech(self, tech: str) -> bool:
        """Determine if a technology is backend-related"""
        backend_techs = {
            "python", "java", "c#", "go", "rust", "php", "ruby", "node.js",
            "django", "flask", "fastapi", "spring", "spring boot", ".net", "express",
            "asp.net", "laravel", "ruby on rails", "nestjs",
            "sql", "mysql", "postgresql", "oracle", "sql server", "sqlite",
            "mongodb", "cassandra", "dynamodb", "redis", "couchdb", "neo4j",
            "api", "rest", "graphql", "grpc", "soap", "microservices",
            "docker", "kubernetes", "aws", "azure", "gcp", "heroku", "digitalocean",
            "ci/cd", "jenkins", "github actions", "gitlab ci", "circleci",
            "rabbitmq", "kafka", "activemq", "sqs", "pubsub",
            "nginx", "apache", "iis", "load balancing", "caching",
            "elasticsearch", "solr", "serverless", "lambda", "authentication",
            "oauth", "jwt", "cors", "security", "hashing", "encryption"
        }
        return tech.lower() in backend_techs
    
    def _is_frontend_tech(self, tech: str) -> bool:
        """Determine if a technology is frontend-related"""
        frontend_techs = {
            "html", "html5", "css", "css3", "javascript", "typescript",
            "react", "angular", "vue", "svelte", "jquery",
            "sass", "less", "bootstrap", "tailwind", "material-ui",
            "webpack", "babel", "rollup", "vite", "parcel",
            "jest", "cypress", "selenium", "puppeteer", "storybook"
        }
        return tech.lower() in frontend_techs
    
    def _identify_programming_languages(self, technologies: List[str], raw_text: str) -> List[str]:
        """Identify which programming languages are mentioned in the resume"""
        languages = []
        
        language_keywords = [
            "python", "java", "javascript", "typescript", "c#", "c++", "go", "golang",
            "rust", "php", "ruby", "swift", "kotlin", "scala", "perl", "r", "dart",
            "objective-c", "clojure", "haskell", "erlang", "elixir", "f#", "vb.net"
        ]
        
        for lang in language_keywords:
            if any(lang.lower() in tech.lower() for tech in technologies) or lang.lower() in raw_text.lower():
                # Normalize some language names
                if lang == "golang":
                    languages.append("go")
                else:
                    languages.append(lang)
        
        return list(set(languages))  # Remove duplicates
    
    def _identify_backend_frameworks(self, technologies: List[str], raw_text: str) -> List[str]:
        """Identify which backend frameworks are mentioned in the resume"""
        frameworks = []
        
        framework_keywords = {
            "django": ["django", "drf", "django rest framework"],
            "flask": ["flask", "flask-restful"],
            "fastapi": ["fastapi", "fast api"],
            "spring": ["spring", "spring boot", "spring framework", "spring mvc", "spring cloud"],
            "express": ["express", "express.js", "expressjs"],
            "asp.net": ["asp.net", "asp.net core", "asp.net mvc", ".net core"],
            "laravel": ["laravel", "laravel framework"],
            "rails": ["rails", "ruby on rails", "ror"],
            "nestjs": ["nestjs", "nest.js"],
            "phoenix": ["phoenix", "phoenix framework"],
            "nodejs": ["node.js", "nodejs", "node"],
            "dotnet": [".net", "dotnet", ".net framework"]
        }