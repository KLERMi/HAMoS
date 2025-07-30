import streamlit as st
import pandas as pd
import gspread
import textwrap
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# --- Page and header styling ---
st.set_page_config(page_title="Follow-Up Tracker", layout="centered")
st.markdown("""
<style>
.header-flex { display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }
.church-logo { width: 48px; height: auto; }
.church-name { font-family: 'Aptos Light', sans-serif; font-size: 24px; color: #4472C4; margin: 0; }
</style>
<div class="header-flex">
  <img class="church-logo" src="https://raw.githubusercontent.com/KLERMi/HAMoS/main/cropped_image.png" />
  <p class="church-name">Christ Base Assembly - Follow-Up</p>
</div>
<hr>
""", unsafe_allow_html=True)

# --- Google Sheets setup via Service Account ---
info = dict(st.secrets["gcp_service_account"])
info["private_key"] = textwrap.dedent(info["private_key"]).replace("\\n", "\n").strip()
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(info, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(st.secrets["sheet_id"]).worksheet(st.secrets["sheet_name"])

# --- Load all records into DataFrame ---
records = sheet.get_all_records()
df = pd.DataFrame(records)
# Ensure columns exist or create them if needed
for col in ["Last Update", "Updated full address"]:
    if col not in df.columns:
        # Add column to sheet
        sheet.add_cols(1)
        header = sheet.row_values(1)
        new_col_idx = len(header) + 1
        sheet.update_cell(1, new_col_idx, col)
        df[col] = ""
# Parse Last Update as datetime for sorting (if not empty)
if not df.empty:
    try:
        df["Last Update"] = pd.to_datetime(df["Last Update"])
    except Exception:
        pass  # leave as is if parsing fails

# --- Select group ---
groups = sorted(df['Group'].dropna().unique().tolist())
group = st.selectbox("Select your assigned group:", [""] + groups)
if not group:
    st.stop()

# Filter attendees by group and sort by Last Update (recent first)
filtered = df[df['Group'] == group].copy()
if filtered.empty:
    st.info("No attendees found for this group.")
    st.stop()
filtered = filtered.sort_values(by="Last Update", ascending=False, na_position='last')

# Show attendees list
st.subheader(f"Attendees in Group: {group}")
st.dataframe(filtered[["name", "phone", "Last Update"]], use_container_width=True)

# Select one attendee
options = [f"{row['name']} ({row['tag']})" for _, row in filtered.iterrows()]
selected = st.selectbox("Select an attendee:", options)
if not selected:
    st.stop()

# Identify row index and record for selected attendee
sel_name, sel_tag = selected.rsplit("(", 1)[0].strip(), selected.split("(")[-1].strip(")")
match = filtered[(filtered['name'] == sel_name) & (filtered['tag'] == sel_tag)]
if match.empty:
    st.error("Could not find the selected attendee.")
    st.stop()
row_idx = match.index[0]  # index in original df (0-based, header row offset to 2)
sheet_row = row_idx + 2

# Show selected attendee info
st.write(f"**Name:** {match.at[row_idx, 'name']}")
st.write(f"**Phone:** {match.at[row_idx, 'phone']}")
st.write(f"**Tag ID:** {match.at[row_idx, 'tag']}")

# --- Choose operation ---
action = st.radio("Action:", ["Update Address", "Capture Follow-Up"])

tz = pytz.timezone("Africa/Lagos")
now_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

if action == "Update Address":
    current_address = match.at[row_idx, "Updated full address"]
    new_address = st.text_input("Updated Full Address:", value=current_address or "")
    if st.button("Submit Address"):
        # Update sheet
        col_idx = list(df.columns).index("Updated full address") + 1
        sheet.update_cell(sheet_row, col_idx, new_address)
        # Also update Last Update timestamp
        last_idx = list(df.columns).index("Last Update") + 1
        sheet.update_cell(sheet_row, last_idx, now_str)
        st.success("Address updated successfully.")

else:  # Capture Follow-Up
    followup_type = st.selectbox("Type of follow-up:", ["Call", "Physical visit"])
    if followup_type == "Call":
        result = st.selectbox("Result of call:", ["Not reachable", "Switched off", "Reached", "Missed call"])
    else:
        result = st.selectbox("Result of visit:", ["Available", "Not Available", "Invalid Address"])
    soon = st.radio("Soon to be CBA member?", ["Next service", "Soon"])
    remarks = st.text_area("Remarks:")

    if st.button("Submit Follow-Up"):
        # Determine follow-up column
        follow_cols = [c for c in df.columns if c.startswith("Follow_up")]
        follow_cols.sort(key=lambda x: int(x.split("Follow_up")[-1]) if x.split("Follow_up")[-1].isdigit() else 0)
        # Find first empty follow-up slot
        slot = None
        for col in follow_cols:
            if not match.at[row_idx, col]:  # empty cell
                slot = col
                break
        if not slot:
            # Create new Follow_up column
            next_num = len(follow_cols) + 1
            slot = f"Follow_up{next_num}"
            sheet.add_cols(1)
            header = sheet.row_values(1)
            new_idx = len(header) + 1
            sheet.update_cell(1, new_idx, slot)
            df[slot] = ""
            col_idx = new_idx
        else:
            col_idx = list(df.columns).index(slot) + 1

        # Prepare and write follow-up entry
        step_num = slot.replace("Follow_up", "")  # e.g. "1" or "2"
        entry = f"{step_num}||{followup_type}||{result}||{soon}||{remarks}"
        sheet.update_cell(sheet_row, col_idx, entry)
        # Update Last Update
        last_idx = list(df.columns).index("Last Update") + 1
        sheet.update_cell(sheet_row, last_idx, now_str)
        st.success("Follow-up report submitted successfully.")
