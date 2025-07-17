# hamos_db.py
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# URL-encoded Supabase connection string (special chars encoded)
DEFAULT_DB_URL = (
    'postgresql+pg8000://'
    'postgres:Wg2gdt4QQL%26%25dsW'
    '@db.qfmlibtedkyowuxeruaa.supabase.co:5432/postgres'
)

# Allow override via environment variable
DATABASE_URL = os.getenv('DATABASE_URL', DEFAULT_DB_URL)

# Declarative base
Base = declarative_base()

# Registration model
class Registration(Base):
    __tablename__ = 'registrations'
    id            = Column(Integer, primary_key=True, autoincrement=True)
    tag_id        = Column(String(12), unique=True, nullable=False)
    phone         = Column(String(11), nullable=False)
    name          = Column(String(100), nullable=False)
    gender        = Column(String(10), nullable=False)
    age_range     = Column(String(10), nullable=False)
    membership    = Column(String(10), nullable=False)
    location      = Column(String(100), nullable=False)
    consent       = Column(Boolean, default=False)
    services      = Column(Text)
    day2_attended = Column(Boolean, default=False)
    day3_attended = Column(Boolean, default=False)
    ts            = Column(DateTime, default=datetime.utcnow)
    source        = Column(String(20), nullable=False)  # 'public' or 'admin'

# Create engine with SSL mode required
engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"}
)

# Session factory
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """
    Create all tables. Call this at application startup.
    """
    Base.metadata.create_all(bind=engine)

def get_session():
    """
    Obtain a new database session.
    """
    return SessionLocal()
