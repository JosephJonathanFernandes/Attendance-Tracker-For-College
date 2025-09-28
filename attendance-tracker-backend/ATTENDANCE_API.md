# Attendance API Documentation

## Overview
Complete attendance management system with marking, updating, statistics calculation, and reporting functionality.

## Authentication
All endpoints require JWT authentication. Include the JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. Mark Attendance
**POST** `/api/attendance/mark`

Mark attendance for a specific subject.

**Request Body:**
```json
{
    "subject_id": 1,
    "status": "Present",  // "Present" or "Absent"
    "date": "2025-09-28"  // Optional, defaults to today
}
```

**Response (201):**
```json
{
    "message": "Attendance marked successfully",
    "attendance_log": {
        "id": 1,
        "date": "2025-09-28",
        "status": "Present",
        "subject_id": 1
    },
    "subject_stats": {
        "total_classes": 10,
        "attended_classes": 8,
        "attendance_percentage": 80.0
    }
}
```

**Error Cases:**
- `400`: Missing required fields, invalid status, or attendance already marked for today
- `404`: Subject not found

---

### 2. Get Attendance Logs
**GET** `/api/attendance/logs/<subject_id>`

Retrieve paginated attendance history for a specific subject.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Records per page (default: 20)

**Response (200):**
```json
{
    "logs": [
        {
            "id": 1,
            "date": "2025-09-28",
            "status": "Present",
            "subject_id": 1
        }
    ],
    "pagination": {
        "page": 1,
        "per_page": 20,
        "total": 50,
        "pages": 3,
        "has_next": true,
        "has_prev": false
    },
    "subject": {
        "id": 1,
        "name": "Mathematics",
        "type": "theory"
    }
}
```

---

### 3. Update Attendance
**PUT** `/api/attendance/update/<log_id>`

Update an existing attendance record.

**Request Body:**
```json
{
    "status": "Absent",      // Optional
    "date": "2025-09-27"     // Optional, format: YYYY-MM-DD
}
```

**Response (200):**
```json
{
    "message": "Attendance updated successfully",
    "attendance_log": {
        "id": 1,
        "date": "2025-09-27",
        "status": "Absent",
        "subject_id": 1
    },
    "subject_stats": {
        "total_classes": 10,
        "attended_classes": 7,
        "attendance_percentage": 70.0
    }
}
```

---

### 4. Get Attendance Statistics
**GET** `/api/attendance/stats/<subject_id>`

Get detailed attendance statistics for a subject.

**Response (200):**
```json
{
    "subject": {
        "id": 1,
        "name": "Mathematics",
        "type": "theory"
    },
    "statistics": {
        "total_classes": 20,
        "present_count": 16,
        "absent_count": 4,
        "attendance_percentage": 80.0,
        "absence_percentage": 20.0,
        "current_streak": {
            "count": 3,
            "type": "Present"
        }
    },
    "recent_attendance": [
        {
            "date": "2025-09-28",
            "status": "Present"
        }
    ]
}
```

---

### 5. Delete Attendance Record
**DELETE** `/api/attendance/<log_id>`

Remove an attendance record and update subject counters.

**Response (200):**
```json
{
    "message": "Attendance record deleted successfully",
    "subject_stats": {
        "total_classes": 9,
        "attended_classes": 7,
        "attendance_percentage": 77.78
    }
}
```

---

### 6. Get Attendance Summary
**GET** `/api/attendance/summary`

Get overall attendance summary for all user's subjects.

**Response (200):**
```json
{
    "subjects": [
        {
            "id": 1,
            "name": "Mathematics",
            "type": "theory",
            "total_classes": 20,
            "attended_classes": 16,
            "attendance_percentage": 80.0,
            "last_attendance": {
                "date": "2025-09-28",
                "status": "Present"
            }
        }
    ],
    "overall_stats": {
        "total_classes": 60,
        "attended_classes": 45,
        "attendance_percentage": 75.0,
        "total_subjects": 3
    }
}
```

## Features

### ✅ Implemented Features:
1. **Mark Attendance**: Record daily attendance with Present/Absent status
2. **View History**: Paginated attendance logs with filtering
3. **Update Records**: Modify existing attendance entries
4. **Statistics**: Detailed attendance analytics including:
   - Attendance percentage
   - Present/Absent counts
   - Current streak tracking
   - Recent attendance history
5. **Delete Records**: Remove attendance entries with automatic counter updates
6. **Summary Dashboard**: Overview of all subjects' attendance
7. **Automatic Counters**: Real-time updates to subject statistics
8. **Date Validation**: Proper date handling and validation
9. **Duplicate Prevention**: Prevents marking attendance twice for the same day
10. **User Isolation**: JWT-based access control ensuring users only see their data

### 📊 Calculated Metrics:
- **Attendance Percentage**: (Present classes / Total classes) × 100
- **Absence Percentage**: (Absent classes / Total classes) × 100  
- **Current Streak**: Consecutive present/absent days
- **Overall Statistics**: Aggregated data across all subjects

### 🔒 Security Features:
- JWT token validation on all endpoints
- User ownership verification for all operations
- Input validation and sanitization
- Proper error handling with appropriate HTTP status codes

## Usage Examples

### Mark Today's Attendance
```bash
curl -X POST http://localhost:5000/api/attendance/mark \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"subject_id": 1, "status": "Present"}'
```

### Get Subject Statistics
```bash
curl -X GET http://localhost:5000/api/attendance/stats/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Update Attendance Record
```bash
curl -X PUT http://localhost:5000/api/attendance/update/5 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "Absent"}'
```