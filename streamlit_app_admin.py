import streamlit as st
import pandas as pd
import gspread
import textwrap
from google.oauth2.service_account import Credentials

# --- Login helpers ---
def do_login():
    if VALID_USERS.get(st.session_state.login_user) == st.session_state.login_pass:
        st.session_state.logged_in = True
        st.session_state.login_error = False
    else:
        st.session_state.login_error = True

def do_logout():
    st.session_state.logged_in = False

# --- Admin Login (from secrets) ---
VALID_USERS = st.secrets["admin_credentials"]

# Initialize session_state
st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("login_error", False)
st.session_state.setdefault("login_user", "")
st.session_state.setdefault("login_pass", "")
st.session_state.setdefault("selected_group", None)
st.session_state.setdefault("prev_group", None)
st.session_state.setdefault("selected_name", None)

with st.sidebar:
    if not st.session_state.logged_in:
        st.header("Admin Login")
        st.text_input("Username", key="login_user")
        st.text_input("Password", type="password", key="login_pass")
        st.button("Login", on_click=do_login)
        if st.session_state.login_error:
            st.error("Invalid login details, please retry.")
    else:
        st.write(f"👋 Logged in as **{st.session_state.login_user}**")
        st.button("Logout", on_click=do_logout)

if not st.session_state.logged_in:
    st.stop()

# --- Page config & compact header styling ---
st.set_page_config(page_title="HAMoS Admin Portal", layout="centered")

st.markdown(
    """
    <style>
      .header-flex {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1rem;
      }
      .church-logo {
        width: 64px;
        height: auto;
      }
      .church-text {
        line-height: 0.8;
      }
      .church-name {
        font-family: 'Aptos Light', sans-serif;
        font-size: 30px;
        color: #4472C4;
        margin: 0;
      }
      .church-slogan {
        font-family: 'Aptos Light', sans-serif;
        font-size: 11px;
        color: #ED7D31;
        margin: 0;
      }
    </style>

    <div class="header-flex">
      <img class="church-logo" src="https://raw.githubusercontent.com/KLERMi/HAMoS/refs/heads/main/cropped_image.png" />
      <div class="church-text">
        <p class="church-name">Christ Base Assembly</p>
        <p class="church-slogan">winning souls, building people…</p>
      </div>
    </div>
    <hr>
    """,
    unsafe_allow_html=True
)

# --- Google Sheets Setup ---
raw = st.secrets["gcp_service_account"]
creds_info = dict(raw)
creds_info["private_key"] = (
    textwrap.dedent(creds_info["private_key"])
        .replace("\\n", "\n")
        .strip()
)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
credentials = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(st.secrets["sheet_id"]).worksheet(st.secrets["sheet_name"])

# --- Load DataFrame ---
records = sheet.get_all_records()
df = pd.DataFrame(records)
df['phone'] = df['phone'].astype(str).str.strip()

# --- Group selection ---
group_list = sorted(df['group'].unique()) if 'group' in df.columns else ['Default']
selected_group = st.selectbox("Select Group", group_list, key="selected_group")

# Detect group change and reset selected_name
if st.session_state.prev_group and selected_group != st.session_state.prev_group:
    st.session_state.selected_name = None
    st.session_state.prev_group = selected_group
    st.warning("Group changed. Please re-enter Tag ID or Phone Number.")
    st.stop()
else:
    st.session_state.prev_group = selected_group

# --- Lookup & Update Services ---
st.subheader("🔍 Lookup and Update Services")
q = st.text_input("Enter Tag ID or Phone Number").strip()

if q:
    q_up = q.upper()
    filtered = df[df['group'] == selected_group]
    filtered = filtered[
        (filtered['tag'].astype(str).str.upper() == q_up) |
        (filtered['phone'] == q)
    ]

    if filtered.empty:
        st.warning("No matching record found.")
    else:
        # Protect against empty selection
        match_df = filtered
        if match_df.empty:
            st.warning("Name not found in selected group.")
            st.session_state.selected_name = None
            st.stop()
        else:
            rec = match_df.iloc[0]

            # Display key details
            st.markdown(f"**Name:** {rec.get('name', '—')}")
            st.markdown(f"**Phone:** {rec.get('phone', '—')}")
            st.markdown(f"**Tag ID:** {rec.get('tag', '—')}")
            st.markdown(f"**Membership:** {rec.get('membership', '')}")

            # Registered services
            st.markdown("**Registered Services:**")
            services = rec.get('services', '')
            services = [s.strip() for s in services.split(',')] if services else []

            for svc in services:
                st.write(f"- {svc}")

            # --- Updated "Mark Services Received" block ---
            st.markdown("**Mark Services Received:**")
            col_name = "Services Received"

            # 1) Ensure the column exists
            if col_name not in df.columns:
                sheet.add_cols(1)
                header_row = sheet.row_values(1)
                new_col_idx = len(header_row) + 1
                sheet.update_cell(1, new_col_idx, col_name)
                df[col_name] = ""

            # 2) Render checkboxes with unique keys
            received = []
            row_number = match_df.index[0] + 2  # header row offset
            for svc in services:
                key = f"svc_{row_number}_{svc}"
                if st.checkbox(svc, key=key):
                    received.append(svc)

            # 3) On submit, update via update_cell and patch local df
            if st.button("Submit Update"):
                col_idx = df.columns.get_loc(col_name) + 1
                sheet.update_cell(row_number, col_idx, ", ".join(received))
                df.at[match_df.index[0], col_name] = ", ".join(received)
                st.success("Updated successfully.")

# --- Download All Records ---
st.markdown("---")
st.subheader("📥 Download All Records")
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("Download CSV", csv, "hamos_admin_data.csv", "text/csv")
