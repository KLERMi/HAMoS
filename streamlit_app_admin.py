# streamlit_app_public.py

import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
from datetime import datetime

# --- Page config & header ---
st.set_page_config(
    page_title="Healing All Manner of Sickness Registration",
    layout="centered"
)

# Custom header with logo and title
st.markdown(
    """
    <div style="text-align:center">
        <img src="https://example.com/logo.png" alt="Event Logo" width="100" /><br>
        <h1>Healing All Manner of Sickness</h1>
        <h3>Day 1 Registration (18 Jul 2025)</h3>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Load Google Sheets client from secrets ---
creds_info = st.secrets["gcp_service_account"]  # service account credentials
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(st.secrets["sheet_id"]).worksheet(st.secrets["sheet_name"])

# --- Registration Form ---
with st.form("day1_registration", clear_on_submit=False):
    phone = st.text_input("Phone Number", max_chars=11)
    name = st.text_input("Full Name")
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    age = st.selectbox("Age Range", ["<18", "18-25", "26-35", "36-45", "46+"])
    membership = st.selectbox("CBA Membership", ["Yes", "No"])
    location = st.text_input("Location")
    consent = st.checkbox("I consent to data processing.")
    services = st.multiselect(
        "Select desired services:",
        ["Medical ≤200", "Welfare ≤200", "Counseling", "Prayer"]
    )
    submitted = st.form_submit_button("Submit")

    if submitted:
        if not consent:
            st.error("Consent is required to register.")
        else:
            # generate Tag ID
            records = sheet.get_all_records()
            tag = f"HAMoS-{len(records)+1:04d}"
            timestamp = datetime.utcnow().isoformat()
            services_csv = ",".join(services)
            row = [
                tag,
                phone,
                name,
                gender,
                age,
                membership,
                location,
                consent,
                services_csv,
                False,  # attended_day2
                False,  # attended_day3
                timestamp
            ]
            sheet.append_row(row)
            st.success(f"Thank you! Your Tag ID is {tag}")
            if st.button("Register Another"):
                st.experimental_rerun()
