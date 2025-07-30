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

# --- Auth using service account ---
raw = st.secrets["service_account"]
info = dict(raw)
info["private_key"] = textwrap.dedent(info["private_key"]).strip()
SCOPES = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(info, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(st.secrets["sheet_id"]).worksheet(st.secrets["sheet_name"])

# --- Load data ---
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

# --- Group selection ---
groups = sorted(df.get('Group', pd.Series()).dropna().unique())
group = st.selectbox("Select your assigned group:", [""] + groups, key='selected_group')
if not group:
    st.stop()

# --- Display attendees in group, sorted by hidden Last Update ---
filtered = df[df.get('Group') == group].copy()
if filtered.empty:
    st.info("No attendees in this group.")
    st.stop()
# sort by Last Update descending (hidden column)
filtered = filtered.sort_values("Last Update", ascending=False, na_position='last')
st.subheader(f"Attendees in Group {group}")
display_df = filtered[['name', 'gender', 'phone', 'Updated full address']].rename(
    columns={'name':'Name', 'gender':'Gender', 'phone':'Phone', 'Updated full address':'Address'}
)
st.table(display_df)

# --- Pick an attendee ---
name_to_phone = {row['name']: row['phone'] for _, row in filtered.iterrows()}
selected_name = st.selectbox("Pick an attendee by name:", [""] + list(name_to_phone.keys()), key='selected_name')
if not selected_name:
    st.stop()
selected_phone = name_to_phone[selected_name]
match = filtered[filtered['phone'] == selected_phone].iloc[0]
idx = match.name
row_num = idx + 2

# --- Show attendee info ---
st.write(f"**{match.get('name','')}** — {selected_phone} — {match.get('tag','')}")

# --- Choose action ---
action = st.radio("Action:", ["Update Address","Capture Follow-Up"], key='action')
now = datetime.now(pytz.timezone("Africa/Lagos")).strftime("%Y-%m-%d %H:%M:%S")

# --- Address update flow ---
if action == "Update Address":
    current = match.get('Updated full address','') or ''
    new_addr = st.text_input("New Address:", value=current, key='new_addr')
    if st.button("Submit Address", key='submit_addr'):
        sheet.update_cell(row_num, df.columns.get_loc('Updated full address')+1, new_addr)
        sheet.update_cell(row_num, df.columns.get_loc('Last Update')+1, now)
        st.success("Address updated successfully.")

# --- Follow-up capture flow ---
else:
    ftype = st.selectbox("Type of follow-up:", ["Call","Physical visit"], key='ftype')
    if ftype == 'Call':
        result = st.selectbox("Result of call:", ["Not reachable","Switched off","Reached","Missed call"], key='result')
    else:
        result = st.selectbox("Result of visit:", ["Available","Not Available","Invalid Address"], key='result')
    soon = st.radio("Soon to be CBA member?", ["Next service","Soon"], key='soon')
    remarks = st.text_area("Remarks:", key='remarks')

    if st.button("Submit Follow-Up", key='submit_followup'):
        follow_cols = sorted([c for c in df.columns if c.startswith('Follow_up')],
                             key=lambda x: int(x.replace('Follow_up','')) if x.replace('Follow_up','').isdigit() else 0)
        slot = next((c for c in follow_cols if not match.get(c)), None)
        if not slot:
            slot = f'Follow_up{len(follow_cols)+1}'
            header = sheet.row_values(1)
            new_idx = len(header)+1
            sheet.add_cols(1)
            sheet.update_cell(1, new_idx, slot)
        col_idx = df.columns.get_loc(slot)+1
        entry = f"{slot.replace('Follow_up','')}||{ftype}||{result}||{soon}||{remarks}"
        sheet.update_cell(row_num, col_idx, entry)
        sheet.update_cell(row_num, df.columns.get_loc('Last Update')+1, now)
        st.success("Follow-up report submitted.")
