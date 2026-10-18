import pytest
import os
from app.services.ocr_service import ocr_service
from app.services.validation_service import validation_engine
from app.services.forensics_service import forensics_engine
from app.services.face_service import face_verification_engine
from app.services.risk_service import risk_engine
from app.services.database_service import db_verification_service
from app.services.osint_service import osint_manager
from app.models.models import ValidationStatus, RiskCategory

def test_ocr_mrz_parsing_and_checksum():
    # Mathematically valid ICAO 9303 TD3 check digits:
    # doc P84920194 -> check 0; dob 880414 -> check 5; expiry 300509 -> check 5
    mrz_lines_valid = [
        "P<UTOMORGAN<<ALEXANDER<VICTOR<<<<<<<<<<<<<<<",
        "P849201940UTO8804145M3005095<<<<<<<<<<<<<<02"
    ]
    parsed_valid = ocr_service.parse_mrz(mrz_lines_valid)
    assert parsed_valid["document_code"] == "P"
    assert parsed_valid["issuing_country"] == "UTO"
    assert parsed_valid["full_name"] == "ALEXANDER VICTOR MORGAN"
    assert parsed_valid["document_number"] == "P84920194"
    assert parsed_valid["nationality"] == "UTO"
    assert parsed_valid["date_of_birth"] == "1988-04-14"
    assert parsed_valid["gender"] == "Male"
    assert parsed_valid["expiry_date"] == "2030-05-09"
    assert parsed_valid["checksum_valid"] is True

    # Tampered / corrupted check digits should fail checksum verification
    mrz_lines_invalid = [
        "P<UTOMORGAN<<ALEXANDER<VICTOR<<<<<<<<<<<<<<<",
        "P849201949UTO8804149M3005099<<<<<<<<<<<<<<02"
    ]
    parsed_invalid = ocr_service.parse_mrz(mrz_lines_invalid)
    assert parsed_invalid["checksum_valid"] is False

def test_validation_engine_mandatory_fields():
    # Test valid fields
    valid_fields = [
        {"field_name": "full_name", "extracted_value": "John Doe"},
        {"field_name": "passport_number", "extracted_value": "P12345678"},
        {"field_name": "nationality", "extracted_value": "USA"},
        {"field_name": "date_of_birth", "extracted_value": "1990-01-01"},
        {"field_name": "expiry_date", "extracted_value": "2032-01-01"}
    ]
    results = validation_engine.validate_document(valid_fields, "passport")
    req_rule = next(r for r in results if r["rule_identifier"] == "VAL_REQ_FIELDS")
    assert req_rule["status"] == ValidationStatus.PASSED

    # Test missing field
    missing_fields = [
        {"field_name": "full_name", "extracted_value": "John Doe"}
    ]
    results_missing = validation_engine.validate_document(missing_fields, "passport")
    req_rule_missing = next(r for r in results_missing if r["rule_identifier"] == "VAL_REQ_FIELDS")
    assert req_rule_missing["status"] == ValidationStatus.FAILED

def test_validation_engine_expiry_and_chrono():
    # Expired document
    expired_fields = [
        {"field_name": "full_name", "extracted_value": "Jane Smith"},
        {"field_name": "passport_number", "extracted_value": "P98765432"},
        {"field_name": "nationality", "extracted_value": "GBR"},
        {"field_name": "date_of_birth", "extracted_value": "1985-06-15"},
        {"field_name": "date_of_issue", "extracted_value": "2010-01-01"},
        {"field_name": "expiry_date", "extracted_value": "2020-01-01"}
    ]
    results = validation_engine.validate_document(expired_fields, "passport")
    exp_rule = next(r for r in results if r["rule_identifier"] == "VAL_EXPIRY_CHECK")
    assert exp_rule["status"] == ValidationStatus.FAILED

    # Inverted Chronology (issue >= expiry)
    inverted_fields = [
        {"field_name": "full_name", "extracted_value": "Bad Actor"},
        {"field_name": "date_of_issue", "extracted_value": "2030-01-01"},
        {"field_name": "expiry_date", "extracted_value": "2025-01-01"}
    ]
    results_inv = validation_engine.validate_document(inverted_fields, "passport")
    chrono_rule = next(r for r in results_inv if r["rule_identifier"] == "VAL_CHRONO_CONSISTENCY")
    assert chrono_rule["status"] == ValidationStatus.FAILED

def test_validation_engine_mrz_mismatch():
    mismatched_fields = [
        {"field_name": "full_name", "extracted_value": "Tampered Holder"},
        {"field_name": "passport_number", "extracted_value": "P11111111"},
        {"field_name": "mrz_line1", "extracted_value": "P<UTOMORGAN<<ALEXANDER<VICTOR<<<<<<<<<<<<<<<"},
        {"field_name": "mrz_line2", "extracted_value": "P849201947UTO8804148M3005098<<<<<<<<<<<<<<02"}
    ]
    results = validation_engine.validate_document(mismatched_fields, "passport")
    mrz_rule = next(r for r in results if r["rule_identifier"] == "VAL_MRZ_VISUAL_MATCH")
    assert mrz_rule["status"] == ValidationStatus.FAILED

def test_risk_assessment_engine():
    # Clean case
    clean_assessment = risk_engine.compute_assessment(
        extracted_fields=[{"field_name": "full_name", "extracted_value": "Test Person"}],
        validation_results=[{"rule_name": "Check", "status": "passed", "explanation": "OK"}],
        tampering_findings=[],
        face_verifications=[{"match_status": "match", "comparison_score": 0.95, "model_version": "v1"}],
        database_checks=[{"response_status": "verified_valid", "source_identifier": "INTERPOL"}],
        osint_findings=[{"investigation_relevance": "informational", "finding_summary": "Clean"}]
    )
    assert clean_assessment["category"] == RiskCategory.LOW_CONCERN
    assert clean_assessment["risk_score"] == 0.0

    # Stolen and tampered case
    high_risk_assessment = risk_engine.compute_assessment(
        extracted_fields=[],
        validation_results=[{"rule_name": "Expiry", "status": "failed", "explanation": "Expired"}],
        tampering_findings=[{"finding_type": "photo_manipulation_seam", "severity": "critical", "confidence": 0.9, "explanation": "Tampered"}],
        face_verifications=[{"match_status": "mismatch", "comparison_score": 0.2, "model_version": "v1"}],
        database_checks=[{"response_status": "revoked_stolen", "source_identifier": "INTERPOL_SLTD"}],
        osint_findings=[{"investigation_relevance": "critical", "finding_summary": "Sanctions hit"}]
    )
    assert high_risk_assessment["category"] == RiskCategory.ELEVATED_CONCERN
    assert high_risk_assessment["risk_score"] >= 80.0
    assert len(high_risk_assessment["contributing_factors"]) >= 4

@pytest.mark.anyio
async def test_database_verification_service():
    # Stolen check
    results_stolen = await db_verification_service.verify_against_databases(
        doc_number="P84920194",
        country_code="UTO",
        services=["INTERPOL_SLTD", "NATIONAL_VISA_SYS"]
    )
    assert len(results_stolen) == 2
    assert results_stolen[0]["response_status"] == "revoked_stolen"

    # Clean check
    results_clean = await db_verification_service.verify_against_databases(
        doc_number="P12300099",
        country_code="UTO",
        services=["INTERPOL_SLTD"]
    )
    assert results_clean[0]["response_status"] == "verified_valid"

@pytest.mark.anyio
async def test_osint_manager():
    status_dict = osint_manager.get_status()
    assert "spiderfoot" in status_dict
    assert "theharvester" in status_dict
    assert "maltego" in status_dict
    assert "sanctions_watch" in status_dict

    findings = await osint_manager.execute_search(
        target="VIKTOR KASLOV",
        query_type="identity_name",
        selected_connectors=["spiderfoot", "sanctions_watch"]
    )
    assert len(findings) == 2
    sanctions_hit = next(f for f in findings if f["connector_name"] == "SanctionsWatch")
    assert sanctions_hit["investigation_relevance"] == "adverse"
