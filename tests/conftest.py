"""Shared pytest fixtures for DevTrack."""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402


@pytest.fixture()
def app():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": db_path,
            "SECRET_KEY": "test-secret-key",
        }
    )
    yield app
    app.config["DATABASE"]
    os.close(db_fd)
    if os.path.exists(db_path):
        os.remove(db_path)


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