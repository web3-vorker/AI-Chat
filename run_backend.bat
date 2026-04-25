@echo off
REM Быстрый запуск бэкенда FastAPI

echo.
echo ╔═══════════════════════════════════════════════════╗
echo ║     🚀 Запуск бэкенда - AI Chat Server            ║
echo ╚═══════════════════════════════════════════════════╝
echo.

REM Активируем виртуальное окружение
if exist ".venv" (
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️  Ошибка: Виртуальное окружение не найдено
    echo    Запустите setup.bat первый раз
    pause
    exit /b 1
)

REM Проверяем .env
if not exist ".env" (
    echo ⚠️  Ошибка: Файл .env не найден
    echo    Создайте .env из .env.example
    pause
    exit /b 1
)

echo.
echo ✅ Все проверки пройдены
echo.
echo 🔗 Запускаю сервер...
echo.
echo    FastAPI документация: http://127.0.0.1:8000/docs
echo    API URL: http://127.0.0.1:8000
echo.
echo    Нажмите Ctrl+C для остановки
echo.

python -m uvicorn backend.main:app --reload
