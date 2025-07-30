import streamlit as st
import pandas as pd
import gspread
import textwrap
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# --- Page setup ---
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

# --- Auth using fresh JSON secret ---
raw = st.secrets["service_account"]
info = dict(raw)
info["private_key"] = textwrap.dedent(info["private_key"]).strip()
SCOPES = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(info, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(st.secrets["sheet_id"]).worksheet(st.secrets["sheet_name"])

# --- Load DataFrame & ensure columns ---
records = sheet.get_all_records()
df = pd.DataFrame(records)
for col in ["Last Update", "Updated full address"]:
    if col not in df.columns:
        header = sheet.row_values(1)
        idx = len(header) + 1
        sheet.add_cols(1)
        sheet.update_cell(1, idx, col)
        df[col] = ""
if not df.empty:
    try:
        df["Last Update"] = pd.to_datetime(df["Last Update"])
    except:
        pass

# --- Coordinator flow ---
groups = sorted(df.get('Group', pd.Series()).dropna().unique())
group = st.selectbox("Select your assigned group:", [""] + groups)
if not group:
    st.stop()

filtered = df[df.get('Group') == group].copy()
if filtered.empty:
    st.info("No attendees in this group.")
    st.stop()
filtered = filtered.sort_values("Last Update", ascending=False, na_position='last')

# Display attendees
st.subheader(f"Attendees – Group {group}")
st.dataframe(filtered[["name","phone","Last Update"]], use_container_width=True)

# Select by name, fetch by phone
name_to_phone = {row['name']: row['phone'] for _, row in filtered.iterrows()}
selected_name = st.selectbox("Pick an attendee by name:", [""] + list(name_to_phone.keys()))
if not selected_name:
    st.stop()
selected_phone = name_to_phone[selected_name]

# Locate record by phone
match = filtered[filtered['phone'] == selected_phone].iloc[0]
idx = match.name  # DataFrame index
row_num = idx + 2  # account for header row

# Show selection details
st.write(f"**{match.get('name','')}** — {selected_phone} — {match.get('tag','')} ")

action = st.radio("Action:", ["Update Address","Capture Follow-Up"])
now = datetime.now(pytz.timezone("Africa/Lagos")).strftime("%Y-%m-%d %H:%M:%S")

if action == "Update Address":
    current = match.get('Updated full address','') or ''
    new_addr = st.text_input("New Address:", value=current)
    if st.button("Submit Address"):
        addr_col = df.columns.get_loc('Updated full address') + 1
        sheet.update_cell(row_num, addr_col, new_addr)
        lu_col = df.columns.get_loc('Last Update') + 1
        sheet.update_cell(row_num, lu_col, now)
        st.success("Address updated successfully.")

else:
    # Capture Follow-Up form
    ftype = st.selectbox("Type of follow-up:", ["Call","Physical visit"])
    if ftype == 'Call':
        result = st.selectbox("Result of call:", ["Not reachable","Switched off","Reached","Missed call"])
    else:
        result = st.selectbox("Result of visit:", ["Available","Not Available","Invalid Address"])
    soon = st.radio("Soon to be CBA member?", ["Next service","Soon"])
    remarks = st.text_area("Remarks:")

    if st.button("Submit Follow-Up"):
        follow_cols = sorted([c for c in df.columns if c.startswith('Follow_up')],
                             key=lambda x: int(x.replace('Follow_up','')) if x.replace('Follow_up','').isdigit() else 0)
        slot = next((c for c in follow_cols if not match.get(c)), None)
        if not slot:
            slot = f'Follow_up{len(follow_cols) + 1}'
            header = sheet.row_values(1)
            new_idx = len(header) + 1
            sheet.add_cols(1)
            sheet.update_cell(1, new_idx, slot)
            df[slot] = ''
            col_idx = new_idx
        else:
            col_idx = df.columns.get_loc(slot) + 1

        entry = f"{slot.replace('Follow_up','')}||{ftype}||{result}||{soon}||{remarks}"
        sheet.update_cell(row_num, col_idx, entry)
        lu_col = df.columns.get_loc('Last Update') + 1
        sheet.update_cell(row_num, lu_col, now)
        st.success("Follow-up report submitted.")
