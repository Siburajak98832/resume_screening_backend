# from sqlalchemy import select, delete
# from sqlalchemy.ext.asyncio import AsyncSession
# from models import ResumeLog
# from schemas import ResumeLogCreate
# from datetime import datetime

# # Save a new resume log (insert or replace based on email)
# async def save_resume_log(db: AsyncSession, log_data: ResumeLogCreate):
#     # Check if record already exists for the email
#     result = await db.execute(select(ResumeLog).where(ResumeLog.email == log_data.email))
#     existing = result.scalar_one_or_none()

#     if existing:
#         # Update existing log with newer data
#         for field, value in log_data.dict().items():
#             setattr(existing, field, value)
#         existing.timestamp = datetime.utcnow()
#     else:
#         new_log = ResumeLog(**log_data.dict())
#         db.add(new_log)

#     await db.commit()

# # Fetch all logs
# async def get_all_logs(db: AsyncSession):
#     result = await db.execute(select(ResumeLog))
#     return result.scalars().all()

# # Delete a log by email
# async def delete_log_by_email(db: AsyncSession, email: str):
#     await db.execute(delete(ResumeLog).where(ResumeLog.email == email))
#     await db.commit()




