"""Shared JSON response helpers — a single envelope for every endpoint."""

from flask import jsonify


def json_ok(**data):
    """Return ``{"ok": true, **data}``."""
    return jsonify({"ok": True, **data})


def json_error(message, errors=None, status=400):
    """Return ``{"ok": false, "error": message, "errors": [...]}``."""
    payload = {"ok": False, "error": message}
    if errors:
        payload["errors"] = errors
    return jsonify(payload), status


def json_payload(data, status=200):
    """Return a bare named-key JSON payload (e.g. ``{"tasks": [...]}``)."""
    return jsonify(data), status