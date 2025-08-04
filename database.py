
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
# import os
from dotenv import load_dotenv
import os

load_dotenv()  # 👈 This must be called before you use os.getenv

DB_URL = os.getenv("DATABASE_URL")

DB_URL =os.getenv("DATABASE_URL")

Base = declarative_base()
engine = create_async_engine(DB_URL, echo=True)
async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
