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
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

try:
    from .db import connect_database, ensure_database_parent, resolve_database_url, schema_path_for
except ImportError:
    from db import connect_database, ensure_database_parent, resolve_database_url, schema_path_for


BASE_DIR = os.path.dirname(__file__)
DATABASE_URL = resolve_database_url(BASE_DIR)
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")
if not SECRET_KEY:
    if os.environ.get("FLASK_ENV") == "production":
        raise RuntimeError("FLASK_SECRET_KEY environment variable must be set")
    SECRET_KEY = secrets.token_hex(32)

ROLES = ("admin", "member", "viewer")
PROJECT_STATUSES = ("Planning", "Active", "Blocked", "Completed")
TASK_STATUSES = ("Todo", "In Progress", "Done")
TASK_PRIORITIES = ("Low", "Medium", "High")
FEEDBACK_CATEGORIES = ("Bug", "Security", "Feature", "General")
PASSWORD_RE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{10,}$")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE="Lax",
    RATELIMIT_ENABLED=os.environ.get("RATELIMIT_ENABLED", "1") != "0",
)

limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memory://",
)

@app.after_request
def set_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self' data:; "
        "frame-ancestors 'none'; "
        "form-action 'self'; "
        "base-uri 'self'; "
        "object-src 'none';"
    )
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), geolocation=(), microphone=(), payment=(), usb=()"
    )
    if g.get("user") or request.path in ("/login", "/register"):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
    return response


def get_db():
    return connect_database(DATABASE_URL)


def init_db():
    """Create schema and seed demo users/data if missing."""
    ensure_database_parent(DATABASE_URL)
    schema_path = schema_path_for(BASE_DIR, DATABASE_URL)

    db = get_db()
    with open(schema_path, encoding="utf-8") as schema_file:
        db.executescript(schema_file.read())

    seed_users(db)
    seed_projects(db)
    db.commit()
    db.close()


def seed_users(db):
    admin_pw = os.environ.get("ADMIN_PASSWORD", secrets.token_hex(8))
    member_pw = os.environ.get("MEMBER_PASSWORD", secrets.token_hex(8))
    viewer_pw = os.environ.get("VIEWER_PASSWORD", secrets.token_hex(8))
    
    if "ADMIN_PASSWORD" not in os.environ:
        print(f"[*] Generated random admin password: {admin_pw}")
        print(f"[*] Generated random member password: {member_pw}")
        print(f"[*] Generated random viewer password: {viewer_pw}")

    users = [
        ("admin", "admin@nexus.local", admin_pw, "admin"),
        ("member", "member@nexus.local", member_pw, "member"),
        ("viewer", "viewer@nexus.local", viewer_pw, "viewer"),
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

    security_project = db.execute(
        "SELECT id FROM projects WHERE title = ?",
        ("Security Review Portal",),
    ).fetchone()
    db.execute(
        """
        INSERT INTO tasks (project_id, title, assignee_id, status, priority, due_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            security_project["id"],
            "Document STRIDE threats",
            member["id"],
            "In Progress",
            "High",
            "2026-05-03",
        ),
    )
    db.execute(
        """
        INSERT INTO tasks (project_id, title, assignee_id, status, priority, due_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            security_project["id"],
            "Review executive summary",
            viewer["id"],
            "Todo",
            "Medium",
            "2026-05-08",
        ),
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
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def roles_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if g.user is None:
                flash("Please log in first.", "warning")
                return redirect(url_for("login"))
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


def log_activity(db, action, entity_type, entity_id=None, details=None, actor_id=None):
    if actor_id is None and g.get("user"):
        actor_id = g.user["id"]

    db.execute(
        """
        INSERT INTO activity_log (actor_id, action, entity_type, entity_id, details)
        VALUES (?, ?, ?, ?, ?)
        """,
        (actor_id, action, entity_type, entity_id, details or {}),
    )


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
@limiter.limit("5 per minute; 20 per hour", methods=["POST"])
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
        if not PASSWORD_RE.fullmatch(password):
            errors.append(
                "Password must be at least 10 characters and include uppercase, "
                "lowercase, a number, and a special character."
            )
        if password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("register.html", username=username, email=email)

        db = get_db()
        duplicate = db.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email),
        ).fetchone()
        
        if duplicate:
            db.close()
            flash("Username or email is already registered.", "danger")
            return render_template("register.html", username=username, email=email)

        cursor = db.execute(
            """
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, 'member')
            """,
            (username, email, generate_password_hash(password)),
        )
        log_activity(
            db,
            "user.registered",
            "user",
            getattr(cursor, "lastrowid", None),
            {"username": username, "email": email, "role": "member"},
            actor_id=getattr(cursor, "lastrowid", None),
        )
        db.commit()
        db.close()
        flash("Account created. You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute; 20 per hour", methods=["POST"])
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
            audit_db = get_db()
            log_activity(
                audit_db,
                "user.login",
                "session",
                details={"username": user["username"]},
                actor_id=user["id"],
            )
            audit_db.commit()
            audit_db.close()
            flash(f"Welcome back, {user['username']}.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid username/email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    db = get_db()
    log_activity(db, "user.logout", "session", details={"username": g.user["username"]})
    db.commit()
    db.close()
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
        GROUP BY p.id, u.username
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
        cursor = db.execute(
            """
            INSERT INTO projects (title, description, status, owner_id)
            VALUES (?, ?, ?, ?)
            """,
            (title, description, status, g.user["id"]),
        )
        log_activity(
            db,
            "project.created",
            "project",
            getattr(cursor, "lastrowid", None),
            {"title": title, "status": status},
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
        "SELECT id, username FROM users ORDER BY username"
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
        log_activity(
            db,
            "project.updated",
            "project",
            project_id,
            {"title": title, "status": status},
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
    log_activity(
        db,
        "project.deleted",
        "project",
        project_id,
        {"title": project["title"]},
    )
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
    cursor = db.execute(
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
    log_activity(
        db,
        "task.created",
        "task",
        getattr(cursor, "lastrowid", None),
        {"project_id": project_id, "title": title, "status": status, "priority": priority},
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
    log_activity(
        db,
        "task.updated",
        "task",
        task_id,
        {"project_id": task["project_id"], "status": status, "priority": priority},
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
    log_activity(
        db,
        "task.deleted",
        "task",
        task_id,
        {"project_id": task["project_id"], "title": task["title"]},
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
            cursor = db.execute(
                """
                INSERT INTO feedback (user_id, category, message)
                VALUES (?, ?, ?)
                """,
                (g.user["id"], category, message),
            )
            log_activity(
                db,
                "feedback.submitted",
                "feedback",
                getattr(cursor, "lastrowid", None),
                {"category": category},
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
        else:
            cursor = db.execute(
                """
                UPDATE users
                SET role = ?
                WHERE id = ?
                  AND (
                    role != 'admin'
                    OR ? = 'admin'
                    OR (SELECT COUNT(*) FROM users WHERE role = 'admin') > 1
                  )
                """,
                (role, user_id, role),
            )
            if cursor.rowcount == 0 and target["role"] == "admin" and role != "admin":
                flash("At least one admin account must remain.", "danger")
            elif cursor.rowcount == 0:
                flash("Choose a valid user and role.", "danger")
            else:
                log_activity(
                    db,
                    "user.role_changed",
                    "user",
                    user_id,
                    {"new_role": role},
                )
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
    recent_activity = db.execute(
        """
        SELECT a.*, u.username
        FROM activity_log a
        LEFT JOIN users u ON u.id = a.actor_id
        ORDER BY a.created_at DESC
        LIMIT 10
        """
    ).fetchall()
    db.close()
    return render_template(
        "admin.html",
        users=users,
        status_rows=status_rows,
        recent_activity=recent_activity,
    )


if __name__ == "__main__":
    init_db()
    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    cert_path = os.path.join(BASE_DIR, "database", "cert.pem")
    key_path = os.path.join(BASE_DIR, "database", "key.pem")
    ssl_context = None
    if os.path.exists(cert_path) and os.path.exists(key_path):
        ssl_context = (cert_path, key_path)
    app.run(host=host, port=5000, debug=os.environ.get("FLASK_DEBUG") == "1", ssl_context=ssl_context)
