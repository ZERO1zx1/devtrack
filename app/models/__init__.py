"""Data-access layer.

Re-exports the SQLite helpers from :mod:`app.extensions` so that model
modules and services can ``from ..models import query, execute`` without
knowing (or creating) database connections themselves.
"""

from ..extensions import SCHEMA, db

get_db = db.get
query = db.query
execute = db.execute
execute_affected = db.execute_affected
init_db = db.init_schema
init_app = db.init_app

from .base import BaseModel, now_utc, to_dict  # noqa: E402,F401
from . import password_reset, user, task, project  # noqa: E402,F401

__all__ = [
    "SCHEMA",
    "get_db",
    "query",
    "execute",
    "execute_affected",
    "init_db",
    "init_app",
    "BaseModel",
    "now_utc",
    "to_dict",
    "user",
    "task",
    "project",
    "password_reset",
]