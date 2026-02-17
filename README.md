# Online Examination System

## Introduction
The Online Examination System is a digital platform designed to simplify the examination process, allowing students to take exams from anywhere at any time. It is developed using Python, Django, CSS, HTML, and JavaScript. The system includes separate interfaces for students, professors, and administrators, ensuring a smooth and efficient exam management experience.

## Main Features
- **Auto-Submit Form**: Exams are automatically submitted when the timer runs out.
- **Focus Monitoring**: If a student’s window goes out of focus five times during an exam, the professor receives an email alert.
- **Automatic Mark Calculation**: Marks are calculated automatically once the student submits the exam.
- **User Types**: The system supports two types of users - Professors and Students.
- **Control Panels**: Separate control panels for administrators and students.
- **MCQ Exams**: Students can take multiple-choice exams, view their scores, and see the correct answers.
- **Superuser Account**: Separate superuser account for account validations.

## Project Overview
![Project Overview](https://user-images.githubusercontent.com/47894634/117118618-9c1d1b00-adae-11eb-8b61-a6e87578f8da.png)

# Installation Guide

## Prerequisites
- Python
- Django
- Pipenv

## Steps to Run the Project

## Step 1: Download or Clone From :-
```
https://github.com/ParasKumbhar/Online-Examination-System-New
```

---

## Step 2: Verify Python Installation (in CMD) :-
```bash
python --version
```

---

## Step 3: Verify PIP Installation (in CMD) :-
```bash
pip --version
```

OR

```bash
python -m pip --version
```

---

## Step 4: Installation of PIPENV (in CMD) :-
```bash
pip install pipenv
```

---

## Step 5: Verify PIPENV Installation (in CMD) :-
```bash
pipenv --version
```

---

## Step 6.1: Identify Your Python Scripts Path (in CMD) :-
```bash
python -m site --user-site
```

---

## Step 6.2: Example output (Copy the Output and Add it in Environment Variables Users Path) :-
```
C:\Users\paras\AppData\Roaming\Python\Python38\site-packages
```

---

## Step 7: Creates Virtual Environment (in VS Code Terminal) :-
```bash
pipenv install
```

---

## Step 8: Activate the shell of PIPENV (in VS Code Terminal, Every Time when New Terminal Creates) :-
```bash
pipenv shell
```

---

## Skip Step 9 because the Step 10 Requirements file will Install Django :-
(Step 9: Installation of Django (in VS Code Terminal) :-
```bash
pip install django[argon2]
```
)

---

## Step 10: Installation of Requirements (in VS Code Terminal) :-
```bash
pip install -r requirements.txt
```

---

## Step 11: Set Up Environment Variables for Email Functionality :-
Create a env.bat file in the project Folder

### Sample:
```bash
set EMAIL_HOST_PASSWORD=REDACTED_EMAIL_PASSWORD
set EMAIL_HOST_USER=your_email@example.com
set EMAIL_HOST=smtp.gmail.com
set DEFAULT_FROM_EMAIL=your_email@example.com
```

### Example:
```bash
set EMAIL_HOST_PASSWORD=REDACTED_EMAIL_PASSWORD
set EMAIL_HOST_USER=online.examination.system.project@gmail.com
set EMAIL_HOST=online.examination.system.project@gmail.com
set DEFAULT_FROM_EMAIL=online.examination.system.project@gmail.com
```

---

## Step 12: Runs ENV File (in VS Code Terminal) :-
```bash
.\env.bat
```

---

## Step 13: Change Project Path to Run Code (in VS Code Terminal) :-
```bash
cd Exam
```

---

## Step 14: Run Database Migrations (in VS Code Terminal) :-
```bash
python manage.py migrate
```

---

## Step 15: Generate any new migrations (if needed) (in VS Code Terminal) :-
```bash
python manage.py makemigrations
```

---

## Step 16: Apply them again (in VS Code Terminal) :-
```bash
python manage.py migrate
```

---

## Step 17: Create a Superuser Account (in VS Code Terminal) :-
```bash
python manage.py createsuperuser
```

---

## Step 18: Run the Development Server (in VS Code Terminal) :-
```bash
python manage.py runserver
```

Homepage of Site :-
```
http://127.0.0.1:8000/
```

Access the admin panel :-
```
http://127.0.0.1:8000/admin/auth/group/add/
```

Add two groups: "Professor & Students"

---

### 1. Professor Permissions :
- Contenttypes  
- Faculty  
- Questions  

---

### 2. Students Permission :
- Student (It Should Start with Student)  
- Studentpreferences  

---

After Register you need to add the specific Group in the users as per Faculty or Students (For Faculty - “Professor” Group & For Student – “Students” Group).