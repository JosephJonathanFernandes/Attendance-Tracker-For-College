from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Subject
from datetime import datetime

subjects_bp = Blueprint("subjects", __name__)

@subjects_bp.route("/", methods=["POST"])
@jwt_required()
def add_subject():
    """Create a new subject"""
    data = request.json
    user_id = get_jwt_identity()
    
    # Validate required fields
    if not data.get("name"):
        return jsonify({"error": "Subject name is required"}), 400
    
    if not data.get("type"):
        return jsonify({"error": "Subject type is required"}), 400
    
    # Validate type
    valid_types = ["theory", "lab", "tutorial", "practical"]
    if data["type"] not in valid_types:
        return jsonify({"error": f"Subject type must be one of: {valid_types}"}), 400
    
    # Validate target_percentage if provided
    target_percentage = data.get("target_percentage", 75.0)
    if not (0 <= target_percentage <= 100):
        return jsonify({"error": "Target percentage must be between 0 and 100"}), 400
    
    # Create subject
    subject = Subject(
        name=data["name"],
        type=data["type"],
        user_id=user_id,
        target_percentage=target_percentage,
        color=data.get("color", "#007bff"),
        credits=data.get("credits", 3),
        semester=data.get("semester")
    )
    
    db.session.add(subject)
    db.session.commit()
    
    return jsonify({
        "message": "Subject created successfully",
        "subject": subject.to_dict()
    }), 201

@subjects_bp.route("/", methods=["GET"])
@jwt_required()
def get_subjects():
    """Get all subjects for the current user"""
    user_id = get_jwt_identity()
    
    # Get query parameters
    include_archived = request.args.get("include_archived", "false").lower() == "true"
    subject_type = request.args.get("type")
    semester = request.args.get("semester")
    
    # Build query
    query = Subject.query.filter_by(user_id=user_id)
    
    if not include_archived:
        query = query.filter_by(is_archived=False)
    
    if subject_type:
        query = query.filter_by(type=subject_type)
    
    if semester:
        query = query.filter_by(semester=semester)
    
    subjects = query.order_by(Subject.name).all()
    
    return jsonify({
        "subjects": [subject.to_dict() for subject in subjects],
        "count": len(subjects)
    })

@subjects_bp.route("/<int:subject_id>", methods=["GET"])
@jwt_required()
def get_subject(subject_id):
    """Get a specific subject with detailed statistics"""
    user_id = get_jwt_identity()
    
    subject = Subject.query.filter_by(id=subject_id, user_id=user_id).first()
    if not subject:
        return jsonify({"error": "Subject not found"}), 404
    
    return jsonify({"subject": subject.to_dict()})

@subjects_bp.route("/<int:subject_id>", methods=["PUT"])
@jwt_required()
def update_subject(subject_id):
    """Update a subject"""
    user_id = get_jwt_identity()
    data = request.json
    
    subject = Subject.query.filter_by(id=subject_id, user_id=user_id).first()
    if not subject:
        return jsonify({"error": "Subject not found"}), 404
    
    # Update fields if provided
    if "name" in data:
        subject.name = data["name"]
    
    if "type" in data:
        valid_types = ["theory", "lab", "tutorial", "practical"]
        if data["type"] not in valid_types:
            return jsonify({"error": f"Subject type must be one of: {valid_types}"}), 400
        subject.type = data["type"]
    
    if "target_percentage" in data:
        target_percentage = data["target_percentage"]
        if not (0 <= target_percentage <= 100):
            return jsonify({"error": "Target percentage must be between 0 and 100"}), 400
        subject.target_percentage = target_percentage
    
    if "color" in data:
        subject.color = data["color"]
    
    if "credits" in data:
        subject.credits = data["credits"]
    
    if "semester" in data:
        subject.semester = data["semester"]
    
    if "is_archived" in data:
        subject.is_archived = data["is_archived"]
    
    subject.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "message": "Subject updated successfully",
        "subject": subject.to_dict()
    })

@subjects_bp.route("/<int:subject_id>", methods=["DELETE"])
@jwt_required()
def delete_subject(subject_id):
    """Delete a subject and all related attendance logs"""
    user_id = get_jwt_identity()
    
    subject = Subject.query.filter_by(id=subject_id, user_id=user_id).first()
    if not subject:
        return jsonify({"error": "Subject not found"}), 404
    
    # Note: Related attendance logs will be deleted due to cascade
    db.session.delete(subject)
    db.session.commit()
    
    return jsonify({"message": "Subject deleted successfully"})

@subjects_bp.route("/analytics", methods=["GET"])
@jwt_required()
def get_subjects_analytics():
    """Get comprehensive analytics for all subjects"""
    user_id = get_jwt_identity()
    
    subjects = Subject.query.filter_by(user_id=user_id, is_archived=False).all()
    
    # Calculate overall statistics
    total_subjects = len(subjects)
    total_classes = sum(s.total_classes for s in subjects)
    total_attended = sum(s.attended_classes for s in subjects)
    overall_percentage = (total_attended / total_classes * 100) if total_classes > 0 else 0
    
    # Subjects below target
    below_target = [s for s in subjects if s.attendance_percentage < s.target_percentage]
    critical_subjects = [s for s in subjects if s.attendance_percentage < 60]
    
    # Subject performance categories
    excellent = [s for s in subjects if s.attendance_percentage >= 90]
    good = [s for s in subjects if 75 <= s.attendance_percentage < 90]
    warning = [s for s in subjects if 60 <= s.attendance_percentage < 75]
    critical = [s for s in subjects if s.attendance_percentage < 60]
    
    # Calculate weighted average (by credits)
    total_credits = sum(s.credits for s in subjects if s.credits)
    weighted_percentage = 0
    if total_credits > 0:
        weighted_percentage = sum(
            s.attendance_percentage * s.credits for s in subjects if s.credits
        ) / total_credits
    
    # Classes needed to reach targets
    classes_needed = sum(s.classes_needed_for_target for s in below_target)
    
    # Type-wise breakdown
    type_stats = {}
    for subject_type in ["theory", "lab", "tutorial", "practical"]:
        type_subjects = [s for s in subjects if s.type == subject_type]
        if type_subjects:
            type_total_classes = sum(s.total_classes for s in type_subjects)
            type_attended = sum(s.attended_classes for s in type_subjects)
            type_percentage = (type_attended / type_total_classes * 100) if type_total_classes > 0 else 0
            
            type_stats[subject_type] = {
                "count": len(type_subjects),
                "total_classes": type_total_classes,
                "attended_classes": type_attended,
                "percentage": round(type_percentage, 2),
                "below_target": len([s for s in type_subjects if s.attendance_percentage < s.target_percentage])
            }
    
    return jsonify({
        "analytics": {
            "summary": {
                "total_subjects": total_subjects,
                "total_classes": total_classes,
                "total_attended": total_attended,
                "overall_percentage": round(overall_percentage, 2),
                "weighted_percentage": round(weighted_percentage, 2),
                "subjects_below_target": len(below_target),
                "critical_subjects": len(critical_subjects),
                "classes_needed_for_targets": classes_needed
            },
            "performance_categories": {
                "excellent": {
                    "count": len(excellent),
                    "subjects": [{"id": s.id, "name": s.name, "percentage": s.attendance_percentage} for s in excellent]
                },
                "good": {
                    "count": len(good),
                    "subjects": [{"id": s.id, "name": s.name, "percentage": s.attendance_percentage} for s in good]
                },
                "warning": {
                    "count": len(warning),
                    "subjects": [{"id": s.id, "name": s.name, "percentage": s.attendance_percentage} for s in warning]
                },
                "critical": {
                    "count": len(critical),
                    "subjects": [{"id": s.id, "name": s.name, "percentage": s.attendance_percentage} for s in critical]
                }
            },
            "type_breakdown": type_stats,
            "action_items": {
                "immediate_attention": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "percentage": s.attendance_percentage,
                        "classes_needed": s.classes_needed_for_target,
                        "can_afford_to_miss": s.can_afford_to_miss
                    } for s in below_target
                ]
            }
        }
    })

@subjects_bp.route("/predictions", methods=["GET"])
@jwt_required()
def get_attendance_predictions():
    """Get attendance predictions and recommendations"""
    user_id = get_jwt_identity()
    
    subjects = Subject.query.filter_by(user_id=user_id, is_archived=False).all()
    predictions = []
    
    for subject in subjects:
        # Simple prediction based on current trend
        if subject.total_classes >= 5:  # Need some history for prediction
            current_percentage = subject.attendance_percentage
            
            # Predict based on different scenarios
            scenarios = {
                "maintain_current": {
                    "description": "If you maintain current attendance pattern",
                    "classes_to_predict": 20,
                    "expected_attendance_rate": current_percentage / 100
                },
                "perfect_attendance": {
                    "description": "If you attend all remaining classes",
                    "classes_to_predict": 20,
                    "expected_attendance_rate": 1.0
                },
                "skip_one_per_week": {
                    "description": "If you skip one class per week",
                    "classes_to_predict": 20,
                    "expected_attendance_rate": 0.8
                }
            }
            
            subject_predictions = {"id": subject.id, "name": subject.name, "scenarios": {}}
            
            for scenario_name, scenario in scenarios.items():
                future_classes = scenario["classes_to_predict"]
                future_attended = int(future_classes * scenario["expected_attendance_rate"])
                
                final_total = subject.total_classes + future_classes
                final_attended = subject.attended_classes + future_attended
                final_percentage = (final_attended / final_total) * 100
                
                subject_predictions["scenarios"][scenario_name] = {
                    "description": scenario["description"],
                    "predicted_percentage": round(final_percentage, 2),
                    "will_meet_target": final_percentage >= subject.target_percentage,
                    "classes_predicted": future_classes,
                    "attendance_rate": scenario["expected_attendance_rate"]
                }
            
            predictions.append(subject_predictions)
    
    return jsonify({
        "predictions": predictions,
        "generated_at": datetime.utcnow().isoformat()
    })

@subjects_bp.route("/recommendations", methods=["GET"])
@jwt_required()
def get_recommendations():
    """Get personalized recommendations for improving attendance"""
    user_id = get_jwt_identity()
    
    subjects = Subject.query.filter_by(user_id=user_id, is_archived=False).all()
    recommendations = []
    
    for subject in subjects:
        subject_recommendations = []
        
        # Below target recommendations
        if subject.attendance_percentage < subject.target_percentage:
            classes_needed = subject.classes_needed_for_target
            subject_recommendations.append({
                "type": "urgent",
                "message": f"Attend the next {classes_needed} classes to reach {subject.target_percentage}% target",
                "action": "attend_consecutively",
                "priority": "high"
            })
        
        # Critical subjects
        elif subject.attendance_percentage < 60:
            subject_recommendations.append({
                "type": "critical",
                "message": "Your attendance is critically low. Consider speaking with your instructor.",
                "action": "contact_instructor",
                "priority": "urgent"
            })
        
        # Good performance but room for improvement
        elif 75 <= subject.attendance_percentage < 85:
            can_miss = subject.can_afford_to_miss
            if can_miss > 0:
                subject_recommendations.append({
                    "type": "info",
                    "message": f"You can afford to miss {can_miss} more classes while maintaining your target",
                    "action": "maintain_current",
                    "priority": "low"
                })
        
        # Excellent performance
        elif subject.attendance_percentage >= 90:
            subject_recommendations.append({
                "type": "success",
                "message": "Excellent attendance! Keep up the good work.",
                "action": "continue",
                "priority": "low"
            })
        
        if subject_recommendations:
            recommendations.append({
                "subject_id": subject.id,
                "subject_name": subject.name,
                "current_percentage": subject.attendance_percentage,
                "recommendations": subject_recommendations
            })
    
    return jsonify({
        "recommendations": recommendations,
        "generated_at": datetime.utcnow().isoformat()
    })
