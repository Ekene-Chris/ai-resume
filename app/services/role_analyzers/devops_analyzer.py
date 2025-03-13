# app/services/role_analyzers/devops_analyzer.py
from app.services.role_analyzers.base_analyzer import BaseRoleAnalyzer
from typing import Dict, Any, List
import os
import json
import logging
import re

logger = logging.getLogger(__name__)

class DevOpsRoleAnalyzer(BaseRoleAnalyzer):
    """Analyzer specifically for DevOps Engineer roles"""
    
    def __init__(self, experience_level: str):
        super().__init__("DevOps Engineer", experience_level)
    
    def _load_role_requirements(self) -> Dict[str, Any]:
        """Load DevOps role-specific requirements"""
        try:
            # First try to load from file
            role_file = f"app/data/roles/devops_engineer.json"
            
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
                    "Linux/Unix", "Basic Scripting (Bash/Python)", 
                    "Git & Version Control", "Basic CI/CD Concepts",
                    "Docker Basics", "Cloud Basics (AWS/Azure/GCP)",
                    "Basic Monitoring", "Infrastructure Basics"
                ],
                "preferred_skills": [
                    "Configuration Management Tools", "Basic Kubernetes",
                    "Infrastructure as Code", "Networking Fundamentals",
                    "Security Basics", "Log Management"
                ],
                "responsibilities": [
                    "Assist with deployment processes",
                    "Help maintain CI/CD pipelines",
                    "Perform basic server administration tasks",
                    "Monitor system performance and availability",
                    "Document infrastructure and processes",
                    "Support development and operations teams"
                ]
            },
            "mid": {
                "core_skills": [
                    "Advanced Linux/Unix", "Scripting & Automation",
                    "Container Orchestration (Kubernetes)",
                    "CI/CD Pipeline Design", "Infrastructure as Code",
                    "Cloud Services & Architecture", "Monitoring & Logging",
                    "Networking & Security"
                ],
                "preferred_skills": [
                    "Multi-cloud Deployments", "Configuration Management",
                    "Database Administration", "Performance Tuning",
                    "High Availability Design", "Disaster Recovery",
                    "Cost Optimization"
                ],
                "responsibilities": [
                    "Design and implement CI/CD pipelines",
                    "Build and maintain containerized environments",
                    "Automate infrastructure provisioning",
                    "Implement monitoring and alerting solutions",
                    "Troubleshoot complex system issues",
                    "Improve system reliability and performance",
                    "Collaborate with development teams on best practices"
                ]
            },
            "senior": {
                "core_skills": [
                    "DevOps Architecture", "Platform Engineering",
                    "Advanced Kubernetes & Container Orchestration",
                    "Advanced CI/CD & GitOps", "Cloud-Native Architecture",
                    "SRE Practices", "Security & Compliance",
                    "Performance Engineering"
                ],
                "preferred_skills": [
                    "Multi-cloud Strategy", "Service Mesh",
                    "Serverless Architecture", "Chaos Engineering",
                    "Advanced Monitoring & Observability",
                    "Mentorship & Leadership", "Cost Management"
                ],
                "responsibilities": [
                    "Design resilient and scalable infrastructure",
                    "Establish DevOps best practices and standards",
                    "Lead implementation of complex DevOps solutions",
                    "Design disaster recovery and high availability solutions",
                    "Optimize cloud infrastructure and costs",
                    "Mentor junior engineers and collaborate with leadership",
                    "Drive automation and continuous improvement",
                    "Ensure security and compliance throughout the pipeline"
                ]
            }
        }.get(self.experience_level, {})
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for DevOps role analysis"""
        return f"""You are an expert technical recruiter specializing in DevOps Engineer roles with deep knowledge of infrastructure, CI/CD, cloud services, containerization, and automation.

Your task is to analyze a resume for a {self.experience_level}-level DevOps Engineer position and provide detailed, actionable feedback.

For a {self.experience_level}-level DevOps Engineer, evaluate for these key areas:
1. Infrastructure and cloud platform experience
2. CI/CD pipeline design and implementation
3. Containerization and orchestration knowledge
4. Automation and scripting abilities
5. Monitoring and observability expertise
6. Security practices and implementation
7. Performance optimization experience
8. Collaboration and communication skills

When analyzing the resume, consider:
- For junior roles: Focus on fundamentals, Linux skills, basic cloud knowledge, and willingness to learn
- For mid-level roles: Look for automation experience, CI/CD pipeline implementation, and container orchestration
- For senior roles: Evaluate architecture decisions, scalability solutions, and technical leadership in DevOps practices

Your analysis should be thorough, constructive, and tailored to DevOps specifically.

The expected JSON format for your response must be:
{{
  "overall_score": <0-100 integer>,
  "categories": [
    {{
      "name": "Infrastructure & Cloud",
      "score": <0-100 integer>,
      "feedback": "<specific feedback on infrastructure & cloud experience>",
      "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
    }},
    {{
      "name": "CI/CD & Deployment",
      "score": <0-100 integer>,
      "feedback": "<specific feedback on CI/CD experience>",
      "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
    }},
    {{
      "name": "Containerization & Orchestration",
      "score": <0-100 integer>,
      "feedback": "<specific feedback on container experience>",
      "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
    }},
    {{
      "name": "Automation & Scripting",
      "score": <0-100 integer>,
      "feedback": "<specific feedback on automation experience>",
      "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
    }},
    {{
      "name": "Monitoring & Observability",
      "score": <0-100 integer>,
      "feedback": "<specific feedback on monitoring experience>",
      "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
    }}
  ],
  "keyword_analysis": {{
    "present": ["<DevOps keyword 1>", "<DevOps keyword 2>", ...],
    "missing": ["<missing DevOps keyword 1>", "<missing DevOps keyword 2>", ...],
    "recommended": ["<recommended DevOps keyword 1>", "<recommended DevOps keyword 2>", ...]
  }},
  "matrix_alignment": {{
    "current_level": "<current DevOps skill level assessment>",
    "target_level": "{self.experience_level}",
    "gap_areas": ["<gap area 1>", "<gap area 2>", ...]
  }},
  "summary": "<concise summary of overall DevOps engineer analysis>"
}}"""
    
    def get_user_prompt(self, resume_data: Dict[str, Any]) -> str:
        """Get the user prompt for the DevOps role analysis"""
        # Extract relevant data from the resume
        contact_info = resume_data.get("contact_info", {})
        name = contact_info.get("name", "")
        work_experience = self.format_work_experience(resume_data.get("work_experience", []))
        education = self.format_education(resume_data.get("education", []))
        skills = self.format_skills_list(resume_data.get("skills", []))
        raw_text = resume_data.get("raw_text", "")
        years_exp = self.extract_years_of_experience(resume_data.get("work_experience", []))
        
        # Get DevOps-specific technologies
        devops_techs = [tech for tech in self.extract_technologies(resume_data) 
                       if self._is_devops_tech(tech)]
        
        # Extract DevOps specific information
        cloud_experience = self._extract_cloud_experience(resume_data)
        cicd_experience = self._extract_cicd_experience(resume_data)
        container_experience = self._extract_container_experience(resume_data)
        
        # Format the role requirements
        role_req_text = self._format_role_requirements()
        
        return f"""Analyze this resume for a {self.role_name} position at {self.experience_level} level:

CANDIDATE INFO:
Name: {name}
Estimated Years of Experience: {years_exp}
Identified DevOps Technologies: {', '.join(devops_techs)}

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

CLOUD EXPERIENCE:
{cloud_experience}

CI/CD EXPERIENCE:
{cicd_experience}

CONTAINER EXPERIENCE:
{container_experience}

ADDITIONAL RESUME CONTENT:
{raw_text[:2000]}  # Limiting to first 2000 chars of raw text to avoid token limits

Based on this information, provide a comprehensive analysis of this candidate for a {self.experience_level}-level {self.role_name} position. Focus specifically on infrastructure, cloud platforms, CI/CD, containerization, automation, and monitoring experience.

Provide your analysis in the specified JSON format only. No additional text or explanations outside the JSON structure.
"""
    
    def create_analysis_payload(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a structured payload for DevOps engineer analysis"""
        # Extract core data
        contact_info = resume_data.get("contact_info", {})
        name = contact_info.get("name", "")
        email = contact_info.get("email", "")
        
        # Extract experience metrics
        years_exp = self.extract_years_of_experience(resume_data.get("work_experience", []))
        detected_level = self.estimate_experience_level(years_exp)
        
        # Extract technologies with focus on DevOps
        all_techs = self.extract_technologies(resume_data)
        devops_techs = [tech for tech in all_techs if self._is_devops_tech(tech)]
        
        # Identify specific DevOps categories
        cloud_platforms = self._identify_cloud_platforms(all_techs, resume_data.get("raw_text", ""))
        ci_cd_tools = self._identify_cicd_tools(all_techs, resume_data.get("raw_text", ""))
        container_techs = self._identify_container_techs(all_techs, resume_data.get("raw_text", ""))
        config_mgmt_tools = self._identify_config_mgmt_tools(all_techs, resume_data.get("raw_text", ""))
        monitoring_tools = self._identify_monitoring_tools(all_techs, resume_data.get("raw_text", ""))
        
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
                "devops_technologies": devops_techs,
                "cloud_platforms": cloud_platforms,
                "ci_cd_tools": ci_cd_tools,
                "container_technologies": container_techs,
                "config_management": config_mgmt_tools,
                "monitoring_tools": monitoring_tools,
                "missing_core_skills": self._identify_missing_skills(devops_techs)
            },
            "experience_analysis": {
                "has_cloud_experience": bool(cloud_platforms),
                "has_cicd_experience": bool(ci_cd_tools),
                "has_container_experience": bool(container_techs),
                "has_iac_experience": self._has_iac_experience(resume_data),
                "has_automation_experience": self._has_automation_experience(resume_data),
                "cloud_experience": self._extract_cloud_experience(resume_data),
                "cicd_experience": self._extract_cicd_experience(resume_data),
                "container_experience": self._extract_container_experience(resume_data)
            }
        }
    
    def _format_role_requirements(self) -> str:
        """Format DevOps role requirements into readable text"""
        text = ""
        
        if "core_skills" in self.role_requirements:
            text += "Core DevOps Skills Required:\n"
            for skill in self.role_requirements["core_skills"]:
                text += f"- {skill}\n"
            text += "\n"
        
        if "preferred_skills" in self.role_requirements:
            text += "Preferred DevOps Skills:\n"
            for skill in self.role_requirements["preferred_skills"]:
                text += f"- {skill}\n"
            text += "\n"
        
        if "responsibilities" in self.role_requirements:
            text += "DevOps Engineer Responsibilities:\n"
            for resp in self.role_requirements["responsibilities"]:
                text += f"- {resp}\n"
            text += "\n"
        
        return text
    
    def _is_devops_tech(self, tech: str) -> bool:
        """Determine if a technology is DevOps-related"""
        devops_techs = {
            "docker", "kubernetes", "k8s", "jenkins", "gitlab ci", "github actions",
            "circleci", "travis ci", "terraform", "cloudformation", "ansible", "puppet",
            "chef", "salt", "aws", "azure", "gcp", "google cloud", "cloud", "devops",
            "ci/cd", "continuous integration", "continuous delivery", "continuous deployment",
            "prometheus", "grafana", "nagios", "zabbix", "elk", "elasticsearch", "logstash",
            "kibana", "datadog", "splunk", "new relic", "linux", "bash", "shell script", 
            "powershell", "python", "automation", "git", "vagrant", "packer", "istio",
            "consul", "vault", "argocd", "fluxcd", "helm", "microservices", "serverless",
            "lambda", "vpc", "security group", "iam", "load balancer", "nginx", "apache",
            "iis", "s3", "ec2", "rds", "sqs", "sns", "route53", "cloudfront", "cloudwatch",
            "networking", "virtual machine", "vm", "high availability", "ha", "disaster recovery",
            "dr", "infrastructure", "infrastructure as code", "iac"
        }
        return tech.lower() in devops_techs
    
    def _identify_cloud_platforms(self, technologies: List[str], raw_text: str) -> List[str]:
        """Identify which cloud platforms are mentioned in the resume"""
        platforms = []
        
        cloud_keywords = {
            "aws": ["aws", "amazon web services", "amazon cloud", "ec2", "s3", "rds", "lambda", 
                   "cloudformation", "cloudfront", "cloudwatch", "iam", "vpc", "ecs", "eks"],
            "azure": ["azure", "microsoft azure", "azure devops", "app service", "azure functions", 
                     "azure vm", "azure storage", "azure sql", "arm template"],
            "gcp": ["gcp", "google cloud", "google cloud platform", "compute engine", "cloud storage", 
                   "cloud sql", "cloud functions", "gke", "app engine", "bigquery"],
            "alibaba": ["alibaba cloud", "aliyun"],
            "ibm": ["ibm cloud", "bluemix"],
            "oracle": ["oracle cloud", "oci", "oracle cloud infrastructure"],
            "digital_ocean": ["digital ocean", "digitalocean"],
            "heroku": ["heroku"]
        }
        
        for platform, keywords in cloud_keywords.items():
            for keyword in keywords:
                if any(keyword.lower() in tech.lower() for tech in technologies) or keyword.lower() in raw_text.lower():
                    platforms.append(platform)
                    break
        
        return list(set(platforms))  # Remove duplicates
    
    def _identify_cicd_tools(self, technologies: List[str], raw_text: str) -> List[str]:
        """Identify which CI/CD tools are mentioned in the resume"""
        tools = []
        
        cicd_keywords = {
            "jenkins": ["jenkins", "jenkins pipeline", "jenkinsfile"],
            "github_actions": ["github actions", "github workflow"],
            "gitlab_ci": ["gitlab ci", "gitlab-ci", "gitlab pipeline", ".gitlab-ci.yml"],
            "circleci": ["circleci", "circle ci"],
            "travis_ci": ["travis ci", "travis-ci", ".travis.yml"],
            "azure_devops": ["azure devops", "azure pipeline", "azure pipelines", "vsts", "tfs"],
            "teamcity": ["teamcity", "team city"],
            "bamboo": ["bamboo", "atlassian bamboo"],
            "codebuild": ["codebuild", "aws codebuild", "code build"],
            "codepipeline": ["codepipeline", "aws codepipeline", "code pipeline"],
            "argocd": ["argocd", "argo cd", "gitops"],
            "fluxcd": ["fluxcd", "flux cd", "flux"],
            "spinnaker": ["spinnaker"],
            "tekton": ["tekton", "tekton pipeline"],
            "concourse": ["concourse", "concourse ci"]
        }
        
        for tool, keywords in cicd_keywords.items():
            for keyword in keywords:
                if any(keyword.lower() in tech.lower() for tech in technologies) or keyword.lower() in raw_text.lower():
                    tools.append(tool)
                    break
        
        # Check for generic CI/CD mentions
        if not tools and ("ci/cd" in raw_text.lower() or "ci / cd" in raw_text.lower() or 
                          "continuous integration" in raw_text.lower() or 
                          "continuous delivery" in raw_text.lower()):
            tools.append("ci_cd_generic")
            
        return list(set(tools))  # Remove duplicates
    
    def _identify_container_techs(self, technologies: List[str], raw_text: str) -> List[str]:
        """Identify which container technologies are mentioned in the resume"""
        container_techs = []
        
        container_keywords = {
            "docker": ["docker", "dockerfile", "docker-compose", "docker swarm"],
            "kubernetes": ["kubernetes", "k8s", "kubectl", "kubernetes cluster", "k8s cluster",
                          "aks", "eks", "gke", "openshift", "rancher", "kube"],
            "openshift": ["openshift", "okd", "origin"],
            "rancher": ["rancher"],
            "nomad": ["nomad", "hashicorp nomad"],
            "containerd": ["containerd"],
            "cri-o": ["cri-o", "crio"],
            "podman": ["podman"],
            "helm": ["helm", "helm chart"],
            "istio": ["istio", "service mesh"],
            "linkerd": ["linkerd"],
            "consul": ["consul", "hashicorp consul"]
        }
        
        for tech, keywords in container_keywords.items():
            for keyword in keywords:
                if any(keyword.lower() in t.lower() for t in technologies) or keyword.lower() in raw_text.lower():
                    container_techs.append(tech)
                    break
        
        return list(set(container_techs))  # Remove duplicates
    
    def _identify_config_mgmt_tools(self, technologies: List[str], raw_text: str) -> List[str]:
        """Identify which configuration management tools are mentioned in the resume"""
        tools = []
        
        config_keywords = {
            "ansible": ["ansible", "ansible playbook", "ansible tower", "ansible automation"],
            "puppet": ["puppet", "puppet enterprise"],
            "chef": ["chef", "chef cookbook"],
            "salt": ["salt", "saltstack"],
            "terraform": ["terraform", "hashicorp terraform", "terraform module", "terraform plan", "terraform apply"],
            "cloudformation": ["cloudformation", "aws cloudformation", "cloud formation"],
            "pulumi": ["pulumi"],
            "cdktf": ["cdktf", "cdk for terraform", "terraform cdk"]
        }
        
        for tool, keywords in config_keywords.items():
            for keyword in keywords:
                if any(keyword.lower() in tech.lower() for tech in technologies) or keyword.lower() in raw_text.lower():
                    tools.append(tool)
                    break
        
        return list(set(tools))  # Remove duplicates
    
    def _identify_monitoring_tools(self, technologies: List[str], raw_text: str) -> List[str]:
        """Identify which monitoring tools are mentioned in the resume"""
        tools = []
        
        monitoring_keywords = {
            "prometheus": ["prometheus", "prometheus metrics", "alertmanager"],
            "grafana": ["grafana", "grafana dashboard"],
            "nagios": ["nagios"],
            "zabbix": ["zabbix"],
            "datadog": ["datadog", "data dog"],
            "new_relic": ["new relic", "newrelic"],
            "splunk": ["splunk"],
            "elk": ["elk", "elasticsearch", "logstash", "kibana", "elastic stack"],
            "cloudwatch": ["cloudwatch", "aws cloudwatch", "cloud watch"],
            "dynatrace": ["dynatrace"],
            "appdynamics": ["appdynamics", "app dynamics"],
            "sumologic": ["sumologic", "sumo logic"],
            "sentry": ["sentry"],
            "fluentd": ["fluentd"],
            "telegraf": ["telegraf"],
            "influxdb": ["influxdb", "influx", "influx db"]
        }
        
        for tool, keywords in monitoring_keywords.items():
            for keyword in keywords:
                if any(keyword.lower() in tech.lower() for tech in technologies) or keyword.lower() in raw_text.lower():
                    tools.append(tool)
                    break
        
        return list(set(tools))  # Remove duplicates
    
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
        # Handle compound skills like "Linux/Unix"
        if "/" in skill:
            skill_parts = skill.lower().split("/")
            return any(part in tech.lower() or tech.lower() in part for part in skill_parts)
        
        return skill.lower() in tech.lower() or tech.lower() in skill.lower()
    
    def _has_iac_experience(self, resume_data: Dict[str, Any]) -> bool:
        """Check if the resume mentions Infrastructure as Code experience"""
        iac_keywords = ["terraform", "cloudformation", "infrastructure as code", "iac", 
                       "pulumi", "arm template", "bicep", "cdk", "serverless framework"]
        
        raw_text = resume_data.get("raw_text", "").lower()
        
        return any(keyword in raw_text for keyword in iac_keywords)
    
    def _has_automation_experience(self, resume_data: Dict[str, Any]) -> bool:
        """Check if the resume mentions automation experience"""
        automation_keywords = ["automat", "script", "pipeline", "ci/cd", "continuous integration",
                             "ansible", "puppet", "chef", "salt", "cron", "shell script", "python script"]
        
        raw_text = resume_data.get("raw_text", "").lower()
        
        return any(keyword in raw_text for keyword in automation_keywords)
    
    def _extract_cloud_experience(self, resume_data: Dict[str, Any]) -> str:
        """Extract cloud-specific experience from the resume"""
        raw_text = resume_data.get("raw_text", "").lower()
        sections = resume_data.get("sections", {})
        
        # Cloud related keywords to look for
        cloud_keywords = ["aws", "amazon web services", "ec2", "s3", "rds", "lambda", "azure",
                         "microsoft azure", "app service", "azure functions", "gcp", "google cloud",
                         "compute engine", "cloud", "iaas", "paas", "saas", "vpc", "subnet",
                         "security group", "cloud formation", "terraform", "load balancer"]
        
        # Look for paragraphs with cloud mentions
        cloud_experience = ""
        
        # First look in work experiences
        work_experiences = resume_data.get("work_experience", [])
        for exp in work_experiences:
            description = exp.get("description", "").lower()
            if any(keyword in description for keyword in cloud_keywords):
                cloud_experience += f"At {exp.get('company', '')}: {exp.get('description', '')}\n\n"
                
            # Also check responsibilities
            responsibilities = exp.get("responsibilities", [])
            for resp in responsibilities:
                if any(keyword in resp.lower() for keyword in cloud_keywords):
                    cloud_experience += f"At {exp.get('company', '')}: {resp}\n"
        
        # If nothing found in experiences, check entire raw text
        if not cloud_experience:
            # Find sentences containing cloud keywords
            sentences = re.split(r'[.!?]+', raw_text)
            for sentence in sentences:
                if any(keyword in sentence for keyword in cloud_keywords):
                    cloud_experience += sentence.strip() + ".\n"
        
        if not cloud_experience:
            return "No specific cloud experience identified."
        
        return cloud_experience
    
    def _extract_cicd_experience(self, resume_data: Dict[str, Any]) -> str:
        """Extract CI/CD-specific experience from the resume"""
        raw_text = resume_data.get("raw_text", "").lower()
        sections = resume_data.get("sections", {})
        
        # CI/CD related keywords to look for
        cicd_keywords = ["ci/cd", "continuous integration", "continuous delivery", "continuous deployment",
                         "jenkins", "gitlab ci", "github actions", "azure devops", "pipeline", "build",
                         "release", "travis", "circleci", "codebuild", "argocd", "flux"]
        
        # Look for paragraphs with CI/CD mentions
        cicd_experience = ""
        
        # First look in work experiences
        work_experiences = resume_data.get("work_experience", [])
        for exp in work_experiences:
            description = exp.get("description", "").lower()
            if any(keyword in description for keyword in cicd_keywords):
                cicd_experience += f"At {exp.get('company', '')}: {exp.get('description', '')}\n\n"
                
            # Also check responsibilities
            responsibilities = exp.get("responsibilities", [])
            for resp in responsibilities:
                if any(keyword in resp.lower() for keyword in cicd_keywords):
                    cicd_experience += f"At {exp.get('company', '')}: {resp}\n"
        
        # If nothing found in experiences, check entire raw text
        if not cicd_experience:
            # Find sentences containing CI/CD keywords
            sentences = re.split(r'[.!?]+', raw_text)
            for sentence in sentences:
                if any(keyword in sentence for keyword in cicd_keywords):
                    cicd_experience += sentence.strip() + ".\n"
        
        if not cicd_experience:
            return "No specific CI/CD experience identified."
        
        return cicd_experience
    
    def _extract_container_experience(self, resume_data: Dict[str, Any]) -> str:
        """Extract container-specific experience from the resume"""
        raw_text = resume_data.get("raw_text", "").lower()
        sections = resume_data.get("sections", {})
        
        # Container related keywords to look for
        container_keywords = ["docker", "container", "kubernetes", "k8s", "pod", "deployment",
                             "cluster", "helm", "openshift", "rancher", "containerization",
                             "microservice", "service mesh", "istio", "linkerd", "docker-compose"]
        
        # Look for paragraphs with container mentions
        container_experience = ""
        
        # First look in work experiences
        work_experiences = resume_data.get("work_experience", [])
        for exp in work_experiences:
            description = exp.get("description", "").lower()
            if any(keyword in description for keyword in container_keywords):
                container_experience += f"At {exp.get('company', '')}: {exp.get('description', '')}\n\n"
                
            # Also check responsibilities
            responsibilities = exp.get("responsibilities", [])
            for resp in responsibilities:
                if any(keyword in resp.lower() for keyword in container_keywords):
                    container_experience += f"At {exp.get('company', '')}: {resp}\n"
        
        # If nothing found in experiences, check entire raw text
        if not container_experience:
            # Find sentences containing container keywords
            sentences = re.split(r'[.!?]+', raw_text)
            for sentence in sentences:
                if any(keyword in sentence for keyword in container_keywords):
                    container_experience += sentence.strip() + ".\n"
        
        if not container_experience:
            return "No specific container experience identified."
        
        return container_experience