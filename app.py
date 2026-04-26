import streamlit as st
from pathlib import Path

st.set_page_config(
    layout="wide",
    page_title="Мой портфель",
    page_icon="📊",
)

from auth import require_auth
from components.navigation import render_sidebar, find_page_by_part

require_auth()
render_sidebar()


BASE_DIR = Path(__file__).parent


st.markdown(
    """
    <style>
        .main {
            background: #f8fafc;
        }

        .hero {
            padding: 42px 46px;
            border-radius: 30px;
            background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 45%, #2563eb 100%);
            color: white;
            box-shadow: 0 22px 50px rgba(15, 23, 42, 0.22);
            margin-bottom: 34px;
        }

        .hero h1 {
            font-size: 48px;
            line-height: 1.08;
            margin-bottom: 16px;
            font-weight: 800;
        }

        .hero p {
            font-size: 18px;
            line-height: 1.65;
            color: rgba(255,255,255,0.9);
            max-width: 850px;
        }

        .eyebrow {
            display: inline-block;
            padding: 8px 14px;
            border-radius: 999px;
            background: rgba(255,255,255,0.15);
            border: 1px solid rgba(255,255,255,0.25);
            font-size: 14px;
            margin-bottom: 20px;
        }

        .hero-visual {
            min-height: 290px;
            border-radius: 26px;
            background:
                radial-gradient(circle at 20% 20%, rgba(255,255,255,0.35), transparent 28%),
                radial-gradient(circle at 80% 30%, rgba(96,165,250,0.65), transparent 30%),
                radial-gradient(circle at 45% 75%, rgba(34,197,94,0.45), transparent 32%),
                rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.22);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 82px;
            box-shadow: inset 0 0 40px rgba(255,255,255,0.08);
        }

        .section-title {
            font-size: 30px;
            font-weight: 800;
            margin-top: 8px;
            margin-bottom: 6px;
            color: #0f172a;
        }

        .section-subtitle {
            color: #64748b;
            font-size: 16px;
            margin-bottom: 22px;
        }

        .card-icon {
            font-size: 44px;
            margin-bottom: 8px;
        }

        .info-box {
            padding: 24px 28px;
            border-radius: 24px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
            margin-bottom: 26px;
        }

        .info-box h3 {
            margin-top: 0;
            color: #0f172a;
        }

        .info-box p {
            color: #475569;
            line-height: 1.65;
            font-size: 16px;
        }

        section[data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #e2e8f0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


user_name = st.session_state.get("username", "инвестор")


left, right = st.columns([1.45, 0.85], gap="large")

with left:
    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">Ваш персональный инвестиционный центр</div>
            <h1>Добро пожаловать, {user_name} 👋</h1>
            <p>
                Этот дашборд помогает отслеживать состояние инвестиционного портфеля,
                анализировать структуру активов, изучать доходность и риски,
                а также принимать более осознанные инвестиционные решения.
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


st.markdown(
    """
    <div class="info-box">
        <h3>Что можно сделать в дашборде?</h3>
        <p>
            Перейдите в один из разделов ниже: посмотрите общую информацию по портфелю,
            изучите углублённую аналитику или воспользуйтесь инструментами оптимизации.
            Все страницы доступны через боковое меню слева.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown('<div class="section-title">Разделы дашборда</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-subtitle">Выберите нужный раздел для дальнейшей работы.</div>',
    unsafe_allow_html=True,
)


info_page = find_page_by_part("Основная информация")
analytics_page = find_page_by_part("Углубленная аналитика")
optimization_page = find_page_by_part("Оптимизация")


def render_nav_card(
    icon: str,
    title: str,
    description: str,
    page: str | None,
    button_label: str,
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
            "Общая картина портфеля: состав активов, доли инструментов, "
            "ключевые показатели и базовая информация."
        ),
        page=info_page,
        button_label="Открыть раздел",
    )

with col2:
    render_nav_card(
        icon="📈",
        title="Углубленная аналитика",
        description=(
            "Анализ динамики доходности, сравнение с индексом IMOEX," 
            "технический анализ ваших акций, "
            "оценка рисков по Монте-Карло."
        ),
        page=analytics_page,
        button_label="Перейти к аналитике",
    )

with col3:
    render_nav_card(
        icon="🚀",
        title="Оптимизация портфеля",
        description=(
            "Инструменты для поиска более эффективного распределения активов "
            "с учётом риска и доходности."
        ),
        page=optimization_page,
        button_label="Запустить оптимизацию",
    )
