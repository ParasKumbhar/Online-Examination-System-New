# Online Examination System

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-4-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

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

## Installation Guide

### Prerequisites
- Python
- Django
- Pipenv

### Steps to Run the Project

1. **Clone the Project**
    ```bash
    git clone 
    cd Exam-Portal
    ```

2. **Set Up Environment Variables**
    Create a `.env` file in the `Exam-Portal` directory with the following contents:
    ```bash
    export EMAIL_HOST_PASSWORD=<PASSWORD_OF_EMAIL_ACCOUNT>
    export EMAIL_HOST_USER=<EMAIL_ACCOUNT>
    export EMAIL_HOST=<SMTP>
    export DEFAULT_FROM_EMAIL=<EMAIL_ACCOUNT>
    ```

    For Windows, create a `env.bat` file:
    ```bash
    set EMAIL_HOST_PASSWORD=<PASSWORD_OF_EMAIL_ACCOUNT>
    set EMAIL_HOST_USER=<EMAIL_ACCOUNT>
    set EMAIL_HOST=<SMTP>
    set DEFAULT_FROM_EMAIL=<EMAIL_ACCOUNT>
    ```

3. **Install Dependencies**
    ```bash
    pip install pipenv
    pip install django[argon2]
    pipenv shell
    pipenv install
    ```

4. **Load Environment Variables**
    On Linux:
    ```bash
    source .env
    ```
    On Windows:
    ```bash
    env.bat
    ```

5. **Database Migrations**
    ```bash
    cd Exam
    python manage.py migrate
    python manage.py makemigrations
    python manage.py migrate
    ```

6. **Create a Superuser Account**
    ```bash
    python manage.py createsuperuser
    ```

7. **Run the Server**
    ```bash
    python manage.py runserver
    ```

    The website should now be running at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

8. **Set Up User Groups**
    - Go to [http://127.0.0.1:8000/admin/auth/group/add/](http://127.0.0.1:8000/admin/auth/group/add/)
    - Login with the superuser account.
    - Add two groups named "Professor" and "Students".

9. **Professor Verification**
    - Admins need to manually add professors to the "Professor" group once they create a new account.