# app/services/email_service.py - Customized for Ekene Chris brand
import logging
import os
from typing import Dict, Any, Optional, BinaryIO
import base64
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for sending branded analysis results using Azure Communication Services"""
    
    def __init__(self):
        """Initialize the email service with Azure Communication Services credentials"""
        self.connection_string = settings.AZURE_COMMUNICATION_SERVICES_CONNECTION_STRING
        self.sender = settings.EMAIL_SENDER_ADDRESS
        self._client = None
        self.enabled = settings.EMAIL_ENABLED
        
        # Ekene Chris brand settings
        self.brand_name = "Ekene Chris - DevOps Career Acceleration"
        self.brand_colors = {
            'primary': "#592429",  # Caput Mortuum
            'secondary': "#FFD700",  # Gold
            'background': "#FFF4E9",  # Linen
            'text': "#070402"  # Deep Black
        }
        self.logo_url = "https://ekenechris.com/logo.png"  # Update with your actual logo URL
        self.website_url = "https://ekenechris.com"
        self.teleios_url = "https://jointeleios.com"

    @property
    def client(self):
        """Lazy initialization of the Azure Communication Services email client"""
        if not self._client and self.enabled:
            try:
                # Import here to avoid startup errors if the package is not installed
                from azure.communication.email import EmailClient
                self._client = EmailClient.from_connection_string(self.connection_string)
                logger.info("Azure Communication Services email client initialized with Ekene Chris branding")
            except Exception as e:
                logger.error(f"Failed to initialize email client: {str(e)}")
                self.enabled = False
                
        return self._client

    async def send_analysis_completion_email(
        self,
        to_email: str,
        name: str,
        analysis_id: str,
        target_role: str,
        pdf_attachment: BinaryIO
    ) -> bool:
        """
        Send analysis results email with PDF attachment using Ekene Chris branding
        
        Args:
            to_email: Recipient email address
            name: Recipient name
            analysis_id: Analysis ID
            target_role: Target role that was analyzed
            pdf_attachment: PDF report as binary data
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service is disabled. Not sending email.")
            return False
            
        try:
            # Only import the EmailClient class
            from azure.communication.email import EmailClient
            
            # Read the PDF data
            pdf_data = pdf_attachment.read()
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            # Create the email message using dictionary structure
            # This avoids importing specific classes that might change across SDK versions
            message = {
                "content": {
                    "subject": f"Your {target_role} Resume Analysis Results - Ekene Chris Career Acceleration",
                    "plainText": self._get_plain_text_content(name, target_role, analysis_id),
                    "html": self._get_html_content(name, target_role, analysis_id)
                },
                "recipients": {
                    "to": [
                        {
                            "address": to_email,
                            "displayName": name
                        }
                    ]
                },
                "senderAddress": self.sender,
                "attachments": [
                    {
                        "name": f"Resume_Analysis_{target_role.replace(' ', '_')}.pdf",
                        "contentType": "application/pdf",
                        "contentInBase64": pdf_base64
                    }
                ]
            }
            
            # Send the email
            try:
                logger.info(f"Sending branded email to {to_email}")
                poller = self.client.begin_send(message)
                result = poller.result()
                logger.info(f"Email sent successfully to {to_email}")
                return True
            except Exception as e:
                logger.error(f"Failed to send email with attachment: {str(e)}")
                
                # Attempt to send a simple email without the attachment
                try:
                    logger.info("Attempting to send email without attachment")
                    simple_message = {
                        "content": {
                            "subject": f"Your {target_role} Resume Analysis Results - Ekene Chris",
                            "plainText": f"Your resume analysis is complete. View your results at: {settings.APP_FRONTEND_URL}/analysis/{analysis_id}/results",
                            "html": self._get_simplified_html_content(name, target_role, analysis_id)
                        },
                        "recipients": {
                            "to": [
                                {
                                    "address": to_email,
                                    "displayName": name
                                }
                            ]
                        },
                        "senderAddress": self.sender
                    }
                    
                    poller = self.client.begin_send(simple_message)
                    result = poller.result()
                    logger.info(f"Simple email sent successfully to {to_email}")
                    return True
                except Exception as inner_e:
                    logger.error(f"Failed to send simple email: {str(inner_e)}")
                    return False
        except Exception as e:
            logger.error(f"Error in email service: {str(e)}")
            return False
    
    def _get_plain_text_content(self, name: str, target_role: str, analysis_id: str) -> str:
        """Generate plain text email content with Ekene Chris branding"""
        return f"""
Hello {name},

Your resume analysis for the {target_role} position is now complete.

I've analyzed your resume and created a detailed report with actionable insights to help improve your chances of landing your target role and accelerating your tech career.

The report includes:
- Overall score and assessment aligned with industry standards
- Detailed feedback on your technical skills and experience
- Keyword analysis for better visibility with hiring managers
- Gap analysis against the Global DevOps Competency Matrix
- Actionable recommendations for improvement and career acceleration

Please find your complete analysis report attached to this email.

You can also view your results online at:
{settings.APP_FRONTEND_URL}/analysis/{analysis_id}/results

NEXT STEPS:
1. Review your analysis report in detail
2. Implement the suggested improvements to your resume
3. Visit https://jointeleios.com to learn about our exclusive tech learning platform
4. Subscribe to our newsletter for ongoing career development insights

"Technical excellence is not just about what you know, but how effectively you demonstrate that knowledge in ways that create disproportionate value."

Thank you for using our AI Resume Analyzer!

Best regards,
Ekene Chris
DevOps Architect & Technical Educator
https://ekenechris.com
        """
    
    def _get_html_content(self, name: str, target_role: str, analysis_id: str) -> str:
        """Generate HTML email content with full Ekene Chris branding"""
        results_url = f"{settings.APP_FRONTEND_URL}/analysis/{analysis_id}/results"
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Resume Analysis Results</title>
    <style>
        body {{
            font-family: 'Avenir', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: {self.brand_colors['text']};
            max-width: 600px;
            margin: 0 auto;
            background-color: {self.brand_colors['background']};
        }}
        .header {{
            padding: 30px 20px 20px;
            text-align: center;
        }}
        .logo {{
            margin-bottom: 20px;
            max-width: 180px;
        }}
        .header h1 {{
            margin: 0;
            font-weight: bold;
            font-size: 24px;
            color: {self.brand_colors['primary']};
        }}
        .content {{
            background-color: {self.brand_colors['background']};
            padding: 30px 25px;
            border-radius: 4px;
            border-top: 3px solid {self.brand_colors['primary']};
        }}
        .main-banner {{
            background-color: {self.brand_colors['primary']};
            color: white;
            padding: 20px;
            border-radius: 4px;
            margin-bottom: 25px;
            text-align: center;
        }}
        .main-banner h2 {{
            margin: 0;
            font-size: 20px;
        }}
        .section {{
            margin-bottom: 25px;
        }}
        .section h3 {{
            color: {self.brand_colors['primary']};
            margin-top: 0;
            border-bottom: 1px solid #E8E0D9;
            padding-bottom: 8px;
            font-size: 18px;
        }}
        .button {{
            display: inline-block;
            background-color: {self.brand_colors['primary']};
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
            margin-top: 15px;
            margin-bottom: 15px;
            text-align: center;
        }}
        .button:hover {{
            background-color: #4a1e23;
        }}
        .results-highlight {{
            background-color: #f9f4ef;
            border-left: 3px solid {self.brand_colors['secondary']};
            padding: 15px;
            margin-bottom: 20px;
        }}
        .results-highlight p {{
            margin: 0 0 10px 0;
        }}
        .score {{
            font-size: 22px;
            font-weight: bold;
            color: {self.brand_colors['primary']};
        }}
        ul {{
            padding-left: 20px;
            margin-bottom: 20px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            font-size: 14px;
            color: #666;
            border-top: 1px solid #E8E0D9;
        }}
        .social-links {{
            margin: 15px 0;
        }}
        .social-links a {{
            display: inline-block;
            margin: 0 8px;
            color: {self.brand_colors['primary']};
            text-decoration: none;
        }}
        .quote {{
            font-style: italic;
            padding: 15px;
            border-left: 3px solid {self.brand_colors['primary']};
            background-color: #f9f4ef;
            margin: 20px 0;
        }}
        .values {{
            text-align: center;
            font-size: 12px;
            margin: 10px 0;
            color: #666;
        }}
        @media only screen and (max-width: 480px) {{
            .content {{
                padding: 20px 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <img src="{self.logo_url}" alt="Ekene Chris Logo" class="logo">
        <h1>DevOps Career Acceleration</h1>
    </div>
    
    <div class="content">
        <div class="main-banner">
            <h2>Your Resume Analysis is Complete</h2>
        </div>
        
        <div class="section">
            <p>Hello {name},</p>
            
            <p>Your resume analysis for the <strong>{target_role}</strong> position is now complete. This AI-powered assessment provides actionable insights to help you align your resume with industry expectations and advance your tech career.</p>
            
            <div class="results-highlight">
                <p>Target Role: <strong>{target_role}</strong></p>
                <p>Analysis Completed: <strong>{datetime.now().strftime("%B %d, %Y")}</strong></p>
            </div>
            
            <p>Your comprehensive analysis report includes:</p>
            <ul>
                <li>Technical skills assessment with specific feedback</li>
                <li>Keyword optimization for better visibility with hiring managers</li>
                <li>Gap analysis against Global DevOps Competency Matrix standards</li>
                <li>Actionable recommendations to strengthen your profile</li>
                <li>Career advancement strategies based on current market demands</li>
            </ul>
            
            <p><strong>Your detailed analysis report is attached to this email.</strong></p>
        </div>
        
        <div class="section">
            <h3>Next Steps</h3>
            <p>To view your analysis online:</p>
            <div style="text-align: center;">
                <a href="{results_url}" class="button">View Full Analysis</a>
            </div>
            
            <div class="quote">
                "Technical excellence is not just about what you know, but how effectively you demonstrate that knowledge in ways that create disproportionate value."
            </div>
            
            <p>After reviewing your analysis, consider these next steps:</p>
            <ul>
                <li>Implement the suggested improvements to your resume</li>
                <li>Focus on closing the identified skill gaps</li>
                <li>Connect with our community for ongoing career guidance</li>
            </ul>
        </div>
        
        <div class="section">
            <h3>Elevate Your Tech Career with Teleios</h3>
            <p>If you're ready to accelerate your tech career and compete globally, explore Teleios - our exclusive tech learning platform designed for ambitious engineers:</p>
            <ul>
                <li>Join a selective community of exceptional engineers</li>
                <li>Learn advanced DevOps concepts through real-world projects</li>
                <li>Receive 1:1 mentorship from industry experts</li>
                <li>Build a portfolio that demonstrates senior-level capabilities</li>
            </ul>
            <div style="text-align: center;">
                <a href="{self.teleios_url}" class="button">Learn More About Teleios</a>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <div class="values">
            Innovation · Mentorship · Adaptability · Growth · Excellence
        </div>
        <p>Helping African engineers compete globally through technical excellence</p>
        <div class="social-links">
            <a href="https://twitter.com/ekenechris">Twitter</a> | 
            <a href="https://linkedin.com/in/ekenechris">LinkedIn</a> | 
            <a href="{self.website_url}">ekenechris.com</a>
        </div>
        <p>&copy; {datetime.now().year} Ekene Chris. All rights reserved.</p>
        <p>This is an automated message. Please do not reply to this email.</p>
    </div>
</body>
</html>
        """
    
    def _get_simplified_html_content(self, name: str, target_role: str, analysis_id: str) -> str:
        """Generate simplified HTML email content with Ekene Chris branding"""
        results_url = f"{settings.APP_FRONTEND_URL}/analysis/{analysis_id}/results"
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Resume Analysis Results</title>
    <style>
        body {{
            font-family: 'Avenir', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: {self.brand_colors['text']};
            margin: 0;
            padding: 20px;
            background-color: {self.brand_colors['background']};
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            overflow: hidden;
        }}
        .header {{
            background-color: {self.brand_colors['primary']};
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .content {{
            padding: 20px;
        }}
        .button {{
            display: inline-block;
            background-color: {self.brand_colors['primary']};
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
        }}
        .footer {{
            background-color: #f7f7f7;
            padding: 15px;
            text-align: center;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Resume Analysis Complete</h1>
        </div>
        
        <div class="content">
            <p>Hello {name},</p>
            
            <p>Your resume analysis for the <strong>{target_role}</strong> position is now complete.</p>
            
            <p>Due to technical limitations, we weren't able to attach your full report to this email, but you can view your complete analysis online:</p>
            
            <p style="text-align: center;">
                <a href="{results_url}" class="button">View Your Analysis</a>
            </p>
            
            <p>After reviewing your analysis, explore <a href="{self.teleios_url}">Teleios</a> - our exclusive learning platform designed to close skill gaps and accelerate your tech career.</p>
        </div>
        
        <div class="footer">
            <p>&copy; {datetime.now().year} Ekene Chris | <a href="{self.website_url}">{self.website_url}</a></p>
        </div>
    </div>
</body>
</html>
        """

# Singleton instance
email_service = EmailService()