from flask import current_app
from models import db, Reminder, User
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

class NotificationService:
    """Service for handling notifications and reminders"""
    
    @staticmethod
    def send_email_notification(user_email, subject, message):
        """Send email notification"""
        try:
            if not current_app.config.get('MAIL_SERVER'):
                logging.warning("Email server not configured, skipping email notification")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = current_app.config['MAIL_USERNAME']
            msg['To'] = user_email
            msg['Subject'] = subject
            
            body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                    color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                            <h2 style="margin: 0;">📚 Smart Attendance Tracker</h2>
                        </div>
                        
                        <div style="background: #f9f9f9; padding: 20px; border-radius: 0 0 8px 8px;">
                            <h3 style="color: #667eea; margin-top: 0;">{subject}</h3>
                            <p style="font-size: 16px;">{message}</p>
                            
                            <div style="margin-top: 20px; padding: 15px; background: white; 
                                        border-left: 4px solid #667eea; border-radius: 4px;">
                                <p style="margin: 0; font-size: 14px; color: #666;">
                                    📱 Log in to your dashboard to take action or update your settings.
                                </p>
                            </div>
                        </div>
                        
                        <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #888;">
                            <p>Smart Attendance & Productivity Tracker</p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT'])
            server.starttls()
            server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
            
            text = msg.as_string()
            server.sendmail(current_app.config['MAIL_USERNAME'], user_email, text)
            server.quit()
            
            return True
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            return False
    
    @staticmethod
    def process_due_reminders():
        """Process all due reminders and send notifications"""
        now = datetime.utcnow()
        
        # Get all due reminders
        due_reminders = Reminder.query.filter(
            Reminder.reminder_time <= now,
            Reminder.sent == False,
            Reminder.active == True
        ).all()
        
        notifications_sent = 0
        
        for reminder in due_reminders:
            user = User.query.get(reminder.user_id)
            if user:
                # Create notification message
                subject = f"Reminder: {reminder.title}"
                message = reminder.message
                
                # Add context based on reminder type
                if reminder.reminder_type == "attendance":
                    message += "\\n\\n📝 Don't forget to mark your attendance after class!"
                elif reminder.reminder_type == "task" and reminder.task_id:
                    message += "\\n\\n✅ Check your task list to update progress."
                elif reminder.reminder_type == "exam":
                    message += "\\n\\n🎯 Good luck with your preparation!"
                
                # Send notification (email if configured, otherwise just log)
                if current_app.config.get('MAIL_SERVER'):
                    email_sent = NotificationService.send_email_notification(
                        user.email, subject, message
                    )
                    if email_sent:
                        notifications_sent += 1
                else:
                    logging.info(f"Notification for {user.email}: {subject} - {message}")
                    notifications_sent += 1
                
                # Mark reminder as sent
                reminder.sent = True
                
                # Handle recurrence
                if reminder.recurrence and reminder.recurrence != "none":
                    next_time = reminder.reminder_time
                    
                    if reminder.recurrence == "daily":
                        next_time += timedelta(days=1)
                    elif reminder.recurrence == "weekly":
                        next_time += timedelta(weeks=1)
                    elif reminder.recurrence == "monthly":
                        next_time += timedelta(days=30)  # Approximate month
                    
                    # Create new recurring reminder
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
        
        # Commit all changes
        if due_reminders:
            db.session.commit()
        
        return notifications_sent
    
    @staticmethod
    def create_attendance_reminder(user_id, subject_id, message, reminder_time):
        """Helper to create attendance-specific reminders"""
        reminder = Reminder(
            title="Attendance Reminder",
            message=message,
            reminder_time=reminder_time,
            reminder_type="attendance",
            subject_id=subject_id,
            user_id=user_id
        )
        
        db.session.add(reminder)
        db.session.commit()
        return reminder
    
    @staticmethod
    def create_task_reminder(user_id, task_id, reminder_time):
        """Helper to create task-specific reminders"""
        from models import Task
        task = Task.query.get(task_id)
        
        if task:
            reminder = Reminder(
                title=f"Task Due: {task.title}",
                message=f"Your task '{task.title}' is due soon. Don't forget to complete it!",
                reminder_time=reminder_time,
                reminder_type="task",
                task_id=task_id,
                user_id=user_id
            )
            
            db.session.add(reminder)
            db.session.commit()
            return reminder
        
        return None
    
    @staticmethod
    def get_browser_notification_data(user_id):
        """Get data formatted for browser notifications"""
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
        
        return notifications
    
    @staticmethod
    def create_attendance_warnings(user_id):
        """Create reminders for subjects with low attendance"""
        from models import Subject
        
        subjects = Subject.query.filter_by(user_id=user_id, is_archived=False).all()
        warnings_created = 0
        
        for subject in subjects:
            if subject.attendance_percentage < subject.target_percentage:
                # Create warning reminder for tomorrow
                tomorrow = datetime.utcnow() + timedelta(days=1)
                tomorrow = tomorrow.replace(hour=8, minute=0, second=0, microsecond=0)  # 8 AM
                
                message = (f"⚠️ Your {subject.name} attendance is {subject.attendance_percentage:.1f}%, "
                          f"which is below your {subject.target_percentage}% target. "
                          f"You need to attend the next {subject.classes_needed_for_target} classes to reach your goal.")
                
                # Check if similar reminder already exists
                existing = Reminder.query.filter(
                    Reminder.user_id == user_id,
                    Reminder.subject_id == subject.id,
                    Reminder.reminder_type == "attendance",
                    Reminder.reminder_time >= datetime.utcnow(),
                    Reminder.active == True
                ).first()
                
                if not existing:
                    reminder = Reminder(
                        title=f"Attendance Warning: {subject.name}",
                        message=message,
                        reminder_time=tomorrow,
                        reminder_type="attendance",
                        subject_id=subject.id,
                        user_id=user_id
                    )
                    
                    db.session.add(reminder)
                    warnings_created += 1
        
        if warnings_created > 0:
            db.session.commit()
        
        return warnings_created