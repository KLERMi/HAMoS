# ADMIN VERSION: streamlit_app_admin.py

import streamlit as st
from sqlalchemy import create_engine, Table, MetaData, select
import pandas as pd
from datetime import datetime

# Database path (same as public app)
db_path = 'public_registrations.db'
DATABASE_URL = f'sqlite:///{db_path}'
engine = create_engine(DATABASE_URL)
metadata = MetaData()

registrations = Table('registrations', metadata, autoload_with=engine)

# Simple admin login system
CREDENTIALS = {
    "HAM1": "christbase22",
    "HAM2": "christbase23"
}

st.set_page_config("HAMoS Admin", layout="centered")

# UI Header
st.markdown("""
    <div style='display: flex; align-items: center; justify-content: center;'>
        <img src='https://raw.githubusercontent.com/KLERMi/HAMoS/refs/heads/main/cropped_image.png' style='height:60px; margin-right:10px;'>
        <div style='line-height: 0.8;'>
            <h1 style='font-family: Aptos Light; font-size: 26px; color: #4472C4; margin: 0;'>Christ Base Assembly</h1>
            <p style='font-family: Aptos Light; font-size: 14px; color: #ED7D31; margin: 0;'>winning souls, building people..</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Login form
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    with st.form("Login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")
    
    if login_btn:
        if username in CREDENTIALS and CREDENTIALS[username] == password:
            st.session_state.authenticated = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

if st.session_state.authenticated:
    st.write("### Registered Attendees")
    with engine.connect() as conn:
        result = conn.execute(select(registrations)).fetchall()
        df = pd.DataFrame(result, columns=registrations.columns.keys())
    
    st.dataframe(df.drop(columns=["id"]))
    
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "hamos_attendees.csv", "text/csv")
