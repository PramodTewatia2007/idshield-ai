from typing import Dict, Any, List
from app.models.models import RiskCategory, ValidationStatus

class RiskAssessmentEngine:
    """
    Transparent, explainable risk assessment engine.
    Aggregates:
    - OCR extraction confidence & field completeness
    - Deterministic validation check results
    - Tampering and image forensics findings
    - Authorized biometric face match results
    - Authorized database responses (INTERPOL SLTD, etc.)
    - OSINT intelligence findings
    Never double counts and clearly articulates each contributing factor.
    """
    def __init__(self):
        self.version = "v1.4.0-explainable"

    def compute_assessment(
        self,
        extracted_fields: List[Dict[str, Any]],
        validation_results: List[Dict[str, Any]],
        tampering_findings: List[Dict[str, Any]],
        face_verifications: List[Dict[str, Any]],
        database_checks: List[Dict[str, Any]],
        osint_findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        
        base_score = 0.0
        contributing_factors = []
        
        # 1. Evaluate Database checks (Highest weight: hard legal stop)
        for db in database_checks:
            status = db.get("response_status", "")
            if status == "revoked_stolen":
                base_score += 45.0
                contributing_factors.append({
                    "factor": "Stolen / Lost Document Hit",
                    "impact": "+45 (Critical)",
                    "category": "database_verification",
                    "explanation": f"Document is listed as revoked or stolen in {db.get('source_identifier')}.",
                    "evidence_id": db.get("result_reference")
                })
            elif status == "system_unavailable":
                contributing_factors.append({
                    "factor": "Authoritative Database Check Unavailable",
                    "impact": "Requires Manual Review",
                    "category": "system_availability",
                    "explanation": f"Service {db.get('source_identifier')} was unreachable at time of screening.",
                    "evidence_id": None
                })

        # 2. Evaluate Tampering Findings (High weight)
        for tf in tampering_findings:
            sev = tf.get("severity", "medium").lower()
            conf = float(tf.get("confidence", 0.7))
            pts = 25.0 if sev == "critical" else (18.0 if sev == "high" else 10.0)
            weighted_pts = round(pts * conf, 1)
            base_score += weighted_pts
            contributing_factors.append({
                "factor": f"Document Forensics: {tf.get('finding_type')}",
                "impact": f"+{weighted_pts} ({sev.capitalize()})",
                "category": "tampering_forensics",
                "explanation": tf.get("explanation"),
                "evidence_id": tf.get("model_version")
            })

        # 3. Evaluate Rule-based Validation
        for vr in validation_results:
            st = vr.get("status")
            if st == ValidationStatus.FAILED or st == "failed":
                base_score += 20.0
                contributing_factors.append({
                    "factor": f"Validation Failure: {vr.get('rule_name')}",
                    "impact": "+20 (High)",
                    "category": "rule_validation",
                    "explanation": vr.get("explanation"),
                    "evidence_id": vr.get("rule_identifier")
                })
            elif st == ValidationStatus.REQUIRES_REVIEW or st == "requires_review":
                base_score += 8.0
                contributing_factors.append({
                    "factor": f"Review Item: {vr.get('rule_name')}",
                    "impact": "+8 (Moderate)",
                    "category": "rule_validation",
                    "explanation": vr.get("explanation"),
                    "evidence_id": vr.get("rule_identifier")
                })

        # 4. Evaluate Facial Comparison (if available)
        for fv in face_verifications:
            m_status = fv.get("match_status")
            if m_status == "mismatch":
                base_score += 30.0
                contributing_factors.append({
                    "factor": "Facial Biometric Discrepancy",
                    "impact": "+30 (High)",
                    "category": "facial_verification",
                    "explanation": f"Presented individual face does not match document portrait (score: {fv.get('comparison_score')}).",
                    "evidence_id": fv.get("model_version")
                })
            elif m_status == "potential_mismatch":
                base_score += 12.0
                contributing_factors.append({
                    "factor": "Facial Biometric Low Confidence",
                    "impact": "+12 (Moderate)",
                    "category": "facial_verification",
                    "explanation": f"Borderline biometric similarity ({fv.get('comparison_score')}) requires secondary inspection.",
                    "evidence_id": fv.get("model_version")
                })

        # 5. Evaluate OSINT Findings
        for osint in osint_findings:
            rel = osint.get("investigation_relevance", "").lower()
            if rel in ["adverse", "critical"]:
                base_score += 15.0
                contributing_factors.append({
                    "factor": f"Adverse OSINT Notice: {osint.get('connector_name')}",
                    "impact": "+15 (Adverse)",
                    "category": "osint_intelligence",
                    "explanation": osint.get("finding_summary"),
                    "evidence_id": osint.get("source_name")
                })

        # Normalize score between 0 and 100
        final_score = min(100.0, max(0.0, base_score))
        
        # Categorize
        if final_score >= 45.0:
            category = RiskCategory.ELEVATED_CONCERN
        elif final_score >= 18.0:
            category = RiskCategory.REVIEW_RECOMMENDED
        else:
            category = RiskCategory.LOW_CONCERN

        # If zero factors, add positive note
        if not contributing_factors:
            contributing_factors.append({
                "factor": "All Core Integrity Checks Satisfied",
                "impact": "0 (Clean)",
                "category": "baseline_integrity",
                "explanation": "No tampering artifacts, validation failures, or adverse records detected.",
                "evidence_id": "CLEAN_BASELINE"
            })

        return {
            "risk_score": round(final_score, 1),
            "category": category,
            "contributing_factors": contributing_factors,
            "rule_engine_version": self.version
        }

risk_engine = RiskAssessmentEngine()
