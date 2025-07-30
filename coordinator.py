import streamlit as st
import pandas as pd
import gspread
import textwrap
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# --- Main application wrapped to catch exceptions ---
def main():
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

    # --- State reset helper ---
    def reset_state():
        for key in ['selected_name', 'action', 'ftype', 'result', 'soon', 'remarks']:
            if key in st.session_state:
                del st.session_state[key]

    # Callback to switch to follow-up
    def go_to_followup():
        st.session_state.action = "Capture Follow-Up"

    # --- Step 1: Group Selection ---
    groups = sorted(df.get('Group', pd.Series()).dropna().unique())
    group = st.selectbox("Select your assigned group:", [""] + groups, key='selected_group')
    if not group:
        st.stop()

    # --- Step 2: Filter and select attendee ---
    filtered = df[df.get('Group') == group].copy()
    if filtered.empty:
        st.info("No attendees in this group.")
        st.stop()
    filtered = filtered.sort_values("Last Update", ascending=False, na_position='last')

    name_to_phone = {row['name']: row['phone'] for _, row in filtered.iterrows()}

    # Auto-select if no name is already picked
    if 'selected_name' not in st.session_state:
        seen_phones = set(df[df['Last Update'].notna()]['phone'])
        unseen = filtered[~filtered['phone'].isin(seen_phones)]
        st.session_state['selected_name'] = unseen.iloc[0]['name'] if not unseen.empty else filtered.sample(1).iloc[0]['name']

    selected_name = st.session_state['selected_name']
    selected_phone = name_to_phone[selected_name]
    match = filtered[filtered['phone'] == selected_phone].iloc[0]
    idx = match.name
    row_num = idx + 2

    # --- Display attendee info ---
    st.write(f"**{match.get('name','')}** — {selected_phone} — {match.get('tag','')} ")

    # --- Step 3: Choose action ---
    action = st.radio("Action:", ["Update Address","Capture Follow-Up"], key='action')
    now = datetime.now(pytz.timezone("Africa/Lagos")).strftime("%Y-%m-%d %H:%M:%S")

    # --- Handle Update Address ---
    if action == "Update Address":
        current = match.get('Updated full address','') or ''
        new_addr = st.text_input("New Address:", value=current, key='new_addr')
        if st.button("Submit Address", key='submit_addr'):
            sheet.update_cell(row_num, df.columns.get_loc('Updated full address')+1, new_addr)
            sheet.update_cell(row_num, df.columns.get_loc('Last Update')+1, now)
            st.success("Address updated successfully.")
        if st.button("Complete", key='complete_addr'):
            reset_state()
            st.experimental_rerun()
        if st.button("Next", key='next_to_followup', on_click=go_to_followup):
            st.experimental_rerun()

    # --- Handle Capture Follow-Up ---
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
        if st.button("Complete", key='complete_followup'):
            reset_state()
            st.experimental_rerun()

if __name__ == '__main__':
    try:
        main()
    except Exception:
        # Show generic message, errors logged elsewhere
        st.error("An unexpected error occurred. Please try again later.")
