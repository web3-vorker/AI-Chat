@echo off
REM =============================================
REM AI Chat - Quick Start Script для Windows
REM =============================================

echo.
echo  ╔════════════════════════════════════════╗
echo  ║     🚀 AI Chat - Быстрый старт        ║
echo  ╚════════════════════════════════════════╝
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Ошибка: Python не установлен или не в PATH
    echo    Установите Python 3.10+ с python.org
    pause
    exit /b 1
)

REM Активируем виртуальное окружение
echo 📦 Активирую виртуальное окружение...
if not exist ".venv" (
    echo ⚠️  Виртуальное окружение не найдено
    echo    Создаю новое окружение...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

REM Проверяем зависимости
echo 📥 Проверяю зависимости...
pip install -q -r requirements.txt >nul 2>&1
pip install -q itsdangerous >nul 2>&1

REM Проверяем .env файл
if not exist ".env" (
    echo ⚠️  Файл .env не найден
    echo    Создаю .env из .env.example...
    copy .env.example .env >nul
    echo.
    echo 📝 ВАЖНО! Отредактируйте файл .env:
    echo    1. Откройте .env в текстовом редакторе
    echo    2. Установите OPENROUTER_API_KEY
    echo    3. Получить ключ: https://openrouter.ai/
    echo.
    pause
)

REM Показываем информацию
echo.
echo  ╔════════════════════════════════════════╗
echo  ║          ✨ Успешно готово!            ║
echo  ╚════════════════════════════════════════╝
echo.
echo  Ваша система готова к запуску!
echo.
echo  🔧 Чтобы запустить приложение:
echo.
echo     Вариант 1 (рекомендуется):
echo     ========================
echo     1. Откройте 2 терминала
echo     2. В первом запустите:
echo        python -m uvicorn main:app --reload
echo     3. Во втором запустите:
echo        cd frontend && python serve.py
echo     4. Откройте http://127.0.0.1:5500 в браузере
echo.
echo     Вариант 2 (один клик):
echo     ======================
echo     Запустите run_dev.bat (если создан)
echo.
echo  📚 Дополнительно:
echo     - API документация: http://127.0.0.1:8000/docs
echo     - Frontend: http://127.0.0.1:5500
echo     - Чтение GETTING_STARTED.md для деталей
echo.
pause
