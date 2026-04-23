# pages/5_📈_Оптимизация_портфеля.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# ← ВАШ модуль из корня проекта
from db import api_get_json, api_post_json

# ============================================================
#                      КОНФИГУРАЦИЯ СТРАНИЦЫ
# ============================================================
st.set_page_config(
    page_title="Оптимизация портфеля",
    page_icon="📈",
    layout="wide",
)

# Проверка авторизации (у вас ключ — jwt_token + authenticated)
if not st.session_state.get("authenticated") or not st.session_state.get("jwt_token"):
    st.warning("🔐 Пожалуйста, войдите в систему на главной странице.")
    st.stop()

st.title("📈 Оптимизация портфеля — Markowitz")
st.caption("Современная портфельная теория: найдите оптимальное соотношение риск/доходность")

# ============================================================
#                     САЙДБАР — ПАРАМЕТРЫ
# ============================================================
with st.sidebar:
    st.header("⚙️ Параметры")

    lookback_days = st.select_slider(
        "Горизонт истории",
        options=[90, 180, 365, 730, 1095, 1825],
        value=365,
        format_func=lambda x: f"{x} дн. ({x // 365}г.)" if x >= 365 else f"{x} дн.",
        help="За какой период анализировать цены",
    )

    rf_rate = st.number_input(
        "Безрисковая ставка (год)",
        min_value=0.0, max_value=0.30, value=0.16, step=0.005,
        format="%.3f",
        help="Ставка ОФЗ / ключевая ставка ЦБ. Для расчёта Sharpe",
    )

    st.divider()
    st.subheader("Ограничения на веса")

    col_a, col_b = st.columns(2)
    min_weight = col_a.number_input(
        "Мин. вес", 0.0, 0.5, 0.0, 0.01, format="%.2f",
    )
    max_weight = col_b.number_input(
        "Макс. вес", 0.05, 1.0, 0.40, 0.05, format="%.2f",
        help="Защита от концентрации в одной бумаге",
    )

    constraints = {"min_weight": min_weight, "max_weight": max_weight}

# ============================================================
#                       СВОДКА ПОРТФЕЛЯ
# ============================================================
summary = api_get_json("/api/optimization/portfolio_summary")

if not summary or summary.get("n_assets", 0) < 2:
    st.error("❌ В вашем портфеле меньше 2 бумаг (акции/облигации/ETF) — оптимизация невозможна.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Стоимость портфеля", f"{summary['total_value']:,.0f} ₽".replace(",", " "))
col2.metric("📊 Активов", summary["n_assets"])

by_type = summary.get("by_type", {})
shares_val = by_type.get("share", 0)
bonds_val = by_type.get("bond", 0)
col3.metric("📈 Акции", f"{shares_val:,.0f} ₽".replace(",", " "))
col4.metric("📜 Облигации", f"{bonds_val:,.0f} ₽".replace(",", " "))

st.divider()

# ============================================================
#                          ВКЛАДКИ
# ============================================================
tab_frontier, tab_optimize, tab_backtest, tab_corr, tab_positions = st.tabs([
    "🎯 Эффективная граница",
    "⚡ Оптимизация стратегии",
    "🔬 Бэктест",
    "🔗 Корреляции",
    "📋 Состав портфеля",
])

# ============================================================
#               ВКЛАДКА 1: ЭФФЕКТИВНАЯ ГРАНИЦА
# ============================================================
with tab_frontier:
    st.subheader("Эффективная граница Марковица")
    st.caption(
        "Каждая точка — возможный портфель. Линия сверху — оптимальные. "
        "Звёзды — ключевые точки (max Sharpe, min variance, ваш текущий)."
    )

    col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
    n_points = col_f1.slider("Точек на границе", 20, 80, 40, 5)
    n_random = col_f2.slider("Случайных портфелей (фон)", 0, 5000, 2000, 500)
    go_btn = col_f3.button("🚀 Построить", type="primary",
                            use_container_width=True, key="frontier_btn")

    if go_btn or "frontier_data" in st.session_state:
        if go_btn:
            with st.spinner("Строим эффективную границу..."):
                data = api_post_json("/api/optimization/efficient_frontier", {
                    "lookback_days": lookback_days,
                    "n_points": n_points,
                    "n_random": n_random,
                    "rf_rate": rf_rate,
                    "constraints": constraints,
                })
                st.session_state["frontier_data"] = data
        else:
            data = st.session_state["frontier_data"]

        if not data or "error" in data:
            st.error(data.get("error", "Не удалось получить данные"))
        else:
            # ========== ГРАФИК ==========
            fig = go.Figure()

            if data.get("random_portfolios"):
                rp = pd.DataFrame(data["random_portfolios"])
                fig.add_trace(go.Scatter(
                    x=rp["volatility"] * 100,
                    y=rp["return"] * 100,
                    mode="markers",
                    marker=dict(
                        size=4,
                        color=rp["sharpe"],
                        colorscale="Viridis",
                        opacity=0.5,
                        colorbar=dict(title="Sharpe", x=1.15),
                        showscale=True,
                    ),
                    name="Случайные портфели",
                    hovertemplate="σ: %{x:.2f}%<br>μ: %{y:.2f}%<extra></extra>",
                ))

            if data.get("frontier"):
                fr = pd.DataFrame(data["frontier"])
                fig.add_trace(go.Scatter(
                    x=fr["volatility"] * 100,
                    y=fr["return"] * 100,
                    mode="lines+markers",
                    line=dict(color="#FF4B4B", width=3),
                    marker=dict(size=6, color="#FF4B4B"),
                    name="Эффективная граница",
                    customdata=fr["sharpe"],
                    hovertemplate="σ: %{x:.2f}%<br>μ: %{y:.2f}%<br>Sharpe: %{customdata:.2f}<extra></extra>",
                ))

            def _add_point(portfolio, name, color, symbol):
                if not portfolio or "expected_return" not in portfolio:
                    return
                fig.add_trace(go.Scatter(
                    x=[portfolio["volatility"] * 100],
                    y=[portfolio["expected_return"] * 100],
                    mode="markers",
                    marker=dict(size=22, color=color, symbol=symbol,
                                line=dict(color="white", width=2)),
                    name=name,
                    hovertemplate=f"<b>{name}</b><br>σ: %{{x:.2f}}%<br>μ: %{{y:.2f}}%<br>"
                                  f"Sharpe: {portfolio.get('sharpe', 0):.2f}<extra></extra>",
                ))

            _add_point(data.get("max_sharpe"), "⭐ Max Sharpe", "#FFD700", "star")
            _add_point(data.get("min_variance"), "🛡️ Min Variance", "#00CED1", "diamond")
            _add_point(data.get("current"), "📍 Ваш портфель", "#FF69B4", "circle")

            fig.update_layout(
                xaxis_title="Риск (волатильность), % годовых",
                yaxis_title="Ожидаемая доходность, % годовых",
                height=600,
                hovermode="closest",
                template="plotly_white",
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01,
                            bgcolor="rgba(255,255,255,0.8)"),
            )
            st.plotly_chart(fig, use_container_width=True)

            # ========== СРАВНЕНИЕ ==========
            st.subheader("📊 Сравнение портфелей")

            comparison = []
            for label, key in [
                ("📍 Ваш текущий", "current"),
                ("⭐ Max Sharpe", "max_sharpe"),
                ("🛡️ Min Variance", "min_variance"),
            ]:
                p = data.get(key, {})
                if p and "expected_return" in p:
                    comparison.append({
                        "Портфель": label,
                        "Доходность": f"{p['expected_return'] * 100:.2f}%",
                        "Волатильность": f"{p['volatility'] * 100:.2f}%",
                        "Sharpe": f"{p['sharpe']:.3f}",
                    })
            st.dataframe(pd.DataFrame(comparison), hide_index=True,
                         use_container_width=True)

            # ========== СОСТАВ MAX SHARPE ==========
            ms = data.get("max_sharpe", {})
            if ms.get("weights_detail"):
                st.subheader("🎯 Состав портфеля Max Sharpe")
                wd = pd.DataFrame(ms["weights_detail"])
                wd["weight_pct"] = wd["weight"] * 100

                col_pie, col_tbl = st.columns([1, 1])
                with col_pie:
                    fig_pie = px.pie(
                        wd, values="weight_pct", names="ticker",
                        hole=0.4, title="Распределение весов",
                    )
                    fig_pie.update_traces(textposition="inside",
                                          textinfo="percent+label")
                    st.plotly_chart(fig_pie, use_container_width=True)

                with col_tbl:
                    display_df = wd[["ticker", "name", "weight_pct"]].copy()
                    display_df.columns = ["Тикер", "Название", "Вес, %"]
                    display_df["Вес, %"] = display_df["Вес, %"].round(2)
                    st.dataframe(display_df, hide_index=True,
                                 use_container_width=True, height=400)
    else:
        st.info("👆 Нажмите «Построить», чтобы увидеть эффективную границу")

# ============================================================
#              ВКЛАДКА 2: ОПТИМИЗАЦИЯ СТРАТЕГИИ
# ============================================================
with tab_optimize:
    st.subheader("Оптимизация под стратегию")
    st.caption("Система рассчитает целевые веса и план ребалансировки")

    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        strategy = st.selectbox(
            "Стратегия",
            options=[
                "max_sharpe", "min_variance", "risk_parity",
                "target_return", "target_volatility",
            ],
            format_func=lambda x: {
                "max_sharpe": "⭐ Max Sharpe — максимум доходность/риск",
                "min_variance": "🛡️ Min Variance — минимум волатильности",
                "risk_parity": "⚖️ Risk Parity — равный риск на актив",
                "target_return": "🎯 Target Return — целевая доходность",
                "target_volatility": "📉 Target Volatility — целевой риск",
            }[x],
        )

    target_value = None
    with col_s2:
        if strategy == "target_return":
            target_value = st.number_input(
                "Целевая доходность (год)",
                0.0, 1.0, 0.25, 0.01, format="%.2f",
            )
        elif strategy == "target_volatility":
            target_value = st.number_input(
                "Целевая волатильность (год)",
                0.01, 1.0, 0.15, 0.01, format="%.2f",
            )

    if st.button("⚡ Оптимизировать", type="primary", key="optimize_btn"):
        with st.spinner("Оптимизируем..."):
            payload = {
                "strategy": strategy,
                "lookback_days": lookback_days,
                "rf_rate": rf_rate,
                "constraints": constraints,
            }
            if target_value is not None:
                payload["target_value"] = target_value

            result = api_post_json("/api/optimization/optimize", payload)
            st.session_state["optimize_result"] = result

    if "optimize_result" in st.session_state:
        result = st.session_state["optimize_result"]
        if not result or "error" in result:
            st.error(result.get("error", "Ошибка оптимизации"))
        else:
            optimal = result["optimal"]
            current = result["current"]
            improvement = result["improvement"]

            st.markdown("### 📊 Текущий vs Оптимальный")
            m1, m2, m3 = st.columns(3)
            m1.metric(
                "Ожидаемая доходность",
                f"{optimal['expected_return'] * 100:.2f}%",
                f"{improvement['return_delta'] * 100:+.2f} п.п.",
            )
            m2.metric(
                "Волатильность",
                f"{optimal['volatility'] * 100:.2f}%",
                f"{improvement['volatility_delta'] * 100:+.2f} п.п.",
                delta_color="inverse",
            )
            m3.metric(
                "Sharpe Ratio",
                f"{optimal['sharpe']:.3f}",
                f"{improvement['sharpe_delta']:+.3f}",
            )

            # ========== ВЕСА ==========
            st.markdown("### 🎯 Распределение весов")
            cur_wd = pd.DataFrame(current["weights_detail"])
            opt_wd = pd.DataFrame(optimal["weights_detail"])

            all_tickers = set(cur_wd["ticker"]) | set(opt_wd["ticker"])
            merged = []
            for t in all_tickers:
                cur_row = cur_wd[cur_wd["ticker"] == t]
                opt_row = opt_wd[opt_wd["ticker"] == t]
                merged.append({
                    "ticker": t,
                    "current": float(cur_row["weight"].iloc[0]) if len(cur_row) else 0.0,
                    "target": float(opt_row["weight"].iloc[0]) if len(opt_row) else 0.0,
                })
            merged_df = pd.DataFrame(merged).sort_values("target", ascending=True)

            fig_bars = go.Figure()
            fig_bars.add_trace(go.Bar(
                y=merged_df["ticker"], x=merged_df["current"] * 100,
                name="Текущий", orientation="h", marker_color="#888",
            ))
            fig_bars.add_trace(go.Bar(
                y=merged_df["ticker"], x=merged_df["target"] * 100,
                name="Целевой", orientation="h", marker_color="#FF4B4B",
            ))
            fig_bars.update_layout(
                barmode="group",
                height=max(400, 35 * len(merged_df)),
                xaxis_title="Вес, %",
                template="plotly_white",
                legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
            )
            st.plotly_chart(fig_bars, use_container_width=True)

            # ========== РЕБАЛАНСИРОВКА ==========
            st.markdown("### 💼 План ребалансировки")
            rebalancing = result.get("rebalancing", [])
            if rebalancing:
                rb_df = pd.DataFrame(rebalancing)
                rb_actions = rb_df[rb_df["action"] != "HOLD"].copy()

                if len(rb_actions):
                    buy_total = rb_actions[rb_actions["action"] == "BUY"]["amount_rub"].sum()
                    sell_total = -rb_actions[rb_actions["action"] == "SELL"]["amount_rub"].sum()

                    rb1, rb2, rb3 = st.columns(3)
                    rb1.metric("🟢 Купить на", f"{buy_total:,.0f} ₽".replace(",", " "))
                    rb2.metric("🔴 Продать на", f"{sell_total:,.0f} ₽".replace(",", " "))
                    rb3.metric("Всего операций", len(rb_actions))

                    rb_display = rb_actions[[
                        "action", "ticker", "name",
                        "current_weight", "target_weight", "delta", "amount_rub",
                    ]].copy()
                    rb_display.columns = [
                        "Действие", "Тикер", "Название",
                        "Тек. вес", "Цель", "Δ", "Сумма, ₽",
                    ]
                    rb_display["Тек. вес"] = (rb_display["Тек. вес"] * 100).round(2).astype(str) + "%"
                    rb_display["Цель"] = (rb_display["Цель"] * 100).round(2).astype(str) + "%"
                    rb_display["Δ"] = (rb_display["Δ"] * 100).round(2).astype(str) + " п.п."
                    rb_display["Сумма, ₽"] = rb_display["Сумма, ₽"].round(0).astype(int)

                    def _color_action(val):
                        if val == "BUY":
                            return "background-color: #d4edda; color: #155724; font-weight: bold"
                        if val == "SELL":
                            return "background-color: #f8d7da; color: #721c24; font-weight: bold"
                        return ""

                    st.dataframe(
                        rb_display.style.map(_color_action, subset=["Действие"]),
                        hide_index=True, use_container_width=True,
                    )
                else:
                    st.success("✅ Портфель уже близок к оптимальному")

# ============================================================
#                    ВКЛАДКА 3: БЭКТЕСТ
# ============================================================
with tab_backtest:
    st.subheader("Walk-forward бэктест")
    st.caption(
        "Симулируем стратегию на исторических данных. "
        "Обучаемся на N днях, держим M дней, переобучаемся — и так до конца."
    )

    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
    bt_strategy = col_b1.selectbox(
        "Стратегия",
        ["max_sharpe", "min_variance", "risk_parity"],
        format_func=lambda x: {
            "max_sharpe": "Max Sharpe",
            "min_variance": "Min Variance",
            "risk_parity": "Risk Parity",
        }[x],
    )
    bt_lookback = col_b2.select_slider(
        "Период теста",
        options=[730, 1095, 1825, 2555, 3650],
        value=1095,
        format_func=lambda x: f"{x // 365} г.",
    )
    bt_train = col_b3.select_slider(
        "Окно обучения",
        options=[126, 252, 378, 504, 756],
        value=252,
        format_func=lambda x: f"{x // 21} мес." if x < 252 else f"{x // 252} г.",
    )
    bt_rebal = col_b4.select_slider(
        "Ребалансировка",
        options=[5, 21, 63, 126, 252],
        value=21,
        format_func=lambda x: {
            5: "Неделя",
            21: "Месяц",
            63: "Квартал",
            126: "Полгода",
            252: "Год",
        }[x],
    )

    if st.button("🚀 Запустить бэктест", type="primary", key="backtest_btn"):
        with st.spinner("Запускаем бэктест... (10-30 сек.)"):
            result = api_post_json("/api/optimization/backtest", {
                "strategy": bt_strategy,
                "lookback_days": bt_lookback,
                "train_window": bt_train,
                "rebalance_every": bt_rebal,
                "rf_rate": rf_rate,
                "constraints": constraints,
            })
            st.session_state["backtest_result"] = result

    if "backtest_result" in st.session_state:
        result = st.session_state["backtest_result"]

        if not result or "error" in result:
            st.error(result.get("error", "Ошибка бэктеста"))
        elif not result.get("equity_curve"):
            st.warning("Бэктест не вернул данных — проверьте параметры")
        else:
            # ========== КРИВАЯ КАПИТАЛА ==========
            eq_df = pd.DataFrame(result["equity_curve"])
            eq_df["date"] = pd.to_datetime(eq_df["date"])

            fig_eq = go.Figure()
            fig_eq.add_trace(go.Scatter(
                x=eq_df["date"], y=eq_df["optimal"],
                mode="lines", name="⭐ Оптимальная стратегия",
                line=dict(color="#FF4B4B", width=2.5),
                hovertemplate="%{x|%Y-%m-%d}<br>Капитал: %{y:.3f}<extra></extra>",
            ))
            fig_eq.add_trace(go.Scatter(
                x=eq_df["date"], y=eq_df["current"],
                mode="lines", name="📍 Ваш портфель (buy & hold)",
                line=dict(color="#888", width=2, dash="dash"),
                hovertemplate="%{x|%Y-%m-%d}<br>Капитал: %{y:.3f}<extra></extra>",
            ))
            if "imoex" in eq_df.columns and eq_df["imoex"].notna().any():
                fig_eq.add_trace(go.Scatter(
                    x=eq_df["date"], y=eq_df["imoex"],
                    mode="lines", name="📈 IMOEX",
                    line=dict(color="#00AA44", width=2, dash="dot"),
                    hovertemplate="%{x|%Y-%m-%d}<br>IMOEX: %{y:.3f}<extra></extra>",
                ))

            fig_eq.update_layout(
                title="Рост капитала (начальный = 1.0)",
                xaxis_title="Дата",
                yaxis_title="Капитал",
                height=500,
                hovermode="x unified",
                template="plotly_white",
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01,
                            bgcolor="rgba(255,255,255,0.8)"),
            )
            st.plotly_chart(fig_eq, use_container_width=True)

            # ========== МЕТРИКИ ==========
            st.markdown("### 📊 Итоговые метрики")

            metrics = result.get("metrics", {})
            rows = []
            for label, key in [
                ("⭐ Оптимальная", "optimal"),
                ("📍 Ваш (buy & hold)", "current"),
                ("📈 IMOEX", "imoex"),
            ]:
                m = metrics.get(key)
                if not m:
                    continue
                rows.append({
                    "Портфель": label,
                    "Итоговая доходность": f"{m.get('total_return', 0) * 100:+.2f}%",
                    "CAGR": f"{m.get('cagr', 0) * 100:+.2f}%",
                    "Волатильность": f"{m.get('volatility', 0) * 100:.2f}%",
                    "Sharpe": f"{m.get('sharpe', 0):.3f}",
                    "Max Drawdown": f"{m.get('max_drawdown', 0) * 100:.2f}%",
                })

            if rows:
                st.dataframe(pd.DataFrame(rows), hide_index=True,
                             use_container_width=True)

            # ========== ПРОСАДКИ ==========
            st.markdown("### 📉 Просадки")

            def _compute_drawdown(series: pd.Series) -> pd.Series:
                peaks = series.cummax()
                return (series - peaks) / peaks * 100

            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(
                x=eq_df["date"],
                y=_compute_drawdown(eq_df["optimal"]),
                mode="lines", name="⭐ Оптимальная",
                line=dict(color="#FF4B4B", width=1.5),
                fill="tozeroy", fillcolor="rgba(255,75,75,0.15)",
            ))
            fig_dd.add_trace(go.Scatter(
                x=eq_df["date"],
                y=_compute_drawdown(eq_df["current"]),
                mode="lines", name="📍 Ваш портфель",
                line=dict(color="#888", width=1.5, dash="dash"),
            ))
            if "imoex" in eq_df.columns and eq_df["imoex"].notna().any():
                fig_dd.add_trace(go.Scatter(
                    x=eq_df["date"],
                    y=_compute_drawdown(eq_df["imoex"]),
                    mode="lines", name="📈 IMOEX",
                    line=dict(color="#00AA44", width=1.5, dash="dot"),
                ))
            fig_dd.update_layout(
                xaxis_title="Дата",
                yaxis_title="Просадка, %",
                height=350,
                hovermode="x unified",
                template="plotly_white",
            )
            st.plotly_chart(fig_dd, use_container_width=True)

            # ========== ЖУРНАЛ РЕБАЛАНСИРОВОК ==========
            rebal_log = result.get("rebalance_log", [])
            if rebal_log:
                with st.expander(f"📋 Журнал ребалансировок ({len(rebal_log)} шт.)"):
                    for i, entry in enumerate(rebal_log, 1):
                        weights_str = ", ".join(
                            f"{k}: {v * 100:.1f}%"
                            for k, v in sorted(
                                entry["weights"].items(),
                                key=lambda x: -x[1],
                            )[:5]
                        )
                        st.markdown(
                            f"**#{i} — {entry['date']}** · топ-5: {weights_str}"
                        )
    else:
        st.info("👆 Выберите параметры и нажмите «Запустить бэктест»")

# ============================================================
#                  ВКЛАДКА 4: КОРРЕЛЯЦИИ
# ============================================================
with tab_corr:
    st.subheader("Матрица корреляций")
    st.caption(
        "Показывает, насколько похоже движутся бумаги. "
        "Красный (→1) — вместе растут/падают. "
        "Синий (→-1 или 0) — дают эффект диверсификации."
    )

    if st.button("🔍 Рассчитать корреляции", type="primary", key="corr_btn"):
        with st.spinner("Считаем..."):
            corr_data = api_get_json(
                "/api/optimization/correlation",
                params={"lookback_days": lookback_days},
            )
            st.session_state["corr_data"] = corr_data

    if "corr_data" in st.session_state:
        corr_data = st.session_state["corr_data"]

        if not corr_data or "error" in corr_data:
            st.error(corr_data.get("error", "Ошибка"))
        else:
            tickers = corr_data["tickers"]
            matrix = np.array(corr_data["matrix"])

            fig_corr = go.Figure(data=go.Heatmap(
                z=matrix,
                x=tickers, y=tickers,
                colorscale="RdBu_r",
                zmin=-1, zmax=1,
                text=np.round(matrix, 2),
                texttemplate="%{text}",
                textfont=dict(size=10),
                hovertemplate="%{y} ↔ %{x}<br>ρ = %{z:.3f}<extra></extra>",
                colorbar=dict(title="ρ"),
            ))
            fig_corr.update_layout(
                height=max(500, 40 * len(tickers)),
                template="plotly_white",
                xaxis=dict(side="bottom", tickangle=-45),
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig_corr, use_container_width=True)

            # ========== ИНСАЙТЫ ==========
            pairs = []
            for i in range(len(tickers)):
                for j in range(i + 1, len(tickers)):
                    pairs.append({
                        "Бумага 1": tickers[i],
                        "Бумага 2": tickers[j],
                        "corr": matrix[i][j],
                    })
            pairs_df = pd.DataFrame(pairs)

            if len(pairs_df):
                col_i1, col_i2 = st.columns(2)

                with col_i1:
                    st.markdown("#### 🔴 Самые похожие пары")
                    top_corr = pairs_df.nlargest(5, "corr").copy()
                    top_corr["Корреляция"] = top_corr["corr"].round(3)
                    st.dataframe(
                        top_corr[["Бумага 1", "Бумага 2", "Корреляция"]],
                        hide_index=True, use_container_width=True,
                    )

                with col_i2:
                    st.markdown("#### 🟢 Лучшая диверсификация")
                    low_corr = pairs_df.nsmallest(5, "corr").copy()
                    low_corr["Корреляция"] = low_corr["corr"].round(3)
                    st.dataframe(
                        low_corr[["Бумага 1", "Бумага 2", "Корреляция"]],
                        hide_index=True, use_container_width=True,
                    )
    else:
        st.info("👆 Нажмите «Рассчитать корреляции»")

# ============================================================
#                  ВКЛАДКА 5: СОСТАВ ПОРТФЕЛЯ
# ============================================================
with tab_positions:
    st.subheader("Текущий состав портфеля")

    positions = summary.get("positions", [])
    if not positions:
        st.info("Портфель пуст")
    else:
        pos_df = pd.DataFrame(positions)

        col_chart, col_stats = st.columns([2, 1])

        with col_chart:
            fig_tree = px.treemap(
                pos_df,
                path=["instrument_type", "ticker"],
                values="value",
                color="weight",
                color_continuous_scale="Viridis",
                title="Распределение капитала",
                hover_data={"name": True, "value": ":,.0f", "weight": ":.3f"},
            )
            fig_tree.update_layout(height=500)
            st.plotly_chart(fig_tree, use_container_width=True)

        with col_stats:
            st.markdown("#### Структура по типам")
            type_names = {
                "share": "📈 Акции",
                "bond": "📜 Облигации",
                "etf": "📊 ETF/БПИФ",
            }
            total = summary["total_value"]
            for t, val in sorted(by_type.items(), key=lambda x: -x[1]):
                pct = val / total * 100 if total else 0
                st.metric(
                    type_names.get(t, t),
                    f"{val:,.0f} ₽".replace(",", " "),
                    f"{pct:.1f}% портфеля",
                )

        st.markdown("#### Полный список позиций")
        display_pos = pos_df.copy()
        display_pos["weight_pct"] = (display_pos["weight"] * 100).round(2)
        display_pos["value"] = display_pos["value"].round(0).astype(int)

        display_pos = display_pos[[
            "ticker", "name", "instrument_type", "value", "weight_pct",
        ]]
        display_pos.columns = ["Тикер", "Название", "Тип", "Стоимость, ₽", "Вес, %"]
        display_pos["Тип"] = display_pos["Тип"].map({
            "share": "Акция",
            "bond": "Облигация",
            "etf": "ETF",
        }).fillna(display_pos["Тип"])

        st.dataframe(display_pos, hide_index=True, use_container_width=True)

# ============================================================
#                         ПОДВАЛ
# ============================================================
st.divider()
with st.expander("ℹ️ Как это работает"):
    st.markdown("""
    **Теория Марковица (1952, Нобелевская премия 1990)** — фундамент современного инвестирования.

    - **Эффективная граница** — множество портфелей с максимальной доходностью при каждом уровне риска.
    - **Max Sharpe** — лучшее соотношение «доходность / риск» (касательный портфель).
    - **Min Variance** — минимум волатильности.
    - **Risk Parity** — равный вклад каждого актива в общий риск портфеля.

    **Ограничения** защищают от концентрации: `max_weight = 0.3` → ни одна бумага не займёт больше 30%.

    **Walk-forward бэктест** честно симулирует прошлое:
    1. Обучаемся на первых N днях
    2. Держим портфель M дней
    3. Переобучаемся на новых данных — и так до конца

    Это защищает от *lookahead bias* (заглядывания в будущее).

    ⚠️ **Важно:** исторические результаты не гарантируют будущую доходность.
    """)
