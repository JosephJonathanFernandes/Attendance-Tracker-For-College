# Contributing to Attendance Tracker For College

First off, thank you for considering contributing to the Attendance Tracker For College! It's people like you that make this project a great tool for students everywhere.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Workflow](#development-workflow)
- [Style Guidelines](#style-guidelines)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)

## 📜 Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please be respectful, inclusive, and considerate in all interactions.

## 🚀 Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.8+**
- **Node.js 16+**
- **Git**
- **A GitHub account**

### Development Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/Attendance-Tracker-For-College.git
   cd Attendance-Tracker-For-College
   ```
3. **Set up the backend** (follow README.md instructions)
4. **Set up the frontend** (follow README.md instructions)
5. **Create a new branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🤝 How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior** vs **actual behavior**
- **Screenshots** if applicable
- **Environment details** (OS, browser, versions)
- **Error messages** or console logs

### 💡 Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- **Clear title and description**
- **Use case** and **motivation**
- **Detailed explanation** of the proposed feature
- **Mockups or examples** if applicable

### 🔧 Code Contributions

We welcome code contributions for:

- **Bug fixes**
- **New features**
- **Performance improvements**
- **Documentation improvements**
- **Test coverage improvements**

## 🔄 Development Workflow

### Backend Development

1. **Navigate to backend directory:**
   ```bash
   cd attendance-tracker-backend
   ```

2. **Activate virtual environment:**
   ```bash
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run tests:**
   ```bash
   python -m pytest tests/ -v
   ```

5. **Start development server:**
   ```bash
   python app.py
   ```

### Frontend Development

1. **Navigate to frontend directory:**
   ```bash
   cd attendance-tracker-frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run tests:**
   ```bash
   npm test
   ```

4. **Start development server:**
   ```bash
   npm run dev
   ```

## 🎨 Style Guidelines

### Python (Backend)

- Follow **PEP 8** style guide
- Use **meaningful variable names**
- Add **docstrings** for functions and classes
- Keep **functions small** and focused
- Use **type hints** where appropriate

Example:
```python
def calculate_attendance_percentage(present_days: int, total_days: int) -> float:
    """
    Calculate attendance percentage.
    
    Args:
        present_days (int): Number of days present
        total_days (int): Total number of days
        
    Returns:
        float: Attendance percentage
    """
    if total_days == 0:
        return 0.0
    return (present_days / total_days) * 100
```

### JavaScript/React (Frontend)

- Use **ES6+ features**
- Follow **React best practices**
- Use **meaningful component names**
- Keep **components small** and reusable
- Use **JSX** properly

Example:
```jsx
import React from 'react';

const AttendanceCard = ({ subject, percentage, status }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'good': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'danger': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="text-lg font-semibold">{subject}</h3>
      <p className={`text-2xl font-bold ${getStatusColor(status)}`}>
        {percentage}%
      </p>
    </div>
  );
};

export default AttendanceCard;
```

### Commit Messages

Use clear and descriptive commit messages:

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

Example:
```
feat: add attendance percentage calculation API endpoint

- Implement calculate_attendance_percentage function
- Add new route /api/attendance/percentage
- Include input validation and error handling
- Add unit tests for percentage calculation

Fixes #123
```

## 🧪 Testing

### Backend Testing

```bash
cd attendance-tracker-backend
python -m pytest tests/ -v --coverage
```

### Frontend Testing

```bash
cd attendance-tracker-frontend
npm test
npm run test:coverage
```

### Writing Tests

- **Write tests** for new features
- **Update tests** when modifying existing code
- **Maintain high test coverage** (aim for 80%+)
- **Test edge cases** and error conditions

## 📝 Pull Request Process

1. **Ensure your branch is up to date:**
   ```bash
   git checkout main
   git pull upstream main
   git checkout your-feature-branch
   git rebase main
   ```

2. **Run tests** and ensure they pass
3. **Update documentation** if needed
4. **Create a pull request** with:
   - **Clear title and description**
   - **Reference related issues**
   - **Screenshots** for UI changes
   - **Testing instructions**

### Pull Request Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

## 📂 Project Structure Guidelines

### Backend Structure
```
attendance-tracker-backend/
├── routes/          # API endpoints
├── models.py        # Database models
├── config.py        # Configuration
├── utils.py         # Utility functions
├── services/        # Business logic
├── tests/          # Test files
└── requirements.txt # Dependencies
```

### Frontend Structure
```
attendance-tracker-frontend/
├── src/
│   ├── components/  # Reusable components
│   ├── pages/      # Page components
│   ├── services/   # API services
│   ├── utils/      # Utility functions
│   ├── context/    # React contexts
│   └── hooks/      # Custom hooks
├── public/         # Static files
└── tests/         # Test files
```

## 🚫 What NOT to Contribute

- **Incomplete features** without tests
- **Breaking changes** without discussion
- **Large refactors** without prior approval
- **Code style changes** without functional improvements
- **Dependencies** without justification

## 💬 Getting Help

If you need help or have questions:

1. **Check existing documentation**
2. **Search existing issues**
3. **Ask in discussions** (if available)
4. **Create an issue** with your question
5. **Contact maintainers** directly

## 🎉 Recognition

Contributors will be recognized in:

- **README.md** contributors section
- **Release notes** for significant contributions
- **GitHub contributors** page

Thank you for contributing to make this project better! 🙏

---

**Happy Coding!** 🚀