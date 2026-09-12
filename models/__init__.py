"""Database helpers for DevTrack.

SQLite is accessed through a per-request connection stored on Flask's ``g``.
The schema is created idempotently via :func:`init_db`.
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
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    start_date  TEXT,
    deadline    TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
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
    completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id);
"""


def get_db():
    """Return the request-scoped SQLite connection."""
    if "db" not in g:
        db_path = current_app.config["DATABASE"]
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    """Close the request-scoped connection."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create the tables if they do not exist yet."""
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()


def query(sql, params=(), one=False):
    """Run a SELECT and return dict rows (or a single dict when ``one``)."""
    cur = get_db().execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    if one:
        return rows[0] if rows else None
    return rows


def execute(sql, params=()):
    """Run a write statement, commit, and return lastrowid (INSERT) or rowcount (DELETE/UPDATE)."""
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    result = cur.lastrowid if cur.lastrowid else cur.rowcount
    cur.close()
    return result


def execute_affected(sql, params=()):
    """Run a write statement, commit, and return the number of affected rows."""
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    affected = cur.rowcount
    cur.close()
    return affected


def init_app(app):
    """Register the teardown hook on the Flask app."""
    app.teardown_appcontext(close_db)