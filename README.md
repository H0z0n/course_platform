# Платформа онлайн-курсов — шаблон

Однопользовательский шаблон: одна инсталляция = один владелец и его курсы. Владелец разворачивает свою копию и наполняет её курсами через админку.

- **Backend:** FastAPI (async) + PostgreSQL + SQLAlchemy 2.0 (AsyncSession, asyncpg) + Alembic
- **Frontend:** React + TypeScript + Vite

Как устроен код и почему именно так — в [NOTES.md](NOTES.md).

## Требования

- Python 3.12+ (проект разрабатывается на 3.14)
- PostgreSQL 14+ (проверено на 18)
- Node.js 20+ (проверено на 24) — только для фронтенда

## Backend

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
copy .env.example .env
```

Заполнить в `.env`:
- `DATABASE_URL` — строка подключения к PostgreSQL;
- `SECRET_KEY` — длинная случайная строка. Сгенерировать можно так:
  ```powershell
  .venv\Scripts\python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```

Создать таблицы:

```powershell
.venv\Scripts\alembic upgrade head
```

Наполнить данными — один из двух вариантов:
- для разработки — демо-данные (пользователи и два курса):
  ```powershell
  .venv\Scripts\python -m app.scripts.seed_demo
  ```
- для настоящей инсталляции — только владелец:
  ```powershell
  .venv\Scripts\python -m app.scripts.create_owner --email you@example.com
  ```

Запустить сервер:

```powershell
.venv\Scripts\python -m uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000/api
- Интерактивная документация: http://127.0.0.1:8000/docs (кнопка «Authorize» → email в поле username и пароль)

## Frontend (разработка)

```powershell
cd frontend
npm install
npm run dev
```

Открыть http://localhost:5173. Vite проксирует запросы `/api` на backend (`:8000`), поэтому backend должен быть запущен.

## Продакшен-сборка

```powershell
cd frontend
npm run build
```

После сборки FastAPI сам отдаёт фронтенд из `frontend/dist`. Достаточно одного процесса uvicorn: http://127.0.0.1:8000.

## Тесты

```powershell
.venv\Scripts\python -m pytest
```

Тесты работают с отдельной БД `<имя основной БД>_test`. Она создаётся автоматически, основная база не затрагивается.

## Демо-аккаунты (после `seed_demo`)

| Email | Пароль | Роль |
|---|---|---|
| owner@example.com | owner12345 | владелец |
| admin@example.com | admin12345 | администратор |
| student@example.com | student12345 | ученик |

## Переменные окружения

| Переменная | Обязательна | По умолчанию | Назначение |
|---|---|---|---|
| `DATABASE_URL` | да | — | `postgresql+asyncpg://user:password@host:5432/db` |
| `SECRET_KEY` | да | — | ключ подписи JWT |
| `DB_ECHO` | нет | `false` | печатать SQL-запросы в консоль |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | нет | `1440` | срок жизни токена входа |
| `SITE_NAME` | нет | `Course Platform` | название сайта, пока владелец не задал своё в «Управление → Оформление» |
| `CURRENCY` | нет | `RUB` | валюта цен (код ISO 4217) |
| `DEMO_PAYMENTS` | нет | `false` | тестовая оплата без денег. **Не включать на боевом сервере** |
| `CORS_ORIGINS` | нет | `[]` | JSON-список доменов, если фронтенд живёт на другом домене |
| `PUBLIC_URL` | нет | `http://localhost:5173` | адрес сайта для ссылок в письмах (на сервере — `https://ваш-домен`) |
| `PASSWORD_RESET_EXPIRE_MINUTES` | нет | `60` | сколько живёт ссылка восстановления пароля |
| `SMTP_HOST`, `SMTP_PORT` | нет | —, `587` | почтовый сервер. Если `SMTP_HOST` пустой, письма не отправляются, а печатаются в консоль сервера |
| `SMTP_USER`, `SMTP_PASSWORD` | нет | — | логин и пароль почтового ящика (для Яндекса и Mail.ru — пароль приложения) |
| `SMTP_FROM` | нет | `noreply@example.com` | адрес отправителя |
| `SMTP_STARTTLS`, `SMTP_SSL` | нет | `true`, `false` | шифрование: порт 587 → STARTTLS, порт 465 → `SMTP_SSL=true`, `SMTP_STARTTLS=false` |

## Структура

```
app/
  core/            config.py (настройки), security.py (пароли, JWT)
  models/          таблицы SQLAlchemy
  schemas/         Pydantic-схемы запросов и ответов
  services/        бизнес-логика: доступ к урокам, покупки, прогресс, порядок
  routers/         HTTP-эндпоинты
  scripts/         create_owner, seed_demo
  database.py      engine, сессии, Base
  dependencies.py  зависимости FastAPI: сессия, текущий пользователь, роли
  main.py          сборка приложения, раздача фронтенда
migrations/        миграции Alembic
tests/             тесты pytest
frontend/          React-приложение
```
