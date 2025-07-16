# ADMIN VERSION: streamlit_app_admin.py

import streamlit as st
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Table, MetaData
from sqlalchemy.orm import sessionmaker
import pandas as pd
import os

ADMIN_MODE = True

engine = create_engine('sqlite:///registrations.db')
metadata = MetaData()

registrations = Table('registrations', metadata,
    Column('id', Integer, primary_key=True),
    Column('tag_id', String, unique=True),
    Column('phone', String),
    Column('full_name', String),
    Column('gender', String),
    Column('age_range', String),
    Column('membership', String),
    Column('location', String),
    Column('consent', Boolean),
    Column('services', String),
    Column('medical_count', Integer, default=0),
    Column('welfare_count', Integer, default=0),
    Column('day2_attended', Boolean, default=False),
    Column('day3_attended', Boolean, default=False),
    Column('ts', DateTime, default=datetime.utcnow)
)
metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def next_tag():
    count = session.query(registrations).count() + 1
    return f"HAMoS-{count:04d}"

output_directory = r"C:\\Users\\OMODELEC\\OneDrive - Access Bank PLC\\Documents\\2025 codes"
os.makedirs(output_directory, exist_ok=True)
output_file = os.path.join(output_directory, "hamos_registrations.csv")

def ui_header():
    st.set_page_config("HAMoS Admin", layout="centered")
    st.markdown("""
        <div style='display: flex; align-items: center; justify-content: center;'>
            <img src='https://raw.githubusercontent.com/KLERMi/HAMoS/refs/heads/main/cropped_image.png' style='height:60px; margin-right:10px;'>
            <div>
                <h1 style='font-family: Aptos Light; font-size: 26px; color: #4472C4; margin: 0;'>Christ Base Assembly</h1>
                <p style='font-family: Aptos Light; font-size: 14px; color: #ED7D31; margin: 0;'>winning souls, building people..</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

ui_header()
st.header("Healing All Manner of Sickness - Admin Panel")

if st.checkbox("Show all registrations"):
    df = pd.read_sql_table('registrations', 'sqlite:///registrations.db')
    st.dataframe(df)
    st.download_button(label="Download CSV", data=df.to_csv(index=False), file_name="hamos_registrations.csv", mime="text/csv")
    df.to_csv(output_file, index=False)
    st.success(f"CSV saved to {output_file}")
