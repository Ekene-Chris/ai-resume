# app/services/role_analyzers/__init__.py
from app.services.role_analyzers.frontend_analyzer import FrontendRoleAnalyzer
from app.services.role_analyzers.backend_analyzer import BackendRoleAnalyzer
from app.services.role_analyzers.devops_analyzer import DevOpsRoleAnalyzer
from app.services.role_analyzers.base_analyzer import BaseRoleAnalyzer
import logging

logger = logging.getLogger(__name__)

def get_role_analyzer(role_name: str, experience_level: str) -> BaseRoleAnalyzer:
    """
    Factory function to create a role-specific analyzer
    
    Args:
        role_name: The target role name
        experience_level: The target experience level
        
    Returns:
        A role-specific analyzer instance
    """
    # Normalize role name and experience level
    role_name_lower = role_name.lower().strip()
    experience_level_lower = experience_level.lower().strip()
    
    # Map experience levels to standard values
    if experience_level_lower in ["junior", "entry", "beginner", "associate"]:
        normalized_level = "junior"
    elif experience_level_lower in ["mid", "middle", "intermediate"]:
        normalized_level = "mid"
    elif experience_level_lower in ["senior", "lead", "expert", "principal"]:
        normalized_level = "senior"
    else:
        # Default to mid-level if unknown
        normalized_level = "mid"
        logger.warning(f"Unknown experience level: {experience_level}, defaulting to 'mid'")
    
    # Select the appropriate analyzer based on role name
    if "frontend" in role_name_lower or "ui" in role_name_lower or "front-end" in role_name_lower:
        return FrontendRoleAnalyzer(normalized_level)
    elif "backend" in role_name_lower or "api" in role_name_lower or "back-end" in role_name_lower:
        return BackendRoleAnalyzer(normalized_level)
    elif "devops" in role_name_lower or "sre" in role_name_lower or "platform" in role_name_lower:
        return DevOpsRoleAnalyzer(normalized_level)
    else:
        # Default to backend if role is unknown
        logger.warning(f"Unknown role name: {role_name}, defaulting to Backend Developer")
        return BackendRoleAnalyzer(normalized_level)