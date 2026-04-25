"""
Конфигурация и fixtures для тестов
"""

import asyncio

import httpx
import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from backend.db.database import get_session
from backend.main import app
from backend.models.chat import Base, Chat, ChatMessage
from unittest.mock import AsyncMock, MagicMock, patch


# ========== Database Setup ==========


@pytest.fixture(scope="session")
def event_loop():
    """Создаёт event loop для async тестов"""

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Создаёт тестовую БД (in-memory SQLite)"""

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"timeout": 30, "check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture(scope="session")
def test_session_maker(test_engine):
    """Создаёт SessionMaker для тестов"""

    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@pytest.fixture
async def test_session(test_session_maker):
    """Создаёт новую сессию для каждого теста"""

    async with test_session_maker() as session:
        yield session

    # Очищаем БД после теста
    async with test_session_maker() as session:
        await session.execute(delete(ChatMessage))
        await session.execute(delete(Chat))
        await session.commit()


# ========== FastAPI Client ==========


@pytest.fixture
async def async_client(test_session_maker, test_user_id):
    """Создаёт async HTTP клиент для тестирования API"""

    async def override_get_session():
        async with test_session_maker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        from itsdangerous import URLSafeTimedSerializer
        from backend.config.config import app_config

        token = URLSafeTimedSerializer(app_config.SECRET_KEY).dumps({"user_id": test_user_id})
        client.cookies.set("session_id", token)
        yield client

    app.dependency_overrides.clear()


# ========== Test Data ==========


@pytest.fixture
def test_user_id():
    """ID тестового пользователя"""

    return "test-user-123"


@pytest.fixture
async def test_chat(test_session, test_user_id):
    """Создаёт тестовый чат в БД"""

    from datetime import datetime, timezone

    chat = Chat(
        user_id=test_user_id,
        title="Test Chat",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_session.add(chat)
    await test_session.commit()
    await test_session.refresh(chat)
    return chat


@pytest.fixture
async def test_messages(test_session, test_chat):
    """Создаёт тестовые сообщения в БД"""

    from datetime import datetime, timezone

    messages = [
        ChatMessage(
            chat_id=test_chat.id,
            role="user",
            content="Привет!",
            created_at=datetime.now(timezone.utc),
        ),
        ChatMessage(
            chat_id=test_chat.id,
            role="assistant",
            content="Привет! Как дела?",
            created_at=datetime.now(timezone.utc),
        ),
    ]

    for msg in messages:
        test_session.add(msg)

    await test_session.commit()

    for msg in messages:
        await test_session.refresh(msg)

    return messages


# ========== Mocks ==========


@pytest.fixture
def mock_ai_client(mocker):
    """Мокирует AI клиент"""

    mock = mocker.AsyncMock()
    mock.chat.return_value = "Мокированный ответ от AI"
    return mock


@pytest.fixture
def mocker():
    """
    Минимальная замена `pytest-mock` (fixture `mocker`), чтобы тесты не зависели от внешнего плагина.
    Поддерживает `mocker.patch(...)` и `mocker.AsyncMock()`.
    """

    class _Mocker:
        AsyncMock = AsyncMock
        MagicMock = MagicMock

        def __init__(self):
            self._patchers = []

        def patch(self, target, *args, **kwargs):
            patcher = patch(target, *args, **kwargs)
            started = patcher.start()
            self._patchers.append(patcher)
            return started

        def stopall(self):
            for patcher in reversed(self._patchers):
                patcher.stop()
            self._patchers.clear()

    m = _Mocker()
    try:
        yield m
    finally:
        m.stopall()
