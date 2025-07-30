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
# Only dedent & strip—no replace of "\\n"
info["private_key"] = textwrap.dedent(info["private_key"]).strip()
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(info, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(st.secrets["sheet_id"]).worksheet(st.secrets["sheet_name"])

# --- Load all records into DataFrame ---
records = sheet.get_all_records()
df = pd.DataFrame(records)

# Ensure required columns exist
for col in ["Last Update", "Updated full address"]:
    if col not in df.columns:
        sheet.add_cols(1)
        header = sheet.row_values(1)
        new_idx = len(header) + 1
        sheet.update_cell(1, new_idx, col)
        df[col] = ""

# Parse Last Update for sorting
if not df.empty:
    try:
        df["Last Update"] = pd.to_datetime(df["Last Update"])
    except Exception:
        pass

# --- Coordinator flow ---
groups = sorted(df['Group'].dropna().unique().tolist())
group = st.selectbox("Select your assigned group:", [""] + groups)
if not group:
    st.stop()

filtered = df[df['Group'] == group].copy()
if filtered.empty:
    st.info("No attendees found for this group.")
    st.stop()
filtered = filtered.sort_values("Last Update", ascending=False, na_position='last')

st.subheader(f"Attendees in Group: {group}")
st.dataframe(filtered[["name", "phone", "Last Update"]], use_container_width=True)

options = [f"{r['name']} ({r['tag']})" for _, r in filtered.iterrows()]
selected = st.selectbox("Select an attendee:", [""] + options)
if not selected:
    st.stop()

# Resolve selected row
sel_name, sel_tag = selected.rsplit("(", 1)[0].strip(), selected.split("(")[-1].strip(")")
match = filtered[(filtered['name'] == sel_name) & (filtered['tag'] == sel_tag)]
if match.empty:
    st.error("Could not find the selected attendee.")
    st.stop()
row_idx = match.index[0]
sheet_row = row_idx + 2  # account for header row

st.write(f"**Name:** {match.at[row_idx, 'name']}")
st.write(f"**Phone:** {match.at[row_idx, 'phone']}")
st.write(f"**Tag ID:** {match.at[row_idx, 'tag']}")

action = st.radio("Action:", ["Update Address", "Capture Follow-Up"])
tz = pytz.timezone("Africa/Lagos")
now_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

if action == "Update Address":
    current = match.at[row_idx, "Updated full address"]
    new_addr = st.text_input("Updated Full Address:", value=current or "")
    if st.button("Submit Address"):
        col_idx = df.columns.get_loc("Updated full address") + 1
        sheet.update_cell(sheet_row, col_idx, new_addr)
        last_idx = df.columns.get_loc("Last Update") + 1
        sheet.update_cell(sheet_row, last_idx, now_str)
        st.success("Address updated successfully.")

else:
    ftype = st.selectbox("Type of follow-up:", ["Call", "Physical visit"])
    result_opts = (["Not reachable","Switched off","Reached","Missed call"] 
                   if ftype=="Call" 
                   else ["Available","Not Available","Invalid Address"])
    result = st.selectbox("Result:", result_opts)
    soon = st.radio("Soon to be CBA member?", ["Next service","Soon"])
    remarks = st.text_area("Remarks:")
    if st.button("Submit Follow-Up"):
        follow_cols = sorted([c for c in df.columns if c.startswith("Follow_up")],
                             key=lambda x: int(x.replace("Follow_up","")))
        slot = next((c for c in follow_cols if not match.at[row_idx, c]), None)
        if not slot:
            num = len(follow_cols) + 1
            slot = f"Follow_up{num}"
            sheet.add_cols(1)
            hdr = sheet.row_values(1)
            new_i = len(hdr) + 1
            sheet.update_cell(1, new_i, slot)
            df[slot] = ""
            col_idx = new_i
        else:
            col_idx = df.columns.get_loc(slot) + 1

        step = slot.replace("Follow_up","")
        entry = f"{step}||{ftype}||{result}||{soon}||{remarks}"
        sheet.update_cell(sheet_row, col_idx, entry)

        last_idx = df.columns.get_loc("Last Update") + 1
        sheet.update_cell(sheet_row, last_idx, now_str)
        st.success("Follow-up report submitted successfully.")
