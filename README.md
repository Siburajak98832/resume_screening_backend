📄 Resume Screening Platform

This is a full-stack web application designed for multi-admin job posting and automated resume screening using AI.

🚀 Features

👥 For Admins

Post jobs (title, description, location, deadline, etc.)

See all applications for their own jobs only

Analyze resumes using AI scoring logic

Filter, search, and sort candidates

Send personalized emails (Accepted/Rejected)

Bulk email support with modal-based SMTP authentication

Track application counts per job

🧑‍💼 For Candidates

View open job listings

Upload resume (PDF or DOCX)

Automated skill matching

No login required

🏗️ Tech Stack

Layer

Tech

Frontend

React + Tailwind + ShadCN UI

Backend

FastAPI + SQLAlchemy + Uvicorn

Database

SQLite / PostgreSQL

Resume Parser

Python NLP + PyPDF2 + python-docx

AI Matching

Custom scoring on skills/roles

Auth

Firebase Admin UID

⚙️ Setup Instructions

1. Clone the Repos

git clone https://github.com/YOUR_USERNAME/resume_backend.git
cd resume_backend

2. Setup Backend

pip install -r requirements.txt
uvicorn main:app --reload

3. Setup Frontend

cd ../resume_frontend
npm install
npm run dev

Make sure to update your .env files with correct API base URLs and Firebase config.

✉️ SMTP Configuration for Email

Each admin must:

Enter their Gmail address & app password (passkey)

Emails are sent through their own credentials

No global SMTP hardcoding ✅

🧠 AI Resume Analysis

Scores candidates based on keyword match

Filters unqualified applicants automatically

Rank resumes for HR teams