# Website Archaeologist Backend

FastAPI service that scans a public HTTP(S) website and returns technology fingerprints, API routes discovered in HTML/JavaScript, SEO metadata, and basic performance measurements.

## Run locally

```bash
uv sync
uv run uvicorn backend.main:app --reload
```

The service runs at `http://127.0.0.1:8000`; interactive API documentation is available at `/docs`.

## API

Create a scan:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/scans \
  -H 'content-type: application/json' \
  -d '{"url":"https://example.com"}'
```

Poll `GET /api/v1/scans/{scan_id}` every 1–2 seconds until `status` is `done` or `failed`.

## Safety and limits

Every initial request, redirect, and fetched same-origin bundle is resolved before connecting. HTTP(S) only, public IP addresses only, five redirects maximum, bounded response bodies and bundles, an honest crawler user agent, and a default in-process limit of ten scans per IP per hour are enforced. The current job store and cache are process-local and are intended as a deployable single-process baseline; production deployments should replace them with the Postgres/Redis/Celery stores described in the project specification.
