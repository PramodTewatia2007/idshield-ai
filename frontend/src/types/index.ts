export type UserRole = 'admin' | 'officer' | 'investigator' | 'supervisor' | 'auditor';

export type CaseStatus = 
  | 'new'
  | 'processing'
  | 'awaiting_verification'
  | 'manual_review_required'
  | 'under_investigation'
  | 'closed';

export type DocumentType = 'passport' | 'visa' | 'national_id' | 'driving_license' | 'residence_permit' | 'unknown';
export type ValidationStatus = 'passed' | 'failed' | 'requires_review' | 'unable_to_verify' | 'source_unavailable';
export type RiskCategory = 'low_concern' | 'review_recommended' | 'elevated_concern' | 'verification_unavailable';

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface ExtractedField {
  id: number;
  document_id: number;
  field_name: string;
  field_label: string;
  extracted_value: string | null;
  ocr_confidence: number;
  is_corrected: boolean;
  original_value?: string;
  review_status: string;
  bounding_box?: [number, number, number, number];
}

export interface ValidationResult {
  id: number;
  document_id: number;
  rule_identifier: string;
  rule_name: string;
  status: ValidationStatus;
  explanation: string;
  source_reference?: string;
  evidence_data?: any;
  timestamp: string;
}

export interface TamperingFinding {
  id: number;
  document_id: number;
  finding_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  region_coordinates?: [number, number, number, number];
  confidence: number;
  explanation: string;
  model_version: string;
  recommended_checks?: string;
  created_at: string;
}

export interface FaceVerification {
  id: number;
  case_id: number;
  verification_method: string;
  comparison_score: number;
  match_status: string;
  model_version: string;
  doc_face_coords?: [number, number, number, number];
  probe_face_coords?: [number, number, number, number];
  review_status: string;
  analyst_notes?: string;
  timestamp: string;
}

export interface OSINTFinding {
  id: number;
  case_id: number;
  connector_name: string;
  source_name: string;
  source_url?: string;
  query_target: string;
  finding_summary: string;
  finding_details?: any;
  investigation_relevance: string;
  reliability_assessment: string;
  verification_status: string;
  analyst_notes?: string;
  collection_timestamp: string;
  publication_date?: string;
}

export interface DatabaseCheck {
  id: number;
  case_id: number;
  source_identifier: string;
  request_payload_summary: string;
  response_status: string;
  result_reference?: string;
  explanation: string;
  is_mock: boolean;
  request_timestamp: string;
}

export interface RiskAssessment {
  id: number;
  case_id: number;
  category: RiskCategory;
  risk_score: number;
  contributing_factors: Array<{
    factor: string;
    impact: string;
    category: string;
    explanation: string;
    evidence_id?: string;
  }>;
  rule_engine_version: string;
  assessment_timestamp: string;
}

export interface DocumentRecord {
  id: number;
  case_id: number;
  document_type: DocumentType;
  file_name: string;
  file_path: string;
  file_hash: string;
  file_size: number;
  mime_type: string;
  processing_status: string;
  upload_timestamp: string;
  extracted_fields: ExtractedField[];
  validation_results: ValidationResult[];
  tampering_findings: TamperingFinding[];
}

export interface CaseRecord {
  id: number;
  case_reference: string;
  title: string;
  description?: string;
  status: CaseStatus;
  assigned_officer_id?: number;
  created_at: string;
  updated_at: string;
  review_notes?: string;
  final_decision?: string;
  documents: DocumentRecord[];
  osint_findings: OSINTFinding[];
  database_checks: DatabaseCheck[];
  face_verifications: FaceVerification[];
  risk_assessments: RiskAssessment[];
}

export interface DashboardMetrics {
  documents_processed: number;
  cases_awaiting_review: number;
  potential_anomalies: number;
  validation_failures: number;
  osint_investigations: number;
  avg_processing_time_sec: number;
  recent_activity: Array<{
    id: number;
    action: string;
    actor: string;
    resource: string;
    outcome: string;
    timestamp: string;
  }>;
  integration_status: Record<string, string>;
}
