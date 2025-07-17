import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="Healing All Manner of Sickness", layout="centered")
# ... your existing header markdown ...

# --- Load Secrets & Validate ---
creds_info = st.secrets["gcp_service_account"]
required = ["type","project_id","private_key_id","private_key","client_email","token_uri","sheet_id","sheet_name"]
missing = [k for k in required if k not in creds_info]
if missing:
    st.error(f"🚨 Missing required secret keys: {missing}")
    st.stop()

# --- OAuth Scopes ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# --- Cache the Sheet Connection ---
@st.cache_resource
def get_sheet(creds_info):
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(creds_info["sheet_id"]) \
                 .worksheet(creds_info["sheet_name"])

try:
    sheet = get_sheet(creds_info)
except Exception as e:
    st.error(f"Could not open Google Sheet: {e}")
    st.stop()

# --- Registration Form ---
with st.form("day1_registration", clear_on_submit=False):
    phone      = st.text_input("Phone Number", max_chars=11)
    name       = st.text_input("Full Name")
    gender     = st.selectbox("Gender", ["Male", "Female"])
    age        = st.selectbox("Age Range", ["<18", "18-25", "26-35", "36-45", "46-55", "56-65", "66+"])
    membership = st.selectbox("CBA Membership", ["Yes", "No"])
    location   = st.text_input("Location")
    consent    = st.checkbox("I'm open to CBA following up to stay in touch.")
    services   = st.multiselect("Select desired services:", ["Medical ≤200", "Welfare ≤200", "Counseling", "Prayer"])
    submitted  = st.form_submit_button("Submit")

    if submitted:
        if not consent:
            st.error("Consent is required to register.")
        else:
            try:
                records = sheet.get_all_records()
                tag      = f"HAMoS-{len(records)+1:04d}"
                timestamp= datetime.utcnow().isoformat()
                services_csv = ",".join(services)
                row = [
                    tag, phone, name, gender, age, membership,
                    location, consent, services_csv,
                    False, False, timestamp
                ]
                sheet.append_row(row)
                st.success(f"Thank you! Your Tag ID is {tag}")
                st.session_state.registration_done = True
            except Exception as e:
                st.error(f"An error occurred: {e}")
