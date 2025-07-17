# streamlit_app_public.py

import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
from datetime import datetime

# --- Page config ---
st.set_page_config(
    page_title="HAMoS Registration",
    layout="centered"
)

# --- Global CSS & Watermark Background ---
st.markdown(
    """
    <style>
    /* Watermark logo */
    .stApp::before {
      content: "";
      background: url('https://raw.githubusercontent.com/KLERMi/HAMoS/refs/heads/main/cropped_image.png') no-repeat center;
      background-size: contain;
      opacity: 0.3;
      position: fixed;
      top: 0; right: 0; bottom: 0; left: 0;
      z-index: -1;
    }
    /* Form container styling */
    .stForm {
      background-color: #4472C4 !important;
      padding: 1.5rem;
      border-radius: 8px;
    }
    /* Header text */
    .church-name {
      font-family: 'Aptos Light', sans-serif;
      font-size: 26px;
      color: #4472C4;
      line-height: 0.8;
      margin: 0;
    }
    .church-slogan {
      font-family: 'Aptos Light', sans-serif;
      font-size: 14px;
      color: #ED7D31;
      line-height: 0.8;
      margin: 0;
    }
    .header-flex {
      display: flex; 
      align-items: center; 
      justify-content: center; 
      gap: 1rem;
      margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Header with logo, church name & slogan ---
st.markdown(
    """
    <div class="header-flex">
      <img src="https://raw.githubusercontent.com/KLERMi/HAMoS/refs/heads/main/cropped_image.png"
           width="80" />
      <div style="text-align:center;">
        <p class="church-name">Christ Base Assembly</p>
        <p class="church-slogan">winning souls, building people..</p>
      </div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Google Sheets client setup ---
creds_info = st.secrets["gcp_service_account"]
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(st.secrets["sheet_id"])

# --- Ensure headers exist ---
expected_headers = [
    "tag", "phone", "name", "gender", "age", "membership",
    "location", "consent", "services",
    "attended_day2", "attended_day3", "timestamp"
]
first_row = sheet.sheet1.row_values(1)
if first_row != expected_headers:
    sheet.sheet1.insert_row(expected_headers, 1)
sheet = sheet.worksheet(st.secrets["sheet_name"])

# --- Compute service capacities ---
records = sheet.get_all_records()
all_services = sum((r["services"].split(",") for r in records if r["services"]), [])
med_count = all_services.count("Medical")
wel_count = all_services.count("Welfare")

service_options = ["Counseling", "Prayer"]
if med_count < 200:
    service_options.insert(0, "Medical")
else:
    st.markdown("<span style='color:lightgray'>Medical (Sold Out)</span>", unsafe_allow_html=True)
if wel_count < 200:
    service_options.insert(1, "Welfare")
else:
    st.markdown("<span style='color:lightgray'>Welfare (Sold Out)</span>", unsafe_allow_html=True)

# --- Registration Form ---
with st.form("day1_registration", clear_on_submit=False):
    phone = st.text_input("Phone Number", max_chars=11)
    name = st.text_input("Full Name")
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    age = st.selectbox(
        "Age Range",
        ["<18", "18-25", "26-35", "36-45", "46-55", "56-65", "66+"]
    )
    membership = st.selectbox("CBA Membership", ["Yes", "No"])
    location = st.text_input("Location")
    consent = st.checkbox("I consent to data processing.")
    services = st.multiselect("Select desired services:", service_options)
    submitted = st.form_submit_button("Submit")

# --- Post‑submit handling outside form ---
if submitted:
    if not consent:
        st.error("Consent is required to register.")
    else:
        # Generate Tag ID and append row
        tag = f"HAMoS-{len(records) + 1:04d}"
        timestamp = datetime.utcnow().isoformat()
        row = [
            tag,
            phone, name, gender, age, membership,
            location, consent, ",".join(services),
            False, False, timestamp
        ]
        sheet.append_row(row)

        st.success(f"✅ Your Tag ID is **{tag}**")
        st.info("Copy your Tag ID, then click **OK** to register another.")
        if st.button("OK"):
            st.experimental_rerun()
