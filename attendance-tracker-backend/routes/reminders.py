from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Reminder, Task, Subject
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

reminders_bp = Blueprint("reminders", __name__)

@reminders_bp.route("/", methods=["POST"])
@jwt_required()
def create_reminder():
    """Create a new reminder"""
    data = request.json
    user_id = get_jwt_identity()
    
    # Validate required fields
    if not all(k in data for k in ("title", "message", "reminder_time")):
        return jsonify({"error": "Title, message, and reminder_time are required"}), 400
    
    # Parse reminder_time
    try:
        reminder_time = datetime.fromisoformat(data["reminder_time"].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({"error": "Invalid reminder_time format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400
    
    # Validate reminder_type
    valid_types = ["general", "task", "attendance", "exam", "assignment", "meeting"]
    reminder_type = data.get("reminder_type", "general")
    if reminder_type not in valid_types:
        return jsonify({"error": f"reminder_type must be one of: {valid_types}"}), 400
    
    # Validate recurrence
    valid_recurrence = [None, "none", "daily", "weekly", "monthly"]
    recurrence = data.get("recurrence")
    if recurrence not in valid_recurrence:
        return jsonify({"error": f"recurrence must be one of: {valid_recurrence}"}), 400
    
    # Validate task_id if provided
    task_id = data.get("task_id")
    if task_id:
        task = Task.query.filter_by(id=task_id, user_id=user_id).first()
        if not task:
            return jsonify({"error": "Task not found"}), 404
    
    # Validate subject_id if provided
    subject_id = data.get("subject_id")
    if subject_id:
        subject = Subject.query.filter_by(id=subject_id, user_id=user_id).first()
        if not subject:
            return jsonify({"error": "Subject not found"}), 404
    
    # Create reminder
    reminder = Reminder(
        title=data["title"],
        message=data["message"],
        reminder_time=reminder_time,
        reminder_type=reminder_type,
        recurrence=recurrence,
        task_id=task_id,
        subject_id=subject_id,
        user_id=user_id
    )
    
    db.session.add(reminder)
    db.session.commit()
    
    return jsonify({
        "message": "Reminder created successfully",
        "reminder": reminder.to_dict()
    }), 201

@reminders_bp.route("/", methods=["GET"])
@jwt_required()
def get_reminders():
    """Get all reminders for the current user with filtering"""
    user_id = get_jwt_identity()
    
    # Get query parameters
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    active = request.args.get("active", type=str)
    reminder_type = request.args.get("reminder_type", type=str)
    upcoming_only = request.args.get("upcoming_only", type=str)
    due_only = request.args.get("due_only", type=str)
    
    # Build query
    query = Reminder.query.filter_by(user_id=user_id)
    
    # Apply filters
    if active is not None:
        active_bool = active.lower() in ['true', '1', 'yes']
        query = query.filter(Reminder.active == active_bool)
    
    if reminder_type:
        query = query.filter(Reminder.reminder_type == reminder_type)
    
    if upcoming_only and upcoming_only.lower() in ['true', '1', 'yes']:
        query = query.filter(Reminder.reminder_time >= datetime.utcnow())
    
    if due_only and due_only.lower() in ['true', '1', 'yes']:
        query = query.filter(
            and_(Reminder.reminder_time <= datetime.utcnow(),
                 Reminder.sent == False,
                 Reminder.active == True)
        )
    
    # Order by reminder time
    query = query.order_by(Reminder.reminder_time)
    
    # Paginate
    reminders_paginated = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        "reminders": [reminder.to_dict() for reminder in reminders_paginated.items],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": reminders_paginated.total,
            "pages": reminders_paginated.pages,
            "has_next": reminders_paginated.has_next,
            "has_prev": reminders_paginated.has_prev
        }
    })

@reminders_bp.route("/<int:reminder_id>", methods=["GET"])
@jwt_required()
def get_reminder(reminder_id):
    """Get a specific reminder"""
    user_id = get_jwt_identity()
    
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=user_id).first()
    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404
    
    return jsonify({"reminder": reminder.to_dict()})

@reminders_bp.route("/<int:reminder_id>", methods=["PUT"])
@jwt_required()
def update_reminder(reminder_id):
    """Update a reminder"""
    user_id = get_jwt_identity()
    data = request.json
    
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=user_id).first()
    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404
    
    # Update fields if provided
    if "title" in data:
        reminder.title = data["title"]
    
    if "message" in data:
        reminder.message = data["message"]
    
    if "reminder_time" in data:
        try:
            reminder.reminder_time = datetime.fromisoformat(data["reminder_time"].replace('Z', '+00:00'))
            # Reset sent status if time changed
            reminder.sent = False
        except ValueError:
            return jsonify({"error": "Invalid reminder_time format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400
    
    if "reminder_type" in data:
        valid_types = ["general", "task", "attendance", "exam", "assignment", "meeting"]
        if data["reminder_type"] not in valid_types:
            return jsonify({"error": f"reminder_type must be one of: {valid_types}"}), 400
        reminder.reminder_type = data["reminder_type"]
    
    if "recurrence" in data:
        valid_recurrence = [None, "none", "daily", "weekly", "monthly"]
        if data["recurrence"] not in valid_recurrence:
            return jsonify({"error": f"recurrence must be one of: {valid_recurrence}"}), 400
        reminder.recurrence = data["recurrence"]
    
    if "active" in data:
        reminder.active = data["active"]
    
    if "task_id" in data:
        if data["task_id"]:
            task = Task.query.filter_by(id=data["task_id"], user_id=user_id).first()
            if not task:
                return jsonify({"error": "Task not found"}), 404
            reminder.task_id = data["task_id"]
        else:
            reminder.task_id = None
    
    if "subject_id" in data:
        if data["subject_id"]:
            subject = Subject.query.filter_by(id=data["subject_id"], user_id=user_id).first()
            if not subject:
                return jsonify({"error": "Subject not found"}), 404
            reminder.subject_id = data["subject_id"]
        else:
            reminder.subject_id = None
    
    reminder.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "message": "Reminder updated successfully",
        "reminder": reminder.to_dict()
    })

@reminders_bp.route("/<int:reminder_id>", methods=["DELETE"])
@jwt_required()
def delete_reminder(reminder_id):
    """Delete a reminder"""
    user_id = get_jwt_identity()
    
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=user_id).first()
    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404
    
    db.session.delete(reminder)
    db.session.commit()
    
    return jsonify({"message": "Reminder deleted successfully"})

@reminders_bp.route("/due", methods=["GET"])
@jwt_required()
def get_due_reminders():
    """Get all due reminders (for notifications)"""
    user_id = get_jwt_identity()
    
    due_reminders = Reminder.query.filter(
        Reminder.user_id == user_id,
        Reminder.reminder_time <= datetime.utcnow(),
        Reminder.sent == False,
        Reminder.active == True
    ).all()
    
    return jsonify({
        "due_reminders": [reminder.to_dict() for reminder in due_reminders],
        "count": len(due_reminders)
    })

@reminders_bp.route("/<int:reminder_id>/mark-sent", methods=["POST"])
@jwt_required()
def mark_reminder_sent(reminder_id):
    """Mark a reminder as sent"""
    user_id = get_jwt_identity()
    
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=user_id).first()
    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404
    
    reminder.sent = True
    
    # Handle recurrence
    if reminder.recurrence and reminder.recurrence != "none":
        # Create next reminder based on recurrence
        next_time = reminder.reminder_time
        
        if reminder.recurrence == "daily":
            next_time += timedelta(days=1)
        elif reminder.recurrence == "weekly":
            next_time += timedelta(weeks=1)
        elif reminder.recurrence == "monthly":
            next_time += timedelta(days=30)  # Approximate month
        
        # Create new reminder for next occurrence
        new_reminder = Reminder(
            title=reminder.title,
            message=reminder.message,
            reminder_time=next_time,
            reminder_type=reminder.reminder_type,
            recurrence=reminder.recurrence,
            task_id=reminder.task_id,
            subject_id=reminder.subject_id,
            user_id=reminder.user_id
        )
        db.session.add(new_reminder)
    
    db.session.commit()
    
    return jsonify({
        "message": "Reminder marked as sent",
        "created_recurring": reminder.recurrence and reminder.recurrence != "none"
    })

@reminders_bp.route("/upcoming", methods=["GET"])
@jwt_required()
def get_upcoming_reminders():
    """Get upcoming reminders (next 24 hours)"""
    user_id = get_jwt_identity()
    
    now = datetime.utcnow()
    tomorrow = now + timedelta(days=1)
    
    upcoming_reminders = Reminder.query.filter(
        Reminder.user_id == user_id,
        Reminder.active == True,
        Reminder.reminder_time >= now,
        Reminder.reminder_time <= tomorrow
    ).order_by(Reminder.reminder_time).all()
    
    return jsonify({
        "upcoming_reminders": [reminder.to_dict() for reminder in upcoming_reminders],
        "count": len(upcoming_reminders)
    })

@reminders_bp.route("/bulk-create", methods=["POST"])
@jwt_required()
def bulk_create_reminders():
    """Create multiple reminders at once"""
    data = request.json
    user_id = get_jwt_identity()
    
    if not data.get("reminders") or not isinstance(data["reminders"], list):
        return jsonify({"error": "reminders must be provided as an array"}), 400
    
    created_reminders = []
    errors = []
    
    for i, reminder_data in enumerate(data["reminders"]):
        try:
            # Validate required fields
            if not all(k in reminder_data for k in ("title", "message", "reminder_time")):
                errors.append(f"Reminder {i+1}: Missing required fields")
                continue
            
            # Parse reminder_time
            reminder_time = datetime.fromisoformat(reminder_data["reminder_time"].replace('Z', '+00:00'))
            
            # Create reminder
            reminder = Reminder(
                title=reminder_data["title"],
                message=reminder_data["message"],
                reminder_time=reminder_time,
                reminder_type=reminder_data.get("reminder_type", "general"),
                recurrence=reminder_data.get("recurrence"),
                task_id=reminder_data.get("task_id"),
                subject_id=reminder_data.get("subject_id"),
                user_id=user_id
            )
            
            db.session.add(reminder)
            created_reminders.append(reminder)
            
        except Exception as e:
            errors.append(f"Reminder {i+1}: {str(e)}")
    
    if created_reminders:
        db.session.commit()
    
    return jsonify({
        "message": f"Successfully created {len(created_reminders)} reminders",
        "created_count": len(created_reminders),
        "errors": errors,
        "created_reminders": [reminder.to_dict() for reminder in created_reminders]
    }), 201 if created_reminders else 400

@reminders_bp.route("/statistics", methods=["GET"])
@jwt_required()
def get_reminder_statistics():
    """Get reminder statistics for the user"""
    user_id = get_jwt_identity()
    
    # Basic counts
    total_reminders = Reminder.query.filter_by(user_id=user_id).count()
    active_reminders = Reminder.query.filter_by(user_id=user_id, active=True).count()
    sent_reminders = Reminder.query.filter_by(user_id=user_id, sent=True).count()
    
    # Due reminders
    due_reminders = Reminder.query.filter(
        Reminder.user_id == user_id,
        Reminder.reminder_time <= datetime.utcnow(),
        Reminder.sent == False,
        Reminder.active == True
    ).count()
    
    # Upcoming (next 24 hours)
    now = datetime.utcnow()
    tomorrow = now + timedelta(days=1)
    upcoming_reminders = Reminder.query.filter(
        Reminder.user_id == user_id,
        Reminder.active == True,
        Reminder.reminder_time >= now,
        Reminder.reminder_time <= tomorrow
    ).count()
    
    # Type breakdown
    type_stats = {}
    for reminder_type in ["general", "task", "attendance", "exam", "assignment", "meeting"]:
        type_stats[reminder_type] = Reminder.query.filter_by(
            user_id=user_id, 
            reminder_type=reminder_type,
            active=True
        ).count()
    
    return jsonify({
        "statistics": {
            "total_reminders": total_reminders,
            "active_reminders": active_reminders,
            "sent_reminders": sent_reminders,
            "due_reminders": due_reminders,
            "upcoming_reminders": upcoming_reminders,
            "type_breakdown": type_stats
        }
    })
