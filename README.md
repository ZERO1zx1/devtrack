# &#128640; DevTrack — Developer Task & Progress Tracker

A full-stack developer productivity app that turns everyday coding into a visible
GitHub-style contribution graph, measured streaks, and shipping progress.

Built step by step in the **DevTrack 30-day full-stack challenge** — every layer
was written by hand: `HTML → CSS → JavaScript → Python → Flask → SQLite → REST API
→ Authentication → Projects → Analytics → Tests`.

## &#128081; Features

- **Task Manager** — create, edit, complete/uncomplete and delete tasks with
  client-side validation and instant UI feedback.
- **Search & Filters** — search titles/descriptions, filter by status
  (All / Active / Completed) and by priority (Low / Medium / High).
- **Project Tracker** — group tasks under projects with descriptions, start dates,
  deadlines, and an auto-computed progress percentage.
- **Contribution Calendar** — a GitHub-style 53-week grid where each cell's
  intensity reflects tasks completed that day; hover shows
  `September 12 — 5 tasks completed`.
- **Streaks** — current and longest streak computed from days with real activity.
- **Productivity Analytics** — a dependency-free canvas bar chart of the current
  week plus completion-rate stats.
- **User Accounts** — register / login / logout with scrypt-hashed passwords and
  server sessions; every user only ever sees their own data.
- **Platform Roles** — database-backed owner, co-owner, admin, moderator and
  member permissions with fail-closed HTML/API route guards.
- **Theme System** — dark / light / system modes persisted in `localStorage`.
- **Polish** — toast notifications, modals, loading spinners, empty states,
  custom 404 and 500 pages, and responsive layouts at 768px and 480px.

## &#128737; Technologies

| Layer        | Tech                              |
|--------------|-----------------------------------|
| Frontend     | HTML5 (semantic), CSS3 (variables, Flexbox, Grid), vanilla JavaScript |
| Backend      | Python 3, Flask                  |
| Database     | SQLite (via Python `sqlite3`)    |
| Testing      | pytest                           |
| VCS          | Git / GitHub                     |

## &#128295; Installation

```bash
# 1. Clone or create the project directory
git clone https://github.com/YOUR_USERNAME/devtrack.git
cd devtrack

# 2. Create a virtual environment (Windows)
python -m venv .venv
.\.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional but recommended) set a real secret key
#    set SECRET_KEY=your-long-random-value   (Windows PowerShell)

# 5. Run
python app.py
```

Open <http://127.0.0.1:5000>, register an account, and start tracking.

To bootstrap the platform owner safely, set `BOOTSTRAP_OWNER_EMAIL` before that
account registers. Registrations use the `member` role by default; developer
seniority is separate and never grants administrative access.

The SQLite database is created automatically at `instance/devtrack.db`
(ignored by Git).

## &#128214; Folder structure

```text
devtrack/
├── app.py                 # App factory, dashboard route, error handlers
├── requirements.txt
├── README.md
├── .gitignore
├── instance/
│   └── devtrack.db        # SQLite database (auto-created, git-ignored)
│
├── templates/             # Jinja2 templates
│   ├── base.html          # Dashboard shell (sidebar, topbar)
│   ├── index.html         # Landing page
│   ├── dashboard.html     # Stats, calendar, tasks, charts
│   ├── projects.html      # Project manager
│   ├── login.html
│   ├── register.html
│   ├── 404.html
│   └── 500.html
│
├── static/
│   ├── css/
│   │   └── style.css      # Full theme + responsive system
│   └── js/
│       ├── app.js         # Theme, toasts, modals, API client
│       ├── tasks.js       # Task manager UI
│       ├── projects.js    # Project manager UI
│       ├── contributions.js  # Activity calendar
│       └── charts.js      # Canvas analytics chart
│
├── models/                # Data-access layer
│   ├── __init__.py        # sqlite connection helpers + schema
│   ├── user.py
│   ├── task.py
│   └── project.py
│
├── routes/                # Flask blueprints
│   ├── __init__.py        # login guards + blueprint registry
│   ├── auth.py            # register / login / logout
│   ├── tasks.py           # tasks API + analytics
│   └── projects.py        # projects page + API
│
└── tests/                 # pytest suite
    ├── conftest.py
    ├── test_auth.py
    ├── test_tasks.py
    └── test_projects.py
```

## &#127918; Run the tests

```bash
python -m pytest tests -q
```

The suite uses a temporary SQLite database per run and covers registration
validation, hashed passwords, login/logout, session guards, the full task CRUD
cycle, filtering, user data isolation, project progress math, and API error
handling.

## &#128209; REST API documentation

All task/project endpoints require login (401 otherwise).
Payloads are JSON. `project_id` may be `null`.

### Tasks

| Method   | Endpoint              | Description                          |
|----------|-----------------------|--------------------------------------|
| `GET`    | `/api/tasks`          | List tasks (query: `status`, `priority`, `q`) |
| `POST`   | `/api/tasks`          | Create a task                        |
| `PUT`    | `/api/tasks/<id>`     | Partial update (title, description, status, priority, project_id) |
| `DELETE` | `/api/tasks/<id>`     | Delete a task                        |

**Create example:**

```bash
curl -X POST http://127.0.0.1:5000/api/tasks \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"title":"Ship DevTrack","description":"Push the release","priority":"high"}'
```

Validation rules:

- `title` — required, 1–200 characters (empty/whitespace rejected).
- `description` — optional, max 1000 characters.
- `priority` — one of `low`, `medium`, `high` (defaults to `medium`).
- `status` — one of `pending`, `completed`.
- `project_id` — integer or null; must belong to the current user.

### Projects

| Method   | Endpoint                 | Description            |
|----------|--------------------------|------------------------|
| `GET`    | `/api/projects`          | List projects with `tasks_count` and computed `progress` |
| `POST`   | `/api/projects`          | Create a project       |
| `PUT`    | `/api/projects/<id>`     | Update name/description/start_date/deadline |
| `DELETE` | `/api/projects/<id>`     | Delete (tasks become unassigned) |

Project `progress` = completed tasks ÷ total tasks × 100.

### Analytics

| Method | Endpoint          | Description                                        |
|--------|-------------------|----------------------------------------------------|
| `GET`  | `/api/analytics`  | Counts, per-day `activity` map, `weekly` series, `current_streak`, `longest_streak` |

### Error responses

```json
{ "error": "Title is required." }
```

- `400` — invalid payload (missing title, bad priority, unknown project, etc.)
- `401` — not authenticated on an API route
- `404` — unknown task/project id
- `500` — unexpected server error

## &#128218; Build history (the 30-day challenge, condensed)

The repository is intentionally committed milestone by milestone so the history
reads like a real learning path:

```text
chore: initialize DevTrack project
feat: build landing page structure
style: add responsive dark and light theme
feat: create developer dashboard layout       + localStorage task manager
feat: setup Flask backend and templates
feat: add SQLite database models
feat: implement tasks REST API
feat: implement user authentication
feat: add project management
feat: build contribution calendar + streaks
feat: add productivity analytics charts
feat: implement theme switcher
style: improve dashboard user experience
fix: strengthen server-side validation
test: add backend API and auth tests
docs: complete project documentation
```

Each step was a shippable unit, not a blank contribution-graph fill.

## &#128640; Roadmap

- [ ] CSRF protection and rate limiting
- [ ] Task due dates with "overdue" highlighting
- [ ] Drag-and-drop task ordering / Kanban board
- [ ] Export analytics as image / CSV
- [ ] Deployment (Gunicorn + managed SQLite/PostgreSQL)
- [ ] Dark-mode calendar legend tooltips on touch devices

## &#128109; License

MIT — use it, learn from it, break it, rebuild it better.
