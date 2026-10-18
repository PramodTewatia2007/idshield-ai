import pytest
import io
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.init_db import init_db_and_seed
from app.core.auth import create_access_token

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_report_download_auth_modes():
    await init_db_and_seed()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Unauthenticated download must return 401
        unauth_resp = await client.get("/api/cases/1/report")
        assert unauth_resp.status_code == 401

        # 2. Header authentication download must return 200 PDF
        token = create_access_token(subject="officer", role="officer")
        header_resp = await client.get(
            "/api/cases/1/report",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert header_resp.status_code == 200
        assert header_resp.headers["content-type"] == "application/pdf"

        # 3. Query token authentication (for browser <a> direct links) must return 200 PDF
        query_token_resp = await client.get(f"/api/cases/1/report?token={token}")
        assert query_token_resp.status_code == 200
        assert query_token_resp.headers["content-type"] == "application/pdf"

        # 4. Invalid query token must return 401
        invalid_token_resp = await client.get("/api/cases/1/report?token=invalid.jwt.token")
        assert invalid_token_resp.status_code == 401

@pytest.mark.anyio
async def test_document_upload_path_traversal_sanitization():
    await init_db_and_seed()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = create_access_token(subject="officer", role="officer")
        headers = {"Authorization": f"Bearer {token}"}

        # Attempt to upload with path traversal in filename
        malicious_filename = "../../../etc_passwd_exploit.jpg"
        fake_content = b"\xFF\xD8\xFF\xE0" + b"A" * 1024  # Minimal JPEG header
        files = {
            "file": (malicious_filename, io.BytesIO(fake_content), "image/jpeg")
        }
        data = {
            "case_id": "1",
            "doc_type_hint": "passport"
        }

        resp = await client.post("/api/documents/upload", headers=headers, files=files, data=data)
        assert resp.status_code == 200
        doc_data = resp.json()

        # The saved file_path must NOT contain directory traversal
        assert ".." not in doc_data["file_path"]
        assert doc_data["file_name"] == malicious_filename
        # Check that file_url is serialized
        assert "file_url" in doc_data
        assert doc_data["file_url"].startswith("/storage/documents/")
