"""
Модуль для получения цены CC/USDT
"""
import requests
from typing import Optional, Dict
from config import BYBIT_API_URL, BYBIT_SYMBOL


class PriceFetcher:
    """Класс для получения цены CC/USDT с различных бирж"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_cc_price_from_coingecko(self) -> Optional[Dict]:
        """Пытается получить цену с CoinGecko"""
        try:
            coin_id = 'canton-network'  # Правильный ID токена Canton Network на CoinGecko
            
            # Получаем базовую информацию о цене
            url = 'https://api.coingecko.com/api/v3/simple/price'
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_high': 'true',
                'include_24hr_low': 'true'
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if coin_id in data and 'usd' in data[coin_id]:
                price_data = data[coin_id]
                price = float(price_data.get('usd', 0))
                
                if price > 0:
                    change_24h = float(price_data.get('usd_24h_change', 0) or 0)
                    volume_24h = float(price_data.get('usd_24h_vol', 0) or 0)
                    high_24h = float(price_data.get('usd_24h_high', 0) or price * 1.02)
                    low_24h = float(price_data.get('usd_24h_low', 0) or price * 0.98)
                    
                    # Если high/low не получены, вычисляем приблизительно
                    if high_24h == 0 or high_24h < price:
                        high_24h = price * (1 + abs(change_24h) / 100) if change_24h > 0 else price * 1.01
                    if low_24h == 0 or low_24h > price:
                        low_24h = price * (1 - abs(change_24h) / 100) if change_24h < 0 else price * 0.99
                    
                    return {
                        'symbol': 'CCUSDT',
                        'last_price': price,
                        'bid_price': price * 0.9995,  # Приблизительное значение (0.05% спред)
                        'ask_price': price * 1.0005,  # Приблизительное значение (0.05% спред)
                        'volume_24h': volume_24h,
                        'price_change_24h': change_24h,
                        'high_24h': high_24h,
                        'low_24h': low_24h,
                    }
        except Exception as e:
            print(f"Ошибка при получении цены с CoinGecko: {e}")
        return None
    
    def get_cc_price_from_binance(self) -> Optional[Dict]:
        """Пытается получить цену с Binance"""
        try:
            url = 'https://api.binance.com/api/v3/ticker/24hr'
            params = {'symbol': 'CCUSDT'}
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'lastPrice' in data:
                return {
                    'symbol': 'CCUSDT',
                    'last_price': float(data.get('lastPrice', 0)),
                    'bid_price': float(data.get('bidPrice', 0)),
                    'ask_price': float(data.get('askPrice', 0)),
                    'volume_24h': float(data.get('volume', 0)),
                    'price_change_24h': float(data.get('priceChangePercent', 0)),
                    'high_24h': float(data.get('highPrice', 0)),
                    'low_24h': float(data.get('lowPrice', 0)),
                }
        except Exception as e:
            print(f"Ошибка при получении цены с Binance: {e}")
        return None
    
    def get_cc_price_from_bybit(self) -> Optional[Dict]:
        """Пытается получить цену с Bybit"""
        try:
            params = {'category': 'spot', 'symbol': BYBIT_SYMBOL}
            response = self.session.get(BYBIT_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('retCode') == 0 and data.get('result'):
                result = data['result']
                if 'list' in result and len(result['list']) > 0:
                    ticker = result['list'][0]
                    return {
                        'symbol': ticker.get('symbol', BYBIT_SYMBOL),
                        'last_price': float(ticker.get('lastPrice', 0)),
                        'bid_price': float(ticker.get('bid1Price', 0)),
                        'ask_price': float(ticker.get('ask1Price', 0)),
                        'volume_24h': float(ticker.get('volume24h', 0)),
                        'price_change_24h': float(ticker.get('price24hPcnt', 0)) * 100,
                        'high_24h': float(ticker.get('highPrice24h', 0)),
                        'low_24h': float(ticker.get('lowPrice24h', 0)),
                    }
        except Exception as e:
            print(f"Ошибка при получении цены с Bybit: {e}")
        return None
    
    def get_cc_price(self) -> Optional[Dict]:
        """
        Получает текущую цену CC/USDT с различных источников
        Пробует несколько API с fallback механизмом
        Возвращает словарь с данными о цене или None в случае ошибки
        """
        # Пробуем CoinGecko первым (обычно не блокирует по геолокации)
        price_data = self.get_cc_price_from_coingecko()
        if price_data and price_data.get('last_price', 0) > 0:
            return price_data
        
        # Если CoinGecko не сработал, пробуем Binance
        price_data = self.get_cc_price_from_binance()
        if price_data and price_data.get('last_price', 0) > 0:
            return price_data
        
        # Если Binance не сработал, пробуем Bybit
        price_data = self.get_cc_price_from_bybit()
        if price_data and price_data.get('last_price', 0) > 0:
            return price_data
        
        return None
    
    def format_price_message(self, price_data: Dict) -> str:
        """Formats price message for sending to Telegram (full information)"""
        if not price_data:
            return ("❌ Failed to get CC/USDT price\n\n"
                   "Possible reasons:\n"
                   "• Geographic restrictions on exchange APIs\n"
                   "• CC/USDT token may be unavailable on selected exchanges\n"
                   "• Temporary connection issues\n\n"
                   "Please try again later or check price at https://ru.tradingview.com/chart/?symbol=BYBIT%3ACCUSDT")
        
        change_24h = price_data.get('price_change_24h', 0)
        change_emoji = "📈" if change_24h >= 0 else "📉"
        
        message = f"{change_emoji} <b>CC/USDT Price</b>\n\n"
        message += f"💰 <b>Current Price:</b> ${price_data['last_price']:.6f}\n"
        message += f"📊 <b>24h Change:</b> {change_24h:+.2f}%\n"
        message += f"⬆️ <b>24h High:</b> ${price_data['high_24h']:.6f}\n"
        message += f"⬇️ <b>24h Low:</b> ${price_data['low_24h']:.6f}\n"
        message += f"💵 <b>Bid:</b> ${price_data['bid_price']:.6f}\n"
        message += f"💵 <b>Ask:</b> ${price_data['ask_price']:.6f}\n"
        message += f"📦 <b>24h Volume:</b> {price_data['volume_24h']:,.2f} CC\n"
        
        return message
    
    def format_price_simple(self, price_data: Dict) -> str:
        """Formats only price for sending to channel (without additional text)"""
        if not price_data:
            return None
        
        price = price_data.get('last_price', 0)
        if price <= 0:
            return None
        
        # Только цена, без дополнительных символов и надписей
        return f"${price:.6f}"

