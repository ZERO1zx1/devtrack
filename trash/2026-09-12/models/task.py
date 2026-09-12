"""Task data-access functions.

Everything is scoped by ``user_id`` so users can only see their own rows.
"""

from datetime import date, datetime, timedelta

from models import execute, execute_affected, query


def create_task(user_id, title, description="", priority="medium", project_id=None):
    task_id = execute(
        """
        INSERT INTO tasks (user_id, project_id, title, description, priority)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, project_id, title, description, priority),
    )
    return get_task(task_id, user_id)


def list_tasks(user_id, status=None, priority=None, q=None):
    sql = """
        SELECT t.*, p.name AS project_name
        FROM tasks t
        LEFT JOIN projects p ON p.id = t.project_id
        WHERE t.user_id = ?
    """
    params = [user_id]
    if status in ("pending", "completed"):
        sql += " AND t.status = ?"
        params.append(status)
    if priority in ("low", "medium", "high"):
        sql += " AND t.priority = ?"
        params.append(priority)
    if q:
        sql += " AND (t.title LIKE ? OR t.description LIKE ?)"
        like = f"%{q}%"
        params += [like, like]
    sql += " ORDER BY t.created_at DESC, t.id DESC"
    return query(sql, params)


def get_task(task_id, user_id):
    return query(
        """
        SELECT t.*, p.name AS project_name
        FROM tasks t
        LEFT JOIN projects p ON p.id = t.project_id
        WHERE t.id = ? AND t.user_id = ?
        """,
        (task_id, user_id),
        one=True,
    )


def update_task(task_id, user_id, fields):
    """Update a task using an allow-listed set of field/value pairs."""
    allowed = {
        "title",
        "description",
        "status",
        "priority",
        "project_id",
        "completed_at",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_task(task_id, user_id)

    labels = []
    params = []
    if "status" in updates:
        updates["completed_at"] = (
            datetime.now().isoformat(sep=" ", timespec="seconds")
            if updates["status"] == "completed"
            else None
        )
    for key, value in updates.items():
        labels.append(f"{key} = ?")
        params.append(value)
    params += [task_id, user_id]
    execute(f"UPDATE tasks SET {', '.join(labels)} WHERE id = ? AND user_id = ?", params)
    return get_task(task_id, user_id)


def delete_task(task_id, user_id):
    return execute_affected(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)
    )


def stats(user_id):
    """Aggregate counters used by the dashboard."""
    counts = query(
        """
        SELECT
            COUNT(*)                                        AS total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed
        FROM tasks WHERE user_id = ?
        """,
        (user_id,),
        one=True,
    )
    total = counts["total"] or 0
    completed = counts["completed"] or 0
    completion_pct = round((completed / total) * 100) if total else 0
    projects = query(
        "SELECT COUNT(*) AS n FROM projects WHERE user_id = ?", (user_id,), one=True
    )["n"]
    return {
        "total": total,
        "completed": completed,
        "completion_pct": completion_pct,
        "projects": projects,
    }


def completed_dates(user_id):
    """Return the date part of every completion timestamp, most recent first."""
    rows = query(
        "SELECT completed_at FROM tasks "
        "WHERE user_id = ? AND status = 'completed' AND completed_at IS NOT NULL "
        "ORDER BY completed_at DESC",
        (user_id,),
    )
    return [r["completed_at"][:10] for r in rows]


def weekly_counts(user_id):
    """Tasks completed per day for the current Monday-to-Sunday week."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    dates = [monday + timedelta(days=i) for i in range(7)]
    keys = [d.isoformat() for d in dates]

    rows = query(
        """
        SELECT date(completed_at) AS day, COUNT(*) AS n
        FROM tasks
        WHERE user_id = ? AND status = 'completed' AND completed_at IS NOT NULL
          AND date(completed_at) BETWEEN ? AND ?
        GROUP BY date(completed_at)
        """,
        (user_id, keys[0], keys[-1]),
    )
    lookup = {r["day"]: r["n"] for r in rows}
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return [
        {"label": labels[i], "count": lookup.get(keys[i], 0), "date": keys[i]}
        for i in range(7)
    ]