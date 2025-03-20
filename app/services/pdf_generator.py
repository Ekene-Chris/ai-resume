# app/services/pdf_generator.py - Updated to be generic for all engineering roles
import logging
import io
from typing import Dict, Any, BinaryIO
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class PDFGenerator:
    """Service for generating branded PDF reports of resume analyses for all engineering roles"""
    
    def __init__(self):
        """Initialize the PDF generator with Ekene Chris brand styles"""
        # Try to import the required libraries
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem, Image
            from reportlab.lib.units import inch
            
            # Define brand colors
            self.colors = {
                'linen': colors.Color(255/255, 244/255, 233/255),  # #FFF4E9
                'caput_mortuum': colors.Color(89/255, 36/255, 41/255),  # #592429
                'black': colors.Color(7/255, 4/255, 2/255),  # #070402
                'gold': colors.Color(255/255, 215/255, 0/255),  # #FFD700
            }
            
            self.reportlab_available = True
            logger.info("ReportLab library initialized successfully with Ekene Chris brand colors")
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
        Generate a branded PDF report for the resume analysis
        
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
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        
        try:
            # Create a buffer for the PDF
            buffer = io.BytesIO()
            
            # Create the document template
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch,
                title=f"Resume Analysis for {name} - {target_role}"
            )
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Custom styles with Ekene Chris branding
            title_style = ParagraphStyle(
                'EkeneTitle',
                parent=styles["Title"],
                fontName='Helvetica-Bold',
                fontSize=22,
                textColor=self.colors['caput_mortuum'],
                spaceAfter=24,
                alignment=TA_LEFT
            )
            
            subtitle_style = ParagraphStyle(
                'EkeneSubtitle',
                parent=styles["Heading2"],
                fontName='Helvetica-Bold',
                fontSize=16,
                textColor=self.colors['caput_mortuum'],
                spaceBefore=12,
                spaceAfter=6
            )
            
            heading_style = ParagraphStyle(
                'EkeneHeading1',
                parent=styles["Heading1"],
                fontName='Helvetica-Bold',
                fontSize=14,
                textColor=self.colors['caput_mortuum'],
                spaceBefore=16,
                spaceAfter=8
            )
            
            normal_style = ParagraphStyle(
                'EkeneNormal',
                parent=styles["Normal"],
                fontName='Helvetica',
                fontSize=10,
                textColor=self.colors['black'],
                spaceBefore=6,
                spaceAfter=6
            )
            
            score_style = ParagraphStyle(
                "EkeneScoreStyle",
                parent=styles["Heading1"],
                fontName='Helvetica-Bold',
                fontSize=24,
                textColor=self.colors['caput_mortuum'],
                alignment=TA_CENTER,
                spaceBefore=12,
                spaceAfter=12
            )
            
            category_heading = ParagraphStyle(
                "EkeneCategoryHeading",
                parent=styles["Heading2"],
                fontName='Helvetica-Bold',
                fontSize=14,
                textColor=self.colors['caput_mortuum'],
                spaceBefore=14,
                spaceAfter=6
            )
            
            list_item_style = ParagraphStyle(
                "EkeneListItem",
                parent=styles["Normal"],
                fontName='Helvetica',
                fontSize=10,
                leftIndent=20,
                textColor=self.colors['black']
            )
            
            quote_style = ParagraphStyle(
                "EkeneQuote",
                parent=styles["Italic"],
                fontName='Helvetica-Oblique',
                fontSize=10,
                leftIndent=30,
                rightIndent=30,
                spaceBefore=12,
                spaceAfter=12,
                textColor=self.colors['caput_mortuum']
            )
            
            footer_style = ParagraphStyle(
                "EkeneFooter",
                parent=styles["Normal"],
                fontName='Helvetica',
                fontSize=8,
                alignment=TA_CENTER,
                textColor=colors.gray
            )
            
            # Create document elements
            elements = []
            
            # Try to add logo if it exists
            try:
                # Check if logo file exists
                if os.path.exists("app/static/images/ekene_chris_logo.png"):
                    logo = Image("app/static/images/ekene_chris_logo.png", width=2*inch, height=0.75*inch)
                    elements.append(logo)
                    elements.append(Spacer(1, 12))
            except Exception as e:
                logger.warning(f"Could not add logo to PDF: {str(e)}")

            # Title
            elements.append(Paragraph(f"Resume Analysis Report", title_style))
            elements.append(Spacer(1, 6))
            
            # Date
            date_str = datetime.now().strftime("%B %d, %Y")
            elements.append(Paragraph(f"Generated on: {date_str}", normal_style))
            elements.append(Spacer(1, 24))
            
            # Quote about career advancement
            elements.append(Paragraph(
                "\"Technical excellence is not just about what you know, but how effectively you demonstrate that knowledge in ways that create disproportionate value.\"", 
                quote_style
            ))
            
            # Candidate Info
            elements.append(Paragraph("Candidate Information", heading_style))
            elements.append(Spacer(1, 6))
            
            candidate_data = [
                ["Name:", name],
                ["Email:", email],
                ["Target Role:", target_role],
                ["Experience Level:", analysis_data.get("matrix_alignment", {}).get("target_level", "Not specified").capitalize()]
            ]
            
            candidate_table = Table(candidate_data, colWidths=[1.5*inch, 5*inch])
            candidate_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('BACKGROUND', (0, 0), (0, -1), self.colors['caput_mortuum']),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
                ('ALIGNMENT', (0, 0), (0, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
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
                score_color = self.colors['gold']
            elif overall_score >= 70:
                score_interpretation = "Good match for the role. Your resume shows good alignment with most key requirements."
                score_color = colors.green
            elif overall_score >= 50:
                score_interpretation = "Moderate match. There are some areas that could be improved to better align with the role."
                score_color = colors.orange
            else:
                score_interpretation = "Additional work needed. Your resume needs significant improvements to align with the role requirements."
                score_color = colors.red
                
            # Add score indicator with colored background
            score_indicator = Table([[score_interpretation]], colWidths=[6.5*inch])
            score_indicator.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), score_color),
                ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
                ('ALIGNMENT', (0, 0), (0, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('PADDING', (0, 0), (0, 0), 8),
            ]))
            
            elements.append(score_indicator)
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
                
                # Create a colored category header based on score
                if score >= 85:
                    category_color = self.colors['gold']
                elif score >= 70:
                    category_color = colors.green
                elif score >= 50:
                    category_color = colors.orange
                else:
                    category_color = colors.red
                
                category_header = Table([[f"{name} - {score}/100"]], colWidths=[6.5*inch])
                category_header.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, 0), self.colors['caput_mortuum']),
                    ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
                    ('ALIGNMENT', (0, 0), (0, 0), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                    ('PADDING', (0, 0), (0, 0), 8),
                ]))
                
                elements.append(category_header)
                elements.append(Spacer(1, 6))
                elements.append(Paragraph(feedback, normal_style))
                elements.append(Spacer(1, 6))
                
                if suggestions:
                    elements.append(Paragraph("Suggestions for Improvement:", subtitle_style))
                    
                    suggestion_items = []
                    for suggestion in suggestions:
                        suggestion_items.append(ListItem(Paragraph(suggestion, list_item_style)))
                    
                    suggestion_list = ListFlowable(
                        suggestion_items,
                        bulletType='bullet',
                        start='•',
                        bulletFontName='Helvetica',
                        bulletFontSize=10
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
            
            # Create a nice table for present keywords
            elements.append(Paragraph("Keywords Present in Your Resume:", subtitle_style))
            if present_keywords:
                # Create a multi-column table for keywords
                keyword_rows = []
                row = []
                for i, keyword in enumerate(present_keywords):
                    row.append(keyword)
                    if (i + 1) % 3 == 0 or i == len(present_keywords) - 1:
                        # Pad row if needed
                        while len(row) < 3:
                            row.append("")
                        keyword_rows.append(row)
                        row = []
                
                present_table = Table(keyword_rows, colWidths=[2.17*inch, 2.17*inch, 2.16*inch])
                present_table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
                    ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
                    ('PADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(present_table)
            else:
                elements.append(Paragraph("No keywords detected.", normal_style))
                
            elements.append(Spacer(1, 12))
            
            # Missing keywords with colored background for emphasis
            elements.append(Paragraph("Important Keywords Missing from Your Resume:", subtitle_style))
            if missing_keywords:
                # Create a multi-column table for missing keywords with highlighted background
                missing_rows = []
                row = []
                for i, keyword in enumerate(missing_keywords):
                    row.append(keyword)
                    if (i + 1) % 3 == 0 or i == len(missing_keywords) - 1:
                        # Pad row if needed
                        while len(row) < 3:
                            row.append("")
                        missing_rows.append(row)
                        row = []
                
                missing_table = Table(missing_rows, colWidths=[2.17*inch, 2.17*inch, 2.16*inch])
                missing_table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.lavender),
                    ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
                    ('PADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(missing_table)
            else:
                elements.append(Paragraph("No critical keywords missing.", normal_style))
                
            elements.append(Spacer(1, 12))
            
            # Recommended keywords with gold background
            elements.append(Paragraph("Recommended Keywords to Add:", subtitle_style))
            if recommended_keywords:
                # Create a multi-column table for recommended keywords with highlighted background
                recommended_rows = []
                row = []
                for i, keyword in enumerate(recommended_keywords):
                    row.append(keyword)
                    if (i + 1) % 3 == 0 or i == len(recommended_keywords) - 1:
                        # Pad row if needed
                        while len(row) < 3:
                            row.append("")
                        recommended_rows.append(row)
                        row = []
                
                recommended_table = Table(recommended_rows, colWidths=[2.17*inch, 2.17*inch, 2.16*inch])
                recommended_table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.lightyellow),
                    ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
                    ('PADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(recommended_table)
            else:
                elements.append(Paragraph("No additional keywords recommended.", normal_style))
                
            elements.append(Spacer(1, 24))
            
            # Matrix Alignment with Engineering Competency Matrix
            elements.append(Paragraph("Global Engineering Competency Matrix Alignment", heading_style))
            elements.append(Spacer(1, 6))
            
            matrix_alignment = analysis_data.get("matrix_alignment", {})
            current_level = matrix_alignment.get("current_level", "Unknown")
            target_level = matrix_alignment.get("target_level", "Unknown")
            gap_areas = matrix_alignment.get("gap_areas", [])
            
            # Create a visual representation of the levels
            level_data = [["Junior", "Mid", "Senior", "Staff"]]
            level_table = Table(level_data, colWidths=[1.625*inch, 1.625*inch, 1.625*inch, 1.625*inch])
            
            # Set up styles for the level indicators
            level_styles = [
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]
            
            # Highlight current and target levels
            levels = ["junior", "mid", "senior", "staff"]
            current_idx = levels.index(current_level.lower()) if current_level.lower() in levels else -1
            target_idx = levels.index(target_level.lower()) if target_level.lower() in levels else -1
            
            if current_idx >= 0:
                level_styles.append(('BACKGROUND', (current_idx, 0), (current_idx, 0), colors.lightblue))
                level_styles.append(('TEXTCOLOR', (current_idx, 0), (current_idx, 0), colors.black))
            
            if target_idx >= 0 and target_idx != current_idx:
                level_styles.append(('BACKGROUND', (target_idx, 0), (target_idx, 0), self.colors['gold']))
                level_styles.append(('TEXTCOLOR', (target_idx, 0), (target_idx, 0), colors.black))
            
            level_table.setStyle(TableStyle(level_styles))
            
            elements.append(Paragraph("Current vs. Target Level:", subtitle_style))
            elements.append(level_table)
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(f"Current Level: <strong>{current_level.capitalize()}</strong>", normal_style))
            elements.append(Paragraph(f"Target Level: <strong>{target_level.capitalize()}</strong>", normal_style))
            elements.append(Spacer(1, 12))
            
            elements.append(Paragraph("Gap Areas to Address:", subtitle_style))
            if gap_areas:
                gap_items = []
                for gap in gap_areas:
                    gap_items.append(ListItem(Paragraph(gap, list_item_style)))
                
                gap_list = ListFlowable(
                    gap_items,
                    bulletType='bullet',
                    start='•',
                    bulletFontName='Helvetica',
                    bulletFontSize=10
                )
                elements.append(gap_list)
            else:
                elements.append(Paragraph("No significant gaps identified.", normal_style))
                
            elements.append(Spacer(1, 24))
            
            # Next Steps with Teleios integration
            elements.append(Paragraph("Recommended Next Steps", heading_style))
            elements.append(Spacer(1, 6))
            
            # Generate appropriate next steps based on score
            next_steps = []
            if overall_score < 50:
                next_steps = [
                    "Revise your resume structure to highlight relevant skills and experience",
                    "Add missing keywords and technical skills that are valued globally",
                    "Quantify your achievements with specific metrics and outcomes",
                    "Consider joining Teleios to close specific skill gaps",
                    "Create a GitHub portfolio showcasing your technical projects",
                    "Develop a targeted career acceleration plan focusing on high-ROI skills"
                ]
            elif overall_score < 70:
                next_steps = [
                    "Enhance descriptions of your most relevant technical projects",
                    "Add the missing technical keywords identified in this analysis",
                    "Ensure achievements are quantified with metrics and outcomes",
                    "Join the Teleios community to accelerate your growth in specific gap areas",
                    "Create technical blog posts demonstrating your expertise",
                    "Consider specialized certifications in your target domain"
                ]
            else:
                next_steps = [
                    "Fine-tune your resume with the recommended keywords",
                    "Position yourself for senior roles by highlighting your most impressive projects",
                    "Consider Teleios masterminds to connect with other high-performing engineers",
                    "Build or expand your personal brand with technical writing and speaking",
                    "Target global companies with remote roles that value your expertise",
                    "Consider mentoring others to reinforce your leadership capabilities"
                ]
                
            step_items = []
            for step in next_steps:
                step_items.append(ListItem(Paragraph(step, list_item_style)))
                
            step_list = ListFlowable(
                step_items,
                bulletType='bullet',
                start='•',
                bulletFontName='Helvetica',
                bulletFontSize=10
            )
            elements.append(step_list)
            
            elements.append(Spacer(1, 20))
            
            # Add Teleios CTA box
            teleios_cta = [
                ["Accelerate Your Career with Teleios"]
            ]
            teleios_table = Table(teleios_cta, colWidths=[6.5*inch])
            teleios_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), self.colors['caput_mortuum']),
                ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
                ('ALIGNMENT', (0, 0), (0, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('PADDING', (0, 0), (0, 0), 10),
            ]))
            elements.append(teleios_table)
            
            teleios_description = [
                ["Teleios is an exclusive, invitation-only tech learning platform dedicated to producing world-class engineers from Africa. Access advanced technical curriculum, real-world projects, and 1:1 mentorship to close your skill gaps and accelerate your tech career."]
            ]
            teleios_desc_table = Table(teleios_description, colWidths=[6.5*inch])
            teleios_desc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.whitesmoke),
                ('TEXTCOLOR', (0, 0), (0, 0), self.colors['black']),
                ('ALIGNMENT', (0, 0), (0, 0), 'LEFT'),
                ('PADDING', (0, 0), (0, 0), 10),
            ]))
            elements.append(teleios_desc_table)
            
            # Website URL
            elements.append(Spacer(1, 10))
            web_url = Paragraph("Learn more at <a href='https://jointeleios.com'>jointeleios.com</a>", normal_style)
            elements.append(web_url)
            
            elements.append(Spacer(1, 30))
            
            # Footer with Ekene Chris branding
            footer_text = "Powered by Ekene Chris | Technology Architect & Technical Educator"
            elements.append(Paragraph(footer_text, footer_style))
            
            # Additional Ekene Chris info
            footer_values = "Innovation · Mentorship · Adaptability · Growth · Excellence"
            elements.append(Paragraph(footer_values, footer_style))
            
            # Copyright and contact
            footer_contact = f"© {datetime.now().year} Ekene Chris | ekenechris.com | hello@ekenechris.com"
            elements.append(Paragraph(footer_contact, footer_style))
            
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