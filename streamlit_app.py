import streamlit as st
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Table, MetaData
from sqlalchemy.orm import sessionmaker
import pandas as pd

# Database setup
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
    Column('services', String),  # comma-separated
    Column('medical_count', Integer, default=0),
    Column('welfare_count', Integer, default=0),
    Column('day2_attended', Boolean, default=False),
    Column('day3_attended', Boolean, default=False),
    Column('ts', DateTime, default=datetime.utcnow)
)
metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Helper functions
def next_tag():
    count = session.query(registrations).count() + 1
    return f"HAMoS-{count:04d}"

# Session definitions
event_sessions = [
    {'name': 'Day 1 (Fri 18 Jul 2025 18:00)', 'dt': datetime(2025, 7, 18, 18, 0), 'day': 1},
    {'name': 'Day 2 Morning (Sat 19 Jul 2025 08:00)', 'dt': datetime(2025, 7, 19, 8, 0), 'day': 2},
    {'name': 'Day 2 Evening (Sat 19 Jul 2025 18:00)', 'dt': datetime(2025, 7, 19, 18, 0), 'day': 2},
    {'name': 'Day 3 (Sun 20 Jul 2025 08:30)', 'dt': datetime(2025, 7, 20, 8, 30), 'day': 3},
]

def get_next_session():
    now = datetime.utcnow() + timedelta(hours=1)  # adjust for Lagos GMT+1
    upcoming = [s for s in event_sessions if s['dt'] > now]
    return min(upcoming, key=lambda s: s['dt']) if upcoming else None

# Streamlit UI
st.set_page_config("HAMoS Check-In & Ticketing", layout="centered")
st.image("https://raw.githubusercontent.com/KLERMi/HAMoS/refs/heads/main/cropped_image.png")
st.title("Christ Base Assembly")
st.subheader("Winning souls, building people..")

st.header("Healing All Manner of Sickness - Check-In & Ticketing")

session_info = get_next_session()
if session_info:
    st.subheader(f"Next Session: {session_info['name']}")
else:
    st.subheader("Event has concluded")

mode = st.sidebar.selectbox("Mode", ["Register (Day 1)", "Check-In (Day 2/3)"])

if mode == "Register (Day 1)":
    with st.form("registration_form"):
        phone = st.text_input("Phone", max_chars=11)
        name = st.text_input("Full Name")
        gender = st.selectbox("Gender", ["Male", "Female"])
        age = st.selectbox("Age Range", ["10-20","21-30","31-40","41-50","51-60","61-70","70+"])
        membership = st.selectbox("CBA Membership", ["Existing","New"])
        location = st.text_input("Location (Community/LGA)")
        consent = st.checkbox("Consent to follow-up")
        services = st.multiselect("Services", ["Prayer","Medical","Welfare"])
        submitted = st.form_submit_button("Submit")
    if submitted:
        medical = 1 if "Medical" in services else 0
        welfare = 1 if "Welfare" in services else 0
        med_count = session.query(registrations).filter(registrations.c.services.like('%Medical%')).count()
        wel_count = session.query(registrations).filter(registrations.c.services.like('%Welfare%')).count()
        if med_count + medical > 200 or wel_count + welfare > 200:
            st.error("Medical or Welfare service cap reached.")
        else:
            tag = next_tag()
            ins = registrations.insert().values(
                tag_id=tag, phone=phone, full_name=name, gender=gender,
                age_range=age, membership=membership, location=location,
                consent=consent, services=','.join(services),
                medical_count=medical, welfare_count=welfare
            )
            session.execute(ins)
            session.commit()
            st.success(f"Thank you! Your Tag ID is {tag}")
            st.button("OK", on_click=lambda: st.experimental_rerun())

else:  # Check-In
    with st.form("checkin_form"):
        key = st.text_input("Enter Phone or Tag ID")
        chk_submit = st.form_submit_button("Check-In")
    if chk_submit:
        rec = session.query(registrations).filter(
            (registrations.c.phone == key) | (registrations.c.tag_id == key)
        ).first()
        if not rec:
            st.error("No registration found.")
        else:
            day = session_info['day'] if session_info else None
            if day == 2:
                session.query(registrations).filter(registrations.c.id==rec.id).update({"day2_attended": True})
            elif day == 3:
                session.query(registrations).filter(registrations.c.id==rec.id).update({"day3_attended": True})
            else:
                session.query(registrations).filter(registrations.c.id==rec.id).update({"day1_attended": True})
            session.commit()
            st.success(f"Check-in recorded for {session_info['name']}")
            st.button("OK", on_click=lambda: st.experimental_rerun())

if st.checkbox("Show all registrations"):
    df = pd.read_sql_table('registrations', 'sqlite:///registrations.db')
    st.dataframe(df)
if st.button("Export CSV"):
    df = pd.read_sql_table('registrations', 'sqlite:///registrations.db')
    df.to_csv('registrations_export.csv', index=False)
    st.write("CSV exported: registrations_export.csv")

st.markdown("---")
st.write("© 2025 CBA HAMoS Revival")
