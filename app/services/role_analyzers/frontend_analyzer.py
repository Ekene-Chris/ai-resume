# app/services/role_analyzers/frontend_analyzer.py
from app.services.role_analyzers.base_analyzer import BaseRoleAnalyzer
from typing import Dict, Any, List
import os
import json
import logging
import re

logger = logging.getLogger(__name__)

class FrontendRoleAnalyzer(BaseRoleAnalyzer):
    """Analyzer specifically for Frontend Developer roles"""
    
    def __init__(self, experience_level: str):
        super().__init__("Frontend Developer", experience_level)
    
    def _load_role_requirements(self) -> Dict[str, Any]:
        """Load frontend role-specific requirements"""
        try:
            # First try to load from file
            role_file = f"app/data/roles/frontend_developer.json"
            
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
                    "HTML5", "CSS3", "JavaScript", "Responsive Design", 
                    "Basic React/Angular/Vue", "Version Control (Git)",
                    "Browser Dev Tools", "CSS Frameworks (Bootstrap/Tailwind)"
                ],
                "preferred_skills": [
                    "TypeScript", "SASS/LESS", "Basic Testing", "Figma/Design Tools",
                    "Accessibility Knowledge", "Basic Performance Optimization"
                ],
                "responsibilities": [
                    "Implement UI components following designs",
                    "Fix bugs and improve UI performance",
                    "Write clean, maintainable code",
                    "Collaborate with designers and backend developers",
                    "Test and debug across browsers"
                ]
            },
            "mid": {
                "core_skills": [
                    "Advanced JavaScript", "React/Angular/Vue Proficiency", 
                    "State Management", "REST/GraphQL APIs", "Jest/Testing Library",
                    "Performance Optimization", "Responsive/Mobile Design",
                    "Webpack/Build Tools", "TypeScript"
                ],
                "preferred_skills": [
                    "CI/CD", "SSR/SSG", "Advanced CSS", "Animation", 
                    "Design Systems", "Cross-browser Compatibility",
                    "Web Accessibility (WCAG)", "SEO Fundamentals"
                ],
                "responsibilities": [
                    "Architect frontend applications",
                    "Build reusable component libraries",
                    "Implement complex UI interactions",
                    "Optimize application performance",
                    "Mentor junior developers",
                    "Work closely with UX/UI designers",
                    "Integrate with backend APIs"
                ]
            },
            "senior": {
                "core_skills": [
                    "Frontend Architecture", "Advanced Framework Knowledge",
                    "Performance Optimization", "Scalable Applications",
                    "Testing Strategies", "Technical Leadership",
                    "CI/CD", "Security Best Practices"
                ],
                "preferred_skills": [
                    "Microfrontends", "Design Systems", "Advanced TypeScript",
                    "WebGL/Canvas", "PWAs", "Internationalization",
                    "Accessibility Expertise", "Cross-platform Development"
                ],
                "responsibilities": [
                    "Design complex frontend architectures",
                    "Establish coding standards and best practices",
                    "Lead technical implementation of major features",
                    "Mentor and grow engineering teams",
                    "Evaluate and select technologies",
                    "Drive performance and scalability improvements",
                    "Collaborate with product and design teams",
                    "Make high-level technical decisions"
                ]
            }
        }.get(self.experience_level, {})
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for frontend role analysis"""
        return f"""You are an expert technical recruiter specializing in Frontend Developer roles with deep knowledge of web technologies, modern frameworks, and UI/UX implementation.

Your task is to analyze a resume for a {self.experience_level}-level Frontend Developer position and provide detailed, actionable feedback.

For a {self.experience_level}-level Frontend Developer, evaluate for these key areas:
1. Technical skills (frameworks, languages, tools)
2. Project experience and complexity
3. UI/UX sensibility and implementation skills
4. Code quality indicators and best practices
5. Responsive design and cross-browser expertise
6. Performance optimization knowledge
7. Testing experience and approaches
8. Collaboration with designers and backend developers

When analyzing the resume, consider:
- For junior roles: Focus on fundamentals, learning potential, and basic projects
- For mid-level roles: Look for framework proficiency, state management, and component design
- For senior roles: Evaluate architecture decisions, scalability approaches, and technical leadership

Your analysis should be thorough, constructive, and tailored to frontend development specifically.

The expected JSON format for your response must be:
{{
  "overall_score": <0-100 integer>,
  "categories": [
    {{
      "name": "Technical Skills",
      "score": <0-100 integer>,
      "feedback": "<specific feedback on frontend technical skills>",
      "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
    }},
    {{
      "name": "Frontend Projects",
      "score": <0-100 integer>,
      "feedback": "<specific feedback on project experience>",
      "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
    }},
    {{
      "name": "Code Quality & Best Practices",
      "score": <0-100 integer>,
      "feedback": "<specific feedback on code quality indicators>",
      "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
    }},
    {{
      "name": "Responsive Design & Compatibility",
      "score": <0-100 integer>,
      "feedback": "<specific feedback on responsive design experience>",
      "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
    }},
    {{
      "name": "Overall Presentation",
      "score": <0-100 integer>,
      "feedback": "<specific feedback on resume presentation>",
      "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
    }}
  ],
  "keyword_analysis": {{
    "present": ["<frontend keyword 1>", "<frontend keyword 2>", ...],
    "missing": ["<missing frontend keyword 1>", "<missing frontend keyword 2>", ...],
    "recommended": ["<recommended frontend keyword 1>", "<recommended frontend keyword 2>", ...]
  }},
  "matrix_alignment": {{
    "current_level": "<current frontend skill level assessment>",
    "target_level": "{self.experience_level}",
    "gap_areas": ["<gap area 1>", "<gap area 2>", ...]
  }},
  "summary": "<concise summary of overall frontend developer analysis>"
}}"""

    def get_user_prompt(self, resume_data: Dict[str, Any]) -> str:
        """Get the user prompt for the frontend role analysis"""
        # Extract relevant data from the resume
        contact_info = resume_data.get("contact_info", {})
        name = contact_info.get("name", "")
        work_experience = self.format_work_experience(resume_data.get("work_experience", []))
        education = self.format_education(resume_data.get("education", []))
        skills = self.format_skills_list(resume_data.get("skills", []))
        raw_text = resume_data.get("raw_text", "")
        years_exp = self.extract_years_of_experience(resume_data.get("work_experience", []))
        
        # Get frontend-specific technologies
        frontend_techs = [tech for tech in self.extract_technologies(resume_data) 
                         if self._is_frontend_tech(tech)]
        
        # Extract frontend specific information
        ui_ux_experience = self._extract_ui_ux_experience(resume_data)
        framework_experience = self._extract_framework_experience(resume_data)
        
        # Format the role requirements
        role_req_text = self._format_role_requirements()
        
        return f"""Analyze this resume for a {self.role_name} position at {self.experience_level} level:

CANDIDATE INFO:
Name: {name}
Estimated Years of Experience: {years_exp}
Identified Frontend Technologies: {', '.join(frontend_techs)}

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

UI/UX EXPERIENCE:
{ui_ux_experience}

FRAMEWORK EXPERIENCE:
{framework_experience}

ADDITIONAL RESUME CONTENT:
{raw_text[:2000]}  # Limiting to first 2000 chars of raw text to avoid token limits

Based on this information, provide a comprehensive analysis of this candidate for a {self.experience_level}-level {self.role_name} position. Focus specifically on frontend development skills, UI/UX implementation, framework proficiency, and responsive design experience.

Provide your analysis in the specified JSON format only. No additional text or explanations outside the JSON structure.
"""
    
    def create_analysis_payload(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a structured payload for frontend developer analysis"""
        # Extract core data
        contact_info = resume_data.get("contact_info", {})
        name = contact_info.get("name", "")
        email = contact_info.get("email", "")
        
        # Extract experience metrics
        years_exp = self.extract_years_of_experience(resume_data.get("work_experience", []))
        detected_level = self.estimate_experience_level(years_exp)
        
        # Extract technologies with focus on frontend
        all_techs = self.extract_technologies(resume_data)
        frontend_techs = [tech for tech in all_techs if self._is_frontend_tech(tech)]
        backend_techs = [tech for tech in all_techs if self._is_backend_tech(tech)]
        
        # Identify frameworks and languages
        languages = self._identify_frontend_languages(all_techs, resume_data.get("raw_text", ""))
        frameworks = self._identify_frontend_frameworks(all_techs, resume_data.get("raw_text", ""))
        styling_techs = self._identify_styling_technologies(all_techs, resume_data.get("raw_text", ""))
        
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
                "frontend_technologies": frontend_techs,
                "backend_technologies": backend_techs,
                "programming_languages": languages,
                "frameworks": frameworks,
                "styling_technologies": styling_techs,
                "missing_core_skills": self._identify_missing_skills(frontend_techs)
            },
            "experience_analysis": {
                "has_responsive_design_experience": self._has_responsive_design_experience(resume_data),
                "has_framework_experience": bool(frameworks),
                "has_testing_experience": self._has_testing_experience(resume_data),
                "has_ui_ux_experience": self._has_ui_ux_experience(resume_data),
                "ui_ux_experience": self._extract_ui_ux_experience(resume_data),
                "framework_experience": self._extract_framework_experience(resume_data)
            }
        }
        
    def _is_frontend_tech(self, tech: str) -> bool:
        """Determine if a technology is frontend-related"""
        frontend_techs = {
            "html", "html5", "css", "css3", "javascript", "typescript",
            "react", "angular", "vue", "svelte", "jquery", "nextjs", "next.js",
            "gatsby", "nuxt", "ember", "backbone", "alpine", "lit",
            "sass", "scss", "less", "stylus", "bootstrap", "tailwind", "bulma",
            "material-ui", "chakra-ui", "ant design", "styled-components",
            "emotion", "css-in-js", "css modules", "postcss",
            "webpack", "babel", "rollup", "vite", "parcel", "esbuild",
            "jest", "cypress", "testing-library", "enzyme", "mocha", "chai",
            "storybook", "bit", "figma", "sketch", "adobe xd", "invision",
            "responsive design", "mobile-first", "pwa", "web components",
            "accessibility", "a11y", "wcag", "aria", "seo",
            "redux", "mobx", "recoil", "zustand", "jotai", "xstate",
            "graphql", "apollo", "relay", "swr", "react-query", "d3"
        }
        return tech.lower() in frontend_techs
    
    def _is_backend_tech(self, tech: str) -> bool:
        """Determine if a technology is backend-related"""
        backend_techs = {
            "node.js", "express", "django", "flask", "spring", "rails",
            "php", "laravel", "asp.net", "fastapi", "graphql", "rest",
            "sql", "mysql", "postgresql", "mongodb", "firebase", "supabase",
            "redis", "memcached", "elasticsearch", "docker", "kubernetes",
            "aws", "azure", "gcp", "serverless", "lambda", "microservices"
        }
        return tech.lower() in backend_techs
        
    def _identify_frontend_languages(self, technologies: List[str], raw_text: str) -> List[str]:
        """Identify which frontend languages are mentioned in the resume"""
        languages = []
        
        language_keywords = ["javascript", "typescript", "html", "html5", "css", "css3"]
        
        for lang in language_keywords:
            if any(lang.lower() in tech.lower() for tech in technologies) or lang.lower() in raw_text.lower():
                languages.append(lang)
        
        return list(set(languages))  # Remove duplicates
    
    def _identify_frontend_frameworks(self, technologies: List[str], raw_text: str) -> List[str]:
        """Identify which frontend frameworks are mentioned in the resume"""
        frameworks = []
        
        framework_keywords = {
            "react": ["react", "react.js", "reactjs", "create-react-app", "cra"],
            "angular": ["angular", "angularjs", "angular 2+", "ng"],
            "vue": ["vue", "vue.js", "vuejs", "nuxt", "nuxt.js"],
            "svelte": ["svelte", "sveltekit"],
            "next.js": ["next.js", "nextjs", "next"],
            "gatsby": ["gatsby", "gatsbyjs"],
            "jquery": ["jquery", "jquery ui"],
            "backbone": ["backbone", "backbone.js"],
            "ember": ["ember", "ember.js"],
            "lit": ["lit", "lit-element", "lit-html"],
            "alpine": ["alpine", "alpine.js", "alpinejs"]
        }
        
        for framework, keywords in framework_keywords.items():
            for keyword in keywords:
                if any(keyword.lower() in tech.lower() for tech in technologies) or keyword.lower() in raw_text.lower():
                    frameworks.append(framework)
                    break
        
        return list(set(frameworks))  # Remove duplicates
    
    def _identify_styling_technologies(self, technologies: List[str], raw_text: str) -> List[str]:
        """Identify which styling technologies are mentioned in the resume"""
        styling_techs = []
        
        styling_keywords = {
            "sass": ["sass", "scss"],
            "less": ["less"],
            "bootstrap": ["bootstrap"],
            "tailwind": ["tailwind", "tailwindcss"],
            "material-ui": ["material-ui", "mui", "material design"],
            "styled-components": ["styled-components", "styled components"],
            "emotion": ["emotion", "css-in-js"],
            "css-modules": ["css modules", "css-modules"],
            "postcss": ["postcss"],
            "bulma": ["bulma"],
            "chakra-ui": ["chakra", "chakra-ui"],
            "ant-design": ["ant design", "antd"]
        }
        
        for tech, keywords in styling_keywords.items():
            for keyword in keywords:
                if any(keyword.lower() in t.lower() for t in technologies) or keyword.lower() in raw_text.lower():
                    styling_techs.append(tech)
                    break
        
        return list(set(styling_techs))  # Remove duplicates
    
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
        # Handle compound skills like "React/Angular/Vue"
        if "/" in skill:
            skill_parts = skill.lower().split("/")
            return any(part in tech.lower() or tech.lower() in part for part in skill_parts)
        
        return skill.lower() in tech.lower() or tech.lower() in skill.lower()
    
    def _has_responsive_design_experience(self, resume_data: Dict[str, Any]) -> bool:
        """Check if the resume mentions responsive design experience"""
        responsive_keywords = ["responsive", "mobile-first", "mobile friendly", "media queries", 
                              "adaptive", "fluid layout", "flexible", "viewport"]
        
        raw_text = resume_data.get("raw_text", "").lower()
        
        return any(keyword in raw_text for keyword in responsive_keywords)
    
    def _has_testing_experience(self, resume_data: Dict[str, Any]) -> bool:
        """Check if the resume mentions testing experience"""
        testing_keywords = ["test", "jest", "cypress", "selenium", "testing-library", "enzyme",
                           "mocha", "chai", "karma", "jasmine", "protractor", "unit test",
                           "integration test", "e2e", "end-to-end", "tdd", "bdd"]
        
        raw_text = resume_data.get("raw_text", "").lower()
        
        return any(keyword in raw_text for keyword in testing_keywords)
    
    def _has_ui_ux_experience(self, resume_data: Dict[str, Any]) -> bool:
        """Check if the resume mentions UI/UX experience"""
        ui_ux_keywords = ["ui", "ux", "user interface", "user experience", "usability",
                         "wireframe", "prototype", "figma", "sketch", "adobe xd", "invision",
                         "zeplin", "design system", "user-centered", "accessibility"]
        
        raw_text = resume_data.get("raw_text", "").lower()
        
        return any(keyword in raw_text for keyword in ui_ux_keywords)
    
    def _extract_ui_ux_experience(self, resume_data: Dict[str, Any]) -> str:
        """Extract UI/UX-specific experience from the resume"""
        raw_text = resume_data.get("raw_text", "").lower()
        sections = resume_data.get("sections", {})
        
        # UI/UX related keywords to look for
        ui_ux_keywords = ["ui", "ux", "user interface", "user experience", "wireframe", 
                         "prototype", "figma", "sketch", "adobe xd", "invision", "zeplin",
                         "design system", "usability", "user-centered", "accessib"]
        
        # Look for paragraphs with UI/UX mentions
        ui_ux_experience = ""
        
        # First look in work experiences
        work_experiences = resume_data.get("work_experience", [])
        for exp in work_experiences:
            description = exp.get("description", "").lower()
            if any(keyword in description for keyword in ui_ux_keywords):
                ui_ux_experience += f"At {exp.get('company', '')}: {exp.get('description', '')}\n\n"
                
            # Also check responsibilities
            responsibilities = exp.get("responsibilities", [])
            for resp in responsibilities:
                if any(keyword in resp.lower() for keyword in ui_ux_keywords):
                    ui_ux_experience += f"At {exp.get('company', '')}: {resp}\n"
        
        # If nothing found in experiences, check entire raw text
        if not ui_ux_experience:
            # Find sentences containing UI/UX keywords
            sentences = re.split(r'[.!?]+', raw_text)
            for sentence in sentences:
                if any(keyword in sentence for keyword in ui_ux_keywords):
                    ui_ux_experience += sentence.strip() + ".\n"
        
        if not ui_ux_experience:
            return "No specific UI/UX experience identified."
        
        return ui_ux_experience
    
    def _extract_framework_experience(self, resume_data: Dict[str, Any]) -> str:
        """Extract framework-specific experience from the resume"""
        raw_text = resume_data.get("raw_text", "").lower()
        sections = resume_data.get("sections", {})
        
        # Framework related keywords to look for
        framework_keywords = ["react", "angular", "vue", "svelte", "next.js", "gatsby",
                             "jquery", "ember", "backbone", "lit", "alpine", "redux",
                             "mobx", "context api", "hooks", "components"]
        
        # Look for paragraphs with framework mentions
        framework_experience = ""
        
        # First look in work experiences
        work_experiences = resume_data.get("work_experience", [])
        for exp in work_experiences:
            description = exp.get("description", "").lower()
            if any(keyword in description for keyword in framework_keywords):
                framework_experience += f"At {exp.get('company', '')}: {exp.get('description', '')}\n\n"
                
            # Also check responsibilities
            responsibilities = exp.get("responsibilities", [])
            for resp in responsibilities:
                if any(keyword in resp.lower() for keyword in framework_keywords):
                    framework_experience += f"At {exp.get('company', '')}: {resp}\n"
        
        # If nothing found in experiences, check entire raw text
        if not framework_experience:
            # Find sentences containing framework keywords
            sentences = re.split(r'[.!?]+', raw_text)
            for sentence in sentences:
                if any(keyword in sentence for keyword in framework_keywords):
                    framework_experience += sentence.strip() + ".\n"
        
        if not framework_experience:
            return "No specific framework experience identified."
        
        return framework_experience
    
    def _format_role_requirements(self) -> str:
        """Format frontend role requirements into readable text"""
        text = ""
        
        if "core_skills" in self.role_requirements:
            text += "Core Frontend Skills Required:\n"
            for skill in self.role_requirements["core_skills"]:
                text += f"- {skill}\n"
            text += "\n"
        
        if "preferred_skills" in self.role_requirements:
            text += "Preferred Frontend Skills:\n"
            for skill in self.role_requirements["preferred_skills"]:
                text += f"- {skill}\n"
            text += "\n"
        
        if "responsibilities" in self.role_requirements:
            text += "Frontend Developer Responsibilities:\n"
            for resp in self.role_requirements["responsibilities"]:
                text += f"- {resp}\n"
            text += "\n"
        
        return text