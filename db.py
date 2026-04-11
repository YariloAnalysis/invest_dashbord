
import streamlit as st
import pandas as pd
import requests
import os
from dotenv import load_dotenv
from decimal import Decimal
from datetime import date, datetime
import json


class CustomEncoder(json.JSONEncoder):
    """Для сериализации Decimal, date, datetime из API"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


def get_api_url() -> str:
    try:
        return st.secrets["API_URL"]
    except Exception:
        load_dotenv()
        return os.getenv("API_URL", "http://localhost:8000")


def get_token() -> str | None:
    return st.session_state.get("jwt_token")


def api_get(endpoint: str, params: dict = None) -> pd.DataFrame:
    """
    GET к FastAPI. Возвращает pd.DataFrame.
    Использует Bearer-токен из session_state.
    """
    token = get_token()
    if not token:
        st.error("🔒 Требуется авторизация")
        st.stop()

    api_url = get_api_url()

    try:
        response = requests.get(
            f"{api_url}{endpoint}",
            params=params or {},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )

        if response.status_code == 401:
            st.error("🔒 Сессия истекла — войдите заново")
            for key in ["jwt_token", "authenticated", "username"]:
                st.session_state.pop(key, None)
            st.stop()

        response.raise_for_status()
        data = response.json().get("data", [])
        return pd.DataFrame(data)

    except requests.exceptions.ConnectionError:
        st.error("❌ Не удалось подключиться к API. Запущен ли FastAPI?")
        st.stop()
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ API ошибка: {e}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Ошибка: {e}")
        st.stop()


def login(username: str, password: str) -> bool:
    """
    Логин через ТВОЙ эндпоинт POST /api/login
    Тело: JSON {"username": ..., "password": ...}
    """
    api_url = get_api_url()
    try:
        response = requests.post(
            f"{api_url}/api/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state["jwt_token"] = data["access_token"]
            st.session_state["authenticated"] = True
            st.session_state["username"] = data["username"]
            st.session_state["user_id"] = data["user_id"]
            return True
        return False
    except requests.exceptions.ConnectionError:
        st.error("❌ API недоступен")
        return False
    except Exception as e:
        st.error(f"Ошибка: {e}")
        return False


def register(username: str, email: str, password: str,
             broker_token: str = "", account_id: str = "") -> bool:
    """Регистрация через POST /api/register"""
    api_url = get_api_url()
    try:
        response = requests.post(
            f"{api_url}/api/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "broker_token": broker_token,
                "account_id": account_id,
            },
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state["jwt_token"] = data["access_token"]
            st.session_state["authenticated"] = True
            st.session_state["username"] = data["username"]
            st.session_state["user_id"] = data["user_id"]
            return True
        elif response.status_code == 400:
            st.error("❌ Пользователь уже существует")
            return False
        return False
    except requests.exceptions.ConnectionError:
        st.error("❌ API недоступен")
        return False
    except Exception as e:
        st.error(f"Ошибка: {e}")
        return False
