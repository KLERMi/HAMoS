# PUBLIC VERSION: streamlit_app_public.py

import streamlit as st
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Table, MetaData
from sqlalchemy.orm import sessionmaker
import os

ADMIN_MODE = False

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

def ui_header():
    st.set_page_config("HAMoS Registration", layout="centered")
    st.markdown("""
        <div style='display: flex; align-items: center; justify-content: center;'>
            <img src='https://raw.githubusercontent.com/KLERMi/HAMoS/refs/heads/main/cropped_image.png' style='height:60px; margin-right:10px;'>
            <div style='line-height: 0.8;'>
                <h1 style='font-family: Aptos Light; font-size: 26px; color: #4472C4; margin: 0;'>Christ Base Assembly</h1>
                <p style='font-family: Aptos Light; font-size: 14px; color: #ED7D31; margin: 0;'>winning souls, building people..</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

ui_header()

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if not st.session_state.submitted:
    with st.form("registration_form"):
        phone = st.text_input("Phone", max_chars=11)
        name = st.text_input("Full Name")
        gender = st.selectbox("Gender", ["Male", "Female"])
        age = st.selectbox("Age Range", ["10-20", "21-30", "31-40", "41-50", "51-60", "61-70", "70+"])
        membership = st.selectbox("CBA Membership", ["Existing", "New"])
        location = st.text_input("Location (Community/LGA)")
        consent = st.checkbox("Consent to follow-up")
        services = st.multiselect("Services", ["Prayer", "Medical", "Welfare"])
        submitted = st.form_submit_button("Submit")

    if submitted:
        tag = next_tag()
        ins = registrations.insert().values(
            tag_id=tag, phone=phone, full_name=name, gender=gender,
            age_range=age, membership=membership, location=location,
            consent=consent, services=','.join(services)
        )
        session.execute(ins)
        session.commit()
        st.session_state.submitted = True
        st.success(f"Thank you! Your Tag ID is {tag}")
else:
    st.button("Register Another", on_click=lambda: st.session_state.update(submitted=False))
