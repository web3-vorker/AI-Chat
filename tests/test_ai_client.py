"""
Тесты для AI клиента (client/ai_client.py)
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from client.ai_client import AiClient
from openai import APIError, APIConnectionError
from config.config import app_config


class TestAiClientChat:
    """Тесты для методов AI клиента"""

    @pytest.mark.asyncio
    async def test_chat_success(self, mocker):
        """Успешный вызов API"""
        # Мокируем OpenAI клиент
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Ответ от AI"
        mock_client.chat.completions.create.return_value = mock_response
        
        mocker.patch('client.ai_client.AsyncOpenAI', return_value=mock_client)
        
        ai_client = AiClient()
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ]
        
        response = await ai_client.chat(messages)
        
        assert response == "Ответ от AI"
        mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_empty_response(self, mocker):
        """Обработка пустого ответа от API"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_client.chat.completions.create.return_value = mock_response
        
        mocker.patch('client.ai_client.AsyncOpenAI', return_value=mock_client)
        
        ai_client = AiClient()
        
        with pytest.raises(ValueError) as exc_info:
            await ai_client.chat([{"role": "user", "content": "Hello"}])
        
        assert "Empty response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_chat_with_empty_choices(self, mocker):
        """Обработка пустого списка choices"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = []
        mock_client.chat.completions.create.return_value = mock_response
        
        mocker.patch('client.ai_client.AsyncOpenAI', return_value=mock_client)
        
        ai_client = AiClient()
        
        with pytest.raises(ValueError) as exc_info:
            await ai_client.chat([{"role": "user", "content": "Hello"}])
        
        assert "Empty response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_chat_connection_error(self, mocker):
        """Обработка ошибки подключения"""
        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = APIConnectionError(
            message="Connection failed",
            request=httpx.Request("POST", "http://test"),
        )
        
        mocker.patch('client.ai_client.AsyncOpenAI', return_value=mock_client)
        
        ai_client = AiClient()
        
        with pytest.raises(APIConnectionError):
            await ai_client.chat([{"role": "user", "content": "Hello"}])

    @pytest.mark.asyncio
    async def test_chat_api_error(self, mocker):
        """Обработка API ошибки"""
        mock_client = AsyncMock()
        mock_error = APIError("API Error", request=httpx.Request("POST", "http://test"), body={})
        mock_error.status_code = 429  # Rate limited
        mock_client.chat.completions.create.side_effect = mock_error
        
        mocker.patch('client.ai_client.AsyncOpenAI', return_value=mock_client)
        
        ai_client = AiClient()
        
        with pytest.raises(APIError):
            await ai_client.chat([{"role": "user", "content": "Hello"}])

    @pytest.mark.asyncio
    async def test_chat_parameters(self, mocker):
        """Проверка параметров запроса к API"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_client.chat.completions.create.return_value = mock_response
        
        mocker.patch('client.ai_client.AsyncOpenAI', return_value=mock_client)
        
        ai_client = AiClient()
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hi"}
        ]
        
        await ai_client.chat(messages)
        
        # Проверяем вызванные параметры
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == app_config.openrouter_model
        assert call_kwargs["messages"] == messages
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["max_tokens"] == 2000
        assert call_kwargs["timeout"] == 30.0

    @pytest.mark.asyncio
    async def test_chat_long_response(self, mocker):
        """Обработка длинного ответа"""
        long_response = "А" * 10000
        
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = long_response
        mock_client.chat.completions.create.return_value = mock_response
        
        mocker.patch('client.ai_client.AsyncOpenAI', return_value=mock_client)
        
        ai_client = AiClient()
        
        response = await ai_client.chat([{"role": "user", "content": "Hello"}])
        
        assert response == long_response
        assert len(response) == 10000

    @pytest.mark.asyncio
    async def test_chat_with_special_characters(self, mocker):
        """Обработка спецсимволов в ответе"""
        special_response = "Ответ с символами: 🤖 <script>alert('xss')</script> \\n \\t"
        
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = special_response
        mock_client.chat.completions.create.return_value = mock_response
        
        mocker.patch('client.ai_client.AsyncOpenAI', return_value=mock_client)
        
        ai_client = AiClient()
        
        response = await ai_client.chat([{"role": "user", "content": "Hello"}])
        
        assert response == special_response


class TestAiClientInitialization:
    """Тесты инициализации AI клиента"""

    def test_ai_client_initialization(self, mocker):
        """Инициализация AI клиента с правильными параметрами"""
        mock_openai = mocker.patch('client.ai_client.AsyncOpenAI')
        
        ai_client = AiClient()
        
        # Проверяем, что AsyncOpenAI инициализирован правильно
        mock_openai.assert_called_once()
        call_kwargs = mock_openai.call_args[1]
        
        assert call_kwargs["base_url"] == "https://openrouter.ai/api/v1"
        assert "api_key" in call_kwargs
        assert "http_client" in call_kwargs

    def test_ai_client_has_correct_model(self):
        """Проверка, что установлена правильная модель"""
        with patch('client.ai_client.AsyncOpenAI'):
            ai_client = AiClient()
            
            assert ai_client.model == app_config.openrouter_model

    def test_ai_client_config(self):
        """Проверка конфигурации AI клиента"""
        with patch('client.ai_client.AsyncOpenAI'):
            ai_client = AiClient()
            
            assert hasattr(ai_client, 'client')
            assert hasattr(ai_client, 'model')
            assert ai_client.model is not None


class TestAiClientErrorHandling:
    """Тесты обработки ошибок"""

    @pytest.mark.asyncio
    async def test_chat_generic_exception(self, mocker):
        """Обработка неожиданной ошибки"""
        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = Exception("Unexpected error")
        
        mocker.patch('client.ai_client.AsyncOpenAI', return_value=mock_client)
        
        ai_client = AiClient()
        
        with pytest.raises(Exception) as exc_info:
            await ai_client.chat([{"role": "user", "content": "Hello"}])
        
        assert "Unexpected error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_chat_timeout(self, mocker):
        """Обработка таймаута"""
        import asyncio
        
        mock_client = AsyncMock()
        
        async def timeout_side_effect(*args, **kwargs):
            await asyncio.sleep(0.1)
            raise TimeoutError("Request timeout")
        
        mock_client.chat.completions.create.side_effect = timeout_side_effect
        
        mocker.patch('client.ai_client.AsyncOpenAI', return_value=mock_client)
        
        ai_client = AiClient()
        
        with pytest.raises(TimeoutError):
            await ai_client.chat([{"role": "user", "content": "Hello"}])
