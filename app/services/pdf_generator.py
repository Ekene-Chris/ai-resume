# app/services/pdf_generator.py
import logging
import io
from typing import Dict, Any, BinaryIO
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class PDFGenerator:
    """Service for generating PDF reports of resume analyses"""
    
    def __init__(self):
        """Initialize the PDF generator"""
        # Try to import the required libraries
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
            
            self.reportlab_available = True
            logger.info("ReportLab library initialized successfully")
        except ImportError:
            self.reportlab_available = False
            logger.error("ReportLab library not available. PDF generation will be disabled.")
    
    def generate_analysis_report(
        self,
        analysis_data: Dict[str, Any],
        name: str,
        email: str,
        target_role: str
    ) -> BinaryIO:
        """
        Generate a PDF report for the resume analysis
        
        Args:
            analysis_data: The analysis data from Azure OpenAI
            name: Candidate's name
            email: Candidate's email
            target_role: The target role
            
        Returns:
            PDF file as a binary stream
        """
        if not self.reportlab_available:
            raise ImportError("ReportLab library is required for PDF generation")
            
        # Import reportlab components
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem, Image
        from reportlab.lib.units import inch
        
        try:
            # Create a buffer for the PDF
            buffer = io.BytesIO()
            
            # Create the document template
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = styles["Title"]
            heading_style = styles["Heading1"]
            heading2_style = styles["Heading2"]
            normal_style = styles["Normal"]
            
            # Custom styles
            score_style = ParagraphStyle(
                "ScoreStyle",
                parent=styles["Heading1"],
                alignment=1,  # Center alignment
            )
            
            # Add custom styles
            category_heading = ParagraphStyle(
                "CategoryHeading",
                parent=styles["Heading2"],
                fontSize=14,
                spaceAfter=6
            )
            
            list_item_style = ParagraphStyle(
                "ListItem",
                parent=styles["Normal"],
                leftIndent=20
            )
            
            # Create document elements
            elements = []
            
            # Try to add logo if it exists
            try:
                # Check if logo file exists
                if os.path.exists("app/static/images/teleios_logo.png"):
                    logo = Image("app/static/images/teleios_logo.png", width=2*inch, height=0.75*inch)
                    elements.append(logo)
                    elements.append(Spacer(1, 12))
            except Exception as e:
                logger.warning(f"Could not add logo to PDF: {str(e)}")

            # Title
            elements.append(Paragraph(f"Resume Analysis Report", title_style))
            elements.append(Spacer(1, 12))
            
            # Date
            date_str = datetime.now().strftime("%B %d, %Y")
            elements.append(Paragraph(f"Generated on: {date_str}", normal_style))
            elements.append(Spacer(1, 24))
            
            # Candidate Info
            elements.append(Paragraph("Candidate Information", heading_style))
            elements.append(Spacer(1, 6))
            
            candidate_data = [
                ["Name:", name],
                ["Email:", email],
                ["Target Role:", target_role],
                ["Experience Level:", analysis_data.get("matrix_alignment", {}).get("target_level", "Not specified").capitalize()]
            ]
            
            candidate_table = Table(candidate_data, colWidths=[100, 350])
            candidate_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                ('ALIGNMENT', (0, 0), (0, -1), 'RIGHT'),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(candidate_table)
            elements.append(Spacer(1, 24))
            
            # Overall Score
            overall_score = analysis_data.get("overall_score", 0)
            elements.append(Paragraph("Overall Assessment", heading_style))
            elements.append(Spacer(1, 6))
            
            score_text = f"Score: {overall_score}/100"
            elements.append(Paragraph(score_text, score_style))
            elements.append(Spacer(1, 12))
            
            # Score interpretation
            if overall_score >= 85:
                score_interpretation = "Excellent match for the role. Your resume demonstrates strong alignment with the requirements."
            elif overall_score >= 70:
                score_interpretation = "Good match for the role. Your resume shows good alignment with most key requirements."
            elif overall_score >= 50:
                score_interpretation = "Moderate match. There are some areas that could be improved to better align with the role."
            else:
                score_interpretation = "Additional work needed. Your resume needs significant improvements to align with the role requirements."
                
            elements.append(Paragraph(f"Assessment: {score_interpretation}", normal_style))
            elements.append(Spacer(1, 24))
            
            # Summary
            summary = analysis_data.get("summary", "No summary available.")
            elements.append(Paragraph("Executive Summary", heading_style))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(summary, normal_style))
            elements.append(Spacer(1, 24))
            
            # Detailed Category Analysis
            elements.append(Paragraph("Detailed Analysis", heading_style))
            elements.append(Spacer(1, 12))
            
            categories = analysis_data.get("categories", [])
            for category in categories:
                name = category.get("name", "Unnamed Category")
                score = category.get("score", 0)
                feedback = category.get("feedback", "No feedback provided.")
                suggestions = category.get("suggestions", [])
                
                elements.append(Paragraph(f"{name} - {score}/100", category_heading))
                elements.append(Paragraph(feedback, normal_style))
                elements.append(Spacer(1, 6))
                
                if suggestions:
                    elements.append(Paragraph("Suggestions for Improvement:", normal_style))
                    
                    suggestion_items = []
                    for suggestion in suggestions:
                        suggestion_items.append(ListItem(Paragraph(suggestion, list_item_style)))
                    
                    suggestion_list = ListFlowable(
                        suggestion_items,
                        bulletType='bullet',
                        start='•'
                    )
                    elements.append(suggestion_list)
                
                elements.append(Spacer(1, 12))
            
            # Keyword Analysis
            elements.append(Paragraph("Keyword Analysis", heading_style))
            elements.append(Spacer(1, 6))
            
            keyword_analysis = analysis_data.get("keyword_analysis", {})
            present_keywords = keyword_analysis.get("present", [])
            missing_keywords = keyword_analysis.get("missing", [])
            recommended_keywords = keyword_analysis.get("recommended", [])
            
            elements.append(Paragraph("Keywords Present in Your Resume:", heading2_style))
            if present_keywords:
                elements.append(Paragraph(", ".join(present_keywords), normal_style))
            else:
                elements.append(Paragraph("No keywords detected.", normal_style))
                
            elements.append(Spacer(1, 12))
            
            elements.append(Paragraph("Important Keywords Missing from Your Resume:", heading2_style))
            if missing_keywords:
                missing_items = []
                for keyword in missing_keywords:
                    missing_items.append(ListItem(Paragraph(keyword, list_item_style)))
                
                missing_list = ListFlowable(
                    missing_items,
                    bulletType='bullet',
                    start='•'
                )
                elements.append(missing_list)
            else:
                elements.append(Paragraph("No critical keywords missing.", normal_style))
                
            elements.append(Spacer(1, 12))
            
            elements.append(Paragraph("Recommended Keywords to Add:", heading2_style))
            if recommended_keywords:
                recommended_items = []
                for keyword in recommended_keywords:
                    recommended_items.append(ListItem(Paragraph(keyword, list_item_style)))
                
                recommended_list = ListFlowable(
                    recommended_items,
                    bulletType='bullet',
                    start='•'
                )
                elements.append(recommended_list)
            else:
                elements.append(Paragraph("No additional keywords recommended.", normal_style))
                
            elements.append(Spacer(1, 24))
            
            # Matrix Alignment
            elements.append(Paragraph("Skills Matrix Alignment", heading_style))
            elements.append(Spacer(1, 6))
            
            matrix_alignment = analysis_data.get("matrix_alignment", {})
            current_level = matrix_alignment.get("current_level", "Unknown")
            target_level = matrix_alignment.get("target_level", "Unknown")
            gap_areas = matrix_alignment.get("gap_areas", [])
            
            elements.append(Paragraph(f"Current Level: {current_level.capitalize()}", normal_style))
            elements.append(Paragraph(f"Target Level: {target_level.capitalize()}", normal_style))
            elements.append(Spacer(1, 12))
            
            elements.append(Paragraph("Gap Areas to Address:", heading2_style))
            if gap_areas:
                gap_items = []
                for gap in gap_areas:
                    gap_items.append(ListItem(Paragraph(gap, list_item_style)))
                
                gap_list = ListFlowable(
                    gap_items,
                    bulletType='bullet',
                    start='•'
                )
                elements.append(gap_list)
            else:
                elements.append(Paragraph("No significant gaps identified.", normal_style))
                
            elements.append(Spacer(1, 24))
            
            # Next Steps
            elements.append(Paragraph("Recommended Next Steps", heading_style))
            elements.append(Spacer(1, 6))
            
            # Generate appropriate next steps based on score
            next_steps = []
            if overall_score < 50:
                next_steps = [
                    "Revise your resume structure to highlight relevant skills and experience",
                    "Add missing keywords and technical skills",
                    "Quantify your achievements with specific metrics",
                    "Consider additional training or certification in gap areas",
                    "Create a targeted cover letter that addresses your transition to this role"
                ]
            elif overall_score < 70:
                next_steps = [
                    "Enhance descriptions of your most relevant projects",
                    "Add missing technical keywords",
                    "Ensure achievements are quantified with metrics where possible",
                    "Address the specific gap areas mentioned above",
                    "Tailor your resume for each specific job application"
                ]
            else:
                next_steps = [
                    "Fine-tune your resume with the recommended keywords",
                    "Highlight your most impressive achievements even more prominently",
                    "Consider creating a portfolio to showcase relevant projects",
                    "Prepare to discuss your experience in the gap areas during interviews",
                    "Research target companies to customize your applications further"
                ]
                
            step_items = []
            for step in next_steps:
                step_items.append(ListItem(Paragraph(step, list_item_style)))
                
            step_list = ListFlowable(
                step_items,
                bulletType='bullet',
                start='•'
            )
            elements.append(step_list)
            
            # Footer
            elements.append(Spacer(1, 36))
            elements.append(Paragraph("Powered by Teleios AI Resume Analyzer", ParagraphStyle(
                "Footer", 
                parent=styles["Normal"],
                alignment=1,  # Center alignment
                textColor=colors.grey
            )))
            
            # Build the PDF
            doc.build(elements)
            
            # Reset buffer position
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}", exc_info=True)
            raise
    
# Create singleton instance
pdf_generator = PDFGenerator()