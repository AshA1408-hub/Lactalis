import streamlit as st
import pandas as pd
import datetime
import requests
import base64
import json
import io

# Настройка страницы
st.set_page_config(
    page_title="Охрана труда и безопасность | ГК Лакталис",
    page_icon="🛡️",
    layout="centered"
)

# Кастомные стили
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        background-color: #0056b3;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        height: 45px;
    }
    .stButton>button:hover {
        background-color: #003d82;
        color: white;
    }
    .card {
        padding: 20px;
        border-radius: 10px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Инициализация сессии
if "step" not in st.session_state:
    st.session_state.step = "login"
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "score" not in st.session_state:
    st.session_state.score = 0

# Вопросы теста по охране труда (Лакталис)
QUESTIONS = [
    {
        "id": 1,
        "question": "Каковы основные обязанности работника в области охраны труда?",
        "options": [
            "Соблюдать требования охраны труда, правильно применять средства индивидуальной защиты",
            "Самостоятельно расследовать несчастные случаи на производстве",
            "Проводить вводный инструктаж для новых сотрудников",
            "Разрабатывать инструкции по охране труда"
        ],
        "answer": 0,
        "explanation": "Каждый работник обязан соблюдать требования охраны труда и использовать выданные СИЗ."
    },
    {
        "id": 2,
        "question": "Что необходимо сделать при обнаружении неисправности оборудования или защитных ограждений?",
        "options": [
            "Продолжить работу с повышенной осторожностью",
            "Попытаться самостоятельно отремонтировать оборудование",
            "Немедленно прекратить работу, отключить оборудование и сообщить руководителю",
            "Дождаться окончания смены и сообщить сменщику"
        ],
        "answer": 2,
        "explanation": "При любой неисправности работу необходимо остановить и поставить в известность руководство."
    },
    {
        "id": 3,
        "question": "Какие действия следует предпринять при возникновении пожара на рабочем месте?",
        "options": [
            "Спрятаться в подсобном помещении",
            "Покинуть здание через ближайший эвакуационный выход и сообщить руководству / пожарной охране",
            "Продолжать тушить пожар без средств защиты",
            "Забрать личные вещи и покинуть рабочее место"
        ],
        "answer": 1,
        "explanation": "Главный приоритет при пожаре — безопасная эвакуация людей и вызов экстренных служб."
    },
    {
        "id": 4,
        "question": "Каково назначение средств индивидуальной защиты (СИЗ)?",
        "options": [
            "Для улучшения внешнего вида сотрудника на производстве",
            "Для предотвращения или уменьшения воздействия вредных и опасных производственных факторов",
            "Для соблюдения дресс-кода компании",
            "Для удобства хранения личных инструментов"
        ],
        "answer": 1,
        "explanation": "СИЗ предназначены для защиты работника от вредных и опасных факторов."
    },
    {
        "id": 5,
        "question": "Кто допускается к выполнению работ с повышенной опасностью?",
        "options": [
            "Любой сотрудник по решению коллеги",
            "Сотрудники, прошедшие специальное обучение, инструктаж и медицинский осмотр",
            "Только руководители подразделений",
            "Сотрудники со стажем работы более 1 месяца"
        ],
        "answer": 1,
        "explanation": "Работы повышенной опасности требуют специального допуска, обучения и медосмотра."
    },
    {
        "id": 6,
        "question": "Что запрещается делать в производственных и складских помещениях?",
        "options": [
            "Курить в неустановленных местах, загромождать эвакуационные проходы",
            "Использовать сертифицированный ручной инструмент",
            "Соблюдать график работы",
            "Проводить влажную уборку рабочего места"
        ],
        "answer": 0,
        "explanation": "Загромождение проходов и курение вне отведенных мест грубо нарушают правила пожарной безопасности."
    },
    {
        "id": 7,
        "question": "Каков порядок действий при получении производственной травмы?",
        "options": [
            "Обратиться к врачу в конце недели",
            "Немедленно обратиться за первой помощью, уведомить непосредственного руководителя",
            "Промолчать, чтобы не портить статистику подразделения",
            "Уйти домой без уведомления руководства"
        ],
        "answer": 1,
        "explanation": "О любой травме необходимо незамедлительно сообщить руководству и получить первую помощь."
    },
    {
        "id": 8,
        "question": "Что означает знак безопасности в виде желтого треугольника с черной каймой и изображением молнии?",
        "options": [
            "Осторожно! Электрическое напряжение",
            "Вход воспрещен",
            "Место огнетушителя",
            "Медицинский пункт"
        ],
        "answer": 0,
        "explanation": "Желтый треугольник с символом молнии предупреждает об опасности поражения электрическим током."
    },
    {
        "id": 9,
        "question": "Какую первую помощь оказывают при попадании химических веществ в глаза?",
        "options": [
            "Протереть сухой салфеткой",
            "Промыть большим количеством чистой воды в течение не менее 15 минут и обратиться к врачу",
            "Закапать спиртовой раствор",
            "Ничего не предпринимать"
        ],
        "answer": 1,
        "explanation": "Химикаты из глаз необходимо немедленно и обильно смыть водой."
    },
    {
        "id": 10,
        "question": "Что относится к основным средствам пожаротушения?",
        "options": [
            "Огнетушители, пожарные краны, песок, кошма",
            "Обычная питьевая вода в бутылках",
            "Пластиковые пакеты и веники",
            "Вентиляционные шахты"
        ],
        "answer": 0,
        "explanation": "Огнетушители и пожарные щиты — это первичные средства тушения возгораний."
    },
    {
        "id": 11,
        "question": "Какие требования предъявляются к ручному инструменту (молотки, зубила, ключи)?",
        "options": [
            "Инструмент должен быть исправным, без трещин, скобов и заусенцев",
            "Разрешается использовать инструменты с самодельными деревянными ручками без фиксации",
            "Инструмент может быть любой степени износа",
            "Инструмент не подлежит проверке перед началом работ"
        ],
        "answer": 0,
        "explanation": "Инструмент с дефектами может стать причиной травмы."
    },
    {
        "id": 12,
        "question": "Какова главная цель системы управления охраной труда (СУОТ) на предприятии?",
        "options": [
            "Сохранение жизни и здоровья работников в процессе трудовой деятельности",
            "Увеличение объемов выпуска продукции любой ценой",
            "Снижение затрат на закупку средств защиты",
            "Формирование отчетов для сторонних организаций"
        ],
        "answer": 0,
        "explanation": "Главная цель СУОТ — защита жизни и здоровья каждого сотрудника."
    }
]

# Функция сохранения результатов в GitHub
def save_result_to_github(data):
    try:
        GITHUB_TOKEN = st.secrets["github"]["token"]
        REPO = st.secrets["github"]["repo"]
        PATH = "results.csv"
        
        url = f"https://api.github.com/repos/{REPO}/contents/{PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "vnd.github.v3+json"}
        
        # Получаем текущий файл
        response = requests.get(url, headers=headers)
        df = pd.DataFrame()
        sha = None
        
        if response.status_code == 200:
            file_data = response.json()
            sha = file_data["sha"]
            content = base64.b64decode(file_data["content"]).decode("utf-8")
            df = pd.read_csv(io.StringIO(content))
        
        new_row = pd.DataFrame([data])
        df = pd.concat([df, new_row], ignore_index=True)
        csv_content = df.to_csv(index=False)
        
        # Кодируем в base64
        encoded_content = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")
        
        data_payload = {
            "message": f"Add test result for {data['FIO']}",
            "content": encoded_content,
            "sha": sha
        }
        
        put_response = requests.put(url, headers=headers, data=json.dumps(data_payload))
        return put_response.status_code in [200, 201]
    except Exception as e:
        # Локальное резервное сохранение, если GitHub не настроен
        try:
            df_loc = pd.read_csv("results.csv")
        except:
            df_loc = pd.DataFrame(columns=["Timestamp", "FIO", "Position", "Department", "Score", "Total", "Status"])
        df_loc = pd.concat([df_loc, pd.DataFrame([data])], ignore_index=True)
        df_loc.to_csv("results.csv", index=False)
        return True

# Функция загрузки результатов для отчета
def load_results():
    try:
        GITHUB_TOKEN = st.secrets["github"]["token"]
        REPO = st.secrets["github"]["repo"]
        PATH = "results.csv"
        url = f"https://api.github.com/repos/{REPO}/contents/{PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "vnd.github.v3+json"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            file_data = response.json()
            content = base64.b64decode(file_data["content"]).decode("utf-8")
            return pd.read_csv(io.StringIO(content))
    except:
        pass
    
    # Фолбэк на локальный файл
    try:
        return pd.read_csv("results.csv")
    except:
        return pd.DataFrame(columns=["Timestamp", "FIO", "Position", "Department", "Score", "Total", "Status"])

# ==================== БОКОВАЯ ПАНЕЛЬ: АДМИН-ПАНЕЛЬ ====================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/2/2f/Lactalis_logo.svg", width=150)
    st.markdown("### 🔒 Администрирование")
    admin_pass = st.text_input("Пароль администратора", type="password")
    
    if admin_pass:
        try:
            correct_pass = st.secrets["admin"]["password"]
        except:
            correct_pass = "admin123"  # Дефолтный пароль, если не задан в secrets
            
        if admin_pass == correct_pass:
            st.success("Доступ разрешен")
            st.session_state.is_admin = True
        else:
            st.error("Неверный пароль")
            st.session_state.is_admin = False

# ==================== ОСНОВНОЙ ЭКРАН ====================

if st.session_state.get("is_admin", False):
    st.markdown("## 📊 Отчет администратора по результатам тестирования")
    st.markdown("Сводная аналитика и результаты проверки знаний сотрудников ГК Лакталис.")
    
    df_results = load_results()
    
    if not df_results.empty:
        # Метрики
        total_tests = len(df_results)
        passed_tests = len(df_results[df_results["Status"] == "Сдал"]) if "Status" in df_results.columns else total_tests
        avg_score = df_results["Score"].mean() if "Score" in df_results.columns else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Всего сдали тестов", total_tests)
        col2.metric("Успешно сдали", f"{passed_tests} ({int(passed_tests/total_tests*100) if total_tests > 0 else 0}%)")
        col3.metric("Средний балл", f"{avg_score:.1f} / {len(QUESTIONS)}")
        
        st.markdown("---")
        
        # Фильтры
        search_query = st.text_input("🔍 Поиск по ФИО или должности")
        if search_query:
            df_filtered = df_results[
                df_results["FIO"].str.contains(search_query, case=False, na=False) |
                df_results["Position"].str.contains(search_query, case=False, na=False)
            ]
        else:
            df_filtered = df_results
            
        st.dataframe(df_filtered, use_container_width=True)
        
        # Кнопка скачивания
        csv = df_results.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Скачать полный отчет в CSV",
            data=csv,
            file_name=f"lactalis_safety_report_{datetime.date.today()}.csv",
            mime="text/csv"
        )
    else:
        st.info("Пока нет сохраненных результатов тестирования.")

else:
    # Интерфейс прохождения теста для сотрудника
    st.markdown("<h1 style='text-align: center; color: #003d82;'>🛡️ Охрана труда и безопасность</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #555;'>Группа компаний «Лакталис»</h3>", unsafe_allow_html=True)
    st.markdown("---")

    if st.session_state.step == "login":
        with st.form("login_form"):
            st.markdown("### Введите ваши данные для начала тестирования:")
            fio = st.text_input("ФИО (Полностью)*")
            position = st.text_input("Должность*")
            department = st.selectbox("Подразделение / Отдел", [
                "Производство",
                "Склад и логистика",
                "Отдел качества",
                "Администрация / Офис",
                "Техническая служба / АХО"
            ])
            
            submitted = st.form_submit_button("Начать тест")
            if submitted:
                if fio.strip() and position.strip():
                    st.session_state.fio = fio.strip()
                    st.session_state.position = position.strip()
                    st.session_state.department = department
                    st.session_state.step = "quiz"
                    st.rerun()
                else:
                    st.warning("Пожалуйста, заполните ФИО и должность.")

    elif st.session_state.step == "quiz":
        st.markdown(f"**Сотрудник:** {st.session_state.fio} | **Должность:** {st.session_state.position}")
        
        # Прогресс бар
        progress = len(st.session_state.answers) / len(QUESTIONS)
        st.progress(progress)
        
        all_answered = True
        
        for idx, q in enumerate(QUESTIONS):
            st.markdown(f"#### Вопрос {idx+1} из {len(QUESTIONS)}")
            st.write(q["question"])
            
            ans = st.radio(
                f"Выберите вариант ответа:",
                options=q["options"],
                key=f"q_{idx}",
                index=st.session_state.answers.get(idx, None)
            )
            
            if ans is not None:
                st.session_state.answers[idx] = q["options"].index(ans)
            else:
                all_answered = False
            st.markdown("---")
            
        if st.button("Завершить и отправить результаты"):
            if len(st.session_state.answers) < len(QUESTIONS):
                st.error("Пожалуйста, ответьте на все вопросы перед отправкой!")
            else:
                # Подсчет баллов
                score = 0
                for idx, q in enumerate(QUESTIONS):
                    if st.session_state.answers.get(idx) == q["answer"]:
                        score += 1
                
                st.session_state.score = score
                status = "Сдал" if score >= int(len(QUESTIONS) * 0.8) else "Не сдал"
                
                result_data = {
                    "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "FIO": st.session_state.fio,
                    "Position": st.session_state.position,
                    "Department": st.session_state.department,
                    "Score": score,
                    "Total": len(QUESTIONS),
                    "Status": status
                }
                
                with st.spinner("Сохранение результатов..."):
                    save_result_to_github(result_data)
                
                st.session_state.step = "result"
                st.rerun()

    elif st.session_state.step == "result":
        score = st.session_state.score
        total = len(QUESTIONS)
        percent = int((score / total) * 100)
        
        st.markdown(f"### Результаты тестирования")
        st.markdown(f"**Сотрудник:** {st.session_state.fio}")
        st.markdown(f"**Должность:** {st.session_state.position}")
        
        if percent >= 80:
            st.success(f"🎉 Тест успешно пройден! Ваш результат: {score}/{total} ({percent}%)")
        else:
            st.error(f"⚠️ Тест не пройден. Ваш результат: {score}/{total} ({percent}%). Требуется результат от 80%.")
            
        st.markdown("---")
        st.markdown("#### Разбор вопросов и правильные ответы:")
        for idx, q in enumerate(QUESTIONS):
            user_ans_idx = st.session_state.answers.get(idx)
            is_correct = (user_ans_idx == q["answer"])
            
            icon = "✅" if is_correct else "❌"
            st.markdown(f"**{idx+1}. {q['question']}** {icon}")
            st.write(f"Ваш ответ: {q['options'][user_ans_idx] if user_ans_idx is not None else 'Нет ответа'}")
            if not is_correct:
                st.write(f"Правильный ответ: **{q['options'][q['answer']]}**")
            st.info(f"💡 {q['explanation']}")
            st.markdown("---")
            
        if st.button("Пройти тест заново"):
            st.session_state.answers = {}
            st.session_state.score = 0
            st.session_state.step = "login"
            st.rerun()
