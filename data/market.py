from db import select
import pandas as pd
import streamlit as st
TICKER_MAP = {
    'TCS20A107662': 'HEAD',
    'TCS03A108X38': 'X5',
    'BBG004S68473': 'IRAO',
    'BBG004730N88': 'SBER',
}

TICKER_MAP_REVERSE = {v: k for k, v in TICKER_MAP.items()}
@st.cache_data(ttl=3600)
def load_candles(figi: str, period: str = '1D') -> tuple:
    """
    Возвращает два датафрейма:
    df_full     — все данные (для расчёта индикаторов)
    df_display  — обрезанный по периоду (для отображения)
    """
    df = select(f'''
        SELECT time, open, high, low, close, volume
        FROM market_candles
        WHERE figi = '{figi}'
        ORDER BY time
    ''')
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time')
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Агрегация для длинных периодов
    rule = {
        '1D' : None,
        '1W' : '4h',
        '1M' : '1D',
        '6M' : '1D',
        '1Y' : '1W',
        'ALL': '1W',
    }.get(period)

    if rule:
        df = df.resample(rule).agg({
            'open'  : 'first',
            'high'  : 'max',
            'low'   : 'min',
            'close' : 'last',
            'volume': 'sum',
        }).dropna()

    # df_full — для индикаторов (все данные после агрегации)
    df_full = df.copy()

    # df_display — обрезаем по периоду
    now = df.index.max()
    delta = {
        '1D' : pd.Timedelta(days=1),
        '1W' : pd.Timedelta(weeks=1),
        '1M' : pd.Timedelta(days=30),
        '6M' : pd.Timedelta(days=180),
        '1Y' : pd.Timedelta(days=365),
        'ALL': None,
    }.get(period)

    df_display = df if delta is None else df[df.index >= now - delta]

    return df_full, df_display
@st.cache_data(ttl=3600)
def load_available_tickers() -> list:
    df = select('SELECT DISTINCT figi FROM market_candles')
    return sorted([TICKER_MAP.get(f, f) for f in df['figi']])