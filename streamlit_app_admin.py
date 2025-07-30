import streamlit as st
import pandas as pd
import gspread
import textwrap
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# --- Streamlit configuration ---
st.set_page_config(page_title="Follow-Up Tracker", layout="centered")
st.set_option('server.showErrorDetails', False)

# --- CSS and Header ---
st.markdown("""
<style>
.header-flex { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; }
.church-logo { width: 36px; height: auto; }
.church-name { font-family: 'Aptos Light', sans-serif; font-size: 20px; color: #4472C4; margin: 0; }
.grid-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 0.5rem; margin-bottom: 1rem; }
.grid-item { flex: 1 0 calc(33.33% - 0.5rem); max-width: calc(33.33% - 0.5rem); box-sizing: border-box; }
@media (max-width: 768px) { .grid-item { flex: 1 0 calc(50% - 0.5rem); max-width: calc(50% - 0.5rem); } }
@media (max-width: 480px) { .grid-item { flex: 1 0 100%; max-width: 100%; } }
.stButton>button { width: 100%; font-size: 0.8rem; padding: 0.3rem; white-space: normal; word-wrap: break-word; }
</style>
<div class="header-flex">
  <img class="church-logo" src="https://raw.githubusercontent.com/KLERMi/HAMoS/main/cropped_image.png" />
  <p class="church-name">Christ Base Assembly - Follow-Up</p>
</div>
<hr>
""", unsafe_allow_html=True)

try:
    # --- Authentication ---
    creds_info = dict(st.secrets["service_account"])
    creds_info["private_key"] = textwrap.dedent(creds_info["private_key"]).strip()
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["sheet_id"]).worksheet(st.secrets["sheet_name"])

    # --- Load and prepare data ---
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    # Ensure columns exist
    for col in ["Last Update", "Updated full address"]:
        if col not in df.columns:
            header = sheet.row_values(1)
            sheet.add_cols(1)
            sheet.update_cell(1, len(header) + 1, col)
            df[col] = ""
    if not df.empty:
        df["Last Update"] = pd.to_datetime(df["Last Update"], errors="ignore")

    # --- Select group ---
    groups = sorted(df.get('Group', pd.Series()).dropna().unique())
    group = st.selectbox("Select your assigned group:", [None] + groups)
    if not group:
        st.stop()

    # Reset selection on group change
    if st.session_state.get('prev_group') != group:
        st.session_state['selected_name'] = None
    st.session_state['prev_group'] = group

    # --- Filter attendees ---
    group_df = df[df['Group'] == group].copy()
    if group_df.empty:
        st.info("No attendees in this group.")
        st.stop()
    group_df = group_df.sort_values("Last Update", ascending=False, na_position='last')

    # Rename display columns
    display_df = group_df.rename(columns={
        'name':'Name', 'gender':'Gender', 'phone':'Phone', 'Updated full address':'Address'
    })

    # --- Default selection ---
    if 'selected_name' not in st.session_state or st.session_state['prev_group'] != group:
        # pick first
        st.session_state['selected_name'] = display_df['Name'].iat[0]

    selected_name = st.session_state['selected_name']

    # --- Attendee buttons ---
    st.subheader(f"Select Attendee in Group {group}")
    st.markdown('<div class="grid-container">', unsafe_allow_html=True)
    for i, name in enumerate(display_df['Name']):
        st.markdown('<div class="grid-item">', unsafe_allow_html=True)
        if st.button(name, key=f'name_btn_{i}'):
            st.session_state['selected_name'] = name
            selected_name = name
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Safe record retrieval ---
    match_rows = group_df[group_df['name'] == selected_name]
    if match_rows.empty:
        # reset and rerun
        st.warning("Selection lost; defaulting to first attendee.")
        st.session_state['selected_name'] = display_df['Name'].iat[0]
        st.experimental_rerun()
    match = match_rows.iloc[0]
    idx = match.name
    row_num = idx + 2
    selected_phone = match.get('phone', '')

    # --- Display and actions ---
    st.write(f"**{match.get('name','')}** — {selected_phone} — {match.get('tag','')}")
    action = st.radio("Action:", ["Update Address","Capture Follow-Up"])
    now = datetime.now(pytz.timezone("Africa/Lagos")).strftime("%Y-%m-%d %H:%M:%S")

    if action == "Update Address":
        current = match.get('Updated full address', '')
        new_addr = st.text_input("New Address:", value=current)
        if st.button("Submit Address"):
            c_idx = df.columns.get_loc('Updated full address') + 1
            sheet.update_cell(row_num, c_idx, new_addr)
            sheet.update_cell(row_num, df.columns.get_loc('Last Update') + 1, now)
            st.success("Address updated.")
    else:
        ftype = st.selectbox("Type of follow-up:", ["Call","Physical visit"])
        result = st.selectbox("Result:", ["Not reachable","Switched off","Reached","Missed call"] if ftype=='Call' else ["Available","Not Available","Invalid Address"] )
        soon = st.radio("Soon to be CBA member?", ["Next service","Soon"])
        remarks = st.text_area("Remarks:")
        if st.button("Submit Follow-Up"):
            follow_cols = sorted([c for c in df.columns if c.startswith('Follow_up')], key=lambda x: int(x.replace('Follow_up','')) if x.replace('Follow_up','').isdigit() else 0)
            slot = next((c for c in follow_cols if not match.get(c)), None)
            if not slot:
                slot = f'Follow_up{len(follow_cols)+1}'
                header = sheet.row_values(1)
                sheet.add_cols(1)
                sheet.update_cell(1, len(header)+1, slot)
            col_idx = df.columns.get_loc(slot) + 1
            entry = f"{slot.replace('Follow_up','')}||{ftype}||{result}||{soon}||{remarks}"
            sheet.update_cell(row_num, col_idx, entry)
            sheet.update_cell(row_num, df.columns.get_loc('Last Update') + 1, now)
            st.success("Follow-up submitted.")

    # --- Expandable list ---
    with st.expander("Show/Hide Attendees List"):
        st.dataframe(display_df[['Name','Gender','Phone','Address']])

except Exception:
    st.error("An unexpected error occurred. Please try again later.")
