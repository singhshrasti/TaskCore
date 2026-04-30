from collections import defaultdict
from datetime import UTC, datetime, timedelta
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from models import Project, Task, User, db

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

TASK_STATUSES = ["Todo", "In Progress", "Done"]
PRIORITY_OPTIONS = ["High", "Medium", "Low"]
PRIORITY_WEIGHTS = {"High": 0, "Medium": 1, "Low": 2}
PROJECT_THEMES = {
    "sunset": "Sunset",
    "ocean": "Ocean",
    "forest": "Forest",
    "midnight": "Midnight",
}
DEFAULT_THEME = "sunset"
WORKSPACE_ROUTE_PREFIXES = ("/dashboard", "/board", "/insights", "/manage")


def utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


def ensure_schema():
    column_definitions = {
        "project": {
            "description": "TEXT DEFAULT ''",
            "theme": f"VARCHAR(20) DEFAULT '{DEFAULT_THEME}'",
        },
        "task": {
            "priority": "VARCHAR(20) DEFAULT 'Medium'",
            "notes": "TEXT DEFAULT ''",
            "created_at": "DATETIME",
            "completed_at": "DATETIME",
        },
    }

    with db.engine.begin() as connection:
        tables = {
            row[0]
            for row in connection.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

        for table_name, columns in column_definitions.items():
            if table_name not in tables:
                continue

            existing_columns = {
                row[1]
                for row in connection.exec_driver_sql(
                    f"PRAGMA table_info({table_name})"
                ).fetchall()
            }

            for column_name, definition in columns.items():
                if column_name not in existing_columns:
                    connection.exec_driver_sql(
                        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
                    )

        if "project" in tables:
            connection.exec_driver_sql(
                "UPDATE project SET description = CASE "
                "WHEN description IS NULL OR description = '' THEN '' "
                "ELSE description END"
            )
            connection.exec_driver_sql(
                f"UPDATE project SET theme = CASE "
                f"WHEN theme IS NULL OR theme = '' THEN '{DEFAULT_THEME}' "
                f"ELSE theme END"
            )

        if "task" in tables:
            connection.exec_driver_sql(
                "UPDATE task SET priority = CASE "
                "WHEN priority IS NULL OR priority = '' THEN 'Medium' "
                "ELSE priority END"
            )
            connection.exec_driver_sql(
                "UPDATE task SET notes = CASE "
                "WHEN notes IS NULL OR notes = '' THEN '' "
                "ELSE notes END"
            )
            connection.exec_driver_sql(
                "UPDATE task SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP)"
            )
            connection.exec_driver_sql(
                "UPDATE task SET completed_at = COALESCE(completed_at, CURRENT_TIMESTAMP) "
                "WHERE status = 'Done'"
            )
            connection.exec_driver_sql(
                "UPDATE task SET completed_at = NULL WHERE status != 'Done'"
            )


with app.app_context():
    db.create_all()
    ensure_schema()


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("login"))

        if not db.session.get(User, user_id):
            session.clear()
            flash("Your session expired. Please sign in again.", "warning")
            return redirect(url_for("login"))

        return view_func(*args, **kwargs)

    return wrapped_view


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapped_view(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access is required for that action.", "warning")
            return redirect(url_for("dashboard"))
        return view_func(*args, **kwargs)

    return wrapped_view


def normalize_status(value):
    return value if value in TASK_STATUSES else "Todo"


def normalize_priority(value):
    return value if value in PRIORITY_OPTIONS else "Medium"


def normalize_theme(value):
    return value if value in PROJECT_THEMES else DEFAULT_THEME


def parse_deadline(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def format_date(value):
    if not value:
        return "No date"
    return value.strftime("%b %d, %Y")


def describe_deadline(deadline, status):
    if not deadline:
        return "No deadline", "no-deadline", None

    today = utcnow().date()
    deadline_date = deadline.date()
    days_left = (deadline_date - today).days

    if status != "Done" and days_left < 0:
        remaining = abs(days_left)
        label = f"Overdue by {remaining} day" if remaining == 1 else f"Overdue by {remaining} days"
        return label, "overdue", days_left

    if days_left == 0:
        return "Due today", "today", days_left

    if days_left == 1:
        return "Due tomorrow", "soon", days_left

    if status != "Done" and days_left <= 7:
        return f"Due in {days_left} days", "soon", days_left

    return f"Due {format_date(deadline)}", "scheduled", days_left


def build_task_card(task, users_map, projects_map, current_role, current_user_id):
    project = projects_map.get(task.project_id)
    assignee = users_map.get(task.assigned_to)
    status = normalize_status(task.status)
    priority = normalize_priority(task.priority)
    deadline_text, deadline_state, days_left = describe_deadline(task.deadline, status)
    search_blob = " ".join(
        [
            task.title or "",
            task.description or "",
            task.notes or "",
            project.name if project else "",
            assignee.name if assignee else "",
            priority,
            status,
        ]
    ).lower()

    return {
        "task": task,
        "status": status,
        "priority": priority,
        "assignee_name": assignee.name if assignee else "Unassigned",
        "project_name": project.name if project else "No project",
        "project_description": project.description if project else "",
        "project_theme": normalize_theme(project.theme) if project else "neutral",
        "deadline_text": deadline_text,
        "deadline_state": deadline_state,
        "days_left": days_left,
        "is_overdue": deadline_state == "overdue",
        "created_label": format_date(task.created_at),
        "completed_label": format_date(task.completed_at) if task.completed_at else "",
        "can_edit": current_role == "admin" or task.assigned_to == current_user_id,
        "search_blob": search_blob,
    }


def sort_task_cards(cards, sort_key):
    if sort_key == "priority":
        return sorted(
            cards,
            key=lambda card: (
                PRIORITY_WEIGHTS.get(card["priority"], 99),
                card["task"].deadline or datetime.max,
                (card["task"].title or "").lower(),
            ),
        )

    if sort_key == "newest":
        return sorted(
            cards,
            key=lambda card: card["task"].created_at or datetime.min,
            reverse=True,
        )

    if sort_key == "project":
        return sorted(
            cards,
            key=lambda card: (
                (card["project_name"] or "").lower(),
                card["task"].deadline or datetime.max,
            ),
        )

    return sorted(
        cards,
        key=lambda card: (
            card["task"].deadline or datetime.max,
            PRIORITY_WEIGHTS.get(card["priority"], 99),
            (card["task"].title or "").lower(),
        ),
    )


def build_project_summaries(projects, task_cards):
    cards_by_project = defaultdict(list)
    for card in task_cards:
        cards_by_project[card["task"].project_id].append(card)

    summaries = []
    for project in projects:
        cards = cards_by_project.get(project.id, [])
        total = len(cards)
        completed = sum(card["status"] == "Done" for card in cards)
        open_count = total - completed
        progress = round((completed / total) * 100) if total else 0
        summaries.append(
            {
                "name": project.name,
                "description": project.description or "No project brief yet.",
                "theme": normalize_theme(project.theme),
                "total": total,
                "open": open_count,
                "completed": completed,
                "progress": progress,
            }
        )

    return sorted(
        summaries,
        key=lambda summary: (-summary["total"], summary["name"].lower()),
    )


def build_dashboard_redirect(target):
    if target and target.startswith(WORKSPACE_ROUTE_PREFIXES):
        return target
    return url_for("dashboard")


def build_workspace_context(active_page):
    user_id = session["user_id"]
    role = session["role"]
    current_user = db.session.get(User, user_id)

    projects = Project.query.order_by(Project.name.asc()).all()
    users = User.query.order_by(User.name.asc()).all()
    users_map = {user.id: user for user in users}
    projects_map = {project.id: project for project in projects}

    task_query = Task.query
    if role != "admin":
        task_query = task_query.filter_by(assigned_to=user_id)

    all_visible_tasks = task_query.all()
    all_cards = [
        build_task_card(task, users_map, projects_map, role, user_id)
        for task in all_visible_tasks
    ]

    filters = {
        "q": request.args.get("q", "").strip(),
        "status": request.args.get("status", "All"),
        "priority": request.args.get("priority", "All"),
        "project": request.args.get("project", "all"),
        "view": request.args.get("view", "all"),
        "sort": request.args.get("sort", "deadline"),
    }

    filtered_cards = []
    today = utcnow().date()
    week_end = today + timedelta(days=7)

    for card in all_cards:
        task = card["task"]

        if filters["q"] and filters["q"].lower() not in card["search_blob"]:
            continue

        if filters["status"] != "All" and card["status"] != filters["status"]:
            continue

        if filters["priority"] != "All" and card["priority"] != filters["priority"]:
            continue

        if filters["project"] != "all" and str(task.project_id) != filters["project"]:
            continue

        if filters["view"] == "open" and card["status"] == "Done":
            continue

        if filters["view"] == "due_soon":
            if card["status"] == "Done" or not task.deadline:
                continue
            if not (today <= task.deadline.date() <= week_end):
                continue

        if filters["view"] == "overdue":
            if not card["is_overdue"]:
                continue

        if filters["view"] == "completed" and card["status"] != "Done":
            continue

        filtered_cards.append(card)

    filtered_cards = sort_task_cards(filtered_cards, filters["sort"])

    tasks_by_status = {status: [] for status in TASK_STATUSES}
    for card in filtered_cards:
        tasks_by_status[card["status"]].append(card)

    total = len(filtered_cards)
    completed = sum(card["status"] == "Done" for card in filtered_cards)
    in_progress = sum(card["status"] == "In Progress" for card in filtered_cards)
    overdue = sum(card["is_overdue"] for card in filtered_cards)
    high_priority = sum(
        card["priority"] == "High" and card["status"] != "Done"
        for card in filtered_cards
    )
    completion_rate = round((completed / total) * 100) if total else 0

    upcoming_tasks = [
        card
        for card in filtered_cards
        if card["status"] != "Done" and card["task"].deadline
    ]
    upcoming_tasks = sorted(upcoming_tasks, key=lambda card: card["task"].deadline)[:4]

    recent_wins = [
        card
        for card in filtered_cards
        if card["status"] == "Done" and card["task"].completed_at
    ]
    recent_wins = sorted(
        recent_wins,
        key=lambda card: card["task"].completed_at,
        reverse=True,
    )[:4]

    focus_cards = [
        card for card in sort_task_cards(filtered_cards, "priority")
        if card["status"] != "Done"
    ][:5]

    project_summaries = build_project_summaries(projects, all_cards)
    project_spotlight = project_summaries[:4]

    page_nav = [
        {"key": "overview", "label": "Overview", "endpoint": "dashboard"},
        {"key": "board", "label": "Task Board", "endpoint": "board"},
        {"key": "insights", "label": "Insights", "endpoint": "insights"},
    ]
    if role == "admin":
        page_nav.append({"key": "manage", "label": "Manage", "endpoint": "manage"})

    return {
        "body_class": "dashboard-page",
        "active_page": active_page,
        "page_nav": page_nav,
        "current_user": current_user,
        "role": role,
        "tasks_by_status": tasks_by_status,
        "total": total,
        "completed": completed,
        "overdue": overdue,
        "in_progress": in_progress,
        "high_priority": high_priority,
        "completion_rate": completion_rate,
        "users": users,
        "projects": projects,
        "filters": filters,
        "task_statuses": TASK_STATUSES,
        "priority_options": PRIORITY_OPTIONS,
        "project_themes": PROJECT_THEMES,
        "project_summaries": project_summaries,
        "project_spotlight": project_spotlight,
        "upcoming_tasks": upcoming_tasks,
        "recent_wins": recent_wins,
        "focus_cards": focus_cards,
        "board_total": len(all_cards),
        "has_projects": bool(projects),
        "dashboard_return": request.full_path if request.query_string else request.path,
        "project_count": len(projects),
        "member_count": len(users),
    }


# ---------------- AUTH ---------------- #


@app.route("/", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session.clear()
            session["user_id"] = user.id
            session["role"] = user.role
            flash(f"Welcome back, {user.name}.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html", body_class="auth-page")


@app.route("/signup", methods=["POST"])
def signup():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    role = request.form.get("role", "member")

    if not name or not email or not password:
        flash("Name, email, and password are required.", "warning")
        return redirect(url_for("login"))

    if role not in {"admin", "member"}:
        role = "member"

    if User.query.filter_by(email=email).first():
        flash("That email already has an account.", "warning")
        return redirect(url_for("login"))

    user = User(
        name=name,
        email=email,
        password=generate_password_hash(password),
        role=role,
    )
    db.session.add(user)
    db.session.commit()

    flash("Account created. You can sign in now.", "success")
    return redirect(url_for("login"))


# ---------------- DASHBOARD ---------------- #


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard_overview.html", **build_workspace_context("overview"))


@app.route("/board")
@login_required
def board():
    return render_template("dashboard_board.html", **build_workspace_context("board"))


@app.route("/insights")
@login_required
def insights():
    return render_template("dashboard_insights.html", **build_workspace_context("insights"))


@app.route("/manage")
@admin_required
def manage():
    return render_template("dashboard_manage.html", **build_workspace_context("manage"))


# ---------------- PROJECT ---------------- #


@app.route("/create_project", methods=["POST"])
@admin_required
def create_project():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    theme = normalize_theme(request.form.get("theme", DEFAULT_THEME))
    redirect_to = request.form.get("redirect_to")

    if not name:
        flash("Project name is required.", "warning")
        return redirect(build_dashboard_redirect(redirect_to))

    project = Project(
        name=name,
        description=description,
        theme=theme,
        created_by=session["user_id"],
    )
    db.session.add(project)
    db.session.commit()

    flash(f"Project '{name}' created.", "success")
    return redirect(build_dashboard_redirect(redirect_to))


# ---------------- TASK ---------------- #


@app.route("/create_task", methods=["POST"])
@admin_required
def create_task():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    notes = request.form.get("notes", "").strip()
    assigned_to = request.form.get("assigned_to", type=int)
    project_id = request.form.get("project_id", type=int)
    deadline = parse_deadline(request.form.get("deadline", "").strip())
    priority = normalize_priority(request.form.get("priority"))
    status = normalize_status(request.form.get("status"))
    redirect_to = request.form.get("redirect_to")

    if not title or not description or not assigned_to or not project_id:
        flash("Title, description, assignee, and project are required.", "warning")
        return redirect(build_dashboard_redirect(redirect_to))

    assignee = db.session.get(User, assigned_to)
    project = db.session.get(Project, project_id)
    if not assignee or not project:
        flash("Choose a valid assignee and project.", "warning")
        return redirect(build_dashboard_redirect(redirect_to))

    now = utcnow()
    task = Task(
        title=title,
        description=description,
        assigned_to=assigned_to,
        project_id=project_id,
        status=status,
        priority=priority,
        notes=notes,
        deadline=deadline,
        created_at=now,
        completed_at=now if status == "Done" else None,
    )

    db.session.add(task)
    db.session.commit()

    flash(f"Task '{title}' added to {project.name}.", "success")
    return redirect(build_dashboard_redirect(redirect_to))


@app.route("/update_task/<int:task_id>", methods=["POST"])
@login_required
def update_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        flash("That task could not be found.", "warning")
        return redirect(url_for("dashboard"))

    if session.get("role") != "admin" and task.assigned_to != session["user_id"]:
        flash("You can only update tasks assigned to you.", "warning")
        return redirect(url_for("dashboard"))

    task.status = normalize_status(request.form.get("status"))
    task.notes = request.form.get("notes", "").strip()

    if task.status == "Done":
        task.completed_at = task.completed_at or utcnow()
    else:
        task.completed_at = None

    db.session.commit()

    flash(f"Updated '{task.title}'.", "success")
    return redirect(build_dashboard_redirect(request.form.get("redirect_to")))


# ---------------- LOGOUT ---------------- #


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
