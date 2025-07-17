import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="Healing All Manner of Sickness", layout="centered")

# --- Header (omitted for brevity) ---
# ... your existing header markdown ...

# --- Load and Inspect Secrets ---
creds_info = st.secrets["gcp_service_account"]

# 1) Check for missing keys
required = ["type","project_id","private_key_id","private_key","client_email","token_uri"]
missing = [k for k in required if k not in creds_info]
if missing:
    st.error(f"🚨 Missing required fields in gcp_service_account secret: {missing}")
    st.stop()

# 2) Debug-print the first/last 30 chars of the private key
st.write("🔑 KEY start:", repr(creds_info["private_key"][:30]))
st.write("🔑 KEY end:", repr(creds_info["private_key"][-30:]))

# --- OAuth Scopes ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# --- Attempt to Load Credentials ---
try:
    credentials = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
except Exception as e:
    st.error(f"⚠️ Failed to load service account credentials: {e}")
    st.stop()

# --- Authorize and Open Sheet ---
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(st.secrets["gcp_service_account"]["sheet_id"]) \
          .worksheet(st.secrets["gcp_service_account"]["sheet_name"])

# --- Registration Form (your existing code) ---
with st.form("day1_registration", clear_on_submit=False):
    phone = st.text_input("Phone Number", max_chars=11)
    name = st.text_input("Full Name")
    gender = st.selectbox("Gender", ["Male", "Female"])
    age = st.selectbox("Age Range", ["<18", "18-25", "26-35", "36-45", "46-55", "56-65", "66+"])
    membership = st.selectbox("CBA Membership", ["Yes", "No"])
    location = st.text_input("Location")
    consent = st.checkbox("I'm open to CBA following up to stay in touch.")
    services = st.multiselect("Select desired services:", ["Medical ≤200", "Welfare ≤200", "Counseling", "Prayer"])
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
                row = [tag, phone, name, gender, age, membership,
                       location, consent, services_csv, False, False, timestamp]
                sheet.append_row(row)
                st.success(f"Thank you! Your Tag ID is {tag}")
                if st.button("Register Another"):
                    st.experimental_rerun()
            except Exception as e:
                st.error(f"An error occurred: {e}")
