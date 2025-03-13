# app/services/role_analyzers/frontend_analyzer.py
from app.services.role_analyzers.base_analyzer import BaseRoleAnalyzer
from typing import Dict, Any, List
import os
import json
import logging

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