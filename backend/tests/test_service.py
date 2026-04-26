"""
Тесты для сервиса (services/service.py)
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import select

from backend.services.service import ChatService
from backend.models.chat import Chat, ChatMessage
from backend.client.ai_client import AiClient


class TestChatServiceChats:
    """Тесты для работы с чатами"""

    @pytest.mark.asyncio
    async def test_create_chat(self, test_session, test_user_id):
        """Создание нового чата"""
        service = ChatService()
        
        chat = await service.create_chat(test_user_id, test_session)
        
        assert chat.id is not None
        assert chat.user_id == test_user_id
        assert chat.title == "New chat"
        assert chat.created_at is not None
        assert chat.updated_at is not None

    @pytest.mark.asyncio
    async def test_get_user_chats(self, test_session, test_user_id, test_chat):
        """Получение чатов пользователя"""
        service = ChatService()
        
        chats = await service.get_user_chats(test_user_id, test_session)
        
        assert len(chats) > 0
        assert any(c.id == test_chat.id for c in chats)

    @pytest.mark.asyncio
    async def test_get_user_chats_empty(self, test_session, test_user_id):
        """Получение пустого списка чатов"""
        service = ChatService()
        
        chats = await service.get_user_chats(999, test_session)
        
        assert len(chats) == 0

    @pytest.mark.asyncio
    async def test_get_user_chats_sorted_by_updated_at(self, test_session, test_user_id):
        """Проверка сортировки чатов по updated_at"""
        service = ChatService()
        
        # Создаём два чата
        chat1 = await service.create_chat(test_user_id, test_session)
        chat2 = await service.create_chat(test_user_id, test_session)
        
        chats = await service.get_user_chats(test_user_id, test_session)
        
        # Последний созданный должен быть первым
        assert chats[0].id == chat2.id
        assert chats[1].id == chat1.id

    @pytest.mark.asyncio
    async def test_delete_chat(self, test_session, test_user_id, test_chat):
        """Удаление чата"""
        service = ChatService()
        
        result = await service.delete_chat(test_chat.id, test_user_id, test_session)
        
        assert result["status"] == "deleted"
        
        # Проверяем, что чат удалён
        chats = await service.get_user_chats(test_user_id, test_session)
        assert not any(c.id == test_chat.id for c in chats)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_chat(self, test_session, test_user_id):
        """Удаление несуществующего чата"""
        service = ChatService()
        
        with pytest.raises(Exception) as exc_info:
            await service.delete_chat(999999, test_user_id, test_session)
        
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_delete_other_users_chat(self, test_session, test_user_id, test_chat):
        """Попытка удалить чат другого пользователя"""
        service = ChatService()
        
        with pytest.raises(Exception) as exc_info:
            await service.delete_chat(test_chat.id, 999, test_session)
        
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_delete_chat_with_messages(self, test_session, test_user_id, test_chat, test_messages):
        """Удаление чата с сообщениями"""
        service = ChatService()
        
        # Убедимся, что есть сообщения
        messages = await service.get_chat_messages(test_chat.id, test_user_id, test_session)
        assert len(messages) > 0
        
        # Удаляем чат
        result = await service.delete_chat(test_chat.id, test_user_id, test_session)
        assert result["status"] == "deleted"
        
        # Проверяем, что сообщения тоже удалены
        with pytest.raises(Exception):
            await service.get_chat_messages(test_chat.id, test_user_id, test_session)


class TestChatServiceMessages:
    """Тесты для работы с сообщениями"""

    @pytest.mark.asyncio
    async def test_get_chat_messages(self, test_session, test_user_id, test_chat, test_messages):
        """Получение сообщений чата"""
        service = ChatService()
        
        messages = await service.get_chat_messages(test_chat.id, test_user_id, test_session)
        
        assert len(messages) == 2
        assert messages[0].content == "Привет!"
        assert messages[1].content == "Привет! Как дела?"

    @pytest.mark.asyncio
    async def test_get_chat_messages_empty(self, test_session, test_user_id, test_chat):
        """Получение пустого списка сообщений"""
        service = ChatService()
        
        messages = await service.get_chat_messages(test_chat.id, test_user_id, test_session)
        
        assert isinstance(messages, list)

    @pytest.mark.asyncio
    async def test_get_messages_nonexistent_chat(self, test_session, test_user_id):
        """Получение сообщений несуществующего чата"""
        service = ChatService()
        
        with pytest.raises(Exception) as exc_info:
            await service.get_chat_messages(999999, test_user_id, test_session)
        
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_messages_other_users_chat(self, test_session, test_user_id, test_chat):
        """Получение сообщений чата другого пользователя"""
        service = ChatService()
        
        with pytest.raises(Exception) as exc_info:
            await service.get_chat_messages(test_chat.id, "other-user", test_session)
        
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_send_message(self, test_session, test_user_id, test_chat, mocker):
        """Отправка сообщения"""
        # Мокируем AI клиент
        mocker.patch(
            'backend.services.service.AiClient.chat',
            return_value="Ответ от AI"
        )
        
        service = ChatService()
        
        result = await service.send_message(
            test_chat.id,
            test_user_id,
            "Тестовое сообщение",
            test_session
        )
        
        assert "user_message" in result
        assert "ai_response" in result
        assert result["user_message"] == "Тестовое сообщение"
        assert result["ai_response"] == "Ответ от AI"

    @pytest.mark.asyncio
    async def test_send_message_stores_in_db(self, test_session, test_user_id, test_chat, mocker):
        """Проверка, что сообщение сохраняется в БД"""
        mocker.patch(
            'backend.services.service.AiClient.chat',
            return_value="Ответ"
        )
        
        service = ChatService()
        
        await service.send_message(
            test_chat.id,
            test_user_id,
            "Новое сообщение",
            test_session
        )
        
        # Получаем сообщения из БД
        messages = await service.get_chat_messages(test_chat.id, test_user_id, test_session)
        
        # Должно быть 2 сообщения: user + assistant
        assert len(messages) == 2
        assert any(m.content == "Новое сообщение" for m in messages)
        assert any(m.content == "Ответ" for m in messages)

    @pytest.mark.asyncio
    async def test_send_message_to_nonexistent_chat(self, test_session, test_user_id, mocker):
        """Отправка сообщения в несуществующий чат"""
        mocker.patch(
            'backend.services.service.AiClient.chat',
            return_value="Ответ"
        )
        
        service = ChatService()
        
        with pytest.raises(Exception) as exc_info:
            await service.send_message(999999, test_user_id, "Сообщение", test_session)
        
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_send_message_to_other_users_chat(self, test_session, test_user_id, test_chat, mocker):
        """Отправка сообщения в чат другого пользователя"""
        mocker.patch(
            'backend.services.service.AiClient.chat',
            return_value="Ответ"
        )
        
        service = ChatService()
        
        with pytest.raises(Exception) as exc_info:
            await service.send_message(test_chat.id, "other-user", "Сообщение", test_session)
        
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()


class TestChatServiceInternal:
    """Тесты для внутренних методов сервиса"""

    @pytest.mark.asyncio
    async def test_get_chat_or_404(self, test_session, test_user_id, test_chat):
        """Получение чата (успех)"""
        service = ChatService()
        
        chat = await service._get_chat_or_404(test_chat.id, test_user_id, test_session)
        
        assert chat.id == test_chat.id
        assert chat.user_id == test_user_id

    @pytest.mark.asyncio
    async def test_get_chat_or_404_not_found(self, test_session, test_user_id):
        """Получение несуществующего чата"""
        service = ChatService()
        
        with pytest.raises(Exception) as exc_info:
            await service._get_chat_or_404(999999, test_user_id, test_session)
        
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_chat_or_404_wrong_user(self, test_session, test_chat):
        """Получение чата другого пользователя"""
        service = ChatService()
        
        with pytest.raises(Exception) as exc_info:
            await service._get_chat_or_404(test_chat.id, "other-user", test_session)
        
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_last_messages(self, test_session, test_chat, test_messages):
        """Получение последних сообщений"""
        service = ChatService()
        
        messages = await service._get_last_messages(test_chat.id, test_session, limit=10)
        
        assert len(messages) == 2
        # Они должны быть в правильном порядке (от старых к новым)
        assert messages[0].content == "Привет!"
        assert messages[1].content == "Привет! Как дела?"

    @pytest.mark.asyncio
    async def test_get_last_messages_with_limit(self, test_session, test_user_id, mocker):
        """Проверка лимита на количество сообщений"""
        service = ChatService()
        
        # Мокируем AI клиент
        mocker.patch(
            'backend.services.service.AiClient.chat',
            return_value="Ответ"
        )
        
        # Создаём чат
        chat = await service.create_chat(test_user_id, test_session)
        
        # Отправляем 5 сообщений
        for i in range(5):
            await service.send_message(
                chat.id,
                test_user_id,
                f"Сообщение {i}",
                test_session
            )
        
        # Получаем только последние 3
        messages = await service._get_last_messages(chat.id, test_session, limit=3)
        
        assert len(messages) <= 3
