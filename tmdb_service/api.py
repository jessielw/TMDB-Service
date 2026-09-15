import secrets

from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIASGIMiddleware
from slowapi.util import get_remote_address

from tmdb_service.config import api_key_is_secure
from tmdb_service.globals import global_config, tmdb_logger
from tmdb_service.job_queue import enqueue_job

docs_url = "/docs" if global_config.API_DOCS_ENABLED else None
redoc_url = "/redoc" if global_config.API_DOCS_ENABLED else None
openapi_url = "/openapi.json" if global_config.API_DOCS_ENABLED else None
app = FastAPI(
    title="TMDB Service API",
    description="API for managing TMDB cache service jobs",
    version="1.0.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
)

rate_limit_disabled = global_config.API_RATE_LIMIT.lower() in {
    "",
    "false",
    "off",
    "disable",
    "disabled",
    "no",
}
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[] if rate_limit_disabled else [global_config.API_RATE_LIMIT],
    enabled=not rate_limit_disabled,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[reportArgumentType]
app.add_middleware(SlowAPIASGIMiddleware)

# API Key security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verify the caller's API key and fail closed if configuration is unsafe."""
    configured = global_config.API_KEY
    if not configured or not api_key_is_secure(configured):
        tmdb_logger.error("Rejecting request: API_KEY is missing or insecure.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )

    if api_key is None or not secrets.compare_digest(
        api_key.encode("utf-8"), configured.encode("utf-8")
    ):
        tmdb_logger.warning("Rejected a request with a missing or invalid API key.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key


class JobResponse(BaseModel):
    status: str = Field(..., description="Job status")
    job_type: str = Field(..., description="Type of job enqueued")
    message: str = Field(..., description="Additional information")


class AddMediaRequest(BaseModel):
    tmdb_id: int = Field(..., description="TMDB ID of the movie or series", gt=0)


class FullSweepRequest(BaseModel):
    force: bool = Field(
        default=False, description="Force full sweep regardless of row counts"
    )


class TestWebhookRequest(BaseModel):
    message: str = Field(
        default="Test webhook message from TMDB Service API",
        description="Custom message to send via webhook",
    )


@app.get("/health", tags=["General"])
@limiter.exempt
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post(
    "/jobs/full-sweep",
    response_model=JobResponse,
    tags=["Jobs"],
    summary="Trigger a full TMDB sweep",
)
async def trigger_full_sweep(
    request: FullSweepRequest = FullSweepRequest(),
    _api_key: str = Depends(verify_api_key),
):
    """
    Enqueue a full sweep job to refresh all TMDB data.

    - **force**: If true, forces a full sweep regardless of existing data
    """
    try:
        enqueue_job("full_sweep", request.force)
        return JobResponse(
            status="queued",
            job_type="full_sweep",
            message=f"Full sweep job enqueued (force={request.force})",
        )
    except Exception as e:
        tmdb_logger.error(f"Error enqueueing full_sweep job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to enqueue job")


@app.post(
    "/jobs/missing-ids",
    response_model=JobResponse,
    tags=["Jobs"],
    summary="Sync missing TMDB IDs",
)
async def trigger_missing_ids(_api_key: str = Depends(verify_api_key)):
    """
    Enqueue a job to sync missing TMDB IDs from the latest dataset.
    """
    try:
        enqueue_job("missing_ids")
        return JobResponse(
            status="queued",
            job_type="missing_ids",
            message="Missing IDs sync job enqueued",
        )
    except Exception as e:
        tmdb_logger.error(f"Error enqueueing missing_ids job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to enqueue job")


@app.post(
    "/jobs/prune-deleted",
    response_model=JobResponse,
    tags=["Jobs"],
    summary="Prune deleted records",
)
async def trigger_prune_deleted(_api_key: str = Depends(verify_api_key)):
    """
    Enqueue a job to remove records that no longer exist in TMDB.
    """
    try:
        enqueue_job("prune_deleted")
        return JobResponse(
            status="queued",
            job_type="prune_deleted",
            message="Prune deleted records job enqueued",
        )
    except Exception as e:
        tmdb_logger.error(f"Error enqueueing prune_deleted job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to enqueue job")


@app.post(
    "/jobs/changes-sync",
    response_model=JobResponse,
    tags=["Jobs"],
    summary="Sync recent changes from TMDB",
)
async def trigger_changes_sync(_api_key: str = Depends(verify_api_key)):
    """
    Enqueue a job to sync recent changes from TMDB API.
    """
    try:
        enqueue_job("changes_sync")
        return JobResponse(
            status="queued",
            job_type="changes_sync",
            message="Changes sync job enqueued",
        )
    except Exception as e:
        tmdb_logger.error(f"Error enqueueing changes_sync job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to enqueue job")


@app.post(
    "/movies/{tmdb_id}",
    response_model=JobResponse,
    tags=["Media"],
    summary="Add or update a movie",
)
async def add_movie(tmdb_id: int, _api_key: str = Depends(verify_api_key)):
    """
    Enqueue a job to add or update a specific movie by TMDB ID.

    - **tmdb_id**: The TMDB movie ID
    """
    if tmdb_id <= 0:
        raise HTTPException(status_code=400, detail="TMDB ID must be greater than 0")

    try:
        enqueue_job("add_movie", str(tmdb_id))
        return JobResponse(
            status="queued",
            job_type="add_movie",
            message=f"Movie {tmdb_id} add/update job enqueued",
        )
    except Exception as e:
        tmdb_logger.error(f"Error enqueueing add_movie job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to enqueue job")


@app.post(
    "/series/{tmdb_id}",
    response_model=JobResponse,
    tags=["Media"],
    summary="Add or update a TV series",
)
async def add_series(tmdb_id: int, _api_key: str = Depends(verify_api_key)):
    """
    Enqueue a job to add or update a specific TV series by TMDB ID.

    - **tmdb_id**: The TMDB series ID
    """
    if tmdb_id <= 0:
        raise HTTPException(status_code=400, detail="TMDB ID must be greater than 0")

    try:
        enqueue_job("add_series", str(tmdb_id))
        return JobResponse(
            status="queued",
            job_type="add_series",
            message=f"Series {tmdb_id} add/update job enqueued",
        )
    except Exception as e:
        tmdb_logger.error(f"Error enqueueing add_series job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to enqueue job")


@app.post(
    "/jobs/test-webhook",
    response_model=JobResponse,
    tags=["Jobs"],
    summary="Test webhook notification",
)
async def trigger_test_webhook(
    request: TestWebhookRequest = TestWebhookRequest(),
    _api_key: str = Depends(verify_api_key),
):
    """
    Enqueue a job to test webhook notifications.

    - **message**: Custom message to send (optional)
    """
    try:
        enqueue_job("test_webhook", request.message)
        return JobResponse(
            status="queued",
            job_type="test_webhook",
            message=f"Webhook test job enqueued with message: {request.message}",
        )
    except Exception as e:
        tmdb_logger.error(f"Error enqueueing test_webhook job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to enqueue job")
