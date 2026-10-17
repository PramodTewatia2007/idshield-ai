import os
import random
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import (
    User, Case, Document, CaseStatus, RiskAssessment, AuditEvent,
    OSINTFinding, DatabaseCheck, FaceVerificationResult
)
from app.schemas.schemas import (
    CaseCreate, CaseResponse, CaseReviewRequest,
    OSINTSearchRequest, OSINTFindingResponse,
    DatabaseCheckRequest, DatabaseCheckResponse,
    FaceVerificationRequest, FaceVerificationResponse,
    DashboardMetrics, RiskAssessmentResponse
)
from app.services.osint_service import osint_manager
from app.services.database_service import db_verification_service
from app.services.face_service import face_verification_engine
from app.services.risk_service import risk_engine
from app.services.report_service import report_service
from app.services.audit_service import record_audit_event

router = APIRouter(prefix="/cases", tags=["Case Management & Screening"])

@router.post("", response_model=CaseResponse)
async def create_case(
    req: CaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case_ref = f"IDS-{random.randint(100000, 999999)}"
    new_case = Case(
        case_reference=case_ref,
        title=req.title,
        description=req.description,
        status=CaseStatus.NEW,
        assigned_officer_id=current_user.id
    )
    db.add(new_case)
    await db.commit()
    await db.refresh(new_case)

    await record_audit_event(
        db=db,
        actor_username=current_user.username,
        action="CASE_CREATED",
        resource_type="case",
        resource_id=str(new_case.id),
        outcome="SUCCESS",
        details={"case_reference": case_ref, "title": req.title},
        actor_id=current_user.id
    )

    # Return full loaded case
    return await get_case_by_id(case_id=new_case.id, current_user=current_user, db=db)

@router.get("", response_model=List[CaseResponse])
async def list_cases(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Case)
        .options(
            selectinload(Case.documents).selectinload(Document.extracted_fields),
            selectinload(Case.documents).selectinload(Document.validation_results),
            selectinload(Case.documents).selectinload(Document.tampering_findings),
            selectinload(Case.osint_findings),
            selectinload(Case.database_checks),
            selectinload(Case.face_verifications),
            selectinload(Case.risk_assessments)
        )
        .order_by(Case.created_at.desc())
    )
    if status_filter:
        query = query.where(Case.status == status_filter)
        
    res = await db.execute(query)
    return res.scalars().all()

@router.get("/{case_id}", response_model=CaseResponse)
async def get_case_by_id(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Case)
        .options(
            selectinload(Case.documents).selectinload(Document.extracted_fields),
            selectinload(Case.documents).selectinload(Document.validation_results),
            selectinload(Case.documents).selectinload(Document.tampering_findings),
            selectinload(Case.osint_findings),
            selectinload(Case.database_checks),
            selectinload(Case.face_verifications),
            selectinload(Case.risk_assessments)
        )
        .where(Case.id == case_id)
    )
    res = await db.execute(query)
    case_obj = res.scalar_one_or_none()
    if not case_obj:
        raise HTTPException(status_code=404, detail="Case not found")
    return case_obj

@router.post("/{case_id}/review", response_model=CaseResponse)
async def submit_case_review(
    case_id: int,
    req: CaseReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case_obj = await get_case_by_id(case_id=case_id, current_user=current_user, db=db)
    
    status_map = {
        "APPROVED": CaseStatus.CLOSED,
        "REJECTED": CaseStatus.CLOSED,
        "ESCALATED": CaseStatus.MANUAL_REVIEW_REQUIRED,
        "HOLD": CaseStatus.UNDER_INVESTIGATION
    }
    
    case_obj.final_decision = req.decision
    case_obj.review_notes = req.review_notes
    case_obj.status = status_map.get(req.decision.upper(), CaseStatus.CLOSED)
    
    await db.commit()
    
    await record_audit_event(
        db=db,
        actor_username=current_user.username,
        action="CASE_REVIEW_DECISION",
        resource_type="case",
        resource_id=str(case_obj.id),
        outcome="SUCCESS",
        details={"decision": req.decision, "notes": req.review_notes, "final_status": case_obj.status.value},
        actor_id=current_user.id
    )

    return case_obj

@router.post("/{case_id}/osint-search", response_model=List[OSINTFindingResponse])
async def trigger_osint_search(
    case_id: int,
    req: OSINTSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case_obj = await get_case_by_id(case_id=case_id, current_user=current_user, db=db)
    
    findings = await osint_manager.execute_search(
        target=req.query_target,
        query_type=req.query_type,
        selected_connectors=req.connectors
    )
    
    db_findings = []
    for f in findings:
        of = OSINTFinding(
            case_id=case_obj.id,
            connector_name=f["connector_name"],
            source_name=f["source_name"],
            source_url=f.get("source_url"),
            query_target=f["query_target"],
            finding_summary=f["finding_summary"],
            finding_details=f.get("finding_details"),
            investigation_relevance=f.get("investigation_relevance", "informational"),
            reliability_assessment=f.get("reliability_assessment", "moderate"),
            verification_status=f.get("verification_status", "pending_review"),
            publication_date=f.get("publication_date"),
            analyst_notes=f.get("analyst_notes")
        )
        db.add(of)
        db_findings.append(of)
    
    await db.commit()
    
    # Recalculate risk assessment with new OSINT findings
    await _recalculate_case_risk(case_id, db)

    await record_audit_event(
        db=db,
        actor_username=current_user.username,
        action="OSINT_QUERY_EXECUTED",
        resource_type="case",
        resource_id=str(case_obj.id),
        outcome="SUCCESS",
        details={"target": req.query_target, "connectors": req.connectors, "findings_count": len(findings)},
        actor_id=current_user.id
    )

    return db_findings

@router.post("/{case_id}/database-check", response_model=List[DatabaseCheckResponse])
async def trigger_database_check(
    case_id: int,
    req: DatabaseCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case_obj = await get_case_by_id(case_id=case_id, current_user=current_user, db=db)
    
    results = await db_verification_service.verify_against_databases(
        doc_number=req.document_number,
        country_code=req.issuing_country,
        services=req.services
    )
    
    db_checks = []
    for r in results:
        dc = DatabaseCheck(
            case_id=case_obj.id,
            source_identifier=r["source_identifier"],
            request_payload_summary=r["request_payload_summary"],
            response_status=r["response_status"],
            result_reference=r.get("result_reference"),
            explanation=r["explanation"],
            is_mock=r.get("is_mock", True)
        )
        db.add(dc)
        db_checks.append(dc)
        
    await db.commit()
    
    # Recalculate risk assessment
    await _recalculate_case_risk(case_id, db)

    await record_audit_event(
        db=db,
        actor_username=current_user.username,
        action="DATABASE_CHECK_EXECUTED",
        resource_type="case",
        resource_id=str(case_obj.id),
        outcome="SUCCESS",
        details={"doc_num": req.document_number, "services": req.services},
        actor_id=current_user.id
    )

    return db_checks

@router.post("/{case_id}/face-verify", response_model=FaceVerificationResponse)
async def perform_face_verification(
    case_id: int,
    req: FaceVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case_obj = await get_case_by_id(case_id=case_id, current_user=current_user, db=db)
    if not case_obj.documents:
        raise HTTPException(status_code=400, detail="Case has no uploaded documents for face extraction.")

    # Use first document image
    primary_doc = case_obj.documents[0]
    
    result = face_verification_engine.compare_faces(
        doc_image_path=primary_doc.file_path,
        probe_image_base64=req.probe_image_base64
    )
    
    fv = FaceVerificationResult(
        case_id=case_obj.id,
        verification_method="facial_biometric_comparison_authorized",
        comparison_score=result["comparison_score"],
        match_status=result["match_status"],
        image_quality_indicators=result.get("image_quality_indicators"),
        model_version=result["model_version"],
        doc_face_coords=result.get("doc_face_coords"),
        probe_face_coords=result.get("probe_face_coords"),
        review_status="verified" if result["match_status"] == "match" else "review_required",
        analyst_notes=result.get("analyst_notes")
    )
    db.add(fv)
    await db.commit()
    await db.refresh(fv)

    await _recalculate_case_risk(case_id, db)

    await record_audit_event(
        db=db,
        actor_username=current_user.username,
        action="FACE_VERIFICATION_EXECUTED",
        resource_type="case",
        resource_id=str(case_obj.id),
        outcome="SUCCESS",
        details={"match_status": result["match_status"], "score": result["comparison_score"]},
        actor_id=current_user.id
    )

    return fv

@router.get("/{case_id}/report")
async def download_case_report(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case_obj = await get_case_by_id(case_id=case_id, current_user=current_user, db=db)
    
    # Format case dictionary for report builder
    case_dict = {
        "case_reference": case_obj.case_reference,
        "title": case_obj.title,
        "status": case_obj.status.value,
        "created_at": str(case_obj.created_at),
        "review_notes": case_obj.review_notes,
        "final_decision": case_obj.final_decision,
        "risk_assessments": [
            {
                "category": r.category.value,
                "risk_score": r.risk_score,
                "rule_engine_version": r.rule_engine_version,
                "contributing_factors": r.contributing_factors
            } for r in case_obj.risk_assessments
        ],
        "documents": [
            {
                "file_name": d.file_name,
                "document_type": d.document_type.value,
                "file_hash": d.file_hash,
                "extracted_fields": [
                    {
                        "field_name": ef.field_name,
                        "field_label": ef.field_label,
                        "extracted_value": ef.extracted_value,
                        "ocr_confidence": ef.ocr_confidence,
                        "is_corrected": ef.is_corrected
                    } for ef in d.extracted_fields
                ],
                "tampering_findings": [
                    {
                        "finding_type": tf.finding_type,
                        "severity": tf.severity,
                        "confidence": tf.confidence,
                        "explanation": tf.explanation
                    } for tf in d.tampering_findings
                ]
            } for d in case_obj.documents
        ],
        "database_checks": [
            {
                "source_identifier": dc.source_identifier,
                "response_status": dc.response_status,
                "result_reference": dc.result_reference,
                "explanation": dc.explanation
            } for dc in case_obj.database_checks
        ],
        "osint_findings": [
            {
                "connector_name": of.connector_name,
                "source_name": of.source_name,
                "source_url": of.source_url,
                "investigation_relevance": of.investigation_relevance,
                "reliability_assessment": of.reliability_assessment,
                "finding_summary": of.finding_summary
            } for of in case_obj.osint_findings
        ]
    }

    report_path = report_service.generate_pdf_report(case_dict)
    
    await record_audit_event(
        db=db,
        actor_username=current_user.username,
        action="REPORT_DOWNLOADED",
        resource_type="case",
        resource_id=str(case_obj.id),
        outcome="SUCCESS",
        actor_id=current_user.id
    )

    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=f"IDShield_Report_{case_obj.case_reference}.pdf"
    )

async def _recalculate_case_risk(case_id: int, db: AsyncSession):
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
        .where(Case.id == case_id)
    )
    case_obj = case_res.scalar_one_or_none()
    if not case_obj:
        return

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
