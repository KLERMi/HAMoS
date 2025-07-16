# ADMIN VERSION: streamlit_app_admin.py

import streamlit as st
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Table, MetaData, inspect, select, func
from sqlalchemy.orm import sessionmaker
import pandas as pd

# SQLite database file
DATABASE_URL = 'sqlite:///public_registrations.db'
engine = create_engine(DATABASE_URL)
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

inspector = inspect(engine)
if 'registrations' not in inspector.get_table_names():
    metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

def authenticate():
    st.set_page_config("HAMoS Admin", layout="centered")
    with st.sidebar:
        profile = st.text_input("Profile ID")
        password = st.text_input("Password", type="password")
        login_btn = st.button("Login")
    if login_btn:
        if (profile == "HAM1" and password == "christbase22") or (profile == "HAM2" and password == "christbase23"):
            st.session_state.logged_in = True
        else:
            st.error("Invalid credentials")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    authenticate()
else:
    st.title("HAMoS Admin Dashboard")

    with st.expander("Search Records"):
        search_input = st.text_input("Enter Phone Number or Tag ID")
        if st.button("Search"):
            with engine.connect() as conn:
                query = select(registrations).where(
                    (registrations.c.phone == search_input) | (registrations.c.tag_id == search_input)
                )
                result = conn.execute(query).fetchall()
                if result:
                    df = pd.DataFrame(result, columns=result[0].keys())
                    st.write(df)
                else:
                    st.info("No matching record found.")

    with engine.connect() as conn:
        df = pd.read_sql(select(registrations), conn)
    st.download_button("Download All Registrations", data=df.to_csv(index=False).encode(), file_name="hamos_registrations.csv", mime="text/csv")
