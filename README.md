# TaskCore

TaskCore is a lightweight team task manager built with Flask and SQLite. The current UI is branded as `PulseBoard` and gives teams a cleaner way to manage projects, priorities, deadlines, and task updates from one dashboard.

## Features

- Role-based authentication for admins and members
- Project creation with descriptions and visual themes
- Task assignment with priorities, deadlines, and notes
- Kanban-style dashboard with Todo, In Progress, and Done columns
- Smart filtering by search, status, priority, project, and timeline view
- Progress insights, upcoming deadlines, and recent wins
- Responsive interface for desktop and mobile

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- HTML, CSS, and JavaScript

## Project Structure

```text
.
|-- app.py
|-- config.py
|-- models.py
|-- requirements.txt
|-- static/
|   |-- script.js
|   `-- style.css
`-- templates/
    |-- base.html
    |-- dashboard.html
    `-- login.html
```

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
python app.py
```

4. Open `http://127.0.0.1:5000` in your browser.

## Default Behavior

- The app creates its SQLite database automatically on first run.
- Admins can create projects and assign tasks.
- Members can update task status and leave progress notes.

## Suggested Next Improvements

- Drag-and-drop task movement
- File attachments and comments
- Email or in-app reminders
- Team activity timeline
- Deployment configuration for production secrets

## Live Link
web-production-fb878.up.railway.app
