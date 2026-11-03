import asyncio
from decimal import Decimal

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.database import async_session_maker, engine
from app.models import (
    ContentType,
    Course,
    Lesson,
    Module,
    QuestionKind,
    QuizOption,
    QuizQuestion,
    User,
    UserRole,
)

DEMO_VIDEO = "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4"

DEMO_USERS = [
    ("owner@example.com", "owner12345", UserRole.OWNER),
    ("admin@example.com", "admin12345", UserRole.ADMIN),
    ("student@example.com", "student12345", UserRole.STUDENT),
]

TEXT = ContentType.TEXT
VIDEO = ContentType.VIDEO

DEMO_COURSES = [
    {
        "title": "Python с нуля",
        "slug": "python-basics",
        "price": Decimal("4990.00"),
        "description": (
            "Практический курс для тех, кто никогда не программировал.\n\n"
            "За три модуля вы научитесь писать небольшие программы: работать с переменными, "
            "условиями, циклами и функциями. Первые уроки открыты бесплатно."
        ),
        "modules": [
            {
                "title": "Первые шаги",
                "price": Decimal("1490.00"),
                "lessons": [
                    (
                        "Что такое Python и зачем он нужен",
                        TEXT,
                        "## Почему Python\n\n"
                        "Python — один из самых популярных языков программирования. На нём пишут:\n\n"
                        "- веб-сайты и API;\n- анализ данных и машинное обучение;\n"
                        "- скрипты для автоматизации рутины.\n\n"
                        "> Простой синтаксис позволяет думать о задаче, а не о языке.\n\n"
                        "Первая программа выглядит так:\n\n"
                        "```python\nprint(\"Привет, мир!\")\n```",
                        True,
                    ),
                    ("Установка и первый запуск", VIDEO, DEMO_VIDEO, True),
                    (
                        "Переменные и типы данных",
                        TEXT,
                        "## Переменные\n\n"
                        "Переменная — это имя, за которым хранится значение:\n\n"
                        "```python\nname = \"Анна\"\nage = 30\nprice = 19.99\nis_student = True\n```\n\n"
                        "| Тип | Пример |\n|---|---|\n| `str` | `\"текст\"` |\n| `int` | `42` |\n"
                        "| `float` | `3.14` |\n| `bool` | `True` |",
                        False,
                    ),
                ],
            },
            {
                "title": "Условия и циклы",
                "price": Decimal("1990.00"),
                "lessons": [
                    (
                        "Условия: if, elif, else",
                        TEXT,
                        "## Ветвление\n\n```python\nage = 17\n\nif age >= 18:\n    print(\"Добро пожаловать\")\n"
                        "elif age >= 14:\n    print(\"Нужно согласие родителей\")\nelse:\n"
                        "    print(\"Пока рано\")\n```\n\nОбратите внимание на **отступы**: "
                        "в Python они обязательны.",
                        False,
                    ),
                    (
                        "Циклы for и while",
                        TEXT,
                        "## Цикл for\n\n```python\nfor number in range(1, 4):\n    print(number)\n```\n\n"
                        "## Цикл while\n\n```python\ncount = 3\nwhile count > 0:\n    print(count)\n"
                        "    count -= 1\n```",
                        False,
                    ),
                    ("Практика: игра «Угадай число»", VIDEO, DEMO_VIDEO, False),
                ],
            },
            {
                "title": "Функции",
                "price": None,
                "lessons": [
                    (
                        "Как объявить функцию",
                        TEXT,
                        "## def\n\n```python\ndef greet(name):\n    return f\"Привет, {name}!\"\n\n"
                        "print(greet(\"Мир\"))\n```",
                        False,
                    ),
                    (
                        "Аргументы и return",
                        TEXT,
                        "## Значения по умолчанию\n\n```python\ndef power(base, exponent=2):\n"
                        "    return base ** exponent\n\npower(3)     # 9\npower(2, 10) # 1024\n```",
                        False,
                    ),
                ],
            },
        ],
    },
    {
        "title": "SQL для аналитиков",
        "slug": "sql-basics",
        "price": Decimal("2990.00"),
        "description": (
            "Научитесь доставать ответы из базы данных самостоятельно: фильтровать, "
            "группировать и соединять таблицы. Курс продаётся только целиком."
        ),
        "modules": [
            {
                "title": "SELECT и фильтрация",
                "price": None,
                "lessons": [
                    (
                        "Первый запрос",
                        TEXT,
                        "## SELECT\n\n```sql\nSELECT title, price\nFROM courses;\n```\n\n"
                        "`SELECT` перечисляет колонки, `FROM` — таблицу.",
                        True,
                    ),
                    (
                        "WHERE и сортировка",
                        TEXT,
                        "```sql\nSELECT title, price\nFROM courses\nWHERE price < 3000\n"
                        "ORDER BY price DESC;\n```",
                        False,
                    ),
                ],
            },
            {
                "title": "Группировки и соединения",
                "price": None,
                "lessons": [
                    (
                        "GROUP BY и агрегатные функции",
                        TEXT,
                        "```sql\nSELECT course_id, COUNT(*) AS purchases\nFROM purchases\n"
                        "GROUP BY course_id;\n```",
                        False,
                    ),
                    ("JOIN: соединяем таблицы", VIDEO, DEMO_VIDEO, False),
                ],
            },
        ],
    },
]


DEMO_DURATIONS = {
    "Что такое Python и зачем он нужен": 8,
    "Установка и первый запуск": 12,
    "Переменные и типы данных": 10,
    "Условия: if, elif, else": 12,
    "Циклы for и while": 15,
    "Практика: игра «Угадай число»": 20,
    "Как объявить функцию": 10,
    "Аргументы и return": 12,
    "Первый запрос": 8,
    "WHERE и сортировка": 10,
    "GROUP BY и агрегатные функции": 12,
    "JOIN: соединяем таблицы": 15,
}

SINGLE = QuestionKind.SINGLE
MULTIPLE = QuestionKind.MULTIPLE
TEXT_ANSWER = QuestionKind.TEXT

DEMO_QUIZZES = {
    "Что такое Python и зачем он нужен": [
        (
            SINGLE,
            "Какой функцией вывести текст на экран?",
            "Для вывода в Python используется встроенная функция `print()`.",
            [("print()", True), ("echo()", False), ("write()", False)],
        ),
    ],
    "Переменные и типы данных": [
        (
            SINGLE,
            "Какой тип у значения `3.14`?",
            "Числа с дробной частью в Python имеют тип `float`.",
            [("int", False), ("float", True), ("str", False)],
        ),
        (
            MULTIPLE,
            "Какие имена переменных допустимы?",
            "Имя не может начинаться с цифры, а с подчёркивания — может.",
            [("user_name", True), ("2nd_place", False), ("_total", True)],
        ),
        (
            TEXT_ANSWER,
            "Что выведет `print(type(True).__name__)`?",
            "`True` и `False` — значения логического типа `bool`.",
            [("bool", True)],
        ),
    ],
    "Условия: if, elif, else": [
        (
            SINGLE,
            "Что обязательно для блока кода внутри `if`?",
            "В Python блоки выделяются отступом, скобки не нужны.",
            [("Отступ", True), ("Фигурные скобки", False), ("Точка с запятой", False)],
        ),
        (
            TEXT_ANSWER,
            "Какое ключевое слово означает «иначе, если»?",
            "Это `elif` — сокращение от else if.",
            [("elif", True)],
        ),
    ],
    "Циклы for и while": [
        (
            MULTIPLE,
            "Какие циклы есть в Python?",
            "В Python два цикла: `for` и `while`.",
            [("for", True), ("while", True), ("repeat", False), ("do-while", False)],
        ),
        (
            TEXT_ANSWER,
            "Сколько раз выполнится тело цикла `for i in range(3)`?",
            "`range(3)` даёт числа 0, 1 и 2 — три повторения.",
            [("3", True), ("три", True)],
        ),
    ],
    "Первый запрос": [
        (
            SINGLE,
            "Какое ключевое слово указывает таблицу в запросе?",
            "Таблица указывается после `FROM`.",
            [("FROM", True), ("SELECT", False), ("WHERE", False)],
        ),
    ],
}


async def ensure_lesson_extras(session: AsyncSession) -> None:
    slugs = [course["slug"] for course in DEMO_COURSES]
    lessons = await session.scalars(
        select(Lesson).join(Lesson.module).join(Module.course).where(Course.slug.in_(slugs))
    )
    for lesson in lessons:
        if lesson.duration_minutes is None and lesson.title in DEMO_DURATIONS:
            lesson.duration_minutes = DEMO_DURATIONS[lesson.title]
        quiz = DEMO_QUIZZES.get(lesson.title)
        if not quiz:
            continue
        has_questions = await session.scalar(
            select(exists().where(QuizQuestion.lesson_id == lesson.id))
        )
        if has_questions:
            continue
        for position, (kind, prompt, explanation, options) in enumerate(quiz, start=1):
            session.add(
                QuizQuestion(
                    lesson_id=lesson.id,
                    position=position,
                    kind=kind,
                    prompt=prompt,
                    explanation=explanation,
                    options=[
                        QuizOption(position=index, text=text, is_correct=is_correct)
                        for index, (text, is_correct) in enumerate(options, start=1)
                    ],
                )
            )
        print(f"Вопросы добавлены к уроку «{lesson.title}»")


async def ensure_users(session: AsyncSession) -> User:
    owner = await session.scalar(select(User).where(User.role == UserRole.OWNER))
    for email, password, role in DEMO_USERS:
        if role == UserRole.OWNER and owner is not None:
            continue
        if await session.scalar(select(User.id).where(User.email == email)) is not None:
            continue
        user = User(email=email, password_hash=await hash_password(password), role=role)
        session.add(user)
        if role == UserRole.OWNER:
            owner = user
        print(f"Пользователь {email} / {password} ({role})")
    await session.flush()
    return owner


async def ensure_course(session: AsyncSession, owner: User, data: dict) -> None:
    if await session.scalar(select(Course.id).where(Course.slug == data["slug"])) is not None:
        print(f"Курс {data['slug']} уже есть, пропускаю")
        return
    course = Course(
        title=data["title"],
        slug=data["slug"],
        price=data["price"],
        description=data["description"],
        owner_id=owner.id,
    )
    for module_position, module_data in enumerate(data["modules"], start=1):
        module = Module(
            title=module_data["title"], position=module_position, price=module_data["price"]
        )
        course.modules.append(module)
        for lesson_position, (title, content_type, content, is_free) in enumerate(
            module_data["lessons"], start=1
        ):
            module.lessons.append(
                Lesson(
                    title=title,
                    content_type=content_type,
                    content=content,
                    position=lesson_position,
                    is_free_preview=is_free,
                )
            )
    session.add(course)
    print(f"Курс {data['slug']} создан")


async def seed() -> None:
    try:
        async with async_session_maker() as session:
            owner = await ensure_users(session)
            for course_data in DEMO_COURSES:
                await ensure_course(session, owner, course_data)
            await session.flush()
            await ensure_lesson_extras(session)
            await session.commit()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
