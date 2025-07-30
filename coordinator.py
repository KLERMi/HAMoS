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
info = st.secrets["service_account"]  # dict with all JSON fields
# Ensure private_key has real newlines
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
    try: df["Last Update"] = pd.to_datetime(df["Last Update"])
    except: pass

# --- Coordinator flow ---
groups = sorted(df['Group'].dropna().unique())
group = st.selectbox("Select your assigned group:", [""] + groups)
if not group:
    st.stop()

filtered = df[df['Group']==group].copy().sort_values("Last Update", ascending=False, na_position='last')
if filtered.empty:
    st.info("No attendees in this group.")
    st.stop()

st.subheader(f"Attendees – Group {group}")
st.dataframe(filtered[["name","phone","Last Update"]], use_container_width=True)

opts = [f"{r['name']} ({r['tag']})" for _,r in filtered.iterrows()]
sel = st.selectbox("Pick an attendee:", [""] + opts)
if not sel:
    st.stop()

# Resolve selection
nm, tg = sel.rsplit("(",1)
tg = tg.rstrip(")")
match = filtered[(filtered['name']==nm.strip())&(filtered['tag']==tg)]
if match.empty:
    st.error("Selection error.")
    st.stop()
idx = match.index[0]; row_num = idx+2

st.write(f"**{match.at[idx,'name']}**  —  {match.at[idx,'phone']}  —  {match.at[idx,'tag']}")

action = st.radio("Action:", ["Update Address","Capture Follow-Up"])
now = datetime.now(pytz.timezone("Africa/Lagos")).strftime("%Y-%m-%d %H:%M:%S")

if action=="Update Address":
    cur = match.at[idx,"Updated full address"] or ""
    addr = st.text_input("New address:", value=cur)
    if st.button("Submit Address"):
        c = df.columns.get_loc("Updated full address")+1
        sheet.update_cell(row_num, c, addr)
        lu = df.columns.get_loc("Last Update")+1
        sheet.update_cell(row_num, lu, now)
        st.success("Address updated.")

else:
    ftype = st.selectbox("Mode:", ["Call","Physical visit"])
    res_opts = ["Not reachable","Switched off","Reached","Missed call"] if ftype=="Call" else ["Available","Not Available","Invalid Address"]
    res = st.selectbox("Result:", res_opts)
    soon = st.radio("Soon to be member?", ["Next service","Soon"])
    rem = st.text_area("Remarks:")
    if st.button("Submit Follow-Up"):
        fu_cols = sorted([c for c in df.columns if c.startswith("Follow_up")], key=lambda x:int(x.replace("Follow_up","")))
        slot = next((c for c in fu_cols if not match.at[idx,c]), None)
        if not slot:
            n = len(fu_cols)+1; slot = f"Follow_up{n}"
            hdr = sheet.row_values(1); new_i=len(hdr)+1
            sheet.add_cols(1); sheet.update_cell(1,new_i,slot); df[slot]=""
            col_i=new_i
        else:
            col_i = df.columns.get_loc(slot)+1

        seq = slot.replace("Follow_up","")
        entry = f"{seq}||{ftype}||{res}||{soon}||{rem}"
        sheet.update_cell(row_num, col_i, entry)
        lu = df.columns.get_loc("Last Update")+1
        sheet.update_cell(row_num, lu, now)
        st.success("Follow-up saved.")
