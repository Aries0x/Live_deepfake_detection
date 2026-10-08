"""
Call Session, Timeline, Evidence, and Audit REST API Endpoints.
"""
import asyncio
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import HTMLResponse
from backend.app.schemas.contracts import (
    CallCreateRequest,
    CallResponse,
)
from backend.app.services.call_manager import CallManager
from backend.app.services.gpu_worker import ForensicGPUWorker
from audit.hash_chain import AuditChainManager
from reports.generator import ForensicReportGenerator

router = APIRouter()


async def _async_sync_call_report(report_dict: dict, html_content: str):
    """Background task to sync generated report to Supabase storage & DB without delaying download."""
    try:
        from backend.app.services.supabase_service import SupabaseService
        supabase_svc = SupabaseService.get_instance()
        if supabase_svc.client:
            storage_url = await asyncio.to_thread(supabase_svc.upload_report_html, report_dict["report_id"], html_content)
            await asyncio.to_thread(supabase_svc.upload_report_json, report_dict["report_id"], report_dict)
            await supabase_svc.persist_forensic_report(
                report_dict=report_dict,
                html_content=html_content,
                storage_url=storage_url
            )
            report_dict["storage_url"] = storage_url
    except Exception:
        pass


@router.post("/calls", response_model=CallResponse)
async def create_call(req: CallCreateRequest):
    call_mgr = CallManager.get_instance()
    call = call_mgr.create_call(room_id=req.room_id, title=req.title)
    return CallResponse(
        call_id=call.call_id,
        room_id=call.room_id,
        created_at=call.created_at,
        status=call.status,
    )


@router.get("/calls/{call_id}", response_model=CallResponse)
async def get_call(call_id: str):
    call_mgr = CallManager.get_instance()
    call = call_mgr.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call session not found")
    return CallResponse(
        call_id=call.call_id,
        room_id=call.room_id,
        created_at=call.created_at,
        status=call.status,
    )


@router.get("/calls/{call_id}/timeline")
async def get_call_timeline(call_id: str):
    call_mgr = CallManager.get_instance()
    call = call_mgr.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call session not found")
    return {"call_id": call_id, "timeline": call.timeline}


@router.get("/calls/{call_id}/events")
async def get_call_events(call_id: str):
    call_mgr = CallManager.get_instance()
    call = call_mgr.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call session not found")
    return {"call_id": call_id, "events": call.events}


@router.get("/calls/{call_id}/evidence")
async def get_call_evidence(call_id: str):
    call_mgr = CallManager.get_instance()
    call = call_mgr.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call session not found")
    
    worker = ForensicGPUWorker.get_instance()
    session_key = f"{call_id}:remote"
    session = worker.sessions.get(session_key)

    heatmap_b64 = session.last_heatmap_base64 if session else None
    last_update = session.last_risk_update if session else None
    
    # Run evidence stability evaluation if frame is available
    stability_data = None
    if session and session.last_frame_bgr is not None:
        face_tracks = worker.face_detector.track_and_crop(session.last_frame_bgr)
        if face_tracks:
            crop = face_tracks[0][1]
            base_risk = last_update.calibrated_risk_score if last_update else 0.5
            stability_res = worker.stability_engine.evaluate_stability(crop, base_risk)
            stability_data = stability_res.model_dump()

    return {
        "call_id": call_id,
        "latest_update": last_update,
        "heatmap_base64": heatmap_b64,
        "stability": stability_data,
        "events_count": len(call.events),
    }


@router.get("/calls/{call_id}/report")
async def get_call_report(call_id: str, format: str = Query("json", pattern="^(json|html|pdf)$")):
    call_mgr = CallManager.get_instance()
    call = call_mgr.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call session not found")

    worker = ForensicGPUWorker.get_instance()
    session = (
        worker.sessions.get(f"{call.call_id}:remote")
        or worker.sessions.get(f"{call.call_id}:local")
        or worker.sessions.get(f"{call_id}:remote")
        or worker.sessions.get(f"{call_id}:local")
    )
    if not session:
        for k, s in worker.sessions.items():
            if k.startswith(f"{call.call_id}:") or k.startswith(f"{call_id}:"):
                session = s
                break

    last_update = session.last_risk_update if session else None
    has_frames = len(call.timeline) > 0
    has_audio = any(t.audio is not None for t in call.timeline)

    if has_frames:
        cal_risk = last_update.calibrated_risk_score if last_update else round(
            sum((t.calibrated_risk_score or 0.15) for t in call.timeline) / len(call.timeline), 4
        )
        assessment = last_update.classification if last_update else (
            "LIKELY_MANIPULATED" if cal_risk >= 0.55 else ("INCONCLUSIVE" if cal_risk >= 0.35 else "LIKELY_AUTHENTIC")
        )
    else:
        cal_risk = 0.0
        assessment = "INCONCLUSIVE"

    cam_str = "Physical Web Camera (Direct Hardware Sensor)"
    if session:
        if getattr(session, "is_obs", False):
            cam_str = "OBS Virtual Camera (Simulated / Face Swap Active)"
        elif getattr(session, "source_device", None):
            cam_str = str(session.source_device)

    metrics = {
        "frames_sampled": len(call.timeline),
        "suspicious_frames": sum(1 for t in call.timeline if (t.visual or 0.0) >= 0.55),
        "audio_windows_analyzed": sum(1 for t in call.timeline if t.audio is not None),
        "voice_anomaly_detected": any((t.audio or 0.0) >= 0.55 for t in call.timeline),
        "camera_source": cam_str,
        "mean_visual_score": round(
            sum((t.visual or 0.0) for t in call.timeline) / max(1, len(call.timeline)), 4
        ) if has_frames else 0.0,
        "mean_audio_score": round(
            sum((t.audio or 0.0) for t in call.timeline if t.audio is not None) / max(1, sum(1 for t in call.timeline if t.audio is not None)), 4
        ) if has_audio else 0.0,
        "mean_av_sync_score": round(
            sum((t.av_sync or 1.0) for t in call.timeline) / max(1, len(call.timeline)), 2
        ) if (has_frames and has_audio) else None,
    }

    # Check cache on call object to avoid duplicate computation
    cached_report = getattr(call, "_cached_report", None)
    cached_len = getattr(call, "_cached_timeline_len", -1)
    need_ai = (format == "html")

    if cached_report and cached_len == len(call.timeline) and (not need_ai or cached_report.get("ai_reasoning")):
        report_dict = cached_report
    else:
        report_dict = ForensicReportGenerator.create_report(
            call_id=call_id,
            media_sha256="live-webrtc-stream",
            final_assessment=assessment,
            calibrated_risk=cal_risk,
            metrics=metrics,
            model_versions={
                "visual": "efficientnet_b0_v1.0.0",
                "audio": "aasist_l_v1.0.0",
                "temporal": "temporal_gru_v1.0.0",
            },
            events=[e.model_dump() for e in call.events],
            audit_events=[e.model_dump() for e in call.audit_chain.chain],
            segments=[e.model_dump() for e in call.events],
            include_ai_reasoning=need_ai,
        )
        call._cached_report = report_dict
        call._cached_timeline_len = len(call.timeline)
        call.audit_chain.append_event("REPORT_CREATED", {"report_id": report_dict["report_id"]})

    # Prepare HTML content and trigger background cloud sync without blocking PDF download
    html_content = getattr(call, "_cached_html", None)
    if not html_content or cached_len != len(call.timeline):
        html_content = ForensicReportGenerator.render_html(report_dict)
        call._cached_html = html_content

    # Fire background task for Supabase uploads (non-blocking)
    asyncio.create_task(_async_sync_call_report(report_dict, html_content))

    if format == "html":
        return HTMLResponse(content=html_content)
    elif format == "pdf":
        cached_pdf = getattr(call, "_cached_pdf", None)
        if not cached_pdf or cached_len != len(call.timeline):
            cached_pdf = ForensicReportGenerator.render_pdf(report_dict)
            call._cached_pdf = cached_pdf
        return Response(
            content=cached_pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="forensic_report_{call_id}.pdf"'}
        )
    
    return report_dict


@router.get("/reports")
async def list_reports(limit: int = Query(50, ge=1, le=100)):
    """List recent forensic reports stored in Supabase."""
    from backend.app.services.supabase_service import SupabaseService
    svc = SupabaseService.get_instance()
    return await svc.get_all_reports(limit=limit)



@router.get("/calls/{call_id}/audit")
async def get_call_audit(call_id: str):
    call_mgr = CallManager.get_instance()
    call = call_mgr.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call session not found")
    return {"call_id": call_id, "chain": call.audit_chain.chain}


@router.get("/calls/{call_id}/audit/verify")
async def verify_call_audit(call_id: str):
    call_mgr = CallManager.get_instance()
    call = call_mgr.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call session not found")
    
    valid, broken_event, expected_hash, actual_hash = AuditChainManager.verify_chain(call.audit_chain.chain)
    return {
        "call_id": call_id,
        "valid": valid,
        "chain_length": len(call.audit_chain.chain),
        "broken_at_event": broken_event,
        "expected_hash": expected_hash,
        "actual_hash": actual_hash,
    }


from pydantic import BaseModel
from typing import Dict, Any, Optional, List

class ForensicExplainRequest(BaseModel):
    metrics: Dict[str, Any]
    stability: Optional[Dict[str, Any]] = None
    segments: Optional[List[Dict[str, Any]]] = None

@router.post("/forensics/explain")
async def explain_multimodal_evidence(req: ForensicExplainRequest):
    """
    Synthesize visual and acoustic forensic metrics together into a legal/judge-defensible
    forensic explanation using Meta-Llama-3.3-70B-Instruct-Turbo via Hugging Face.
    """
    from forensic.explainable_ai import MultimodalForensicExplainer
    return MultimodalForensicExplainer.generate_reasoning_synthesis(
        metrics=req.metrics,
        stability=req.stability,
        segments=req.segments,
    )
