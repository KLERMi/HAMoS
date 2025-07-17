# hamos_db.py
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# URL‑encode your password (& → %26, % → %25)
DEFAULT_DB_URL = (
    "postgresql+pg8000://"
    "postgres:Wg2gdt4QQL%26%25dsW"
    "@db.qfmlibtedkyowuxeruaa.supabase.co:5432/postgres"
)

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

Base = declarative_base()

class Registration(Base):
    __tablename__ = "registrations"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    tag_id        = Column(String(12), unique=True)
    phone         = Column(String(11))
    name          = Column(String(100))
    gender        = Column(String(10))
    age_range     = Column(String(10))
    membership    = Column(String(10))
    location      = Column(String(100))
    consent       = Column(Boolean)
    services      = Column(Text)
    day2_attended = Column(Boolean, default=False)
    day3_attended = Column(Boolean, default=False)
    ts            = Column(DateTime, default=datetime.utcnow)
    source        = Column(String(20))  # 'public' or 'admin'

# Enforce SSL with the simple pg8000 argument
engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"}
)

SessionLocal = sessionmaker(bind=engine)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: could not initialize DB: {e}")

def get_session():
    return SessionLocal()
