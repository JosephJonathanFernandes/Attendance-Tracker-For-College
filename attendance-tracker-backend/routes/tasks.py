from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Task, Subject
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

tasks_bp = Blueprint("tasks", __name__)

@tasks_bp.route("/", methods=["POST"])
@jwt_required()
def create_task():
    """Create a new task"""
    data = request.json
    user_id = get_jwt_identity()
    
    # Validate required fields
    if not data.get("title"):
        return jsonify({"error": "Title is required"}), 400
    
    # Validate priority
    valid_priorities = ["low", "medium", "high", "urgent"]
    priority = data.get("priority", "medium")
    if priority not in valid_priorities:
        return jsonify({"error": f"Priority must be one of: {valid_priorities}"}), 400
    
    # Parse due_date if provided
    due_date = None
    if data.get("due_date"):
        try:
            due_date = datetime.fromisoformat(data["due_date"].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": "Invalid due_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400
    
    # Validate subject_id if provided
    subject_id = data.get("subject_id")
    if subject_id:
        subject = Subject.query.filter_by(id=subject_id, user_id=user_id).first()
        if not subject:
            return jsonify({"error": "Subject not found"}), 404
    
    # Create task
    task = Task(
        title=data["title"],
        description=data.get("description"),
        due_date=due_date,
        priority=priority,
        category=data.get("category"),
        estimated_hours=data.get("estimated_hours"),
        subject_id=subject_id,
        user_id=user_id
    )
    
    db.session.add(task)
    db.session.commit()
    
    return jsonify({
        "message": "Task created successfully",
        "task": task.to_dict()
    }), 201

@tasks_bp.route("/", methods=["GET"])
@jwt_required()
def get_tasks():
    """Get all tasks for the current user with filtering and pagination"""
    user_id = get_jwt_identity()
    
    # Get query parameters
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    completed = request.args.get("completed", type=str)
    priority = request.args.get("priority", type=str)
    category = request.args.get("category", type=str)
    subject_id = request.args.get("subject_id", type=int)
    overdue_only = request.args.get("overdue_only", type=str)
    sort_by = request.args.get("sort_by", "created_at")
    sort_order = request.args.get("sort_order", "desc")
    
    # Build query
    query = Task.query.filter_by(user_id=user_id)
    
    # Apply filters
    if completed is not None:
        completed_bool = completed.lower() in ['true', '1', 'yes']
        query = query.filter(Task.completed == completed_bool)
    
    if priority:
        query = query.filter(Task.priority == priority)
    
    if category:
        query = query.filter(Task.category == category)
    
    if subject_id:
        query = query.filter(Task.subject_id == subject_id)
    
    if overdue_only and overdue_only.lower() in ['true', '1', 'yes']:
        query = query.filter(
            and_(Task.due_date.isnot(None), 
                 Task.due_date < datetime.utcnow(),
                 Task.completed == False)
        )
    
    # Apply sorting
    valid_sort_fields = ["created_at", "updated_at", "due_date", "priority", "title"]
    if sort_by in valid_sort_fields:
        sort_field = getattr(Task, sort_by)
        if sort_order.lower() == "desc":
            sort_field = sort_field.desc()
        query = query.order_by(sort_field)
    
    # Paginate
    tasks_paginated = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        "tasks": [task.to_dict() for task in tasks_paginated.items],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": tasks_paginated.total,
            "pages": tasks_paginated.pages,
            "has_next": tasks_paginated.has_next,
            "has_prev": tasks_paginated.has_prev
        }
    })

@tasks_bp.route("/<int:task_id>", methods=["GET"])
@jwt_required()
def get_task(task_id):
    """Get a specific task"""
    user_id = get_jwt_identity()
    
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    return jsonify({"task": task.to_dict()})

@tasks_bp.route("/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    """Update a task"""
    user_id = get_jwt_identity()
    data = request.json
    
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    # Update fields if provided
    if "title" in data:
        task.title = data["title"]
    
    if "description" in data:
        task.description = data["description"]
    
    if "due_date" in data:
        if data["due_date"]:
            try:
                task.due_date = datetime.fromisoformat(data["due_date"].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"error": "Invalid due_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400
        else:
            task.due_date = None
    
    if "priority" in data:
        valid_priorities = ["low", "medium", "high", "urgent"]
        if data["priority"] not in valid_priorities:
            return jsonify({"error": f"Priority must be one of: {valid_priorities}"}), 400
        task.priority = data["priority"]
    
    if "category" in data:
        task.category = data["category"]
    
    if "estimated_hours" in data:
        task.estimated_hours = data["estimated_hours"]
    
    if "completed" in data:
        was_completed = task.completed
        task.completed = data["completed"]
        
        # Set completion timestamp
        if not was_completed and task.completed:
            task.completed_at = datetime.utcnow()
        elif was_completed and not task.completed:
            task.completed_at = None
    
    if "subject_id" in data:
        if data["subject_id"]:
            subject = Subject.query.filter_by(id=data["subject_id"], user_id=user_id).first()
            if not subject:
                return jsonify({"error": "Subject not found"}), 404
            task.subject_id = data["subject_id"]
        else:
            task.subject_id = None
    
    task.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "message": "Task updated successfully",
        "task": task.to_dict()
    })

@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    """Delete a task"""
    user_id = get_jwt_identity()
    
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({"message": "Task deleted successfully"})

@tasks_bp.route("/bulk", methods=["PUT"])
@jwt_required()
def bulk_update_tasks():
    """Bulk update tasks (mark multiple as complete, change priority, etc.)"""
    user_id = get_jwt_identity()
    data = request.json
    
    if not data.get("task_ids") or not isinstance(data["task_ids"], list):
        return jsonify({"error": "task_ids must be provided as an array"}), 400
    
    # Get tasks belonging to user
    tasks = Task.query.filter(
        Task.id.in_(data["task_ids"]),
        Task.user_id == user_id
    ).all()
    
    if not tasks:
        return jsonify({"error": "No tasks found"}), 404
    
    updated_count = 0
    
    for task in tasks:
        if "completed" in data:
            was_completed = task.completed
            task.completed = data["completed"]
            
            if not was_completed and task.completed:
                task.completed_at = datetime.utcnow()
            elif was_completed and not task.completed:
                task.completed_at = None
        
        if "priority" in data:
            valid_priorities = ["low", "medium", "high", "urgent"]
            if data["priority"] in valid_priorities:
                task.priority = data["priority"]
        
        if "category" in data:
            task.category = data["category"]
        
        task.updated_at = datetime.utcnow()
        updated_count += 1
    
    db.session.commit()
    
    return jsonify({
        "message": f"Successfully updated {updated_count} tasks",
        "updated_count": updated_count
    })

@tasks_bp.route("/statistics", methods=["GET"])
@jwt_required()
def get_task_statistics():
    """Get task statistics for the user"""
    user_id = get_jwt_identity()
    
    # Basic counts
    total_tasks = Task.query.filter_by(user_id=user_id).count()
    completed_tasks = Task.query.filter_by(user_id=user_id, completed=True).count()
    pending_tasks = total_tasks - completed_tasks
    
    # Overdue tasks
    overdue_tasks = Task.query.filter(
        Task.user_id == user_id,
        Task.completed == False,
        Task.due_date.isnot(None),
        Task.due_date < datetime.utcnow()
    ).count()
    
    # Due today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    due_today = Task.query.filter(
        Task.user_id == user_id,
        Task.completed == False,
        Task.due_date >= today_start,
        Task.due_date < today_end
    ).count()
    
    # Due this week
    week_end = today_start + timedelta(days=7)
    due_this_week = Task.query.filter(
        Task.user_id == user_id,
        Task.completed == False,
        Task.due_date >= today_start,
        Task.due_date < week_end
    ).count()
    
    # Priority breakdown
    priority_stats = {}
    for priority in ["low", "medium", "high", "urgent"]:
        priority_stats[priority] = Task.query.filter_by(
            user_id=user_id, 
            priority=priority, 
            completed=False
        ).count()
    
    # Category breakdown
    categories = db.session.query(Task.category).filter_by(user_id=user_id).distinct().all()
    category_stats = {}
    for (category,) in categories:
        if category:
            category_stats[category] = Task.query.filter_by(
                user_id=user_id, 
                category=category, 
                completed=False
            ).count()
    
    # Completion rate
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    return jsonify({
        "statistics": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "overdue_tasks": overdue_tasks,
            "due_today": due_today,
            "due_this_week": due_this_week,
            "completion_rate": round(completion_rate, 2),
            "priority_breakdown": priority_stats,
            "category_breakdown": category_stats
        }
    })

@tasks_bp.route("/upcoming", methods=["GET"])
@jwt_required()
def get_upcoming_tasks():
    """Get upcoming tasks (next 7 days) grouped by day"""
    user_id = get_jwt_identity()
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = today_start + timedelta(days=7)
    
    upcoming_tasks = Task.query.filter(
        Task.user_id == user_id,
        Task.completed == False,
        Task.due_date >= today_start,
        Task.due_date < week_end
    ).order_by(Task.due_date).all()
    
    # Group by day
    grouped_tasks = {}
    for task in upcoming_tasks:
        day_key = task.due_date.strftime("%Y-%m-%d")
        if day_key not in grouped_tasks:
            grouped_tasks[day_key] = {
                "date": day_key,
                "day_name": task.due_date.strftime("%A"),
                "tasks": []
            }
        grouped_tasks[day_key]["tasks"].append(task.to_dict())
    
    return jsonify({
        "upcoming_tasks": list(grouped_tasks.values())
    })
