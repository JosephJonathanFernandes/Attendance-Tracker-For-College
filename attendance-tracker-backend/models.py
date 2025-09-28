from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    timezone = db.Column(db.String(50), default='UTC')
    preferences = db.Column(db.JSON, default=lambda: {"theme": "light", "notifications": True})
    subjects = db.relationship("Subject", backref="user", lazy=True, cascade="all, delete-orphan")
    tasks = db.relationship("Task", backref="user", lazy=True, cascade="all, delete-orphan")
    reminders = db.relationship("Reminder", backref="user", lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'timezone': self.timezone,
            'preferences': self.preferences
        }

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # theory/lab/tutorial
    total_classes = db.Column(db.Integer, default=0)
    attended_classes = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    target_percentage = db.Column(db.Float, default=75.0)  # Target attendance percentage
    color = db.Column(db.String(7), default='#007bff')  # Hex color for UI
    is_archived = db.Column(db.Boolean, default=False)
    credits = db.Column(db.Integer, default=3)  # Subject credits for weighted calculations
    semester = db.Column(db.String(20), nullable=True)  # e.g., "Fall 2025"
    logs = db.relationship("AttendanceLog", backref="subject", lazy=True, cascade="all, delete-orphan")
    
    @property
    def attendance_percentage(self):
        """Calculate attendance percentage"""
        if self.total_classes == 0:
            return 0.0
        return round((self.attended_classes / self.total_classes) * 100, 2)
    
    @property
    def classes_needed_for_target(self):
        """Calculate how many classes needed to reach target percentage"""
        if self.attendance_percentage >= self.target_percentage:
            return 0
        
        # Formula: (attended + x) / (total + x) = target/100
        # Solving for x: x = (target * total - 100 * attended) / (100 - target)
        target = self.target_percentage
        if target >= 100:
            return float('inf')
        
        x = (target * self.total_classes - 100 * self.attended_classes) / (100 - target)
        return max(0, int(x) + 1)  # Round up
    
    @property
    def can_afford_to_miss(self):
        """Calculate how many classes can be missed while maintaining target"""
        if self.total_classes == 0:
            return 0
        
        current_percentage = self.attendance_percentage
        if current_percentage <= self.target_percentage:
            return 0
        
        # Binary search for maximum classes that can be missed
        max_miss = 0
        for miss in range(1, 20):  # Reasonable upper limit
            future_attended = self.attended_classes
            future_total = self.total_classes + miss
            future_percentage = (future_attended / future_total) * 100
            
            if future_percentage >= self.target_percentage:
                max_miss = miss
            else:
                break
        
        return max_miss
    
    def to_dict(self, include_stats=True):
        data = {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'total_classes': self.total_classes,
            'attended_classes': self.attended_classes,
            'target_percentage': self.target_percentage,
            'color': self.color,
            'credits': self.credits,
            'semester': self.semester,
            'is_archived': self.is_archived,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_stats:
            data.update({
                'attendance_percentage': self.attendance_percentage,
                'classes_needed_for_target': self.classes_needed_for_target,
                'can_afford_to_miss': self.can_afford_to_miss,
                'status': 'good' if self.attendance_percentage >= self.target_percentage else 'warning'
            })
        
        return data

class AttendanceLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(10), nullable=False)  # Present/Absent
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)  # Optional notes for the attendance
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status,
            'subject_id': self.subject_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)  # Changed to DateTime for time-specific tasks
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.String(20), default='medium')  # low/medium/high/urgent
    category = db.Column(db.String(50), nullable=True)  # study/assignment/exam/personal
    estimated_hours = db.Column(db.Float, nullable=True)  # Estimated time to complete
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=True)  # Link to subject
    
    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if not self.due_date or self.completed:
            return False
        return datetime.utcnow() > self.due_date
    
    @property
    def days_until_due(self):
        """Calculate days until due date"""
        if not self.due_date:
            return None
        delta = self.due_date - datetime.utcnow()
        return delta.days
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'priority': self.priority,
            'category': self.category,
            'estimated_hours': self.estimated_hours,
            'subject_id': self.subject_id,
            'is_overdue': self.is_overdue,
            'days_until_due': self.days_until_due,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)  # Added title field
    message = db.Column(db.String(500), nullable=False)  # Increased length
    reminder_time = db.Column(db.DateTime, nullable=False)  # Renamed from 'time'
    active = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reminder_type = db.Column(db.String(50), default='general')  # general/task/attendance/exam
    recurrence = db.Column(db.String(20), nullable=True)  # none/daily/weekly/monthly
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=True)  # Link to task
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=True)  # Link to subject
    sent = db.Column(db.Boolean, default=False)  # Track if reminder was sent
    
    @property
    def is_due(self):
        """Check if reminder is due to be sent"""
        return datetime.utcnow() >= self.reminder_time and not self.sent and self.active
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'reminder_time': self.reminder_time.isoformat() if self.reminder_time else None,
            'active': self.active,
            'reminder_type': self.reminder_type,
            'recurrence': self.recurrence,
            'task_id': self.task_id,
            'subject_id': self.subject_id,
            'sent': self.sent,
            'is_due': self.is_due,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Analytics Models for Advanced Features
class AttendanceGoal(db.Model):
    """Track user-defined attendance goals and milestones"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=True)  # None for overall goals
    goal_type = db.Column(db.String(50), nullable=False)  # percentage/streak/total_classes
    target_value = db.Column(db.Float, nullable=False)
    current_value = db.Column(db.Float, default=0.0)
    achieved = db.Column(db.Boolean, default=False)
    achieved_at = db.Column(db.DateTime, nullable=True)
    deadline = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'subject_id': self.subject_id,
            'goal_type': self.goal_type,
            'target_value': self.target_value,
            'current_value': self.current_value,
            'achieved': self.achieved,
            'achieved_at': self.achieved_at.isoformat() if self.achieved_at else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserSession(db.Model):
    """Track user login sessions for analytics"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    logout_time = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # Support IPv6
    user_agent = db.Column(db.Text, nullable=True)
    session_duration_minutes = db.Column(db.Integer, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'login_time': self.login_time.isoformat() if self.login_time else None,
            'logout_time': self.logout_time.isoformat() if self.logout_time else None,
            'session_duration_minutes': self.session_duration_minutes,
            'ip_address': self.ip_address
        }
