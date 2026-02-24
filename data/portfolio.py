
import pandas as pd
import numpy as np
from db import select
from constants import FORECAST_DAYS

def load_portfolio_metrics():
    """Основные метрики портфеля + прогноз тренда"""
    df = select("""
        SELECT date, total_amount, expected_yield, expected_yield_percent
        FROM portfolio_metrics
        ORDER BY date
    """)


    df['total_amount']   = pd.to_numeric(df['total_amount'],   errors='coerce')
    df['expected_yield'] = pd.to_numeric(df['expected_yield'], errors='coerce')
    df['fact_amount']    = df['total_amount'] - df['expected_yield']


    x_numeric        = np.arange(len(df))
    z                = np.polyfit(x_numeric, df['total_amount'], 1)
    p                = np.poly1d(z)
    x_extended       = np.arange(len(df) + FORECAST_DAYS)
    forecast_extended = p(x_extended)

    last_date    = df['date'].iloc[-1]
    future_dates = pd.date_range(
        start   = pd.to_datetime(last_date) + pd.Timedelta(days=1),
        periods = FORECAST_DAYS,
        freq    = 'D'
    )
    all_dates = pd.to_datetime(list(df['date']) + list(future_dates))

    return df, all_dates, forecast_extended


def load_portfolio_today():
    """Метрики за сегодня и вчера для st.metric"""
    df, _, _ = load_portfolio_metrics()

    today     = df.iloc[-1]
    yesterday = df.iloc[-2]

    value_today    = today['total_amount']
    invested_today = today['fact_amount']
    proffit        = today['expected_yield']

    return_today     = (value_today / invested_today - 1) * 100
    return_yesterday = (yesterday['total_amount'] / yesterday['fact_amount'] - 1) * 100
    delta_return     = return_today - return_yesterday

    return {
        'value_today':    value_today,
        'invested_today': invested_today,
        'proffit':        proffit,
        'return_today':   return_today,
        'delta_return':   delta_return,
    }


def load_bar_money():
    """Распределение вложений по типам активов"""
    df = select('''
        WITH per1 AS (
            SELECT instrument_type, SUM(average_price * quantity) AS sm
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
    return df.melt(id_vars=["nm"], var_name="активы", value_name="Вложено")


def load_coupon_metrics():
    """Купонная доходность — сумма облигаций + купоны за год"""
    suma_per = select("""
        SELECT COALESCE(SUM(average_price * quantity), 0) AS sm
        FROM portfolio_positions
        WHERE date = date(now())
          AND instrument_type = 'bond'
    """)

    coupon_per = select('''
        WITH per1 AS (
            SELECT
                payment_date, name, amount,
                to_char(now(), 'YYYY') AS nw,
                CASE WHEN currency = 'usd' THEN amount * 90 ELSE amount END AS sma
            FROM payment_calendar
        )
        SELECT COALESCE(SUM(sma), 0) AS sma
        FROM per1
        WHERE to_char(payment_date, 'YYYY') = nw
    ''')

    df_coupons = select('''
        WITH per1 AS (
            SELECT
                payment_date, name, amount,
                to_char(now(), 'YYYY') AS nw,
                CASE WHEN currency = 'usd' THEN amount * 90 ELSE amount END AS sma
            FROM payment_calendar
        )
        SELECT payment_date, name, amount
        FROM per1
        WHERE to_char(payment_date, 'YYYY') = nw
        ORDER BY payment_date
    ''')
    df_calendar = select('''
            WITH per1 AS (
                SELECT
                    date(payment_date) as dt, name, amount,
                    to_char(now(), 'YYYY') AS nw,
                    CASE WHEN currency = 'usd' THEN amount * 90 ELSE amount END AS sma
                FROM payment_calendar
            )
            SELECT dt, name, sum(amount) as sm
            FROM per1
            WHERE to_char(dt, 'YYYY') = nw
            GROUP BY 1,2
            ORDER BY 1
    ''')

    # Дополнительная защита на случай пустого датафрейма
    suma_val   = float(suma_per.iloc[0, 0])   if not suma_per.empty   else 0.0
    coupon_val = float(coupon_per.iloc[0, 0]) if not coupon_per.empty else 0.0

    return {
        'suma':       suma_val,
        'coupon':     coupon_val,
        'df_coupons': df_coupons,
    }