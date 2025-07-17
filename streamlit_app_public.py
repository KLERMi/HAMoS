# streamlit_app_public.py
import streamlit as st
from datetime import datetime
from hamos_db import init_db, get_session, Registration

# Initialize database
init_db()

# Page configuration
st.set_page_config(page_title="HAMoS Registration", layout="centered")

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

# Identify source
PAGE_SOURCE = 'public'

# Submission state
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# Registration form
if not st.session_state.submitted:
    with st.form('registration_form'):
        phone      = st.text_input('Phone', max_chars=11)
        name       = st.text_input('Full Name')
        gender     = st.selectbox('Gender', ['Male', 'Female'])
        age_range  = st.selectbox('Age Range', ['10-20','21-30','31-40','41-50','51-60','61-70','70+'])
        membership = st.selectbox('CBA Membership', ['Existing', 'New'])
        location   = st.text_input('Location (Community/LGA)')
        consent    = st.checkbox('Consent to follow-up')
        services   = st.multiselect('Services', ['Prayer', 'Medical', 'Welfare'])
        submit_btn = st.form_submit_button('Submit')

    if submit_btn:
        session = get_session()
        count   = session.query(Registration).count()
        tag     = f"HAMoS-{count+1:04d}"
        now     = datetime.utcnow()

        reg = Registration(
            tag_id=tag,
            phone=phone,
            name=name,
            gender=gender,
            age_range=age_range,
            membership=membership,
            location=location,
            consent=consent,
            services=','.join(services),
            ts=now,
            source=PAGE_SOURCE
        )
        session.add(reg)
        session.commit()

        st.session_state.submitted = True
        st.success(f"Thank you! Your Tag ID is {tag}")
else:
    st.button('Register Another', on_click=lambda: st.session_state.update(submitted=False))
