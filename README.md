# 📈 Инвестиционный аналитический дашборд (T-Invest API)

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/postgresql-4169e1?style=for-the-badge&logo=postgresql&logoColor=white)
![Apache Airflow](https://img.shields.io/badge/Airflow-017CEE?style=for-the-badge&logo=Apache%20Airflow&logoColor=white)
![Tailscale](https://img.shields.io/badge/Tailscale-FFFFFF?style=for-the-badge&logo=Tailscale&logoColor=black)

> **Внимание:** В данном репозитории представлен **только код Frontend-части (Streamlit)**. 
> Бэкенд, база данных и ETL-пайплайны (Airflow) развернуты на приватном домашнем сервере из соображений безопасности инфраструктуры. 

## 📝 Описание проекта

Проект представляет собой комплексный аналитический центр для управления инвестиционным портфелем. Данные подтягиваются **исключительно через официальный T-Invest API**. 

Дашборд позволяет не только отслеживать текущее состояние активов, но и применять методы количественного анализа (Quantitative Analysis) для оценки рисков и оптимизации доходности. Проект демонстрирует навыки построения полного цикла работы с данными: от сбора по расписанию до сложной визуализации.

## 🏗 Архитектура и Data Flow

Проект разделен на публичную (облачную) и приватную (локальную) части:

1. **ETL Process (Приватный сервер):** **Apache Airflow** по расписанию (DAGs) обращается к **T-Invest API**, собирает исторические данные по котировкам, дивидендам, купонам и сделкам пользователя, трансформирует их и загружает в **PostgreSQL**.
   <img width="1815" height="926" alt="image" src="https://github.com/user-attachments/assets/69779822-69fd-4699-86c2-c128d485a005" />
   <img width="1755" height="522" alt="image" src="https://github.com/user-attachments/assets/2ddd8944-ffbe-4c00-835a-3c2c13690c35" />


2. **Backend (Приватный сервер):** **FastAPI** выступает в роли REST API интерфейса, который забирает данные из БД, производит тяжелые математические расчеты (симуляции Монте-Карло, расчет границы эффективности Марковица) и отдает готовые JSON.
  <img width="1813" height="898" alt="image" src="https://github.com/user-attachments/assets/17508cdf-1b89-4a12-addb-e309f7c305f8" />
  <img width="1763" height="848" alt="szIUFoga3mc2hcbapbGMmuqCRwvv9mvoRp6rx8gRtRmGEJqR3O0XKpGQcPNrvPxlTiphC078q2bpUjnHQvAmBJX0" src="https://github.com/user-attachments/assets/ea02a20d-d292-4db4-96f6-cfedfe155b94" />
3. **Tunneling:** Для безопасного доступа извне к локальному FastAPI используется **Tailscale Funnel**, который пробрасывает публичный HTTPS-эндпоинт к локальному порту.
4. **Frontend (Публичный):** **Streamlit** приложение (развернуто на Streamlit Cloud) обращается к FastAPI через Tailscale-ссылку, отрисовывая дашборды с помощью Plotly/Pandas.

## 🚀 Основной функционал и визуализация

### 1. Главная страница: Состояние портфеля
Общая сводка по активам, их долям (акции, облигации, золото) и топы лучших/худших активов за период.
> *<img width="1920" height="996" alt="image" src="https://github.com/user-attachments/assets/1c3306bf-2258-45ff-818f-bc80c23a47fc" />

### 2. Углубленная аналитика и бенчмаркинг
Сравнение накопленной доходности портфеля с рынком (индекс Мосбиржи - IMOEX). Анализ доходности по месяцам (Heatmap) и детализированный календарь ожидаемых выплат (купоны и дивиденды) с разбивкой по эмитентам.
> *<img width="1394" height="952" alt="image" src="https://github.com/user-attachments/assets/98d12b47-da31-452d-899e-9af259df6e3d" />

> *<img width="1288" height="540" alt="image" src="https://github.com/user-attachments/assets/00818b06-d6aa-42bf-ae87-224f624c8d40" />

> *<img width="1470" height="867" alt="image" src="https://github.com/user-attachments/assets/17bec8fe-6c3c-4661-95b4-2f8eb0f1c3c8" />
*


### 3. Технический анализ и динамика
Отображение графиков японских свечей для выбранных бумаг с наложением технических индикаторов (EMA, Bollinger Bands). Динамика стоимости портфеля относительно вложенных средств с линией тренда.
<img width="1309" height="1018" alt="image" src="https://github.com/user-attachments/assets/2811221f-6679-4c79-88b5-4fe5a8e0c99b" />
<img width="1375" height="768" alt="image" src="https://github.com/user-attachments/assets/c5fc8edb-8bfe-47b5-9b66-9c68cb5e866f" />


### 4. Оценка рисков (Моделирование Монте-Карло)
Расчет метрики Value at Risk (VaR 95%) на основе 10 000 симуляций методом Монте-Карло. Показывает вероятный максимальный однодневный убыток по активу.
<img width="1437" height="962" alt="image" src="https://github.com/user-attachments/assets/0ea70f85-e66d-4dbe-b581-4235359a319e" />


### 5. Оптимизация портфеля (Теория Марковица)
Построение границы эффективности (Efficient Frontier). Генерация случайных портфелей для поиска оптимальных весов активов по критериям:
* **Max Sharpe** (Максимальный коэффициент Шарпа)
* **Min Variance** (Минимальная волатильность/риск)
<img width="1458" height="940" alt="image" src="https://github.com/user-attachments/assets/ab941959-e085-4ad0-aca5-11d4cc6257dc" />
<img width="1469" height="789" alt="image" src="https://github.com/user-attachments/assets/13998a52-d6fe-4f36-90f8-6654cd101ac6" />


## 🛠 Технологический стек

* **Сбор и оркестрация данных (Data Engineering):** Apache Airflow, T-Invest API
* **База данных:** PostgreSQL
* **Бэкенд:** Python, FastAPI, Pydantic, SQLAlchemy, NumPy, SciPy (для фин. математики)
* **Сеть и Деплой:** Tailscale Funnel (Secure TCP tunneling), Docker
* **Фронтенд и Визуализация:** Streamlit, Streamlit Cloud, Plotly, Pandas

