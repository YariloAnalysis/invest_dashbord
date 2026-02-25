import streamlit as st
import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

@st.cache_resource
def init_connection():
    try:
        return psycopg2.connect(
            host=st.secrets["DB_HOST"],
            port=st.secrets["DB_PORT"],
            dbname=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            connect_timeout=10,
            sslmode="require"# ← добавь это!
        )
    except Exception:
        load_dotenv()
        return psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            connect_timeout=10,  # ← и сюда
        )

@st.cache_data(ttl=600)
def select(query, params=None):
    conn = init_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params or ())
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        conn.commit()
        return df
    except Exception as e:
        conn.rollback()
        st.error(f"SQL error: {e}")
        raise
    finally:
        cur.close()

