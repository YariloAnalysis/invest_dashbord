# data/assets.py
import pandas as pd
import streamlit as st
from db import api_get


@st.cache_data(ttl=3600)
def load_donut_top():
    df = api_get("/api/assets/donut_top")
    return df.melt(id_vars=["nm"], var_name="Активы", value_name="По факту")


@st.cache_data(ttl=3600)
def load_donut_detail():
    return api_get("/api/assets/donut_detail")


@st.cache_data(ttl=3600)
def load_top_alltime():
    return api_get("/api/assets/top_alltime")


@st.cache_data(ttl=3600)
def load_top_daily():
    return api_get("/api/assets/top_daily")


@st.cache_data(ttl=3600)
def load_market_comparison():
    return api_get("/api/assets/market_comparison")


@st.cache_data(ttl=3600)
def load_monthly_returns():
    return api_get("/api/assets/monthly_returns")


@st.cache_data(ttl=3600)
def load_candles_for_mc(figi: str) -> pd.DataFrame:
    """Дневные close для Монте-Карло"""
    df = api_get(f"/api/market/candles_close/{figi}")
    df['time']  = pd.to_datetime(df['time'])
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df = df.set_index('time')

    # Ресемплим до дневных (на случай если интрадей)
    df_daily = df['close'].resample('1D').last().dropna().to_frame()
    return df_daily
