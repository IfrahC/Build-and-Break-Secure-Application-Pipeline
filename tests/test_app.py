import os
import tempfile

import pytest


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    import importlib

    os.environ.setdefault("FLASK_SECRET_KEY", "test-secret")
    os.environ.setdefault("ADMIN_PASSWORD", "Admin1234")
    os.environ.setdefault("MEMBER_PASSWORD", "Member1234")
    os.environ.setdefault("VIEWER_PASSWORD", "Viewer1234")
    os.environ.setdefault("RATELIMIT_ENABLED", "0")

    flask_app_module = importlib.import_module("app.app")

    flask_app_module.DATABASE_URL = "sqlite:///" + db_path.replace("\\", "/")
    flask_app_module.app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
        CSRF_ENABLED=False,
        RATELIMIT_ENABLED=False,
    )

    with flask_app_module.app.app_context():
        flask_app_module.init_db()

    yield flask_app_module.app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, identifier="member", password="Member1234"):
    return client.post(
        "/login",
        data={"identifier": identifier, "password": password},
        follow_redirects=True,
    )


def test_public_pages_return_200(client):
    assert client.get("/").status_code == 200
    assert client.get("/login").status_code == 200
    assert client.get("/register").status_code == 200


def test_valid_login_and_logout(client):
    response = login(client)
    assert response.status_code == 200
    assert b"Dashboard" in response.data

    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"logged out" in response.data

    protected = client.get("/dashboard", follow_redirects=False)
    assert protected.status_code == 302
    assert "/login" in protected.headers["Location"]


def test_invalid_login_shows_error(client):
    response = client.post(
        "/login",
        data={"identifier": "member", "password": "wrong-password"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid username/email or password" in response.data


def test_register_validates_and_creates_member(client):
    response = client.post(
        "/register",
        data={
            "username": "newmember",
            "email": "newmember@example.com",
            "password": "Pass12345!",
            "confirm_password": "Pass12345!",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Account created" in response.data

    response = client.post(
        "/login",
        data={"identifier": "newmember", "password": "Pass12345!"},
        follow_redirects=True,
    )
    assert b"Dashboard" in response.data


@pytest.mark.parametrize(
    "password",
    [
        "password1",
        "12345678",
        "aaaaaaaa1",
        "letmein1",
        "Password123",
        "password123!",
        "PASSWORD123!",
        "Password!!!",
    ],
)
def test_register_rejects_weak_passwords(client, password):
    response = client.post(
        "/register",
        data={
            "username": "weakmember",
            "email": "weakmember@example.com",
            "password": password,
            "confirm_password": password,
        },
        follow_redirects=True,
    )
    assert b"at least 10 characters" in response.data


def test_register_rejects_duplicate_user(client):
    response = client.post(
        "/register",
        data={
            "username": "member",
            "email": "other@example.com",
            "password": "Pass12345!",
            "confirm_password": "Pass12345!",
        },
        follow_redirects=True,
    )
    assert b"already registered" in response.data


def test_protected_routes_redirect_when_unauthenticated(client):
    for path in ["/dashboard", "/projects", "/feedback", "/admin"]:
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["Location"] == "/login"
        assert "next=" not in response.headers["Location"]


def test_member_project_crud(client):
    login(client)

    created = client.post(
        "/projects/new",
        data={
            "title": "Threat Model Refresh",
            "description": "Update data flow diagrams and STRIDE assumptions.",
            "status": "Planning",
        },
        follow_redirects=True,
    )
    assert created.status_code == 200
    assert b"Threat Model Refresh" in created.data

    detail = client.get("/projects/3")
    assert detail.status_code == 200

    updated = client.post(
        "/projects/3/edit",
        data={
            "title": "Threat Model Refresh",
            "description": "Update data flow diagrams and STRIDE assumptions.",
            "status": "Active",
        },
        follow_redirects=True,
    )
    assert b"Project updated" in updated.data

    deleted = client.post("/projects/3/delete", follow_redirects=True)
    assert b"Project deleted" in deleted.data


def test_project_search_and_filter(client):
    login(client)
    response = client.get("/projects?q=Campus&status=Planning")
    assert response.status_code == 200
    assert b"Campus Events Board" in response.data


def test_viewer_has_read_only_project_access(client):
    login(client, "viewer", "Viewer1234")

    projects = client.get("/projects")
    assert projects.status_code == 200
    assert b"Security Review Portal" in projects.data

    denied = client.get("/projects/new", follow_redirects=True)
    assert b"do not have permission" in denied.data


def test_member_cannot_view_other_member_project(client):
    login(client)
    response = client.get("/projects/1", follow_redirects=True)
    assert b"Members can only view projects they own" in response.data


def test_admin_can_access_admin_page_and_update_roles(client):
    login(client, "admin", "Admin1234")

    response = client.get("/admin")
    assert response.status_code == 200
    assert b"User and system control" in response.data

    response = client.post(
        "/admin",
        data={"user_id": "3", "role": "member"},
        follow_redirects=True,
    )
    assert b"Role updated" in response.data


def test_admin_cannot_demote_only_admin(client):
    login(client, "admin", "Admin1234")

    response = client.post(
        "/admin",
        data={"user_id": "1", "role": "member"},
        follow_redirects=True,
    )
    assert b"At least one admin account must remain" in response.data

    from app.app import get_db

    db = get_db()
    admin = db.execute("SELECT role FROM users WHERE id = ?", ("1",)).fetchone()
    db.close()
    assert admin["role"] == "admin"


def test_admin_can_demote_admin_when_another_admin_exists(client):
    login(client, "admin", "Admin1234")

    promote_response = client.post(
        "/admin",
        data={"user_id": "3", "role": "admin"},
        follow_redirects=True,
    )
    assert b"Role updated" in promote_response.data

    demote_response = client.post(
        "/admin",
        data={"user_id": "1", "role": "member"},
        follow_redirects=True,
    )
    assert b"Role updated" in demote_response.data

    from app.app import get_db

    db = get_db()
    roles = db.execute(
        "SELECT id, role FROM users WHERE id IN (?, ?) ORDER BY id",
        ("1", "3"),
    ).fetchall()
    db.close()
    assert [user["role"] for user in roles] == ["member", "admin"]


def test_admin_can_review_activity_log(client):
    login(client)
    client.post(
        "/projects/new",
        data={
            "title": "Activity Trail",
            "description": "Confirm meaningful actions are saved to the activity log.",
            "status": "Active",
        },
        follow_redirects=True,
    )
    client.get("/logout", follow_redirects=True)

    login(client, "admin", "Admin1234")
    response = client.get("/admin")

    assert response.status_code == 200
    assert b"project.created" in response.data


def test_feedback_submission(client):
    login(client)
    response = client.post(
        "/feedback",
        data={"category": "Security", "message": "Please review role permissions."},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Feedback submitted" in response.data


def test_task_create_update_delete(client):
    login(client, "admin", "Admin1234")

    response = client.post(
        "/projects/1/tasks",
        data={
            "title": "Run ZAP baseline",
            "assignee_id": "2",
            "status": "Todo",
            "priority": "High",
            "due_date": "2026-05-10",
        },
        follow_redirects=True,
    )
    assert b"Task added" in response.data

    response = client.post(
        "/tasks/3/update",
        data={"status": "Done", "priority": "Medium"},
        follow_redirects=True,
    )
    assert b"Task updated" in response.data

    response = client.post("/tasks/3/delete", follow_redirects=True)
    assert b"Task deleted" in response.data


def test_project_task_assignee_dropdown_does_not_disclose_roles(client):
    login(client, "member", "Member1234")

    response = client.get("/projects/2")

    assert response.status_code == 200
    assert b"admin &#183; admin" not in response.data
    assert b"member &#183; member" not in response.data
    assert b"viewer &#183; viewer" not in response.data
    assert b'<option value="1">admin</option>' in response.data
