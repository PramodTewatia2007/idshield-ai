import os
import shutil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine, Base
from app.core.config import settings
from app.core.auth import get_password_hash
from app.models.models import User, UserRole, Case, Document, CaseStatus, DocumentType
from app.services.ocr_service import ocr_service
from app.services.validation_service import validation_engine
from app.services.forensics_service import forensics_engine
from app.services.risk_service import risk_engine
from app.models.models import ExtractedField, ValidationResult, TamperingFinding, RiskAssessment, AuditEvent, DatabaseCheck, OSINTFinding
import numpy as np
import cv2

def create_synthetic_passport_image(output_path: str, name: str, doc_no: str, is_altered: bool = False):
    """Generate high-resolution realistic synthetic passport graphic with security guilloche and MRZ."""
    img = np.zeros((480, 720, 3), dtype=np.uint8)
    img[:] = (244, 246, 248)  # Off-white / light parchment
    
    # Decorative header
    cv2.rectangle(img, (0, 0), (720, 50), (22, 38, 70), -1)  # Navy blue banner
    cv2.putText(img, "GLOBAL CONFEDERATION - PASSPORT", (160, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Watermark / guilloche background lines
    for i in range(60, 420, 20):
        cv2.line(img, (20, i), (700, i), (225, 230, 238), 1)

    # Portrait area (left side)
    cv2.rectangle(img, (40, 70), (220, 290), (200, 210, 220), -1)
    # Head silhouette
    cv2.circle(img, (130, 150), 45, (120, 140, 160), -1)
    cv2.ellipse(img, (130, 260), (70, 60), 0, 180, 360, (100, 120, 140), -1)
    cv2.putText(img, "OFFICIAL PORTRAIT", (55, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (240, 240, 240), 1)

    # Alteration seam artifact if requested
    if is_altered:
        cv2.rectangle(img, (38, 68), (222, 292), (180, 100, 100), 2)  # Spliced photo seam

    # Details text
    cv2.putText(img, f"NAME: {name}", (250, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 20, 20), 2)
    cv2.putText(img, f"PASSPORT NO: {doc_no}", (250, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 20, 20), 2)
    cv2.putText(img, "NATIONALITY: UTOPIAN", (250, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (40, 40, 40), 1)
    cv2.putText(img, "DATE OF BIRTH: 14 APR 1988", (250, 215), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (40, 40, 40), 1)
    cv2.putText(img, "DATE OF ISSUE: 10 MAY 2020", (250, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (40, 40, 40), 1)
    cv2.putText(img, "DATE OF EXPIRY: 09 MAY 2030", (250, 285), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (40, 40, 40), 1)

    # Stamp
    cv2.circle(img, (580, 200), 55, (180, 40, 40) if not is_altered else (100, 40, 180), 2)
    cv2.putText(img, "BORDER", (545, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 40, 40), 1)
    cv2.putText(img, "ENTRY VERIFIED", (530, 215), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (180, 40, 40), 1)

    # MRZ Zone (bottom)
    cv2.rectangle(img, (0, 390), (720, 480), (255, 255, 255), -1)
    cv2.line(img, (0, 390), (720, 390), (180, 180, 180), 1)
    clean_name = name.replace(" ", "<")
    mrz1 = f"P<UTO{clean_name}<<<<<<<<<<<<<<<<<<<<<<<<<<<"[:44]
    mrz2 = f"{doc_no}7UTO8804148M3005098<<<<<<<<<<<<<<02"[:44]
    cv2.putText(img, mrz1, (30, 425), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.75, (10, 10, 10), 1)
    cv2.putText(img, mrz2, (30, 455), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.75, (10, 10, 10), 1)

    cv2.imwrite(output_path, img)

async def init_db_and_seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as session:
        # Check if users already seeded
        res = await session.execute(select(User))
        existing_users = res.scalars().all()
        if existing_users:
            return  # Already seeded
            
        print("[SEED] Creating initial demonstration users & roles...")
        users = [
            User(
                username="admin",
                email="admin@idshield.gov",
                full_name="System Administrator",
                role=UserRole.ADMIN,
                hashed_password=get_password_hash("Admin@123456"),
                is_active=True
            ),
            User(
                username="officer",
                email="officer@border.gov",
                full_name="Officer Jane Doe",
                role=UserRole.OFFICER,
                hashed_password=get_password_hash("Officer@123456"),
                is_active=True
            ),
            User(
                username="investigator",
                email="investigator@idshield.gov",
                full_name="Senior Analyst Marcus Croft",
                role=UserRole.INVESTIGATOR,
                hashed_password=get_password_hash("Investigator@123"),
                is_active=True
            ),
            User(
                username="supervisor",
                email="supervisor@border.gov",
                full_name="Supervisor David Vance",
                role=UserRole.SUPERVISOR,
                hashed_password=get_password_hash("Supervisor@123"),
                is_active=True
            )
        ]
        session.add_all(users)
        await session.commit()

        # Seed sample documents and cases
        os.makedirs(settings.DOCUMENTS_DIR, exist_ok=True)
        sample1_path = os.path.join(settings.DOCUMENTS_DIR, "passport_alexander_morgan.jpg")
        sample2_path = os.path.join(settings.DOCUMENTS_DIR, "passport_altered_tampered.jpg")
        
        create_synthetic_passport_image(sample1_path, "ALEXANDER MORGAN", "P84920194", is_altered=False)
        create_synthetic_passport_image(sample2_path, "VIKTOR KASLOV", "P9948201", is_altered=True)

        print("[SEED] Creating demonstration screening cases...")
        # Case 1: Standard Verification
        case1 = Case(
            case_reference="IDS-104921",
            title="Standard Primary Screening - Alexander Morgan",
            description="Border transit terminal B-12 passport verification.",
            status=CaseStatus.NEW,
            assigned_officer_id=2
        )
        session.add(case1)
        await session.commit()
        await session.refresh(case1)

        doc1 = Document(
            case_id=case1.id,
            document_type=DocumentType.PASSPORT,
            file_name="passport_alexander_morgan.jpg",
            file_path=sample1_path,
            file_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            file_size=os.path.getsize(sample1_path),
            mime_type="image/jpeg",
            processing_status="completed"
        )
        session.add(doc1)
        await session.commit()
        await session.refresh(doc1)

        # Fields for Doc 1
        fields1 = [
            ExtractedField(document_id=doc1.id, field_name="full_name", field_label="Full Name", extracted_value="ALEXANDER VICTOR MORGAN", ocr_confidence=0.98),
            ExtractedField(document_id=doc1.id, field_name="passport_number", field_label="Passport Number", extracted_value="P84920194", ocr_confidence=0.99),
            ExtractedField(document_id=doc1.id, field_name="nationality", field_label="Nationality", extracted_value="UTOPIAN", ocr_confidence=0.97),
            ExtractedField(document_id=doc1.id, field_name="date_of_birth", field_label="Date of Birth", extracted_value="1988-04-14", ocr_confidence=0.96),
            ExtractedField(document_id=doc1.id, field_name="date_of_issue", field_label="Date of Issue", extracted_value="2020-05-10", ocr_confidence=0.95),
            ExtractedField(document_id=doc1.id, field_name="expiry_date", field_label="Date of Expiry", extracted_value="2030-05-09", ocr_confidence=0.96),
        ]
        session.add_all(fields1)

        # Validation results for Doc 1
        vals1 = [
            ValidationResult(document_id=doc1.id, rule_identifier="VAL_REQ_FIELDS", rule_name="Mandatory Field Completeness", status="passed", explanation="All mandatory passport fields extracted successfully."),
            ValidationResult(document_id=doc1.id, rule_identifier="VAL_EXPIRY_CHECK", rule_name="Document Validity & Expiry", status="passed", explanation="Passport valid until 2030-05-09 (1300+ days remaining)."),
            ValidationResult(document_id=doc1.id, rule_identifier="VAL_MRZ_VISUAL_MATCH", rule_name="Visual Zone vs MRZ Consistency", status="passed", explanation="MRZ document numbers and check digits conform to ICAO Doc 9303.")
        ]
        session.add_all(vals1)

        # OSINT for Case 1
        osint1 = OSINTFinding(
            case_id=case1.id,
            connector_name="SpiderFoot",
            source_name="Global Directory Public Registry",
            source_url="https://registry.spiderfoot.net/targets/ALEXANDER_MORGAN",
            query_target="ALEXANDER VICTOR MORGAN",
            finding_summary="Target has standard commercial registrations with no adverse sanctions or red notices.",
            investigation_relevance="informational",
            reliability_assessment="moderate",
            verification_status="verified"
        )
        session.add(osint1)

        # Risk assessment for Case 1
        ra1 = RiskAssessment(
            case_id=case1.id,
            category="low_concern",
            risk_score=4.0,
            contributing_factors=[
                {"factor": "Baseline Integrity Satisfied", "impact": "0 (Clean)", "category": "baseline_integrity", "explanation": "Document passes all ICAO validity and security rule checks."}
            ],
            rule_engine_version="v1.4.0-explainable"
        )
        session.add(ra1)

        # Case 2: Altered / Suspicious Case
        case2 = Case(
            case_reference="IDS-882914",
            title="Expedited Secondary Review - Suspected Tampered Travel Doc",
            description="Passenger flagged at checkpoint due to irregular font alignment on bio page.",
            status=CaseStatus.MANUAL_REVIEW_REQUIRED,
            assigned_officer_id=2
        )
        session.add(case2)
        await session.commit()
        await session.refresh(case2)

        doc2 = Document(
            case_id=case2.id,
            document_type=DocumentType.PASSPORT,
            file_name="passport_altered_tampered.jpg",
            file_path=sample2_path,
            file_hash="9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            file_size=os.path.getsize(sample2_path),
            mime_type="image/jpeg",
            processing_status="completed"
        )
        session.add(doc2)
        await session.commit()
        await session.refresh(doc2)

        # Tampering findings for Doc 2
        tamp2 = [
            TamperingFinding(
                document_id=doc2.id,
                finding_type="photo_manipulation_seam",
                severity="critical",
                region_coordinates=[38, 68, 184, 224],
                confidence=0.89,
                explanation="Detected sharp rectangular boundary seam surrounding portrait region. High likelihood of photograph replacement.",
                model_version="IDShield-Forensics-v2.1-hybrid",
                recommended_checks="Examine document edge under UV light for adhesive or laminate disruption."
            ),
            TamperingFinding(
                document_id=doc2.id,
                finding_type="text_manipulation_font",
                severity="high",
                region_coordinates=[250, 100, 200, 30],
                confidence=0.91,
                explanation="Font kerning and baseline irregularities detected in holder name field.",
                model_version="IDShield-Forensics-v2.1-hybrid",
                recommended_checks="Compare typography against issuing state master specimen."
            )
        ]
        session.add_all(tamp2)

        # Database Check for Doc 2 (Stolen Hit)
        db_check2 = DatabaseCheck(
            case_id=case2.id,
            source_identifier="INTERPOL_SLTD_GLOBAL_DATABASE",
            request_payload_summary="Query: DocNum=P9948201",
            response_status="revoked_stolen",
            result_reference="SLTD-ALERT-99214-INTERPOL",
            explanation="Document P9948201 is actively flagged in the INTERPOL Stolen and Lost Travel Documents register.",
            is_mock=True
        )
        session.add(db_check2)

        # Risk Assessment for Case 2
        ra2 = RiskAssessment(
            case_id=case2.id,
            category="elevated_concern",
            risk_score=78.5,
            contributing_factors=[
                {"factor": "Stolen / Lost Document Hit", "impact": "+45 (Critical)", "category": "database_verification", "explanation": "Document flagged in INTERPOL SLTD database."},
                {"factor": "Photograph Replacement Seam", "impact": "+22.3 (Critical)", "category": "tampering_forensics", "explanation": "Spliced border boundary detected in portrait zone."},
                {"factor": "Typography Anomaly", "impact": "+16.4 (High)", "category": "tampering_forensics", "explanation": "Font kerning discrepancy in biographical zone."}
            ],
            rule_engine_version="v1.4.0-explainable"
        )
        session.add(ra2)

        # Seed initial audit log
        audit1 = AuditEvent(
            actor_username="system",
            action="DATABASE_INITIALIZED",
            resource_type="system",
            resource_id="root",
            outcome="SUCCESS",
            details={"version": "1.0.0", "seeded_cases": 2}
        )
        session.add(audit1)

        await session.commit()
        print("[SEED] IDShield AI database initialized and seeded successfully.")
