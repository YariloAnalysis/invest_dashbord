import streamlit as st
import pandas as pd
import requests
import os
from dotenv import load_dotenv

def get_api_url():
    try:
        return st.secrets["API_URL"]
    except Exception:
        load_dotenv()
        return os.getenv("API_URL", "http://localhost:8000")

def get_api_key():
    try:
        return st.secrets["API_KEY"]
    except Exception:
        load_dotenv()
        return os.getenv("API_KEY", "")

@st.cache_data(ttl=600)
def select(query, params=None):
    try:
        api_url = get_api_url()
        api_key = get_api_key()
        response = requests.get(
            f"{api_url}/query",
            params={"sql": query},
            headers={"X-API-Key": api_key},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()["data"]
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"API error: {e}")
        raise

