"""
Service for generating PDF reports with proper text wrapping and optimized layout
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, Image
)
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
from typing import List, Dict
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOGO_PATH = Path(__file__).resolve().parents[2] / "static" / "img" / "image.png"


class NumberedCanvas(canvas.Canvas):
    """Custom canvas for page numbering"""
    
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6b7280"))
        page_num = f"Page {self._pageNumber} / {page_count}"
        self.drawRightString(A4[0] - 2*cm, 1.5*cm, page_num)
        self.setStrokeColor(colors.HexColor("#e5e7eb"))
        self.setLineWidth(0.5)
        self.line(2*cm, 2*cm, A4[0] - 2*cm, 2*cm)


def safe_str(value, max_length=None):
    """Safely convert to string"""
    try:
        text = str(value) if value is not None else "N/A"
        if max_length and len(text) > max_length:
            return text[:max_length - 3] + "..."
        return text
    except Exception:
        return "N/A"


def format_date(date_str, format_output="%d/%m/%Y"):
    """Format date with fallback"""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime(format_output)
    except Exception:
        return safe_str(date_str)


def append_logo(elements, width_cm=3.0, height_cm=3.0):
    """Add visible boxed logo if available."""
    if not LOGO_PATH.exists():
        return
    try:
        logo = Image(str(LOGO_PATH), width=width_cm * cm, height=height_cm * cm)
        logo_table = Table([[logo]], colWidths=[width_cm * cm + 0.8 * cm])
        logo_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BORDER", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        logo_table.hAlign = "CENTER"
        elements.append(logo_table)
        elements.append(Spacer(1, 0.28 * cm))
    except Exception as e:
        logger.warning(f"Failed to load logo: {e}")


def generate_assignment_report(assignments: List[Dict]) -> BytesIO:
    """
    Generate PDF report with proper text wrapping using Paragraph
    """
    try:
        if not assignments:
            raise ValueError("No assignments to generate report")
        
        logger.info(f"Generating report for {len(assignments)} assignments")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            rightMargin=1.5*cm, 
            leftMargin=1.5*cm, 
            topMargin=2*cm, 
            bottomMargin=2.5*cm,
            title="Rapport d'Attribution des Projets GL3E",
            author="Institut Africain d'Informatique"
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Styles optimisés
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor("#1e3a8a"),
            alignment=TA_CENTER,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor("#374151"),
            alignment=TA_CENTER,
            spaceAfter=4,
            fontName='Helvetica'
        )
        
        info_style = ParagraphStyle(
            'Info',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor("#6b7280"),
            alignment=TA_CENTER,
            spaceAfter=15
        )
        
        # Style pour texte dans cellules avec word wrapping
        cell_style = ParagraphStyle(
            'CellText',
            parent=styles['Normal'],
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#111827"),
            fontName='Helvetica',
            alignment=TA_LEFT
        )
        
        cell_center_style = ParagraphStyle(
            'CellCenter',
            parent=cell_style,
            alignment=TA_CENTER
        )
        
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=colors.whitesmoke,
            alignment=TA_CENTER,
            leading=12
        )
        
        # Header
        append_logo(elements, width_cm=3.2, height_cm=3.2)
        elements.append(Paragraph("Institut Africain d'Informatique", title_style))
        elements.append(Paragraph("Yaoundé - Cameroun", subtitle_style))
        elements.append(Spacer(1, 0.2*cm))
        
        elements.append(Paragraph("Rapport d'Attribution des Projets", title_style))
        elements.append(Paragraph("Promotion GL3E", subtitle_style))
        
        date_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
        elements.append(Paragraph(f"Document généré le {date_str}", info_style))
        
        # Summary
        summary_text = f"<b>Total:</b> {len(assignments)} projet(s) attribué(s)"
        summary_para = Paragraph(summary_text, info_style)
        summary_table = Table([[summary_para]], colWidths=[A4[0] - 3*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
            ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor("#3b82f6")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.4*cm))
        
        # Table avec Paragraphs pour word wrapping automatique
        data = [[
            Paragraph("<b>N°</b>", header_style),
            Paragraph("<b>Étudiant</b>", header_style),
            Paragraph("<b>Projet Attribué</b>", header_style),
            Paragraph("<b>Note</b>", header_style),
            Paragraph("<b>Date</b>", header_style)
        ]]
        
        # Data rows - Paragraphs empêchent le débordement
        for idx, a in enumerate(assignments, 1):
            student_name = safe_str(a.get("student_name", "N/A"))
            project = safe_str(a.get("project_title", "N/A"))
            assigned_date = format_date(a.get("assigned_at", ""), "%d/%m/%Y")
            
            data.append([
                Paragraph(f"<b>{idx}</b>", cell_center_style),
                Paragraph(student_name, cell_style),
                Paragraph(project, cell_style),
                Paragraph("", cell_center_style),  # Note vide
                Paragraph(assigned_date, cell_center_style)
            ])
        
        # Largeurs optimisées (Total: 18cm)
        # N°=1cm, Étudiant=5.5cm, Projet=7cm, Note=2cm, Date=2.5cm
        col_widths = [1*cm, 5.5*cm, 7*cm, 2*cm, 2.5*cm]
        
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        style = TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor("#1e3a8a")),
            
            # Data rows styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Alternating colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ])
        
        table.setStyle(style)
        elements.append(table)
        
        # Footer
        elements.append(Spacer(1, 0.6*cm))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor("#6b7280"),
            alignment=TA_CENTER,
            leading=11
        )
        footer_text = """
        Ce document est généré automatiquement par le système d'attribution des projets.<br/>
        Pour toute question, contactez Stephane Zoa à contact@stephanezoa.online .
        """
        elements.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        doc.build(elements, canvasmaker=NumberedCanvas)
        buffer.seek(0)
        
        logger.info("Report generated successfully")
        return buffer
        
    except Exception as e:
        logger.error(f"Error generating assignment report: {e}")
        raise


def generate_student_theme_pdf(
    student_name: str,
    student_matricule: str,
    project_title: str,
    project_description: str,
    assigned_at: str,
    signature_name: str = "Stéphane Zoa ",
    signature_title: str = "Aspirant ingénieur en Informatique , stephanezoa.online copyright ©️ 2026"
) -> BytesIO:
    """
    Generate professional student certificate with proper text wrapping
    """
    try:
        if not all([student_name, student_matricule, project_title]):
            raise ValueError("Missing required fields")
        
        logger.info(f"Generating certificate for {student_name}")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2.5*cm,
            leftMargin=2.5*cm,
            topMargin=2.5*cm,
            bottomMargin=3*cm,
            title=f"Attribution - {student_name}",
            author="Institut Africain d'Informatique"
        )

        styles = getSampleStyleSheet()
        elements = []

        # Styles
        title_style = ParagraphStyle(
            "CertTitle",
            parent=styles["Heading1"],
            fontSize=20,
            textColor=colors.HexColor("#1e3a8a"),
            alignment=TA_CENTER,
            spaceAfter=6,
            fontName='Helvetica-Bold',
            leading=24
        )
        
        subtitle_style = ParagraphStyle(
            "CertSubtitle",
            parent=styles["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#374151"),
            alignment=TA_CENTER,
            spaceAfter=18,
            fontName='Helvetica'
        )
        
        section_style = ParagraphStyle(
            "Section",
            parent=styles["Heading3"],
            fontSize=12,
            textColor=colors.HexColor("#1e3a8a"),
            spaceAfter=8,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#111827"),
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        )
        
        highlight_style = ParagraphStyle(
            "Highlight",
            parent=body_style,
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor("#1e3a8a"),
            alignment=TA_LEFT
        )

        # Header
        append_logo(elements, width_cm=2, height_cm=2)
        elements.append(Paragraph("Institut Africain d'Informatique", title_style))
        elements.append(Paragraph("Yaoundé - Cameroun", subtitle_style))
        elements.append(Spacer(1, 0.2*cm))
        
        # Title box
        cert_title = Paragraph("ATTESTATION D'ATTRIBUTION DE THÈME", title_style)
        cert_subtitle = Paragraph("Licence 3 - Génie Logiciel", subtitle_style)
        
        title_data = [[cert_title], [cert_subtitle]]
        title_table = Table(title_data, colWidths=[A4[0] - 5*cm])
        title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
            ('BORDER', (0, 0), (-1, -1), 2, colors.HexColor("#1e3a8a")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(title_table)
        elements.append(Spacer(1, 0.4*cm))

        # Date formatting
        try:
            dt = datetime.fromisoformat(assigned_at.replace('Z', '+00:00'))
            date_label = dt.strftime("%d/%m/%Y à %H:%M")
        except Exception:
            date_label = safe_str(assigned_at)

        # Student info with Paragraph for wrapping
        student_data = [
            ["Étudiant(e)", Paragraph(safe_str(student_name), body_style)],
            ["Matricule", Paragraph(safe_str(student_matricule), body_style)],
            ["Date d'attribution", Paragraph(date_label, body_style)],
            ["Date d'édition", Paragraph(datetime.now().strftime("%d/%m/%Y"), body_style)],
            ["Année académique", Paragraph(datetime.now().strftime("%Y"), body_style)],
        ]
        
        student_table = Table(student_data, colWidths=[4*cm, A4[0] - 9*cm])
        student_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(student_table)
        elements.append(Spacer(1, 0.5*cm))

        # Project with wrapping
        elements.append(Paragraph("Thème attribué", section_style))
        
        project_para = Paragraph(f"<b>{safe_str(project_title)}</b>", highlight_style)
        project_box = Table([[project_para]], colWidths=[A4[0] - 5*cm])
        project_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#dbeafe")),
            ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor("#3b82f6")),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(project_box)
        elements.append(Spacer(1, 0.3*cm))

        # Description with wrapping
        elements.append(Paragraph("Description du projet", section_style))
        
        desc_para = Paragraph(safe_str(project_description or "Aucune description fournie."), body_style)
        desc_box = Table([[desc_para]], colWidths=[A4[0] - 5*cm])
        desc_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f9fafb")),
            ('BORDER', (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(desc_box)
        elements.append(Spacer(1, 0.8*cm))

        # Note
        note_style = ParagraphStyle(
            'Note',
            parent=body_style,
            fontSize=9,
            textColor=colors.HexColor("#dc2626"),
            leading=12
        )
        note_text = """
        <b>Note importante:</b> Ce thème vous est attribué de manière définitive. 
        Toute modification devra faire l'objet d'une demande écrite.
        """
        note_para = Paragraph(note_text, note_style)
        note_box = Table([[note_para]], colWidths=[A4[0] - 5*cm])
        note_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fef2f2")),
            ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor("#dc2626")),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(note_box)
        elements.append(Spacer(1, 1*cm))

        # Signature
        sig_style = ParagraphStyle(
            'Sig',
            parent=body_style,
            fontSize=10,
            alignment=TA_CENTER
        )
        
        sig_name_style = ParagraphStyle(
            'SigName',
            parent=sig_style,
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=colors.HexColor("#1e3a8a")
        )
        
        current_date = datetime.now().strftime("Fait à Yaoundé, le %d/%m/%Y")
        
        sig_data = [
            [Paragraph(current_date, sig_style)],
            [Spacer(1, 0.3*cm)],
            [Paragraph(safe_str(signature_name), sig_name_style)],
            [Paragraph(safe_str(signature_title), sig_style)],
        ]
        
        sig_table = Table(sig_data, colWidths=[A4[0] - 5*cm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(sig_table)

        doc.build(elements)
        buffer.seek(0)
        
        logger.info(f"Certificate generated for {student_name}")
        return buffer
        
    except Exception as e:
        logger.error(f"Error generating certificate: {e}")
        raise


__all__ = ['generate_assignment_report', 'generate_student_theme_pdf']
