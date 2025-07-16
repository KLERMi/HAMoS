# ADMIN VERSION: streamlit_app_admin.py

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Table, MetaData

# Connect to the same SQLite database
engine = create_engine('sqlite:///registrations.db')
metadata = MetaData(bind=engine)
metadata.reflect()

registrations = metadata.tables['registrations']

def ui_header():
    st.set_page_config("HAMoS Admin", layout="centered")
    st.markdown("""
        <div style='display: flex; align-items: center; justify-content: center;'>
            <img src='https://raw.githubusercontent.com/KLERMi/HAMoS/refs/heads/main/cropped_image.png' style='height:60px; margin-right:10px;'>
            <div style='line-height: 0.8;'>
                <h1 style='font-family: Aptos Light; font-size: 26px; color: #4472C4; margin: 0;'>Christ Base Assembly</h1>
                <p style='font-family: Aptos Light; font-size: 14px; color: #ED7D31; margin: 0;'>winning souls, building people..</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

ui_header()

# Display and export data
with engine.connect() as conn:
    df = pd.read_sql_table('registrations', conn)

if df.empty:
    st.info("No registrations found.")
else:
    st.dataframe(df)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name="hamos_registrations.csv",
        mime="text/csv"
    )
