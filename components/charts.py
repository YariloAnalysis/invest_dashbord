
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


def build_portfolio_chart(df: pd.DataFrame, all_dates, forecast_extended):
    """
    Основной график портфеля
    df               — DataFrame из load_portfolio_metrics()
    all_dates        — даты включая прогноз
    forecast_extended — значения тренда включая прогноз
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # ── Бары — вложенные средства ────────────────────────────
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['fact_amount'],
        name='Вложенные средства',
        marker=dict(
            color='rgba(29, 53, 87, 0.4)',
            line=dict(color='#1D3557', width=1)
        ),
    ), secondary_y=False)

    # ── Линия — стоимость портфеля ───────────────────────────
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['total_amount'],
        mode='lines',
        name='Стоимость портфеля',
        fill='tozeroy',
        fillcolor='rgba(29, 53, 87, 0.07)',
        line=dict(color='#1D3557', width=2.5),
        hovertemplate='Дата: %{x}<br>Стоимость: %{y:,.0f}<extra></extra>'
    ), secondary_y=False)

    # ── Линия — доходность % ─────────────────────────────────
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['expected_yield_percent'],
        mode='lines+text',
        name='Доходность, %',
        line=dict(color='#F4A261', width=2, dash='dot'),
        text=[f"{v:.1f}%" for v in df['expected_yield_percent']],
        textposition='top center',
        textfont=dict(size=10, color='#2B2D42', family='Inter Black, Inter, sans-serif'),
        hovertemplate='Дата: %{x}<br>Доходность: %{y:.2f}%<extra></extra>'
    ), secondary_y=True)

    # ── Layout ───────────────────────────────────────────────
    fig.update_layout(
        title=dict(
            text='Процесс рождения деняк',
            x=0.5,
            xanchor='center'
        ),
        plot_bgcolor='#F8F9FA',
        paper_bgcolor='white',
        font=dict(family='Inter, sans-serif', size=13, color='#2B2D42'),
        hovermode='x unified',
        barmode='group',
        height=550,
        margin=dict(l=60, r=60, t=80, b=60),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )

    fig.update_xaxes(
        type='date',
        showgrid=False,
        showline=True,
        linecolor='#CED4DA',
        tickfont=dict(size=11)
    )
    fig.update_yaxes(
        title_text='Сумма (₽)',
        showgrid=True,
        gridcolor='#E9ECEF',
        gridwidth=1,
        secondary_y=False
    )
    fig.update_yaxes(
        title_text='Доходность, %',
        showgrid=False,
        secondary_y=True
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
    df — из load_market_comparison()
    """
    df = df.copy()
    df['Мой портфель'] = pd.to_numeric(df['Мой портфель'], errors='coerce')
    df['Рынок']        = pd.to_numeric(df['Рынок'],        errors='coerce')

    # Последние значения для аннотаций
    last             = df.iloc[-1]
    last_portf       = last['Мой портфель']
    last_market      = last['Рынок']
    portf_vs_market  = last_portf - last_market

    # Цвет итоговой плашки
    color_result = "#2DC653" if portf_vs_market >= 0 else "#E63946"
    sign         = "+" if portf_vs_market >= 0 else ""

    fig = go.Figure()

    # ── Мой портфель ────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x    = df['dt'],
        y    = df['Мой портфель'],
        mode = 'lines',
        name = 'Мой портфель',
        line = dict(color='#1D3557', width=2.5),
        fill = 'tonexty',
        fillcolor = 'rgba(29, 53, 87, 0.07)',
        hovertemplate = 'Дата: %{x}<br>Портфель: %{y:.2f}%<extra></extra>'
    ))

    # ── Рынок (IMOEX) ────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x    = df['dt'],
        y    = df['Рынок'],
        mode = 'lines',
        name = 'Рынок (IMOEX)',
        line = dict(color='#F4A261', width=2.5, dash='dot'),
        fill = 'tonexty',
        fillcolor = 'rgba(244, 162, 97, 0.07)',
        hovertemplate = 'Дата: %{x}<br>Рынок: %{y:.2f}%<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=df['dt'],
        y=df['Мой портфель'],
        fill='tonexty',
        fillcolor='rgba(45, 198, 83, 0.15)',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip',
    ))

    # ── Нулевая линия ────────────────────────────────────────
    fig.add_hline(
        y           = 0,
        line_dash   = 'dash',
        line_color  = '#CED4DA',
        line_width  = 1,
    )

    # ── Аннотация итога ──────────────────────────────────────
    fig.add_annotation(
        x         = df['dt'].iloc[-1],
        y         = max(last_portf, last_market),
        text      = f"<b>Разрыв: {sign}{portf_vs_market:.2f}%</b>",
        showarrow = False,
        font      = dict(size=13, color=color_result),
        bgcolor   = "white",
        bordercolor = color_result,
        borderwidth = 1,
        borderpad   = 6,
        xanchor   = 'right',
    )

    # ── Layout ───────────────────────────────────────────────
    fig.update_layout(
        title = dict(
            text     = '📈 Мой портфель vs Рынок (IMOEX)',
            x        = 0.5,
            xanchor  = 'center',
            font     = dict(size=16)
        ),
        plot_bgcolor  = '#F8F9FA',
        paper_bgcolor = 'white',
        font          = dict(family='Inter, sans-serif', size=13, color='#2B2D42'),
        hovermode     = 'x unified',
        height        = 500,
        margin        = dict(l=60, r=60, t=80, b=60),
        legend        = dict(
            orientation = 'h',
            yanchor     = 'bottom',
            y           = 1.02,
            xanchor     = 'right',
            x           = 1,
        ),
        yaxis = dict(
            title      = 'Накопленная доходность, %',
            showgrid   = True,
            gridcolor  = '#E9ECEF',
            gridwidth  = 1,
            ticksuffix = '%',
        ),
        xaxis = dict(
            showgrid  = False,
            showline  = True,
            linecolor = '#CED4DA',
        ),
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
