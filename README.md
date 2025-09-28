# 📚 Attendance Tracker For College

A comprehensive full-stack web application designed to help college students track their attendance, manage tasks, set reminders, and analyze their academic performance.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![React](https://img.shields.io/badge/react-v18+-blue.svg)
![Flask](https://img.shields.io/badge/flask-v2.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🌟 Features

### 📊 Attendance Management
- Track attendance for multiple subjects
- View attendance percentage and statistics
- Set minimum attendance thresholds
- Visual attendance calendar

### 📝 Task Management
- Create and manage academic tasks
- Set due dates and priorities
- Task completion tracking
- Category-based task organization

### ⏰ Reminders & Notifications
- Smart reminder system for classes and tasks
- Customizable notification preferences
- Email and in-app notifications
- Recurring reminders

### 📈 Analytics & Insights
- Detailed attendance analytics
- Performance trends and insights
- Subject-wise statistics
- Progress tracking charts

### 📅 Calendar Integration
- Academic calendar view
- Class schedule management
- Important dates tracking
- Event synchronization

## 🏗️ Project Structure

```
attendance-tracker/
├── attendance-tracker-backend/     # Flask REST API
│   ├── routes/                    # API endpoints
│   ├── models.py                  # Database models
│   ├── config.py                  # Configuration settings
│   ├── app.py                     # Main application file
│   └── requirements.txt           # Python dependencies
├── attendance-tracker-frontend/    # React frontend
│   ├── src/
│   │   ├── components/           # Reusable components
│   │   ├── pages/               # Main pages
│   │   ├── services/            # API services
│   │   └── utils/               # Utility functions
│   ├── package.json             # Node.js dependencies
│   └── vite.config.js          # Vite configuration
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **npm or yarn**
- **SQLite** (default) or **PostgreSQL**

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd attendance-tracker-backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables:**
   ```bash
   # Create a .env file in the backend directory
   DATABASE_URL=sqlite:///attendance.db
   JWT_SECRET_KEY=your-secret-key-here
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   ```

6. **Initialize the database:**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

7. **Run the backend server:**
   ```bash
   python app.py
   ```

The backend will be available at `http://localhost:5000`

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd attendance-tracker-frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create environment file:**
   ```bash
   # Create a .env file in the frontend directory
   VITE_API_URL=http://localhost:5000
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173`

## 🔧 Configuration

### Backend Configuration

The backend configuration can be modified in `config.py`:

- **Database URL**: Configure your database connection
- **JWT Settings**: Set JWT secret key and expiration
- **Email Settings**: Configure SMTP settings for notifications
- **CORS Settings**: Configure allowed origins

### Frontend Configuration

The frontend configuration uses Vite and can be customized in `vite.config.js`:

- **API Endpoint**: Set the backend API URL
- **Build Settings**: Configure build optimization
- **Development Server**: Configure dev server settings

## 📱 API Documentation

The API documentation is available in the `API_DOCUMENTATION.md` file in the backend directory. Key endpoints include:

- **Authentication**: `/api/auth/`
- **Subjects**: `/api/subjects/`
- **Attendance**: `/api/attendance/`
- **Tasks**: `/api/tasks/`
- **Reminders**: `/api/reminders/`
- **Analytics**: `/api/analytics/`
- **Calendar**: `/api/calendar/`

## 🧪 Testing

### Backend Testing
```bash
cd attendance-tracker-backend
python -m pytest tests/
```

### Frontend Testing
```bash
cd attendance-tracker-frontend
npm test
```

## 🚀 Deployment

### Backend Deployment (Heroku)
```bash
# Install Heroku CLI and login
heroku create your-app-name-backend
git subtree push --prefix attendance-tracker-backend heroku main
```

### Frontend Deployment (Vercel/Netlify)
```bash
cd attendance-tracker-frontend
npm run build
# Deploy dist/ folder to your preferred hosting service
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Joseph Jonathan Fernandes**
- GitHub: [@JosephJonathanFernandes](https://github.com/JosephJonathanFernandes)
- Email: [your-email@example.com](mailto:your-email@example.com)

## 🙏 Acknowledgments

- Flask community for the excellent web framework
- React team for the amazing frontend library
- All contributors who helped improve this project

## 📞 Support

If you have any questions or need help with setup, please:

1. Check the [Issues](https://github.com/JosephJonathanFernandes/Attendance-Tracker-For-College/issues) page
2. Create a new issue if your problem isn't already reported
3. Contact the maintainer directly

## 🔮 Future Enhancements

- [ ] Mobile app development (React Native)
- [ ] Advanced analytics with ML predictions
- [ ] Integration with university management systems
- [ ] Offline mode support
- [ ] Multi-language support
- [ ] Dark/Light theme toggle
- [ ] Bulk attendance import from CSV
- [ ] Advanced reporting features

---

⭐ **If this project helped you, please give it a star!** ⭐