"""
Модуль для хранения информации о подписках пользователей
"""
import json
import os
from pathlib import Path

# Путь к файлу с данными о пользователях
SUBSCRIPTIONS_FILE = Path("user_subscriptions.json")

def load_subscriptions() -> dict:
    """Загружает данные о подписках пользователей из файла"""
    if not SUBSCRIPTIONS_FILE.exists():
        return {}
    
    try:
        with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_subscriptions(subscriptions: dict):
    """Сохраняет данные о подписках пользователей в файл"""
    try:
        with open(SUBSCRIPTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(subscriptions, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"Ошибка сохранения подписок: {e}")

def is_user_verified(user_id: int) -> bool:
    """Проверяет, прошел ли пользователь проверку подписки"""
    subscriptions = load_subscriptions()
    return subscriptions.get(str(user_id), {}).get('verified', False)

def set_user_verified(user_id: int, verified: bool = True):
    """Устанавливает статус проверки подписки для пользователя"""
    subscriptions = load_subscriptions()
    if str(user_id) not in subscriptions:
        subscriptions[str(user_id)] = {}
    subscriptions[str(user_id)]['verified'] = verified
    save_subscriptions(subscriptions)

