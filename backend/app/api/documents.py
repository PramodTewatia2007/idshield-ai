import os
import hashlib
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.core.config import settings
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User, Case, Document, ExtractedField, ValidationResult, TamperingFinding, DocumentType
from app.schemas.schemas import DocumentResponse, ExtractedFieldResponse, FieldCorrectionRequest
from app.services.ocr_service import ocr_service
from app.services.validation_service import validation_engine
from app.services.forensics_service import forensics_engine
from app.services.risk_service import risk_engine
from app.services.audit_service import record_audit_event
from app.models.models import RiskAssessment

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    case_id: int = Form(...),
    doc_type_hint: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify case exists
    res = await db.execute(select(Case).where(Case.id == case_id))
    case = res.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Associated Case not found")

    # Read and hash file for evidence integrity
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds maximum 20MB limit")

    file_hash = hashlib.sha256(content).hexdigest()
    
    # Save file to protected storage
    safe_name = f"{file_hash[:12]}_{file.filename}"
    file_path = os.path.join(settings.DOCUMENTS_DIR, safe_name)
    with open(file_path, "wb") as f:
        f.write(content)

    # Determine document type enum
    dtype = DocumentType.UNKNOWN
    if doc_type_hint:
        try:
            dtype = DocumentType(doc_type_hint.lower())
        except Exception:
            pass

    doc = Document(
        case_id=case.id,
        document_type=dtype,
        file_name=file.filename,
        file_path=file_path,
        file_hash=file_hash,
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        processing_status="pending"
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    await record_audit_event(
        db=db,
        actor_username=current_user.username,
        action="DOCUMENT_UPLOAD",
        resource_type="document",
        resource_id=str(doc.id),
        outcome="SUCCESS",
        details={"file_name": file.filename, "file_hash": file_hash, "case_id": case.id},
        actor_id=current_user.id
    )

    # Automatically trigger OCR, validation and tampering analysis
    await analyze_document(doc_id=doc.id, current_user=current_user, db=db)

    # Re-fetch document with relations
    res_doc = await db.execute(
        select(Document)
        .options(
            selectinload(Document.extracted_fields),
            selectinload(Document.validation_results),
            selectinload(Document.tampering_findings)
        )
        .where(Document.id == doc.id)
    )
    return res_doc.scalar_one()

@router.post("/{doc_id}/analyze", response_model=DocumentResponse)
async def analyze_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Document).where(Document.id == doc_id))
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 1. Run OCR
    ocr_res = ocr_service.process_document(doc.file_path, doc.file_name)
    if doc.document_type == DocumentType.UNKNOWN:
        try:
            doc.document_type = DocumentType(ocr_res.get("document_type", "unknown"))
        except Exception:
            pass

    # Save extracted fields
    # Delete old fields, validations, and tampering findings if re-analyzing
    await db.execute(delete(ExtractedField).where(ExtractedField.document_id == doc.id))
    await db.execute(delete(ValidationResult).where(ValidationResult.document_id == doc.id))
    await db.execute(delete(TamperingFinding).where(TamperingFinding.document_id == doc.id))
    
    extracted_objs = []
    fields_list = ocr_res.get("fields", [])
    for f in fields_list:
        ef = ExtractedField(
            document_id=doc.id,
            field_name=f["field_name"],
            field_label=f["field_label"],
            extracted_value=f.get("extracted_value"),
            ocr_confidence=f.get("ocr_confidence", 1.0),
            bounding_box=f.get("bounding_box")
        )
        db.add(ef)
        extracted_objs.append(ef)

    # 2. Run Validation Engine
    val_checks = validation_engine.validate_document(fields_list, doc.document_type.value)
    for v in val_checks:
        vr = ValidationResult(
            document_id=doc.id,
            rule_identifier=v["rule_identifier"],
            rule_name=v["rule_name"],
            status=v["status"],
            explanation=v["explanation"],
            source_reference=v.get("source_reference"),
            evidence_data=v.get("evidence_data")
        )
        db.add(vr)

    # 3. Run Tampering & Forensics Engine
    tamper_results = forensics_engine.analyze_document_tampering(doc.file_path, doc.file_name)
    for tf in tamper_results:
        t_obj = TamperingFinding(
            document_id=doc.id,
            finding_type=tf["finding_type"],
            severity=tf.get("severity", "medium"),
            region_coordinates=tf.get("region_coordinates"),
            confidence=tf.get("confidence", 0.8),
            explanation=tf.get("explanation"),
            model_version=tf.get("model_version"),
            recommended_checks=tf.get("recommended_checks")
        )
        db.add(t_obj)

    doc.processing_status = "completed"
    await db.commit()

    # 4. Trigger explainable risk assessment update for the case
    case_res = await db.execute(
        select(Case)
        .options(
            selectinload(Case.documents).selectinload(Document.extracted_fields),
            selectinload(Case.documents).selectinload(Document.validation_results),
            selectinload(Case.documents).selectinload(Document.tampering_findings),
            selectinload(Case.face_verifications),
            selectinload(Case.database_checks),
            selectinload(Case.osint_findings)
        )
        .where(Case.id == doc.case_id)
    )
    case_obj = case_res.scalar_one_or_none()
    if case_obj:
        all_fields = []
        all_vals = []
        all_tamp = []
        for d in case_obj.documents:
            all_fields.extend([{"field_name": ef.field_name, "extracted_value": ef.extracted_value} for ef in d.extracted_fields])
            all_vals.extend([{"rule_name": v.rule_name, "rule_identifier": v.rule_identifier, "status": v.status, "explanation": v.explanation} for v in d.validation_results])
            all_tamp.extend([{"finding_type": t.finding_type, "severity": t.severity, "confidence": t.confidence, "explanation": t.explanation, "model_version": t.model_version} for t in d.tampering_findings])

        assessment = risk_engine.compute_assessment(
            extracted_fields=all_fields,
            validation_results=all_vals,
            tampering_findings=all_tamp,
            face_verifications=[{"match_status": f.match_status, "comparison_score": f.comparison_score, "model_version": f.model_version} for f in case_obj.face_verifications],
            database_checks=[{"response_status": dc.response_status, "source_identifier": dc.source_identifier, "result_reference": dc.result_reference} for dc in case_obj.database_checks],
            osint_findings=[{"investigation_relevance": o.investigation_relevance, "finding_summary": o.finding_summary, "connector_name": o.connector_name, "source_name": o.source_name} for o in case_obj.osint_findings]
        )

        new_ra = RiskAssessment(
            case_id=case_obj.id,
            category=assessment["category"],
            risk_score=assessment["risk_score"],
            contributing_factors=assessment["contributing_factors"],
            rule_engine_version=assessment["rule_engine_version"]
        )
        db.add(new_ra)
        await db.commit()

    await record_audit_event(
        db=db,
        actor_username=current_user.username,
        action="DOCUMENT_ANALYSIS_COMPLETED",
        resource_type="document",
        resource_id=str(doc.id),
        outcome="SUCCESS",
        details={"fields_count": len(fields_list), "val_checks": len(val_checks), "tamper_findings": len(tamper_results)},
        actor_id=current_user.id
    )

    # Return refreshed doc
    res_final = await db.execute(
        select(Document)
        .options(
            selectinload(Document.extracted_fields),
            selectinload(Document.validation_results),
            selectinload(Document.tampering_findings)
        )
        .where(Document.id == doc.id)
    )
    return res_final.scalar_one()

@router.put("/fields/{field_id}/correct", response_model=ExtractedFieldResponse)
async def correct_field_value(
    field_id: int,
    req: FieldCorrectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(ExtractedField).where(ExtractedField.id == field_id))
    ef = res.scalar_one_or_none()
    if not ef:
        raise HTTPException(status_code=404, detail="Field not found")

    original = ef.extracted_value
    ef.original_value = original if ef.original_value is None else ef.original_value
    ef.extracted_value = req.corrected_value
    ef.is_corrected = True
    ef.review_status = "verified"
    await db.commit()
    await db.refresh(ef)

    await record_audit_event(
        db=db,
        actor_username=current_user.username,
        action="FIELD_CORRECTION",
        resource_type="extracted_field",
        resource_id=str(ef.id),
        outcome="SUCCESS",
        details={"field_name": ef.field_name, "old_val": original, "new_val": req.corrected_value},
        actor_id=current_user.id
    )

    return ef
