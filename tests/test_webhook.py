import importlib
import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import RedirectResponse


def _build_request(body: bytes, headers: dict[str, str] | None = None) -> Request:
    headers = headers or {}
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/webhook/transactions",
        "headers": [
            (key.lower().encode("latin-1"), value.encode("latin-1"))
            for key, value in headers.items()
        ],
    }

    async def receive() -> dict[str, bytes | bool]:
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(scope, receive)


@pytest.fixture
def webhook_server(monkeypatch):
    """Готовит модуль backend.server с подменёнными зависимостями для теста."""

    monkeypatch.setenv("MONGO_URL", "mongodb://localhost:27017")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("WEBHOOK_REDIRECT_URL", "https://example.com/webhook")

    if "motor" not in sys.modules:
        motor_package = ModuleType("motor")
        sys.modules["motor"] = motor_package
    else:
        motor_package = sys.modules["motor"]

    motor_asyncio_module = ModuleType("motor.motor_asyncio")

    class DummyAsyncIOMotorClient:
        def __init__(self, *args, **kwargs):
            pass

        def __getitem__(self, name):
            return MagicMock()

    motor_asyncio_module.AsyncIOMotorClient = DummyAsyncIOMotorClient
    motor_package.motor_asyncio = motor_asyncio_module
    sys.modules["motor.motor_asyncio"] = motor_asyncio_module

    if "backend.server" in sys.modules:
        del sys.modules["backend.server"]

    server = importlib.import_module("backend.server")

    server.is_webhook_verified = AsyncMock(return_value=True)
    server.mark_webhook_verified = AsyncMock()

    server.webhook_state_collection = MagicMock()
    server.webhook_state_collection.find_one = AsyncMock(return_value={"verified": True})
    server.webhook_state_collection.update_one = AsyncMock()

    server.webhook_events_collection = MagicMock()
    server.webhook_events_collection.update_one = AsyncMock()

    return server


@pytest.mark.anyio("asyncio")

async def test_empty_body_triggers_verification_redirect(webhook_server):
    request = _build_request(b"")

    response = await webhook_server.receive_transaction_webhook(request)

    assert isinstance(response, RedirectResponse)
    assert response.status_code == 307
    assert response.headers["location"] == webhook_server.WEBHOOK_REDIRECT_URL
    assert webhook_server.mark_webhook_verified.await_count == 1


@pytest.mark.anyio("asyncio")

async def test_empty_json_body_triggers_verification_redirect(webhook_server):
    request = _build_request(b"{}", headers={"Content-Type": "application/json"})

    response = await webhook_server.receive_transaction_webhook(request)

    assert isinstance(response, RedirectResponse)
    assert response.status_code == 307
    assert response.headers["location"] == webhook_server.WEBHOOK_REDIRECT_URL
    assert webhook_server.mark_webhook_verified.await_count == 1


@pytest.fixture
def anyio_backend():
    """Ограничивает запуск anyio только циклом asyncio."""

    return "asyncio"

