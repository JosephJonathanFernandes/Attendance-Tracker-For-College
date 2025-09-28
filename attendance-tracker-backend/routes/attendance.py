from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, AttendanceLog, Subject
from datetime import datetime, date
from sqlalchemy import func

attendance_bp = Blueprint("attendance", __name__)

@attendance_bp.route("/mark", methods=["POST"])
@jwt_required()
def mark_attendance():
    """Mark attendance for a subject"""
    data = request.json
    user_id = get_jwt_identity()
    
    # Validate required fields
    if not all(k in data for k in ("subject_id", "status")):
        return jsonify({"error": "Subject ID and status are required"}), 400
    
    if data["status"] not in ["Present", "Absent"]:
        return jsonify({"error": "Status must be 'Present' or 'Absent'"}), 400
    
    # Verify subject belongs to user
    subject = Subject.query.filter_by(id=data["subject_id"], user_id=user_id).first()
    if not subject:
        return jsonify({"error": "Subject not found"}), 404
    
    # Check if attendance already marked for today
    today = date.today()
    existing_log = AttendanceLog.query.filter_by(
        subject_id=data["subject_id"], 
        date=today
    ).first()
    
    if existing_log:
        return jsonify({"error": "Attendance already marked for today"}), 400
    
    # Create attendance log
    attendance_log = AttendanceLog(
        date=data.get("date", today),
        status=data["status"],
        subject_id=data["subject_id"]
    )
    
    # Update subject counters
    subject.total_classes += 1
    if data["status"] == "Present":
        subject.attended_classes += 1
    
    db.session.add(attendance_log)
    db.session.commit()
    
    # Calculate attendance percentage
    percentage = (subject.attended_classes / subject.total_classes * 100) if subject.total_classes > 0 else 0
    
    return jsonify({
        "message": "Attendance marked successfully",
        "attendance_log": {
            "id": attendance_log.id,
            "date": attendance_log.date.isoformat(),
            "status": attendance_log.status,
            "subject_id": attendance_log.subject_id
        },
        "subject_stats": {
            "total_classes": subject.total_classes,
            "attended_classes": subject.attended_classes,
            "attendance_percentage": round(percentage, 2)
        }
    }), 201

@attendance_bp.route("/logs/<int:subject_id>", methods=["GET"])
@jwt_required()
def get_attendance_logs(subject_id):
    """Get attendance logs for a specific subject"""
    user_id = get_jwt_identity()
    
    # Verify subject belongs to user
    subject = Subject.query.filter_by(id=subject_id, user_id=user_id).first()
    if not subject:
        return jsonify({"error": "Subject not found"}), 404
    
    # Get pagination parameters
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    # Query attendance logs
    logs_query = AttendanceLog.query.filter_by(subject_id=subject_id).order_by(AttendanceLog.date.desc())
    logs_paginated = logs_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    logs_data = [{
        "id": log.id,
        "date": log.date.isoformat(),
        "status": log.status,
        "subject_id": log.subject_id
    } for log in logs_paginated.items]
    
    return jsonify({
        "logs": logs_data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": logs_paginated.total,
            "pages": logs_paginated.pages,
            "has_next": logs_paginated.has_next,
            "has_prev": logs_paginated.has_prev
        },
        "subject": {
            "id": subject.id,
            "name": subject.name,
            "type": subject.type
        }
    })

@attendance_bp.route("/update/<int:log_id>", methods=["PUT"])
@jwt_required()
def update_attendance(log_id):
    """Update an existing attendance record"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Find the attendance log
    attendance_log = AttendanceLog.query.join(Subject).filter(
        AttendanceLog.id == log_id,
        Subject.user_id == user_id
    ).first()
    
    if not attendance_log:
        return jsonify({"error": "Attendance log not found"}), 404
    
    # Validate status if provided
    if "status" in data and data["status"] not in ["Present", "Absent"]:
        return jsonify({"error": "Status must be 'Present' or 'Absent'"}), 400
    
    # Get the subject for counter updates
    subject = Subject.query.get(attendance_log.subject_id)
    old_status = attendance_log.status
    new_status = data.get("status", old_status)
    
    # Update counters if status changed
    if old_status != new_status:
        if old_status == "Present" and new_status == "Absent":
            subject.attended_classes -= 1
        elif old_status == "Absent" and new_status == "Present":
            subject.attended_classes += 1
    
    # Update attendance log
    attendance_log.status = new_status
    if "date" in data:
        try:
            attendance_log.date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    db.session.commit()
    
    # Calculate updated percentage
    percentage = (subject.attended_classes / subject.total_classes * 100) if subject.total_classes > 0 else 0
    
    return jsonify({
        "message": "Attendance updated successfully",
        "attendance_log": {
            "id": attendance_log.id,
            "date": attendance_log.date.isoformat(),
            "status": attendance_log.status,
            "subject_id": attendance_log.subject_id
        },
        "subject_stats": {
            "total_classes": subject.total_classes,
            "attended_classes": subject.attended_classes,
            "attendance_percentage": round(percentage, 2)
        }
    })

@attendance_bp.route("/stats/<int:subject_id>", methods=["GET"])
@jwt_required()
def get_attendance_stats(subject_id):
    """Get attendance statistics for a subject"""
    user_id = get_jwt_identity()
    
    # Verify subject belongs to user
    subject = Subject.query.filter_by(id=subject_id, user_id=user_id).first()
    if not subject:
        return jsonify({"error": "Subject not found"}), 404
    
    # Get detailed statistics
    total_logs = AttendanceLog.query.filter_by(subject_id=subject_id).count()
    present_count = AttendanceLog.query.filter_by(subject_id=subject_id, status="Present").count()
    absent_count = AttendanceLog.query.filter_by(subject_id=subject_id, status="Absent").count()
    
    # Calculate percentages
    attendance_percentage = (present_count / total_logs * 100) if total_logs > 0 else 0
    absence_percentage = (absent_count / total_logs * 100) if total_logs > 0 else 0
    
    # Get recent attendance (last 10 classes)
    recent_logs = AttendanceLog.query.filter_by(subject_id=subject_id)\
        .order_by(AttendanceLog.date.desc()).limit(10).all()
    
    recent_attendance = [{
        "date": log.date.isoformat(),
        "status": log.status
    } for log in recent_logs]
    
    # Calculate streak (consecutive present/absent days)
    current_streak = 0
    streak_type = None
    if recent_logs:
        streak_type = recent_logs[0].status
        for log in recent_logs:
            if log.status == streak_type:
                current_streak += 1
            else:
                break
    
    return jsonify({
        "subject": {
            "id": subject.id,
            "name": subject.name,
            "type": subject.type
        },
        "statistics": {
            "total_classes": total_logs,
            "present_count": present_count,
            "absent_count": absent_count,
            "attendance_percentage": round(attendance_percentage, 2),
            "absence_percentage": round(absence_percentage, 2),
            "current_streak": {
                "count": current_streak,
                "type": streak_type
            }
        },
        "recent_attendance": recent_attendance
    })

@attendance_bp.route("/<int:log_id>", methods=["DELETE"])
@jwt_required()
def delete_attendance(log_id):
    """Delete an attendance record"""
    user_id = get_jwt_identity()
    
    # Find the attendance log
    attendance_log = AttendanceLog.query.join(Subject).filter(
        AttendanceLog.id == log_id,
        Subject.user_id == user_id
    ).first()
    
    if not attendance_log:
        return jsonify({"error": "Attendance log not found"}), 404
    
    # Get the subject for counter updates
    subject = Subject.query.get(attendance_log.subject_id)
    
    # Update counters
    subject.total_classes -= 1
    if attendance_log.status == "Present":
        subject.attended_classes -= 1
    
    # Delete the log
    db.session.delete(attendance_log)
    db.session.commit()
    
    # Calculate updated percentage
    percentage = (subject.attended_classes / subject.total_classes * 100) if subject.total_classes > 0 else 0
    
    return jsonify({
        "message": "Attendance record deleted successfully",
        "subject_stats": {
            "total_classes": subject.total_classes,
            "attended_classes": subject.attended_classes,
            "attendance_percentage": round(percentage, 2)
        }
    })

@attendance_bp.route("/summary", methods=["GET"])
@jwt_required()
def get_attendance_summary():
    """Get overall attendance summary for all subjects"""
    user_id = get_jwt_identity()
    
    # Get all subjects for the user
    subjects = Subject.query.filter_by(user_id=user_id).all()
    
    summary_data = []
    overall_total = 0
    overall_attended = 0
    
    for subject in subjects:
        total_classes = subject.total_classes
        attended_classes = subject.attended_classes
        percentage = (attended_classes / total_classes * 100) if total_classes > 0 else 0
        
        # Get recent attendance status
        last_attendance = AttendanceLog.query.filter_by(subject_id=subject.id)\
            .order_by(AttendanceLog.date.desc()).first()
        
        subject_data = {
            "id": subject.id,
            "name": subject.name,
            "type": subject.type,
            "total_classes": total_classes,
            "attended_classes": attended_classes,
            "attendance_percentage": round(percentage, 2),
            "last_attendance": {
                "date": last_attendance.date.isoformat() if last_attendance else None,
                "status": last_attendance.status if last_attendance else None
            }
        }
        
        summary_data.append(subject_data)
        overall_total += total_classes
        overall_attended += attended_classes
    
    # Calculate overall percentage
    overall_percentage = (overall_attended / overall_total * 100) if overall_total > 0 else 0
    
    return jsonify({
        "subjects": summary_data,
        "overall_stats": {
            "total_classes": overall_total,
            "attended_classes": overall_attended,
            "attendance_percentage": round(overall_percentage, 2),
            "total_subjects": len(subjects)
        }
    })
