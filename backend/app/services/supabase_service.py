"""
Supabase Integration Service for Media Integrity / SecureCall.
Provides persistent cloud storage for forensic dossiers, structured reports,
and bulk verification jobs using Supabase Storage and PostgreSQL.
"""
import json
import time
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from sqlalchemy import select, update
from backend.app.config import settings
from backend.app.database import async_session_factory
from backend.app.models.models import ForensicReportRecord, BulkJobRecord
from backend.app.logging_config import get_logger

logger = get_logger("supabase_service")


class SupabaseService:
    _instance: Optional["SupabaseService"] = None

    def __init__(self):
        self.client: Optional[Client] = None
        self.bucket_name: str = settings.SUPABASE_STORAGE_BUCKET or "forensic-reports"
        self._init_client()

    def _init_client(self):
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                self.client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_ROLE_KEY
                )
                logger.info(
                    "Supabase client initialized successfully",
                    url=settings.SUPABASE_URL,
                    bucket=self.bucket_name,
                )
            except Exception as e:
                logger.error("Failed to initialize Supabase client", error=str(e))
                self.client = None
        else:
            logger.warning("Supabase credentials not configured in settings")

    @classmethod
    def get_instance(cls) -> "SupabaseService":
        if cls._instance is None:
            cls._instance = SupabaseService()
        return cls._instance

    # -------------------------------------------------------------------------
    # Supabase Storage Methods
    # -------------------------------------------------------------------------
    def upload_file_bytes(
        self,
        storage_path: str,
        file_bytes: bytes,
        content_type: str = "text/html",
    ) -> Optional[str]:
        """
        Upload binary/text content to Supabase Storage and return its public URL.
        """
        if not self.client:
            logger.warning("Supabase client not active; skipping upload", path=storage_path)
            return None

        try:
            self.client.storage.from_(self.bucket_name).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": content_type, "upsert": "true"}
            )
            public_url = self.client.storage.from_(self.bucket_name).get_public_url(storage_path)
            logger.info("Uploaded artifact to Supabase Storage", path=storage_path, url=public_url)
            return public_url
        except Exception as e:
            logger.error("Failed to upload artifact to Supabase Storage", path=storage_path, error=str(e))
            return None

    def upload_report_html(self, report_id: str, html_content: str) -> Optional[str]:
        """Upload a rendered HTML forensic report dossier to Supabase Storage."""
        path = f"call_reports/{report_id}.html"
        return self.upload_file_bytes(path, html_content.encode("utf-8"), content_type="text/html")

    def upload_report_json(self, report_id: str, report_dict: Dict[str, Any]) -> Optional[str]:
        """Upload a machine-readable JSON forensic dossier to Supabase Storage."""
        path = f"call_reports/{report_id}.json"
        data = json.dumps(report_dict, indent=2).encode("utf-8")
        return self.upload_file_bytes(path, data, content_type="application/json")

    def upload_batch_report_html(self, job_id: str, html_content: str) -> Optional[str]:
        """Upload a batch forensic HTML dossier to Supabase Storage."""
        path = f"batch_reports/{job_id}.html"
        return self.upload_file_bytes(path, html_content.encode("utf-8"), content_type="text/html")

    def upload_batch_report_json(self, job_id: str, report_dict: Dict[str, Any]) -> Optional[str]:
        """Upload a batch forensic JSON dossier to Supabase Storage."""
        path = f"batch_reports/{job_id}.json"
        data = json.dumps(report_dict, indent=2).encode("utf-8")
        return self.upload_file_bytes(path, data, content_type="application/json")

    # -------------------------------------------------------------------------
    # PostgreSQL Persistence Methods
    # -------------------------------------------------------------------------
    async def persist_forensic_report(
        self,
        report_dict: Dict[str, Any],
        html_content: Optional[str] = None,
        storage_url: Optional[str] = None,
    ) -> Optional[ForensicReportRecord]:
        """
        Persist a forensic report to the Supabase PostgreSQL database.
        """
        report_id = report_dict.get("report_id") or report_dict.get("id")
        call_id = report_dict.get("call_id", "unknown-call")
        media_sha256 = report_dict.get("media_sha256")
        final_assessment = report_dict.get("final_assessment", "UNKNOWN")
        calibrated_risk = float(report_dict.get("calibrated_risk", 0.0))

        async with async_session_factory() as session:
            try:
                # Check if report already exists
                stmt = select(ForensicReportRecord).where(ForensicReportRecord.id == report_id)
                res = await session.execute(stmt)
                existing = res.scalar_one_or_none()

                if existing:
                    existing.final_assessment = final_assessment
                    existing.calibrated_risk = calibrated_risk
                    existing.report_json = report_dict
                    if html_content:
                        existing.html_content = html_content
                    if storage_url:
                        existing.storage_url = storage_url
                    record = existing
                else:
                    record = ForensicReportRecord(
                        id=report_id,
                        call_id=call_id,
                        media_sha256=media_sha256,
                        final_assessment=final_assessment,
                        calibrated_risk=calibrated_risk,
                        report_json=report_dict,
                        html_content=html_content,
                        storage_url=storage_url,
                        created_at=time.time(),
                    )
                    session.add(record)

                await session.commit()
                await session.refresh(record)
                logger.info("Persisted forensic report to Supabase DB", report_id=report_id)
                return record
            except Exception as e:
                await session.rollback()
                logger.error("Failed to persist report to Supabase DB", report_id=report_id, error=str(e))
                return None

    async def persist_bulk_job(
        self,
        job_id: str,
        status: str,
        total_files: int,
        processed_files: int,
        results: List[Dict[str, Any]],
        storage_url: Optional[str] = None,
    ) -> Optional[BulkJobRecord]:
        """
        Persist or update a bulk verification job in the Supabase PostgreSQL database.
        """
        async with async_session_factory() as session:
            try:
                stmt = select(BulkJobRecord).where(BulkJobRecord.job_id == job_id)
                res = await session.execute(stmt)
                existing = res.scalar_one_or_none()

                completed_at = time.time() if status in ("completed", "failed") else None

                if existing:
                    existing.status = status
                    existing.total_files = total_files
                    existing.processed_files = processed_files
                    existing.results = results
                    if storage_url:
                        existing.storage_url = storage_url
                    if completed_at:
                        existing.completed_at = completed_at
                    record = existing
                else:
                    record = BulkJobRecord(
                        job_id=job_id,
                        status=status,
                        total_files=total_files,
                        processed_files=processed_files,
                        results=results,
                        storage_url=storage_url,
                        created_at=time.time(),
                        completed_at=completed_at,
                    )
                    session.add(record)

                await session.commit()
                await session.refresh(record)
                logger.info("Persisted bulk job to Supabase DB", job_id=job_id, status=status)
                return record
            except Exception as e:
                await session.rollback()
                logger.error("Failed to persist bulk job to Supabase DB", job_id=job_id, error=str(e))
                return None

    async def get_all_reports(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch latest forensic reports from Supabase DB."""
        async with async_session_factory() as session:
            try:
                stmt = select(ForensicReportRecord).order_by(ForensicReportRecord.created_at.desc()).limit(limit)
                res = await session.execute(stmt)
                records = res.scalars().all()
                return [
                    {
                        "id": r.id,
                        "call_id": r.call_id,
                        "media_sha256": r.media_sha256,
                        "final_assessment": r.final_assessment,
                        "calibrated_risk": r.calibrated_risk,
                        "storage_url": r.storage_url,
                        "created_at": r.created_at,
                    }
                    for r in records
                ]
            except Exception as e:
                logger.error("Failed to fetch reports from Supabase DB", error=str(e))
                return []
