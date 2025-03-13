from app.config import settings
import openai
from typing import Dict, Any, List

# Configure OpenAI client
openai.api_type = "azure"
openai.api_key = settings.AZURE_OPENAI_KEY
openai.api_base = settings.AZURE_OPENAI_ENDPOINT
openai.api_version = "2023-05-15"  # Update as needed

async def analyze_cv_with_openai(
    cv_url: str,
    target_role: str,
    experience_level: str,
    role_requirements: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze a CV using Azure OpenAI
    
    Parameters:
        cv_url: SAS URL to access the CV in Azure Blob Storage
        target_role: The role the candidate is targeting
        experience_level: The experience level being evaluated
        role_requirements: Requirements for the target role
        
    Returns:
        Dict containing analysis results
    """
    try:
        # Call Azure OpenAI with appropriate system prompt
        response = openai.ChatCompletion.create(
            engine=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an expert CV analyzer for tech roles. 
                    Analyze the provided CV against the requirements for a {target_role} at {experience_level} level.
                    Focus on technical skills, experience descriptions, achievements, and overall presentation.
                    Provide detailed feedback and suggestions for improvement."""
                },
                {
                    "role": "user",
                    "content": f"""Please analyze the resume at this URL: {cv_url}
                    
                    Target Role: {target_role}
                    Experience Level: {experience_level}
                    
                    Role Requirements:
                    {role_requirements}
                    
                    Provide a comprehensive analysis with the following:
                    1. Overall fit score (0-100)
                    2. Strengths and weaknesses by category
                    3. Missing keywords and skills
                    4. Specific improvement suggestions
                    5. Current vs target competency level assessment
                    """
                }
            ],
            temperature=0.1,
            max_tokens=4000
        )
        
        # Process and structure the response
        result = response.choices[0].message.content
        
        # Here you would parse the result into a structured format
        # This is a placeholder
        structured_result = {
            "overall_score": 75,
            "categories": [
                {
                    "name": "Technical Skills",
                    "score": 80,
                    "feedback": "Strong cloud skills but lacking in CI/CD",
                    "suggestions": ["Add specific CI/CD tools you've used"]
                }
            ],
            "keyword_analysis": {
                "present": ["AWS", "Docker"],
                "missing": ["Kubernetes", "Terraform"],
                "recommended": ["Infrastructure as Code", "GitOps"]
            },
            "matrix_alignment": {
                "current_level": "mid",
                "target_level": "senior",
                "gap_areas": ["System Design", "Team Leadership"]
            },
            "summary": "Overall good foundation but needs improvement in key areas"
        }
        
        return structured_result
        
    except Exception as e:
        print(f"Error calling Azure OpenAI: {str(e)}")
        raise