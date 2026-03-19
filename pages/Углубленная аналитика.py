
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
import pandas as pd
import numpy as np
from data.market import load_candles, load_available_tickers, TICKER_MAP_REVERSE
from data.assets  import load_market_comparison, load_monthly_returns,load_candles_for_mc

from components.charts import (build_market_comparison, build_monthly_heatmap,
                                build_candle_chart, build_monte_carlo)

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
        label = "📈 Мой портфель",
        value = f"{float(last['Мой портфель']):.2f}%",
    )
with col2:
    st.metric(
        label = "🏛 Рынок (IMOEX)",
        value = f"{float(last['Рынок']):.2f}%",
    )
with col3:
    diff = float(last['Мой портфель']) - float(last['Рынок'])
    sign = "+" if diff >= 0 else ""
    color = "green" if diff >= 0 else "red"
    status = "обгоняю рынок 🚀" if diff >= 0 else "отстаю от рынка 📉"

    st.metric(
        label="⚡ Я vs Рынок",
        value=f"{sign}{diff:.2f}%",
    )

    st.markdown(
        f"<span style='color:{color}; font-weight:600'>{status}</span>",
        unsafe_allow_html=True
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
        label       = "🥇 Лучший месяц",
        value       = f"+{float(best_month['monthly_return']):.2f}%",
        delta       = best_label,
        delta_color = "off",
    )
with col2:
    st.metric(
        label       = worst_icon,
        value       = f"{worst_sign}{worst_val:.2f}%",
        delta       = worst_label,
        delta_color = "off",
    )
with col3:
    sign = "+" if avg_return >= 0 else ""
    st.metric(
        label = "📊 Среднемесячная",
        value = f"{sign}{float(avg_return):.2f}%",
    )

st.plotly_chart(build_monthly_heatmap(df_monthly), use_container_width=True)
st.markdown("---")

# ════════════════════════════════════════════════════════════
# БЛОК 3 — Технический анализ
# ════════════════════════════════════════════════════════════
st.markdown("### 📈 Технический анализ")

# ── Выбор тикера ─────────────────────────────────────────────
tickers = load_available_tickers()

# Инициализация — только один раз
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
        label   = '🔍 Выберите акцию',
        options = tickers,
        index   = tickers.index(st.session_state.active_ticker),
    )

# Единый источник истины
active_ticker = st.session_state.active_ticker
figi          = TICKER_MAP_REVERSE[active_ticker]

# ── Выбор периода ─────────────────────────────────────────────
period = st.radio(
    label      = 'Период',
    options    = ['1D', '1W', '1M', '6M', '1Y', 'ALL'],
    index      = 0,
    horizontal = True,
)

PERIOD_LABEL = {
    '1D' : 'за день',
    '1W' : 'за неделю',
    '1M' : 'за месяц',
    '6M' : 'за 6 месяцев',
    '1Y' : 'за год',
    'ALL': 'за всё время',
}

# ── Загрузка ──────────────────────────────────────────────────
df_full, df_display = load_candles(figi, period)

# ── Метрики по df_display ─────────────────────────────────────
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
    st.metric(
        label = f"📈 Изменение {PERIOD_LABEL[period]}",
        value = f"{sign}{change_pct:.2f}%",
    )
with col3:
    st.metric(f"🔺 Макс {PERIOD_LABEL[period]}", f"{high_period:,.0f} ₽")
with col4:
    st.metric(f"🔻 Мин {PERIOD_LABEL[period]}", f"{low_period:,.0f} ₽")

# ── График ────────────────────────────────────────────────────
st.plotly_chart(
    build_candle_chart(df_full, df_display, active_ticker, period),
    use_container_width=True,
)
st.markdown("---")

# ════════════════════════════════════════════════════════════
# БЛОК 4 — Монте-Карло
# ════════════════════════════════════════════════════════════
st.markdown("### 🎲 Моделирование Монте-Карло")

col_conf, col_sim, _ = st.columns([2, 2, 4])
with col_conf:
    confidence = st.slider(
        'Уровень доверия',
        min_value = 0.90,
        max_value = 0.99,
        value     = 0.95,
        step      = 0.01,
        format    = '%.2f',
    )
with col_sim:
    n_sim = st.select_slider(
        'Симуляций',
        options = [1000, 5000, 10000, 50000],
        value   = 10000,
    )

fig_mc, var_val, last_price = build_monte_carlo(
    figi,
    active_ticker,
    n_sim,
    confidence,
)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("💰 Текущая цена", f"{last_price:,.2f} ₽")
with col2:
    st.metric(
        label       = f"⚠️ VaR {int(confidence*100)}%",
        value       = f"{var_val:,.2f} ₽",
        delta       = f"{var_val / last_price * 100:.2f}% от цены",
        delta_color = "inverse",
    )
with col3:
    risk_pct   = var_val / last_price
    risk_label = (
        "🟢 Низкий риск"  if risk_pct < 0.02 else
        "🟡 Средний риск" if risk_pct < 0.04 else
        "🔴 Высокий риск"
    )
    st.metric("🎯 Оценка риска", risk_label)

st.plotly_chart(fig_mc, use_container_width=True)

st.info(
    f"📊 **Интерпретация:** С вероятностью **{int(confidence*100)}%** "
    f"однодневный убыток по **{active_ticker}** не превысит "
    f"**{var_val:,.2f} ₽** ({var_val / last_price * 100:.2f}% от текущей цены). "
    f"Смоделировано **{n_sim:,}** сценариев."
)
