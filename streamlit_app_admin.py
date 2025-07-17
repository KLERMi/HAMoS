import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---- PAGE SETUP ----
st.set_page_config(page_title="HAMoS Admin", layout="centered")

# ---- STYLES ----
st.markdown("""
    <style>
        .title {
            font-family: 'Aptos Light', sans-serif;
            font-size: 26px;
            text-align: center;
            color: #4472C4;
        }
        .slogan {
            font-family: 'Aptos Light', sans-serif;
            font-size: 14px;
            text-align: center;
            color: #ED7D31;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# ---- HEADER ----
st.markdown('<div class="title">Christ Base Assembly</div>', unsafe_allow_html=True)
st.markdown('<div class="slogan">winning souls, building people..</div>', unsafe_allow_html=True)
st.markdown("---")

# ---- LOGIN ----
with st.sidebar:
    st.subheader("🔐 Admin Login")
    password = st.text_input("Enter admin password", type="password")
    login = st.button("Login")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if login and password == st.secrets["admin_credentials"]:
    st.session_state.logged_in = True
elif login and password != st.secrets["admin_credentials"]:
    st.error("Incorrect password.")

if not st.session_state.logged_in:
    st.stop()

# ---- GOOGLE AUTH ----
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPES
)
gc = gspread.authorize(creds)

# ---- SHEET ----
sheet = gc.open_by_key(st.secrets["sheet_id"]).worksheet(st.secrets["sheet_name"])
df = pd.DataFrame(sheet.get_all_records())

# ---- SEARCH RECORD ----
st.subheader("🔍 Search Attendee Record")
query = st.text_input("Search by Tag ID or Phone Number")

if query:
    match = df[(df['Tag ID'].str.upper() == query.upper()) | (df['Phone'] == query)]
    if match.empty:
        st.warning("No matching record found.")
    else:
        record = match.iloc[0]
        st.success("Record found:")
        st.json(record.to_dict())

        st.markdown("#### ✅ Mark Services as Provided")
        original_services = record["Services"].split(", ")
        provided_services = []

        for service in original_services:
            if st.checkbox(service.strip(), key=service):
                provided_services.append(service.strip())

        if st.button("Update Record"):
            row = match.index[0] + 2  # account for header
            col = df.columns.get_loc("Provided Services") + 1
            sheet.update_cell(row, col, ", ".join(provided_services))
            st.success("Record updated successfully.")

# ---- DOWNLOAD DATA ----
st.markdown("---")
st.subheader("📥 Download All Records")
if st.button("Download as CSV"):
    st.download_button(
        label="Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="hamos_admin_data.csv",
        mime="text/csv"
    )
