# app.py
import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="Мой портфель",
    page_icon="📊",
)

from auth import require_auth, logout_button

require_auth()
logout_button()

st.write("Добро пожаловать! Что вас интересует?")
