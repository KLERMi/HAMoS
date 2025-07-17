# streamlit_app_admin.py
import streamlit as st
import pandas as pd
from hamos_db import init_db, get_session, Registration

# Initialize the shared database
init_db()

# Page configuration
st.set_page_config(page_title="HAMoS Admin", layout="centered")

# Header banner
st.markdown("""
<div style='display:flex; align-items:center; justify-content:center;'>
  <img src='https://raw.githubusercontent.com/KLERMi/HAMoS/main/cropped_image.png' style='height:60px; margin-right:10px;'>
  <div style='line-height:0.8;'>
    <h1 style='font-family:Aptos Light; font-size:26px; color:#4472C4; margin:0;'>Christ Base Assembly</h1>
    <p style='font-family:Aptos Light; font-size:14px; color:#ED7D31; margin:0;'>winning souls, building people..</p>
  </div>
</div>
""", unsafe_allow_html=True)

# Authentication
def authenticate():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    with st.sidebar:
        profile = st.text_input("Profile ID")
        pwd     = st.text_input("Password", type="password")
        if st.button("Login"):
            if (profile, pwd) in [("HAM1","christbase22"),("HAM2","christbase23")]:
                st.session_state.logged_in = True
            else:
                st.error("Invalid credentials")
    if not st.session_state.logged_in:
        st.stop()

authenticate()

# Fetch recent registrations
db = get_session()
records = db.query(Registration).order_by(Registration.ts.desc()).limit(10).all()
df_recent = pd.DataFrame([r.__dict__ for r in records]).drop(columns=['_sa_instance_state'])

st.title("HAMoS Admin Dashboard")
st.subheader("Recent Registrations")
if df_recent.empty:
    st.info("No records yet.")
else:
    st.dataframe(df_recent)

# Search functionality
with st.expander("Search Records"):
    query = st.text_input("Phone or Tag ID")
    if st.button("Search"):
        results = db.query(Registration).filter(
            (Registration.phone == query) | (Registration.tag_id == query)
        ).all()
        df_search = pd.DataFrame([r.__dict__ for r in results]).drop(columns=['_sa_instance_state'])
        if df_search.empty:
            st.info("No matching record found.")
        else:
            st.write(df_search)

# Download all registrations
all_recs = db.query(Registration).all()
df_all = pd.DataFrame([r.__dict__ for r in all_recs]).drop(columns=['_sa_instance_state'])

st.download_button(
    label="Download All Registrations",
    data=df_all.to_csv(index=False).encode(),
    file_name="hamos_registrations.csv",
    mime="text/csv"
)
