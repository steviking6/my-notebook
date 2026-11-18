import pytest

from app.core.config import get_settings


@pytest.fixture
def api_key(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_api_key", "secret")


def test_no_key_configured_means_open_api(client):
    assert client.get("/documents").status_code == 200


def test_wrong_or_missing_key_is_rejected(client, api_key):
    assert client.get("/documents").status_code == 401
    assert client.get("/documents", headers={"X-API-Key": "wrong"}).status_code == 401


def test_right_key_is_accepted(client, api_key):
    assert client.get("/documents", headers={"X-API-Key": "secret"}).status_code == 200


def test_health_stays_public(client, api_key):
    assert client.get("/health").status_code == 200
