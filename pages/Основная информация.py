# pages/1_Портфель.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd

from constants           import COLORS_TOP, COLORS_DETAIL, REVERSE_MAP
from data.portfolio      import load_portfolio_metrics, load_portfolio_today, load_bar_money, load_coupon_metrics
from data.assets         import load_donut_top, load_donut_detail, load_top_alltime, load_top_daily
from components.charts   import build_donut, build_portfolio_chart, build_bar_assets
from components.metrics  import render_top, render_coupon_metrics

# ── Session state ────────────────────────────────────────────
if 'selected_sector' not in st.session_state:
    st.session_state.selected_sector = None
if 'show_chart' not in st.session_state:
    st.session_state.show_chart = False
if 'show_assets_details' not in st.session_state:
    st.session_state.show_assets_details = False
if 'show_yield_details' not in st.session_state:
    st.session_state.show_yield_details = False

# ── Toggles ──────────────────────────────────────────────────
def toggle_chart():
    st.session_state.show_chart = not st.session_state.show_chart

def toggle_assets_details():
    st.session_state.show_assets_details = not st.session_state.show_assets_details

def toggle_yield_details():
    st.session_state.show_yield_details = not st.session_state.show_yield_details

# ── Загрузка данных ──────────────────────────────────────────
metrics          = load_portfolio_today()
df, all_dates, forecast = load_portfolio_metrics()
coupons          = load_coupon_metrics()
df_bar           = load_bar_money()
df_donut_top     = load_donut_top()
df_donut_detail  = load_donut_detail()
df_alltime       = load_top_alltime()
df_daily         = load_top_daily()

# ── Шорткаты ─────────────────────────────────────────────────
value_today    = metrics['value_today']
invested_today = metrics['invested_today']
proffit        = metrics['proffit']
return_today   = metrics['return_today']
delta_return   = metrics['delta_return']
suma           = coupons['suma']
coupon         = coupons['coupon']

# ════════════════════════════════════════════════════════════
# СТРАНИЦА
# ════════════════════════════════════════════════════════════
st.markdown("## 📊 Основная информация")
st.markdown("---")

# ── Три метрики ──────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="💼 Стоимость портфеля",
        value=f"{value_today:,.0f} ₽"
    )
    st.button(
        "🔼 Скрыть" if st.session_state.show_chart else "📉 Посмотреть в динамике",
        key="toggle_chart_btn",
        on_click=toggle_chart,
        type="primary",
        use_container_width=True
    )

with col2:
    st.metric(
        label="📈 Доходность",
        value=f"{return_today:.2f}%",
        delta=f"{delta_return:+.2f}% к вчера",
        delta_color="normal"
    )
    st.button(
        "🔼 Скрыть" if st.session_state.show_yield_details else "Подробнее",
        key="yield_button",
        type="primary",
        use_container_width=True,
        on_click=toggle_yield_details
    )

with col3:
    st.metric(
        label="💰 Вложено",
        value=f"{invested_today:,.0f} ₽",
        delta=f"{proffit:+.2f}₽",
        delta_color="normal"
    )
    st.button(
        "🔼 Скрыть" if st.session_state.show_assets_details else "Подробнее по активам",
        key="assets_button",
        on_click=toggle_assets_details,
        type="primary",
        use_container_width=True,
    )

st.markdown("---")

# ── График портфеля ──────────────────────────────────────────
if st.session_state.show_chart:
    fig_portfolio = build_portfolio_chart(df, all_dates, forecast)
    st.plotly_chart(fig_portfolio, use_container_width=True)

# ── Детали доходности ────────────────────────────────────────
if st.session_state.show_yield_details:
    st.markdown("### 📈 Детали доходности")
    render_coupon_metrics(
        coupon         = coupon,
        suma           = suma,
        invested_today = invested_today
    )

# ── Детали по активам ────────────────────────────────────────
if st.session_state.show_assets_details:
    st.markdown("### 💼 Распределение по активам")
    fig_bar = build_bar_assets(df_bar)
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Бублик + Топ активов ─────────────────────────────────────
st.markdown("### 🥯 Доля активов")

col_donut, col_right = st.columns([1, 1])

with col_donut:
    selected = st.session_state.selected_sector

    if selected is None:
        # Верхний уровень
        total      = df_donut_top['По факту'].sum()
        color_list = [COLORS_TOP.get(n, '#CED4DA') for n in df_donut_top['Активы']]

        fig_donut = build_donut(
            df          = df_donut_top,
            label_col   = 'Активы',
            value_col   = 'По факту',
            colors      = color_list,
            center_text = f'<b>{total:,.0f} ₽</b><br>в портфеле',
        )
        st.plotly_chart(fig_donut, use_container_width=True)

        st.markdown("**Что вас интересует, милорд?**")
        btn_cols = st.columns(len(df_donut_top))

        for i, (_, row) in enumerate(df_donut_top.iterrows()):
            with btn_cols[i]:
                st.button(
                    row['Активы'],
                    key=f"sector_btn_{row['Активы']}",
                    use_container_width=True,
                    on_click=lambda name=row['Активы']: (
                        st.session_state.update(selected_sector=name)
                    ),
                )
    else:
        # Детализация внутри категории
        instrument_type = REVERSE_MAP.get(selected)
        df_inner = df_donut_detail[
            df_donut_detail['instrument_type'] == instrument_type
        ].copy()
        df_inner['amount'] = pd.to_numeric(df_inner['amount'], errors='coerce')

        inner_total  = df_inner['amount'].sum()
        colors_inner = COLORS_DETAIL.get(selected, ['#CED4DA'] * len(df_inner))

        fig_inner = build_donut(
            df          = df_inner,
            label_col   = 'name',
            value_col   = 'amount',
            colors      = colors_inner[:len(df_inner)],
            center_text = f'<b>{selected}</b><br>{inner_total:,.0f} ₽',
        )
        st.plotly_chart(fig_inner, use_container_width=True)

        st.button(
            "← Назад к общему",
            key="back_btn",
            type="primary",
            on_click=lambda: st.session_state.update(selected_sector=None),
        )

with col_right:
    st.markdown("#### 🏆 Топ активов")

    tab_all, tab_day = st.tabs(["📅 За всё время", "⚡ За день"])

    with tab_all:
        render_top(df_alltime, diff_col='end_yield_pct')

    with tab_day:
        render_top(df_daily, diff_col='diff_pct')