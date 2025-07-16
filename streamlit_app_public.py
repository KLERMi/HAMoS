# PUBLIC VERSION: streamlit_app_public.py

import streamlit as st
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Google Sheets setup
SHEET_ID = '1mFa47rJ7-ilULFu52PxLTo8OuxGsasveBL5N6CL4nCk'
SHEET_NAME = 'Sheet1'

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(dict(st.secrets["gcp"]), scopes=SCOPES)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

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

def next_tag():
    records = sheet.get_all_records()
    count = len(records) + 1
    return f"HAMoS-{count:04d}"

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
        new_row = [
            tag,
            phone,
            name,
            gender,
            age,
            membership,
            location,
            int(consent),
            ",".join(services),
            0,
            0,
            0,
            0,
            datetime.utcnow().isoformat()
        ]
        sheet.append_row(new_row)
        st.session_state.submitted = True
        st.success(f"Thank you! Your Tag ID is {tag}")
else:
    st.button("Register Another", on_click=lambda: st.session_state.update(submitted=False))
