# 🎓 GIKI MS Student Portal

**Internship Project — July 2026**
> ⚠️ PROJECT STATUS: UNDER DEVELOPMENT — NOT YET TESTED

### Full-Stack Student Management & Application Portal

A full-stack web application developed during an internship at **Ghulam Ishaq Khan Institute (GIKI)** 

## ✨ Features

* 🔐 **Authentication & Authorization** — Secure student authentication with protected portal views.
* 🤖 **AI Image Validation** — Validates student photographs against required image criteria.
* 📱 **Responsive Interface** — Responsive frontend built with Bootstrap 5.

## 🛠️ Tech Stack

| Category        | Technologies                       |
| --------------- | ---------------------------------- |
| Backend         | Python, Django                     |
| Frontend        | HTML, CSS, JavaScript, Bootstrap 5 |
| Database        | SQLite                             |
| AI              | Python-based Image Processing      |
| Version Control | Git / GitHub                       |

## 🤖 AI Image Validation

The portal includes an AI-powered image-processing module for validating uploaded student photographs.

The validation pipeline processes submitted images and checks them against predefined requirements before they are accepted by the application workflow.

```text
Student Photo
      ↓
Image Processing
      ↓
Validation Checks
      ↓
Pass / Reject
      ↓
Application Workflow
```

## 🏗️ Application Workflow

```text
Authentication
      ↓
Application
      ↓
Photo Validation
      ↓
Application Submission
```

## 🚀 Installation

### Clone the repository

```bash
git clone <repository-url>
cd <project-folder>
```

### Create a virtual environment

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

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run migrations

```bash
python manage.py migrate
```

### Start the development server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```


## 🎯 Project Purpose

The portal provides a centralized system for MS students to manage their **profiles, applications, and documents**, while incorporating AI-assisted image validation into the application workflow.

## 💼 Development

Developed as part of a Software Engineering Internship at Ghulam Ishaq Khan Institute (GIKI).

Status: 🚧 Under development and pending testing.

## 👩‍💻 Developer

**Amna Mumtaz**
Software Engineer

[GitHub](https://github.com/aamnamz) · [LinkedIn](https://www.linkedin.com/in/amnaamumtaz/)
