from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Subject, AttendanceLog, Task, Reminder
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_, extract
import pandas as pd
from io import StringIO, BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import base64

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def get_dashboard_data():
    """Get comprehensive dashboard data"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Date ranges for analytics
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Attendance Overview
    subjects = Subject.query.filter_by(user_id=user_id, is_archived=False).all()
    total_subjects = len(subjects)
    total_classes = sum(s.total_classes for s in subjects)
    total_attended = sum(s.attended_classes for s in subjects)
    overall_percentage = (total_attended / total_classes * 100) if total_classes > 0 else 0
    
    # Subjects at risk (below 75%)
    at_risk_subjects = [s for s in subjects if s.attendance_percentage < 75]
    critical_subjects = [s for s in subjects if s.attendance_percentage < 60]
    
    # Recent attendance activity
    recent_logs = AttendanceLog.query.join(Subject).filter(
        Subject.user_id == user_id,
        AttendanceLog.date >= week_ago
    ).order_by(AttendanceLog.date.desc()).limit(10).all()
    
    # Task Statistics
    total_tasks = Task.query.filter_by(user_id=user_id).count()
    pending_tasks = Task.query.filter_by(user_id=user_id, completed=False).count()
    overdue_tasks = Task.query.filter(
        Task.user_id == user_id,
        Task.completed == False,
        Task.due_date.isnot(None),
        Task.due_date < datetime.utcnow()
    ).count()
    
    completed_this_week = Task.query.filter(
        Task.user_id == user_id,
        Task.completed == True,
        Task.completed_at >= datetime.combine(week_ago, datetime.min.time())
    ).count()
    
    # Due reminders
    due_reminders = Reminder.query.filter(
        Reminder.user_id == user_id,
        Reminder.reminder_time <= datetime.utcnow(),
        Reminder.sent == False,
        Reminder.active == True
    ).count()
    
    # Attendance trends (last 30 days)
    attendance_trend = []
    for i in range(30, 0, -1):
        check_date = today - timedelta(days=i)
        daily_logs = AttendanceLog.query.join(Subject).filter(
            Subject.user_id == user_id,
            AttendanceLog.date == check_date
        ).all()
        
        if daily_logs:
            present_count = len([log for log in daily_logs if log.status == "Present"])
            total_count = len(daily_logs)
            percentage = (present_count / total_count * 100) if total_count > 0 else 0
            
            attendance_trend.append({
                "date": check_date.isoformat(),
                "percentage": round(percentage, 2),
                "present": present_count,
                "total": total_count
            })
    
    # Weekly attendance distribution
    weekly_distribution = {}
    for i in range(7):  # Monday = 0, Sunday = 6
        day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][i]
        day_logs = AttendanceLog.query.join(Subject).filter(
            Subject.user_id == user_id,
            extract('dow', AttendanceLog.date) == (i + 1) % 7  # PostgreSQL style
        ).all()
        
        if day_logs:
            present_count = len([log for log in day_logs if log.status == "Present"])
            total_count = len(day_logs)
            percentage = (present_count / total_count * 100) if total_count > 0 else 0
            
            weekly_distribution[day_name.lower()] = {
                "percentage": round(percentage, 2),
                "present": present_count,
                "total": total_count
            }
    
    # Subject-wise performance for charts
    subject_performance = []
    for subject in subjects:
        subject_performance.append({
            "name": subject.name,
            "type": subject.type,
            "percentage": subject.attendance_percentage,
            "attended": subject.attended_classes,
            "total": subject.total_classes,
            "target": subject.target_percentage,
            "status": "good" if subject.attendance_percentage >= subject.target_percentage else "warning",
            "color": subject.color
        })
    
    # Upcoming items
    upcoming_tasks = Task.query.filter(
        Task.user_id == user_id,
        Task.completed == False,
        Task.due_date >= datetime.utcnow(),
        Task.due_date <= datetime.utcnow() + timedelta(days=7)
    ).order_by(Task.due_date).limit(5).all()
    
    upcoming_reminders = Reminder.query.filter(
        Reminder.user_id == user_id,
        Reminder.active == True,
        Reminder.reminder_time >= datetime.utcnow(),
        Reminder.reminder_time <= datetime.utcnow() + timedelta(days=7)
    ).order_by(Reminder.reminder_time).limit(5).all()
    
    return jsonify({
        "dashboard": {
            "user": user.to_dict(),
            "attendance_overview": {
                "total_subjects": total_subjects,
                "total_classes": total_classes,
                "total_attended": total_attended,
                "overall_percentage": round(overall_percentage, 2),
                "at_risk_count": len(at_risk_subjects),
                "critical_count": len(critical_subjects)
            },
            "task_overview": {
                "total_tasks": total_tasks,
                "pending_tasks": pending_tasks,
                "overdue_tasks": overdue_tasks,
                "completed_this_week": completed_this_week
            },
            "alerts": {
                "due_reminders": due_reminders,
                "at_risk_subjects": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "percentage": s.attendance_percentage,
                        "classes_needed": s.classes_needed_for_target
                    } for s in at_risk_subjects
                ],
                "overdue_tasks": overdue_tasks
            },
            "charts": {
                "attendance_trend": attendance_trend,
                "weekly_distribution": weekly_distribution,
                "subject_performance": subject_performance
            },
            "upcoming": {
                "tasks": [task.to_dict() for task in upcoming_tasks],
                "reminders": [reminder.to_dict() for reminder in upcoming_reminders]
            },
            "recent_activity": [
                {
                    "date": log.date.isoformat(),
                    "subject_name": log.subject.name,
                    "status": log.status,
                    "notes": log.notes
                } for log in recent_logs
            ]
        }
    })

@analytics_bp.route("/insights", methods=["GET"])
@jwt_required()
def get_insights():
    """Get AI-like insights and patterns from attendance data"""
    user_id = get_jwt_identity()
    
    subjects = Subject.query.filter_by(user_id=user_id, is_archived=False).all()
    insights = []
    
    # Pattern detection
    for subject in subjects:
        if subject.total_classes >= 10:  # Need sufficient data
            logs = AttendanceLog.query.filter_by(subject_id=subject.id)\
                .order_by(AttendanceLog.date.desc()).limit(20).all()
            
            if logs:
                # Analyze patterns
                recent_absences = [log for log in logs[:5] if log.status == "Absent"]
                streak_data = analyze_attendance_streak(logs)
                
                # Generate insights
                if len(recent_absences) >= 3:
                    insights.append({
                        "type": "warning",
                        "subject": subject.name,
                        "message": f"You've missed {len(recent_absences)} out of the last 5 {subject.name} classes",
                        "recommendation": "Consider attending the next few classes to improve your percentage",
                        "priority": "high"
                    })
                
                if streak_data["current_type"] == "Present" and streak_data["current_length"] >= 7:
                    insights.append({
                        "type": "achievement",
                        "subject": subject.name,
                        "message": f"Great job! You have a {streak_data['current_length']}-class attendance streak in {subject.name}",
                        "recommendation": "Keep up the excellent work!",
                        "priority": "low"
                    })
                
                # Weekly pattern analysis
                weekly_pattern = analyze_weekly_pattern(subject.id, user_id)
                if weekly_pattern["most_missed_day"]:
                    insights.append({
                        "type": "pattern",
                        "subject": subject.name,
                        "message": f"You tend to miss {subject.name} classes on {weekly_pattern['most_missed_day']}",
                        "recommendation": f"Set a reminder for {subject.name} on {weekly_pattern['most_missed_day']}s",
                        "priority": "medium"
                    })
    
    # Overall performance insights
    overall_percentage = sum(s.attendance_percentage * s.credits for s in subjects if s.credits) / sum(s.credits for s in subjects if s.credits) if subjects else 0
    
    if overall_percentage >= 90:
        insights.append({
            "type": "achievement",
            "subject": "Overall",
            "message": f"Outstanding! Your overall attendance is {overall_percentage:.1f}%",
            "recommendation": "You're on track for excellent academic performance",
            "priority": "low"
        })
    elif overall_percentage < 75:
        insights.append({
            "type": "warning",
            "subject": "Overall",
            "message": f"Your overall attendance ({overall_percentage:.1f}%) is below the typical requirement",
            "recommendation": "Focus on improving attendance in your weakest subjects",
            "priority": "high"
        })
    
    return jsonify({
        "insights": insights,
        "generated_at": datetime.utcnow().isoformat()
    })

def analyze_attendance_streak(logs):
    """Analyze attendance streak from logs"""
    if not logs:
        return {"current_type": None, "current_length": 0}
    
    current_status = logs[0].status
    current_length = 1
    
    for log in logs[1:]:
        if log.status == current_status:
            current_length += 1
        else:
            break
    
    return {
        "current_type": current_status,
        "current_length": current_length
    }

def analyze_weekly_pattern(subject_id, user_id):
    """Analyze weekly attendance patterns"""
    logs = AttendanceLog.query.join(Subject).filter(
        Subject.user_id == user_id,
        AttendanceLog.subject_id == subject_id
    ).all()
    
    day_stats = {}
    for i in range(7):
        day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][i]
        day_logs = [log for log in logs if log.date.weekday() == i]
        
        if day_logs:
            absent_count = len([log for log in day_logs if log.status == "Absent"])
            total_count = len(day_logs)
            absence_rate = (absent_count / total_count) if total_count > 0 else 0
            
            day_stats[day_name] = {
                "absence_rate": absence_rate,
                "total_classes": total_count,
                "absences": absent_count
            }
    
    # Find most missed day
    most_missed_day = None
    highest_rate = 0
    
    for day, stats in day_stats.items():
        if stats["absence_rate"] > highest_rate and stats["total_classes"] >= 3:  # Need at least 3 classes for pattern
            highest_rate = stats["absence_rate"]
            most_missed_day = day
    
    return {
        "most_missed_day": most_missed_day,
        "absence_rate": highest_rate,
        "day_stats": day_stats
    }

@analytics_bp.route("/export/csv", methods=["GET"])
@jwt_required()
def export_csv():
    """Export attendance data as CSV"""
    user_id = get_jwt_identity()
    export_type = request.args.get("type", "attendance")  # attendance, tasks, subjects
    
    if export_type == "attendance":
        # Export attendance logs
        logs = db.session.query(
            AttendanceLog.date,
            Subject.name.label('subject_name'),
            Subject.type.label('subject_type'),
            AttendanceLog.status,
            AttendanceLog.notes
        ).join(Subject).filter(Subject.user_id == user_id).all()
        
        df = pd.DataFrame(logs, columns=['Date', 'Subject', 'Type', 'Status', 'Notes'])
        
    elif export_type == "subjects":
        # Export subjects with statistics
        subjects = Subject.query.filter_by(user_id=user_id).all()
        
        data = []
        for subject in subjects:
            data.append({
                'Name': subject.name,
                'Type': subject.type,
                'Total Classes': subject.total_classes,
                'Attended Classes': subject.attended_classes,
                'Attendance Percentage': subject.attendance_percentage,
                'Target Percentage': subject.target_percentage,
                'Classes Needed': subject.classes_needed_for_target,
                'Credits': subject.credits,
                'Semester': subject.semester
            })
        
        df = pd.DataFrame(data)
        
    elif export_type == "tasks":
        # Export tasks
        tasks = Task.query.filter_by(user_id=user_id).all()
        
        data = []
        for task in tasks:
            data.append({
                'Title': task.title,
                'Description': task.description,
                'Due Date': task.due_date.isoformat() if task.due_date else '',
                'Completed': task.completed,
                'Priority': task.priority,
                'Category': task.category,
                'Created At': task.created_at.isoformat(),
                'Completed At': task.completed_at.isoformat() if task.completed_at else ''
            })
        
        df = pd.DataFrame(data)
    
    else:
        return jsonify({"error": "Invalid export type"}), 400
    
    # Convert to CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    
    # Encode as base64 for safe transport
    csv_base64 = base64.b64encode(csv_data.encode()).decode()
    
    return jsonify({
        "filename": f"{export_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "data": csv_base64,
        "mime_type": "text/csv"
    })

@analytics_bp.route("/export/pdf", methods=["GET"])
@jwt_required()
def export_pdf():
    """Export attendance report as PDF"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    story.append(Paragraph("Attendance Report", title_style))
    story.append(Spacer(1, 20))
    
    # User info
    story.append(Paragraph(f"<b>Student:</b> {user.name}", styles['Normal']))
    story.append(Paragraph(f"<b>Email:</b> {user.email}", styles['Normal']))
    story.append(Paragraph(f"<b>Report Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Overall statistics
    subjects = Subject.query.filter_by(user_id=user_id, is_archived=False).all()
    total_classes = sum(s.total_classes for s in subjects)
    total_attended = sum(s.attended_classes for s in subjects)
    overall_percentage = (total_attended / total_classes * 100) if total_classes > 0 else 0
    
    story.append(Paragraph("<b>Overall Statistics</b>", styles['Heading2']))
    
    overall_data = [
        ['Metric', 'Value'],
        ['Total Subjects', str(len(subjects))],
        ['Total Classes', str(total_classes)],
        ['Classes Attended', str(total_attended)],
        ['Overall Percentage', f"{overall_percentage:.2f}%"]
    ]
    
    overall_table = Table(overall_data)
    overall_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(overall_table)
    story.append(Spacer(1, 20))
    
    # Subject-wise breakdown
    story.append(Paragraph("<b>Subject-wise Breakdown</b>", styles['Heading2']))
    
    subject_data = [['Subject', 'Type', 'Attended/Total', 'Percentage', 'Status']]
    
    for subject in subjects:
        status = "✓ Good" if subject.attendance_percentage >= subject.target_percentage else "⚠ Below Target"
        subject_data.append([
            subject.name,
            subject.type.title(),
            f"{subject.attended_classes}/{subject.total_classes}",
            f"{subject.attendance_percentage:.1f}%",
            status
        ])
    
    subject_table = Table(subject_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch, 1.5*inch])
    subject_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))
    
    story.append(subject_table)
    story.append(Spacer(1, 20))
    
    # Recommendations
    story.append(Paragraph("<b>Recommendations</b>", styles['Heading2']))
    
    below_target = [s for s in subjects if s.attendance_percentage < s.target_percentage]
    
    if below_target:
        for subject in below_target:
            story.append(Paragraph(
                f"• <b>{subject.name}</b>: Attend the next {subject.classes_needed_for_target} classes to reach {subject.target_percentage}% target",
                styles['Normal']
            ))
    else:
        story.append(Paragraph("• Excellent work! All subjects meet the attendance requirements.", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF data
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()
    
    # Encode as base64
    pdf_base64 = base64.b64encode(pdf_data).decode()
    
    return jsonify({
        "filename": f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        "data": pdf_base64,
        "mime_type": "application/pdf"
    })