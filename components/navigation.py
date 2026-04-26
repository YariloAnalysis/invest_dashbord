import streamlit as st
from pathlib import Path
from auth import logout_button


BASE_DIR = Path(__file__).resolve().parent.parent
PAGES_DIR = BASE_DIR / "pages"


def find_page_by_part(name_part: str):
    """
    Ищет страницу по части имени файла.
    Удобно, если у страницы есть emoji или номер в названии.
    Например:
    pages/📈 Оптимизация портфеля.py
    pages/1_Основная информация.py
    """
    if not PAGES_DIR.exists():
        return None

    for page in PAGES_DIR.glob("*.py"):
        if page.name == "__init__.py":
            continue

        if name_part.lower() in page.name.lower():
            return f"pages/{page.name}"

    return None


def hide_streamlit_default_navigation():
    """
    Дополнительная страховка.
    Даже если config.toml не сработает, CSS скроет стандартную навигацию Streamlit.
    """
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    hide_streamlit_default_navigation()

    main_page = "app.py"
    info_page = find_page_by_part("Основная информация")
    analytics_page = find_page_by_part("Углубленная аналитика")
    optimization_page = find_page_by_part("Оптимизация")

    with st.sidebar:
        st.markdown("## 📊 Мой портфель")
        st.caption("Инвестиционный дашборд")

        st.divider()

        st.page_link(
            main_page,
            label="Главная",
            icon="🏠",
            use_container_width=True,
        )

        if info_page:
            st.page_link(
                info_page,
                label="Основная информация",
                icon="📌",
                use_container_width=True,
            )

        if analytics_page:
            st.page_link(
                analytics_page,
                label="Углубленная аналитика",
                icon="📈",
                use_container_width=True,
            )

        if optimization_page:
            st.page_link(
                optimization_page,
                label="Оптимизация портфеля",
                icon="🚀",
                use_container_width=True,
            )

        st.divider()

        username = st.session_state.get("username")

        if username:
            st.markdown(f"### 👤 {username}")

        logout_button()
