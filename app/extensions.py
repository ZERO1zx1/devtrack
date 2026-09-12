"""Shared extension objects.

Centralising these here avoids circular imports: many modules can import
``db`` / ``login_manager`` from this one place while the factory wires them
up with ``init_app``.
"""

import os
import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT
);

CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    start_date  TEXT,
    deadline    TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id   INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    title        TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    status       TEXT NOT NULL DEFAULT 'pending',
    priority     TEXT NOT NULL DEFAULT 'medium',
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    updated_at   TEXT
);

CREATE TABLE IF NOT EXISTS password_resets (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_password_resets_user ON password_resets(user_id);
CREATE INDEX IF NOT EXISTS idx_password_resets_token ON password_resets(token_hash);
"""


class Database:
    """Thin request-scoped SQLite handler.

    Connections live per-request on Flask's ``g`` and are torn down
    automatically after each request.
    """

    def init_app(self, app):
        app.teardown_appcontext(self.close)

    def connect(self):
        db_path = current_app.config["DATABASE"]
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def get(self):
        if "db" not in g:
            g.db = self.connect()
        return g.db

    def close(self, _exc=None):
        connection = g.pop("db", None)
        if connection is not None:
            connection.close()

    def init_schema(self):
        connection = self.get()
        connection.executescript(SCHEMA)
        connection.commit()

    def query(self, sql, params=(), one=False):
        cur = self.get().execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        if one:
            return rows[0] if rows else None
        return rows

    def execute(self, sql, params=()):
        conn = self.get()
        cur = conn.execute(sql, params)
        conn.commit()
        result = cur.lastrowid if cur.lastrowid else cur.rowcount
        cur.close()
        return result

    def execute_affected(self, sql, params=()):
        conn = self.get()
        cur = conn.execute(sql, params)
        conn.commit()
        affected = cur.rowcount
        cur.close()
        return affected


db = Database()


class LoginManager:
    """Lightweight, dependency-free login manager.

    Guards rely on the session directly; this object injects the
    ``current_user`` helper into every template context.
    """

    def init_app(self, app):
        @app.context_processor
        def _inject_current_user():
            from flask import session

            from .models.user import get_user_by_id

            user_id = session.get("user_id")
            return {"current_user": get_user_by_id(user_id) if user_id else None}


login_manager = LoginManager()

# CSRF guard is available whenever Flask-WTF is installed. Install it with
# ``pip install flask-wtf`` — the app still runs (with CSRF disabled) without it.
try:
    from flask_wtf import CSRFProtect

    csrf = CSRFProtect()
    CSRF_ENABLED = True
except ImportError:  # pragma: no cover — optional dependency
    csrf = None
    CSRF_ENABLED = False


def init_csrf(app):
    """Attach CSRF protection only when Flask-WTF is present."""
    if csrf is not None:
        csrf.init_app(app)