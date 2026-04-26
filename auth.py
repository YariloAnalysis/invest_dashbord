# auth.py — с регистрацией
import streamlit as st
from db import login, register


def require_auth():
    """
    Вызывать в начале каждой страницы.
    Показывает логин/регистрацию если не авторизован.
    """
    if st.session_state.get("authenticated"):
        return

    st.markdown("## 🔐 Вход в систему")
    st.markdown("---")

    tab_login, tab_register = st.tabs(["🔑 Войти", "📝 Регистрация"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Логин", key="login_user")
            password = st.text_input("Пароль", type="password", key="login_pass")
            submitted = st.form_submit_button(
                "Войти", type="primary", use_container_width=True
            )

        if submitted:
            if username and password:
                if login(username, password):
                    st.rerun()
                else:
                    st.error("❌ Неверный логин или пароль")
            else:
                st.warning("Введите логин и пароль")

    with tab_register:
        with st.form("register_form"):
            reg_username = st.text_input("Логин", key="reg_user")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Пароль", type="password", key="reg_pass")
            reg_password2 = st.text_input(
                "Повторите пароль", type="password", key="reg_pass2"
            )
            st.markdown("---")
            st.markdown("**Опционально** (можно добавить позже):")
            reg_broker = st.text_input(
                "Токен брокера (Tinkoff)", key="reg_broker"
            )
            reg_account = st.text_input(
                "Account ID", key="reg_account"
            )
            reg_submitted = st.form_submit_button(
                "Зарегистрироваться", type="primary", use_container_width=True
            )

        if reg_submitted:
            if not reg_username or not reg_email or not reg_password:
                st.warning("Заполните все обязательные поля")
            elif reg_password != reg_password2:
                st.error("❌ Пароли не совпадают")
            else:
                if register(
                    reg_username, reg_email, reg_password,
                    reg_broker, reg_account
                ):
                    st.rerun()

    st.stop()


def logout_button():
    """Кнопка выхода в сайдбаре"""
    if st.session_state.get("authenticated"):
        with st.sidebar:
            st.markdown(f"👤 **{st.session_state.get('username', '')}**")
            if st.button("🚪 Выйти", use_container_width=True):
                # 1) Чистим session_state
                for key in ["jwt_token", "authenticated", "username", "user_id"]:
                    st.session_state.pop(key, None)
                # 2) ВАЖНО: чистим серверный кэш, чтобы данные
                #    не утекли следующему пользователю
                st.cache_data.clear()
                st.rerun()
def current_user_id() -> int | None:
    """Возвращает ID авторизованного пользователя или None."""
    return st.session_state.get("user_id")
