# Online Examination System

## Introduction
The Online Examination System is a digital platform designed to simplify the examination process, allowing students to take exams from anywhere at any time. It is developed using Python, Django, CSS, HTML, and JavaScript. The system includes separate interfaces for students, professors, and administrators, ensuring a smooth and efficient exam management experience.

## Main Features
- **Auto-Submit Form**: Exams are automatically submitted when the timer runs out.
- **Focus Monitoring**: If a student's window goes out of focus five times during an exam, the professor receives an email alert.
- **Automatic Mark Calculation**: Marks are calculated automatically once the student submits the exam.
- **User Types**: The system supports two types of users - Professors and Students.
- **Control Panels**: Separate control panels for administrators and students.
- **MCQ Exams**: Students can take multiple-choice exams, view their scores, and see the correct answers.
- **Superuser Account**: Separate superuser account for account validations.

## Project Overview
![Project Overview](https://user-images.githubusercontent.com/47894634/117118618-9c1d1b00-adae-11eb-8b61-a6e87578f8da.png)

---

# Installation Guide

## Prerequisites
- **Python** (version 3.6 or higher)
- **pip** (Python package manager)
- **Pipenv** (virtual environment manager)
- **Git** (for cloning the repository)

## System Requirements
- Windows, macOS, or Linux
- At least 500 MB free disk space
- Internet connection for package installation

---

## Complete Step-by-Step Installation

### **Phase 1: Project Setup**

#### Step 1: Download or Clone the Repository
Open CMD/Terminal and run:
```bash
git clone https://github.com/ParasKumbhar/Online-Examination-System-New
cd Online-Examination-System-New
```

---

#### Step 2: Verify Python Installation
Open CMD and run:
```bash
python --version
```
Expected output: `Python 3.x.x`

If Python is not installed, download it from [python.org](https://www.python.org/downloads/)

---

#### Step 3: Verify PIP Installation
Open CMD and run:
```bash
pip --version
```

OR

```bash
python -m pip --version
```

Expected output: `pip x.x.x from ...`

---

#### Step 4: Install Pipenv
Open CMD and run:
```bash
pip install pipenv
```

---

#### Step 5: Verify Pipenv Installation
Open CMD and run:
```bash
pipenv --version
```

Expected output: `pipenv, version x.x.x`

---

#### Step 6: Set Up Python Scripts in Environment Variables (Windows Only)

**Step 6.1:** Identify your Python Scripts path by running:
```bash
python -m site --user-site
```

**Step 6.2:** Copy the output (example: `C:\Users\paras\AppData\Roaming\Python\Python38\site-packages`)

**Step 6.3:** Add this path to your Windows Environment Variables:
- Open Environment Variables (Search "Environment Variables" in Windows Search)
- Click "Edit Environment Variables for your account"
- Click "New" and paste the path
- Click "OK" to save

---

### **Phase 2: Virtual Environment & Dependencies**

#### Step 7: Create Virtual Environment
Open VS Code Terminal and run:
```bash
pipenv install
```

This creates a virtual environment and installs dependencies from `Pipfile`.

---

#### Step 8: Activate Pipenv Shell
Open VS Code Terminal and run:
```bash
pipenv shell
```

**Important:** You must run this command every time you open a new terminal before working with the project.

---

#### Step 9: Install Project Requirements
In VS Code Terminal (with pipenv shell activated), run:
```bash
pip install -r requirements.txt
```

This installs all necessary packages including Django, database drivers, and other dependencies.

---

### **Phase 3: Environment Configuration**

#### Step 10: Configure Email Settings
Create a file named `env.bat` in the project root folder (same directory as `manage.py`).

**For Windows**, add the following content:
```bash
@echo off
REM Django Settings
set DEBUG=False
set SECRET_KEY=django-insecure-your-generated-secret-key-here
set ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

REM Database Configuration
set DATABASE_ENGINE=django.db.backends.postgresql
set DATABASE_NAME=exam_system_db
set DATABASE_USER=exam_user
set DATABASE_PASSWORD=strong_password_here
set DATABASE_HOST=localhost
set DATABASE_PORT=5432

REM Email Configuration (Gmail SMTP)
set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
set EMAIL_HOST=smtp.gmail.com
set EMAIL_HOST_USER=your_email@example.com
set EMAIL_HOST_PASSWORD=your_email_password
set EMAIL_PORT=587
set EMAIL_USE_TLS=True
set DEFAULT_FROM_EMAIL=your_email@example.com

REM 2FA Configuration
set TWO_FACTOR_ENABLED=True
set OTP_EXPIRY_TIME=600

REM Redis Cache Configuration
set REDIS_HOST=localhost
set REDIS_PORT=6379
set REDIS_DB=0

REM Security Settings
set SECURE_SSL_REDIRECT=True
set SESSION_COOKIE_SECURE=True
set CSRF_COOKIE_SECURE=True
set SECURE_HSTS_SECONDS=31536000
set SECURE_HSTS_INCLUDE_SUBDOMAINS=True

REM Logging Configuration
set LOG_LEVEL=INFO

REM Display loaded configuration
echo Environment variables loaded:
echo - Email: %EMAIL_HOST_USER%
echo - Database: %DATABASE_HOST%
echo - Redis: %REDIS_HOST%:%REDIS_PORT%
```


**For Linux/macOS**, create `env.sh` instead:
```bash
export EMAIL_HOST_PASSWORD=your_email_password
export EMAIL_HOST_USER=your_email@example.com
export EMAIL_HOST=smtp.gmail.com
export DEFAULT_FROM_EMAIL=your_email@example.com
```

---

#### Step 11: Load Environment Variables
In VS Code Terminal, run:

**For Windows:**
```bash
.\\env.bat
```

**For Linux/macOS:**
```bash
source env.sh
```

---

#### Step 12: Navigate to Project Directory
In VS Code Terminal, run:
```bash
cd Exam
```

---

### **Phase 4: Database Setup**

#### Step 13: Run Initial Migrations
In VS Code Terminal, run:
```bash
python manage.py migrate
```

This applies all database migrations and creates the necessary tables.

---

#### Step 14: Create New Migrations (if needed)
If you've made changes to models, generate new migrations:
```bash
python manage.py makemigrations
```

---

#### Step 15: Apply Migrations Again
After creating new migrations, apply them:
```bash
python manage.py migrate
```

---

#### Step 16: Collect Static Files (For Production)
For production deployment, collect static files:
```bash
python manage.py collectstatic --noinput
```

---

### **Phase 5: User & Group Setup**

#### Step 17: Create Superuser Account
In VS Code Terminal, run:
```bash
python manage.py createsuperuser
```

You'll be prompted to enter:
- **Username**: (e.g., admin)
- **Email**: (e.g., admin@example.com)
- **Password**: (Choose a strong password)

---

#### Step 18: Run the Development Server
In VS Code Terminal, run:
```bash
python manage.py runserver
```

Expected output:
```
Starting development server at http://127.0.0.1:8000/
```

---

### **Phase 6: Post-Deployment Configuration**

#### Step 19: Access the Application
Open a web browser and navigate to:
- **Homepage**: `http://127.0.0.1:8000/`
- **Admin Panel**: `http://127.0.0.1:8000/admin/`

Log in with your superuser credentials.

---

#### Step 20: Create User Groups
1. Go to **Admin Panel** → `http://127.0.0.1:8000/admin/`
2. Navigate to **Authentication and Authorization** → **Groups**
3. Click **Add Group** button
4. Create **Group 1**:
   - **Name**: Professor
   - **Permissions**: 
     - `Contenttypes | content type | Can add content type`
     - `Faculty | faculty | Can add faculty`
     - `Faculty | faculty | Can change faculty`
     - `Faculty | faculty | Can delete faculty`
     - `Faculty | faculty | Can view faculty`
     - `Questions | question | Can add question`
     - `Questions | question | Can change question`
     - `Questions | question | Can delete question`
     - `Questions | question | Can view question`
   - Click **Save**

5. Create **Group 2**:
   - **Name**: Students
   - **Permissions**:
     - `Student | student | Can add student`
     - `Student | student | Can change student`
     - `Student | student | Can view student`
     - `Studentpreferences | studentpreference | Can add studentpreference`
     - `Studentpreferences | studentpreference | Can change studentpreference`
     - `Studentpreferences | studentpreference | Can view studentpreference`
   - Click **Save**

---

#### Step 21: Manage User Groups
1. Go to **Admin Panel** → **Users**
2. Select a user to edit
3. In the **Groups** section, select the appropriate group:
   - Select **Professor** for faculty members
   - Select **Students** for student users
4. Click **Save**

---

#### Step 22: Verify Email Configuration (Optional)
To test if email is working:
1. Go to **Admin Panel**
2. Perform an action that triggers an email (e.g., student focus loss alert)
3. Check if the email is received

If emails are not being sent, verify your `env.bat` file settings and ensure you've enabled "Less secure apps" in your Gmail settings (if using Gmail).

---

## Troubleshooting

### Issue: Pipenv shell not activating
**Solution**: Make sure pipenv is installed and added to PATH. Run `pip install --user pipenv`

### Issue: Port 8000 already in use
**Solution**: Run server on a different port:
```bash
python manage.py runserver 8001
```

### Issue: Database migration errors
**Solution**: Delete `db.sqlite3` and run migrations again:
```bash
python manage.py migrate
```

### Issue: Static files not loading
**Solution**: Run:
```bash
python manage.py collectstatic --noinput
```

### Issue: Email not being sent
**Solution**: 
- Verify `env.bat` variables are correct
- For Gmail, enable "Less secure apps" in account settings
- Check email logs in Django admin

---

## Project Structure
```
Online-Examination-System/
├── Exam/                          # Main Django project
│   ├── manage.py                  # Django management script
│   ├── db.sqlite3                 # SQLite database
│   ├── admission/                 # Admission management app
│   ├── course/                    # Course management app
│   ├── faculty/                   # Faculty management app
│   ├── student/                   # Student management app
│   ├── questions/                 # Question paper management app
│   ├── resultprocessing/          # Result processing app
│   ├── notifications/             # Notification system
│   ├── examProject/               # Django configuration
│   ├── templates/                 # HTML templates
│   └── static/                    # Static files (CSS, JS)
├── requirements.txt               # Python dependencies
├── Pipfile                        # Pipenv dependencies
└── README.md                      # This file
```

---

## Accessing Different Sections

- **Homepage**: `http://127.0.0.1:8000/`
- **Admin Panel**: `http://127.0.0.1:8000/admin/`
- **Student Portal**: `http://127.0.0.1:8000/student/`
- **Faculty Portal**: `http://127.0.0.1:8000/faculty/`

---

## Support & Documentation

For more information, visit the [GitHub Repository](https://github.com/ParasKumbhar/Online-Examination-System-New)

---

## License
This project is open source and available under the MIT License.
