from datetime import datetime
import base64
import requests
import streamlit as st
import pandas as pd
import streamlit as st
from github import Github

# --- БЛОК АДМИНИСТРАТОРА В БОКОВОЙ ПАНЕЛИ ---
st.sidebar.markdown('---')
st.sidebar.subheader('👨‍💻 Панель руководителя')

# Проверка, введен ли уже пароль
if 'admin_logged_in' not in st.session_state:
  st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
  password_input = st.sidebar.text_input('Введите пароль', type='password')
  if st.sidebar.button('Войти'):
    # Читаем пароль из секретов Streamlit
    admin_pass = (
        st.secrets['admin']['password']
        if 'admin' in st.secrets and 'password' in st.secrets['admin']
        else '12345'
    )
    if password_input == admin_pass:
      st.session_state.admin_logged_in = True
      st.sidebar.success('Успешный вход!')
      st.rerun()
    else:
      st.sidebar.error('Неверный пароль')
else:
  if st.sidebar.button('Выйти из кабинета'):
    st.session_state.admin_logged_in = False
    st.rerun()

  st.sidebar.success('Доступ разрешен')

# --- ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ ДЛЯ АДМИНА ---
if st.session_state.admin_logged_in:
  st.header('📊 Сводная таблица результатов тестирования')

  try:
    # Подключаемся к GitHub и скачиваем актуальный results.csv
    token = st.secrets['github']['token']
    repo_name = st.secrets['github']['repo']

    g = Github(token)
    repo = g.get_repo(repo_name)
    file_content = repo.get_contents('results.csv')
    data = file_content.decoded_content.decode('utf-8')

    # Превращаем в DataFrame
    from io import StringIO

    df = pd.read_csv(StringIO(data))

    # Красивые фильтры и поисковая строка
    search_query = st.text_input('🔍 Поиск по ФИО или должности')
    if search_query:
      df = df[
          df.astype(str)
          .apply(lambda row: row.str.contains(search_query, case=False).any(),
                 axis=1)
      ]

    # Показываем интерактивную таблицу
    st.dataframe(df, use_container_width=True)

    # Кнопка для скачивания отчета
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label='📥 Скачать отчет в формате CSV (Excel)',
        data=csv_data,
        file_name='results_report.csv',
        mime='text/csv',
    )

  except Exception as e:
    st.info(
        'Файл результатов (`results.csv`) пока пуст или еще не создан. Как'
        ' только кто-то пройдет тест, здесь появится таблица.'
    )

# --- СОХРАНЕНИЕ В CSV НА GITHUB ---
def save_to_github(row_data):
  try:
    token = st.secrets["github"]["token"]
    repo = st.secrets["github"]["repo"]
    path = "results.csv"

    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    # 1. Получаем текущий файл из репозитория (если он есть)
    response = requests.get(url, headers=headers)
    csv_content = ""
    sha = None

    if response.status_code == 200:
      file_data = response.json()
      sha = file_data["sha"]
      csv_content = base64.b64decode(file_data["content"]).decode("utf-8")
    else:
      # Если файла еще нет, создаем шапку таблицы
      csv_content = (
          "Timestamp,Имя,Должность,Попытка,Правильных"
          " ответов,Всего,Процент,Статус\n"
      )

    # 2. Добавляем новую строчку
    new_row_str = ",".join([str(val) for val in row_data]) + "\n"
    csv_content += new_row_str

    # 3. Кодируем и отправляем обновленный файл обратно на GitHub
    content_encoded = base64.b64encode(csv_content.encode("utf-8")).decode(
        "utf-8"
    )
    data = {
        "message": "Update test results",
        "content": content_encoded,
        "sha": sha,  # Если sha равен None, файл создастся автоматически
    }

    put_response = requests.put(url, headers=headers, json=data)
    return put_response.status_code in [200, 201]
  except Exception:
    return False


QUESTIONS = [
    {
        "question": (
            "Когда началась история компании «Лакталис» и какое событие"
            " положило ей начало?"
        ),
        "options": [
            (
                "19 октября 1933 года, когда Андрей Бенье купил молоко у фермеров"
                " и приготовил первые 17 головок камамбера"
            ),
            "В 1997 году с запуска производства в России",
            (
                "15 августа 1950 года после открытия первого крупного завода в"
                " Лавале"
            ),
            "1 января 1930 года с выпуска плавленых сыров",
        ],
        "correct": 0,
        "explanation": (
            "История компании берет свое начало 19 октября 1933 года, когда"
            " основатель Андрей Бенье приобрел молоко у фермеров в пригороде"
            " Лаваля и изготовил первые 17 головок камамбера «Лепетит Лаваёс»,"
            " что и заложило основу семейного молочного бизнеса."
        ),
    },
    {
        "question": (
            "На какие три групповых документа по безопасности опирается работа"
            " сотрудников компании?"
        ),
        "options": [
            (
                "Трудовой кодекс, должностная инструкция и правила внутреннего"
                " распорядка"
            ),
            (
                "Политика здоровья и безопасности, Устав здоровья и"
                " безопасности, а также 12 золотых правил"
            ),
            (
                "Инструкция по пожарной безопасности, СУОД и правила ОПР"
            ),
            "Паспорт безопасности, план эвакуации и наряд-допуск",
        ],
        "correct": 1,
        "explanation": (
            "Поскольку забота о здоровье и безопасности персонала — это"
            " фундамент компании, вся деятельность регламентируется тремя"
            " ключевыми документами: Политикой здоровья и безопасности,"
            " Уставом здоровья и безопасности и 12 золотыми правилами."
        ),
    },
    {
        "question": (
            "Что представляет собой система управления охраной труда (СУОД)?"
        ),
        "options": [
            (
                "Комплекс правил, обязательных для работодателя, направленных"
                " на снижение травматизма и профзаболеваний"
            ),
            (
                "Набор рекомендаций для сотрудников по прохождению"
                " медицинской комиссии"
            ),
            (
                "Список штрафных санкций за нарушение правил безопасности"
            ),
            (
                "Документ, регламентирующий исключительно работу с"
                " электрооборудованием"
            ),
        ],
        "correct": 0,
        "explanation": (
            "СУОД представляет собой комплекс обязательных для работодателя норм"
            " и правил, целью которых является систематическое снижение уровня"
            " производственного травматизма и предупреждение профессиональных"
            " заболеваний."
        ),
    },
    {
        "question": (
            "Кто проводит вводный инструктаж по охране труда и в какой момент?"
        ),
        "options": [
            "Непосредственный руководитель перед началом каждой смены",
            (
                "Специалист по охране труда перед началом выполнения"
                " трудовых обязанностей"
            ),
            "Начальник производства после прохождения стажировки",
            "Представитель профсоюза один раз в три года",
        ],
        "correct": 1,
        "explanation": (
            "Вводный инструктаж в обязательном порядке проводится профильным"
            " специалистом по охране труда строго перед началом выполнения"
            " сотрудником его непосредственных трудовых обязанностей на"
            " предприятии."
        ),
    },
    {
        "question": (
            "Какова периодичность проведения повторного инструктажа на рабочем"
            " месте?"
        ),
        "options": [
            "Каждую неделю",
            "Один раз в месяц",
            "Раз в три или шесть месяцев",
            "Раз в три года",
        ],
        "correct": 2,
        "explanation": (
            "Повторный инструктаж на рабочем месте проводит непосредственный"
            " руководитель с установленной периодичностью — один раз в три или"
            " шесть месяцев для поддержания бдительности и проверки"
            " актуальных знаний."
        ),
    },
    {
        "question": (
            "Сколько смен может длиться стажировка под руководством опытного"
            " специалиста перед допуском к самостоятельной работе?"
        ),
        "options": [
            "Ровно 1 смену",
            "От 2 до 19 смен",
            "Строго 30 смен",
            "Стажировка в компании не предусмотрена",
        ],
        "correct": 1,
        "explanation": (
            "Практическая стажировка под надежным руководством опытного"
            " наставника длится от 2 до 19 смен. Ее главная задача — отработать"
            " все безопасные навыки на практике перед получением официального"
            " допуска."
        ),
    },
    {
        "question": (
            "Что такое несчастный случай согласно материалам инструктажа?"
        ),
        "options": [
            "Любая царапина или ссадина на производстве",
            "Травмы с потерей рабочего времени более 24 часов",
            "Ситуация, повлекшая поломку оборудования без пострадавших",
            "Опоздание сотрудника на рабочее место более чем на сутки",
        ],
        "correct": 1,
        "explanation": (
            "По внутренним стандартам классификации, несчастным случаем"
            " признается инцидент, повлекший за собой получение травм и потерю"
            " рабочего времени сотрудника на срок более 24 часов (в отличие от"
            " легких микротравм)."
        ),
    },
    {
        "question": (
            "Какой телефон экстренной службы необходимо запомнить сотрудникам?"
        ),
        "options": ["101", "112", "122", "911"],
        "correct": 1,
        "explanation": (
            "Единым универсальным номером телефона для экстренного вызова"
            " оперативных служб при возникновении нештатных ситуаций или"
            " аварий является 112."
        ),
    },
    {
        "question": (
            "Какие требования предъявляются к внешнему виду и личным вещам при"
            " допуске в пищевое производство?"
        ),
        "options": [
            (
                "Разрешено носить часы и кольца, если они закреплены пластырем"
            ),
            (
                "Запрещено наличие накладных ресниц, длинных ногтей, украшений"
                " (колец, серег, браслетов), часов, а также вход в линзах (нужно"
                " надеть обычные очки)"
            ),
            (
                "Допускается использование любых аксессуаров при условии"
                " обработки антисептиком"
            ),
            (
                "Ограничения касаются только парфюма, остальные украшения"
                " разрешены"
            ),
        ],
        "correct": 1,
        "explanation": (
            "Требования пищевой безопасности строги: запрещены накладные"
            " ресницы, длинные ногти, сильный парфюм, любые ювелирные изделия"
            " (кольца, часы, серьги, цепочки) и контактные линзы (их"
            " обязательно нужно заменить на обычные очки)."
        ),
    },
    {
        "question": (
            "Какой тип огнетушителя является наиболее универсальным и"
            " оптимальным для пищевых производств?"
        ),
        "options": [
            "Порошковый",
            "Углекислотный",
            "Воздушно-эмульсионный",
            "Пенный химический",
        ],
        "correct": 2,
        "explanation": (
            "Воздушно-эмульсионный огнетушитель признан наиболее эффективным и"
            " безопасным: он отлично справляется с твердыми материалами и"
            " жидкостями, не вредит электрооборудованию, не выделяет"
            " токсичных веществ и идеально подходит для пищевых зон."
        ),
    },
    {
        "question": (
            "Что необходимо сделать в первую очередь при обнаружении"
            " предмета, похожего на взрывное устройство?"
        ),
        "options": [
            "Самостоятельно перенести его в безопасное место",
            (
                "Использовать радиостанцию или телефон рядом с целью"
                " оперативного оповещения"
            ),
            (
                "Категорически не приближаясь к находке, немедленно сообщить"
                " руководителю или специалисту по охране труда, избегая"
                " использования радиосвязи и телефонов поблизости"
            ),
            "Попытаться самостоятельно обезвредить предмет подручными средствами",
        ],
        "correct": 2,
        "explanation": (
            "При обнаружении подозрительных предметов ни в коем случае нельзя"
            " приближаться к ним, трогать их или пользоваться"
            " радиостанциями/телефонами в непосредственной близости. Следует"
            " безопасно удалиться и сразу проинформировать руководство или"
            " службу охраны труда."
        ),
    },
    {
        "question": (
            "Какое главное правило безопасности упоминается в самом конце"
            " инструктажа?"
        ),
        "options": [
            "«План по производству должен быть выполнен любой ценой»",
            (
                "«Ни одна работа не является настолько важной и срочной, чтобы"
                " выполнять ее небезопасно»"
            ),
            "«Всегда работайте быстрее, чтобы избежать задержек»",
            "«Самостоятельно устраняйте любые неполадки оборудования»",
        ],
        "correct": 1,
        "explanation": (
            "Это ключевой жизненный принцип компании: никакие производственные"
            " задачи, сроки или срочные планы не могут быть важнее человеческой"
            " жизни и здоровья. Безопасность всегда стоит на первом месте."
        ),
    },
]

st.set_page_config(
    page_title="Здоровье и безопасность — Лакталис",
    page_icon="🛡️",
    layout="centered",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0088cc !important;
        color: #ffffff !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    header {visibility: hidden;}
    .card-container {
        background-color: #ffffff;
        padding: 35px;
        border-radius: 16px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        color: #1e293b !important;
        margin-top: 15px;
        margin-bottom: 20px;
    }
    .card-container, .card-container p, .card-container span, .card-container label, .card-container div, .card-container h1, .card-container h2, .card-container h3, .card-container h4, .stRadio label {
        color: #1e293b !important;
    }
    .stMarkdown p {
        color: rgba(255, 255, 255, 0.95) !important;
        font-size: 16px;
    }
    input[type="text"], input {
        background-color: #f8fafc !important;
        color: #1e293b !important;
        -webkit-text-fill-color: #1e293b !important;
        border: 2px solid #cbd5e1 !important;
        border-radius: 10px !important;
        font-size: 16px !important;
    }
    .step-badge {
        display: inline-block;
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 8px 18px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 18px;
        box-shadow: 0 4px 10px rgba(245, 158, 11, 0.3);
        margin-bottom: 10px;
    }
    .stButton>button {
        background: linear-gradient(135deg, #f59e0b 0%, #e11d48 100%) !important;
        color: white !important;
        border-radius: 12px;
        padding: 12px 28px;
        font-weight: 700;
        border: none !important;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4);
        transition: all 0.3s ease;
        width: 100%;
        font-size: 16px;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #d97706 0%, #be123c 100%) !important;
        box-shadow: 0 6px 20px rgba(245, 158, 11, 0.6);
        transform: translateY(-2px);
    }
    [data-testid="stSidebar"] {
        background-color: #0072b1 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #f59e0b, #10b981);
        border-radius: 10px;
    }
    .exp-correct {
        background-color: #f0fdf4 !important;
        border-left: 6px solid #22c55e;
        padding: 16px;
        border-radius: 10px;
        color: #166534 !important;
        margin-top: 15px;
        font-size: 15px;
    }
    .exp-wrong {
        background-color: #fef2f2 !important;
        border-left: 6px solid #ef4444;
        padding: 16px;
        border-radius: 10px;
        color: #991b1b !important;
        margin-top: 15px;
        font-size: 15px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

if "step" not in st.session_state:
  st.session_state.step = "register"
if "name" not in st.session_state:
  st.session_state.name = ""
if "position" not in st.session_state:
  st.session_state.position = ""
if "attempt" not in st.session_state:
  st.session_state.attempt = 1
if "current_q" not in st.session_state:
  st.session_state.current_q = 0
if "score" not in st.session_state:
  st.session_state.score = 0
if "selected_option" not in st.session_state:
  st.session_state.selected_option = None
if "answered" not in st.session_state:
  st.session_state.answered = False

# --- ШАГ 1: РЕГИСТРАЦИЯ ---
if st.session_state.step == "register":
  st.markdown(
      "<div style='text-align: center; padding: 10px 0 0 0;'><div"
      " class='step-badge'>LACTALIS</div><h1"
      " style='color:white;font-weight:800;letter-spacing:-0.5px;margin-bottom:5px;'>ЗДОРОВЬЕ"
      " И БЕЗОПАСНОСТЬ</h1><p>Модуль интерактивной проверки знаний</p></div>",
      unsafe_allow_html=True,
  )

  st.markdown('<div class="card-container">', unsafe_allow_html=True)
  st.markdown(
      "<h3>📝 Регистрация сотрудника</h3><p"
      " style='margin-bottom:20px;color:#64748b;'>Представьтесь, чтобы"
      " зафиксировать прохождение теста в журнале.</p>",
      unsafe_allow_html=True,
  )

  with st.form("reg_form"):
    name_input = st.text_input(
        "ФИО (Фамилия Имя Отчество):",
        value=st.session_state.name,
        placeholder="Иванов Иван Иванович",
    )
    position_input = st.text_input(
        "Должность:",
        value=st.session_state.position,
        placeholder="Оператор / Инженер / Специалист",
    )
    submitted = st.form_submit_button("Начать тестирование ➔")

    if submitted:
      if not name_input.strip() or not position_input.strip():
        st.error("⚠️ Пожалуйста, заполните оба поля: ФИО и должность.")
      else:
        st.session_state.name = name_input.strip()
        st.session_state.position = position_input.strip()
        st.session_state.step = "quiz"
        st.session_state.current_q = 0
        st.session_state.score = 0
        st.session_state.answered = False
        st.rerun()
  st.markdown("</div>", unsafe_allow_html=True)

# --- ШАГ 2: ПРОХОЖДЕНИЕ ТЕСТА ---
elif st.session_state.step == "quiz":
  with st.sidebar:
    st.markdown("### 👤 Ваш профиль")
    st.markdown(f"**ФИО:** {st.session_state.name}")
    st.markdown(f"**Должность:** {st.session_state.position}")
    st.markdown(f"**Попытка:** №{st.session_state.attempt}")
    st.markdown("---")
    st.info(
        "💡 Для успешной сдачи требуется набрать не менее **80%** правильных"
        " ответов."
    )

  q_idx = st.session_state.current_q
  total_q = len(QUESTIONS)
  q_data = QUESTIONS[q_idx]

  st.markdown(
      f"<div class='step-badge'>ВОПРОС {q_idx + 1} ИЗ"
      f" {total_q}</div>",
      unsafe_allow_html=True,
  )
  st.progress((q_idx) / total_q)

  st.markdown('<div class="card-container">', unsafe_allow_html=True)
  st.markdown(
      f"<h3 style='margin-bottom: 20px; color: #1e293b !important;'>"
      f"{q_data['question']}</h3>",
      unsafe_allow_html=True,
  )

  options = q_data["options"]
  selected = st.radio(
      "Выберите вариант ответа:",
      options,
      key=f"q_{q_idx}",
      index=(
          None
          if not st.session_state.answered
          else st.session_state.selected_option
      ),
  )

  if not st.session_state.answered:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Подтвердить ответ"):
      if selected is None:
        st.warning("⚠️ Выберите вариант ответа перед подтверждением.")
      else:
        chosen_index = options.index(selected)
        st.session_state.selected_option = chosen_index
        st.session_state.answered = True
        if chosen_index == q_data["correct"]:
          st.session_state.score += 1
        st.rerun()
  else:
    chosen_index = st.session_state.selected_option
    is_correct = chosen_index == q_data["correct"]

    if is_correct:
      st.markdown(
          f'<div class="exp-correct"><strong>✅'
          f' Верно!</strong><br>{q_data["explanation"]}</div>',
          unsafe_allow_html=True,
      )
    else:
      correct_text = options[q_data["correct"]]
      st.markdown(
          f'<div class="exp-wrong"><strong>❌ Неверно.</strong><br>Правильный'
          f' ответ: <em>{correct_text}</em><br><br>Справка:'
          f' {q_data["explanation"]}</div>',
          unsafe_allow_html=True,
      )

    st.markdown("<br>", unsafe_allow_html=True)
    btn_label = (
        "Следующий вопрос ➔"
        if q_idx < total_q - 1
        else "Посмотреть результаты ➔"
    )
    if st.button(btn_label):
      st.session_state.answered = False
      st.session_state.selected_option = None
      if q_idx < total_q - 1:
        st.session_state.current_q += 1
      else:
        total = len(QUESTIONS)
        score = st.session_state.score
        percent = (score / total) * 100
        status = "Сдал" if percent >= 80 else "Не сдал"

        row_data = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            st.session_state.name,
            st.session_state.position,
            str(st.session_state.attempt),
            str(score),
            str(total),
            f"{percent:.0f}%",
            status,
        ]

        # Запись в GitHub репозиторий
        save_to_github(row_data)

        st.session_state.step = "result"
      st.rerun()
  st.markdown("</div>", unsafe_allow_html=True)

# --- ШАГ 3: РЕЗУЛЬТАТЫ ---
elif st.session_state.step == "result":
  total = len(QUESTIONS)
  score = st.session_state.score
  percent = (score / total) * 100

  st.markdown(
      "<div class='step-badge'>ИТОГИ ТЕСТИРОВАНИЯ</div>",
      unsafe_allow_html=True,
  )
  st.markdown('<div class="card-container">', unsafe_allow_html=True)
  st.markdown(
      f"**Сотрудник:** {st.session_state.name} ({st.session_state.position})"
  )
  st.markdown(f"**Попытка:** №{st.session_state.attempt}")

  color_code = "#10b981" if percent >= 80 else "#ef4444"
  st.markdown(
      f"<h1 style='font-size: 52px; color: {color_code}; margin: 15px"
      f" 0;'>{percent:.0f}%</h1>",
      unsafe_allow_html=True,
  )
  st.markdown(
      f"<p style='font-size: 18px;'>Правильных ответов: <strong>{score} из"
      f" {total}</strong></p>",
      unsafe_allow_html=True,
  )

  st.info(
      "📊 Результат автоматически занесен в общую сводную таблицу"
      " результатов на GitHub."
  )

  if percent >= 80:
    st.success(
        "🎉 Поздравляем! Вы успешно прошли инструктаж. Результат сохранен в"
        " систему."
    )
    st.balloons()
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Завершить сеанс"):
      st.session_state.clear()
      st.rerun()
  else:
    st.error(
        "⚠️ Тест не пройден. Требуется набрать от 80% (минимум"
        f" {int(total * 0.8)} правильных ответов)."
    )
    st.markdown("Изучите материал еще раз и повторите попытку.")
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Пройти тест заново 🔄"):
      st.session_state.attempt += 1
      st.session_state.current_q = 0
      st.session_state.score = 0
      st.session_state.answered = False
      st.session_state.selected_option = None
      st.session_state.step = "quiz"
      st.rerun()
  st.markdown("</div>", unsafe_allow_html=True)
