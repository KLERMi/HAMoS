import streamlit as st
from datetime import datetime
from sqlalchemy import create_engine, Table, MetaData
import pandas as pd

ADMIN_MODE = True
DATABASE_URL = 'sqlite:///registrations.db'

engine = create_engine(DATABASE_URL)
metadata = MetaData()
metadata.reflect(bind=engine)
registrations = metadata.tables['registrations']

st.set_page_config("HAMoS Admin Panel", layout="centered")
st.markdown("""
    <div style='display: flex; align-items: center; justify-content: center;'>
        <img src='https://raw.githubusercontent.com/KLERMi/HAMoS/refs/heads/main/cropped_image.png' style='height:60px; margin-right:10px;'>
        <div>
            <h1 style='font-family: Aptos Light; font-size: 26px; color: #4472C4; margin: 0;'>Christ Base Assembly</h1>
            <p style='font-family: Aptos Light; font-size: 14px; color: #ED7D31; margin: 0;'>winning souls, building people..</p>
        </div>
    </div>
""", unsafe_allow_html=True)

df = pd.read_sql_table('registrations', DATABASE_URL)

if st.checkbox("Show all registrations"):
    st.dataframe(df)

st.download_button("Download CSV", data=df.to_csv(index=False), file_name="hamos_registrations.csv", mime="text/csv")
