"""
Shared fixtures for the end-to-end API tests (run via tests/run.sh).

The API talks to a real Postgres through PostgREST. Supabase Storage and the
Telegram Bot API are replaced by in-memory fakes.
"""
import base64
import hashlib
import hmac
import json
import os
import subprocess
import time
import urllib.parse
from types import SimpleNamespace

import pytest

BOT_TOKEN = "123456:TEST"
OWNER, WIFE, ALI, VALI = 1000, 3000, 2001, 2002


def _jwt(secret: str) -> str:
    enc = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()  # noqa: E731
    head, body = enc({"alg": "HS256", "typ": "JWT"}), enc({"role": "service_role", "exp": 4102444800})
    sig = hmac.new(secret.encode(), f"{head}.{body}".encode(), hashlib.sha256).digest()
    return f"{head}.{body}.{base64.urlsafe_b64encode(sig).rstrip(b'=').decode()}"


os.environ.update(
    BOT_TOKEN=BOT_TOKEN,
    ADMIN_GROUP_ID="-100500",
    ADMIN_NOTIFY_IDS="-100500,1000",
    SUPER_ADMIN_IDS=str(OWNER),
    SUPABASE_URL="http://localhost:54331",
    SUPABASE_KEY=_jwt(os.environ.get("TEST_JWT_SECRET", "x" * 40)),
    MINI_APP_URL="https://app.test",
    ALLOWED_ORIGINS="https://app.test",
    MINI_APP_LINK="https://t.me/TestBot/shop",
    DEV_MODE="false",
    EXPIRY_CHECK_INTERVAL="3600",
)


def init_data(user_id: int, first_name: str = "User", lang: str = "uz", age: int = 0) -> str:
    fields = {
        "auth_date": str(int(time.time()) - age),
        "user": json.dumps({"id": user_id, "first_name": first_name, "language_code": lang}),
    }
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(key, dcs.encode(), hashlib.sha256).hexdigest()
    return urllib.parse.urlencode(fields)


def sql(query: str) -> str:
    """Run SQL directly in the test database (for things only time would do)."""
    out = subprocess.run(
        ["docker", "exec", os.environ.get("TEST_DB_CONTAINER", "msrt-pg"),
         "psql", "-U", "postgres", "-tAc", query],
        check=True, capture_output=True, text=True,
    )
    return out.stdout.strip()


class FakeBucket:
    def __init__(self, store: dict, name: str):
        self.store, self.name = store, name

    async def upload(self, path, data, opts=None):
        self.store[f"{self.name}/{path}"] = (data, opts)
        return {"path": path}

    async def remove(self, paths):
        for p in paths:
            self.store.pop(f"{self.name}/{p}", None)
        return []

    async def create_signed_url(self, path, expires_in, options=None):
        return {"signedURL": f"https://signed.test/{self.name}/{path}?ttl={expires_in}"}


@pytest.fixture(scope="session")
def fakes():
    import api.notify
    import api.storage

    files: dict = {}
    sent: list = []
    storage = SimpleNamespace(from_=lambda name: FakeBucket(files, name))
    api.storage.db = lambda: SimpleNamespace(storage=storage)

    async def fake_send(chat_id, text, button=None):
        sent.append({"chat_id": int(chat_id), "text": text, "button": button})
        return True

    api.notify.send_message = fake_send
    return SimpleNamespace(files=files, sent=sent)


@pytest.fixture(scope="session")
def client(fakes):
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app) as c:
        yield c


class As:
    """Requests as a given Telegram user."""

    def __init__(self, client, user_id: int, name: str = "User", lang: str = "uz"):
        self.c, self.h = client, {"X-Telegram-Init-Data": init_data(user_id, name, lang)}

    def __getattr__(self, method):
        return lambda url, **kw: getattr(self.c, method)(url, headers={**self.h, **kw.pop("headers", {})}, **kw)


@pytest.fixture(scope="session")
def owner(client):
    return As(client, OWNER, "Makhmud")


@pytest.fixture(scope="session")
def wife(client):
    return As(client, WIFE, "Admin")


@pytest.fixture(scope="session")
def ali(client):
    return As(client, ALI, "Ali")


@pytest.fixture(scope="session")
def vali(client):
    return As(client, VALI, "Вали", "ru")
