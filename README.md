# AI Chat (FastAPI + OpenRouter)

Мини‑проект: мини‑сервер “как ChatGPT” с поддержкой нескольких чатов для пользователя, хранением истории в БД и web‑интерфейсом.

## Возможности

- Несколько чатов на пользователя (идентификация по `session_id` в cookie)
- История сообщений (user/assistant/system) в SQLite через async SQLAlchemy
- Генерация ответов через OpenRouter (OpenAI SDK, `AsyncOpenAI`)
- Готовый UI (SPA без сборки) в “tech” стиле

## Стек

- Backend: FastAPI, SQLAlchemy 2.x (async), aiosqlite
- LLM: OpenRouter API (`base_url=https://openrouter.ai/api/v1`)
- Frontend: статические `HTML/CSS/JS`, раздаётся самим бэком

## Быстрый старт (Windows)

1) Установка окружения и зависимостей:
- `setup.bat`

2) Запуск бэкенда:
- `run_backend.bat`

3) Открыть UI:
- `http://127.0.0.1:8000/`

Также доступна Swagger-документация:
- `http://127.0.0.1:8000/docs`

## Переменные окружения

Скопируйте `.env.example` → `.env` и заполните:

- `OPENROUTER_API_KEY` — ключ OpenRouter (обязательно)
- `OPENROUTER_MODEL` — модель (по умолчанию `google/gemma-4-31b-it:free`)
- `OPENROUTER_SITE_URL`, `OPENROUTER_APP_NAME` — метаданные для OpenRouter (опционально)
- `SECRET_KEY` — ключ подписи cookie (в проде обязателен сильный)
- `COOKIE_SECURE` — `true` под HTTPS
- `COOKIE_SAMESITE` — `strict|lax|none` (если фронт отдельно на `:5500`, обычно лучше `lax`)
- `CORS_ORIGINS` — список origin через запятую
- `DATABASE_URL` — (опционально) строка подключения БД, иначе SQLite файл `chat_history.db`
- `MAX_MESSAGES_IN_CONTEXT` — сколько сообщений брать в контекст

## API (основные эндпоинты)

- `GET /chats` — список чатов пользователя
- `POST /chats` — создать чат
- `DELETE /chats/{chat_id}` — удалить чат
- `GET /chats/{chat_id}/messages` — получить сообщения чата
- `POST /chats/{chat_id}/messages` — отправить сообщение, получить ответ AI

Пример запроса:

```bash
curl -X POST http://127.0.0.1:8000/chats
curl -X POST http://127.0.0.1:8000/chats/1/messages -H "Content-Type: application/json" -d "{\"content\":\"Привет\"}"
```

## Frontend

UI хранится в `frontend/` и по умолчанию раздаётся самим бэкендом:

- `GET /` → `frontend/index.html`
- `GET /static/*` → `frontend/static/*`

Если хотите запускать UI отдельно:

- `run_frontend.bat` (поднимает простой HTTP сервер на `http://127.0.0.1:5500`)

Примечание: при отдельном origin браузер может не отправлять cookie (`SameSite`), поэтому UI дополнительно использует заголовок `X-Session-Id` (бэк возвращает его в ответах).

## Тесты

```bash
python -m pytest -q
```

## Деплой Render + Netlify (Опиционально)

### Backend на Render (free)

1) Загрузите репозиторий на GitHub.
2) На Render создайте **Web Service** из GitHub репозитория.
3) Настройки:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
4) Environment Variables (обязательно):
   - `OPENROUTER_API_KEY`
   - `SECRET_KEY`

Примечание про БД:
- По умолчанию используется SQLite файл (`chat_history.db`). На free-хостингах файловая система часто **эфемерна** — история может сбрасываться при рестартах/деплоях. Для “по‑настоящему” лучше Postgres.

### Frontend на Netlify

Рекомендованный вариант — Netlify proxy: браузер обращается к `/api/*` на домене Netlify, а Netlify проксирует запросы на Render. Плюсы: не нужен CORS, cookie становятся first‑party.

1) В Netlify: **Add new site** → импорт из GitHub.
2) Publish directory: `frontend` (см. `netlify.toml`).
3) После первого деплоя откройте `netlify.toml` и замените:
   - `https://YOUR_RENDER_SERVICE.onrender.com` на ваш URL Render.
4) Redeploy.

После этого UI работает сразу на Netlify, а API вызовы идут через `/api/*`.

## Структура проекта

- `main.py` — FastAPI приложение, CORS, раздача фронта, lifespan (инициализация/закрытие AI клиента)
- `routers/routes.py` — HTTP API
- `services/service.py` — бизнес‑логика чатов/сообщений, сессии (cookie + подпись)
- `client/ai_client.py` — клиент OpenRouter (AsyncOpenAI)
- `models/` — SQLAlchemy модели
- `db/database.py` — engine/session + SQLite PRAGMA foreign_keys
- `schemas/` — Pydantic схемы
- `frontend/` — UI
- `tests/` — тесты

## Безопасность (кратко)

- В проде обязательно задайте `SECRET_KEY` и включите `COOKIE_SECURE=true` под HTTPS.
- Добавьте rate limiting (по `session_id`/IP), иначе можно легко “сжечь” лимиты на LLM.
- SQLite подходит для прототипа; для масштаба лучше Postgres + миграции (Alembic).
