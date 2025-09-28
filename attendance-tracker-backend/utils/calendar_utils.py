from datetime import datetime, date, timedelta
import calendar
import pytz
from typing import List, Dict, Any

class CalendarUtils:
    """Utility functions for calendar and date operations"""
    
    @staticmethod
    def get_academic_calendar(year: int = None) -> Dict[str, Any]:
        """Generate academic calendar with typical semester dates"""
        if year is None:
            year = datetime.now().year
        
        # Typical academic calendar (can be customized)
        academic_calendar = {
            "year": year,
            "fall_semester": {
                "start": date(year, 8, 15),  # Mid August
                "end": date(year, 12, 15),   # Mid December
                "midterm_week": {
                    "start": date(year, 10, 1),
                    "end": date(year, 10, 8)
                },
                "finals_week": {
                    "start": date(year, 12, 8),
                    "end": date(year, 12, 15)
                }
            },
            "spring_semester": {
                "start": date(year + 1, 1, 15),  # Mid January
                "end": date(year + 1, 5, 15),    # Mid May
                "midterm_week": {
                    "start": date(year + 1, 3, 1),
                    "end": date(year + 1, 3, 8)
                },
                "finals_week": {
                    "start": date(year + 1, 5, 8),
                    "end": date(year + 1, 5, 15)
                }
            },
            "summer_semester": {
                "start": date(year + 1, 6, 1),   # June
                "end": date(year + 1, 7, 31),    # July
            }
        }
        
        return academic_calendar
    
    @staticmethod
    def get_holidays(year: int = None) -> List[Dict[str, Any]]:
        """Get common academic holidays"""
        if year is None:
            year = datetime.now().year
        
        holidays = [
            {"name": "New Year's Day", "date": date(year, 1, 1)},
            {"name": "Martin Luther King Jr. Day", "date": CalendarUtils._get_nth_weekday(year, 1, 0, 3)},  # 3rd Monday in January
            {"name": "Presidents' Day", "date": CalendarUtils._get_nth_weekday(year, 2, 0, 3)},  # 3rd Monday in February
            {"name": "Memorial Day", "date": CalendarUtils._get_last_weekday(year, 5, 0)},  # Last Monday in May
            {"name": "Independence Day", "date": date(year, 7, 4)},
            {"name": "Labor Day", "date": CalendarUtils._get_nth_weekday(year, 9, 0, 1)},  # 1st Monday in September
            {"name": "Thanksgiving", "date": CalendarUtils._get_nth_weekday(year, 11, 3, 4)},  # 4th Thursday in November
            {"name": "Christmas Day", "date": date(year, 12, 25)},
        ]
        
        return holidays
    
    @staticmethod
    def _get_nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
        """Get the nth occurrence of a weekday in a month"""
        first_day = date(year, month, 1)
        first_weekday = first_day.weekday()
        
        # Calculate days until the desired weekday
        days_ahead = weekday - first_weekday
        if days_ahead < 0:
            days_ahead += 7
        
        # Get the first occurrence
        first_occurrence = first_day + timedelta(days=days_ahead)
        
        # Get the nth occurrence
        nth_occurrence = first_occurrence + timedelta(weeks=(n-1))
        
        return nth_occurrence
    
    @staticmethod
    def _get_last_weekday(year: int, month: int, weekday: int) -> date:
        """Get the last occurrence of a weekday in a month"""
        # Start with the last day of the month
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        
        # Find the last occurrence of the weekday
        days_back = (last_day.weekday() - weekday) % 7
        last_weekday = last_day - timedelta(days=days_back)
        
        return last_weekday
    
    @staticmethod
    def is_academic_day(check_date: date, exclude_weekends: bool = True, 
                       exclude_holidays: bool = True) -> bool:
        """Check if a date is a regular academic day"""
        # Check weekends
        if exclude_weekends and check_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Check holidays
        if exclude_holidays:
            holidays = CalendarUtils.get_holidays(check_date.year)
            holiday_dates = [h["date"] for h in holidays]
            if check_date in holiday_dates:
                return False
        
        return True
    
    @staticmethod
    def get_academic_weeks(start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get academic weeks between two dates"""
        weeks = []
        current_date = start_date
        week_number = 1
        
        # Start from the Monday of the first week
        days_since_monday = current_date.weekday()
        week_start = current_date - timedelta(days=days_since_monday)
        
        while week_start <= end_date:
            week_end = week_start + timedelta(days=6)  # Sunday
            
            # Count academic days in this week
            academic_days = []
            for i in range(7):
                day = week_start + timedelta(days=i)
                if day >= start_date and day <= end_date:
                    if CalendarUtils.is_academic_day(day):
                        academic_days.append({
                            "date": day,
                            "day_name": day.strftime("%A"),
                            "is_holiday": False
                        })
            
            if academic_days:  # Only add weeks with academic days
                weeks.append({
                    "week_number": week_number,
                    "start_date": week_start,
                    "end_date": week_end,
                    "academic_days": academic_days,
                    "total_academic_days": len(academic_days)
                })
                week_number += 1
            
            week_start += timedelta(weeks=1)
        
        return weeks
    
    @staticmethod
    def get_attendance_calendar(user_id: int, year: int = None, month: int = None) -> Dict[str, Any]:
        """Generate attendance calendar for a user"""
        from models import AttendanceLog, Subject
        
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
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
                        "is_holiday": not CalendarUtils.is_academic_day(day_date, exclude_weekends=False, exclude_holidays=True),
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
            "weeks": calendar_weeks,
            "holidays": [h for h in CalendarUtils.get_holidays(year) if h["date"].month == month]
        }
    
    @staticmethod
    def convert_timezone(dt: datetime, from_tz: str = "UTC", to_tz: str = "UTC") -> datetime:
        """Convert datetime between timezones"""
        from_timezone = pytz.timezone(from_tz)
        to_timezone = pytz.timezone(to_tz)
        
        # If datetime is naive, assume it's in from_tz
        if dt.tzinfo is None:
            dt = from_timezone.localize(dt)
        else:
            dt = dt.astimezone(from_timezone)
        
        return dt.astimezone(to_timezone)
    
    @staticmethod
    def get_semester_progress(start_date: date, end_date: date, current_date: date = None) -> Dict[str, Any]:
        """Calculate semester progress"""
        if current_date is None:
            current_date = date.today()
        
        total_days = (end_date - start_date).days + 1
        elapsed_days = max(0, (current_date - start_date).days + 1)
        remaining_days = max(0, (end_date - current_date).days)
        
        progress_percentage = min(100, (elapsed_days / total_days) * 100) if total_days > 0 else 0
        
        # Get academic days
        academic_weeks = CalendarUtils.get_academic_weeks(start_date, end_date)
        total_academic_days = sum(week["total_academic_days"] for week in academic_weeks)
        
        elapsed_academic_days = sum(
            len([day for day in week["academic_days"] if day["date"] <= current_date])
            for week in academic_weeks
        )
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "current_date": current_date,
            "total_days": total_days,
            "elapsed_days": elapsed_days,
            "remaining_days": remaining_days,
            "progress_percentage": round(progress_percentage, 2),
            "total_academic_days": total_academic_days,
            "elapsed_academic_days": elapsed_academic_days,
            "remaining_academic_days": total_academic_days - elapsed_academic_days,
            "weeks_completed": len([w for w in academic_weeks if w["end_date"] <= current_date]),
            "total_weeks": len(academic_weeks)
        }
    
    @staticmethod
    def suggest_study_schedule(tasks: List[Dict[str, Any]], available_hours_per_day: int = 4) -> List[Dict[str, Any]]:
        """Suggest an optimal study schedule based on tasks and available time"""
        schedule = []
        current_date = datetime.now().date()
        
        # Sort tasks by due date and priority
        sorted_tasks = sorted(tasks, key=lambda x: (
            datetime.fromisoformat(x["due_date"]).date() if x["due_date"] else date.max,
            {"urgent": 0, "high": 1, "medium": 2, "low": 3}.get(x["priority"], 2)
        ))
        
        for task in sorted_tasks:
            if task["completed"]:
                continue
                
            due_date = datetime.fromisoformat(task["due_date"]).date() if task["due_date"] else None
            estimated_hours = task.get("estimated_hours", 2)
            
            if due_date and due_date > current_date:
                days_available = (due_date - current_date).days
                daily_hours_needed = estimated_hours / max(1, days_available)
                
                schedule.append({
                    "task_id": task["id"],
                    "task_title": task["title"],
                    "due_date": due_date,
                    "estimated_hours": estimated_hours,
                    "days_available": days_available,
                    "daily_hours_needed": round(daily_hours_needed, 2),
                    "urgency": "high" if daily_hours_needed > available_hours_per_day * 0.8 else 
                             "medium" if daily_hours_needed > available_hours_per_day * 0.4 else "low"
                })
        
        return schedule