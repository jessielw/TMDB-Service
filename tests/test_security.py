import asyncio
import importlib
import logging
import sys
from types import ModuleType, SimpleNamespace

import httpx2
import pytest
from fastapi import HTTPException

from tmdb_service.config import api_key_is_secure
from tmdb_service.error_utils import webhook_failure_message


def load_api(
    monkeypatch,
    *,
    api_key="test-api-key",
    docs_enabled=False,
    rate_limit="60/minute",
):
    fake_globals = ModuleType("tmdb_service.globals")
    fake_globals.global_config = SimpleNamespace(  # type: ignore[reportAttributeAccessIssue]
        API_DOCS_ENABLED=docs_enabled,
        API_KEY=api_key,
        API_RATE_LIMIT=rate_limit,
        DATABASE_URI="postgresql://unused",
    )
    fake_globals.tmdb_logger = logging.getLogger("tmdb.security-tests")  # type: ignore[reportAttributeAccessIssue]
    monkeypatch.setitem(sys.modules, "tmdb_service.globals", fake_globals)
    sys.modules.pop("tmdb_service.job_queue", None)
    sys.modules.pop("tmdb_service.api", None)
    return importlib.import_module("tmdb_service.api")


def load_api_server(monkeypatch, *, api_key, trusted_proxies=""):
    fake_globals = ModuleType("tmdb_service.globals")
    fake_globals.global_config = SimpleNamespace(  # type: ignore[reportAttributeAccessIssue]
        API_ENABLED=True,
        API_FORWARDED_ALLOW_IPS=trusted_proxies,
        API_KEY=api_key,
        API_PORT=8000,
    )
    fake_globals.tmdb_logger = logging.getLogger("tmdb.security-tests")  # type: ignore[reportAttributeAccessIssue]
    monkeypatch.setitem(sys.modules, "tmdb_service.globals", fake_globals)
    sys.modules.pop("tmdb_service.api_server", None)
    return importlib.import_module("tmdb_service.api_server")


def test_api_key_configuration_rejects_blank_and_public_placeholder():
    assert not api_key_is_secure(None)
    assert not api_key_is_secure("")
    assert not api_key_is_secure("your-secret-api-key-here")
    assert api_key_is_secure("unique-secret")


def test_api_server_refuses_to_start_without_a_secure_key(monkeypatch):
    api_server = load_api_server(monkeypatch, api_key=None)
    with pytest.raises(SystemExit) as error:
        api_server.main()
    assert error.value.code == 1


def test_api_server_passes_explicit_proxy_trust_to_uvicorn(monkeypatch):
    api_server = load_api_server(
        monkeypatch, api_key="unique-secret", trusted_proxies="192.0.2.10"
    )
    called = {}
    monkeypatch.setattr(
        api_server.uvicorn,
        "run",
        lambda *args, **kwargs: called.update(args=args, kwargs=kwargs),
    )
    api_server.main()
    assert called["kwargs"]["proxy_headers"] is True
    assert called["kwargs"]["forwarded_allow_ips"] == "192.0.2.10"


@pytest.mark.anyio
async def test_health_is_public_while_root_and_docs_are_disabled(monkeypatch):
    api = load_api(monkeypatch)
    transport = httpx2.ASGITransport(app=api.app)
    async with httpx2.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        assert (await client.get("/health")).status_code == 200
        assert (await client.get("/")).status_code == 404
        assert (await client.get("/docs")).status_code == 404
        assert (await client.get("/redoc")).status_code == 404
        assert (await client.get("/openapi.json")).status_code == 404


@pytest.mark.anyio
async def test_docs_are_explicitly_enabled(monkeypatch):
    api = load_api(monkeypatch, docs_enabled=True)
    transport = httpx2.ASGITransport(app=api.app)
    async with httpx2.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        assert (await client.get("/docs")).status_code == 200
        assert (await client.get("/redoc")).status_code == 200
        assert (await client.get("/openapi.json")).status_code == 200


@pytest.mark.anyio
async def test_auth_fails_closed_without_a_secure_configured_key(monkeypatch):
    api = load_api(monkeypatch, api_key=None)  # type: ignore[reportAttributeAccessIssue]
    transport = httpx2.ASGITransport(app=api.app)
    async with httpx2.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post("/jobs/changes-sync")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}


def test_invalid_non_ascii_key_is_rejected_without_logging_it(monkeypatch, caplog):
    api = load_api(monkeypatch)
    with caplog.at_level(logging.WARNING, logger="tmdb.security-tests"):
        with pytest.raises(HTTPException) as error:
            asyncio.run(api.verify_api_key("canary-é"))
    assert error.value.status_code == 401
    assert "canary" not in caplog.text


@pytest.mark.anyio
async def test_enqueue_failure_returns_generic_error_and_logs_detail(
    monkeypatch, caplog
):
    api = load_api(monkeypatch)

    def fail_enqueue(*_args, **_kwargs):
        raise RuntimeError("private-database-detail")

    monkeypatch.setattr(api, "enqueue_job", fail_enqueue)
    with caplog.at_level(logging.ERROR, logger="tmdb.security-tests"):
        transport = httpx2.ASGITransport(app=api.app)
        async with httpx2.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.post(
                "/jobs/changes-sync", headers={"X-API-Key": "test-api-key"}
            )
    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to enqueue job"}
    assert "private-database-detail" not in response.text
    assert "private-database-detail" in caplog.text


@pytest.mark.anyio
async def test_rate_limit_applies_to_operational_routes_but_not_health(monkeypatch):
    api = load_api(monkeypatch, rate_limit="2/minute")
    monkeypatch.setattr(api, "enqueue_job", lambda *_args, **_kwargs: 1)
    headers = {"X-API-Key": "test-api-key"}
    transport = httpx2.ASGITransport(app=api.app)
    async with httpx2.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        assert (
            await client.post("/jobs/changes-sync", headers=headers)
        ).status_code == 200
        assert (
            await client.post("/jobs/changes-sync", headers=headers)
        ).status_code == 200
        assert (
            await client.post("/jobs/changes-sync", headers=headers)
        ).status_code == 429
        for _ in range(5):
            assert (await client.get("/health")).status_code == 200


def test_webhook_failure_message_never_contains_exception_text():
    message = webhook_failure_message(
        "changes sync", RuntimeError("private-database-detail")
    )
    assert "RuntimeError" in message
    assert "private-database-detail" not in message
    assert "traceback" not in message.lower()
