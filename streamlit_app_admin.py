# hamos_db.py
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# Use the Supabase URL directly if env var not set
DATABASE_URL = os.getenv('DATABASE_URL',
    'postgresql://postgres:[Wg2gdt4QQL&%dsW]@db.qfmlibtedkyowuxeruaa.supabase.co:5432/postgres'
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

# Create engine & session factory
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Initialize database (create tables)
def init_db():
    Base.metadata.create_all(bind=engine)

# Get a new session
def get_session():
    return SessionLocal()


# --- streamlit_app_admin.py ---
import streamlit as st
import pandas as pd
from hamos_db import init_db, get_session, Registration

# Initialize database
init_db()

# Page config
st.set_page_config(page_title="HAMoS Admin", layout="centered")

# UI header
st.markdown("""
<div style='display:flex; align-items:center; justify-content:center;'>
  <img src='https://raw.githubusercontent.com/KLERMi/HAMoS/main/cropped_image.png' style='height:60px; margin-right:10px;'>
  <div style='line-height:0.8;'>
    <h1 style='font-family:Aptos Light; font-size:26px; color:#4472C4; margin:0;'>Christ Base Assembly</h1>
    <p style='font-family:Aptos Light; font-size:14px; color:#ED7D31; margin:0;'>winning souls, building people..</p>
  </div>
</div>
""", unsafe_allow_html=True)

# Authentication
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

with st.sidebar:
    profile = st.text_input("Profile ID")
    pwd     = st.text_input("Password", type="password")
    if st.button("Login"):
        if (profile, pwd) in [("HAM1","christbase22"),("HAM2","christbase23")]:
            st.session_state.logged_in = True
        else:
            st.error("Invalid credentials")

if not st.session_state.logged_in:
    st.stop()

# Fetch and display
session = get_session()
records = session.query(Registration).order_by(Registration.ts.desc()).limit(10).all()
df = pd.DataFrame([r.__dict__ for r in records]).drop(columns=['_sa_instance_state'])

st.title("HAMoS Admin Dashboard")
st.subheader("Recent Registrations")
if df.empty:
    st.info("No records yet.")
else:
    st.dataframe(df)

with st.expander("Search"):
    q = st.text_input("Phone or Tag ID")
    if st.button("Search"):
        res = session.query(Registration).filter(
            (Registration.phone==q)|(Registration.tag_id==q)
        ).all()
        df2 = pd.DataFrame([r.__dict__ for r in res]).drop(columns=['_sa_instance_state'])
        if df2.empty:
            st.info("No match.")
        else:
            st.write(df2)

# CSV download
all_recs = session.query(Registration).all()
df_all  = pd.DataFrame([r.__dict__ for r in all_recs]).drop(columns=['_sa_instance_state'])
st.download_button(
    "Download CSV",
    data=df_all.to_csv(index=False).encode(),
    file_name="hamos_regs.csv",
    mime="text/csv"
)
