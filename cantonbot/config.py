import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

# Canton Network API Configuration
CANTON_API_BASE_URL = 'https://lighthouse.cantonloop.com/api'

# Price Update Interval (in seconds)
PRICE_UPDATE_INTERVAL = 60  # 1 минута

# Bybit API для получения цены CC/USDT
BYBIT_API_URL = 'https://api.bybit.com/v5/market/tickers'
BYBIT_SYMBOL = 'CCUSDT'

# Telegram Mini App URL
MINI_APP_URL = 'https://remindnation.tech/explorers/webapp/index.html'

