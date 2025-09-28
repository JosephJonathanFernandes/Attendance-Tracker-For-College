# Smart Attendance & Productivity Tracker - API Documentation

## 🎯 Overview

A comprehensive Flask REST API for managing attendance, tasks, and reminders with advanced analytics and insights.

## 🚀 Features

- **User Authentication**: JWT-based secure authentication
- **Attendance Management**: Mark attendance, view statistics, track percentages
- **Task Management**: Create, manage, and track tasks with priorities
- **Reminders**: Smart notifications and recurring reminders
- **Analytics Dashboard**: Comprehensive insights and predictions
- **Export Functionality**: CSV and PDF export capabilities
- **Smart Calculations**: 75% threshold warnings, classes needed calculator

## 📊 Base URL

```
http://localhost:5000/api
```

## 🔐 Authentication

All endpoints (except registration and login) require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

---

## 👤 Authentication Endpoints

### Register User
**POST** `/auth/register`

```json
{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepassword123"
}
```

### Login User
**POST** `/auth/login`

```json
{
    "email": "john@example.com",
    "password": "securepassword123"
}
```

---

## 📚 Subjects API

### Create Subject
**POST** `/subjects/`

```json
{
    "name": "Data Structures",
    "type": "theory",
    "target_percentage": 75.0,
    "color": "#007bff",
    "credits": 4,
    "semester": "Fall 2025"
}
```

### Get All Subjects
**GET** `/subjects/`

Query parameters:
- `include_archived`: boolean (default: false)
- `type`: theory|lab|tutorial|practical
- `semester`: string

### Get Subject Analytics
**GET** `/subjects/analytics`

Returns comprehensive analytics for all subjects including:
- Overall statistics
- Performance categories (excellent, good, warning, critical)
- Type-wise breakdown
- Action items for improvement

### Get Attendance Predictions
**GET** `/subjects/predictions`

Returns predictions based on different attendance scenarios.

### Get Recommendations
**GET** `/subjects/recommendations`

Returns personalized recommendations for improving attendance.

---

## 📋 Attendance API

### Mark Attendance
**POST** `/attendance/mark`

```json
{
    "subject_id": 1,
    "status": "Present",
    "date": "2025-09-28",
    "notes": "Optional notes"
}
```

### Get Attendance Summary
**GET** `/attendance/summary`

Returns overall attendance summary for all subjects.

### Get Subject Statistics
**GET** `/attendance/stats/{subject_id}`

Returns detailed statistics for a specific subject including:
- Total and present counts
- Attendance percentage
- Recent attendance history
- Current streak information

### Update Attendance
**PUT** `/attendance/update/{log_id}`

```json
{
    "status": "Absent",
    "date": "2025-09-28",
    "notes": "Updated notes"
}
```

---

## ✅ Tasks API

### Create Task
**POST** `/tasks/`

```json
{
    "title": "Complete Assignment 1",
    "description": "Data Structures assignment on linked lists",
    "due_date": "2025-10-15T23:59:59",
    "priority": "high",
    "category": "assignment",
    "estimated_hours": 5,
    "subject_id": 1
}
```

### Get Tasks with Filtering
**GET** `/tasks/`

Query parameters:
- `completed`: boolean
- `priority`: low|medium|high|urgent
- `category`: string
- `subject_id`: integer
- `overdue_only`: boolean
- `sort_by`: created_at|updated_at|due_date|priority|title
- `sort_order`: asc|desc

### Bulk Update Tasks
**PUT** `/tasks/bulk`

```json
{
    "task_ids": [1, 2, 3],
    "completed": true,
    "priority": "high"
}
```

### Get Task Statistics
**GET** `/tasks/statistics`

Returns comprehensive task analytics including:
- Total, completed, and pending counts
- Overdue tasks
- Priority and category breakdowns
- Completion rate

### Get Upcoming Tasks
**GET** `/tasks/upcoming`

Returns tasks due in the next 7 days, grouped by day.

---

## 🔔 Reminders API

### Create Reminder
**POST** `/reminders/`

```json
{
    "title": "Study Session",
    "message": "Time to study for Data Structures exam",
    "reminder_time": "2025-09-29T14:00:00",
    "reminder_type": "exam",
    "recurrence": "weekly",
    "subject_id": 1
}
```

### Get Due Reminders
**GET** `/reminders/due`

Returns all reminders that are due for notification.

### Mark Reminder as Sent
**POST** `/reminders/{reminder_id}/mark-sent`

Marks a reminder as sent and creates recurring reminders if applicable.

### Bulk Create Reminders
**POST** `/reminders/bulk-create`

```json
{
    "reminders": [
        {
            "title": "Weekly Review",
            "message": "Review this week's topics",
            "reminder_time": "2025-09-29T18:00:00"
        }
    ]
}
```

---

## 📊 Analytics API

### Get Dashboard Data
**GET** `/analytics/dashboard`

Returns comprehensive dashboard data including:
- Attendance overview
- Task statistics
- Alerts and warnings
- Charts data (trends, weekly distribution)
- Upcoming items
- Recent activity

### Get AI Insights
**GET** `/analytics/insights`

Returns intelligent insights and patterns including:
- Attendance streak analysis
- Weekly pattern detection
- Performance achievements
- Recommendations for improvement

---

## 📤 Export API

### Export to CSV
**GET** `/analytics/export/csv?type={type}`

Types: `attendance`, `subjects`, `tasks`

Returns base64-encoded CSV data.

### Export to PDF
**GET** `/analytics/export/pdf`

Returns base64-encoded PDF attendance report with:
- Overall statistics
- Subject-wise breakdown
- Recommendations

---

## 🧮 Smart Calculations

The API automatically calculates:

1. **Attendance Percentage**: `(attended_classes / total_classes) * 100`
2. **Classes Needed for Target**: Formula to reach target percentage
3. **Can Afford to Miss**: Maximum classes that can be missed while maintaining target
4. **Predictions**: Future attendance scenarios
5. **Weekly Patterns**: Day-wise attendance analysis
6. **Streaks**: Consecutive attendance/absence tracking

---

## 📱 Frontend Integration Examples

### React Hook for Dashboard
```javascript
const useDashboard = () => {
  const [dashboard, setDashboard] = useState(null);
  
  useEffect(() => {
    fetch('/api/analytics/dashboard', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => setDashboard(data.dashboard));
  }, []);
  
  return dashboard;
};
```

### Chart.js Integration
```javascript
const AttendanceChart = ({ data }) => {
  const chartData = {
    labels: data.subject_performance.map(s => s.name),
    datasets: [{
      data: data.subject_performance.map(s => s.percentage),
      backgroundColor: data.subject_performance.map(s => s.color)
    }]
  };
  
  return <Doughnut data={chartData} />;
};
```

---

## 🔧 Error Handling

All endpoints return consistent error responses:

```json
{
    "error": "Error description",
    "code": "ERROR_CODE",
    "details": {}
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `500`: Server Error

---

## 🌐 CORS Configuration

The API supports CORS for frontend integration. Configure allowed origins in the environment variables.

---

## 🔒 Security Features

- JWT token authentication
- Password hashing with Werkzeug
- SQL injection prevention with SQLAlchemy ORM
- Input validation and sanitization
- Rate limiting ready (can be added with Flask-Limiter)

---

## 🚀 Deployment Ready

The API is production-ready with:
- Environment variable configuration
- Database migrations support
- Error logging
- Security headers
- Scalable architecture

---

## 📈 Performance Optimizations

- Database indexing on foreign keys
- Pagination for large datasets
- Efficient SQL queries with joins
- JSON responses optimized for frontend consumption
- Caching ready (Redis can be integrated)