"""Project data-access functions.

Progress is computed on the fly as the ratio of completed tasks
attached to the project, so it never goes stale.
"""

from ..extensions import db
from ..models.base import now_utc

TASK_COUNT_SQL = """
    SELECT
        p.*,
        (SELECT COUNT(*) FROM tasks t WHERE t.project_id = p.id) AS all_tasks,
        (SELECT COUNT(*) FROM tasks t WHERE t.project_id = p.id
             AND t.status = 'completed') AS done_tasks
    FROM projects p
"""


def create_project(user_id, name, description="", start_date=None, deadline=None):
    pid = db.execute(
        """
        INSERT INTO projects (user_id, name, description, start_date, deadline)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, name, description, start_date, deadline),
    )
    return get_project(pid, user_id)


def list_projects(user_id):
    rows = db.query(
        f"{TASK_COUNT_SQL} WHERE p.user_id = ? ORDER BY p.created_at DESC", (user_id,)
    )
    return [_decorate(r) for r in rows]


def get_project(project_id, user_id):
    row = db.query(
        f"{TASK_COUNT_SQL} WHERE p.id = ? AND p.user_id = ?",
        (project_id, user_id),
        one=True,
    )
    return _decorate(row) if row else None


def update_project(project_id, user_id, fields):
    allowed = {"name", "description", "start_date", "deadline", "updated_at"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    updates["updated_at"] = now_utc()

    labels = ", ".join(f"{k} = ?" for k in updates)
    params = list(updates.values()) + [project_id, user_id]
    db.execute(f"UPDATE projects SET {labels} WHERE id = ? AND user_id = ?", params)
    return get_project(project_id, user_id)


def delete_project(project_id, user_id):
    return db.execute_affected(
        "DELETE FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id)
    )


def _decorate(row):
    data = dict(row)
    total = data.pop("all_tasks") or 0
    done = data.pop("done_tasks") or 0
    data["tasks_count"] = total
    data["progress"] = round((done / total) * 100) if total else 0
    return data