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
sheet = client.open_by_key(info["sheet_id"]).worksheet(info["sheet_name"])

# Fetch header once for column ordering
HEADER = sheet.row_values(1)

# --- Helper Functions ---
def get_session():
    tz = pytz.timezone("Africa/Lagos")
    now = datetime.now(tz)
    sessions = [
        (tz.localize(datetime(2025, 7, 18, 18, 0)), "Day 1 - Fri 6PM", "attended_day1"),
        (tz.localize(datetime(2025, 7, 19, 8, 0)), "Day 2 - Sat 8AM", "attended_day2_morning"),
        (tz.localize(datetime(2025, 7, 19, 18, 0)), "Day 2 - Sat 6PM", "attended_day2_evening"),
        (tz.localize(datetime(2025, 7, 20, 8, 30)), "Day 3 - Sun 8:30AM", "attended_day3"),
    ]
    for dt, label, key in sessions:
        if now <= dt:
            return label, key
    return None, None


def clear_form_state():
    for key in ["lookup", "row_idx", "session_column"]:
        if key in st.session_state:
            del st.session_state[key]

# --- Logo/Header Layout ---
col1, col2 = st.columns([1, 6])
with col1:
    st.image(
        "https://raw.githubusercontent.com/KLERMi/HAMoS/refs/heads/main/cropped_image.png",
        width=60
    )
with col2:
    st.markdown(
        """
        <h2 style='margin-bottom:0;'>Christ Base Assembly</h2>
        <p style='font-size:0.85rem; color:#884400; margin-top:0;'>winning souls, building people...</p>
        """, unsafe_allow_html=True
    )
st.markdown("---")

# --- Determine Session ---
session_label, session_column = get_session()
if not session_column:
    st.warning("No upcoming sessions available for check-in.")
    st.stop()
else:
    st.info(f"Current/Next session: **{session_label}**")

# --- Main Logic: Check-In / Registration ---
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

        # Build service options
        records = sheet.get_all_records()
        services_list = []
        used_medicals = sum(r.get("services","").split(",").count("Medicals") for r in records)
        used_welfare = sum(r.get("services","").split(",").count("Welfare package") for r in records)
        if used_medicals < 200:
            services_list.append("Medicals")
        if used_welfare < 200:
            services_list.append("Welfare package")
        services_list += ["Counseling","Prayer"]
        services = st.multiselect("Select desired services:", services_list)

        submitted = st.form_submit_button("Submit")
        if submitted:
            if not consent:
                st.error("Consent is required to register.")
            else:
                tags = [r.get('tag','') for r in records]
                nums = [int(re.search(r'HAMoS-(\d{4})', t).group(1)) for t in tags if re.match(r'HAMoS-\d{4}', t)]
                tag = f"HAMoS-{(max(nums)+1) if nums else 1:04d}"
                ts = datetime.now(pytz.timezone("Africa/Lagos")).isoformat()
                attended = {c: "" for c in ["attended_day1","attended_day2_morning","attended_day2_evening","attended_day3"]}
                attended[session_column] = "TRUE"
                data = {
                    'tag': tag, 'phone': phone, 'name': name,
                    'gender': gender, 'age': age, 'membership': membership,
                    'location': location, 'consent': consent,
                    'services': ",".join(services), 'timestamp': ts,
                    **attended
                }
                row = [data.get(col, '') for col in HEADER]
                sheet.append_row(row, value_input_option="USER_ENTERED")
                st.success(f"Registered! Your Tag ID: {tag}")

elif mode == "Check-In by Phone or Tag ID":
    with st.form("find_form", clear_on_submit=False):
        st.text_input("Enter Phone or Tag ID", key="lookup")
        find = st.form_submit_button("Find Record")
        if find:
            recs = sheet.get_all_records()
            header = HEADER
            lookup = st.session_state.lookup.strip()
            match = next((r for r in recs if str(r.get('phone','')).strip()==lookup or str(r.get('tag','')).strip()==lookup), None)
            if not match:
                st.error("No matching record found.")
            else:
                idx = recs.index(match) + 2
                if match.get(session_column) == "TRUE":
                    st.info("Already checked in for this session.")
                    clear_form_state()
                else:
                    st.session_state.row_idx = idx
                    st.session_state.session_column = session_column
                    st.success(f"Welcome, {match.get('name')}!")
    
    # After finding, show check-in button
    if st.session_state.get('row_idx'):
        if st.button("Check In Now"):
            col_idx = HEADER.index(st.session_state.session_column) + 1
            sheet.update_cell(st.session_state.row_idx, col_idx, "TRUE")
            st.success("Check-in successful!")
            clear_form_state()
