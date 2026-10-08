"""
Level 2 Integration Tests for FastAPI Backend.
Validates HTTP endpoints, health checks, call management, report generation, audit verification, and bulk processing.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


from backend.auth.models import UserStore
from backend.auth.dependencies import create_session_jwt


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["backend"] == "ok"
        assert "gpu" in data
        assert "models" in data
        assert data["models"]["visual_efficientnet_b0"] == "ready"


@pytest.mark.asyncio
async def test_call_lifecycle_and_audit():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Create Call
        res_create = await ac.post("/api/v1/calls", json={"title": "Forensic Inspection Test", "room_id": "test-room-1"})
        assert res_create.status_code == 200
        call_data = res_create.json()
        call_id = call_data["call_id"]
        assert call_id.startswith("CALL-")

        # 2. Get Call Details
        res_get = await ac.get(f"/api/v1/calls/{call_id}")
        assert res_get.status_code == 200
        assert res_get.json()["room_id"] == "test-room-1"

        # 3. Check Initial Timeline and Events
        res_tl = await ac.get(f"/api/v1/calls/{call_id}/timeline")
        assert res_tl.status_code == 200
        assert "timeline" in res_tl.json()

        res_ev = await ac.get(f"/api/v1/calls/{call_id}/events")
        assert res_ev.status_code == 200

        # 4. Check Evidence Endpoint
        res_evi = await ac.get(f"/api/v1/calls/{call_id}/evidence")
        assert res_evi.status_code == 200
        assert "events_count" in res_evi.json()

        # 5. Check Forensic Report (JSON)
        res_rep_json = await ac.get(f"/api/v1/calls/{call_id}/report?format=json")
        assert res_rep_json.status_code == 200
        rep_data = res_rep_json.json()
        assert "report_id" in rep_data
        assert "summary_narrative" in rep_data
        assert "disclaimer" in rep_data

        # 6. Check Forensic Report (HTML)
        res_rep_html = await ac.get(f"/api/v1/calls/{call_id}/report?format=html")
        assert res_rep_html.status_code == 200
        assert "<html" in res_rep_html.text

        # 7. Check Forensic Report (PDF)
        res_rep_pdf = await ac.get(f"/api/v1/calls/{call_id}/report?format=pdf")
        assert res_rep_pdf.status_code == 200
        assert res_rep_pdf.headers.get("content-type") == "application/pdf"
        assert res_rep_pdf.content.startswith(b"%PDF")

        # 8. Check Audit Chain Verification
        res_audit = await ac.get(f"/api/v1/calls/{call_id}/audit/verify")
        assert res_audit.status_code == 200
        audit_verify = res_audit.json()
        assert audit_verify["valid"] is True
        assert audit_verify["chain_length"] >= 2  # CALL_CREATED + REPORT_CREATED


@pytest.mark.asyncio
async def test_models_and_metrics_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_models = await ac.get("/api/v1/models")
        assert res_models.status_code == 200
        models_list = res_models.json()
        assert len(models_list) >= 4
        names = [m["name"] for m in models_list]
        assert "EfficientNet-B0" in names
        assert "AASIST-L" in names

        res_metrics = await ac.get("/api/v1/metrics")
        assert res_metrics.status_code == 200
        metrics = res_metrics.json()
        assert "gpu" in metrics
        assert "total_dropped_frames" in metrics


@pytest.mark.asyncio
async def test_bulk_verification_with_dataset():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        user_store = UserStore.get_instance()
        officer = user_store.get_by_email("officer@court.demo")
        token = create_session_jwt(officer)
        headers = {"Authorization": f"Bearer {token}"}

        dataset_path = "c:/Users/sunil/OneDrive/Documents/hackathon/REC_Hack/archive/FaceForensics++_C23/original"
        res_bulk = await ac.post("/api/v1/bulk", data={"dataset_folder": dataset_path}, headers=headers)
        assert res_bulk.status_code == 200
        job_data = res_bulk.json()
        assert job_data["job_id"].startswith("JOB-")
        assert job_data["total_files"] > 0
