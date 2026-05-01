# TaskCore

<p align="center">
  <strong>A polished Flask task manager for teams that need clarity, ownership, and momentum.</strong>
</p>

<p align="center">
  TaskCore powers a dashboard-style workspace branded as <strong>PulseBoard</strong>, helping teams create projects, assign tasks, track deadlines, and monitor progress from one clean interface.
</p>

<p align="center">
  <a href="https://web-production-fb878.up.railway.app"><strong>Live Demo</strong></a>
  |
  <a href="https://github.com/singhshrasti/TaskCore"><strong>GitHub Repository</strong></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python badge" />
  <img src="https://img.shields.io/badge/Flask-Web_App-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask badge" />
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite badge" />
  <img src="https://img.shields.io/badge/Railway-Live_Demo-0B0D0E?style=for-the-badge&logo=railway&logoColor=white" alt="Railway badge" />
</p>

## Live Demo

Explore the deployed app here:

<https://web-production-fb878.up.railway.app>

## Why TaskCore

TaskCore is designed for small teams and student or portfolio projects that want something more structured than a simple to-do list. It combines project management, assignee-based workflows, progress visibility, and deadline awareness in a lightweight Flask application backed by SQLite.

## Highlights

- Role-based authentication for admins and members
- Project creation with descriptions and visual themes
- Task assignment with status, priority, deadlines, and notes
- Kanban-style board with `Todo`, `In Progress`, and `Done`
- Search, filter, and sort controls for faster task tracking
- Insights view with completion rate, overdue work, and recent wins
- Responsive UI for desktop and mobile
- Ready for deployment with `gunicorn` and `DATABASE_URL` support

## Workspace Views

| View | What it offers |
| --- | --- |
| Overview | Team progress summary, focus tasks, deadline tracking, and project spotlight |
| Task Board | A Kanban workflow for moving work across statuses |
| Insights | Completion metrics, overdue visibility, and recent wins |
| Manage | Admin-only space for creating projects and assigning tasks |

## Roles

| Role | Permissions |
| --- | --- |
| Admin | Create projects, assign tasks, and manage the workspace |
| Member | Sign in, review assigned work, update status, and add progress notes |

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- Gunicorn
- HTML, CSS, JavaScript

## Project Structure

```text
.
|-- app.py
|-- config.py
|-- models.py
|-- requirements.txt
|-- Procfile
|-- static/
|   |-- script.js
|   `-- style.css
`-- templates/
    |-- base.html
    |-- dashboard.html
    |-- dashboard_board.html
    |-- dashboard_insights.html
    |-- dashboard_layout.html
    |-- dashboard_manage.html
    |-- dashboard_overview.html
    `-- login.html
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/singhshrasti/TaskCore.git
cd TaskCore
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

## Environment Notes

TaskCore works out of the box for local development, but you can also configure production values:

- `SECRET_KEY`: Flask session secret
- `DATABASE_URL`: Use Postgres or another supported production database

If `DATABASE_URL` is not set, the app automatically creates a local SQLite database inside `instance/database.db`.

## Deployment

The app includes a `Procfile` for production startup:

```text
web: gunicorn app:app
```

This project is already live on Railway:

<https://web-production-fb878.up.railway.app>

## Default App Behavior

- The database is created automatically on first run
- New users can sign up from the auth screen
- Admins can create projects and tasks
- Members can update the tasks assigned to them

## Future Improvements

- Drag-and-drop task movement
- Comments and file attachments
- Notifications or reminders
- Activity timeline for team updates
- Stronger production secret management
