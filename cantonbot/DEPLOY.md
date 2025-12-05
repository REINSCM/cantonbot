# Инструкция по развертыванию бота на сервере

## Файлы для переноса на сервер

### Обязательные файлы:
- `main.py` - основной файл бота
- `canton_api.py` - модуль для работы с Canton Network API
- `price_fetcher.py` - модуль для получения цены CC/USDT
- `config.py` - конфигурация
- `user_subscriptions.py` - модуль для хранения подписок пользователей
- `requirements.txt` - зависимости Python

### Файлы, которые создадутся автоматически:
- `.env` - переменные окружения (создать на сервере)
- `user_subscriptions.json` - данные о подписках пользователей (создастся автоматически)

### Файлы, которые НЕ нужно переносить:
- `__pycache__/` - кэш Python
- `*.pyc`, `*.pyo` - скомпилированные файлы
- `.env` - переменные окружения (создать заново на сервере)
- `install.bat`, `start.bat` - скрипты для Windows
- `check_channel.py` - утилита для проверки (опционально)
- `README.md`, `DEPLOY.md` - документация (опционально)
- `webapp/` - веб-приложение (если не используется)

## Команды для развертывания на Linux сервере

### 1. Подключение к серверу
```bash
ssh user@your-server-ip
```

### 2. Установка Python и pip (если не установлены)
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv -y

# CentOS/RHEL
sudo yum install python3 python3-pip -y
```

### 3. Создание директории для бота
```bash
mkdir -p ~/cantonbot
cd ~/cantonbot
```

### 4. Перенос файлов на сервер

#### Вариант 1: Через SCP (с локального компьютера)
```bash
# С локального компьютера выполните:
scp main.py canton_api.py price_fetcher.py config.py user_subscriptions.py requirements.txt user@your-server-ip:~/cantonbot/
```

#### Вариант 2: Через Git (если есть репозиторий)
```bash
# На сервере:
cd ~/cantonbot
git clone <your-repo-url> .
# Или если уже есть репозиторий:
git pull
```

#### Вариант 3: Через SFTP/FTP клиент
Перенесите файлы через FileZilla, WinSCP или другой FTP клиент.

### 5. Создание виртуального окружения
```bash
cd ~/cantonbot
python3 -m venv venv
source venv/bin/activate
```

### 6. Установка зависимостей
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 7. Создание файла .env
```bash
nano .env
```

Добавьте в файл:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=your_channel_id_here
```

Сохраните файл (Ctrl+O, Enter, Ctrl+X)

### 8. Тестовый запуск
```bash
python3 main.py
```

Если все работает, остановите бота (Ctrl+C).

### 9. Настройка автозапуска через systemd

Создайте файл сервиса:
```bash
sudo nano /etc/systemd/system/cantonbot.service
```

Добавьте следующее содержимое:
```ini
[Unit]
Description=Canton Network Monitor Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/cantonbot
Environment="PATH=/home/your_username/cantonbot/venv/bin"
ExecStart=/home/your_username/cantonbot/venv/bin/python3 /home/your_username/cantonbot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Важно:** Замените `your_username` на ваше имя пользователя на сервере!

### 10. Активация и запуск сервиса
```bash
# Перезагрузить конфигурацию systemd
sudo systemctl daemon-reload

# Включить автозапуск при загрузке системы
sudo systemctl enable cantonbot

# Запустить бота
sudo systemctl start cantonbot

# Проверить статус
sudo systemctl status cantonbot

# Просмотр логов
sudo journalctl -u cantonbot -f
```

### 11. Управление ботом

```bash
# Остановить бота
sudo systemctl stop cantonbot

# Перезапустить бота
sudo systemctl restart cantonbot

# Просмотр логов
sudo journalctl -u cantonbot -n 50

# Просмотр логов в реальном времени
sudo journalctl -u cantonbot -f
```

## Альтернативный вариант: Запуск через screen/tmux

Если не хотите использовать systemd, можно запустить через screen или tmux:

### Через screen:
```bash
# Установить screen (если не установлен)
sudo apt install screen -y

# Создать новую сессию
screen -S cantonbot

# Активировать виртуальное окружение и запустить бота
cd ~/cantonbot
source venv/bin/activate
python3 main.py

# Отключиться от сессии: Ctrl+A, затем D
# Вернуться к сессии: screen -r cantonbot
```

### Через tmux:
```bash
# Установить tmux (если не установлен)
sudo apt install tmux -y

# Создать новую сессию
tmux new -s cantonbot

# Активировать виртуальное окружение и запустить бота
cd ~/cantonbot
source venv/bin/activate
python3 main.py

# Отключиться от сессии: Ctrl+B, затем D
# Вернуться к сессии: tmux attach -t cantonbot
```

## Проверка работы бота

1. Отправьте команду `/start` боту в Telegram
2. Проверьте логи: `sudo journalctl -u cantonbot -f` (для systemd) или `screen -r cantonbot` (для screen)
3. Убедитесь, что бот отвечает на команды

## Обновление бота

```bash
cd ~/cantonbot

# Если используете Git:
git pull

# Если переносите файлы вручную:
# Замените обновленные файлы через scp/sftp

# Перезапустите бота
sudo systemctl restart cantonbot
# или для screen/tmux: остановите (Ctrl+C) и запустите заново
```

## Устранение проблем

### Бот не запускается
```bash
# Проверьте логи
sudo journalctl -u cantonbot -n 100

# Проверьте, что файл .env существует и содержит правильные токены
cat .env

# Проверьте, что виртуальное окружение активировано и зависимости установлены
source venv/bin/activate
pip list
```

### Бот не отвечает
- Проверьте, что токен бота правильный в `.env`
- Убедитесь, что бот запущен: `sudo systemctl status cantonbot`
- Проверьте интернет-соединение сервера

### Ошибки с правами доступа
```bash
# Убедитесь, что файлы принадлежат правильному пользователю
sudo chown -R your_username:your_username ~/cantonbot
```

## Безопасность

1. **Не коммитьте `.env` файл в Git** - он уже в `.gitignore`
2. **Используйте сильные пароли** для SSH доступа
3. **Настройте firewall** для ограничения доступа к серверу
4. **Регулярно обновляйте** зависимости: `pip install --upgrade -r requirements.txt`

