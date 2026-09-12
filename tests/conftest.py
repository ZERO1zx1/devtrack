"""Shared pytest fixtures for DevTrack.

Each test gets a throwaway SQLite database in a temp directory. The
``DATABASE`` env var is honoured by ``create_app`` and points the factory
at that file before schema init runs.
"""

import os

import pytest

os.environ.setdefault("CONFIG", "testing")

from app import create_app  # noqa: E402


@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / "devtrack-test.db"
    os.environ["DATABASE"] = str(db_path)
    app = create_app("testing")
    yield app
    os.environ.pop("DATABASE", None)


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, username="dev", email="dev@example.com", password="secret123"):
    return client.post(
        "/register",
        data={"username": username, "email": email, "password": password},
        follow_redirects=False,
    )


def login(client, username="dev", password="secret123"):
    return client.post("/login", data={"username": username, "password": password})


@pytest.fixture()
def auth_client(client):
    """A client registered and logged in as ``dev``."""
    register(client)
    login(client)
    return client