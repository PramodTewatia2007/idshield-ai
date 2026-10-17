from typing import Dict, Any, List
from datetime import datetime, timezone

class DatabaseVerificationService:
    """
    Authorized Database Verification Service.
    Queries official mock/authorized endpoints:
    - INTERPOL Stolen & Lost Travel Documents (SLTD)
    - National Visa Verification Gateway
    - Document Revocation / Border Alerts Registry
    """
    def __init__(self):
        self.version = "1.0.0-auth-gateway"

    async def verify_against_databases(self, doc_number: str, country_code: str, services: List[str]) -> List[Dict[str, Any]]:
        results = []
        doc_num_clean = doc_number.strip().upper()
        
        # Test stolen/revoked pattern
        is_stolen = "84920" in doc_num_clean or "STOLEN" in doc_num_clean or "REVOKED" in doc_num_clean

        for s in services:
            s_upper = s.upper()
            if "INTERPOL" in s_upper or "SLTD" in s_upper:
                if is_stolen:
                    results.append({
                        "source_identifier": "INTERPOL_SLTD_GLOBAL_DATABASE",
                        "request_payload_summary": f"Query: DocNum={doc_num_clean}, Issuer={country_code}",
                        "response_status": "revoked_stolen",
                        "result_reference": "SLTD-ALERT-99214-INTERPOL",
                        "explanation": f"Document {doc_num_clean} is actively listed in the INTERPOL Stolen and Lost Travel Documents (SLTD) database. Flagged as reported stolen by issuing state.",
                        "is_mock": True
                    })
                else:
                    results.append({
                        "source_identifier": "INTERPOL_SLTD_GLOBAL_DATABASE",
                        "request_payload_summary": f"Query: DocNum={doc_num_clean}, Issuer={country_code}",
                        "response_status": "verified_valid",
                        "result_reference": f"SLTD-CLEAR-{doc_num_clean[:4]}",
                        "explanation": f"Document {doc_num_clean} does not appear in INTERPOL SLTD database. No loss or theft recorded.",
                        "is_mock": True
                    })
            elif "VISA" in s_upper:
                results.append({
                    "source_identifier": "NATIONAL_VISA_CENTRAL_GATEWAY",
                    "request_payload_summary": f"Query: TravelDoc={doc_num_clean}, Issuer={country_code}",
                    "response_status": "verified_valid",
                    "result_reference": f"NVCG-AUTH-{doc_num_clean[-4:]}",
                    "explanation": f"Authorized visa link confirmed. Associated electronic travel authorization active in central immigration database.",
                    "is_mock": True
                })
            else:
                results.append({
                    "source_identifier": "REVOKED_DOCUMENTS_BULLETIN",
                    "request_payload_summary": f"Query: DocNum={doc_num_clean}",
                    "response_status": "verified_valid",
                    "result_reference": "RDB-CLEAR",
                    "explanation": "No administrative revocations or passport hold orders found.",
                    "is_mock": True
                })

        return results

db_verification_service = DatabaseVerificationService()
