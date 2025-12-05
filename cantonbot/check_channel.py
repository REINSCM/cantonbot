"""
Скрипт для проверки доступа бота к каналу
"""
import asyncio
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

async def check_channel():
    """Проверяет доступ бота к каналу"""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    if not TELEGRAM_CHANNEL_ID:
        print("❌ TELEGRAM_CHANNEL_ID не установлен!")
        return
    
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    print(f"🔍 Проверяю доступ к каналу: {TELEGRAM_CHANNEL_ID}")
    print("-" * 50)
    
    try:
        # Пытаемся получить информацию о чате
        chat = await bot.get_chat(chat_id=TELEGRAM_CHANNEL_ID)
        print(f"✅ Канал найден!")
        print(f"   Название: {chat.title}")
        print(f"   Тип: {chat.type}")
        print(f"   ID: {chat.id}")
        
        # Пытаемся отправить тестовое сообщение
        print("\n📤 Отправляю тестовое сообщение...")
        message = await bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text="✅ Тестовое сообщение от бота. Канал настроен правильно!"
        )
        print(f"✅ Сообщение успешно отправлено! (ID: {message.message_id})")
        print("\n🎉 Все работает! Бот может отправлять сообщения в канал.")
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Ошибка: {error_msg}")
        print("\n🔧 Возможные решения:")
        
        if "Chat not found" in error_msg:
            print("   1. Проверьте правильность ID канала в .env")
            print("   2. Убедитесь, что бот добавлен в канал")
            print("   3. Для публичного канала используйте: @channel_name")
            print("   4. Для приватного канала используйте числовой ID: -1001234567890")
            print("\n   Как получить ID канала:")
            print("   - Добавьте @userinfobot в канал")
            print("   - Отправьте любое сообщение в канал")
            print("   - Бот покажет ID канала")
        elif "not enough rights" in error_msg.lower() or "Forbidden" in error_msg:
            print("   1. Добавьте бота в канал как администратора")
            print("   2. Дайте боту право на отправку сообщений")
        else:
            print(f"   Неизвестная ошибка: {error_msg}")
    
    await bot.close()

if __name__ == '__main__':
    asyncio.run(check_channel())

