import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Setup credentials
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["service_account"], scopes=scope)
client = gspread.authorize(creds)

# Load Google Sheet
sheet = client.open_by_key(st.secrets["sheet_id"]).worksheet(st.secrets["sheet_name"])
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Timestamp
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# State reset utility
def reset_state():
    for k in list(st.session_state.keys()):
        del st.session_state[k]

# Dropdown by name, fetch phone + row
names = df["name"].dropna().unique()
selected_name = st.selectbox("Select a name to follow up", names)
match = df[df["name"] == selected_name].iloc[0]
phone = match["phone"]
row_num = df[df["phone"] == phone].index[0] + 2  # header row + 1-indexing

# Action radio
action = st.radio("Choose an action", ["View", "Update Address", "Capture Follow-Up"])

if action == "View":
    st.write("**Details for Follow-Up:**")
    st.write(match)

elif action == "Update Address":
    current = match.get("Updated full address", "")
    new_addr = st.text_input("New Address", value=current)

    if st.button("Submit Address"):
        sheet.update_cell(row_num, df.columns.get_loc("Updated full address") + 1, new_addr)
        sheet.update_cell(row_num, df.columns.get_loc("Last Update") + 1, now)
        st.success("Address updated.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Follow Up"):
            st.session_state['action'] = "Capture Follow-Up"
            st.experimental_rerun()
    with col2:
        if st.button("Next"):
            reset_state()
            st.experimental_rerun()

elif action == "Capture Follow-Up":
    st.write(f"**Follow-Up for:** {selected_name} ({phone})")
    note = st.text_area("Enter follow-up note")

    if st.button("Save Follow-Up"):
        sheet.update_cell(row_num, df.columns.get_loc("Follow-Up Note") + 1, note)
        sheet.update_cell(row_num, df.columns.get_loc("Last Update") + 1, now)
        st.success("Follow-Up saved.")

    if st.button("Next"):
        reset_state()
        st.experimental_rerun()
