# streamlit_app_admin.py

import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
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
      top: 0; right: 0; bottom: 0; left: 0;
      z-index: -1;
    }
    .church-header {
      text-align: center;
      font-family: 'Aptos Light', sans-serif;
      margin: 1rem 0;
    }
    .church-name {
      font-size: 26px;
      color: #4472C4;
      line-height: 0.8;
      margin: 0;
    }
    .church-slogan {
      font-size: 14px;
      color: #ED7D31;
      line-height: 0.8;
      margin: 0;
    }
    </style>
    <div class="church-header">
      <div class="church-name">Christ Base Assembly</div>
      <div class="church-slogan">winning souls, building people..</div>
      <h2>Admin Dashboard - Healing All Manner of Sickness</h2>
    </div>
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
    if st.button("Login"):
        creds = st.secrets["admin_credentials"]
        if user in creds and pwd == creds[user]:
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials.")

if not st.session_state.logged_in:
    st.info("Please log in via sidebar.")
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

# --- Display Recent Records ---
st.subheader("Most Recent Records")
st.dataframe(df.sort_values(by="timestamp", ascending=False))

# --- Search ---
with st.expander("Search Records"):
    term = st.text_input("Filter by Phone or Tag ID")
    if term:
        filtered = df[
            df["phone"].astype(str).str.contains(term, na=False) |
            df["tag"].str.contains(term, na=False)
        ]
        st.dataframe(filtered)

# --- Download All Registrations ---
csv = df.to_csv(index=False)
st.download_button(
    "Download All Registrations",
    data=csv,
    file_name="registrations.csv",
    mime="text/csv"
)

# --- Check-In Section ---
st.subheader("Check-In")
now = datetime.now(timezone.utc)
windows = {
    "Day 1 Evening": (datetime(2025,7,18,18,0,tzinfo=timezone.utc), datetime(2025,7,18,22,0,tzinfo=timezone.utc)),
    "Day 2 Morning": (datetime(2025,7,19,8,0,tzinfo=timezone.utc), datetime(2025,7,19,12,0,tzinfo=timezone.utc)),
    "Day 2 Evening": (datetime(2025,7,19,18,0,tzinfo=timezone.utc), datetime(2025,7,19,22,0,tzinfo=timezone.utc)),
    "Day 3 Morning": (datetime(2025,7,20,8,30,tzinfo=timezone.utc), datetime(2025,7,20,12,0,tzinfo=timezone.utc)),
}
for label, (start, end) in windows.items():
    if start <= now <= end:
        if st.button(f"Check-In {label}"):
            tag_input = st.text_input("Enter Tag ID to check in:", key=label)
            if tag_input:
                idx = df.index[df["tag"] == tag_input].tolist()
                if idx:
                    day_num = int(label.split()[1])
                    col_name = f"attended_day{day_num}"
                    row_idx = idx[0] + 2
                    col_idx = df.columns.get_loc(col_name) + 1
                    sheet.update_cell(row_idx, col_idx, True)
                    st.success(f"{tag_input} checked in for {label}.")
                else:
                    st.error("Tag ID not found.")
    else:
        st.button(f"Check-In {label}", disabled=True)
