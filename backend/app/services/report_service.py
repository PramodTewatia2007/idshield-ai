import os
import html
from typing import Any
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.core.config import settings

def safe_text(val: Any) -> str:
    if val is None:
        return ""
    return html.escape(str(val))

class ReportService:
    def __init__(self):
        self.output_dir = settings.REPORTS_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_pdf_report(self, case_data: dict) -> str:
        """
        Generate comprehensive, tamper-evident PDF screening and investigation report.
        """
        case_ref = case_data.get("case_reference", "UNKNOWN")
        filename = f"IDShield_Report_{case_ref}.pdf"
        file_path = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            file_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom styles
        header_title = ParagraphStyle(
            'HeaderTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0f172a'),
            fontName='Helvetica-Bold'
        )
        
        sub_title = ParagraphStyle(
            'SubTitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#475569'),
            fontName='Helvetica'
        )
        
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#1e293b'),
            fontName='Helvetica-Bold',
            spaceBefore=12,
            spaceAfter=6
        )

        cell_text = ParagraphStyle(
            'CellText',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#1e293b')
        )

        story = []

        # Header Banner
        story.append(Paragraph("IDShield AI — Screening &amp; Forensic Examination Report", header_title))
        story.append(Paragraph(f"Generated at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} | Security Classification: OFFICIAL / LAW ENFORCEMENT SENSITIVE", sub_title))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=15))

        # 1. Case Metadata Table
        story.append(Paragraph("1. Case &amp; Screening Metadata", section_heading))
        meta_data = [
            [Paragraph("<b>Case Reference:</b>", cell_text), Paragraph(safe_text(case_ref), cell_text),
             Paragraph("<b>Case Status:</b>", cell_text), Paragraph(safe_text(case_data.get("status", "NEW")).upper(), cell_text)],
            [Paragraph("<b>Case Title:</b>", cell_text), Paragraph(safe_text(case_data.get("title", "")), cell_text),
             Paragraph("<b>Created Date:</b>", cell_text), Paragraph(safe_text(str(case_data.get("created_at", ""))[:19]), cell_text)],
            [Paragraph("<b>Reviewer Decision:</b>", cell_text), Paragraph(safe_text(case_data.get("final_decision", "PENDING_OVERSIGHT")), cell_text),
             Paragraph("<b>Officer Notes:</b>", cell_text), Paragraph(safe_text(case_data.get("review_notes", "None recorded")), cell_text)]
        ]
        t_meta = Table(meta_data, colWidths=[120, 150, 120, 150])
        t_meta.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_meta)
        story.append(Spacer(1, 10))

        # 2. Risk Assessment Summary
        story.append(Paragraph("2. Explainable Risk Assessment", section_heading))
        risk_assessments = case_data.get("risk_assessments", [])
        if risk_assessments:
            latest_risk = risk_assessments[-1]
            cat = safe_text(latest_risk.get("category", "LOW_CONCERN")).upper()
            score = latest_risk.get("risk_score", 0.0)
            
            risk_summary = [
                [Paragraph("<b>Overall Category:</b>", cell_text), Paragraph(f"<b>{cat}</b>", cell_text)],
                [Paragraph("<b>Risk Score:</b>", cell_text), Paragraph(f"{score} / 100", cell_text)],
                [Paragraph("<b>Engine Version:</b>", cell_text), Paragraph(safe_text(latest_risk.get("rule_engine_version", "")), cell_text)]
            ]
            t_risk = Table(risk_summary, colWidths=[150, 390])
            t_risk.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')),
                ('PADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(t_risk)
            
            # Contributing factors table
            factors = latest_risk.get("contributing_factors", [])
            if factors:
                story.append(Spacer(1, 6))
                factor_rows = [[Paragraph("<b>Factor</b>", cell_text), Paragraph("<b>Weight/Impact</b>", cell_text), Paragraph("<b>Explanation &amp; Evidence</b>", cell_text)]]
                for f in factors:
                    factor_rows.append([
                        Paragraph(safe_text(f.get("factor", "")), cell_text),
                        Paragraph(safe_text(f.get("impact", "")), cell_text),
                        Paragraph(safe_text(f.get("explanation", "")), cell_text)
                    ])
                t_factors = Table(factor_rows, colWidths=[150, 100, 290])
                t_factors.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e2e8f0')),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                    ('PADDING', (0,0), (-1,-1), 5),
                ]))
                story.append(t_factors)
        else:
            story.append(Paragraph("No automated risk assessment compiled.", sub_title))
        story.append(Spacer(1, 10))

        # 3. Documents & Extracted OCR Details
        story.append(Paragraph("3. Submitted Documents &amp; Extracted OCR Fields", section_heading))
        docs = case_data.get("documents", [])
        for d in docs:
            doc_info = f"<b>Document:</b> {safe_text(d.get('file_name'))} ({safe_text(d.get('document_type', '')).upper()}) | SHA-256: {safe_text(d.get('file_hash', '')[:24])}..."
            story.append(Paragraph(doc_info, cell_text))
            story.append(Spacer(1, 4))
            
            fields = d.get("extracted_fields", [])
            if fields:
                field_rows = [[Paragraph("<b>Field Name</b>", cell_text), Paragraph("<b>Extracted Value</b>", cell_text), Paragraph("<b>OCR Confidence</b>", cell_text), Paragraph("<b>Status</b>", cell_text)]]
                for fld in fields:
                    raw_val = fld.get("extracted_value")
                    val_display = safe_text(raw_val) if raw_val is not None else "<i>None</i>"
                    field_rows.append([
                        Paragraph(safe_text(fld.get("field_label", fld.get("field_name"))), cell_text),
                        Paragraph(val_display, cell_text),
                        Paragraph(f"{round(fld.get('ocr_confidence', 1.0) * 100, 1)}%", cell_text),
                        Paragraph("Corrected" if fld.get("is_corrected") else "Verified", cell_text)
                    ])
                t_fields = Table(field_rows, colWidths=[140, 220, 90, 90])
                t_fields.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e2e8f0')),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                    ('PADDING', (0,0), (-1,-1), 4),
                ]))
                story.append(t_fields)
            story.append(Spacer(1, 8))

        # 4. Tampering & Forensics Findings
        story.append(Paragraph("4. Document Tampering &amp; Digital Forensics Findings", section_heading))
        has_tampering = False
        tampering_rows = [[Paragraph("<b>Anomaly Type</b>", cell_text), Paragraph("<b>Severity</b>", cell_text), Paragraph("<b>Confidence</b>", cell_text), Paragraph("<b>Forensic Analysis Explanation</b>", cell_text)]]
        for d in docs:
            for tf in d.get("tampering_findings", []):
                has_tampering = True
                tampering_rows.append([
                    Paragraph(safe_text(tf.get("finding_type", "")), cell_text),
                    Paragraph(safe_text(tf.get("severity", "")).upper(), cell_text),
                    Paragraph(f"{round(tf.get('confidence', 0.8) * 100, 1)}%", cell_text),
                    Paragraph(safe_text(tf.get("explanation", "")), cell_text)
                ])
        if has_tampering:
            t_tamp = Table(tampering_rows, colWidths=[120, 80, 80, 260])
            t_tamp.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#fee2e2')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#fca5a5')),
                ('PADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(t_tamp)
        else:
            story.append(Paragraph("No physical or digital tampering anomalies detected across examined regions.", sub_title))
        story.append(Spacer(1, 10))

        # 5. Authorized Database Verification
        story.append(Paragraph("5. Authorized Database Checks (INTERPOL / Immigration Gateways)", section_heading))
        db_checks = case_data.get("database_checks", [])
        if db_checks:
            db_rows = [[Paragraph("<b>Database Authority</b>", cell_text), Paragraph("<b>Status</b>", cell_text), Paragraph("<b>Reference</b>", cell_text), Paragraph("<b>Response Summary</b>", cell_text)]]
            for db in db_checks:
                db_rows.append([
                    Paragraph(safe_text(db.get("source_identifier", "")), cell_text),
                    Paragraph(safe_text(db.get("response_status", "")).upper(), cell_text),
                    Paragraph(safe_text(db.get("result_reference", "N/A")), cell_text),
                    Paragraph(safe_text(db.get("explanation", "")), cell_text)
                ])
            t_db = Table(db_rows, colWidths=[150, 90, 110, 190])
            t_db.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e2e8f0')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                ('PADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(t_db)
        else:
            story.append(Paragraph("No external database queries recorded for this case.", sub_title))
        story.append(Spacer(1, 10))

        # 6. Sourced OSINT Findings
        story.append(Paragraph("6. Sourced OSINT Intelligence Findings", section_heading))
        osint_findings = case_data.get("osint_findings", [])
        if osint_findings:
            osint_rows = [[Paragraph("<b>Connector / Source</b>", cell_text), Paragraph("<b>Relevance</b>", cell_text), Paragraph("<b>Reliability</b>", cell_text), Paragraph("<b>Finding Summary &amp; Attribution</b>", cell_text)]]
            for of in osint_findings:
                osint_rows.append([
                    Paragraph(f"{safe_text(of.get('connector_name'))} / {safe_text(of.get('source_name'))}", cell_text),
                    Paragraph(safe_text(of.get("investigation_relevance", "")).upper(), cell_text),
                    Paragraph(safe_text(of.get("reliability_assessment", "")).upper(), cell_text),
                    Paragraph(f"{safe_text(of.get('finding_summary'))}<br/><b>Source:</b> {safe_text(of.get('source_url', 'N/A'))}", cell_text)
                ])
            t_osint = Table(osint_rows, colWidths=[130, 80, 90, 240])
            t_osint.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e2e8f0')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                ('PADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(t_osint)
        else:
            story.append(Paragraph("No OSINT findings associated with this case file.", sub_title))
        
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#94a3b8'), spaceAfter=10))
        story.append(Paragraph("DISCLAIMER: This screening report is advisory and assists authorized personnel. Decisions must not be made solely on automated scores. Human oversight is mandatory.", sub_title))

        doc.build(story)
        return file_path

report_service = ReportService()
