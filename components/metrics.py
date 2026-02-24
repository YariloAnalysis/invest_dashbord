
import streamlit as st
import pandas as pd
from constants import MEDALS


def render_top(df: pd.DataFrame, diff_col: str):
    """
    Топ 5 лучших и худших активов
    df       — из load_top_alltime() или load_top_daily()
    diff_col — 'end_yield_pct' или 'diff_pct'
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        st.warning("⚠️ Нет данных")
        return

    best  = df[df['rank_best']  <= 5].sort_values(diff_col, ascending=False)
    worst = df[df['rank_worst'] <= 5].sort_values(diff_col, ascending=True)

    def render_rows(rows, color):
        for i, (_, row) in enumerate(rows.iterrows(), start=1):
            medal = MEDALS.get(i, f"{i}.")
            sign  = "+" if row[diff_col] >= 0 else ""
            bg    = (
                "rgba(45,198,83,0.07)"
                if color == "#2DC653"
                else "rgba(230,57,70,0.07)"
            )
            st.markdown(
                f'<div style="'
                f'display:flex;'
                f'justify-content:space-between;'
                f'padding:4px 8px;'
                f'border-radius:6px;'
                f'margin-bottom:4px;'
                f'background:{bg}'
                f'">'
                f'<span>{medal} {row["name"]}</span>'
                f'<span style="color:{color}">'
                f'<b>{sign}{row[diff_col]:.2f}%</b>'
                f'</span>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("🟢 **Лучшие**")
    render_rows(best,  color="#2DC653")

    st.markdown("---")

    st.markdown("🔴 **Худшие**")
    render_rows(worst, color="#E63946")


def render_coupon_metrics(coupon: float, suma: float, invested_today: float):
    """
    Два metric-блока купонной доходности
    coupon         — сумма купонов за год
    suma           — вложено в облигации
    invested_today — весь вложенный капитал
    """
    col_a, col_b = st.columns(2)

    with col_a:
        st.metric(
            label="Доходность на весь капитал (план, год)",
            value=f"{coupon / invested_today * 100:.2f}%",
            help="Годовые купоны / весь вложенный капитал",
        )
    with col_b:
        st.metric(
            label="Доходность на капитал в облигациях (план, год)",
            value=f"{coupon / suma * 100:.2f}%",
            help="Годовые купоны / вложено в облигации",
        )