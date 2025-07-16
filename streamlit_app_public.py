# ADMIN VERSION: streamlit_app_admin.py

import streamlit as st
from datetime import datetime
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets setup
SHEET_ID = '1mFa47rJ7-ilULFu52PxLTo8OuxGsasveBL5N6CL4nCk'
SHEET_NAME = 'Sheet1'

# Authenticate with service account
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_file("cba-hamos-49c7e60ee4fb.json", scopes=SCOPES)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

def ui_header():
    st.set_page_config("HAMoS Admin", layout="centered")
    st.markdown("""
        <div style='display: flex; align-items: center; justify-content: center;'>
            <img src='https://raw.githubusercontent.com/KLERMi/HAMoS/refs/heads/main/cropped_image.png' style='height:60px; margin-right:10px;'>
            <div style='line-height: 0.8;'>
                <h1 style='font-family: Aptos Light; font-size: 26px; color: #4472C4; margin: 0;'>Christ Base Assembly</h1>
                <p style='font-family: Aptos Light; font-size: 14px; color: #ED7D31; margin: 0;'>winning souls, building people..</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

def authenticate():
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
    ui_header()
    authenticate()
else:
    ui_header()
    st.title("HAMoS Admin Dashboard")

    # Fetch all records
    records = sheet.get_all_records()
    df = pd.DataFrame(records)

    st.subheader("Most Recent Records")
    if not df.empty:
        st.dataframe(df.sort_values(by="ts", ascending=False).head(10))
    else:
        st.info("No records available.")

    with st.expander("Search Records"):
        search_input = st.text_input("Enter Phone Number or Tag ID")
        if st.button("Search"):
            filtered = df[(df['phone'] == search_input) | (df['tag_id'] == search_input)]
            if not filtered.empty:
                st.write(filtered)
            else:
                st.info("No matching record found.")

    st.download_button("Download All Registrations", data=df.to_csv(index=False).encode(), file_name="hamos_registrations.csv", mime="text/csv")
