
from db import select
import streamlit as st
import pandas as pd
@st.cache_data(ttl=3600)
def load_donut_top():
    """Распределение по типам активов (текущая цена) — верхний уровень бублика"""
    df = select('''
        WITH per1 AS (
            SELECT instrument_type, SUM(current_price * quantity) AS sm
            FROM portfolio_positions
            WHERE date = date(now())
            GROUP BY instrument_type
        )
        SELECT 1 AS nm,
            SUM(CASE WHEN instrument_type = 'share'    THEN sm ELSE 0 END) AS "Акции",
            SUM(CASE WHEN instrument_type = 'bond'     THEN sm ELSE 0 END) AS "Облигации",
            SUM(CASE WHEN instrument_type = 'currency' THEN sm ELSE 0 END) AS "Золото"
        FROM per1
    ''')
    return df.melt(id_vars=["nm"], var_name="Активы", value_name="По факту")

@st.cache_data(ttl=3600)
def load_donut_detail():
    """Детализация внутри категории — для drill-down бублика"""
    return select('''
        SELECT
            instrument_type,
            name,
            SUM(current_price * quantity) AS amount
        FROM portfolio_positions
        WHERE date = date(now())
        GROUP BY instrument_type, name
        ORDER BY instrument_type, amount DESC
    ''')

@st.cache_data(ttl=3600)
def load_top_alltime():
    """Топ 5 лучших/худших за всё время по доходности"""
    return select('''
        WITH latest AS (
            SELECT
                name,
                expected_yield / NULLIF(quantity * average_price, 0) AS perc_yield
            FROM portfolio_positions
            WHERE date = (SELECT MAX(date) FROM portfolio_positions)
              AND name NOT IN ('Unknown', 'Российский рубль')
        ),
        ranked AS (
            SELECT
                name,
                ROUND((perc_yield * 100)::numeric, 2)            AS end_yield_pct,
                ROW_NUMBER() OVER (ORDER BY perc_yield ASC)      AS rank_worst,
                ROW_NUMBER() OVER (ORDER BY perc_yield DESC)     AS rank_best
            FROM latest
        )
        SELECT name, end_yield_pct, rank_worst, rank_best
        FROM ranked
        WHERE rank_worst <= 5 OR rank_best <= 5
        ORDER BY end_yield_pct DESC
    ''')

@st.cache_data(ttl=3600)
def load_top_daily():
    """Топ 5 лучших/худших по изменению доходности за последний день"""
    return select('''
        WITH two_dates AS (
            SELECT DISTINCT date
            FROM portfolio_positions
            ORDER BY date DESC
            LIMIT 2
        ),
        today_data AS (
            SELECT
                name,
                expected_yield / NULLIF(quantity * average_price, 0) AS perc_yield_today
            FROM portfolio_positions
            WHERE date = (SELECT MAX(date) FROM two_dates)
              AND name NOT IN ('Unknown', 'Российский рубль')
        ),
        yesterday_data AS (
            SELECT
                name,
                expected_yield / NULLIF(quantity * average_price, 0) AS perc_yield_yesterday
            FROM portfolio_positions
            WHERE date = (SELECT MIN(date) FROM two_dates)
              AND name NOT IN ('Unknown', 'Российский рубль')
        ),
        combined AS (
            SELECT
                t.name,
                ROUND((t.perc_yield_today * 100)::numeric, 2)                             AS yield_today_pct,
                ROUND((y.perc_yield_yesterday * 100)::numeric, 2)                         AS yield_yesterday_pct,
                ROUND(((t.perc_yield_today - y.perc_yield_yesterday) * 100)::numeric, 2)  AS diff_pct
            FROM today_data t
            JOIN yesterday_data y ON t.name = y.name
        ),
        ranked AS (
            SELECT *,
                ROW_NUMBER() OVER (ORDER BY diff_pct ASC)  AS rank_worst,
                ROW_NUMBER() OVER (ORDER BY diff_pct DESC) AS rank_best
            FROM combined
        )
        SELECT name, yield_today_pct, yield_yesterday_pct, diff_pct, rank_worst, rank_best
        FROM ranked
        WHERE rank_worst <= 5 OR rank_best <= 5
        ORDER BY diff_pct DESC
    ''')
@st.cache_data(ttl=3600)
def load_market_comparison():
    """Сравнение доходности портфеля и рынка (IMOEX) накопленным итогом"""
    return select('''
        WITH ld AS (
            SELECT
                pm.date                    AS dt,
                pm.expected_yield_percent  AS perc,
                pm.imoex_points,
                LEAD(pm.expected_yield_percent) OVER (ORDER BY pm.date) AS ld_portf,
                LEAD(pm.imoex_points)           OVER (ORDER BY pm.date) AS ld_index
            FROM portfolio_metrics pm
        ),
        diff AS (
            SELECT
                dt,
                ld_portf - perc                                          AS diff_my_portf,
                ROUND((ld_index - imoex_points) / imoex_points * 100, 2) AS diff_market
            FROM ld
            WHERE ld_portf IS NOT NULL AND ld_index IS NOT NULL
        )
        SELECT
            dt,
            sum(diff_my_portf) OVER (ORDER BY dt) AS "Мой портфель",
            sum(diff_market)   OVER (ORDER BY dt) AS "Рынок"
        FROM diff
        ORDER BY 1
    ''')
@st.cache_data(ttl=3600)
def load_monthly_returns():
    """Доходность портфеля по месяцам — конец месяца минус начало"""
    return select('''
        WITH monthly AS (
            SELECT
                to_char(date, 'YYYY')  AS year,
                to_char(date, 'MM')    AS month_num,
                to_char(date, 'Mon')   AS month_name,
                expected_yield_percent,
                FIRST_VALUE(expected_yield_percent) OVER (
                    PARTITION BY to_char(date, 'YYYY'), to_char(date, 'MM')
                    ORDER BY date ASC
                ) AS first_val,
                FIRST_VALUE(expected_yield_percent) OVER (
                    PARTITION BY to_char(date, 'YYYY'), to_char(date, 'MM')
                    ORDER BY date DESC
                ) AS last_val
            FROM portfolio_metrics
        )
        SELECT DISTINCT
            year,
            month_num,
            month_name,
            ROUND((last_val - first_val)::numeric, 4) AS monthly_return
        FROM monthly
        ORDER BY 1, 2
    ''')


@st.cache_data(ttl=3600)
def load_candles_for_mc(figi: str) -> pd.DataFrame:
    """
    Загружаем все часовые свечи → агрегируем в дневные
    """
    query = f"""
        SELECT time, close
        FROM market_candles
        WHERE figi = '{figi}'
        ORDER BY time ASC
    """
    df = select(query)
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time')

    # Агрегируем часовые → дневные
    df_daily = df['close'].resample('1D').last().dropna()
    df_daily = df_daily.astype(float)
    return df_daily.to_frame()