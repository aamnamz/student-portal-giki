# GIKI MS Student Portal

A full-stack Django-based student portal developed for GIKI MS students to manage their academic and application-related information through a secure and responsive web interface.

## Features

* 🔐 **Authentication & Authorization** — Secure student login and protected portal views.
* 📊 **Student Dashboard** — Centralized overview of student information and portal activities.
* 👤 **Profile Management** — Manage and update student personal and academic information.
* 📄 **Application Management** — Submit and manage student applications.
* 📁 **Document Management** — Upload and manage required student documents.
* 🤖 **AI Image Validation** — AI-powered module that validates student photographs to ensure they meet the required criteria.
* 📱 **Responsive Interface** — Built with Bootstrap 5 for a clean and responsive user experience.

## Tech Stack

* **Backend:** Python, Django
* **Frontend:** HTML, CSS, JavaScript, Bootstrap 5
* **Database:** SQLite / PostgreSQL
* **AI:** Python-based image validation module
* **Version Control:** Git & GitHub

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd <project-folder>
```

Create and activate a virtual environment:

```bash
python -m venv venv
```

**Windows:**

```bash
venv\Scripts\activate
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Run database migrations:

```bash
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

Open the portal at:

```text
http://127.0.0.1:8000/
```

## Project Purpose

The portal provides a centralized platform for MS students to manage their information, applications, and documents while using AI-assisted image validation to improve the student registration and application process.

## Development

This project was developed as part of an internship project at **Ghulam Ishaq Khan Institute (GIKI)**.
