"""
Bulk Offline Media Verification and Batch Forensics Router.
Processes offline video/audio assets and benchmarks against datasets.
"""
import os
import uuid
import time
import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, Query, Depends, Response
from fastapi.responses import HTMLResponse
import cv2
import numpy as np

from backend.app.schemas.contracts import BulkVerificationJob, EvidenceBundle
from backend.app.services.gpu_worker import ForensicGPUWorker
from forensic.media_dna import MediaDNAEngine
from forensic.provenance import ProvenanceInspector
from reports.generator import ForensicReportGenerator
from backend.auth.dependencies import require_permission
from backend.auth.permissions import Permission

router = APIRouter()
jobs: Dict[str, BulkVerificationJob] = {}


def process_video_file(file_path: str, filename: str) -> Dict[str, Any]:
    worker = ForensicGPUWorker.get_instance()
    dna_engine = MediaDNAEngine()
    
    # Read file bytes for SHA-256 and Provenance
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    file_sha = dna_engine.compute_sha256(file_bytes)
    provenance = ProvenanceInspector.inspect(file_bytes)

    # 1. Run Master Temporal Video Transformer to produce EvidenceBundle with timeline segments
    bundle = worker.temporal_fusion.analyze_video_storage(file_path)
    mean_visual = bundle.overall_fake_score
    duration_sec = (bundle.total_frames / bundle.fps) if bundle.fps > 0 else 0.0

    # 2. Run Evidence Stability Test on sample frame
    cap = cv2.VideoCapture(file_path)
    stability_data = None
    if cap.isOpened():
        ret, frame = cap.read()
        cap.release()
        if ret and frame is not None:
            tracks = worker.face_detector.track_and_crop(frame)
            if tracks:
                crop = tracks[0][1]
                stab_res = worker.stability_engine.evaluate_stability(crop, mean_visual)
                stability_data = stab_res.model_dump()

    # 3. Multimodal Evidence Fusion
    raw_risk, cal_risk, classification, uncertainty = worker.fusion_engine.fuse(
        visual_score=mean_visual,
        stability_score=stability_data.get("stability_score", 1.0) if stability_data else 1.0,
    )

    return {
        "filename": filename,
        "sha256": file_sha,
        "duration_seconds": round(duration_sec, 2),
        "frames_sampled": len(bundle.frame_data),
        "visual_score": round(mean_visual, 4),
        "calibrated_risk_score": cal_risk,
        "classification": classification,
        "uncertainty": uncertainty,
        "stability": stability_data,
        "provenance": provenance.model_dump(),
        "status": "COMPLETED",
        "overall_label": bundle.overall_label,
        "overall_fake_score": bundle.overall_fake_score,
        "segments": [s.model_dump() for s in bundle.segments],
        "frame_data": [f.model_dump() for f in bundle.frame_data],
        "evidence_bundle": bundle.model_dump(),
    }


def background_bulk_process(job_id: str, file_paths: List[tuple[str, str]]):
    job = jobs.get(job_id)
    if not job:
        return

    job.status = "processing"
    for file_path, fname in file_paths:
        try:
            res = process_video_file(file_path, fname)
            job.results.append(res)
        except Exception as e:
            job.results.append({"filename": fname, "status": "ERROR", "error": str(e)})
        finally:
            job.processed_files += 1

    job.status = "completed"


@router.post("/bulk", response_model=BulkVerificationJob)
async def create_bulk_verification(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(default=[]),
    dataset_folder: Optional[str] = Form(None),
    user: Dict[str, Any] = Depends(require_permission(Permission.BULK_UPLOAD_VIDEOS)),
):
    """
    Launch bulk verification for either uploaded files or an internal dataset folder.
    Protected by RBAC: Forensic Officer or Admin only.
    """
    job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
    file_list = []

    os.makedirs("./temp_uploads", exist_ok=True)

    if files:
        for f in files:
            safe_name = os.path.basename(f.filename) if f.filename else f"video_{uuid.uuid4().hex[:6]}.mp4"
            dest = f"./temp_uploads/{uuid.uuid4().hex[:8]}_{safe_name}"
            content = await f.read()
            with open(dest, "wb") as out:
                out.write(content)
            file_list.append((dest, f.filename or safe_name))

    elif dataset_folder:
        # Benchmark folder (e.g., from archive/FaceForensics++_C23/original or Deepfakes)
        if os.path.exists(dataset_folder):
            for fname in os.listdir(dataset_folder)[:10]:  # batch up to 10 for quick responsive analysis
                if fname.lower().endswith((".mp4", ".avi", ".mov")):
                    full_p = os.path.join(dataset_folder, fname)
                    file_list.append((full_p, fname))

    if not file_list:
        raise HTTPException(status_code=400, detail="No valid media files or dataset path provided")

    job = BulkVerificationJob(
        job_id=job_id,
        created_at=time.time(),
        status="pending",
        total_files=len(file_list),
        processed_files=0,
        results=[],
    )
    jobs[job_id] = job

    asyncio.create_task(asyncio.to_thread(background_bulk_process, job_id, file_list))
    return job


@router.get("/verify/{job_id}", response_model=BulkVerificationJob)
async def get_bulk_job(
    job_id: str,
    user: Dict[str, Any] = Depends(require_permission(Permission.BULK_VIEW_RESULTS)),
):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Bulk verification job not found")
    return job


@router.post("/verify")
async def verify_single_file(
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(require_permission(Permission.BULK_UPLOAD_VIDEOS)),
):
    """Synchronous single file forensic verification."""
    os.makedirs("./temp_uploads", exist_ok=True)
    temp_path = f"./temp_uploads/{uuid.uuid4().hex[:8]}_{file.filename}"
    content = await file.read()
    with open(temp_path, "wb") as out:
        out.write(content)

    try:
        result = process_video_file(temp_path, file.filename)
        return result
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/verify/bundle", response_model=EvidenceBundle)
async def verify_video_bundle(file: UploadFile = File(...)):
    """
    Dedicated endpoint returning structured EvidenceBundle with timeline segments.
    """
    os.makedirs("./temp_uploads", exist_ok=True)
    temp_path = f"./temp_uploads/{uuid.uuid4().hex[:8]}_{file.filename}"
    content = await file.read()
    with open(temp_path, "wb") as out:
        out.write(content)

    try:
        worker = ForensicGPUWorker.get_instance()
        bundle = worker.temporal_fusion.analyze_video_storage(temp_path)
        return bundle
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


_batch_reports_cache: Dict[str, Dict[str, Any]] = {}
_batch_pdf_cache: Dict[str, bytes] = {}
_batch_html_cache: Dict[str, str] = {}


async def _async_sync_bulk_job(j_id: str, r_data: dict, h_content: str, j_status: str, t_files: int, p_files: int, res: list):
    """Background task to sync bulk job dossier to Supabase without delaying user download."""
    try:
        from backend.app.services.supabase_service import SupabaseService
        svc = SupabaseService.get_instance()
        if svc.client:
            storage_url = await asyncio.to_thread(svc.upload_batch_report_html, j_id, h_content)
            await asyncio.to_thread(svc.upload_batch_report_json, j_id, r_data)
            await svc.persist_bulk_job(
                job_id=j_id,
                status=j_status,
                total_files=t_files,
                processed_files=p_files,
                results=res,
                storage_url=storage_url
            )
            r_data["storage_url"] = storage_url
    except Exception:
        pass


@router.get("/bulk/{job_id}/report")
async def get_bulk_report(job_id: str, format: str = Query("json", pattern="^(json|html|pdf)$")):
    """
    Generate a comprehensive forensic batch report from a completed bulk verification job.
    Supports JSON (structured data), HTML (self-contained printable dossier), and PDF (court-admissible document) formats.
    """
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Bulk verification job not found")
    if job.status != "completed":
        raise HTTPException(status_code=400, detail=f"Job not yet completed (status: {job.status})")

    report = _batch_reports_cache.get(job_id)
    if not report:
        report = ForensicReportGenerator.create_batch_report(
            job_id=job_id,
            results=job.results,
        )
        _batch_reports_cache[job_id] = report

    html_content = _batch_html_cache.get(job_id)
    if not html_content:
        html_content = ForensicReportGenerator.render_batch_html(report)
        _batch_html_cache[job_id] = html_content

    # Fire background task for cloud sync without blocking response
    asyncio.create_task(
        _async_sync_bulk_job(
            job_id,
            report,
            html_content,
            job.status,
            job.total_files,
            job.processed_files,
            job.results,
        )
    )

    if format == "html":
        return HTMLResponse(content=html_content)
    elif format == "pdf":
        pdf_bytes = _batch_pdf_cache.get(job_id)
        if not pdf_bytes:
            pdf_bytes = ForensicReportGenerator.render_batch_pdf(report)
            _batch_pdf_cache[job_id] = pdf_bytes
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="bulk_forensic_report_{job_id}.pdf"'}
        )

    return report

