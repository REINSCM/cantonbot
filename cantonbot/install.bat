@echo off
echo Установка зависимостей для Canton Network Monitor Bot...
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
echo.
echo Установка завершена!
echo Не забудьте создать файл .env с вашими токенами!
pause

