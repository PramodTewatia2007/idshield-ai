import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.init_db import init_db_and_seed

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_full_api_workflow():
    # 1. Initialize DB and demonstration seeds
    await init_db_and_seed()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test Root Endpoint (JSON default for API clients)
        root_resp = await client.get("/")
        assert root_resp.status_code == 200
        assert root_resp.json()["status"] == "online"

        # Test Root with browser Accept header (HTML SPA)
        html_root = await client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
        assert html_root.status_code == 200
        assert "<!doctype html" in html_root.text.lower() or "<html" in html_root.text.lower()

        # Test SPA client-side route fallback
        spa_resp = await client.get("/cases")
        assert spa_resp.status_code == 200
        assert "<!doctype html" in spa_resp.text.lower() or "<html" in spa_resp.text.lower()

        # Test Top-level Health Check (used by Render)
        health_resp = await client.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "online"

        # Test API Health Check
        h_resp = await client.get("/api/health")
        assert h_resp.status_code == 200
        assert h_resp.json()["status"] == "healthy"
        
        # Test Invalid Login Rejection
        bad_login = await client.post(
            "/api/auth/login",
            data={"username": "officer", "password": "WrongPassword123!"}
        )
        assert bad_login.status_code == 401

        # Test Valid Officer Login via Form Data
        login_resp = await client.post(
            "/api/auth/login",
            data={"username": "officer", "password": "Officer@123456"}
        )
        assert login_resp.status_code == 200
        token_data = login_resp.json()
        assert "access_token" in token_data
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test Valid Admin Login via JSON Data
        admin_login_resp = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin@123456"}
        )
        assert admin_login_resp.status_code == 200
        assert "access_token" in admin_login_resp.json()

        # Test /auth/me
        me_resp = await client.get("/api/auth/me", headers=headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["username"] == "officer"

        # Test List Cases
        cases_resp = await client.get("/api/cases", headers=headers)
        assert cases_resp.status_code == 200
        cases = cases_resp.json()
        assert len(cases) >= 2
        
        # Find a case with attached documents
        case_with_docs = next((c for c in cases if c.get("documents")), cases[0])
        case_id = case_with_docs["id"]
        c_detail = await client.get(f"/api/cases/{case_id}", headers=headers)
        assert c_detail.status_code == 200
        assert c_detail.json()["case_reference"] == case_with_docs["case_reference"]

        # Test Create New Case
        create_case_resp = await client.post(
            "/api/cases",
            headers=headers,
            json={"title": "Test Transit Passenger Examination", "description": "Automated verification test case"}
        )
        assert create_case_resp.status_code == 200
        new_case_id = create_case_resp.json()["id"]

        # Test Re-analysis and Duplicate Purging on Document
        first_doc = case_with_docs["documents"][0]
        doc_id = first_doc["id"]
        
        reanalyze1_resp = await client.post(f"/api/documents/{doc_id}/analyze", headers=headers)
        assert reanalyze1_resp.status_code == 200
        fields1 = reanalyze1_resp.json()["extracted_fields"]
        assert len(fields1) > 0

        # Calling analyze a second time must purge old fields and remain at the exact same count (no duplicates)
        reanalyze2_resp = await client.post(f"/api/documents/{doc_id}/analyze", headers=headers)
        assert reanalyze2_resp.status_code == 200
        fields2 = reanalyze2_resp.json()["extracted_fields"]
        assert len(fields2) == len(fields1)

        # Test Field Correction on Extracted Field
        if fields2:
            field_id = fields2[0]["id"]
            correct_resp = await client.put(
                f"/api/documents/fields/{field_id}/correct",
                headers=headers,
                json={"corrected_value": "VERIFIED_TEST_VALUE"}
            )
            assert correct_resp.status_code == 200
            assert correct_resp.json()["extracted_value"] == "VERIFIED_TEST_VALUE"
            assert correct_resp.json()["is_corrected"] is True

        # Test OSINT Query on Case
        osint_resp = await client.post(
            f"/api/cases/{case_id}/osint-search",
            headers=headers,
            json={
                "query_target": "ALEXANDER MORGAN",
                "query_type": "identity_name",
                "connectors": ["spiderfoot", "theharvester", "maltego", "sanctions_watch"]
            }
        )
        assert osint_resp.status_code == 200
        assert len(osint_resp.json()) >= 3

        # Test Database Verification (INTERPOL SLTD & Visa)
        db_resp = await client.post(
            f"/api/cases/{case_id}/database-check",
            headers=headers,
            json={
                "document_number": "P84920194",
                "issuing_country": "UTO",
                "services": ["INTERPOL_SLTD", "NATIONAL_VISA_SYS"]
            }
        )
        assert db_resp.status_code == 200
        assert len(db_resp.json()) >= 2

        # Test Biometric Face Verification Probe Assessment
        face_resp = await client.post(
            f"/api/cases/{case_id}/face-verify",
            headers=headers,
            json={}
        )
        assert face_resp.status_code == 200
        assert face_resp.json()["match_status"] == "awaiting_probe_capture"

        # Test Case Review & Adjudication Decision
        review_resp = await client.post(
            f"/api/cases/{case_id}/review",
            headers=headers,
            json={"decision": "APPROVED", "review_notes": "All checks validated and clear."}
        )
        assert review_resp.status_code == 200
        assert review_resp.json()["final_decision"] == "APPROVED"
        assert review_resp.json()["status"] == "closed"

        # Test PDF Report Generation & Download
        report_resp = await client.get(f"/api/cases/{case_id}/report", headers=headers)
        assert report_resp.status_code == 200
        assert report_resp.headers["content-type"] == "application/pdf"
        assert len(report_resp.content) > 1000

        # Test Dashboard Metrics
        m_resp = await client.get("/api/dashboard/metrics", headers=headers)
        assert m_resp.status_code == 200
        metrics = m_resp.json()
        assert metrics["documents_processed"] >= 2
        assert "recent_activity" in metrics
        assert "integration_status" in metrics

        # Test Audit Events Trail
        audit_resp = await client.get("/api/audit-events?limit=20", headers=headers)
        assert audit_resp.status_code == 200
        assert len(audit_resp.json()) > 0
