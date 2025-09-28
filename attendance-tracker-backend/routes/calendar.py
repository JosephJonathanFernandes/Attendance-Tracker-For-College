from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Subject, AttendanceLog, Task, Reminder
from datetime import datetime, date, timedelta
import calendar

calendar_bp = Blueprint("calendar", __name__)

def get_attendance_calendar(user_id, year, month):
    """Generate attendance calendar for a user"""
    # Get the first and last day of the month
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    
    # Get all attendance logs for the month
    logs = AttendanceLog.query.join(Subject).filter(
        Subject.user_id == user_id,
        AttendanceLog.date >= first_day,
        AttendanceLog.date <= last_day
    ).all()
    
    # Group logs by date
    daily_attendance = {}
    for log in logs:
        date_str = log.date.isoformat()
        if date_str not in daily_attendance:
            daily_attendance[date_str] = []
        
        daily_attendance[date_str].append({
            "subject": log.subject.name,
            "status": log.status,
            "notes": log.notes
        })
    
    # Generate calendar grid
    cal = calendar.monthcalendar(year, month)
    calendar_weeks = []
    
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append(None)  # Days from previous/next month
            else:
                day_date = date(year, month, day)
                date_str = day_date.isoformat()
                
                day_data = {
                    "day": day,
                    "date": date_str,
                    "is_weekend": day_date.weekday() >= 5,
                    "attendance": daily_attendance.get(date_str, []),
                    "has_classes": len(daily_attendance.get(date_str, [])) > 0
                }
                
                # Calculate day status
                if day_data["attendance"]:
                    present_count = len([a for a in day_data["attendance"] if a["status"] == "Present"])
                    total_count = len(day_data["attendance"])
                    day_data["attendance_percentage"] = (present_count / total_count) * 100
                    
                    if present_count == total_count:
                        day_data["status"] = "perfect"
                    elif present_count > 0:
                        day_data["status"] = "partial"
                    else:
                        day_data["status"] = "absent"
                else:
                    day_data["status"] = "no-classes"
                
                week_data.append(day_data)
        
        calendar_weeks.append(week_data)
    
    return {
        "year": year,
        "month": month,
        "month_name": calendar.month_name[month],
        "weeks": calendar_weeks
    }

@calendar_bp.route("/calendar/<int:year>/<int:month>", methods=["GET"])
@jwt_required()
def get_monthly_calendar(year, month):
    """Get monthly attendance calendar"""
    user_id = get_jwt_identity()
    
    try:
        calendar_data = get_attendance_calendar(user_id, year, month)
        return jsonify({"calendar": calendar_data})
    except Exception as e:
        return jsonify({"error": f"Failed to generate calendar: {str(e)}"}), 500

@calendar_bp.route("/calendar/current", methods=["GET"])
@jwt_required()
def get_current_calendar():
    """Get current month's attendance calendar"""
    user_id = get_jwt_identity()
    now = datetime.now()
    
    try:
        calendar_data = get_attendance_calendar(user_id, now.year, now.month)
        return jsonify({"calendar": calendar_data})
    except Exception as e:
        return jsonify({"error": f"Failed to generate calendar: {str(e)}"}), 500

@calendar_bp.route("/notifications/due", methods=["GET"])
@jwt_required()
def get_due_notifications():
    """Get browser notifications for due reminders"""
    user_id = get_jwt_identity()
    
    now = datetime.utcnow()
    
    due_reminders = Reminder.query.filter(
        Reminder.user_id == user_id,
        Reminder.reminder_time <= now,
        Reminder.sent == False,
        Reminder.active == True
    ).all()
    
    notifications = []
    for reminder in due_reminders:
        notifications.append({
            "id": reminder.id,
            "title": reminder.title,
            "body": reminder.message,
            "type": reminder.reminder_type,
            "timestamp": reminder.reminder_time.isoformat(),
            "actions": [
                {"action": "mark-done", "title": "Mark as Done"},
                {"action": "snooze", "title": "Snooze 1 hour"}
            ]
        })
    
    return jsonify({
        "notifications": notifications,
        "count": len(notifications)
    })

@calendar_bp.route("/notifications/<int:notification_id>/snooze", methods=["POST"])
@jwt_required()
def snooze_notification(notification_id):
    """Snooze a notification by specified duration"""
    user_id = get_jwt_identity()
    data = request.json
    snooze_minutes = data.get("minutes", 60)  # Default 1 hour
    
    reminder = Reminder.query.filter_by(id=notification_id, user_id=user_id).first()
    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404
    
    # Update reminder time
    new_time = datetime.utcnow() + timedelta(minutes=snooze_minutes)
    reminder.reminder_time = new_time
    reminder.sent = False  # Reset sent status
    
    db.session.commit()
    
    return jsonify({
        "message": f"Reminder snoozed for {snooze_minutes} minutes",
        "new_time": new_time.isoformat()
    })

@calendar_bp.route("/weekly-overview", methods=["GET"])
@jwt_required()
def get_weekly_overview():
    """Get weekly overview with classes, tasks, and reminders"""
    user_id = get_jwt_identity()
    
    # Get date range for current week
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday
    
    # Get attendance for the week
    attendance_logs = AttendanceLog.query.join(Subject).filter(
        Subject.user_id == user_id,
        AttendanceLog.date >= start_of_week,
        AttendanceLog.date <= end_of_week
    ).all()
    
    # Get tasks for the week
    week_start_dt = datetime.combine(start_of_week, datetime.min.time())
    week_end_dt = datetime.combine(end_of_week, datetime.max.time())
    
    tasks = Task.query.filter(
        Task.user_id == user_id,
        Task.due_date >= week_start_dt,
        Task.due_date <= week_end_dt
    ).all()
    
    # Get reminders for the week
    reminders = Reminder.query.filter(
        Reminder.user_id == user_id,
        Reminder.reminder_time >= week_start_dt,
        Reminder.reminder_time <= week_end_dt,
        Reminder.active == True
    ).all()
    
    # Organize by day
    weekly_data = {}
    current_date = start_of_week
    
    while current_date <= end_of_week:
        day_key = current_date.strftime("%A").lower()
        day_attendance = [log for log in attendance_logs if log.date == current_date]
        day_tasks = [task for task in tasks if task.due_date.date() == current_date]
        day_reminders = [r for r in reminders if r.reminder_time.date() == current_date]
        
        weekly_data[day_key] = {
            "date": current_date.isoformat(),
            "day_name": current_date.strftime("%A"),
            "attendance": [
                {
                    "subject": log.subject.name,
                    "status": log.status,
                    "notes": log.notes
                } for log in day_attendance
            ],
            "tasks": [task.to_dict() for task in day_tasks],
            "reminders": [reminder.to_dict() for reminder in day_reminders],
            "summary": {
                "classes": len(day_attendance),
                "present": len([log for log in day_attendance if log.status == "Present"]),
                "tasks_due": len(day_tasks),
                "reminders": len(day_reminders)
            }
        }
        
        current_date += timedelta(days=1)
    
    return jsonify({
        "week_overview": {
            "start_date": start_of_week.isoformat(),
            "end_date": end_of_week.isoformat(),
            "days": weekly_data,
            "weekly_summary": {
                "total_classes": len(attendance_logs),
                "total_present": len([log for log in attendance_logs if log.status == "Present"]),
                "total_tasks": len(tasks),
                "total_reminders": len(reminders)
            }
        }
    })

calendar_bp = Blueprint("calendar", __name__)

@calendar_bp.route("/calendar/<int:year>/<int:month>", methods=["GET"])
@jwt_required()
def get_monthly_calendar(year, month):
    """Get monthly attendance calendar"""
    user_id = get_jwt_identity()
    
    try:
        calendar_data = CalendarUtils.get_attendance_calendar(user_id, year, month)
        return jsonify({"calendar": calendar_data})
    except Exception as e:
        return jsonify({"error": f"Failed to generate calendar: {str(e)}"}), 500

@calendar_bp.route("/calendar/current", methods=["GET"])
@jwt_required()
def get_current_calendar():
    """Get current month's attendance calendar"""
    user_id = get_jwt_identity()
    now = datetime.now()
    
    try:
        calendar_data = CalendarUtils.get_attendance_calendar(user_id, now.year, now.month)
        return jsonify({"calendar": calendar_data})
    except Exception as e:
        return jsonify({"error": f"Failed to generate calendar: {str(e)}"}), 500

@calendar_bp.route("/academic-calendar", methods=["GET"])
@jwt_required()
def get_academic_calendar():
    """Get academic calendar with important dates"""
    year = request.args.get("year", datetime.now().year, type=int)
    
    academic_calendar = CalendarUtils.get_academic_calendar(year)
    holidays = CalendarUtils.get_holidays(year)
    
    return jsonify({
        "academic_calendar": academic_calendar,
        "holidays": holidays
    })

@calendar_bp.route("/semester-progress", methods=["GET"])
@jwt_required()
def get_semester_progress():
    """Get current semester progress"""
    # For now, assume fall semester (can be made dynamic)
    current_year = datetime.now().year
    semester = request.args.get("semester", "fall")
    
    academic_calendar = CalendarUtils.get_academic_calendar(current_year)
    
    if semester == "fall":
        start_date = academic_calendar["fall_semester"]["start"]
        end_date = academic_calendar["fall_semester"]["end"]
    elif semester == "spring":
        start_date = academic_calendar["spring_semester"]["start"]
        end_date = academic_calendar["spring_semester"]["end"]
    else:
        start_date = academic_calendar["summer_semester"]["start"]
        end_date = academic_calendar["summer_semester"]["end"]
    
    progress = CalendarUtils.get_semester_progress(start_date, end_date)
    
    return jsonify({"semester_progress": progress})

@calendar_bp.route("/study-schedule", methods=["GET"])
@jwt_required()
def get_study_schedule():
    """Get suggested study schedule based on tasks"""
    user_id = get_jwt_identity()
    available_hours = request.args.get("available_hours_per_day", 4, type=int)
    
    # Get pending tasks
    tasks = Task.query.filter_by(user_id=user_id, completed=False).all()
    task_data = [task.to_dict() for task in tasks if task.due_date]
    
    try:
        schedule = CalendarUtils.suggest_study_schedule(task_data, available_hours)
        return jsonify({"study_schedule": schedule})
    except Exception as e:
        return jsonify({"error": f"Failed to generate study schedule: {str(e)}"}), 500

# Notification endpoints
@calendar_bp.route("/notifications/due", methods=["GET"])
@jwt_required()
def get_due_notifications():
    """Get browser notifications for due reminders"""
    user_id = get_jwt_identity()
    
    notifications = NotificationService.get_browser_notification_data(user_id)
    
    return jsonify({
        "notifications": notifications,
        "count": len(notifications)
    })

@calendar_bp.route("/notifications/process", methods=["POST"])
@jwt_required()
def process_notifications():
    """Manually trigger notification processing (admin/testing)"""
    try:
        sent_count = NotificationService.process_due_reminders()
        return jsonify({
            "message": f"Processed notifications successfully",
            "notifications_sent": sent_count
        })
    except Exception as e:
        return jsonify({"error": f"Failed to process notifications: {str(e)}"}), 500

@calendar_bp.route("/notifications/attendance-warnings", methods=["POST"])
@jwt_required()
def create_attendance_warnings():
    """Create attendance warning reminders for low-attendance subjects"""
    user_id = get_jwt_identity()
    
    try:
        warnings_created = NotificationService.create_attendance_warnings(user_id)
        return jsonify({
            "message": f"Created {warnings_created} attendance warning reminders",
            "warnings_created": warnings_created
        })
    except Exception as e:
        return jsonify({"error": f"Failed to create warnings: {str(e)}"}), 500

@calendar_bp.route("/notifications/<int:notification_id>/snooze", methods=["POST"])
@jwt_required()
def snooze_notification(notification_id):
    """Snooze a notification by specified duration"""
    user_id = get_jwt_identity()
    data = request.json
    snooze_minutes = data.get("minutes", 60)  # Default 1 hour
    
    reminder = Reminder.query.filter_by(id=notification_id, user_id=user_id).first()
    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404
    
    # Update reminder time
    new_time = datetime.utcnow() + timedelta(minutes=snooze_minutes)
    reminder.reminder_time = new_time
    reminder.sent = False  # Reset sent status
    
    db.session.commit()
    
    return jsonify({
        "message": f"Reminder snoozed for {snooze_minutes} minutes",
        "new_time": new_time.isoformat()
    })

@calendar_bp.route("/weekly-overview", methods=["GET"])
@jwt_required()
def get_weekly_overview():
    """Get weekly overview with classes, tasks, and reminders"""
    user_id = get_jwt_identity()
    
    # Get date range for current week
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday
    
    # Get attendance for the week
    attendance_logs = AttendanceLog.query.join(Subject).filter(
        Subject.user_id == user_id,
        AttendanceLog.date >= start_of_week,
        AttendanceLog.date <= end_of_week
    ).all()
    
    # Get tasks for the week
    week_start_dt = datetime.combine(start_of_week, datetime.min.time())
    week_end_dt = datetime.combine(end_of_week, datetime.max.time())
    
    tasks = Task.query.filter(
        Task.user_id == user_id,
        Task.due_date >= week_start_dt,
        Task.due_date <= week_end_dt
    ).all()
    
    # Get reminders for the week
    reminders = Reminder.query.filter(
        Reminder.user_id == user_id,
        Reminder.reminder_time >= week_start_dt,
        Reminder.reminder_time <= week_end_dt,
        Reminder.active == True
    ).all()
    
    # Organize by day
    weekly_data = {}
    current_date = start_of_week
    
    while current_date <= end_of_week:
        day_key = current_date.strftime("%A").lower()
        day_attendance = [log for log in attendance_logs if log.date == current_date]
        day_tasks = [task for task in tasks if task.due_date.date() == current_date]
        day_reminders = [r for r in reminders if r.reminder_time.date() == current_date]
        
        weekly_data[day_key] = {
            "date": current_date.isoformat(),
            "day_name": current_date.strftime("%A"),
            "attendance": [
                {
                    "subject": log.subject.name,
                    "status": log.status,
                    "notes": log.notes
                } for log in day_attendance
            ],
            "tasks": [task.to_dict() for task in day_tasks],
            "reminders": [reminder.to_dict() for reminder in day_reminders],
            "summary": {
                "classes": len(day_attendance),
                "present": len([log for log in day_attendance if log.status == "Present"]),
                "tasks_due": len(day_tasks),
                "reminders": len(day_reminders)
            }
        }
        
        current_date += timedelta(days=1)
    
    return jsonify({
        "week_overview": {
            "start_date": start_of_week.isoformat(),
            "end_date": end_of_week.isoformat(),
            "days": weekly_data,
            "weekly_summary": {
                "total_classes": len(attendance_logs),
                "total_present": len([log for log in attendance_logs if log.status == "Present"]),
                "total_tasks": len(tasks),
                "total_reminders": len(reminders)
            }
        }
    })

@calendar_bp.route("/month-overview/<int:year>/<int:month>", methods=["GET"])
@jwt_required()
def get_month_overview(year, month):
    """Get monthly overview with statistics"""
    user_id = get_jwt_identity()
    
    # Get first and last day of month
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    
    # Get attendance for the month
    attendance_logs = AttendanceLog.query.join(Subject).filter(
        Subject.user_id == user_id,
        AttendanceLog.date >= first_day,
        AttendanceLog.date <= last_day
    ).all()
    
    # Get tasks for the month
    month_start_dt = datetime.combine(first_day, datetime.min.time())
    month_end_dt = datetime.combine(last_day, datetime.max.time())
    
    tasks_completed = Task.query.filter(
        Task.user_id == user_id,
        Task.completed == True,
        Task.completed_at >= month_start_dt,
        Task.completed_at <= month_end_dt
    ).count()
    
    tasks_due = Task.query.filter(
        Task.user_id == user_id,
        Task.due_date >= month_start_dt,
        Task.due_date <= month_end_dt
    ).count()
    
    # Calculate statistics
    total_classes = len(attendance_logs)
    present_classes = len([log for log in attendance_logs if log.status == "Present"])
    attendance_percentage = (present_classes / total_classes * 100) if total_classes > 0 else 0
    
    # Subject-wise breakdown
    subjects_data = {}
    for log in attendance_logs:
        subject_name = log.subject.name
        if subject_name not in subjects_data:
            subjects_data[subject_name] = {"total": 0, "present": 0}
        
        subjects_data[subject_name]["total"] += 1
        if log.status == "Present":
            subjects_data[subject_name]["present"] += 1
    
    # Convert to list with percentages
    subjects_breakdown = []
    for subject, data in subjects_data.items():
        percentage = (data["present"] / data["total"] * 100) if data["total"] > 0 else 0
        subjects_breakdown.append({
            "subject": subject,
            "total": data["total"],
            "present": data["present"],
            "percentage": round(percentage, 2)
        })
    
    return jsonify({
        "month_overview": {
            "year": year,
            "month": month,
            "month_name": calendar.month_name[month],
            "statistics": {
                "total_classes": total_classes,
                "present_classes": present_classes,
                "attendance_percentage": round(attendance_percentage, 2),
                "tasks_completed": tasks_completed,
                "tasks_due": tasks_due
            },
            "subjects_breakdown": subjects_breakdown
        }
    })