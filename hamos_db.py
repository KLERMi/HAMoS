# hamos_db.py
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# Database URL from env var or default to your Supabase URL
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:[YOUR-PASSWORD]@db.qfmlibtedkyowuxeruaa.supabase.co:5432/postgres'
)

# Base declarative class
Base = declarative_base()

# Registration model

class Registration(Base):
    __tablename__ = 'registrations'
    id             = Column(Integer, primary_key=True, autoincrement=True)
    tag_id         = Column(String(12), unique=True)
    phone          = Column(String(11))
    name           = Column(String(100))
    gender         = Column(String(10))
    age_range      = Column(String(10))
    membership     = Column(String(10))
    location       = Column(String(100))
    consent        = Column(Boolean)
    services       = Column(Text)
    day2_attended  = Column(Boolean, default=False)
    day3_attended  = Column(Boolean, default=False)
    ts             = Column(DateTime, default=datetime.utcnow)
    source         = Column(String(20))  # 'public' or 'admin'

# Create engine with SSL mode required for Supabase
engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"}
)

# Session factory
db_session = sessionmaker(bind=engine)

# Initialize database (create tables if not exists)
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: could not initialize DB: {e}")

# Get a new session

def get_session():
    return db_session()
