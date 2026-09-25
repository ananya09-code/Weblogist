import asyncio
from celery import Celery
from ..config import get_settings
from .pipeline import run_pipeline

celery_app = Celery("website_archaeologist", broker=get_settings(
).redis_url, backend=get_settings().redis_url)


@celery_app.task(bind=True, soft_time_limit=120, time_limit=150)
def run_scan(self, scan_id: str):
    from ..db.session import SessionLocal
    from ..db.models import Scan, ScanResult
    from sqlalchemy import select
    from datetime import datetime, timezone

    async def execute():
        async with SessionLocal() as session:
            scan = await session.get(Scan, scan_id)
            if not scan:
                return
            scan.status = "running"
            scan.started_at = datetime.now(timezone.utc)
            await session.commit()
            try:
                result = await asyncio.to_thread(run_pipeline, scan.url)
                scan_result = ScanResult(scan_id=scan_id, **result)
                session.add(scan_result)
                scan.status = "done"
                scan.completed_at = datetime.now(timezone.utc)
                await session.commit()
            except Exception as exc:
                scan.status = "failed"
                scan.error = str(exc)[:2000]
                scan.completed_at = datetime.now(timezone.utc)
                await session.commit()
                raise
    asyncio.run(execute())
