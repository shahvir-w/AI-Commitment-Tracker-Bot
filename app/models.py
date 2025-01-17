from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Float, nullable=False, default=0.0)
    user_id = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<UserID {self.user_id}, Task {self.task_name!r}, Status {self.status}>'
