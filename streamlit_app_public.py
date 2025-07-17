import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# --- Auth & Sheet Setup via Streamlit Cloud Secrets ---
creds_info = st.secrets["gcp_service_account"]

# now pull everything from the same table:
sheet_id   = creds_info["sheet_id"]
sheet_name = creds_info["sheet_name"]

info = {
    "type":                        creds_info["type"],
    "project_id":                  creds_info["project_id"],
    "private_key_id":              creds_info["private_key_id"],
    "private_key":                 creds_info["private_key"].replace("\\n", "\n").strip(),
    "client_email":                creds_info["client_email"],
    "token_uri":                   creds_info["token_uri"],
    "auth_uri":                    creds_info["auth_uri"],
    "auth_provider_x509_cert_url": creds_info["auth_provider_x509_cert_url"],
    "client_x509_cert_url":        creds_info["client_x509_cert_url"],
    "client_id":                   creds_info["client_id"],
    "universe_domain":             creds_info["universe_domain"],
}

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
client      = gspread.authorize(credentials)
sheet       = client.open_by_key(sheet_id).worksheet(sheet_name)

# --- Helper Functions ---
def get_session():
    tz = pytz.timezone("Africa/Lagos")
    now = datetime.now(tz)
    sessions = [
        (datetime(2025, 7, 18, 18, 0, tzinfo=tz), "Day 1 – Fri 6 PM",      "attended_day1"),
        (datetime(2025, 7, 19,  8, 0, tzinfo=tz), "Day 2 – Sat 8 AM",      "attended_day2_morning"),
        (datetime(2025, 7, 19, 18, 0, tzinfo=tz), "Day 2 – Sat 6 PM",      "attended_day2_evening"),
        (datetime(2025, 7, 20,  8,30, tzinfo=tz), "Day 3 – Sun 8 :30 AM",   "attended_day3"),
    ]
    for dt, label, key in sessions:
        if now <= dt:
            return label, key
    return None, None

def clear_form_state():
    st.session_state.clear()

# --- Header Layout ---
col1, col2 = st.columns([1, 6])
with col1:
    st.image(
        "https://raw.githubusercontent.com/KLERMi/HAMoS/refs/heads/main/cropped_image.png",
        width=60
    )
with col2:
    st.markdown(
        """
        <h2 style="margin:0; font-size:30px;">Christ Base Assembly</h2>
        <p style="margin:0; font-size:11px; color:#884400;">
          winning souls, building people
        </p>
        """,
        unsafe_allow_html=True
    )
st.markdown("---")

# --- Determine Current/Next Session ---
session_label, session_column = get_session()
if not session_column:
    st.warning("No upcoming sessions available for check-in.")
    st.stop()
st.info(f"Current/Next session: **{session_label}**")

# --- Calculate Service Availability ---
records = sheet.get_all_records()
all_services = [
    s.strip()
    for r in records
    for s in (r.get("services") or "").split(",")
    if s.strip()
]
remaining_medicals = max(0, 200 - all_services.count("Medicals"))
remaining_welfare  = max(0, 200 - all_services.count("Welfare package"))

# --- Main Form Logic ---
checkin_mode = st.radio("Select check-in mode:", ["New Registration", "Check-In by Phone or Tag ID"])

if checkin_mode == "New Registration":
    with st.form("new_reg"):
        phone      = st.text_input("Phone Number", max_chars=11)
        name       = st.text_input("Full Name")
        gender     = st.selectbox("Gender", ["Male", "Female"])
        age        = st.selectbox("Age Range", ["<18","18-25","26-35","36-45","46-55","56-65","66+"])
        membership = st.selectbox("CBA Membership", ["Yes", "No"])
        location   = st.text_input("Location")
        consent    = st.checkbox("I'm open to CBA following up to stay in touch.")
        service_options = []
        if remaining_medicals > 0:
            service_options.append("Medicals")
        if remaining_welfare > 0:
            service_options.append("Welfare package")
        service_options += ["Counseling", "Prayer"]
        services   = st.multiselect("Select desired services:", service_options)
        submitted  = st.form_submit_button("Submit")

        if submitted:
            if not consent:
                st.error("Consent is required to register.")
            else:
                recs   = sheet.get_all_records()
                serial = len(recs) + 1
                tag    = f"HAMoS-{serial:04d}"
                ts     = datetime.now(pytz.timezone("Africa/Lagos")).isoformat()
                services_csv = ",".join(services)
                attended = {
                    "attended_day1": "", 
                    "attended_day2_morning": "", 
                    "attended_day2_evening": "", 
                    "attended_day3": ""
                }
                attended[session_column] = "TRUE"
                row = [
                    tag, phone, name, gender, age, membership,
                    location, consent, services_csv,
                    attended["attended_day1"],
                    attended["attended_day2_morning"],
                    attended["attended_day2_evening"],
                    attended["attended_day3"],
                    ts
                ]
                sheet.append_row(row, value_input_option="USER_ENTERED")
                st.success(f"Thank you! Your Tag ID is {tag}")

    if st.button("OK"):
        clear_form_state()
        st.experimental_rerun()

else:  # Check-In by Phone or Tag ID
    with st.form("checkin"):
        lookup    = st.text_input("Enter Phone or Tag ID")
        submitted = st.form_submit_button("Find Record")
        if submitted:
            records = sheet.get_all_records()
            header  = sheet.row_values(1)
            match   = next(
                (r for r in records
                 if str(r.get("phone")).strip() == lookup.strip()
                 or str(r.get("tag")).strip()   == lookup.strip()),
                None
            )
            if not match:
                st.error("No matching record found.")
            else:
                st.success(f"Welcome {match.get('name')}!")
                if not match.get(session_column):
                    if st.form_submit_button("Check In Now"):
                        row_idx = records.index(match) + 2
                        col_idx = header.index(session_column) + 1
                        sheet.update_cell(row_idx, col_idx, "TRUE")
                        st.success("Check‑in successful!")
                else:
                    st.info("You are already checked in for this session.")
