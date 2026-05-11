"""
NexusPortal

A role-based internal project management application for the Build & Break
DevSecOps assignment. The app is intentionally small enough to demo live, but it
contains real server-side authentication, authorization, validation, CRUD,
search/filtering, and persistence for security testing.
"""

import os
import re
import secrets
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = os.path.dirname(__file__)
DATABASE = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "database", "app.db"))
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

ROLES = ("admin", "member", "viewer")
PROJECT_STATUSES = ("Planning", "Active", "Blocked", "Completed")
TASK_STATUSES = ("Todo", "In Progress", "Done")
TASK_PRIORITIES = ("Low", "Medium", "High")
FEEDBACK_CATEGORIES = ("Bug", "Security", "Feature", "General")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create schema and seed demo users/data if missing."""
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    schema_path = os.path.join(BASE_DIR, "database", "init.sql")

    db = get_db()
    with open(schema_path, encoding="utf-8") as schema_file:
        db.executescript(schema_file.read())

    seed_users(db)
    seed_projects(db)
    db.commit()
    db.close()


def seed_users(db):
    users = [
        ("admin", "admin@nexus.local", "Admin1234", "admin"),
        ("member", "member@nexus.local", "Member1234", "member"),
        ("viewer", "viewer@nexus.local", "Viewer1234", "viewer"),
    ]
    for username, email, password, role in users:
        exists = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if not exists:
            db.execute(
                """
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
                """,
                (username, email, generate_password_hash(password), role),
            )


def seed_projects(db):
    project_count = db.execute("SELECT COUNT(*) AS total FROM projects").fetchone()["total"]
    if project_count:
        return

    admin = db.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone()
    member = db.execute("SELECT id FROM users WHERE username = ?", ("member",)).fetchone()
    viewer = db.execute("SELECT id FROM users WHERE username = ?", ("viewer",)).fetchone()

    projects = [
        (
            "Security Review Portal",
            "Track application security review tasks and remediation status.",
            "Active",
            admin["id"],
        ),
        (
            "Campus Events Board",
            "Coordinate student events, ownership, and release milestones.",
            "Planning",
            member["id"],
        ),
    ]
    for title, description, status, owner_id in projects:
        db.execute(
            """
            INSERT INTO projects (title, description, status, owner_id)
            VALUES (?, ?, ?, ?)
            """,
            (title, description, status, owner_id),
        )

    db.execute(
        """
        INSERT INTO tasks (project_id, title, assignee_id, status, priority, due_date)
        VALUES (1, ?, ?, ?, ?, ?)
        """,
        ("Document STRIDE threats", member["id"], "In Progress", "High", "2026-05-03"),
    )
    db.execute(
        """
        INSERT INTO tasks (project_id, title, assignee_id, status, priority, due_date)
        VALUES (1, ?, ?, ?, ?, ?)
        """,
        ("Review executive summary", viewer["id"], "Todo", "Medium", "2026-05-08"),
    )


@app.before_request
def load_current_user():
    g.user = None
    user_id = session.get("user_id")
    if not user_id:
        return

    db = get_db()
    g.user = db.execute(
        "SELECT id, username, email, role, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    db.close()
    if g.user is None:
        session.clear()


@app.context_processor
def inject_globals():
    return {
        "current_user": g.get("user"),
        "csrf_token": csrf_token,
        "roles": ROLES,
        "project_statuses": PROJECT_STATUSES,
        "task_statuses": TASK_STATUSES,
        "task_priorities": TASK_PRIORITIES,
        "feedback_categories": FEEDBACK_CATEGORIES,
    }


def csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


@app.before_request
def validate_csrf_token():
    if not app.config.get("CSRF_ENABLED", True):
        return
    if request.method != "POST":
        return

    sent_token = request.form.get("csrf_token", "")
    expected_token = session.get("csrf_token", "")
    if not sent_token or not expected_token or not secrets.compare_digest(sent_token, expected_token):
        abort(400)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            flash("Please log in first.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


def roles_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if g.user is None:
                flash("Please log in first.", "warning")
                return redirect(url_for("login", next=request.path))
            if g.user["role"] not in allowed_roles:
                flash("You do not have permission to access that page.", "danger")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)

        return wrapped_view

    return decorator


def can_manage_project(project):
    return g.user and (g.user["role"] == "admin" or project["owner_id"] == g.user["id"])


def can_edit_content():
    return g.user and g.user["role"] in ("admin", "member")


def is_valid_email(email):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email or ""))


def validate_project_form(form):
    errors = []
    title = form.get("title", "").strip()
    description = form.get("description", "").strip()
    status = form.get("status", "").strip()

    if not 3 <= len(title) <= 80:
        errors.append("Project title must be 3 to 80 characters.")
    if not 10 <= len(description) <= 500:
        errors.append("Description must be 10 to 500 characters.")
    if status not in PROJECT_STATUSES:
        errors.append("Choose a valid project status.")

    return errors, title, description, status


def get_project_or_404(project_id):
    db = get_db()
    project = db.execute(
        """
        SELECT p.*, u.username AS owner_name
        FROM projects p
        JOIN users u ON u.id = p.owner_id
        WHERE p.id = ?
        """,
        (project_id,),
    ).fetchone()
    db.close()
    if project is None:
        abort(404)
    return project


@app.route("/")
def index():
    if g.user:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if not re.fullmatch(r"[a-z0-9_.-]{3,30}", username):
            errors.append("Username must be 3 to 30 characters and use letters, numbers, dot, dash, or underscore.")
        if not is_valid_email(email):
            errors.append("Enter a valid email address.")
        if len(password) < 8 or not re.search(r"\d", password):
            errors.append("Password must be at least 8 characters and include a number.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        db = get_db()
        duplicate = db.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email),
        ).fetchone()
        if duplicate:
            errors.append("That username or email is already registered.")

        if errors:
            db.close()
            for error in errors:
                flash(error, "danger")
            return render_template("register.html", username=username, email=email)

        db.execute(
            """
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, 'member')
            """,
            (username, email, generate_password_hash(password)),
        )
        db.commit()
        db.close()
        flash("Account created. You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            """
            SELECT id, username, email, password_hash, role
            FROM users
            WHERE username = ? OR email = ?
            """,
            (identifier, identifier),
        ).fetchone()
        db.close()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["username"] = user["username"]
            session["csrf_token"] = secrets.token_urlsafe(32)
            session.permanent = False
            flash(f"Welcome back, {user['username']}.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid username/email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    if g.user["role"] == "admin":
        projects = db.execute("SELECT COUNT(*) AS total FROM projects").fetchone()["total"]
        users = db.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
        tasks_open = db.execute(
            "SELECT COUNT(*) AS total FROM tasks WHERE status != 'Done'"
        ).fetchone()["total"]
        feedback_open = db.execute(
            "SELECT COUNT(*) AS total FROM feedback WHERE status = 'Open'"
        ).fetchone()["total"]
        recent_projects = db.execute(
            """
            SELECT p.*, u.username AS owner_name
            FROM projects p
            JOIN users u ON u.id = p.owner_id
            ORDER BY p.updated_at DESC
            LIMIT 5
            """
        ).fetchall()
    else:
        projects = db.execute(
            "SELECT COUNT(*) AS total FROM projects WHERE owner_id = ?",
            (g.user["id"],),
        ).fetchone()["total"]
        users = None
        tasks_open = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM tasks
            WHERE assignee_id = ? AND status != 'Done'
            """,
            (g.user["id"],),
        ).fetchone()["total"]
        feedback_open = None
        recent_projects = db.execute(
            """
            SELECT p.*, u.username AS owner_name
            FROM projects p
            JOIN users u ON u.id = p.owner_id
            WHERE p.owner_id = ? OR ? = 'viewer'
            ORDER BY p.updated_at DESC
            LIMIT 5
            """,
            (g.user["id"], g.user["role"]),
        ).fetchall()

    db.close()
    metrics = {
        "projects": projects,
        "users": users,
        "open_tasks": tasks_open,
        "open_feedback": feedback_open,
    }
    return render_template("dashboard.html", metrics=metrics, recent_projects=recent_projects)


@app.route("/projects")
@login_required
def projects():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()

    status_filter = status if status in PROJECT_STATUSES else ""
    like_query = f"%{q}%"
    params = [
        q,
        like_query,
        like_query,
        status_filter,
        status_filter,
        g.user["role"],
        g.user["id"],
    ]
    db = get_db()
    rows = db.execute(
        """
        SELECT p.*, u.username AS owner_name,
               COUNT(t.id) AS task_count,
               SUM(CASE WHEN t.status = 'Done' THEN 1 ELSE 0 END) AS done_count
        FROM projects p
        JOIN users u ON u.id = p.owner_id
        LEFT JOIN tasks t ON t.project_id = p.id
        WHERE (? = '' OR p.title LIKE ? OR p.description LIKE ?)
          AND (? = '' OR p.status = ?)
          AND (? != 'member' OR p.owner_id = ?)
        GROUP BY p.id
        ORDER BY p.updated_at DESC
        """,
        tuple(params),
    ).fetchall()
    db.close()
    return render_template("projects.html", projects=rows, q=q, selected_status=status)


@app.route("/projects/new", methods=["GET", "POST"])
@roles_required("admin", "member")
def new_project():
    if request.method == "POST":
        errors, title, description, status = validate_project_form(request.form)
        if errors:
            for error in errors:
                flash(error, "danger")
            form_project = {"title": title, "description": description, "status": status}
            return render_template("project_form.html", project=form_project, mode="Create")

        db = get_db()
        db.execute(
            """
            INSERT INTO projects (title, description, status, owner_id)
            VALUES (?, ?, ?, ?)
            """,
            (title, description, status, g.user["id"]),
        )
        db.commit()
        db.close()
        flash("Project created.", "success")
        return redirect(url_for("projects"))

    return render_template("project_form.html", project=None, mode="Create")


@app.route("/projects/<int:project_id>")
@login_required
def project_detail(project_id):
    project = get_project_or_404(project_id)
    if g.user["role"] == "member" and project["owner_id"] != g.user["id"]:
        flash("Members can only view projects they own.", "danger")
        return redirect(url_for("projects"))

    db = get_db()
    tasks = db.execute(
        """
        SELECT t.*, u.username AS assignee_name
        FROM tasks t
        LEFT JOIN users u ON u.id = t.assignee_id
        WHERE t.project_id = ?
        ORDER BY
            CASE t.priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END,
            t.due_date ASC
        """,
        (project_id,),
    ).fetchall()
    users = db.execute(
        "SELECT id, username, role FROM users ORDER BY username"
    ).fetchall()
    db.close()
    return render_template(
        "project_detail.html",
        project=project,
        tasks=tasks,
        users=users,
        can_manage=can_manage_project(project),
    )


@app.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@roles_required("admin", "member")
def edit_project(project_id):
    project = get_project_or_404(project_id)
    if not can_manage_project(project):
        flash("You can only edit projects you own.", "danger")
        return redirect(url_for("project_detail", project_id=project_id))

    if request.method == "POST":
        errors, title, description, status = validate_project_form(request.form)
        if errors:
            for error in errors:
                flash(error, "danger")
            form_project = {"title": title, "description": description, "status": status}
            return render_template("project_form.html", project=form_project, mode="Edit")

        db = get_db()
        db.execute(
            """
            UPDATE projects
            SET title = ?, description = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (title, description, status, project_id),
        )
        db.commit()
        db.close()
        flash("Project updated.", "success")
        return redirect(url_for("project_detail", project_id=project_id))

    return render_template("project_form.html", project=project, mode="Edit")


@app.route("/projects/<int:project_id>/delete", methods=["POST"])
@roles_required("admin", "member")
def delete_project(project_id):
    project = get_project_or_404(project_id)
    if not can_manage_project(project):
        flash("You can only delete projects you own.", "danger")
        return redirect(url_for("project_detail", project_id=project_id))

    db = get_db()
    db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    db.commit()
    db.close()
    flash("Project deleted.", "success")
    return redirect(url_for("projects"))


@app.route("/projects/<int:project_id>/tasks", methods=["POST"])
@roles_required("admin", "member")
def create_task(project_id):
    project = get_project_or_404(project_id)
    if not can_manage_project(project):
        flash("You can only add tasks to projects you own.", "danger")
        return redirect(url_for("project_detail", project_id=project_id))

    title = request.form.get("title", "").strip()
    assignee_id = request.form.get("assignee_id", "").strip() or None
    status = request.form.get("status", "").strip()
    priority = request.form.get("priority", "").strip()
    due_date = request.form.get("due_date", "").strip() or None

    errors = []
    if not 2 <= len(title) <= 120:
        errors.append("Task title must be 2 to 120 characters.")
    if status not in TASK_STATUSES:
        errors.append("Choose a valid task status.")
    if priority not in TASK_PRIORITIES:
        errors.append("Choose a valid priority.")
    if due_date:
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            errors.append("Due date must use YYYY-MM-DD format.")
    if assignee_id:
        db = get_db()
        assignee = db.execute("SELECT id FROM users WHERE id = ?", (assignee_id,)).fetchone()
        db.close()
        if assignee is None:
            errors.append("Choose a valid assignee.")

    if errors:
        for error in errors:
            flash(error, "danger")
        return redirect(url_for("project_detail", project_id=project_id))

    db = get_db()
    db.execute(
        """
        INSERT INTO tasks (project_id, title, assignee_id, status, priority, due_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (project_id, title, assignee_id, status, priority, due_date),
    )
    db.execute(
        "UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (project_id,),
    )
    db.commit()
    db.close()
    flash("Task added.", "success")
    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/tasks/<int:task_id>/update", methods=["POST"])
@roles_required("admin", "member")
def update_task(task_id):
    db = get_db()
    task = db.execute(
        """
        SELECT t.*, p.owner_id
        FROM tasks t
        JOIN projects p ON p.id = t.project_id
        WHERE t.id = ?
        """,
        (task_id,),
    ).fetchone()
    if task is None:
        db.close()
        abort(404)
    if g.user["role"] != "admin" and task["owner_id"] != g.user["id"]:
        db.close()
        flash("You can only update tasks on projects you own.", "danger")
        return redirect(url_for("project_detail", project_id=task["project_id"]))

    status = request.form.get("status", "").strip()
    priority = request.form.get("priority", "").strip()
    if status not in TASK_STATUSES or priority not in TASK_PRIORITIES:
        db.close()
        flash("Choose valid task values.", "danger")
        return redirect(url_for("project_detail", project_id=task["project_id"]))

    db.execute(
        """
        UPDATE tasks
        SET status = ?, priority = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (status, priority, task_id),
    )
    db.execute(
        "UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (task["project_id"],),
    )
    db.commit()
    db.close()
    flash("Task updated.", "success")
    return redirect(url_for("project_detail", project_id=task["project_id"]))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
@roles_required("admin", "member")
def delete_task(task_id):
    db = get_db()
    task = db.execute(
        """
        SELECT t.*, p.owner_id
        FROM tasks t
        JOIN projects p ON p.id = t.project_id
        WHERE t.id = ?
        """,
        (task_id,),
    ).fetchone()
    if task is None:
        db.close()
        abort(404)
    if g.user["role"] != "admin" and task["owner_id"] != g.user["id"]:
        db.close()
        flash("You can only delete tasks on projects you own.", "danger")
        return redirect(url_for("project_detail", project_id=task["project_id"]))

    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.execute(
        "UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (task["project_id"],),
    )
    db.commit()
    db.close()
    flash("Task deleted.", "success")
    return redirect(url_for("project_detail", project_id=task["project_id"]))


@app.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        message = request.form.get("message", "").strip()
        errors = []
        if category not in FEEDBACK_CATEGORIES:
            errors.append("Choose a valid feedback category.")
        if not 10 <= len(message) <= 500:
            errors.append("Feedback must be 10 to 500 characters.")

        if errors:
            for error in errors:
                flash(error, "danger")
        else:
            db = get_db()
            db.execute(
                """
                INSERT INTO feedback (user_id, category, message)
                VALUES (?, ?, ?)
                """,
                (g.user["id"], category, message),
            )
            db.commit()
            db.close()
            flash("Feedback submitted.", "success")
            return redirect(url_for("feedback"))

    db = get_db()
    if g.user["role"] == "admin":
        items = db.execute(
            """
            SELECT f.*, u.username
            FROM feedback f
            JOIN users u ON u.id = f.user_id
            ORDER BY f.submitted_at DESC
            """
        ).fetchall()
    else:
        items = db.execute(
            """
            SELECT f.*, u.username
            FROM feedback f
            JOIN users u ON u.id = f.user_id
            WHERE f.user_id = ?
            ORDER BY f.submitted_at DESC
            """,
            (g.user["id"],),
        ).fetchall()
    db.close()
    return render_template("feedback.html", feedback_items=items)


@app.route("/admin", methods=["GET", "POST"])
@roles_required("admin")
def admin():
    db = get_db()
    if request.method == "POST":
        user_id = request.form.get("user_id", "").strip()
        role = request.form.get("role", "").strip()
        target = db.execute("SELECT id, role FROM users WHERE id = ?", (user_id,)).fetchone()

        if role not in ROLES or target is None:
            flash("Choose a valid user and role.", "danger")
        elif target["role"] == "admin" and role != "admin":
            admin_count = db.execute(
                "SELECT COUNT(*) AS total FROM users WHERE role = 'admin'"
            ).fetchone()["total"]
            if admin_count <= 1:
                flash("At least one admin account must remain.", "danger")
            else:
                db.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
                db.commit()
                flash("Role updated.", "success")
        else:
            db.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
            db.commit()
            flash("Role updated.", "success")

    users = db.execute(
        """
        SELECT u.*,
               COUNT(DISTINCT p.id) AS project_count,
               COUNT(DISTINCT f.id) AS feedback_count
        FROM users u
        LEFT JOIN projects p ON p.owner_id = u.id
        LEFT JOIN feedback f ON f.user_id = u.id
        GROUP BY u.id
        ORDER BY u.role, u.username
        """
    ).fetchall()
    status_rows = db.execute(
        "SELECT status, COUNT(*) AS total FROM projects GROUP BY status"
    ).fetchall()
    db.close()
    return render_template("admin.html", users=users, status_rows=status_rows)


if __name__ == "__main__":
    init_db()
    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    cert_path = os.path.join(BASE_DIR, "database", "cert.pem")
    key_path = os.path.join(BASE_DIR, "database", "key.pem")
    ssl_context = None
    if os.path.exists(cert_path) and os.path.exists(key_path):
        ssl_context = (cert_path, key_path)
    app.run(host=host, port=5000, debug=os.environ.get("FLASK_DEBUG") == "1", ssl_context=ssl_context)
