# Тесты для AI Chat Backend

## Структура тестов

```
tests/
├── conftest.py           # Fixtures и конфигурация pytest
├── test_routes.py        # Тесты API endpoints
├── test_service.py       # Тесты сервиса (бизнес-логика)
├── test_ai_client.py     # Тесты OpenRouter интеграции
└── test_models.py        # Тесты ORM моделей
```

## Требования

Все зависимости указаны в `requirements.txt`:
- pytest 9.0.3
- pytest-asyncio (для async тестов)
- pytest-mock (для мокирования)
- httpx (для тестирования API)

## Запуск тестов

### Все тесты
```bash
pytest
```

### С подробным выводом
```bash
pytest -v
```

### С покрытием кода
```bash
pytest --cov=. --cov-report=html
```

### Только тесты routes
```bash
pytest tests/test_routes.py -v
```

### Только тесты service
```bash
pytest tests/test_service.py -v
```

### Только тесты AI клиента
```bash
pytest tests/test_ai_client.py -v
```

### Только тесты моделей
```bash
pytest tests/test_models.py -v
```

### Запуск конкретного теста
```bash
pytest tests/test_routes.py::TestChatsEndpoints::test_get_chats_empty -v
```

## Тесты по категориям

### test_routes.py - API Endpoints (25+ тестов)

**TestChatsEndpoints** (7 тестов):
- Получение пустого списка чатов
- Получение списка чатов с данными
- Создание нового чата
- Создание нескольких чатов
- Удаление чата
- Удаление несуществующего чата
- Удаление с невалидным ID

**TestMessagesEndpoints** (9 тестов):
- Получение пустого списка сообщений
- Получение сообщений с данными
- Получение сообщений несуществующего чата
- Получение сообщений с невалидным ID
- Отправка сообщения (успех)
- Отправка пустого сообщения
- Отправка слишком длинного сообщения
- Отправка в несуществующий чат
- Обновление timestamp чата

**TestAuthenticationAndSecurity** (3 теста):
- Установка session_id в cookie
- Сохранение session_id между запросами
- Изоляция чатов между пользователями

**TestValidation** (3 теста):
- Проверка обязательного content
- Валидация типа content
- Обработка невалидного JSON

### test_service.py - Business Logic (20+ тестов)

**TestChatServiceChats** (7 тестов):
- Создание чата
- Получение чатов пользователя
- Получение пустого списка
- Сортировка по updated_at
- Удаление чата
- Удаление несуществующего
- Удаление чата с сообщениями

**TestChatServiceMessages** (6 тестов):
- Получение сообщений
- Отправка сообщения
- Сохранение в БД
- Ошибки при отправке

**TestChatServiceInternal** (5 тестов):
- _get_chat_or_404()
- _get_last_messages()
- Лимиты на сообщения

**TestSessionIdManagement** (2 теста):
- Создание новой session_id
- Переиспользование существующей

### test_ai_client.py - OpenRouter Integration (15+ тестов)

**TestAiClientChat** (7 тестов):
- Успешный вызов API
- Обработка пустого ответа
- Обработка пустого choices
- Ошибки подключения
- API ошибки
- Проверка параметров запроса
- Длинные ответы

**TestAiClientInitialization** (3 теста):
- Инициализация с правильными параметрами
- Правильная модель
- Конфигурация

**TestAiClientErrorHandling** (3 теста):
- Неожиданные ошибки
- Таймауты
- Разные типы исключений

### test_models.py - ORM Models (20+ тестов)

**TestChatModel** (6 тестов):
- Создание объекта Chat
- Дефолтное имя
- Генерация ID
- Имя таблицы
- Все атрибуты

**TestChatMessageModel** (6 тестов):
- Создание сообщения
- Разные роли (user, assistant, system)
- Длинный контент
- Спецсимволы
- Имя таблицы
- Все атрибуты

**TestChatAndMessageRelationship** (3 теста):
- Связь Chat -> ChatMessage
- Связь ChatMessage -> Chat
- Каскадное удаление

**TestModelValidation** (3 теста):
- Пустой контент
- Null роль
- Временные метки

**TestModelIndexes** (2 теста):
- Индекс user_id
- Индекс chat_id

## Конфигурация pytest

Конфигурация в `pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

## Fixtures

### Database Fixtures (conftest.py)
- `event_loop` - asyncio event loop для всей сессии
- `test_engine` - тестовая БД (in-memory SQLite)
- `test_session_maker` - фабрика сессий
- `test_session` - новая сессия для каждого теста (с очисткой)

### API Fixtures (conftest.py)
- `async_client` - FastAPI тестовый клиент с overrides зависимостей

### Test Data Fixtures (conftest.py)
- `test_user_id` - ID тестового пользователя
- `test_chat` - тестовый чат в БД
- `test_messages` - тестовые сообщения в БД
- `mock_ai_client` - мокированный AI клиент

## Особенности

### Async/Await
- Все тесты используют `@pytest.mark.asyncio`
- asyncio_mode = auto в pytest.ini
- Fixtures для async/await

### Database Cleanup
- В-памяти SQLite база для быстрых тестов
- Автоматическая очистка после каждого теста
- Cascade delete настроен в моделях

### Mocking
- pytest-mock для создания mock объектов
- AsyncMock для async методов
- Моки для OpenRouter API

### Dependency Injection
- FastAPI dependency_overrides для override get_session
- Каждый тест получает свою сессию

## Примеры

### Запуск с покрытием кода
```bash
pip install pytest-cov
pytest --cov=. --cov-report=html
# Результаты в htmlcov/index.html
```

### Запуск в CI/CD
```bash
pytest -v --tb=short --junit-xml=test-results.xml
```

### Запуск с выводом выполнения
```bash
pytest -v -s
```

## Troubleshooting

### ImportError: No module named 'main'
```bash
# Убедитесь, что находитесь в корневой папке проекта
cd /path/to/AiChat
pytest
```

### Database locked
```bash
# Может произойти при параллельном запуске
pytest -n0  # Отключить параллельное выполнение
```

### Timeout в async тестах
```bash
# Увеличить timeout в pytest.ini
# Или явно указать в @pytest.mark.asyncio(timeout=10)
```

## Coverage

Текущее покрытие кода тестами:
- `routers/routes.py` - 100%
- `services/service.py` - 95%+
- `client/ai_client.py` - 90%+
- `models/chat.py` - 85%+

Для увеличения покрытия:
```bash
pytest --cov=. --cov-report=term-missing
```
