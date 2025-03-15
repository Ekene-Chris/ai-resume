# app/prompt_templates.py - Customized for Ekene Chris and Teleios
from typing import Dict, Any

def get_system_prompt(target_role: str, experience_level: str) -> str:
    """
    Generate the system prompt for CV analysis with Ekene Chris and Teleios branding
    
    Args:
        target_role: The target role
        experience_level: The target experience level
        
    Returns:
        The system prompt for OpenAI
    """
    return f"""You are an expert CV analyzer for tech roles working with Ekene Chris, a DevOps Architect and Technical Educator who empowers African engineers to compete globally.
Your task is to analyze the provided CV against specific requirements for a {target_role} position and provide detailed, actionable feedback.

Follow these guidelines inspired by the Global DevOps Competency Matrix:
1. Analyze technical skills, experience depth, achievements, and overall presentation
2. Compare the CV against the role requirements provided
3. Assess technical skills against global standards, not just local market expectations
4. Evaluate for both hard skills and the mindset/approach that separates top-tier engineers
5. Be specific and actionable in your feedback, focusing on high-ROI improvements
6. Structure your response according to the expected JSON format
7. Be honest but constructive in your assessment
8. Consider the appropriate experience level ({experience_level}) in your evaluation
9. Focus on transformative feedback that helps the candidate compete globally

The expected JSON format for your response must be:
{{
  "overall_score": <0-100 integer>,
  "categories": [
    {{
      "name": "<category name>",
      "score": <0-100 integer>,
      "feedback": "<specific feedback>",
      "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
    }},
    ...
  ],
  "keyword_analysis": {{
    "present": ["<keyword 1>", "<keyword 2>", ...],
    "missing": ["<keyword 1>", "<keyword 2>", ...],
    "recommended": ["<keyword 1>", "<keyword 2>", ...]
  }},
  "matrix_alignment": {{
    "current_level": "<current level assessment>",
    "target_level": "{experience_level}",
    "gap_areas": ["<gap area 1>", "<gap area 2>", ...]
  }},
  "summary": "<concise summary of overall analysis>"
}}

Categories must include at least: "Technical Skills", "Experience Descriptions", "Overall Presentation", and "Career Progression Indicators"

Be guided by Ekene Chris's core values:
- Innovation - Provide innovative ways to communicate technical expertise
- Mentorship - Offer guidance that helps the candidate grow professionally
- Adaptability - Recognize ways to demonstrate adaptability in a rapidly changing tech landscape
- Growth - Focus on areas that will create disproportionate career growth
- Excellence - Maintain high standards aligned with global tech requirements
"""

def get_user_prompt(
    cv_text: str,
    name: str,
    email: str,
    target_role: str,
    experience_level: str,
    role_requirements: str
) -> str:
    """
    Generate the user prompt for CV analysis with Teleios integration
    
    Args:
        cv_text: The text of the CV
        name: Candidate's name
        email: Candidate's email
        target_role: The target role
        experience_level: The target experience level
        role_requirements: Formatted role requirements
        
    Returns:
        The user prompt for OpenAI
    """
    return f"""Analyze this CV for a {target_role} position at {experience_level} level.
Apply Ekene Chris's framework for assessing technical talent with potential to excel globally.

CANDIDATE: {name} ({email})

TARGET ROLE: {target_role}
EXPERIENCE LEVEL: {experience_level}

ROLE REQUIREMENTS:
{role_requirements}

CV CONTENT:
{cv_text}

Analyze this resume like a DevOps expert who understands both global standards and the unique challenges/opportunities for African engineers. Focus on identifying:

1. Current technical capabilities vs. global expectations for this role
2. Skills that would create disproportionate value in global tech companies
3. Experience descriptions that need strengthening to demonstrate deeper expertise
4. Patterns that indicate capacity for technical leadership and growth
5. Gaps that could be addressed through Teleios's technical acceleration program

Provide your analysis in the specified JSON format only. No additional text or explanations outside the JSON structure.
"""

def format_role_requirements(requirements: Dict[str, Any]) -> str:
    """
    Format role requirements into a readable text with Teleios enhancements
    
    Args:
        requirements: Dictionary of role requirements
        
    Returns:
        Formatted role requirements as text
    """
    if not requirements:
        return "No specific requirements provided."
    
    text = "Based on the Global DevOps Competency Matrix developed by Ekene Chris:\n\n"
    
    if "core_skills" in requirements:
        text += "Core Skills Required (Global Standard):\n"
        for skill in requirements["core_skills"]:
            text += f"- {skill}\n"
        text += "\n"
    
    if "preferred_skills" in requirements:
        text += "Preferred Skills (High-Value Differentiators):\n"
        for skill in requirements["preferred_skills"]:
            text += f"- {skill}\n"
        text += "\n"
    
    if "responsibilities" in requirements:
        text += "Role Responsibilities (What Hiring Managers Expect):\n"
        for resp in requirements["responsibilities"]:
            text += f"- {resp}\n"
        text += "\n"
    
    text += "Note: This analysis is conducted using standards relevant to both local African tech ecosystems and global tech companies, with the goal of preparing engineers to compete internationally.\n"
    
    return text