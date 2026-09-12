# Trash — Архивлагдсан хуучин файлууд

Энэ хавтас нь **устгагдаагүй**, зөвхөн архивлагдсан хуучин файлуудыг хадгална.
Refactor хийх үед буцааж харах, харьцуулах зорилгоор үлдээсэн.

## Огноо: 2026-09-12 — v1 → app-factory бүтэц шилжилт

- `app.py`, `models/`, `routes/` — v1-ийн Flask бүтэц
- `templates/`, `static/` — v1-ийн HTML/CSS/JS
- `test_auth.py`, `test_tasks.py`, `test_projects.py` — v1-ийн тестүүд
- `devtrack.db.old` — v1-ийн SQLite schema (`updated_at` баганагүй)

Шинэ бүтэц: `app/` (Application Factory + services layer), `tests/unit` + `tests/integration`.