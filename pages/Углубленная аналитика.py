import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from auth import require_auth, logout_button
require_auth()
logout_button()

import pandas as pd
import numpy as np
from data.market import load_candles, load_available_tickers, TICKER_MAP_REVERSE
from data.assets import load_market_comparison, load_monthly_returns, load_candles_for_mc
from components.charts import (
    build_market_comparison,
    build_monthly_heatmap,
    build_candle_chart,
    build_monte_carlo,
)

st.markdown("## 🔍 Углубленная аналитика")
st.markdown("---")

# ════════════════════════════════════════════════════════════
# БЛОК 1 — Сравнение с рынком
# ════════════════════════════════════════════════════════════
st.markdown("### 📊 Сравнение с рынком")

df_market = load_market_comparison()
last      = df_market.iloc[-1]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="📈 Мой портфель",
        value=f"{float(last['Мой портфель']):.2f}%",
    )
with col2:
    st.metric(
        label="🏛 Рынок (IMOEX)",
        value=f"{float(last['Рынок']):.2f}%",
    )
with col3:
    diff = float(last['Мой портфель']) - float(last['Рынок'])
    sign = "+" if diff >= 0 else ""
    st.metric(
        label="⚡ Я vs Рынок",
        value=f"{sign}{diff:.2f}%",
    )

st.plotly_chart(build_market_comparison(df_market), use_container_width=True)
st.markdown("---")

# ════════════════════════════════════════════════════════════
# БЛОК 2 — Доходность по месяцам
# ════════════════════════════════════════════════════════════
st.markdown("### 📅 Доходность по месяцам")

df_monthly = load_monthly_returns()
df_monthly['monthly_return'] = pd.to_numeric(df_monthly['monthly_return'], errors='coerce')

best_month  = df_monthly.loc[df_monthly['monthly_return'].idxmax()]
worst_month = df_monthly.loc[df_monthly['monthly_return'].idxmin()]
avg_return  = df_monthly['monthly_return'].mean()

best_label  = f"{best_month['month_name']} {best_month['year']}"
worst_label = f"{worst_month['month_name']} {worst_month['year']}"
worst_val   = float(worst_month['monthly_return'])
worst_icon  = "📉 Слабейший месяц" if worst_val >= 0 else "💀 Худший месяц"
worst_sign  = "+" if worst_val >= 0 else ""

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="🥇 Лучший месяц",
        value=f"+{float(best_month['monthly_return']):.2f}%",
        delta=best_label,
        delta_color="off",
    )
with col2:
    st.metric(
        label=worst_icon,
        value=f"{worst_sign}{worst_val:.2f}%",
        delta=worst_label,
        delta_color="off",
    )
with col3:
    sign = "+" if avg_return >= 0 else ""
    st.metric(
        label="📊 Среднемесячная",
        value=f"{sign}{float(avg_return):.2f}%",
    )

st.plotly_chart(build_monthly_heatmap(df_monthly), use_container_width=True)
st.markdown("---")

# ════════════════════════════════════════════════════════════
# БЛОК 3 — Технический анализ
# ════════════════════════════════════════════════════════════
st.markdown("### 📈 Технический анализ")

tickers = load_available_tickers()

if 'active_ticker' not in st.session_state:
    st.session_state.active_ticker = 'SBER' if 'SBER' in tickers else tickers[0]

col_search, col_prev, col_next = st.columns([6, 1, 1])

with col_prev:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button('◀', use_container_width=True):
        idx = tickers.index(st.session_state.active_ticker)
        st.session_state.active_ticker = tickers[(idx - 1) % len(tickers)]

with col_next:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button('▶', use_container_width=True):
        idx = tickers.index(st.session_state.active_ticker)
        st.session_state.active_ticker = tickers[(idx + 1) % len(tickers)]

with col_search:
    st.session_state.active_ticker = st.selectbox(
        label='🔍 Выберите акцию',
        options=tickers,
        index=tickers.index(st.session_state.active_ticker),
    )

active_ticker = st.session_state.active_ticker
figi          = TICKER_MAP_REVERSE[active_ticker]

period = st.radio(
    label='Период',
    options=['1D', '1W', '1M', '6M', '1Y', 'ALL'],
    index=0,
    horizontal=True,
)

PERIOD_LABEL = {
    '1D': 'за день',   '1W': 'за неделю', '1M': 'за месяц',
    '6M': 'за 6 месяцев', '1Y': 'за год', 'ALL': 'за всё время',
}

df_full, df_display = load_candles(figi, period)

last_close  = df_display['close'].iloc[-1]
first_close = df_display['close'].iloc[0]
change_pct  = (last_close - first_close) / first_close * 100
high_period = df_display['high'].max()
low_period  = df_display['low'].min()

st.markdown(f"#### 🏢 {active_ticker} — {PERIOD_LABEL[period]}")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("💰 Цена", f"{last_close:,.0f} ₽")
with col2:
    sign = "+" if change_pct >= 0 else ""
    st.metric(f"📈 Изменение {PERIOD_LABEL[period]}", f"{sign}{change_pct:.2f}%")
with col3:
    st.metric(f"🔺 Макс {PERIOD_LABEL[period]}", f"{high_period:,.0f}")
