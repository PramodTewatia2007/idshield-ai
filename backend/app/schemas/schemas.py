from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.models import UserRole, CaseStatus, DocumentType, ValidationStatus, RiskCategory

# User Schemas
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_info: Dict[str, Any]

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Extracted Field Schemas
class ExtractedFieldResponse(BaseModel):
    id: int
    document_id: int
    field_name: str
    field_label: str
    extracted_value: Optional[str] = None
    ocr_confidence: float
    is_corrected: bool
    original_value: Optional[str] = None
    review_status: str
    bounding_box: Optional[List[int]] = None
    
    model_config = ConfigDict(from_attributes=True)

class FieldCorrectionRequest(BaseModel):
    corrected_value: str

# Validation Schemas
class ValidationResultResponse(BaseModel):
    id: int
    document_id: int
    rule_identifier: str
    rule_name: str
    status: ValidationStatus
    explanation: str
    source_reference: Optional[str] = None
    evidence_data: Optional[Dict[str, Any]] = None
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Tampering Findings Schemas
class TamperingFindingResponse(BaseModel):
    id: int
    document_id: int
    finding_type: str
    severity: str
    region_coordinates: Optional[List[int]] = None
    confidence: float
    explanation: str
    model_version: str
    visual_evidence_url: Optional[str] = None
    recommended_checks: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Face Verification Schemas
class FaceVerificationRequest(BaseModel):
    probe_image_base64: Optional[str] = None

class FaceVerificationResponse(BaseModel):
    id: int
    case_id: int
    verification_method: str
    comparison_score: float
    match_status: str
    image_quality_indicators: Optional[Dict[str, Any]] = None
    model_version: str
    doc_face_coords: Optional[List[int]] = None
    probe_face_coords: Optional[List[int]] = None
    review_status: str
    analyst_notes: Optional[str] = None
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

# OSINT Finding Schemas
class OSINTFindingResponse(BaseModel):
    id: int
    case_id: int
    connector_name: str
    source_name: str
    source_url: Optional[str] = None
    query_target: str
    finding_summary: str
    finding_details: Optional[Dict[str, Any]] = None
    investigation_relevance: str
    reliability_assessment: str
    verification_status: str
    analyst_notes: Optional[str] = None
    collection_timestamp: datetime
    publication_date: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class OSINTSearchRequest(BaseModel):
    query_target: str
    query_type: str = "identity_name"  # identity_name, passport_number, domain, organization
    connectors: List[str] = ["spiderfoot", "theharvester", "maltego", "sanctions_watch"]

# Database Check Schemas
class DatabaseCheckRequest(BaseModel):
    document_number: str
    issuing_country: str
    services: List[str] = ["INTERPOL_SLTD", "GOV_VISA_SYS", "STOLEN_DOCS_FEED"]

class DatabaseCheckResponse(BaseModel):
    id: int
    case_id: int
    source_identifier: str
    request_payload_summary: str
    response_status: str
    result_reference: Optional[str] = None
    explanation: str
    is_mock: bool
    request_timestamp: datetime
    response_timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Risk Assessment Schemas
class RiskAssessmentResponse(BaseModel):
    id: int
    case_id: int
    category: RiskCategory
    risk_score: float
    contributing_factors: List[Dict[str, Any]]
    rule_engine_version: str
    assessment_timestamp: datetime
    reviewer_status: str
    
    model_config = ConfigDict(from_attributes=True)

# Document Schemas
class DocumentResponse(BaseModel):
    id: int
    case_id: int
    document_type: DocumentType
    file_name: str
    file_path: str
    file_hash: str
    file_size: int
    mime_type: str
    processing_status: str
    upload_timestamp: datetime
    extracted_fields: List[ExtractedFieldResponse] = []
    validation_results: List[ValidationResultResponse] = []
    tampering_findings: List[TamperingFindingResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

# Case Schemas
class CaseCreate(BaseModel):
    title: str
    description: Optional[str] = None

class CaseReviewRequest(BaseModel):
    decision: str  # APPROVED, REJECTED, ESCALATED, HOLD
    review_notes: str

class CaseResponse(BaseModel):
    id: int
    case_reference: str
    title: str
    description: Optional[str] = None
    status: CaseStatus
    assigned_officer_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    review_notes: Optional[str] = None
    final_decision: Optional[str] = None
    documents: List[DocumentResponse] = []
    osint_findings: List[OSINTFindingResponse] = []
    database_checks: List[DatabaseCheckResponse] = []
    face_verifications: List[FaceVerificationResponse] = []
    risk_assessments: List[RiskAssessmentResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

# Audit Event Schema
class AuditEventResponse(BaseModel):
    id: int
    actor_username: str
    action: str
    resource_type: str
    resource_id: str
    outcome: str
    details: Optional[Dict[str, Any]] = None
    ip_address: str
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Dashboard Metrics Schema
class DashboardMetrics(BaseModel):
    documents_processed: int
    cases_awaiting_review: int
    potential_anomalies: int
    validation_failures: int
    osint_investigations: int
    avg_processing_time_sec: float
    recent_activity: List[Dict[str, Any]]
    integration_status: Dict[str, str]
