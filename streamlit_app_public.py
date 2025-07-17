import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date, time
import pytz

# --- Auth & Sheet Setup ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
info = dict(st.secrets["gcp_service_account"])
info["private_key"] = info["private_key"].replace("\\n", "\n").replace("\r", "").strip()
credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
client = gspread.authorize(credentials)
sheet = client.open_by_key(info["sheet_id"]).worksheet(info["sheet_name"])

# --- Helper Functions ---
def get_session():
    """
    Determine the next upcoming session based on Lagos time. If today is before all sessions,
    pick the first session. If between sessions, pick the nearest future one. If after all,
    return (None, None).
    """
    tz = pytz.timezone("Africa/Lagos")
    now = datetime.now(tz)

    # Define all sessions with their datetime and worksheet column
    sessions = [
        (tz.localize(datetime(2025, 7, 18, 18, 0)), "Day 1 - Fri 6PM", "attended_day1"),
        (tz.localize(datetime(2025, 7, 19, 8, 0)), "Day 2 - Sat 8AM", "attended_day2_morning"),
        (tz.localize(datetime(2025, 7, 19, 18, 0)), "Day 2 - Sat 6PM", "attended_day2_evening"),
        (tz.localize(datetime(2025, 7, 20, 8, 30)), "Day 3 - Sun 8:30AM", "attended_day3"),
    ]
    # Find next session
    for sess_dt, label, key in sessions:
        if now <= sess_dt:
            return label, key
    return None, None

# --- Clear State Callback ---
def clear_form_state():
    st.session_state.clear()

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
        <p style='font-size:0.85rem; color: #884400; margin-top:0;'>winning souls, building people...</p>
        """,
        unsafe_allow_html=True
    )
st.markdown("---")

# --- Determine Session ---
session_label, session_column = get_session()
if not session_column:
    st.warning("No upcoming sessions available for check-in.")
    st.stop()
else:
    st.info(f"Current/Next session: **{session_label}**")

# --- Main Logic ---
checkin_mode = st.radio("Select check-in mode:", ["New Registration", "Check-In by Phone or Tag ID"])

if checkin_mode == "New Registration":
    with st.form("new_reg"):
        name = st.text_input("Full Name")
        phone = st.text_input("Phone Number")
        submitted = st.form_submit_button("Register & Check-In")

        if submitted:
            tag = f"CBA-{datetime.now().strftime('%H%M%S')}"
            # Prepare row with attendance flags
            attended = {"attended_day1": "", 
                        "attended_day2_morning": "", 
                        "attended_day2_evening": "", 
                        "attended_day3": ""}
            attended[session_column] = "TRUE"

            row = [name, phone, tag,
                   attended["attended_day1"],
                   attended["attended_day2_morning"],
                   attended["attended_day2_evening"],
                   attended["attended_day3"]]
            sheet.append_row(row, value_input_option="USER_ENTERED")
            st.success(f"Registered successfully. Tag ID: {tag}")

    if st.button("OK", on_click=clear_form_state):
        pass

elif checkin_mode == "Check-In by Phone or Tag ID":
    with st.form("checkin"):
        lookup = st.text_input("Enter Phone or Tag ID")
        submitted = st.form_submit_button("Find Record")

        if submitted:
            records = sheet.get_all_records()
            header = sheet.row_values(1)
            # Normalize keys
            match = next(
                (r for r in records if str(r.get("phone")).strip() == lookup.strip() 
                 or str(r.get("tag")).strip() == lookup.strip()), None
            )
            if not match:
                st.error("No matching record found.")
            else:
                st.success(f"Welcome {match.get('name')}!")
                if not match.get(session_column):
                    if st.form_submit_button("Check In Now"):
                        row_idx = records.index(match) + 2  # account for header row
                        col_idx = header.index(session_column) + 1
                        sheet.update_cell(row_idx, col_idx, "TRUE")
                        st.success("Check-in successful!")
                else:
                    st.info("You are already checked in for this session.")
