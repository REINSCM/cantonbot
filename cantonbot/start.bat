@echo off
echo Запуск Canton Network Monitor Bot...
if exist .venv\Scripts\python.exe (
    echo Используется виртуальное окружение...
    .venv\Scripts\python.exe main.py
) else (
    echo ВНИМАНИЕ: Виртуальное окружение не найдено!
    echo Убедитесь, что вы активировали виртуальное окружение:
    echo   .venv\Scripts\activate
    echo или используйте: .venv\Scripts\python.exe main.py
    echo.
    echo Используем системный Python (может не работать JobQueue)...
    py main.py
)
pause

