# app/core/azure_openai.py
from app.config import settings
import openai
from typing import Dict, Any, List
import json
import logging
import aiohttp
import re
from app.utils.file_utils import download_file, extract_text_from_pdf_bytes, extract_text_from_docx_bytes
from app.utils.prompt_templates import get_system_prompt, get_user_prompt, format_role_requirements

# Configure logging
logger = logging.getLogger(__name__)

# Configure OpenAI client
openai.api_type = "azure"
openai.api_key = settings.AZURE_OPENAI_KEY
openai.api_base = settings.AZURE_OPENAI_ENDPOINT
openai.api_version = "2023-12-01-preview"  # Update as needed

async def download_cv_content(cv_url: str) -> str:
    """
    Download CV content from the provided URL
    
    Args:
        cv_url: URL to the CV in Azure Blob Storage
        
    Returns:
        The content of the CV as text
    """
    try:
        # Download the file
        content = await download_file(cv_url)
        if not content:
            logger.error("Failed to download CV")
            return "[Failed to download CV]"
        
        # Check content type based on file extension
        if cv_url.lower().endswith('.pdf'):
            return await extract_text_from_pdf_bytes(content)
        elif cv_url.lower().endswith('.docx') or cv_url.lower().endswith('.doc'):
            return await extract_text_from_docx_bytes(content)
        else:
            # Assume it's plain text
            return content.decode('utf-8', errors='replace')
    except Exception as e:
        logger.error(f"Error downloading CV content: {str(e)}")
        return f"[Error extracting CV content: {str(e)}]"# app/core/azure_openai.p

# These functions are now in app/utils/file_utils.py

async def analyze_cv_with_openai(
    cv_url: str,
    name: str,
    email: str,
    target_role: str,
    experience_level: str,
    role_requirements: Dict[str, Any],
    system_prompt: str = None,
    user_prompt: str = None
) -> Dict[str, Any]:
    """
    Analyze a CV using Azure OpenAI
    
    Parameters:
        cv_url: URL to access the CV in Azure Blob Storage
        name: Candidate's name
        email: Candidate's email
        target_role: The role the candidate is targeting
        experience_level: The experience level being evaluated
        role_requirements: Requirements for the target role
        system_prompt: Optional custom system prompt
        user_prompt: Optional custom user prompt
        
    Returns:
        Dict containing analysis results
    """
    try:
        # Download and extract text from the CV if no custom user prompt is provided
        cv_text = ""
        if not user_prompt:
            cv_text = await download_cv_content(cv_url)
            
            # Prepare role requirements as formatted text
            role_req_text = format_role_requirements(role_requirements)
            
            # Get the default system prompt
            if not system_prompt:
                system_prompt = get_system_prompt(target_role, experience_level)
            
            # Get the default user prompt
            user_prompt = get_user_prompt(
                cv_text=cv_text,
                name=name,
                email=email,
                target_role=target_role,
                experience_level=experience_level,
                role_requirements=role_req_text
            )

        # Make the OpenAI API call
        try:
            response = openai.ChatCompletion.create(
                engine=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            # Extract and parse the JSON response
            result_text = response.choices[0].message.content
            
            # Extract JSON from the response if it's wrapped in markdown or other text
            json_str = extract_json(result_text)
            result = json.loads(json_str)
            
            return result
            
        except Exception as api_error:
            logger.error(f"OpenAI API error: {str(api_error)}")
            # Provide a fallback analysis in case of API error
            return create_fallback_analysis(target_role, experience_level)
        
    except Exception as e:
        logger.error(f"Error analyzing CV: {str(e)}")
        raise

def extract_json(text: str) -> str:
    """
    Extract JSON from a text that might have markdown or other content
    """
    # Try to find content between triple backticks
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    
    if json_match:
        return json_match.group(1)
    
    # If no triple backticks, assume the entire text is JSON
    return text

# This function is now in app/utils/prompt_templates.py

def create_fallback_analysis(target_role: str, experience_level: str) -> Dict[str, Any]:
    """
    Create a fallback analysis in case the OpenAI API fails
    """
    return {
        "overall_score": 50,
        "categories": [
            {
                "name": "Technical Skills",
                "score": 50,
                "feedback": "Unable to perform detailed analysis. Please review the CV manually.",
                "suggestions": ["Ensure skills match the core requirements for the role."]
            },
            {
                "name": "Experience Descriptions",
                "score": 50,
                "feedback": "Unable to perform detailed analysis. Please review the CV manually.",
                "suggestions": ["Focus on achievements rather than responsibilities."]
            },
            {
                "name": "Overall Presentation",
                "score": 50,
                "feedback": "Unable to perform detailed analysis. Please review the CV manually.",
                "suggestions": ["Ensure the CV is well-structured and tailored to the role."]
            }
        ],
        "keyword_analysis": {
            "present": [],
            "missing": [],
            "recommended": ["Review manually to identify relevant keywords."]
        },
        "matrix_alignment": {
            "current_level": "unknown",
            "target_level": experience_level,
            "gap_areas": ["Unable to determine gaps automatically."]
        },
        "summary": "Automatic analysis failed. Please review the CV manually against the requirements for a " 
                  f"{target_role} position at {experience_level} level."
    }