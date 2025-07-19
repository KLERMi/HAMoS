import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import re

# --- Auth & Sheet Setup ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
info = dict(st.secrets["gcp_service_account"])
info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
client = gspread.authorize(credentials)
# Open the worksheet
sheet = client.open_by_key(info["sheet_id"]).worksheet(info["sheet_name"])

# --- Helper Functions ---
def get_session():
    tz = pytz.timezone("Africa/Lagos")
    now = datetime.now(tz)
    # Map sheet header names for day2 and day3
    sessions = [
        (tz.localize(datetime(2025, 7, 19, 8, 0)), "Check-in day2"),  # Day2 session
        (tz.localize(datetime(2025, 7, 20, 8, 30)), "Check-in day 3"),  # Day3 session
    ]
    for dt, col_name in sessions:
        if now <= dt:
            return col_name
    return None


def clear_form_state():
    st.session_state.pop('lookup', None)
    st.session_state.pop('row_idx', None)
    st.session_state.pop('session_col', None)


# --- Layout Header ---
col1, col2 = st.columns([1, 6])
with col1:
    st.image("https://raw.githubusercontent.com/KLERMi/HAMoS/refs/heads/main/cropped_image.png", width=60)
with col2:
    st.markdown(
        """
        <h2 style='margin-bottom:0;'>Christ Base Assembly</h2>
        <p style='font-size:0.85rem; color:#884400; margin-top:0;'>winning souls, building people...</p>
        """, unsafe_allow_html=True
    )
st.markdown("---")

# Determine which check-in column applies
session_col = get_session()
if not session_col:
    st.warning("No upcoming check-in available.")
    st.stop()

# Show current local time instead of session column
now = datetime.now(pytz.timezone("Africa/Lagos"))
st.info(f"Current Time: **{now.strftime('%A %d %B %Y, %I:%M %p')}**")

# --- Choose Mode ---
mode = st.radio("Mode:", ["New Registration", "Check-In by Phone or Tag ID"])

if mode == "New Registration":
    with st.form("new_reg", clear_on_submit=True):
        phone = st.text_input("Phone Number", max_chars=11)
        name = st.text_input("Full Name")
        gender = st.selectbox("Gender", ["Male", "Female"])
        age = st.selectbox("Age Range", ["<18","18-25","26-35","36-45","46-55","56-65","66+"])
        membership = st.selectbox("CBA Membership", ["Yes","No"])
        location = st.text_input("Location")
        consent = st.checkbox("I'm open to CBA following up to stay in touch.")

        records = sheet.get_all_records()
        # Service limits
        used_medicals = sum(r.get("services", "").split(",").count("Medicals") for r in records)
        used_welfare = sum(r.get("services", "").split(",").count("Welfare package") for r in records)
        options = []
        if used_medicals < 200: options.append("Medicals")
        if used_welfare < 200: options.append("Welfare package")
        options += ["Counseling", "Prayer"]
        services = st.multiselect("Select desired services:", options)

        if st.form_submit_button("Submit"):
            if not consent:
                st.error("Consent is required to register.")
            else:
                # Tag generation
                tags = [r.get('tag','') for r in records]
                nums = [int(m.group(1)) for t in tags if (m := re.match(r'HAMoS-(\d{4})', t))]
                next_num = max(nums) + 1 if nums else 1
                tag = f"HAMoS-{next_num:04d}"
                ts = datetime.now(pytz.timezone("Africa/Lagos")).isoformat()
                # Initialize attendance flags
                attendance = {"Check-in day2": "", "Check-in day 3": ""}
                # Mark current session
                attendance[session_col] = "TRUE"

                data = {
                    'tag': tag,
                    'phone': phone,
                    'name': name,
                    'gender': gender,
                    'age': age,
                    'membership': membership,
                    'location': location,
                    'consent': consent,
                    'services': ",".join(services),
                    'timestamp': ts,
                    **attendance
                }
                header = sheet.row_values(1)
                row = [data.get(col, '') for col in header]
                sheet.append_row(row, value_input_option="USER_ENTERED")
                st.success(f"Registered! Your Tag ID: {tag}")

else:
    # Check-In Flow
    with st.form("find_form"):
        st.text_input("Enter Phone or Tag ID", key="lookup")
        if st.form_submit_button("Find Record"):
            lookup = st.session_state.lookup.strip()
            recs = sheet.get_all_records()
            header = sheet.row_values(1)
            match = next((r for r in recs if str(r.get("phone",""))==lookup or str(r.get("tag",""))==lookup), None)
            if not match:
                st.error("No matching record.")
            else:
                row_idx = recs.index(match) + 2
                col_idx = header.index(session_col) + 1
                if match.get(session_col) == "TRUE":
                    st.info("Already checked in.")
                else:
                    st.session_state.row_idx = row_idx
                    st.session_state.col_idx = col_idx
                    st.success(f"Welcome, {match.get('name')}!")

    if st.session_state.get('row_idx'):
        if st.button("Check In Now"):
            sheet.update_cell(st.session_state.row_idx, st.session_state.col_idx, "TRUE")
            st.success("Check-in successful!")
            clear_form_state()
