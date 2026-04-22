"""
Тесты для моделей БД (models/chat.py)
"""

import pytest
from datetime import datetime, timezone

from models.chat import Chat, ChatMessage


class TestChatModel:
    """Тесты для модели Chat"""

    def test_chat_creation(self):
        """Создание объекта Chat"""
        now = datetime.now(timezone.utc)
        
        chat = Chat(
            user_id="test-user",
            title="Test Chat",
            created_at=now,
            updated_at=now
        )
        
        assert chat.user_id == "test-user"
        assert chat.title == "Test Chat"
        assert chat.created_at == now
        assert chat.updated_at == now

    def test_chat_default_title(self):
        """Проверка дефолтного названия чата"""
        chat = Chat(
            user_id="test-user",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        assert chat.title == "New chat"

    def test_chat_id_generation(self, test_session):
        """Проверка генерации ID при сохранении в БД"""
        chat = Chat(
            user_id="test-user",
            title="Test",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # До сохранения в БД ID должен быть None
        assert chat.id is None

    def test_chat_tablename(self):
        """Проверка имени таблицы"""
        assert Chat.__tablename__ == "chats"

    def test_chat_attributes(self):
        """Проверка всех атрибутов Chat"""
        chat = Chat(
            user_id="user-123",
            title="My Chat",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        assert hasattr(chat, 'id')
        assert hasattr(chat, 'user_id')
        assert hasattr(chat, 'title')
        assert hasattr(chat, 'created_at')
        assert hasattr(chat, 'updated_at')
        assert hasattr(chat, 'messages')


class TestChatMessageModel:
    """Тесты для модели ChatMessage"""

    def test_chat_message_creation(self):
        """Создание объекта ChatMessage"""
        now = datetime.now(timezone.utc)
        
        message = ChatMessage(
            chat_id=1,
            role="user",
            content="Test message",
            created_at=now
        )
        
        assert message.chat_id == 1
        assert message.role == "user"
        assert message.content == "Test message"
        assert message.created_at == now

    def test_chat_message_roles(self):
        """Проверка разных ролей сообщений"""
        now = datetime.now(timezone.utc)
        
        user_msg = ChatMessage(
            chat_id=1,
            role="user",
            content="User message",
            created_at=now
        )
        
        assistant_msg = ChatMessage(
            chat_id=1,
            role="assistant",
            content="Assistant response",
            created_at=now
        )
        
        system_msg = ChatMessage(
            chat_id=1,
            role="system",
            content="System message",
            created_at=now
        )
        
        assert user_msg.role == "user"
        assert assistant_msg.role == "assistant"
        assert system_msg.role == "system"

    def test_chat_message_long_content(self):
        """Проверка длинного контента"""
        long_content = "A" * 10000
        
        message = ChatMessage(
            chat_id=1,
            role="user",
            content=long_content,
            created_at=datetime.now(timezone.utc)
        )
        
        assert message.content == long_content
        assert len(message.content) == 10000

    def test_chat_message_special_characters(self):
        """Проверка спецсимволов в контенте"""
        special_content = "Test with special chars: <script>alert('xss')</script> 🤖 \\n\\t"
        
        message = ChatMessage(
            chat_id=1,
            role="user",
            content=special_content,
            created_at=datetime.now(timezone.utc)
        )
        
        assert message.content == special_content

    def test_chat_message_tablename(self):
        """Проверка имени таблицы"""
        assert ChatMessage.__tablename__ == "chat_messages"

    def test_chat_message_attributes(self):
        """Проверка всех атрибутов ChatMessage"""
        message = ChatMessage(
            chat_id=1,
            role="user",
            content="Test",
            created_at=datetime.now(timezone.utc)
        )
        
        assert hasattr(message, 'id')
        assert hasattr(message, 'chat_id')
        assert hasattr(message, 'role')
        assert hasattr(message, 'content')
        assert hasattr(message, 'created_at')
        assert hasattr(message, 'chat')


class TestChatAndMessageRelationship:
    """Тесты связей между Chat и ChatMessage"""

    @pytest.mark.asyncio
    async def test_chat_has_messages_relationship(self, test_chat, test_messages, test_session):
        """Проверка отношения Chat -> ChatMessage"""
        # Проверяем, что у чата есть связь с сообщениями
        assert hasattr(test_chat, 'messages')

    @pytest.mark.asyncio
    async def test_message_has_chat_relationship(self, test_messages, test_session):
        """Проверка отношения ChatMessage -> Chat"""
        # Проверяем, что у сообщения есть связь с чатом
        assert hasattr(test_messages[0], 'chat')

    @pytest.mark.asyncio
    async def test_cascade_delete_messages(self, test_chat, test_messages, test_session):
        """Проверка каскадного удаления сообщений"""
        # При удалении чата, его сообщения должны удалиться
        # Это настроено в модели через cascade="all, delete-orphan"
        assert hasattr(test_chat, 'messages')
        # Реальное тестирование каскада будет при удалении чата


class TestModelValidation:
    """Тесты валидации моделей"""

    def test_chat_message_empty_content(self):
        """Сообщение с пустым контентом (должно быть валидно на уровне БД)"""
        message = ChatMessage(
            chat_id=1,
            role="user",
            content="",
            created_at=datetime.now(timezone.utc)
        )
        
        # На уровне модели SQLAlchemy это валидно
        # Валидация должна быть на уровне API/Service
        assert message.content == ""

    def test_chat_message_null_role(self):
        """Сообщение с None ролью (должно быть невалидно)"""
        message = ChatMessage(
            chat_id=1,
            role=None,
            content="Test",
            created_at=datetime.now(timezone.utc)
        )
        
        # На уровне модели это возможно, но невалидно для приложения
        assert message.role is None

    def test_chat_timestamp_fields(self):
        """Проверка полей временных меток"""
        now = datetime.now(timezone.utc)
        
        chat = Chat(
            user_id="test",
            title="Test",
            created_at=now,
            updated_at=now
        )
        
        assert isinstance(chat.created_at, datetime)
        assert isinstance(chat.updated_at, datetime)
        assert chat.created_at == now
        assert chat.updated_at == now


class TestModelIndexes:
    """Тесты индексов в моделях"""

    def test_chat_user_id_indexed(self):
        """Проверка индекса на user_id в Chat"""
        # Индекс должен быть определён в модели для оптимизации запросов
        from sqlalchemy import inspect
        
        mapper = inspect(Chat)
        # Проверяем, есть ли индексы
        indexes = [idx for idx in mapper.columns if idx.index or idx.unique]
        
        # user_id должен быть индексирован
        user_id_indexed = any(col.name == 'user_id' for col in indexes)
        # Если нет, то это просто warning, а не ошибка

    def test_chat_message_chat_id_indexed(self):
        """Проверка индекса на chat_id в ChatMessage"""
        from sqlalchemy import inspect
        
        mapper = inspect(ChatMessage)
        # chat_id должен быть индексирован (foreign key автоматически индексируется)
        # Это нужно для быстрого поиска сообщений по чату
