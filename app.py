# app.py
import streamlit as st
from pathlib import Path

st.set_page_config(
    layout="wide",
    page_title="Мой портфель",
    page_icon="📊",
)

from auth import require_auth, logout_button

require_auth()


# =========================
# Пути к страницам
# =========================

BASE_DIR = Path(__file__).parent
PAGES_DIR = BASE_DIR / "pages"


def page_path(file_name: str):
    """
    Проверяет, существует ли страница в папке pages.
    Если существует — возвращает путь для st.page_link / st.switch_page.
    """
    page = PAGES_DIR / file_name
    if page.exists():
        return f"pages/{file_name}"
    return None


def find_page_by_part(name_part: str):
    """
    Ищет страницу по части названия.
    Удобно, если файл начинается с номера или emoji:
    например: 4_📈_Оптимизация_портфеля.py
    """
    for page in PAGES_DIR.glob("*.py"):
        if page.name == "__init__.py":
            continue

        if name_part.lower() in page.name.lower():
            return f"pages/{page.name}"

    return None


MAIN_PAGE = "app.py"
INFO_PAGE = page_path("Основная информация.py")
ANALYTICS_PAGE = page_path("Углубленная аналитика.py")
OPTIMIZATION_PAGE = find_page_by_part("Оптимизация")


# =========================
# CSS-стили
# =========================

st.markdown(
    """
    <style>
        .main {
            background: #f8fafc;
        }

        .hero {
            padding: 38px 42px;
            border-radius: 28px;
            background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 45%, #2563eb 100%);
            color: white;
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.20);
            margin-bottom: 28px;
        }

        .hero h1 {
            font-size: 46px;
            line-height: 1.05;
            margin-bottom: 14px;
            font-weight: 800;
        }

        .hero p {
            font-size: 18px;
            line-height: 1.6;
            color: rgba(255,255,255,0.88);
            max-width: 850px;
        }

        .eyebrow {
            display: inline-block;
            padding: 7px 12px;
            border-radius: 999px;
            background: rgba(255,255,255,0.15);
            border: 1px solid rgba(255,255,255,0.25);
            font-size: 14px;
            margin-bottom: 18px;
        }

        .hero-visual {
            min-height: 260px;
            border-radius: 24px;
            background:
                radial-gradient(circle at 20% 20%, rgba(255,255,255,0.35), transparent 28%),
                radial-gradient(circle at 80% 30%, rgba(96,165,250,0.65), transparent 30%),
                radial-gradient(circle at 45% 75%, rgba(34,197,94,0.45), transparent 32%),
                rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.22);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 80px;
            box-shadow: inset 0 0 40px rgba(255,255,255,0.08);
        }

        .section-title {
            font-size: 28px;
            font-weight: 800;
            margin-top: 10px;
            margin-bottom: 8px;
            color: #0f172a;
        }

        .section-subtitle {
            color: #64748b;
            font-size: 16px;
            margin-bottom: 20px;
        }

        .card-icon {
            font-size: 42px;
            margin-bottom: 8px;
        }

        .small-muted {
            color: #64748b;
            font-size: 14px;
        }

        div[data-testid="stMetric"] {
            background: white;
            padding: 18px 20px;
            border-radius: 20px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
        }

        section[data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #e2e8f0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# Sidebar-навигация
# =========================

with st.sidebar:
    st.markdown("## 📊 Мой портфель")
    st.caption("Инвестиционный дашборд")

    st.divider()

    st.page_link(MAIN_PAGE, label="Главная", icon="🏠")

    if INFO_PAGE:
        st.page_link(INFO_PAGE, label="Основная информация", icon="📌")

    if ANALYTICS_PAGE:
        st.page_link(ANALYTICS_PAGE, label="Углубленная аналитика", icon="📈")

    if OPTIMIZATION_PAGE:
        st.page_link(OPTIMIZATION_PAGE, label="Оптимизация портфеля", icon="🚀")

    st.divider()

    logout_button()


# =========================
# Hero-блок
# =========================

user_name = st.session_state.get("username", "инвестор")

left, right = st.columns([1.45, 0.85], gap="large")

with left:
    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">Ваш персональный инвестиционный центр</div>
            <h1>Добро пожаловать, {user_name} 👋</h1>
            <p>
                Здесь вы можете изучать структуру портфеля, анализировать доходность,
                контролировать риски и находить оптимальное распределение активов.
                Выберите нужный раздел ниже, чтобы продолжить работу.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    image_path = BASE_DIR / "data" / "dashboard_hero.png"

    if image_path.exists():
        st.image(str(image_path), use_container_width=True)
    else:
        st.markdown(
            """
            <div class="hero-visual">
                📊
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================
# Быстрая статистика
# =========================

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("Разделов", "3+", "для анализа")

with m2:
    st.metric("Фокус", "Портфель", "структура и риски")

with m3:
    st.metric("Инструменты", "Аналитика", "доходность / волатильность")

with m4:
    st.metric("Цель", "Оптимизация", "баланс риска и доходности")


st.markdown("<br>", unsafe_allow_html=True)


# =========================
# Навигационные карточки
# =========================

st.markdown('<div class="section-title">Выберите раздел</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-subtitle">Перейдите к нужной части инвестиционного дашборда.</div>',
    unsafe_allow_html=True,
)


def render_nav_card(
    icon: str,
    title: str,
    description: str,
    page: str | None,
    button_label: str,
    key: str,
):
    with st.container(border=True):
        st.markdown(f'<div class="card-icon">{icon}</div>', unsafe_allow_html=True)
        st.markdown(f"### {title}")
        st.write(description)

        if page:
            st.page_link(
                page,
                label=button_label,
                icon="➡️",
                use_container_width=True,
            )
        else:
            st.warning("Страница не найдена. Проверьте название файла в папке `pages`.")


col1, col2, col3 = st.columns(3, gap="large")

with col1:
    render_nav_card(
        icon="📌",
        title="Основная информация",
        description=(
            "Общая картина портфеля: состав активов, базовые показатели, "
            "стоимость, доли и ключевые параметры."
        ),
        page=INFO_PAGE,
        button_label="Открыть раздел",
        key="info",
    )

with col2:
    render_nav_card(
        icon="📈",
        title="Углубленная аналитика",
        description=(
            "Детальный анализ доходности, динамики, риска, просадок, "
            "волатильности и поведения портфеля."
        ),
        page=ANALYTICS_PAGE,
        button_label="Перейти к аналитике",
        key="analytics",
    )

with col3:
    render_nav_card(
        icon="🚀",
        title="Оптимизация портфеля",
        description=(
            "Инструменты для поиска более эффективного распределения активов "
            "и сравнения вариантов портфеля."
        ),
        page=OPTIMIZATION_PAGE,
        button_label="Запустить оптимизацию",
        key="optimization",
    )


# =========================
# Пример перехода к конкретному разделу
# =========================

st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("### ⚡ Быстрые действия")
    st.write(
        "Можно не просто открыть страницу, а передать другой странице информацию, "
        "какой именно раздел нужно показать."
    )

    quick_col1, quick_col2, quick_col3 = st.columns(3)

    with quick_col1:
        if ANALYTICS_PAGE:
            if st.button("Открыть раздел рисков", use_container_width=True):
                st.session_state["target_section"] = "risks"
                st.switch_page(ANALYTICS_PAGE)

    with quick_col2:
        if ANALYTICS_PAGE:
            if st.button("Открыть раздел доходности", use_container_width=True):
                st.session_state["target_section"] = "returns"
                st.switch_page(ANALYTICS_PAGE)

    with quick_col3:
        if OPTIMIZATION_PAGE:
            if st.button("Сразу к оптимизации", use_container_width=True):
                st.session_state["target_section"] = "optimization"
                st.switch_page(OPTIMIZATION_PAGE)
