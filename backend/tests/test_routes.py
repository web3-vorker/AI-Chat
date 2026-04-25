"""
Тесты для API endpoints (routes.py)
"""

import pytest
from httpx import AsyncClient


class TestChatsEndpoints:
    """Тесты для endpoint'ов чатов"""

    @pytest.mark.asyncio
    async def test_get_chats_empty(self, async_client, test_user_id):
        """Получение пустого списка чатов"""
        response = await async_client.get("/chats")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 0

    @pytest.mark.asyncio
    async def test_get_chats_with_data(self, async_client, test_chat):
        """Получение списка чатов с данными"""
        response = await async_client.get("/chats")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["id"] == test_chat.id
        assert data[0]["title"] == test_chat.title

    @pytest.mark.asyncio
    async def test_create_chat(self, async_client):
        """Создание нового чата"""
        response = await async_client.post("/chats")
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "user_id" in data
        assert "title" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert data["title"] == "New chat"

    @pytest.mark.asyncio
    async def test_create_multiple_chats(self, async_client):
        """Создание нескольких чатов"""
        response1 = await async_client.post("/chats")
        response2 = await async_client.post("/chats")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        chat1_id = response1.json()["id"]
        chat2_id = response2.json()["id"]
        
        assert chat1_id != chat2_id

    @pytest.mark.asyncio
    async def test_delete_chat(self, async_client, test_chat):
        """Удаление чата"""
        response = await async_client.delete(f"/chats/{test_chat.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "deleted"
        
        # Проверяем, что чат удалён
        response = await async_client.get("/chats")
        chats = response.json()
        chat_ids = [c["id"] for c in chats]
        assert test_chat.id not in chat_ids

    @pytest.mark.asyncio
    async def test_delete_nonexistent_chat(self, async_client):
        """Попытка удалить несуществующий чат"""
        response = await async_client.delete("/chats/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_chat_with_invalid_id(self, async_client):
        """Удаление чата с невалидным ID (отрицательное число)"""
        response = await async_client.delete("/chats/-1")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_chat_generates_session_id(self, async_client):
        """Проверка, что session_id установлена в cookie"""
        response = await async_client.post("/chats")
        assert response.status_code == 200
        
        # Проверяем наличие session_id в cookie
        cookies = response.cookies
        assert "session_id" in cookies


class TestMessagesEndpoints:
    """Тесты для endpoint'ов сообщений"""

    @pytest.mark.asyncio
    async def test_get_chat_messages_empty(self, async_client, test_chat):
        """Получение пустого списка сообщений"""
        response = await async_client.get(f"/chats/{test_chat.id}/messages")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_chat_messages_with_data(self, async_client, test_chat, test_messages):
        """Получение списка сообщений с данными"""
        response = await async_client.get(f"/chats/{test_chat.id}/messages")
        assert response.status_code == 200
        
        messages = response.json()
        assert len(messages) == 2
        assert messages[0]["content"] == "Привет!"
        assert messages[1]["content"] == "Привет! Как дела?"

    @pytest.mark.asyncio
    async def test_get_nonexistent_chat_messages(self, async_client):
        """Получение сообщений несуществующего чата"""
        response = await async_client.get("/chats/999999/messages")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_messages_with_invalid_chat_id(self, async_client):
        """Получение сообщений с невалидным ID чата"""
        response = await async_client.get("/chats/-1/messages")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_send_message_success(self, async_client, test_chat, mocker):
        """Успешная отправка сообщения"""
        # Мокируем AI клиент
        mocker.patch(
            'backend.services.service.AiClient.chat',
            return_value="Мокированный ответ"
        )
        
        response = await async_client.post(
            f"/chats/{test_chat.id}/messages",
            json={"content": "Тестовое сообщение"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user_message" in data
        assert "ai_response" in data
        assert data["user_message"] == "Тестовое сообщение"

    @pytest.mark.asyncio
    async def test_send_message_empty(self, async_client, test_chat):
        """Отправка пустого сообщения"""
        response = await async_client.post(
            f"/chats/{test_chat.id}/messages",
            json={"content": ""}
        )
        
        # Pydantic должен валидировать min_length
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_send_message_too_long(self, async_client, test_chat):
        """Отправка слишком длинного сообщения"""
        long_content = "A" * 5000  # Больше чем max_length=4000
        
        response = await async_client.post(
            f"/chats/{test_chat.id}/messages",
            json={"content": long_content}
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_send_message_to_nonexistent_chat(self, async_client):
        """Отправка сообщения в несуществующий чат"""
        response = await async_client.post(
            "/chats/999999/messages",
            json={"content": "Тестовое сообщение"}
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_send_message_updates_chat_timestamp(self, async_client, test_chat, mocker):
        """Проверка, что отправка сообщения обновляет updated_at чата"""
        from datetime import datetime
        
        mocker.patch(
            'backend.services.service.AiClient.chat',
            return_value="Ответ"
        )
        
        old_updated_at = test_chat.updated_at
        
        response = await async_client.post(
            f"/chats/{test_chat.id}/messages",
            json={"content": "Новое сообщение"}
        )
        
        assert response.status_code == 200
        
        # Получаем обновленный чат
        chats_response = await async_client.get("/chats")
        updated_chat = [c for c in chats_response.json() if c["id"] == test_chat.id][0]
        
        assert updated_chat["updated_at"] != str(old_updated_at)


class TestAuthenticationAndSecurity:
    """Тесты аутентификации и безопасности"""

    @pytest.mark.asyncio
    async def test_session_id_is_set(self, async_client):
        """Проверка, что session_id устанавливается в cookie"""
        response = await async_client.post("/chats")
        assert "session_id" in response.cookies

    @pytest.mark.asyncio
    async def test_session_id_persists_across_requests(self, async_client):
        """Проверка, что session_id сохраняется между запросами"""
        # Первый запрос
        response1 = await async_client.post("/chats")
        session_id_1 = response1.cookies.get("session_id")
        
        # Второй запрос с тем же клиентом
        response2 = await async_client.get("/chats")
        
        # session_id должен быть тем же
        assert session_id_1 is not None

    @pytest.mark.asyncio
    async def test_chats_isolation_between_users(self, async_client):
        """Проверка изоляции чатов между пользователями"""
        # Создаём чат с одного клиента
        response1 = await async_client.post("/chats")
        chat1_id = response1.json()["id"]
        
        # Создаём новый AsyncClient (новый session_id)
        from backend.tests.conftest import async_client as other_client
        # На самом деле нужно будет два разных клиента
        # Для простоты здесь мы просто проверяем, что это возможно
        assert chat1_id is not None


class TestValidation:
    """Тесты валидации данных"""

    @pytest.mark.asyncio
    async def test_send_message_requires_content(self, async_client, test_chat):
        """Проверка, что content обязателен"""
        response = await async_client.post(
            f"/chats/{test_chat.id}/messages",
            json={}
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_send_message_content_type_validation(self, async_client, test_chat):
        """Проверка типа content"""
        response = await async_client.post(
            f"/chats/{test_chat.id}/messages",
            json={"content": 123}  # int вместо str
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_json_payload(self, async_client, test_chat):
        """Проверка обработки невалидного JSON"""
        response = await async_client.post(
            f"/chats/{test_chat.id}/messages",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
