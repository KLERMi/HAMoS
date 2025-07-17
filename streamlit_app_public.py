import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, time
import pytz

# --- Auth & Sheet Setup ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
info = dict(st.secrets["gcp_service_account"])
info["private_key"] = info["private_key"].replace("\\n", "\n")
credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
client = gspread.authorize(credentials)
sheet = client.open_by_key(info["sheet_id"]).worksheet(info["sheet_name"])

# --- Helper Functions ---
def get_session():
    now = datetime.now(pytz.timezone("Africa/Lagos"))
    day = now.date()
    sessions = {
        "2025-07-18": [(time(18, 0), "Day 1 - Fri 6PM", "attended_day1")],
        "2025-07-19": [
            (time(8, 0), "Day 2 - Sat 8AM", "attended_day2_morning"),
            (time(18, 0), "Day 2 - Sat 6PM", "attended_day2_evening")
        ],
        "2025-07-20": [(time(8, 30), "Day 3 - Sun 8:30AM", "attended_day3")],
    }
    today_sessions = sessions.get(str(day), [])
    for session_time, label, key in today_sessions:
        if now.time() <= session_time:
            return label, key
    return today_sessions[-1][1:] if today_sessions else ("", "")

def clear_form_state():
    st.session_state.clear()

# --- Logo/Header Layout ---
col1, col2 = st.columns([1, 6])
with col1:
    st.image("https://i.imgur.com/HZ9zpEw.png", width=60)  # use real hosted logo url
with col2:
    st.markdown("""
        <h2 style='margin-bottom:0;'>Christ Base Assembly</h2>
        <p style='font-size:0.85rem; color: #884400; margin-top:0;'>winning souls, building people...</p>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- Get Session Info ---
session_label, session_column = get_session()
if not session_column:
    st.warning("No session currently open for check-in.")
    st.stop()

# --- Main Logic ---
checkin_mode = st.radio("Select check-in mode:", ["New Registration", "Check-In by Phone or Tag ID"])

if checkin_mode == "New Registration":
    with st.form("new_reg"):
        name = st.text_input("Full Name")
        phone = st.text_input("Phone Number")
        tag = f"CBA{datetime.now().strftime('%H%M%S')}"
        submitted = st.form_submit_button("Register & Check-In")

        if submitted:
            sheet.append_row([name, phone, tag, "TRUE" if session_column == "attended_day1" else "",  # Day 1
                              "TRUE" if "day2" in session_column and "morning" in session_column else "",  # Day 2 Morning
                              "TRUE" if "day2" in session_column and "evening" in session_column else "",  # Day 2 Evening
                              "TRUE" if session_column == "attended_day3" else ""],
                             value_input_option="USER_ENTERED")
            st.success(f"Registered successfully. Tag ID: {tag}")
            if st.button("OK", on_click=clear_form_state):
                pass

elif checkin_mode == "Check-In by Phone or Tag ID":
    with st.form("checkin"):
        lookup = st.text_input("Enter Phone or Tag ID")
        submitted = st.form_submit_button("Find Record")

        if submitted:
            records = sheet.get_all_records()
            match = next((r for r in records if r["phone"] == lookup or r["tag"] == lookup), None)
            if not match:
                st.error("No matching record found.")
            else:
                st.success(f"Welcome {match['name']}!")
                if not match.get(session_column):
                    if st.form_submit_button("Check In Now"):
                        row_index = records.index(match) + 2  # account for header
                        sheet.update_cell(row_index, list(match.keys()).index(session_column) + 1, "TRUE")
                        st.success("Check-in successful!")
                else:
                    st.info("You are already checked in for this session.")
