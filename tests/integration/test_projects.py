"""Integration tests for projects page and its REST API."""


def _create_project(client, name="DevTrack", **overrides):
    payload = {"name": name, "description": "Track progress", "start_date": "2026-01-01"}
    payload.update(overrides)
    return client.post("/api/projects", json=payload)


def test_projects_page_requires_login(client):
    resp = client.get("/projects")
    assert resp.status_code == 302


def test_logged_in_user_reaches_projects_page(auth_client):
    resp = auth_client.get("/projects")
    assert resp.status_code == 200
    assert b"Projects" in resp.data


def test_create_project(auth_client):
    resp = _create_project(auth_client)
    assert resp.status_code == 201
    project = resp.get_json()["project"]
    assert project["name"] == "DevTrack"
    assert project["start_date"] == "2026-01-01"
    assert project["progress"] == 0
    assert project["tasks_count"] == 0


def test_create_project_requires_name(auth_client):
    resp = auth_client.post("/api/projects", json={"description": "no name"})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Project name is required."


def test_create_project_rejects_invalid_dates(auth_client):
    resp = _create_project(auth_client, deadline=123)
    assert resp.status_code == 400


def test_project_progress_from_tasks(auth_client):
    project_id = _create_project(auth_client).get_json()["project"]["id"]

    t1 = auth_client.post("/api/tasks", json={"title": "Write tests", "project_id": project_id}).get_json()["task"]["id"]
    t2 = auth_client.post("/api/tasks", json={"title": "Another task", "project_id": project_id}).get_json()["task"]["id"]

    projects = auth_client.get("/api/projects").get_json()["projects"]
    assert projects[0]["tasks_count"] == 2
    assert projects[0]["progress"] == 0

    auth_client.put(f"/api/tasks/{t1}", json={"status": "completed"})
    auth_client.put(f"/api/tasks/{t2}", json={"status": "completed"})
    projects = auth_client.get("/api/projects").get_json()["projects"]
    assert projects[0]["progress"] == 100


def test_update_project(auth_client):
    project_id = _create_project(auth_client).get_json()["project"]["id"]
    resp = auth_client.put(f"/api/projects/{project_id}", json={"name": "Renamed", "deadline": "2026-12-31"})
    assert resp.status_code == 200
    project = resp.get_json()["project"]
    assert project["name"] == "Renamed"
    assert project["deadline"] == "2026-12-31"


def test_delete_project(auth_client):
    project_id = _create_project(auth_client).get_json()["project"]["id"]
    assert auth_client.delete(f"/api/projects/{project_id}").status_code == 204
    assert auth_client.get("/api/projects").get_json()["projects"] == []


def test_deleting_project_unassigns_tasks(auth_client):
    project_id = _create_project(auth_client).get_json()["project"]["id"]
    task = auth_client.post(
        "/api/tasks", json={"title": "Orphan me", "project_id": project_id}
    ).get_json()["task"]
    auth_client.delete(f"/api/projects/{project_id}")

    tasks = auth_client.get("/api/tasks").get_json()["tasks"]
    orphaned = next(t for t in tasks if t["id"] == task["id"])
    assert orphaned["project_id"] is None


def test_users_cannot_touch_foreign_projects(app):
    c1 = app.test_client()
    c1.post("/register", data={"username": "alice", "email": "a@example.com", "password": "secret123"})
    c1.post("/login", data={"username": "alice", "password": "secret123"})
    pid = _create_project(c1).get_json()["project"]["id"]

    c2 = app.test_client()
    c2.post("/register", data={"username": "bob", "email": "b@example.com", "password": "secret123"})
    c2.post("/login", data={"username": "bob", "password": "secret123"})

    assert c2.get("/api/projects").get_json()["projects"] == []
    assert c2.put(f"/api/projects/{pid}", json={"name": "theirs"}).status_code == 404
    assert c2.delete(f"/api/projects/{pid}").status_code == 404