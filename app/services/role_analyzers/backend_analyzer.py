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
    def _identify_databases(self, technologies: List[str], raw_text: str) -> List[str]:
        """Identify which databases are mentioned in the resume"""
        databases = []
        
        database_keywords = {
            "mysql": ["mysql", "my sql"],
            "postgresql": ["postgresql", "postgres", "psql"],
            "mongodb": ["mongodb", "mongo", "nosql"],
            "sqlite": ["sqlite", "sqlite3"],
            "oracle": ["oracle", "oracle db", "plsql"],
            "sql_server": ["sql server", "mssql", "t-sql"],
            "dynamodb": ["dynamodb", "dynamo", "aws dynamodb"],
            "cassandra": ["cassandra"],
            "redis": ["redis", "key-value store"],
            "couchdb": ["couchdb", "couch"],
            "neo4j": ["neo4j", "graph database", "graph db"],
            "elasticsearch": ["elasticsearch", "elastic", "elk"],
            "mariadb": ["mariadb", "maria"],
            "firebase": ["firebase", "firestore", "realtime database"],
            "cosmosdb": ["cosmosdb", "cosmos", "azure cosmos"]
        }
        
        for db, keywords in database_keywords.items():
            for keyword in keywords:
                if any(keyword.lower() in tech.lower() for tech in technologies) or keyword.lower() in raw_text.lower():
                    databases.append(db)
                    break
        
        # Also check for generic SQL knowledge
        if "sql" in raw_text.lower() and not any(db in databases for db in ["mysql", "postgresql", "oracle", "sql_server", "sqlite", "mariadb"]):
            databases.append("sql_generic")
        
        return list(set(databases))  # Remove duplicates
    def _identify_missing_skills(self, technologies: List[str]) -> List[str]:
        """Identify missing core skills for the target role"""
        missing_skills = []
        
        if "core_skills" in self.role_requirements:
            for skill in self.role_requirements["core_skills"]:
                # Check if any technology in the resume matches this skill
                if not any(self._skill_match(skill, tech) for tech in technologies):
                    missing_skills.append(skill)
        
        return missing_skills

    def _skill_match(self, skill: str, tech: str) -> bool:
        """Check if a skill and technology match, handling compound skills"""
        # Handle compound skills like "Python/JavaScript/Java/.NET"
        if "/" in skill:
            skill_parts = skill.lower().split("/")
            return any(part in tech.lower() or tech.lower() in part for part in skill_parts)
        
        return skill.lower() in tech.lower() or tech.lower() in skill.lower()
        
    def _has_api_experience(self, resume_data: Dict[str, Any]) -> bool:
        """Check if the resume mentions API experience"""
        api_keywords = ["api", "rest", "graphql", "endpoint", "http", "request", "response", 
                        "soap", "swagger", "openapi", "postman", "grpc"]
        
        raw_text = resume_data.get("raw_text", "").lower()
        
        return any(keyword in raw_text for keyword in api_keywords)

    def _has_cloud_experience(self, resume_data: Dict[str, Any]) -> bool:
        """Check if the resume mentions cloud experience"""
        cloud_keywords = ["aws", "amazon web services", "ec2", "s3", "lambda",
                        "azure", "microsoft azure", "gcp", "google cloud", 
                        "cloud", "serverless", "iaas", "paas", "saas"]
        
        raw_text = resume_data.get("raw_text", "").lower()
        
        return any(keyword in raw_text for keyword in cloud_keywords)

    def _has_microservices_experience(self, resume_data: Dict[str, Any]) -> bool:
        """Check if the resume mentions microservices experience"""
        microservices_keywords = ["microservice", "service-oriented", "soa", "distributed system",
                                "service mesh", "api gateway", "container", "docker", "kubernetes"]
        
        raw_text = resume_data.get("raw_text", "").lower()
        
        return any(keyword in raw_text for keyword in microservices_keywords)

    def _has_security_experience(self, resume_data: Dict[str, Any]) -> bool:
        """Check if the resume mentions security experience"""
        security_keywords = ["security", "authentication", "authorization", "oauth", 
                            "jwt", "encryption", "csrf", "xss", "sql injection",
                            "vulnerability", "penetration test", "pen test", "owasp"]
        
        raw_text = resume_data.get("raw_text", "").lower()
        
        return any(keyword in raw_text for keyword in security_keywords)

    def _extract_database_experience(self, resume_data: Dict[str, Any]) -> str:
        """Extract database-specific experience from the resume"""
        raw_text = resume_data.get("raw_text", "").lower()
        sections = resume_data.get("sections", {})
        
        # Database related keywords to look for
        db_keywords = ["database", "sql", "nosql", "mysql", "postgresql", "mongodb",
                    "oracle", "sqlserver", "redis", "elasticsearch", "dynamodb",
                    "cassandra", "neo4j", "sqlite", "query", "schema", "normalization",
                    "index", "join", "transaction", "acid", "orm"]
        
        # Look for paragraphs with database mentions
        db_experience = ""
        
        # First look in work experiences
        work_experiences = resume_data.get("work_experience", [])
        for exp in work_experiences:
            description = exp.get("description", "").lower()
            if any(keyword in description for keyword in db_keywords):
                db_experience += f"At {exp.get('company', '')}: {exp.get('description', '')}\n\n"
                
            # Also check responsibilities
            responsibilities = exp.get("responsibilities", [])
            for resp in responsibilities:
                if any(keyword in resp.lower() for keyword in db_keywords):
                    db_experience += f"At {exp.get('company', '')}: {resp}\n"
        
        # If nothing found in experiences, check entire raw text
        if not db_experience:
            # Find sentences containing database keywords
            sentences = re.split(r'[.!?]+', raw_text)
            for sentence in sentences:
                if any(keyword in sentence for keyword in db_keywords):
                    db_experience += sentence.strip() + ".\n"
        
        if not db_experience:
            return "No specific database experience identified."
        
        return db_experience

    def _extract_architecture_experience(self, resume_data: Dict[str, Any]) -> str:
        """Extract architecture-specific experience from the resume"""
        raw_text = resume_data.get("raw_text", "").lower()
        sections = resume_data.get("sections", {})
        
        # Architecture related keywords to look for
        arch_keywords = ["architecture", "design pattern", "mvc", "mvvm", "microservice",
                        "monolith", "scalability", "high availability", "fault tolerance",
                        "distributed system", "api gateway", "load balancing", "caching",
                        "system design", "performance", "optimization", "refactoring"]
        
        # Look for paragraphs with architecture mentions
        arch_experience = ""
        
        # First look in work experiences
        work_experiences = resume_data.get("work_experience", [])
        for exp in work_experiences:
            description = exp.get("description", "").lower()
            if any(keyword in description for keyword in arch_keywords):
                arch_experience += f"At {exp.get('company', '')}: {exp.get('description', '')}\n\n"
                
            # Also check responsibilities
            responsibilities = exp.get("responsibilities", [])
            for resp in responsibilities:
                if any(keyword in resp.lower() for keyword in arch_keywords):
                    arch_experience += f"At {exp.get('company', '')}: {resp}\n"
        
        # If nothing found in experiences, check entire raw text
        if not arch_experience:
            # Find sentences containing architecture keywords
            sentences = re.split(r'[.!?]+', raw_text)
            for sentence in sentences:
                if any(keyword in sentence for keyword in arch_keywords):
                    arch_experience += sentence.strip() + ".\n"
        
        if not arch_experience:
            return "No specific architecture experience identified."
        
        return arch_experience