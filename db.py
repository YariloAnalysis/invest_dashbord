import streamlit as st
import psycopg2
import pandas as pd
import os
@st.cache_resource
def init_connection():
    if hasattr(st, 'secrets') and 'database' in st.secrets:
        return psycopg2.connect(
            host=st.secrets["database"]["host"],
            port=st.secrets["database"]["port"],
            database=st.secrets["database"]["database"],
            user=st.secrets["database"]["user"],
            password=st.secrets["database"]["password"]
        )
        # Если запущено локально
    else:
        from dotenv import load_dotenv
        load_dotenv()
        return psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
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

