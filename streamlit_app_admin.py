# streamlit_app_admin.py

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone

# --- Page config ---
st.set_page_config(
    page_title="HAMoS Admin Portal",
    layout="centered"
)

# --- Global CSS & Watermark Background ---
st.markdown(
    """
    <style>
    .stApp::before {
      content: "";
      background: url('https://raw.githubusercontent.com/KLERMi/HAMoS/refs/heads/main/cropped_image.png') no-repeat center;
      background-size: contain;
      opacity: 0.3;
      position: fixed;
      top: 0; left: 0; bottom: 0; right: 0;
      z-index: -1;
    }
    .header-flex { display:flex; align-items:center; justify-content:center; gap:1rem; margin-bottom:1rem; }
    .church-name { font-family:'Aptos Light',sans-serif; font-size:26px; color:#4472C4; margin:0; line-height:0.8; text-align:center; }
    .church-slogan { font-family:'Aptos Light',sans-serif; font-size:14px; color:#ED7D31; margin:0; line-height:0.8; text-align:center; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Header ---
st.markdown(
    """
    <div class="header-flex">
      <img src="https://raw.githubusercontent.com/KLERMi/HAMoS/refs/heads/main/cropped_image.png" width="80" />
    </div>
    <p class="church-name">Christ Base Assembly</p>
    <p class="church-slogan">winning souls, building people..</p>
    <hr>
    """,
    unsafe_allow_html=True
)

# --- Authentication ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

with st.sidebar:
    st.header("Admin Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    login_clicked = st.button("Login")

if login_clicked:
    creds = st.secrets["admin_credentials"]
    if user in creds and pwd == creds[user]:
        st.session_state.logged_in = True
    else:
        st.sidebar.error("Invalid credentials.")

if not st.session_state.logged_in:
    st.sidebar.info("Please log in via the sidebar.")
    st.stop()

# --- Google Sheets setup ---
creds_info = st.secrets["gcp_service_account"]
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(st.secrets["sheet_id"]).worksheet(st.secrets["sheet_name"])

# --- Load data ---
records = sheet.get_all_records()
df = pd.DataFrame(records)

# --- Search & Update Services ---
st.subheader("🔍 Search & Update Member Services")
query = st.text_input("Enter Tag ID or Phone Number to fetch record")
if query:
    match = df[(df['tag'].str.upper() == query.upper()) | (df['phone'] == query)]
    if match.empty:
        st.warning("No matching record found.")
    else:
        record = match.iloc[0]
        st.markdown("### Registered Services:")
        services = record['services'].split(",") if record['services'] else []
        for svc in services:
            st.write(f"- {svc.strip()}")
        st.markdown("### Mark Services As Provided:")
        provided = []
        for svc in services:
            if st.checkbox(svc.strip(), key=svc):
                provided.append(svc.strip())
        if st.button("Submit Services Update"):
            # ensure Provided Services column exists
            if 'Provided Services' not in df.columns:
                # add header
                sheet.insert_column(['Provided Services'] + [''] * len(df), index=len(df.columns)+1)
                df['Provided Services'] = ''
            # update row
            row_idx = match.index[0] + 2
            col_idx = df.columns.get_loc('Provided Services') + 1
            sheet.update_cell(row_idx, col_idx, ", ".join(provided))
            st.success("Provided Services updated successfully.")

# --- Download All Records ---
st.markdown("---")
st.subheader("📥 Download All Records")
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download CSV",
    data=csv,
    file_name="hamos_admin_data.csv",
    mime="text/csv"
)
