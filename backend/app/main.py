
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import select

from .config import get_settings
from .db.models import Scan, ScanResult
from .db.session import SessionLocal, init_db
from .worker.security import normalize_url
from .worker.tasks import run_scan


settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.scans_per_hour}/hour"],
)


class ScanRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


class ScanResponse(BaseModel):
    scan_id: str
    status: str
    result: dict | None = None
    error: str | None = None
    url: str | None = None


# Allows `uvicorn app.main:app --reload` to work before
# Docker/Postgres/Celery are started.
_memory_jobs: dict[str, dict] = {}


async def _run_local(scan_id: str, url: str):
    from .worker.pipeline import run_pipeline

    _memory_jobs[scan_id]["status"] = "running"

    try:
        result = await asyncio.to_thread(run_pipeline, url)

        _memory_jobs[scan_id].update(
            status="done",
            result=result,
            completed_at=datetime.now(timezone.utc),
        )

    except Exception as exc:
        _memory_jobs[scan_id].update(
            status="failed",
            error=str(exc)[:2000],
            completed_at=datetime.now(timezone.utc),
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
    except Exception:
        # API can still start without Postgres during local development.
        pass

    yield


app = FastAPI(
    title="Website Archaeologist",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/v1/models")
def models():
    # Compatibility probe for clients that check an OpenAI-style model list.
    return {
        "object": "list",
        "data": [
            {
                "id": "website-archaeologist",
                "object": "model",
                "owned_by": "local",
            }
        ],
    }


@app.post(
    "/api/v1/scans",
    response_model=ScanResponse,
    status_code=202,
)
@limiter.limit(lambda: f"{settings.scans_per_hour}/hour")
async def create_scan(
    payload: ScanRequest,
    request: Request,
    background_tasks: BackgroundTasks,
):
    try:
        normalized = normalize_url(payload.url)

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    try:
        async with SessionLocal() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(
                hours=settings.cache_ttl_hours
            )

            result = await session.scalar(
                select(ScanResult)
                .join(Scan)
                .where(
                    Scan.normalized_url == normalized,
                    Scan.status == "done",
                    Scan.completed_at >= cutoff,
                )
            )

            scan = Scan(
                url=payload.url.strip(),
                normalized_url=normalized,
                status="queued",
                requested_by_ip=(
                    request.client.host
                    if request.client
                    else None
                ),
            )

            session.add(scan)
            await session.commit()
            await session.refresh(scan)

            # Return cached result when available.
            if result:
                await session.delete(scan)
                await session.commit()

                return {
                    "scan_id": str(result.scan_id),
                    "status": "done",
                    "url": normalized,
                    "result": {
                        "tech_stack": result.tech_stack,
                        "api_routes": result.api_routes,
                        "seo": result.seo,
                        "performance": result.performance,
                    },
                }

        # Production path: Celery worker.
        run_scan.delay(str(scan.id))

        return {
            "scan_id": str(scan.id),
            "status": "queued",
            "url": normalized,
        }

    except Exception as exc:
        # Local development fallback:
        # no Postgres or Redis/Celery required.
        logger = __import__("logging").getLogger(
            "website_archaeologist"
        )

        logger.warning(
            "Database/Celery unavailable; using local worker: %s",
            exc,
        )

        scan_id = str(uuid4())

        _memory_jobs[scan_id] = {
            "scan_id": scan_id,
            "url": payload.url.strip(),
            "status": "queued",
            "result": None,
            "error": None,
        }

        background_tasks.add_task(
            _run_local,
            scan_id,
            normalized,
        )

        return {
            "scan_id": scan_id,
            "status": "queued",
            "url": normalized,
        }


@app.get(
    "/api/v1/scans/{scan_id}",
    response_model=ScanResponse,
)
async def get_scan(scan_id: UUID):
    try:
        async with SessionLocal() as session:
            scan = await session.get(Scan, scan_id)

            if not scan:
                raise HTTPException(
                    status_code=404,
                    detail="Scan not found",
                )

            result = await session.get(
                ScanResult,
                scan_id,
            )

            return {
                "scan_id": str(scan.id),
                "url": scan.url,
                "status": scan.status,
                "error": scan.error,
                "result": (
                    {
                        "tech_stack": result.tech_stack,
                        "api_routes": result.api_routes,
                        "seo": result.seo,
                        "performance": result.performance,
                    }
                    if result
                    else None
                ),
            }

    except HTTPException:
        raise

    except Exception:
        # Local development fallback.
        job = _memory_jobs.get(str(scan_id))

        if not job:
            raise HTTPException(
                status_code=404,
                detail="Scan not found",
            )

        return {
            "scan_id": job["scan_id"],
            "url": job["url"],
            "status": job["status"],
            "error": job["error"],
            "result": job["result"],
        }
