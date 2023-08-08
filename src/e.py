import time
import streamlit as st

with st.form("test"):
    if st.form_submit_button("GO"):
        with st.spinner('Wait for it...'):
            time.sleep(5)
        #st.success('Done!')
        st.info("some result")
