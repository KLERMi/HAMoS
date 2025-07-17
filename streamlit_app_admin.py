""import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from PIL import Image

# Load credentials and initialize gspread
creds_info = st.secrets["gcp_service_account"]
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
gc = gspread.authorize(credentials)

# Load sheet
sheet = gc.open_by_key(st.secrets["sheet_id"]).worksheet(st.secrets["sheet_name"])

# Set page config
st.set_page_config(page_title="HAMoS Admin Panel", layout="centered")

# Inject background image and custom styling
st.markdown(
    f"""
    <style>
        body {{
            background-image: url('https://raw.githubusercontent.com/KLERMi/HAMoS/refs/heads/main/cropped_image.png');
            background-size: 40%;
            background-position: center center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-blend-mode: lighten;
        }}
        .church-header {{
            text-align: center;
            font-family: 'Aptos Light', sans-serif;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }}
        .church-name {{
            font-size: 26px;
            color: #4472C4;
        }}
        .church-slogan {{
            font-size: 14px;
            color: #ED7D31;
        }}
    </style>
    <div class="church-header">
        <span class="church-name">Christ Base Assembly</span><br>
        <span class="church-slogan">winning souls, building people..</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.title("📋 Admin Check-In Panel")

search_mode = st.radio("Search by", ["Phone", "Tag ID", "Show All"])
query = st.text_input("Enter phone number or tag ID") if search_mode != "Show All" else None

records = sheet.get_all_records()
df = pd.DataFrame(records)

def mark_attendance(tag_id, day):
    idx = df[df['Tag ID'] == tag_id].index
    if not idx.empty:
        row = idx[0] + 2
        sheet.update_cell(row, df.columns.get_loc(f'Day {day} Check-In') + 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        st.success(f"✅ Day {day} Check-in marked for {tag_id}")
    else:
        st.error("Tag ID not found.")

def update_services(tag_id, selected_services):
    idx = df[df['Tag ID'] == tag_id].index
    if not idx.empty:
        row = idx[0] + 2
        for col in selected_services:
            sheet.update_cell(row, df.columns.get_loc(col) + 1, "✅")
        st.success("✅ Services provided updated.")

if search_mode == "Show All":
    st.dataframe(df)
elif query:
    if search_mode == "Phone":
        result = df[df['Phone'] == query]
    else:
        result = df[df['Tag ID'] == query]

    if not result.empty:
        st.subheader("Result:")
        st.dataframe(result)

        tag_id = result.iloc[0]['Tag ID']

        st.markdown("---")
        st.write(f"### ✅ Check-in for {tag_id}")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Check-in Day 2"):
                mark_attendance(tag_id, 2)
        with col2:
            if st.button("Check-in Day 3"):
                mark_attendance(tag_id, 3)

        st.markdown("---")
        st.write("### 🧾 Mark Services Provided")
        service_cols = [col for col in df.columns if col.startswith("Service ")]
        selected = st.multiselect("Select services provided:", service_cols)
        if st.button("✅ Update Services"):
            update_services(tag_id, selected)
    else:
        st.warning("No matching record found.")
