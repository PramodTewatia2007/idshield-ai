import os
from datetime import datetime, timezone
import enum
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean, 
    ForeignKey, Enum, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OFFICER = "officer"
    INVESTIGATOR = "investigator"
    SUPERVISOR = "supervisor"
    AUDITOR = "auditor"

class CaseStatus(str, enum.Enum):
    NEW = "new"
    PROCESSING = "processing"
    AWAITING_VERIFICATION = "awaiting_verification"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    UNDER_INVESTIGATION = "under_investigation"
    CLOSED = "closed"

class DocumentType(str, enum.Enum):
    PASSPORT = "passport"
    VISA = "visa"
    NATIONAL_ID = "national_id"
    DRIVING_LICENSE = "driving_license"
    RESIDENCE_PERMIT = "residence_permit"
    UNKNOWN = "unknown"

class ValidationStatus(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"
    UNABLE_TO_VERIFY = "unable_to_verify"
    SOURCE_UNAVAILABLE = "source_unavailable"

class RiskCategory(str, enum.Enum):
    LOW_CONCERN = "low_concern"
    REVIEW_RECOMMENDED = "review_recommended"
    ELEVATED_CONCERN = "elevated_concern"
    VERIFICATION_UNAVAILABLE = "verification_unavailable"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    full_name = Column(String(128), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.OFFICER, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    cases = relationship("Case", back_populates="assigned_officer_rel")
    audit_events = relationship("AuditEvent", back_populates="actor_rel")

class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    case_reference = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(CaseStatus), default=CaseStatus.NEW, index=True)
    assigned_officer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    review_notes = Column(Text, nullable=True)
    final_decision = Column(String(64), nullable=True)
    
    assigned_officer_rel = relationship("User", back_populates="cases")
    documents = relationship("Document", back_populates="case_rel", cascade="all, delete-orphan")
    osint_findings = relationship("OSINTFinding", back_populates="case_rel", cascade="all, delete-orphan")
    database_checks = relationship("DatabaseCheck", back_populates="case_rel", cascade="all, delete-orphan")
    face_verifications = relationship("FaceVerificationResult", back_populates="case_rel", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="case_rel", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    document_type = Column(Enum(DocumentType), default=DocumentType.UNKNOWN)
    file_name = Column(String(256), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_hash = Column(String(128), nullable=False)  # SHA-256 for evidence integrity
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(64), nullable=False)
    processing_status = Column(String(32), default="pending")  # pending, completed, failed
    upload_timestamp = Column(DateTime(timezone=True), default=utc_now)
    
    case_rel = relationship("Case", back_populates="documents")
    extracted_fields = relationship("ExtractedField", back_populates="document_rel", cascade="all, delete-orphan")
    validation_results = relationship("ValidationResult", back_populates="document_rel", cascade="all, delete-orphan")
    tampering_findings = relationship("TamperingFinding", back_populates="document_rel", cascade="all, delete-orphan")

    @property
    def file_url(self) -> str:
        safe_name = os.path.basename(self.file_path).replace("\\", "/")
        return f"/storage/documents/{safe_name}"

class ExtractedField(Base):
    __tablename__ = "extracted_fields"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    field_name = Column(String(64), nullable=False)  # e.g. full_name, passport_number, dob, mrz
    field_label = Column(String(128), nullable=False)
    extracted_value = Column(Text, nullable=True)
    ocr_confidence = Column(Float, default=1.0)  # 0.0 to 1.0
    is_corrected = Column(Boolean, default=False)
    original_value = Column(Text, nullable=True)
    review_status = Column(String(32), default="pending")  # pending, verified, rejected
    bounding_box = Column(JSON, nullable=True)  # [x, y, w, h]
    
    document_rel = relationship("Document", back_populates="extracted_fields")

class ValidationResult(Base):
    __tablename__ = "validation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    rule_identifier = Column(String(64), nullable=False)
    rule_name = Column(String(128), nullable=False)
    status = Column(Enum(ValidationStatus), nullable=False)
    explanation = Column(Text, nullable=False)
    source_reference = Column(String(256), nullable=True)
    evidence_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now)
    
    document_rel = relationship("Document", back_populates="validation_results")

class TamperingFinding(Base):
    __tablename__ = "tampering_findings"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    finding_type = Column(String(64), nullable=False)  # photo_manipulation, font_inconsistency, stamp_anomaly, metadata_alert, ela_artifact
    severity = Column(String(32), default="medium")  # low, medium, high, critical
    region_coordinates = Column(JSON, nullable=True)  # [x, y, w, h] or polygon
    confidence = Column(Float, nullable=False)
    explanation = Column(Text, nullable=False)
    model_version = Column(String(64), nullable=False)
    visual_evidence_url = Column(String(512), nullable=True)
    recommended_checks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    document_rel = relationship("Document", back_populates="tampering_findings")

class FaceVerificationResult(Base):
    __tablename__ = "face_verification_results"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    verification_method = Column(String(64), default="facial_biometric_comparison_authorized")
    comparison_score = Column(Float, nullable=False)  # 0.0 to 1.0 (similarity)
    match_status = Column(String(32), nullable=False)  # match, potential_mismatch, mismatch, inconclusive
    image_quality_indicators = Column(JSON, nullable=True)
    model_version = Column(String(64), nullable=False)
    doc_face_coords = Column(JSON, nullable=True)
    probe_face_coords = Column(JSON, nullable=True)
    review_status = Column(String(32), default="pending")
    analyst_notes = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now)
    
    case_rel = relationship("Case", back_populates="face_verifications")

class OSINTFinding(Base):
    __tablename__ = "osint_findings"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    connector_name = Column(String(64), nullable=False)  # e.g. SpiderFoot, theHarvester, Maltego, PublicSanctions
    source_name = Column(String(128), nullable=False)
    source_url = Column(String(512), nullable=True)
    query_target = Column(String(256), nullable=False)
    finding_summary = Column(Text, nullable=False)
    finding_details = Column(JSON, nullable=True)
    investigation_relevance = Column(String(32), default="informational")  # informational, suspicious, adverse, critical
    reliability_assessment = Column(String(32), default="unverified")  # verified_official, high, moderate, unverified, questionable
    verification_status = Column(String(32), default="pending_review")
    analyst_notes = Column(Text, nullable=True)
    collection_timestamp = Column(DateTime(timezone=True), default=utc_now)
    publication_date = Column(String(64), nullable=True)
    
    case_rel = relationship("Case", back_populates="osint_findings")

class DatabaseCheck(Base):
    __tablename__ = "database_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    source_identifier = Column(String(128), nullable=False)  # INTERPOL_SLTD_STOLEN_PASSPORTS, NATIONAL_VISA_GATEWAY, etc.
    request_payload_summary = Column(String(256), nullable=False)
    response_status = Column(String(32), nullable=False)  # verified_valid, revoked_stolen, record_not_found, system_unavailable
    result_reference = Column(String(128), nullable=True)
    explanation = Column(Text, nullable=False)
    is_mock = Column(Boolean, default=False)
    request_timestamp = Column(DateTime(timezone=True), default=utc_now)
    response_timestamp = Column(DateTime(timezone=True), default=utc_now)
    
    case_rel = relationship("Case", back_populates="database_checks")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    category = Column(Enum(RiskCategory), nullable=False)
    risk_score = Column(Float, nullable=False)  # 0 to 100
    contributing_factors = Column(JSON, nullable=False)  # list of factor dicts with evidence pointers
    rule_engine_version = Column(String(32), default="v1.4.0-explainable")
    assessment_timestamp = Column(DateTime(timezone=True), default=utc_now)
    reviewer_status = Column(String(32), default="pending_human_oversight")
    
    case_rel = relationship("Case", back_populates="risk_assessments")

class AuditEvent(Base):
    __tablename__ = "audit_events"
    
    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    actor_username = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False)  # UPLOAD_DOC, OCR_EXTRACT, TAMPERING_SCAN, FACE_VERIFY, OSINT_QUERY, CASE_DECISION
    resource_type = Column(String(64), nullable=False)  # document, case, user, audit
    resource_id = Column(String(64), nullable=False)
    outcome = Column(String(32), nullable=False)  # SUCCESS, FAILURE, DENIED
    details = Column(JSON, nullable=True)
    ip_address = Column(String(64), default="127.0.0.1")
    timestamp = Column(DateTime(timezone=True), default=utc_now)
    
    actor_rel = relationship("User", back_populates="audit_events")
