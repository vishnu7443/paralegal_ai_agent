import os
import logging
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

logger = logging.getLogger(__name__)

def generate_mock_nda(pdf_path: str):
    """
    Generates a mock Mutual Non-Disclosure Agreement (NDA) PDF for testing.
    """
    logger.info(f"Generating mock NDA PDF at: {pdf_path}")
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'NDATitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        spaceAfter=15
    )
    
    section_style = ParagraphStyle(
        'NDASection',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        spaceAfter=8,
        spaceBefore=12
    )
    
    body_style = ParagraphStyle(
        'NDABody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=10
    )
    
    story = []
    
    # Title
    story.append(Paragraph("MUTUAL NON-DISCLOSURE AGREEMENT", title_style))
    story.append(Spacer(1, 10))
    
    # Preamble
    story.append(Paragraph(
        "This Mutual Non-Disclosure Agreement (the 'Agreement') is entered into as of June 2, 2026 (the 'Effective Date') "
        "by and between Acme Corporation, a Delaware corporation ('Acme'), and Beta Startups Inc., a California corporation ('Beta').",
        body_style
    ))
    
    # Section 1
    story.append(Paragraph("1. Definition of Confidential Information", section_style))
    story.append(Paragraph(
        "For purposes of this Agreement, 'Confidential Information' shall include all information or material that has or could have "
        "commercial value or other utility in the business in which Disclosing Party is engaged. If Information is in written form, "
        "the Disclosing Party shall label or stamp the materials with the word 'Confidential' or some similar warning.",
        body_style
    ))
    
    # Section 2
    story.append(Paragraph("2. Obligations of Receiving Party", section_style))
    story.append(Paragraph(
        "The Receiving Party shall limit disclosure of Confidential Information within its own organization to its directors, "
        "officers, employees, and consultants who have a need to know such information. The Receiving Party shall not disclose "
        "Confidential Information to any third party without the prior written consent of the Disclosing Party. Under no circumstances "
        "shall either party be liable for indirect, punitive, or consequential damages under this Agreement.",
        body_style
    ))
    
    # Section 3
    story.append(Paragraph("3. Term and Termination", section_style))
    story.append(Paragraph(
        "The non-disclosure provisions of this Agreement shall survive the termination of this Agreement and Receiving Party's "
        "duty to hold Confidential Information in confidence shall remain in effect for a period of five (5) years from the Effective Date, "
        "or until such time as Disclosing Party releases Receiving Party from such obligation in writing.",
        body_style
    ))
    story.append(Paragraph(
        "Either party may terminate this Agreement for convenience immediately upon written notice. However, all obligations regarding "
        "Confidential Information received prior to termination shall survive such termination.",
        body_style
    ))
    
    # Section 4
    story.append(Paragraph("4. Governing Law and Jurisdiction", section_style))
    story.append(Paragraph(
        "This Agreement shall be governed by, and construed in accordance with, the laws of the State of Delaware, without regard to "
        "its conflicts of law principles. Any dispute arising out of this Agreement shall be brought exclusively in the courts of Delaware.",
        body_style
    ))
    
    # Build Document
    doc.build(story)
    logger.info("Mock NDA PDF successfully built.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_mock_nda("backend/scratch/sample_nda.pdf")
