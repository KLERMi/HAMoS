# streamlit_app_admin.py

import streamlit as st
import pandas as pd
import gspread
import textwrap
from google.oauth2.service_account import Credentials

# --- Admin Login (from Streamlit secrets) ---
VALID_USERS = st.secrets["admin_credentials"]

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Only show login UI when not yet logged in
with st.sidebar:
    if not st.session_state.logged_in:
        st.header("Admin Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if VALID_USERS.get(username) == password:
                st.session_state.logged_in = True
                st.experimental_rerun()
            else:
                st.error("Invalid login, please retry.")
    else:
        # Optionally: allow logout
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.experimental_rerun()

if not st.session_state.logged_in:
    st.stop()


# —– All UI below only shows once logged in —–

# --- Page config & styling ---
st.set_page_config(page_title="HAMoS Admin Portal", layout="centered")
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
    """, unsafe_allow_html=True
)
st.markdown(
    """
    <div class="header-flex">
      <img src="https://raw.githubusercontent.com/KLERMi/HAMoS/refs/heads/main/cropped_image.png" width="80" />
    </div>
    <p class="church-name">Christ Base Assembly</p>
    <p class="church-slogan">winning souls, building people..</p>
    <hr>
    """, unsafe_allow_html=True
)

# --- Google Sheets Setup ---
raw = st.secrets["gcp_service_account"]
creds_info = dict(raw)
creds_info["private_key"] = (
    textwrap.dedent(creds_info["private_key"])
            .replace("\\n", "\n")
            .strip()
)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
gc = gspread.authorize(credentials)

sheet = gc.open_by_key(st.secrets["sheet_id"])\
          .worksheet(st.secrets["sheet_name"])

# --- Load DataFrame ---
records = sheet.get_all_records()
df = pd.DataFrame(records)

# --- Search & Update Attendee Services ---
st.subheader("🔍 Lookup and Update Services")

q = st.text_input("Enter Tag ID or Phone Number")
if q:
    q_up = q.strip().upper()
    filtered = df[
        (df['tag'].str.upper() == q_up) |
        (df['phone'] == q.strip())
    ]

    if filtered.empty:
        st.warning("No matching record found.")
    else:
        rec = filtered.iloc[0]
        st.markdown(f"**Name:** {rec.get('name', '—')}")
        st.markdown("**Registered Services:**")
        services = rec.get('services', '').split(',') if rec.get('services') else []
        for svc in services:
            st.write(f"- {svc.strip()}")

        st.markdown("**Mark Services Received:**")
        received = []
        for svc in services:
            if st.checkbox(svc.strip(), key=svc):
                received.append(svc.strip())

        if st.button("Submit Update"):
            # Ensure column exists
            col_name = "Services Received"
            if col_name not in df.columns:
                sheet.add_cols(1)
                new_idx = len(df.columns) + 1
                sheet.update_cell(1, new_idx, col_name)
                df[col_name] = ""

            # Write back to sheet
            row_idx = filtered.index[0] + 2
            col_idx = df.columns.get_loc(col_name) + 1
            sheet.update_cell(row_idx, col_idx, ", ".join(received))
            st.success("Updated successfully.")

# --- Download All Records ---
st.markdown("---")
st.subheader("📥 Download All Records")
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("Download CSV", csv, "hamos_admin_data.csv", "text/csv")
