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
st.markdown(
    """
    <div style="text-align:center">
        <img src="https://raw.githubusercontent.com/KLERMi/HAMoS/refs/heads/main/cropped_image.png"
             alt="Event Logo" width="100" /><br>
        <h1>Healing All Manner of Sickness</h1>
        <h3>Day 1 Registration (18 Jul 2025)</h3>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Load Google Sheets client from secrets ---
creds_info = st.secrets["gcp_service_account"]
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(st.secrets["sheet_id"])

# Ensure headers exist (insert if sheet was blank)
expected_headers = ["tag", "phone", "name", "gender", "age", "membership",
                    "location", "consent", "services",
                    "attended_day2", "attended_day3", "timestamp"]
first_row = sheet.sheet1.row_values(1)
if first_row != expected_headers:
    sheet.sheet1.insert_row(expected_headers, index=1)
# Now select the correct worksheet tab
sheet = sheet.worksheet(st.secrets["sheet_name"])

# --- Compute service capacities ---
records = sheet.get_all_records()
# Flatten all services entries
all_services = sum((r["services"].split(",") for r in records if r["services"]), [])
med_count = all_services.count("Medical")
wel_count = all_services.count("Welfare")

# Build dynamic service options
service_options = ["Counseling", "Prayer"]
if med_count < 200:
    service_options.insert(0, "Medical")
else:
    st.markdown("<span style='color:gray'>Medical (Sold Out)</span>", unsafe_allow_html=True)
if wel_count < 200:
    service_options.insert(1, "Welfare")
else:
    st.markdown("<span style='color:gray'>Welfare (Sold Out)</span>", unsafe_allow_html=True)

# --- Registration Form ---
with st.form("day1_registration", clear_on_submit=False):
    phone = st.text_input("Phone Number", max_chars=11)
    name = st.text_input("Full Name")
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    age = st.selectbox("Age Range", [
        "<18", "18-25", "26-35", "36-45", "46-55", "56-65", "66+"
    ])
    membership = st.selectbox("CBA Membership", ["Yes", "No"])
    location = st.text_input("Location")
    consent = st.checkbox("I consent to data processing.")
    services = st.multiselect("Select desired services:", service_options)
    submitted = st.form_submit_button("Submit")

    if submitted:
        if not consent:
            st.error("Consent is required to register.")
        else:
            # generate Tag ID
            tag = f"HAMoS-{len(records)+1:04d}"
            timestamp = datetime.utcnow().isoformat()
            services_csv = ",".join(services)
            row = [
                tag, phone, name, gender, age, membership,
                location, consent, services_csv,
                False, False, timestamp
            ]
            sheet.append_row(row)
            # Show a copy‑and‑paste dialog for Tag ID
            st.success(f"✅ Thank you! Your Tag ID is **{tag}**")
            st.markdown("Copy your Tag ID above, then click **OK** to register another.")
            if st.button("OK"):
                st.experimental_rerun()
