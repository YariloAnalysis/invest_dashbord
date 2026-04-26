
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from constants import COLORS_TOP, COLORS_DETAIL
from data.portfolio import load_portfolio_metrics
import streamlit as st
@st.cache_data(ttl=3600)
def build_donut(df, label_col, value_col, colors, center_text):
    """Универсальный бублик — принимает DataFrame и возвращает Figure"""
    fig = go.Figure(go.Pie(
        labels=df[label_col],
        values=df[value_col],
        hole=0.6,
        marker=dict(
            colors=colors,
            line=dict(color='white', width=3)
        ),
        textinfo='label+percent',
        textfont=dict(size=13, family='Inter, sans-serif'),
        hovertemplate=(
            '<b>%{label}</b><br>'
            'Получилось по факту: %{value:,.0f} ₽<br>'
            'Доля: %{percent}<br>'
            '<extra></extra>'
        ),
        direction='clockwise',
        sort=False,
    ))

    fig.update_layout(
        annotations=[dict(
            text=center_text,
            x=0.5, y=0.5,
            font=dict(size=14, color='#2B2D42', family='Inter, sans-serif'),
            showarrow=False,
            align='center',
        )],
        showlegend=True,
        legend=dict(
            orientation='v',
            yanchor='middle',
            y=0.5,
            xanchor='left',
            x=1.05,
            font=dict(size=12),
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=20, r=150, t=20, b=20),
        height=400,
    )
    return fig
@st.cache_data(ttl=3600)
def build_portfolio_chart(df, all_dates, forecast):
    """
    Улучшенный график динамики стоимости портфеля и вложенных средств.

    Использует колонки:
    - date
    - total_amount      — стоимость портфеля
    - expected_yield    — прибыль / убыток
    - fact_amount       — вложенные средства
    """

    import numpy as np
    import pandas as pd
    import plotly.graph_objects as go

    plot_df = df.copy()

    required_columns = ["date", "total_amount", "expected_yield", "fact_amount"]

    for col in required_columns:
        if col not in plot_df.columns:
            raise ValueError(
                f"В df отсутствует обязательная колонка: {col}. "
                f"Доступные колонки: {list(plot_df.columns)}"
            )

    # ─────────────────────────────────────────────
    # Подготовка данных
    # ─────────────────────────────────────────────
    plot_df["date"] = pd.to_datetime(plot_df["date"])
    plot_df["total_amount"] = pd.to_numeric(plot_df["total_amount"], errors="coerce")
    plot_df["expected_yield"] = pd.to_numeric(plot_df["expected_yield"], errors="coerce")
    plot_df["fact_amount"] = pd.to_numeric(plot_df["fact_amount"], errors="coerce")

    plot_df = plot_df.sort_values("date").dropna(
        subset=["date", "total_amount", "expected_yield", "fact_amount"]
    )

    if plot_df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Нет данных для построения графика",
            template="plotly_white",
            height=450,
        )
        return fig

    plot_df["yield_percent"] = np.where(
        plot_df["fact_amount"] != 0,
        plot_df["expected_yield"] / plot_df["fact_amount"] * 100,
        np.nan,
    )

    def money_fmt(value):
        if pd.isna(value):
            return "—"
        return f"{value:,.0f} ₽".replace(",", " ")

    def percent_fmt(value):
        if pd.isna(value):
            return "—"
        return f"{value:+.2f}%"

    plot_df["total_amount_fmt"] = plot_df["total_amount"].apply(money_fmt)
    plot_df["fact_amount_fmt"] = plot_df["fact_amount"].apply(money_fmt)
    plot_df["expected_yield_fmt"] = plot_df["expected_yield"].apply(money_fmt)
    plot_df["yield_percent_fmt"] = plot_df["yield_percent"].apply(percent_fmt)

    latest = plot_df.iloc[-1]

    latest_date = latest["date"]
    latest_total = latest["total_amount"]
    latest_yield = latest["expected_yield"]
    latest_yield_percent = latest["yield_percent"]

    is_profit = latest_yield >= 0

    profit_color = "#10b981" if is_profit else "#ef4444"
    profit_bg = "rgba(16, 185, 129, 0.12)" if is_profit else "rgba(239, 68, 68, 0.12)"
    area_color = "rgba(16, 185, 129, 0.13)" if is_profit else "rgba(239, 68, 68, 0.11)"

    custom_data = np.stack(
        [
            plot_df["total_amount_fmt"],
            plot_df["fact_amount_fmt"],
            plot_df["expected_yield_fmt"],
            plot_df["yield_percent_fmt"],
        ],
        axis=-1,
    )

    # ─────────────────────────────────────────────
    # Расчёт комфортного диапазона Y
    # Чтобы график не начинался от нуля
    # ─────────────────────────────────────────────
    y_values = list(plot_df["total_amount"]) + list(plot_df["fact_amount"])

    if forecast is not None:
        try:
            forecast_values_for_range = np.asarray(forecast, dtype=float)
            y_values += list(forecast_values_for_range)
        except Exception:
            pass

    y_values = [value for value in y_values if not pd.isna(value)]

    y_min = min(y_values)
    y_max = max(y_values)

    y_padding = max((y_max - y_min) * 0.18, y_max * 0.025)

    y_axis_min = max(0, y_min - y_padding)
    y_axis_max = y_max + y_padding

    # ─────────────────────────────────────────────
    # Создание графика
    # ─────────────────────────────────────────────
    fig = go.Figure()

    # Вложенные средства
    fig.add_trace(
        go.Scatter(
            x=plot_df["date"],
            y=plot_df["fact_amount"],
            name="Вложенные средства",
            mode="lines",
            line=dict(
                color="#6366f1",
                width=3,
                shape="linear",
            ),
            customdata=custom_data,
            hovertemplate=(
                "<b>%{x|%d.%m.%Y}</b><br><br>"
                "Вложено: <b>%{customdata[1]}</b><br>"
                "Стоимость портфеля: %{customdata[0]}<br>"
                "Результат: %{customdata[2]}<br>"
                "Доходность: %{customdata[3]}"
                "<extra></extra>"
            ),
        )
    )

    # Стоимость портфеля + заливка между линиями
    fig.add_trace(
        go.Scatter(
            x=plot_df["date"],
            y=plot_df["total_amount"],
            name="Стоимость портфеля",
            mode="lines",
            line=dict(
                color="#10b981",
                width=4,
                shape="linear",
            ),
            fill="tonexty",
            fillcolor=area_color,
            customdata=custom_data,
            hovertemplate=(
                "<b>%{x|%d.%m.%Y}</b><br><br>"
                "Стоимость портфеля: <b>%{customdata[0]}</b><br>"
                "Вложено: %{customdata[1]}<br>"
                "Результат: %{customdata[2]}<br>"
                "Доходность: %{customdata[3]}"
                "<extra></extra>"
            ),
        )
    )

    # ─────────────────────────────────────────────
    # Тренд и прогноз
    # ─────────────────────────────────────────────
    if forecast is not None and all_dates is not None:
        try:
            forecast_values = np.asarray(forecast, dtype=float)
            forecast_dates = pd.to_datetime(all_dates)

            min_len = min(len(forecast_values), len(forecast_dates))

            forecast_values = forecast_values[:min_len]
            forecast_dates = forecast_dates[:min_len]

            history_len = len(plot_df)

            # Историческая часть тренда
            trend_dates = forecast_dates[:history_len]
            trend_values = forecast_values[:history_len]

            # Будущая часть прогноза.
            # Берём с последней исторической точки, чтобы линия прогноза начиналась плавно.
            future_dates = forecast_dates[history_len - 1:min_len]
            future_values = forecast_values[history_len - 1:min_len]

            if len(trend_dates) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=trend_dates,
                        y=trend_values,
                        name="Тренд",
                        mode="lines",
                        line=dict(
                            color="#f59e0b",
                            width=2.5,
                            dash="dot",
                            shape="linear",
                        ),
                        hovertemplate=(
                            "<b>%{x|%d.%m.%Y}</b><br><br>"
                            "Линия тренда: <b>%{y:,.0f} ₽</b>"
                            "<extra></extra>"
                        ),
                    )
                )

            if len(future_dates) > 1:
                fig.add_trace(
                    go.Scatter(
                        x=future_dates,
                        y=future_values,
                        name="Прогноз",
                        mode="lines",
                        line=dict(
                            color="#f97316",
                            width=3,
                            dash="dash",
                            shape="linear",
                        ),
                        hovertemplate=(
                            "<b>%{x|%d.%m.%Y}</b><br><br>"
                            "Прогноз: <b>%{y:,.0f} ₽</b>"
                            "<extra></extra>"
                        ),
                    )
                )

                fig.add_vline(
                    x=latest_date,
                    line_width=1,
                    line_dash="dash",
                    line_color="rgba(100, 116, 139, 0.65)",
                )

                fig.add_annotation(
                    x=latest_date,
                    y=y_axis_max,
                    text="старт прогноза",
                    showarrow=False,
                    yshift=-18,
                    xshift=44,
                    font=dict(
                        size=11,
                        color="#64748b",
                    ),
                )

        except Exception:
            pass

    # ─────────────────────────────────────────────
    # Последняя точка
    # ─────────────────────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=[latest_date],
            y=[latest_total],
            name="Текущая стоимость",
            mode="markers",
            marker=dict(
                size=11,
                color="#ffffff",
                line=dict(
                    color=profit_color,
                    width=3,
                ),
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Аннотация текущего результата
    latest_yield_text = money_fmt(latest_yield)
    latest_yield_percent_text = percent_fmt(latest_yield_percent)

    annotation_text = (
        f"<b>{'Прибыль' if is_profit else 'Убыток'}: {latest_yield_text}</b><br>"
        f"{latest_yield_percent_text}"
    )

    fig.add_annotation(
        x=latest_date,
        y=latest_total,
        text=annotation_text,
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=1.3,
        arrowcolor=profit_color,
        ax=-80,
        ay=-45,
        bgcolor=profit_bg,
        bordercolor=profit_color,
        borderwidth=1,
        borderpad=7,
        font=dict(
            color=profit_color,
            size=12,
        ),
    )

    # ─────────────────────────────────────────────
    # Оформление
    # ─────────────────────────────────────────────
    fig.update_layout(
        title=dict(
            text=(
                "<b>Динамика стоимости портфеля</b>"
                "<br><sup>Стоимость портфеля относительно вложенных средств</sup>"
            ),
            x=0.02,
            y=0.98,
            xanchor="left",
            yanchor="top",
            font=dict(
                size=22,
                color="#0f172a",
            ),
        ),
        height=560,
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,250,252,0.75)",
        margin=dict(
            l=35,
            r=35,
            t=120,
            b=45,
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0)",
            font=dict(
                size=12,
                color="#334155",
            ),
        ),
        font=dict(
            family="Inter, Arial, sans-serif",
            color="#334155",
        ),
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor="rgba(148, 163, 184, 0.35)",
        tickfont=dict(
            size=12,
            color="#64748b",
        ),
        rangeselector=dict(
            buttons=[
                dict(count=1, label="1М", step="month", stepmode="backward"),
                dict(count=3, label="3М", step="month", stepmode="backward"),
                dict(count=6, label="6М", step="month", stepmode="backward"),
                dict(step="all", label="Все"),
            ],
            bgcolor="rgba(241, 245, 249, 0.95)",
            activecolor="rgba(16, 185, 129, 0.18)",
            font=dict(
                size=12,
                color="#334155",
            ),
        ),
    )

    fig.update_yaxes(
        range=[y_axis_min, y_axis_max],
        showgrid=True,
        gridcolor="rgba(148, 163, 184, 0.18)",
        zeroline=False,
        tickformat=",.0f",
        ticksuffix=" ₽",
        tickfont=dict(
            size=12,
            color="#64748b",
        ),
    )

    return fig
@st.cache_data(ttl=3600)
def build_bar_assets(df: pd.DataFrame):
    """
    Горизонтальный бар — распределение вложений по активам
    df — из load_bar_money()
    """
    fig = px.bar(
        df,
        x="активы",
        y="Вложено",
        text="Вложено",
        color_discrete_sequence=["#F4A261"],
    )

    fig.update_traces(
        texttemplate="%{text:,.0f} ₽",
        textposition="outside",
    )

    fig.update_layout(
        plot_bgcolor="#F8F9FA",
        paper_bgcolor="white",
        margin=dict(l=80, r=40, t=40, b=40),
        height=400,
        xaxis_title="Вложено, ₽",
        yaxis_title="",
    )

    return fig
@st.cache_data(ttl=3600)
def build_market_comparison(df):
    """
    График сравнения портфеля и рынка
    df должен содержать:
    - dt
    - Мой портфель
    - Рынок
    """
    df = df.copy()

    df["dt"] = pd.to_datetime(df["dt"], errors="coerce")
    df["Мой портфель"] = pd.to_numeric(df["Мой портфель"], errors="coerce")
    df["Рынок"] = pd.to_numeric(df["Рынок"], errors="coerce")

    df = df.dropna(subset=["dt", "Мой портфель", "Рынок"]).sort_values("dt")

    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="Нет данных для отображения")
        return fig

    last = df.iloc[-1]
    last_dt = last["dt"]
    last_portf = last["Мой портфель"]
    last_market = last["Рынок"]
    portf_vs_market = last_portf - last_market

    result_color = "#2DC653" if portf_vs_market >= 0 else "#E63946"
    result_text = "Обгоняю рынок" if portf_vs_market >= 0 else "Отстаю от рынка"
    sign = "+" if portf_vs_market >= 0 else ""

    fig = go.Figure()

    

    # Линия портфеля
    fig.add_trace(go.Scatter(
        x=df["dt"],
        y=df["Мой портфель"],
        mode="lines",
        name="Мой портфель",
        line=dict(color="#1D3557", width=3),
        hovertemplate="Дата: %{x|%d.%m.%Y}<br>Портфель: %{y:.2f}%<extra></extra>"
    ))

    # Линия рынка
    fig.add_trace(go.Scatter(
        x=df["dt"],
        y=df["Рынок"],
        mode="lines",
        name="Рынок (IMOEX)",
        line=dict(color="#F4A261", width=2.5, dash="dot"),
        hovertemplate="Дата: %{x|%d.%m.%Y}<br>Рынок: %{y:.2f}%<extra></extra>"
    ))

    # Маркеры на последних точках
    fig.add_trace(go.Scatter(
        x=[last_dt],
        y=[last_portf],
        mode="markers",
        marker=dict(size=9, color="#1D3557"),
        name="Портфель (текущее)",
        showlegend=False,
        hovertemplate="Портфель: %{y:.2f}%<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=[last_dt],
        y=[last_market],
        mode="markers",
        marker=dict(size=9, color="#F4A261"),
        name="Рынок (текущее)",
        showlegend=False,
        hovertemplate="Рынок: %{y:.2f}%<extra></extra>"
    ))

    # Нулевая линия
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="#ADB5BD",
        line_width=1
    )

    # Подписи последних значений справа
    fig.add_annotation(
        x=last_dt,
        y=last_portf,
        text=f"<b>Портфель: {last_portf:.2f}%</b>",
        showarrow=True,
        arrowhead=0,
        ax=60,
        ay=0,
        font=dict(size=12, color="#1D3557"),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#1D3557",
        borderwidth=1
    )

    fig.add_annotation(
        x=last_dt,
        y=last_market,
        text=f"<b>Рынок: {last_market:.2f}%</b>",
        showarrow=True,
        arrowhead=0,
        ax=60,
        ay=0,
        font=dict(size=12, color="#A85D1A"),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#F4A261",
        borderwidth=1
    )

    # Итоговый бейдж
    fig.add_annotation(
        x=0.01,
        y=1.12,
        xref="paper",
        yref="paper",
        text=f"<b>{result_text}: {sign}{portf_vs_market:.2f} п.п.</b>",
        showarrow=False,
        font=dict(size=13, color=result_color),
        bgcolor="rgba(255,255,255,0.95)",
        bordercolor=result_color,
        borderwidth=1,
        borderpad=6,
        xanchor="left"
    )

    fig.update_layout(
        title=dict(
            text="📈 Портфель vs рынок",
            x=0.5,
            xanchor="center",
            font=dict(size=18)
        ),
        height=540,
        plot_bgcolor="#F8F9FA",
        paper_bgcolor="white",
        font=dict(
            family="Inter, Arial, sans-serif",
            size=13,
            color="#2B2D42"
        ),
        hovermode="x unified",
        margin=dict(l=60, r=100, t=90, b=60),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            title="",
            showgrid=False,
            showline=True,
            linecolor="#CED4DA",
            showspikes=True,
            spikemode="across",
            spikecolor="#ADB5BD",
            spikethickness=1,
            tickformat="%d.%m.%y",
            rangeslider=dict(visible=False)
        ),
        yaxis=dict(
            title="Накопленная доходность",
            ticksuffix="%",
            showgrid=True,
            gridcolor="#E9ECEF",
            zeroline=False
        )
    )

    return fig

@st.cache_data(ttl=3600)
def build_monthly_heatmap(df):
    df = df.copy()
    df['monthly_return'] = pd.to_numeric(df['monthly_return'], errors='coerce')
    df['year'] = df['year'].astype(str)   # ← ключевой фикс — год как строка!

    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    pivot = df.pivot_table(
        index   = 'year',
        columns = 'month_name',
        values  = 'monthly_return',
        aggfunc = 'first'
    )

    pivot = pivot.reindex(
        columns=[m for m in month_order if m in pivot.columns]
    )

    years    = list(pivot.index)
    months   = list(pivot.columns)
    z_values = pivot.values.tolist()

    text_values = []
    for row in z_values:
        text_row = []
        for val in row:
            if pd.isna(val):
                text_row.append('')
            elif val >= 0:
                text_row.append(f'+{val:.2f}%')
            else:
                text_row.append(f'{val:.2f}%')
        text_values.append(text_row)

    fig = go.Figure(go.Heatmap(
        z            = z_values,
        x            = months,
        y            = [str(y) for y in years],   # ← строки!
        text         = text_values,
        texttemplate = '%{text}',
        textfont     = dict(size=13, family='Inter, sans-serif'),
        colorscale   = [
            [0.0, '#E63946'],
            [0.5, '#F8F9FA'],
            [1.0, '#2DC653'],
        ],
        zmid          = 0,
        showscale     = False,
        hovertemplate = (
            '<b>%{y} — %{x}</b><br>'
            'Доходность: %{z:.2f}%'
            '<extra></extra>'
        ),
        xgap = 4,
        ygap = 4,
    ))

    fig.update_layout(
        title = dict(
            text    = '📅 Доходность по месяцам',
            x       = 0.5,
            xanchor = 'center',
            font    = dict(size=16),
        ),
        plot_bgcolor  = 'white',
        paper_bgcolor = 'white',
        font          = dict(family='Inter, sans-serif', size=13, color='#2B2D42'),
        height        = 120 + len(years) * 80,
        margin        = dict(l=80, r=80, t=80, b=60),
        xaxis = dict(
            side     = 'top',          # ← месяцы сверху красивее
            showgrid = False,
            tickangle = 0,
            type     = 'category',     # ← явно категория
        ),
        yaxis = dict(
            showgrid  = False,
            autorange = 'reversed',
            type      = 'category',    # ← явно категория
        ),
    )

    return fig
import ta
import numpy as np

# Настройки EMA под период
EMA_SETTINGS = {
    '1D' : (20, 100),
    '1W' : (20, 50),
    '1M' : (10, 30),
    '6M' : (20, 60),
    '1Y' : (10, 30),
    'ALL': (10, 30),
}
@st.cache_data(ttl=3600)
def build_candle_chart(df_full: pd.DataFrame,
                       df_display: pd.DataFrame,
                       ticker_name: str,
                       period: str = '1D') -> go.Figure:

    df = df_full.copy()

    ema_fast, ema_slow = EMA_SETTINGS.get(period, (20, 100))

    # ── Индикаторы на ПОЛНЫХ данных ──────────────────────────
    df['EMA_fast'] = ta.trend.ema_indicator(df['close'], window=ema_fast)
    df['EMA_slow'] = ta.trend.ema_indicator(df['close'], window=ema_slow)

    bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
    df['BB_High'] = bb.bollinger_hband()
    df['BB_Low']  = bb.bollinger_lband()
    df['BB_Mid']  = bb.bollinger_mavg()

    # ── Обрезаем до нужного периода ──────────────────────────
    df = df[df.index.isin(df_display.index)]

    fig = go.Figure()

    # Bollinger заливка
    fig.add_trace(go.Scatter(
        x=df.index, y=df['BB_High'],
        line=dict(color='rgba(173,216,230,0)'),
        showlegend=False, hoverinfo='skip', name='BB High',
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df['BB_Low'],
        fill='tonexty', fillcolor='rgba(173,216,230,0.2)',
        line=dict(color='rgba(173,216,230,0)'),
        showlegend=True, name='Bollinger Bands', hoverinfo='skip',
    ))

    # Bollinger линии
    for col, label, dash in [
        ('BB_High', 'BB Upper', 'dot'),
        ('BB_Mid',  'BB Mid',   'dash'),
        ('BB_Low',  'BB Lower', 'dot'),
    ]:
        fig.add_trace(go.Scatter(
            x=df.index, y=df[col], mode='lines', name=label,
            line=dict(color='#ADD8E6', width=1, dash=dash),
            hovertemplate=f'{label}: %{{y:.2f}}<extra></extra>',
        ))

    # Свечи
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'], high=df['high'],
        low=df['low'],   close=df['close'],
        name=ticker_name,
        increasing_line_color='#2DC653',
        decreasing_line_color='#E63946',
    ))

    # EMA
    fig.add_trace(go.Scatter(
        x=df.index, y=df['EMA_fast'], mode='lines',
        name=f'EMA20',
        line=dict(color='#F4A261', width=1.5),
        hovertemplate=f'EMA20: %{{y:.2f}}<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df['EMA_slow'], mode='lines',
        name=f'EMA100',
        line=dict(color='#1D3557', width=1.5),
        hovertemplate=f'EMA100: %{{y:.2f}}<extra></extra>',
    ))

    fig.update_layout(
        title=dict(
            text=f'📊 {ticker_name} — Технический анализ',
            x=0.5, xanchor='center', font=dict(size=16),
        ),
        plot_bgcolor='#F8F9FA', paper_bgcolor='white',
        font=dict(family='Inter, sans-serif', size=12, color='#2B2D42'),
        height=550,
        margin=dict(l=60, r=60, t=80, b=60),
        hovermode='x unified',
        xaxis_rangeslider_visible=False,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        yaxis=dict(showgrid=True, gridcolor='#E9ECEF', title='Цена, ₽'),
        xaxis=dict(showgrid=False, showline=True, linecolor='#CED4DA'),
    )

    return fig


from data.assets import load_candles_for_mc
@st.cache_data(ttl=3600)
def build_monte_carlo(figi: str,          # ← принимаем figi
                      ticker_name: str,
                      num_simulations: int = 1000,
                      confidence_level: float = 0.95) -> tuple:

    # Всегда грузим дневные — независимо от периода графика
    df = load_candles_for_mc(figi)
    df['close'] = pd.to_numeric(df['close'], errors='coerce').astype(float)

    returns    = np.log(df['close'] / df['close'].shift(1)).dropna()
    mu         = returns.mean()
    sigma      = returns.std()
    last_price = df['close'].iloc[-1]

    np.random.seed(42)
    sim_returns = np.random.normal(mu, sigma, num_simulations)
    sim_prices  = last_price * np.exp(sim_returns)
    pl          = sim_prices - last_price

    threshold = np.percentile(pl, (1 - confidence_level) * 100)
    var_value = -threshold

    # ── График ────────────────────────────────────────────────
    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=pl,
        nbinsx=80,
        name='P&L распределение',
        marker=dict(
            color='#1D3557',
            opacity=0.75,
            line=dict(color='white', width=0.3),
        ),
        hovertemplate='P&L: %{x:.2f} ₽<br>Частота: %{y}<extra></extra>',
    ))

    fig.add_vline(
        x=threshold,
        line_color='#E63946',
        line_width=2,
        line_dash='dash',
        annotation_text=f"  VaR {int(confidence_level * 100)}%: -{var_value:.2f} ₽",
        annotation_position="top right",
        annotation_font=dict(color='#E63946', size=13),
    )

    fig.add_vline(
        x=0,
        line_color='#CED4DA',
        line_width=1,
    )

    fig.update_layout(
        title=dict(
            text=f'🎲 Монте-Карло: распределение P&L — {ticker_name}',
            x=0.5,
            xanchor='center',
            font=dict(size=16),
        ),
        plot_bgcolor='#F8F9FA',
        paper_bgcolor='white',
        font=dict(family='Inter, sans-serif', size=12, color='#2B2D42'),
        height=400,
        margin=dict(l=60, r=60, t=80, b=60),
        showlegend=False,
        xaxis=dict(
            title='Прибыль / Убыток (₽)',
            showgrid=False,
            showline=True,
            linecolor='#CED4DA',
        ),
        yaxis=dict(
            title='Частота',
            showgrid=True,
            gridcolor='#E9ECEF',
        ),
    )

    return fig, var_value, last_price

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def build_payment_calendar(df: pd.DataFrame):
    if df is None or df.empty:
        return None

    # Словарь для красивого отображения месяцев на русском
    months_ru = {
        '01': 'Янв', '02': 'Фев', '03': 'Мар', '04': 'Апр',
        '05': 'Май', '06': 'Июн', '07': 'Июл', '08': 'Авг',
        '09': 'Сен', '10': 'Окт', '11': 'Ноя', '12': 'Дек'
    }

    df = df.copy()
    df['year_month'] = df['payment_date'].dt.strftime('%Y-%m')
    df['month_num'] = df['payment_date'].dt.strftime('%m')
    df['month_name'] = df['month_num'].map(months_ru) + ' ' + df['payment_date'].dt.strftime('%Y')
    
    # ДОБАВЛЕНО: Создаем красивую строку с точной датой (например, 15.06.2026)
    df['exact_date'] = df['payment_date'].dt.strftime('%d.%m.%Y')

    # ИЗМЕНЕНО: Добавили exact_date в группировку. 
    # Теперь если в одном месяце выплаты в разные дни, график их "запомнит"
    df_grouped = df.groupby(['year_month', 'month_name', 'exact_date', 'name'])['amount'].sum().reset_index()
    df_grouped = df_grouped.sort_values(['year_month', 'exact_date'])

    # Считаем итоги по месяцам
    monthly_totals = df_grouped.groupby(['year_month', 'month_name'])['amount'].sum().reset_index()
    max_monthly_sum = monthly_totals['amount'].max() if not monthly_totals.empty else 0

    # Прячем текст в мелких блоках (меньше 4% от максимума)
    threshold = max_monthly_sum * 0.04
    df_grouped['text_label'] = df_grouped['amount'].apply(
        lambda x: f"{x:,.0f}".replace(',', ' ') if x >= threshold else ""
    )

    # Строим основной график
    fig = px.bar(
        df_grouped,
        x="month_name",
        y="amount",
        color="name",
        text="text_label",
        custom_data=["exact_date"], # ДОБАВЛЕНО: прокидываем точную дату в график
        labels={
            "month_name": "",
            "amount": "Сумма (₽)",
            "name": "Активы"
        }
    )

    # Итоги НАД столбцами
    fig.add_trace(go.Scatter(
        x=monthly_totals['month_name'],
        y=monthly_totals['amount'],
        text=monthly_totals['amount'].apply(lambda x: f"<b>{x:,.0f} ₽</b>".replace(',', ' ')),
        mode='text',
        textposition='top center',
        showlegend=False,
        hoverinfo='skip'
    ))

    # Настройки визуала
    fig.update_layout(
        barmode='stack',
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified", # Показывает всплывашку для всего месяца сразу
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            title_text=""
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor='rgba(128, 128, 128, 0.2)',
            range=[0, max_monthly_sum * 1.15]
        ),
    )
    
    # ИЗМЕНЕНО: Настраиваем всплывашку. Вытаскиваем дату через %{customdata[0]}
    fig.update_traces(
        selector=dict(type='bar'),
        textposition='inside', 
        textfont=dict(color='white'),
        hovertemplate="<b>%{fullData.name}</b> [%{customdata[0]}]: %{y:,.0f} ₽<extra></extra>"
    )

    return fig
