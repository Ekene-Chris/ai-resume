# app/core/azure_openai.py - Enhanced error handling
import logging
import openai
import json
import time
import re
from typing import Dict, Any, Optional
from app.config import settings
from app.prompt_templates import get_system_prompt, get_user_prompt, format_role_requirements

# Configure logging
logger = logging.getLogger(__name__)

# Configure OpenAI client
openai.api_type = "azure"
openai.api_key = settings.AZURE_OPENAI_KEY
openai.api_base = settings.AZURE_OPENAI_ENDPOINT
openai.api_version = "2023-12-01-preview"  # Update as needed

async def analyze_cv_with_openai(
    cv_url: str,
    name: str,
    email: str,
    target_role: str,
    experience_level: str,
    role_requirements: Dict[str, Any],
    system_prompt: str = None,
    user_prompt: str = None,
    max_retries: int = 3,
    retry_delay: int = 2
) -> Dict[str, Any]:
    """
    Analyze a CV using Azure OpenAI with enhanced error handling
    
    Parameters:
        cv_url: URL to access the CV in Azure Blob Storage
        name: Candidate's name
        email: Candidate's email
        target_role: The role the candidate is targeting
        experience_level: The experience level being evaluated
        role_requirements: Requirements for the target role
        system_prompt: Optional custom system prompt
        user_prompt: Optional custom user prompt
        max_retries: Maximum number of retries on failure
        retry_delay: Initial delay between retries (with exponential backoff)
        
    Returns:
        Dict containing analysis results
    """
    # Prepare role requirements as formatted text if not provided directly
    if user_prompt is None and cv_url:
        role_req_text = format_role_requirements(role_requirements)
        
        # Get the default system prompt if not provided
        if not system_prompt:
            system_prompt = get_system_prompt(target_role, experience_level)

    # Track retry attempts
    retry_count = 0
    current_delay = retry_delay
    last_error = None

    # Try multiple times with exponential backoff
    while retry_count < max_retries:
        try:
            logger.info(f"Sending request to OpenAI for {target_role} analysis (attempt {retry_count + 1}/{max_retries})")
            
            # If user_prompt is not provided, download and extract text from the CV
            if user_prompt is None:
                # Import here to avoid circular imports
                from app.file_utils import download_file, extract_text_from_pdf_bytes, extract_text_from_docx_bytes
                
                try:
                    # Download the file
                    logger.info(f"Downloading CV from {cv_url}")
                    file_content = await download_file(cv_url)
                    
                    if not file_content:
                        raise Exception("Failed to download CV file")
                    
                    # Extract text based on file extension
                    if cv_url.lower().endswith('.pdf'):
                        cv_text = await extract_text_from_pdf_bytes(file_content)
                    elif cv_url.lower().endswith('.docx') or cv_url.lower().endswith('.doc'):
                        cv_text = await extract_text_from_docx_bytes(file_content)
                    else:
                        # Assume plain text
                        cv_text = file_content.decode('utf-8', errors='replace')
                    
                    # Check if we got meaningful text
                    if not cv_text or len(cv_text.strip()) < 100:
                        raise Exception(f"Extracted text is too short: {len(cv_text.strip())} chars")
                    
                    # Limit text length to prevent token limit issues
                    if len(cv_text) > 12000:  # Approximate token limit safety margin
                        logger.warning(f"CV text is very long ({len(cv_text)} chars), truncating to 12000 chars")
                        cv_text = cv_text[:12000] + "\n\n[Text truncated due to length...]"
                    
                    logger.info(f"Successfully extracted CV text: {len(cv_text)} characters")
                    
                    # Build user prompt
                    user_prompt = get_user_prompt(
                        cv_text=cv_text,
                        name=name,
                        email=email,
                        target_role=target_role,
                        experience_level=experience_level,
                        role_requirements=role_req_text
                    )
                    
                except Exception as extract_error:
                    logger.error(f"Error extracting CV text: {str(extract_error)}")
                    raise Exception(f"Failed to extract CV text: {str(extract_error)}")
            
            # Check if the prompts are too large
            system_token_estimate = len(system_prompt) / 4  # Rough approximation
            user_token_estimate = len(user_prompt) / 4    # Rough approximation
            
            if system_token_estimate + user_token_estimate > 8000:
                logger.warning(f"Prompts may exceed token limits (est. {int(system_token_estimate + user_token_estimate)} tokens)")
                # Try to trim the user prompt
                max_user_length = min(len(user_prompt), 32000)  # Approximately 8000 tokens
                if len(user_prompt) > max_user_length:
                    user_prompt = user_prompt[:max_user_length] + "\n\n[Content truncated due to length...]"
                    logger.info(f"Truncated user prompt to {len(user_prompt)} characters")
            
            # Make the OpenAI API call with timeout handling
            try:
                response = openai.ChatCompletion.create(
                    engine=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=4000,
                    response_format={"type": "json_object"},
                    timeout=60  # 60 second timeout
                )
                
                # Parse the response
                result_text = response.choices[0].message.content
                logger.info(f"Received response from OpenAI: {len(result_text)} characters")
                
                # Extract JSON from the response if it's wrapped in markdown or other text
                json_str = extract_json(result_text)
                
                try:
                    result = json.loads(json_str)
                    return result
                except json.JSONDecodeError as json_error:
                    logger.error(f"Error parsing JSON response: {str(json_error)}, content: {json_str[:200]}...")
                    raise Exception(f"Invalid JSON response from OpenAI: {str(json_error)}")
                    
            except openai.error.APIConnectionError as api_conn_error:
                logger.warning(f"OpenAI API connection error (attempt {retry_count + 1}): {str(api_conn_error)}")
                last_error = api_conn_error
                retry_count += 1
                
                if retry_count < max_retries:
                    logger.info(f"Retrying in {current_delay} seconds...")
                    time.sleep(current_delay)
                    current_delay *= 2  # Exponential backoff
                    continue
                else:
                    logger.error(f"Maximum retries reached for OpenAI API")
                    raise Exception(f"Failed to connect to OpenAI API after {max_retries} attempts: {str(api_conn_error)}")
            
            except openai.error.Timeout as timeout_error:
                logger.warning(f"OpenAI API timeout (attempt {retry_count + 1}): {str(timeout_error)}")
                last_error = timeout_error
                retry_count += 1
                
                if retry_count < max_retries:
                    logger.info(f"Retrying in {current_delay} seconds...")
                    time.sleep(current_delay)
                    current_delay *= 2  # Exponential backoff
                    continue
                else:
                    logger.error(f"Maximum retries reached for OpenAI API")
                    raise Exception(f"OpenAI API request timed out after {max_retries} attempts: {str(timeout_error)}")
            
            except openai.error.APIError as api_error:
                if "overloaded" in str(api_error).lower() or "rate limit" in str(api_error).lower():
                    logger.warning(f"OpenAI API overloaded or rate limited (attempt {retry_count + 1}): {str(api_error)}")
                    last_error = api_error
                    retry_count += 1
                    
                    if retry_count < max_retries:
                        logger.info(f"Retrying in {current_delay} seconds...")
                        time.sleep(current_delay)
                        current_delay *= 2  # Exponential backoff
                        continue
                    else:
                        logger.error(f"Maximum retries reached for OpenAI API")
                        raise Exception(f"OpenAI API overloaded after {max_retries} attempts: {str(api_error)}")
                else:
                    # For other API errors, don't retry
                    logger.error(f"OpenAI API error: {str(api_error)}")
                    raise Exception(f"OpenAI API error: {str(api_error)}")
                    
            except Exception as general_api_error:
                logger.error(f"Error calling OpenAI API: {str(general_api_error)}")
                raise Exception(f"Error analyzing CV with OpenAI: {str(general_api_error)}")
            
        except Exception as e:
            logger.error(f"Error analyzing CV: {str(e)}", exc_info=True)
            last_error = e
            retry_count += 1
            
            if retry_count < max_retries:
                logger.info(f"Retrying in {current_delay} seconds...")
                time.sleep(current_delay)
                current_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Maximum retries reached for OpenAI analysis")
                raise Exception(f"Failed to analyze CV after {max_retries} attempts: {str(e)}")

    # This should never happen due to the raises above, but just in case
    raise Exception(f"Failed to analyze CV: {str(last_error)}")

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

def generate_fallback_analysis(
    name: str,
    email: str,
    target_role: str,
    experience_level: str,
    cv_text: str
) -> Dict[str, Any]:
    """
    Generate a simplified analysis when OpenAI is unavailable
    This provides basic results to avoid complete failure
    
    Args:
        name: Candidate's name
        email: Candidate's email
        target_role: Target role
        experience_level: Experience level
        cv_text: Resume text
        
    Returns:
        A simplified analysis result
    """
    import re
    
    # Extract skills based on common tech terms
    skills = []
    skill_keywords = [
        "Python", "JavaScript", "Java", "C#", "Go", "Rust", "TypeScript",
        "React", "Angular", "Vue", "Node.js", "Django", "Flask", "Express",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "CI/CD", 
        "Git", "GitHub", "GitLab", "DevOps", "Agile", "Scrum", "REST", "GraphQL",
        "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "Redis", "DynamoDB"
    ]
    
    for skill in skill_keywords:
        if re.search(r'\b' + re.escape(skill) + r'\b', cv_text, re.IGNORECASE):
            skills.append(skill)
    
    # Generate a simple analysis
    return {
        "overall_score": 50,  # Neutral score
        "categories": [
            {
                "name": "Technical Skills",
                "score": 50,
                "feedback": f"Found {len(skills)} relevant skills in the CV. A detailed analysis could not be completed.",
                "suggestions": [
                    "Consider resubmitting your CV for a more detailed analysis.",
                    "Make sure your skills and experience are clearly listed.",
                    "Quantify achievements where possible."
                ]
            },
            {
                "name": "Experience Descriptions",
                "score": 50,
                "feedback": "Due to technical limitations, a detailed analysis of your experience could not be completed.",
                "suggestions": [
                    "Make sure your experience descriptions focus on achievements rather than just responsibilities.",
                    "Use metrics and specific results where possible."
                ]
            },
            {
                "name": "Overall Presentation",
                "score": 50,
                "feedback": "A detailed analysis of your CV presentation could not be completed.",
                "suggestions": [
                    "Ensure your CV is well-structured with clear section headings.",
                    "Keep formatting consistent throughout the document."
                ]
            }
        ],
        "keyword_analysis": {
            "present": skills[:10],  # Limit to first 10 skills
            "missing": [],
            "recommended": ["Relevant Industry Experience", "Communication Skills", "Problem-Solving"]
        },
        "matrix_alignment": {
            "current_level": experience_level,
            "target_level": experience_level,
            "gap_areas": ["Technical skills validation", "Experience verification", "Project examples"]
        },
        "summary": f"This is a limited analysis due to technical difficulties. Your CV appears to include {len(skills)} relevant skills for the {target_role} position. We recommend resubmitting your CV later for a complete analysis. In the meantime, focus on quantifying achievements, highlighting relevant experience, and clearly organizing your technical skills."
    }