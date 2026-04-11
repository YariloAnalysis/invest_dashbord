# data/portfolio.py
import pandas as pd
import numpy as np
import streamlit as st
from db import api_get
from constants import FORECAST_DAYS


@st.cache_data(ttl=3600)
def load_portfolio_metrics():
    """Основные метрики портфеля + прогноз тренда"""
    df = api_get("/api/portfolio/metrics")

    df['date']           = pd.to_datetime(df['date'])
    df['total_amount']   = pd.to_numeric(df['total_amount'],   errors='coerce')
    df['expected_yield'] = pd.to_numeric(df['expected_yield'], errors='coerce')
    df['fact_amount']    = df['total_amount'] - df['expected_yield']

    # Линейный тренд + прогноз
    x_numeric         = np.arange(len(df))
    z                 = np.polyfit(x_numeric, df['total_amount'], 1)
    p                 = np.poly1d(z)
    x_extended        = np.arange(len(df) + FORECAST_DAYS)
    forecast_extended = p(x_extended)

    last_date    = df['date'].iloc[-1]
    future_dates = pd.date_range(
        start   = last_date + pd.Timedelta(days=1),
        periods = FORECAST_DAYS,
        freq    = 'D',
    )
    all_dates = list(df['date']) + list(future_dates)

    return df, all_dates, forecast_extended


def load_portfolio_today():
    """Метрики за сегодня/вчера для карточек st.metric"""
    df, _, _ = load_portfolio_metrics()

    today     = df.iloc[-1]
    yesterday = df.iloc[-2]

    value_today       = today['total_amount']
    invested_today    = today['fact_amount']
    proffit           = today['expected_yield']
    diff_total_amount = today['total_amount'] - yesterday['total_amount']
    return_today      = (value_today / invested_today - 1) * 100
    return_yesterday  = (
        yesterday['total_amount'] / yesterday['fact_amount'] - 1
    ) * 100
    delta_return      = return_today - return_yesterday

    return {
        'value_today':       value_today,
        'invested_today':    invested_today,
        'proffit':           proffit,
        'return_today':      return_today,
        'delta_return':      delta_return,
        'diff_total_amount': diff_total_amount,
    }


@st.cache_data(ttl=3600)
def load_bar_money():
    """Распределение вложений по типам активов → для bar-chart"""
    df = api_get("/api/portfolio/bar_money")
    return df.melt(id_vars=["nm"], var_name="активы", value_name="Вложено")


@st.cache_data(ttl=3600)
def load_coupon_metrics():
    """Купонная доходность"""
    suma_per   = api_get("/api/portfolio/coupon_suma")
    coupon_per = api_get("/api/portfolio/coupon_amount")
    df_coupons = api_get("/api/portfolio/coupon_list")

    suma_val   = float(suma_per.iloc[0, 0])   if not suma_per.empty   else 0.0
    coupon_val = float(coupon_per.iloc[0, 0])  if not coupon_per.empty else 0.0

    return {
        'suma':       suma_val,
        'coupon':     coupon_val,
        'df_coupons': df_coupons,
    }
