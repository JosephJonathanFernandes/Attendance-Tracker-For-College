from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
from models import db
from routes.auth import auth_bp
from routes.subjects import subjects_bp
from routes.attendance import attendance_bp
from routes.tasks import tasks_bp
from routes.reminders import reminders_bp
from routes.analytics import analytics_bp
from routes.calendar import calendar_bp

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)
db.init_app(app)
jwt = JWTManager(app)

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(subjects_bp, url_prefix="/api/subjects")
app.register_blueprint(attendance_bp, url_prefix="/api/attendance")
app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
app.register_blueprint(reminders_bp, url_prefix="/api/reminders")
app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
app.register_blueprint(calendar_bp, url_prefix="/api/calendar")

@app.route("/")
def index():
    return {
        "message": "🎯 Smart Attendance & Productivity Tracker API is running!", 
        "version": "2.0",
        "endpoints": {
            "auth": "/api/auth/",
            "subjects": "/api/subjects/",
            "attendance": "/api/attendance/",
            "tasks": "/api/tasks/",
            "reminders": "/api/reminders/",
            "analytics": "/api/analytics/",
            "calendar": "/api/calendar/"
        }
    }

@app.route("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": "2025-09-28T00:00:00Z"}

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("🚀 Database initialized successfully!")
        print("📊 Starting Smart Attendance & Productivity Tracker API...")
    app.run(debug=True, host="0.0.0.0", port=5000)
