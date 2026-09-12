"""Tests for the tasks REST API."""


def _create_task(client, **overrides):
    payload = {"title": "Write API tests", "description": "Cover CRUD", "priority": "high"}
    payload.update(overrides)
    return client.post("/api/tasks", json=payload)


def test_create_task(auth_client):
    resp = _create_task(auth_client)
    assert resp.status_code == 201
    task = resp.get_json()["task"]
    assert task["title"] == "Write API tests"
    assert task["priority"] == "high"
    assert task["status"] == "pending"


def test_list_tasks(auth_client):
    _create_task(auth_client, title="First")
    _create_task(auth_client, title="Second")
    resp = auth_client.get("/api/tasks")
    assert resp.status_code == 200
    titles = [t["title"] for t in resp.get_json()["tasks"]]
    assert titles == ["Second", "First"]


def test_create_task_requires_title(auth_client):
    resp = auth_client.post("/api/tasks", json={"priority": "low"})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Title is required."


def test_create_task_rejects_empty_title(auth_client):
    resp = auth_client.post("/api/tasks", json={"title": "   "})
    assert resp.status_code == 400


def test_create_task_rejects_overlong_title(auth_client):
    resp = _create_task(auth_client, title="x" * 201)
    assert resp.status_code == 400
    assert "200 characters" in resp.get_json()["error"]


def test_create_task_rejects_bad_priority(auth_client):
    resp = _create_task(auth_client, priority="critical")
    assert resp.status_code == 400


def test_create_task_rejects_invalid_project(auth_client):
    resp = _create_task(auth_client, project_id=999)
    assert resp.status_code == 400
    assert "does not exist" in resp.get_json()["error"]


def test_update_task(auth_client):
    task_id = _create_task(auth_client).get_json()["task"]["id"]
    resp = auth_client.put(f"/api/tasks/{task_id}", json={"status": "completed", "title": "Renamed"})
    assert resp.status_code == 200
    task = resp.get_json()["task"]
    assert task["status"] == "completed"
    assert task["title"] == "Renamed"
    assert task["completed_at"] is not None


def test_delete_task(auth_client):
    task_id = _create_task(auth_client).get_json()["task"]["id"]
    resp = auth_client.delete(f"/api/tasks/{task_id}")
    assert resp.status_code == 204
    assert auth_client.get("/api/tasks").get_json()["tasks"] == []


def test_missing_task_returns_404(auth_client):
    assert auth_client.put("/api/tasks/424242", json={"title": "x"}).status_code == 404
    assert auth_client.delete("/api/tasks/424242").status_code == 404


def test_malformed_json_returns_400(auth_client):
    resp = auth_client.post("/api/tasks", data="not json", content_type="application/json")
    assert resp.status_code == 400


def test_api_requires_auth(client):
    assert client.get("/api/tasks").status_code == 401
    assert client.post("/api/tasks", json={"title": "x"}).status_code == 401
    assert client.post("/api/analytics").status_code == 405 or client.get("/api/analytics").status_code == 401


def test_filtering_by_status(auth_client):
    task_a = _create_task(auth_client, title="Active task")
    _create_task(auth_client, title="Done task")
    auth_client.put(f"/api/tasks/{task_a.get_json()['task']['id']}", json={"status": "completed"})

    completed = auth_client.get("/api/tasks?status=completed").get_json()["tasks"]
    assert [t["title"] for t in completed] == ["Active task"]


def test_filtering_by_priority_and_search(auth_client):
    _create_task(auth_client, title="Deploy backend", priority="high")
    _create_task(auth_client, title="Drink water", priority="low")

    high = auth_client.get("/api/tasks?priority=high").get_json()["tasks"]
    assert len(high) == 1 and high[0]["title"] == "Deploy backend"

    found = auth_client.get('/api/tasks?q=water').get_json()["tasks"]
    assert len(found) == 1 and found[0]["title"] == "Drink water"


def test_users_never_see_each_others_tasks(app):
    c1 = app.test_client()
    c1.post("/register", data={"username": "alice", "email": "a@example.com", "password": "secret123"})
    c1.post("/login", data={"username": "alice", "password": "secret123"})
    task_id = _create_task(c1).get_json()["task"]["id"]

    c2 = app.test_client()
    c2.post("/register", data={"username": "bob", "email": "b@example.com", "password": "secret123"})
    c2.post("/login", data={"username": "bob", "password": "secret123"})

    assert c2.get("/api/tasks").get_json()["tasks"] == []
    assert c2.put(f"/api/tasks/{task_id}", json={"title": "hacked"}).status_code == 404
    assert c2.delete(f"/api/tasks/{task_id}").status_code == 404


def test_analytics_returns_streaks(auth_client):
    task_id = _create_task(auth_client).get_json()["task"]["id"]
    auth_client.put(f"/api/tasks/{task_id}", json={"status": "completed"})

    data = auth_client.get("/api/analytics").get_json()
    assert data["total"] == 1
    assert data["completed"] == 1
    assert data["current_streak"] >= 1
    assert data["longest_streak"] >= 1
    assert "activity" in data
    assert len(data["weekly"]) == 7