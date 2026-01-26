import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. GET THE URL FROM RENDER (OR USE LOCAL FILE IF ON LAPTOP)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # 🌍 CLOUD MODE (PostgreSQL)
    # Fix for Render's URL format (postgres:// -> postgresql://)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
    engine = create_engine(DATABASE_URL)
else:
    # 💻 LAPTOP MODE (SQLite)
    DATABASE_URL = "sqlite:///./fliptrybe_v5.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()