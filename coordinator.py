import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Load credentials
creds_dict = st.secrets["service_account"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Load sheet
sheet = client.open_by_key(st.secrets["sheet_id"]).worksheet(st.secrets["sheet_name"])
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Utilities
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def reset_state():
    for k in list(st.session_state.keys()):
        del st.session_state[k]

# Select name to lookup by phone
names = df["name"].dropna().unique()
selected_name = st.selectbox("Select a name to follow up", names)
match = df[df["name"] == selected_name].iloc[0]
phone = match["phone"]
row_num = df[df["phone"] == phone].index[0] + 2  # +2 for header + 1-indexing

# Action selector
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
        st.success("Address updated successfully.")

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
