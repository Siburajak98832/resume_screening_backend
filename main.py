from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from database import get_db, init_db
from models import ResumeLog, Job,AdminConfig
from schemas import ResumeLogCreate, EmailRequest, JobOut, JobCreate,AdminConfigCreate,AdminConfigOut
from resume_screening_core import analyze_resume
import shutil, os, tempfile, smtplib, datetime, re
from email.mime.text import MIMEText
from fastapi import Query
import docx
import os
import json
import re
import google.generativeai as genai
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_db()


# ============ JOB ROUTES ============

@app.post("/jobs")
async def create_job(job: JobCreate, db: AsyncSession = Depends(get_db)):
    new_job = Job(**job.dict())  # includes created_by
    db.add(new_job)
    await db.commit()
    return {"message": "Job created successfully"}

@app.post("/analyze_resume")
async def analyze_resume_multiple(
    # request: Request,
    file: UploadFile = File(...),
    titles: str = Form(...),
    descriptions: str = Form(...)
):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix="." + file.filename.split('.')[-1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Configure Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-2.5-pro")

        # Extract resume text
        resume_text = ""
        if file.filename.endswith(".pdf"):
            import pdfplumber
            with pdfplumber.open(tmp_path) as pdf:
                resume_text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
        elif file.filename.endswith(".docx"):
            import docx
            doc = docx.Document(tmp_path)
            resume_text = "\n".join(p.text for p in doc.paragraphs)

        os.unlink(tmp_path)

        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Resume could not be parsed.")

        titles = json.loads(titles)
        descriptions = json.loads(descriptions)

        def extract_ats_score(text: str) -> int:
            score_patterns = [
                r"ATS Score\s*[:\-]?\s*(\d{1,3})",
                r"score\s*(?:is|of)?\s*(\d{1,3})\s*(?:/100)?",
                r"(\d{1,3})\s*/\s*100"
            ]
            for pattern in score_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return min(max(int(match.group(1)), 0), 100)
            return 0

        results = []
        for title, desc in zip(titles, descriptions):
            prompt = f"""
You are an expert ATS (Applicant Tracking System) resume reviewer.

Please evaluate the given resume **strictly** for the job title and description provided.

Your output must include the following **four sections** in this **exact format**, formatted clearly for human readability:

---

###  Job Title  
State the job title being analyzed.

###  ATS Score  
Return a numeric ATS Score (0 to 100), **formatted exactly like this**:  
**ATS Score: <number>**

This score should reflect how well the resume matches the job description based on:
- Skill keyword matching
- Relevance of experience
- Formatting & structure
- Language/tone

###  Missing Skills  
List the most important skills that are **mentioned in the job description but missing in the resume**.

###  Suggestions to Improve Resume  
Give **clear and actionable suggestions** to improve the resume for better alignment with this job, such as:
- Skills to add
- Experience to rephrase
- Formatting tips

Do **NOT** include any JSON or code formatting — return plain text only.

---

📄 Resume:
\"\"\"{resume_text}\"\"\"

🧾 Job Title: {title}
📝 Job Description:
\"\"\"{desc}\"\"\"
"""
            response = model.generate_content(prompt)
            text = response.text.strip()
            print(" Gemini Raw Response:")
            print(text) 
            score = extract_ats_score(text)

            results.append({
                "job_title": title,
                "ats_score": score,
                "suggestions": text
            })

        return {"results": results}

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/jobs", response_model=list[JobOut])
async def get_active_jobs(db: AsyncSession = Depends(get_db)):
    now = datetime.datetime.utcnow()
    result = await db.execute(select(Job).where(Job.deadline > now))
    return result.scalars().all()



@app.get("/admin/jobs")
async def get_admin_jobs(created_by:  str = Query(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.created_by == created_by))
    return result.scalars().all()

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await db.delete(job)
    await db.commit()
    return {"message": "Job deleted"}

@app.put("/jobs/{job_id}")
async def update_job(job_id: int, updated_job: JobCreate, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    for key, value in updated_job.dict().items():
        setattr(job, key, value)
    await db.commit()
    return {"message": "Job updated"}




# ============ RESUME SCREENING ============#


@app.post("/screen")
async def screen_resume(
    file: UploadFile = File(...),
    job_id: int = Form(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        #  Read the file once
        file_content = await file.read()

        #  Save to a temporary file for analysis
        ext = file.filename.split('.')[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        job = await db.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Ensure upload folder exists
        os.makedirs("uploaded_resumes", exist_ok=True)

        # Run the analysis
        result = await analyze_resume(
            file_path=tmp_path,
            job_title=job.title,
            job_description=job.description,
            job_id=job_id,
            required_skills=job.required_skills,
            thresholds={"junior": 0.45, "mid": 0.55, "senior": 0.6},
            db=db
        )

        #  Save resume file using actual email
        email = result["email"]
        resume_path = os.path.join("uploaded_resumes", f"{email}.{ext}")
        with open(resume_path, "wb") as f:
            f.write(file_content)

        #  Save to DB
        await db.execute(
            delete(ResumeLog).where(and_(ResumeLog.email == email, ResumeLog.job_id == job_id))
        )

        new_log = ResumeLog(
            name=result["name"],
            email=email,
            role=result["job_title"],
            experience_level=result["level"],
            final_score=result["final_score"],
            status=result["status"],
            timestamp=datetime.datetime.utcnow(),
            job_id=job_id
        )
        db.add(new_log)
        await db.commit()

        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Resume screening failed: {str(e)}")

# ============ ADMIN LOGS ============

@app.get("/admin/logs")
async def get_admin_logs(created_by: str= Query(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.created_by == created_by))
    job_ids = [job.id for job in result.scalars().all()]
    if not job_ids:
        return []

    result = await db.execute(
        select(ResumeLog).where(ResumeLog.job_id.in_(job_ids)).options(joinedload(ResumeLog.job))
    )
    logs = result.scalars().all()

    return [
        {
            "name": log.name,
            "email": log.email,
            "role": log.role,
            "experience_level": log.experience_level,
            "final_score": log.final_score,
            "status": log.status,
            "timestamp": log.timestamp,
            "job_title": log.job.title if log.job else "—",
            "job_id": log.job_id
        }
        for log in logs
    ]







@app.post("/send-email")
async def send_email(req: EmailRequest, db: AsyncSession = Depends(get_db)):
   
    sender_email = req.sender_email
    sender_password = req.sender_password
    result = await db.execute(
        select(ResumeLog).where(ResumeLog.email == req.email,ResumeLog.job_id == req.job_id).options(joinedload(ResumeLog.job))
        
    )
    log = result.scalars().first()

    if not log or not log.job:
        raise HTTPException(status_code=404, detail="Application or Job not found")

    company = log.job.company_name or "our company"

    if req.status.lower() == "accepted":
        body = f"""
Dear {req.name},

Thank you for applying to the {req.best_role} position at {company}.

You have been shortlisted for the next stage of our recruitment process. We’ll contact you soon!

Warm regards,  
HR Team  
"""
    else:
        body = f"""
Dear {req.name},

Thank you for your interest in the {req.best_role} position at {company}.

We regret to inform you that we will not be moving forward with your application at this time.

We wish you all the best in your job search.

Sincerely,  
HR Team  
"""

    msg = MIMEText(body)
    msg["Subject"] = f"Application Status – {req.best_role} at {company}"
    msg["From"] = sender_email
    msg["To"] = req.email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, req.email, msg.as_string())
        return {"message": "Email sent"}
    except Exception as e:
        return {"error": str(e)}





# ============ RESUME FILE VIEW & DELETE ============

@app.get("/resumes/{email}")
def view_resume(email: str):
    folder = "uploaded_resumes"
    safe_email = email.replace("/", "_").replace("\\", "_")
    for ext in [".pdf", ".docx"]:
        resume_path = os.path.join(folder, f"{safe_email}{ext}")
        if os.path.exists(resume_path):
            media_type = "application/pdf" if ext == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            return FileResponse(path=resume_path, media_type=media_type, filename=f"{safe_email}{ext}")
    raise HTTPException(status_code=404, detail="Resume not found.")

@app.delete("/logs/{email}/{job_id}")
async def delete_resume_log(email: str, job_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(ResumeLog).where(
        ResumeLog.email == email,
        ResumeLog.job_id == job_id
    ))
    await db.commit()
    return {"message": "Deleted"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
