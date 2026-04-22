@echo off
REM Быстрый запуск фронтенда

echo.
echo ╔═══════════════════════════════════════════════════╗
echo ║     🎨 Запуск фронтенда - AI Chat UI              ║
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

REM Проверяем наличие файлов фронтенда
if not exist "frontend\index.html" (
    echo ⚠️  Ошибка: Файлы фронтенда не найдены
    pause
    exit /b 1
)

echo.
echo ✅ Все проверки пройдены
echo.
echo 🔗 Запускаю сервер фронтенда...
echo.
echo    Frontend URL: http://127.0.0.1:5500
echo    Backend URL: http://127.0.0.1:8000
echo.
echo    Убедитесь, что бэкенд запущен перед открытием!
echo    Нажмите Ctrl+C для остановки
echo.

cd frontend
python serve.py
