import streamlit as st
import pandas as pd
import gspread
import textwrap
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# --- Page setup ---
st.set_page_config(page_title="Follow-Up Tracker", layout="centered")
# Responsive CSS for button grid
st.markdown("""
<style>
.header-flex { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; }
.church-logo { width: 36px; height: auto; }
.church-name { font-family: 'Aptos Light', sans-serif; font-size: 20px; color: #4472C4; margin: 0; }
.grid-container {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.grid-item {
  flex: 1 0 calc(33.33% - 0.5rem);
  max-width: calc(33.33% - 0.5rem);
  box-sizing: border-box;
}
@media only screen and (max-width: 768px) {
  .grid-item {
    flex: 1 0 calc(50% - 0.5rem);
    max-width: calc(50% - 0.5rem);
  }
}
@media only screen and (max-width: 480px) {
  .grid-item {
    flex: 1 0 100%;
    max-width: 100%;
  }
}
.stButton>button {
  width: 100%;
  font-size: 0.8rem;
  padding: 0.3rem;
  white-space: normal;
  word-wrap: break-word;
}
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

# --- Reset attendee selection if group changes ---
if st.session_state.get('prev_group') and st.session_state['prev_group'] != group:
    st.session_state.pop('selected_name', None)
    st.session_state['prev_group'] = group
    st.success("Group changed")
    st.rerun()
st.session_state['prev_group'] = group

# --- Prepare attendees for this group ---
filtered = df[df.get('Group') == group].copy()
if filtered.empty:
    st.info("No attendees in this group.")
    st.stop()
# sort by hidden Last Update
filtered = filtered.sort_values("Last Update", ascending=False, na_position='last')
display_df = filtered[['name', 'gender', 'phone', 'Updated full address']].rename(
    columns={'name':'Name','gender':'Gender','phone':'Phone','Updated full address':'Address'}
)

# --- 1. Select attendee via clickable buttons ---
st.subheader(f"Select Attendee in Group {group}")
st.markdown('<div class="grid-container">', unsafe_allow_html=True)
for i, name in enumerate(display_df['Name']):
    with st.container():
        st.markdown('<div class="grid-item">', unsafe_allow_html=True)
        if st.button(name, key=f'name_btn_{i}'):
            st.session_state['selected_name'] = name
        st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if 'selected_name' not in st.session_state:
    st.stop()
selected_name = st.session_state['selected_name']

# --- 2. Fields / action for record updates ---
match = filtered[filtered['name'] == selected_name]
if match.empty:
    st.warning("Group changed. Please reselect an attendee.")
    st.stop()
match = match.iloc[0]
idx = match.name
row_num = idx + 2
selected_phone = match['phone']

st.write(f"**{match.get('name','')}** — {selected_phone} — {match.get('tag','')}" )
action = st.radio("Action:", ["Update Address","Capture Follow-Up"], key='action')
now = datetime.now(pytz.timezone("Africa/Lagos")).strftime("%Y-%m-%d %H:%M:%S")

if action == "Update Address":
    current = match.get('Updated full address','') or ''
    new_addr = st.text_input("New Address:", value=current, key='new_addr')
    if st.button("Submit Address", key='submit_addr'):
        sheet.update_cell(row_num, df.columns.get_loc('Updated full address')+1, new_addr)
        sheet.update_cell(row_num, df.columns.get_loc('Last Update')+1, now)
        st.success("Address updated successfully.")
else:
    ftype = st.selectbox("Type of follow-up:", ["Call","Physical visit"], key='ftype')
    if ftype == 'Call':
        result = st.selectbox("Result of call:", ["Not reachable","Switched off","Reached","Missed call"], key='result')
    else:
        result = st.selectbox("Result of visit:", ["Available","Not Available","Invalid Address"], key='result')
    soon = st.radio("Soon to be CBA member?", ["Next service","Soon"], key='soon')
    remarks = st.text_area("Remarks:", key='remarks')
    if st.button("Submit Follow-Up", key='submit_followup'):
        follow_cols = sorted([c for c in df.columns if c.startswith('Follow_up')], key=lambda x: int(x.replace('Follow_up','')) if x.replace('Follow_up','').isdigit() else 0)
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

# --- 3. List of attendees with collapse/expand ---
with st.expander("Show/Hide Attendees List", expanded=False):
    html = display_df.to_html(index=False)
    st.markdown(html, unsafe_allow_html=True)
