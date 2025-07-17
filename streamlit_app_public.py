import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
from datetime import datetime

# --- Page Config ---
st.set_page_config(
    page_title="Healing All Manner of Sickness Registration",
    layout="centered"
)

# --- Custom Header ---
st.markdown(
    """
    <div style="display: flex; align-items: center; justify-content: center;">
        <img src="https://example.com/logo.png" alt="Event Logo" width="80" style="margin-right: 15px;" />
        <div>
            <h1 style="margin: 0; font-size: 30px;">Christ Base Assembly</h1>
            <h4 style="margin: 0; font-size: 11px;">Winning Souls, Building People</h4>
            <h3 style="margin: 0;">Healing All Manner of Sickness – Day 1</h3>
            <h4 style="margin: 0;">18 Jul 2025</h4>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Load Credentials from Secrets ---
creds_info = st.secrets["gcp_service_account"]
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
gc = gspread.authorize(credentials)

# --- Open Sheet ---
sheet_id = creds_info["sheet_id"]
sheet_name = creds_info["sheet_name"]
sheet = gc.open_by_key(sheet_id).worksheet(sheet_name)

# --- Registration Form ---
with st.form("day1_registration", clear_on_submit=False):
    phone = st.text_input("Phone Number", max_chars=11)
    name = st.text_input("Full Name")
    gender = st.selectbox("Gender", ["Male", "Female"])
    age = st.selectbox("Age Range", ["<18", "18-25", "26-35", "36-45", "46-55", "56-65", "66+"])
    membership = st.selectbox("CBA Membership", ["Yes", "No"])
    location = st.text_input("Location")
    consent = st.checkbox("I'm open to CBA following up to stay in touch.")
    services = st.multiselect(
        "Select desired services:",
        ["Medical ≤200", "Welfare ≤200", "Counseling", "Prayer"]
    )

    submitted = st.form_submit_button("Submit")

    if submitted:
        if not consent:
            st.error("Consent is required to register.")
        else:
            try:
                records = sheet.get_all_records()
                tag = f"HAMoS-{len(records) + 1:04d}"
                timestamp = datetime.utcnow().isoformat()
                services_csv = ",".join(services)

                row = [
                    tag, phone, name, gender, age, membership,
                    location, consent, services_csv,
                    False, False, timestamp
                ]

                sheet.append_row(row)
                st.success(f"Thank you! Your Tag ID is {tag}")
                if st.button("Register Another"):
                    st.experimental_rerun()

            except Exception as e:
                st.error(f"An error occurred: {e}")
