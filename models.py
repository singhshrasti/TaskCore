from datetime import UTC, datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    return datetime.now(UTC).replace(tzinfo=None)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(10))


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text, default="")
    theme = db.Column(db.String(20), default="sunset")
    created_by = db.Column(db.Integer)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    status = db.Column(db.String(20))
    priority = db.Column(db.String(20), default="Medium")
    notes = db.Column(db.Text, default="")
    assigned_to = db.Column(db.Integer)
    project_id = db.Column(db.Integer)
    deadline = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utcnow)
    completed_at = db.Column(db.DateTime)
