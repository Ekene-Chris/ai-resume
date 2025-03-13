# app/utils/prompt_templates.py
from typing import Dict, Any

def get_system_prompt(target_role: str, experience_level: str) -> str:
    """
    Generate the system prompt for CV analysis
    
    Args:
        target_role: The target role
        experience_level: The target experience level
        
    Returns:
        The system prompt for OpenAI
    """
    return f"""You are an expert CV analyzer for tech roles, specializing in {target_role} positions.
Your task is to analyze the provided CV against specific requirements and provide detailed, actionable feedback.

Follow these guidelines:
1. Analyze technical skills, experience depth, achievements, and overall presentation
2. Compare the CV against the role requirements provided
3. Be specific and actionable in your feedback
4. Structure your response according to the expected JSON format
5. Be honest but constructive in your assessment
6. Consider the appropriate experience level ({experience_level}) in your evaluation

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

Categories must include at least: "Technical Skills", "Experience Descriptions", and "Overall Presentation"
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
    Generate the user prompt for CV analysis
    
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
    return f"""Analyze this CV for a {target_role} position at {experience_level} level:

CANDIDATE: {name} ({email})

TARGET ROLE: {target_role}
EXPERIENCE LEVEL: {experience_level}

ROLE REQUIREMENTS:
{role_requirements}

CV CONTENT:
{cv_text}

Provide your analysis in the specified JSON format only. No additional text or explanations outside the JSON structure.
"""

def format_role_requirements(requirements: Dict[str, Any]) -> str:
    """
    Format role requirements into a readable text
    
    Args:
        requirements: Dictionary of role requirements
        
    Returns:
        Formatted role requirements as text
    """
    if not requirements:
        return "No specific requirements provided."
    
    text = ""
    
    if "core_skills" in requirements:
        text += "Core Skills:\n"
        for skill in requirements["core_skills"]:
            text += f"- {skill}\n"
        text += "\n"
    
    if "preferred_skills" in requirements:
        text += "Preferred Skills:\n"
        for skill in requirements["preferred_skills"]:
            text += f"- {skill}\n"
        text += "\n"
    
    if "responsibilities" in requirements:
        text += "Responsibilities:\n"
        for resp in requirements["responsibilities"]:
            text += f"- {resp}\n"
        text += "\n"
    
    return text