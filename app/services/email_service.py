# app/services/email_service.py
import logging
import os
from typing import Dict, Any, Optional, BinaryIO
import base64
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for sending analysis results using Azure Communication Services"""
    
    def __init__(self):
        """Initialize the email service with Azure Communication Services credentials"""
        self.connection_string = settings.AZURE_COMMUNICATION_SERVICES_CONNECTION_STRING
        self.sender = settings.EMAIL_SENDER_ADDRESS
        self._client = None
        self.enabled = settings.EMAIL_ENABLED

    @property
    def client(self):
        """Lazy initialization of the Azure Communication Services email client"""
        if not self._client and self.enabled:
            try:
                # Import here to avoid startup errors if the package is not installed
                from azure.communication.email import EmailClient
                self._client = EmailClient.from_connection_string(self.connection_string)
                logger.info("Azure Communication Services email client initialized")
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
        Send analysis results email with PDF attachment
        
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
                    "subject": f"Your {target_role} Resume Analysis Results",
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
                        "name": f"{analysis_id}_resume_analysis.pdf",
                        "contentType": "application/pdf",
                        "contentInBase64": pdf_base64
                    }
                ]
            }
            
            # Send the email
            try:
                logger.info(f"Attempting to send email to {to_email}")
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
                            "subject": f"Your {target_role} Resume Analysis Results",
                            "plainText": f"Your resume analysis is complete. View your results at: {settings.APP_FRONTEND_URL}/analysis/{analysis_id}/results",
                            "html": f"<p>Your resume analysis is complete. <a href='{settings.APP_FRONTEND_URL}/analysis/{analysis_id}/results'>View your results online</a>.</p>"
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
        """Generate plain text email content"""
        return f"""
Hello {name},

Your resume analysis for the {target_role} position is now complete.

We've analyzed your resume and created a detailed report with actionable insights to help improve your chances of landing your target role.

The report includes:
- Overall score and assessment
- Detailed feedback on your technical skills
- Keyword analysis for better ATS optimization
- Gap analysis against the role requirements
- Actionable recommendations for improvement

Please find your complete analysis report attached to this email.

You can also view your results online at:
{settings.APP_FRONTEND_URL}/analysis/{analysis_id}/results

Thank you for using our AI Resume Analyzer!

Best regards,
The Teleios Team
        """
    
    def _get_html_content(self, name: str, target_role: str, analysis_id: str) -> str:
        """Generate HTML email content"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume Analysis Results</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #4a6cf7;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }}
        .content {{
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 0 0 5px 5px;
            border: 1px solid #ddd;
            border-top: none;
        }}
        .button {{
            display: inline-block;
            background-color: #4a6cf7;
            color: white;
            padding: 12px 20px;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 20px;
        }}
        .footer {{
            margin-top: 20px;
            text-align: center;
            font-size: 12px;
            color: #777;
        }}
        ul {{
            padding-left: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Your Resume Analysis is Ready!</h1>
    </div>
    <div class="content">
        <p>Hello {name},</p>
        
        <p>Your resume analysis for the <strong>{target_role}</strong> position is now complete.</p>
        
        <p>We've analyzed your resume and created a detailed report with actionable insights to help improve your chances of landing your target role.</p>
        
        <p>The report includes:</p>
        <ul>
            <li>Overall score and assessment</li>
            <li>Detailed feedback on your technical skills</li>
            <li>Keyword analysis for better ATS optimization</li>
            <li>Gap analysis against the role requirements</li>
            <li>Actionable recommendations for improvement</li>
        </ul>
        
        <p><strong>Your detailed analysis report is attached to this email.</strong></p>
        
        <p>You can also view your results online:</p>
        
        <a href="{settings.APP_FRONTEND_URL}/analysis/{analysis_id}/results" class="button">View Online Results</a>
        
        <p>Thank you for using our AI Resume Analyzer!</p>
        
        <p>Best regards,<br>The Teleios Team</p>
    </div>
    <div class="footer">
        <p>© {datetime.now().year} Teleios. All rights reserved.</p>
        <p>This is an automated message. Please do not reply to this email.</p>
    </div>
</body>
</html>
        """

# Singleton instance
email_service = EmailService()

# For backward compatibility with existing code
async def send_analysis_completion_email(
    to_email: str,
    name: str,
    analysis_id: str,
    target_role: str,
    overall_score: int,
    pdf_attachment: Optional[BinaryIO] = None
) -> bool:
    """
    Backward compatible function for sending analysis completion email
    
    Args:
        to_email: Recipient email address
        name: Recipient name
        analysis_id: Analysis ID
        target_role: Target role that was analyzed
        overall_score: Overall score from the analysis
        pdf_attachment: Optional PDF attachment
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    if pdf_attachment:
        return await email_service.send_analysis_completion_email(
            to_email=to_email,
            name=name,
            analysis_id=analysis_id,
            target_role=target_role,
            pdf_attachment=pdf_attachment
        )
    else:
        logger.warning("No PDF attachment provided. Email not sent.")
        return False