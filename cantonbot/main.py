"""
Telegram bot for monitoring Canton Network
"""
import asyncio
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from telegram.constants import ParseMode
from telegram.error import NetworkError, TimedOut, RetryAfter, BadRequest, Forbidden
from telegram.constants import ChatMemberStatus

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, PRICE_UPDATE_INTERVAL, MINI_APP_URL
from canton_api import CantonAPI
from price_fetcher import PriceFetcher
from user_subscriptions import is_user_verified, set_user_verified

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize API clients
canton_api = CantonAPI()
price_fetcher = PriceFetcher()

# Maximum message length in Telegram (4096 characters, leaving some margin)
MAX_MESSAGE_LENGTH = 4000

# Explorer URL
EXPLORER_URL = "https://remindnation.tech/explorer"

# Channel for subscription check
REQUIRED_CHANNEL = "@remindnation"
X_LINK = "https://x.com/remindnation"


def get_main_keyboard():
    """Creates main keyboard with command buttons"""
    keyboard = [
        [
            KeyboardButton("📊 Stats"),
            KeyboardButton("💰 Price")
        ],
        [
            KeyboardButton("🔐 Validators"),
            KeyboardButton("🔄 Rounds")
        ],
        [
            KeyboardButton("🏛️ Governance"),
            KeyboardButton("ℹ️ Help")
        ],
        [
            KeyboardButton("🌐 Explorer", web_app=WebAppInfo(url=MINI_APP_URL))
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def send_long_message(update: Update, message: str, parse_mode: ParseMode = ParseMode.HTML):
    """
    Sends a long message, splitting it into parts if necessary
    """
    if len(message) <= MAX_MESSAGE_LENGTH:
        try:
            await update.message.reply_text(message, parse_mode=parse_mode)
        except (NetworkError, TimedOut) as e:
            logger.warning(f"Failed to send message: {e}")
            # Try again after a short delay
            try:
                await asyncio.sleep(1)
                await update.message.reply_text(message, parse_mode=parse_mode)
            except Exception:
                logger.error("Retry attempt to send message also failed")
        return
    
    # Split message into parts
    parts = []
    current_part = ""
    lines = message.split('\n')
    
    for line in lines:
        # If the line itself is too long, split it
        if len(line) > MAX_MESSAGE_LENGTH:
            # Save current part if exists
            if current_part:
                parts.append(current_part.strip())
                current_part = ""
            # Split long line into parts
            while len(line) > MAX_MESSAGE_LENGTH:
                parts.append(line[:MAX_MESSAGE_LENGTH])
                line = line[MAX_MESSAGE_LENGTH:]
            if line:
                current_part = line + '\n'
        # If adding the line won't exceed the limit
        elif len(current_part) + len(line) + 1 <= MAX_MESSAGE_LENGTH:
            current_part += line + '\n'
        else:
            # Save current part and start new one
            if current_part:
                parts.append(current_part.strip())
            current_part = line + '\n'
    
    # Add last part
    if current_part:
        parts.append(current_part.strip())
    
    # Send all parts
    for i, part in enumerate(parts, 1):
        if len(parts) > 1:
            part = f"<i>(Part {i} of {len(parts)})</i>\n\n{part}"
        
        try:
            await update.message.reply_text(part, parse_mode=parse_mode)
        except (NetworkError, TimedOut) as e:
            logger.warning(f"Failed to send part {i} of {len(parts)}: {e}")
            # Try again after a short delay
            try:
                await asyncio.sleep(2)
                await update.message.reply_text(part, parse_mode=parse_mode)
            except Exception:
                logger.error(f"Retry attempt to send part {i} also failed")
                # Continue sending next parts
        
        # Small delay between messages
        await asyncio.sleep(0.5)


async def check_channel_subscription(bot, user_id: int, channel: str) -> bool:
    """Проверяет, подписан ли пользователь на канал"""
    try:
        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        # Пользователь подписан, если его статус не "left" или "kicked"
        return member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]
    except (BadRequest, Forbidden) as e:
        logger.warning(f"Ошибка при проверке подписки на канал {channel}: {e}")
        # Если бот не может проверить подписку (например, не добавлен в канал), считаем что пользователь подписан
        return True
    except Exception as e:
        logger.error(f"Неожиданная ошибка при проверке подписки: {e}")
        return False


def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для проверки подписки"""
    keyboard = [
        [
            InlineKeyboardButton("📢 Subscribe to the channel", url=f"https://t.me/{REQUIRED_CHANNEL[1:]}")
        ],
        [
            InlineKeyboardButton("🐦 Subscribe to X", url=X_LINK)
        ],
        [
            InlineKeyboardButton("✅ Check subscription", callback_data="check_subscription")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command"""
    user_id = update.effective_user.id
    
    # Проверяем, прошел ли пользователь проверку подписки
    if not is_user_verified(user_id):
        # Показываем сообщение с требованием подписки
        subscription_message = f"""
🔐 <b>Welcome to RemindView!</b>

To use the bot, you need to subscribe to our official resources:

📢 <b>Telegram Channel:</b> {REQUIRED_CHANNEL}
🐦 <b>X (Twitter):</b> <a href="{X_LINK}">@remindnation</a>

After subscribing, click the "✅ Check Subscription" button below.
"""
        await update.message.reply_text(
            subscription_message,
            parse_mode=ParseMode.HTML,
            reply_markup=get_subscription_keyboard(),
            disable_web_page_preview=False
        )
        return
    
    # Если пользователь уже прошел проверку, показываем обычное приветствие
    welcome_message = """
🤖 <b>Welcome to RemindView</b>

<b>Available Commands:</b>
📊 /stats - Network statistics
💰 /price - Current CC/USDT price
🔐 /validators - Validators list
🔄 /rounds - Rounds list
🏛️ /governance - Governance list
ℹ️ /help - Command help

<b>For detailed information:</b>
/governance_id &lt;id&gt; - Governance details
/party &lt;id&gt; - Party information
/party_tx &lt;id&gt; - Party transactions

<b>📢 Official Resources:</b>
📢 Channel - @remindnation
🐦 X - <a href="https://x.com/remindnation">https://x.com/remindnation</a>
🌐 Website - <a href="https://remindnation.tech">https://remindnation.tech</a>
"""
    # Создаем комбинированную клавиатуру: обычная + inline кнопка эксплорера
    # В Telegram нельзя использовать оба типа одновременно, поэтому отправляем два сообщения
    # Но inline кнопку добавляем к основному сообщению
    explorer_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Explorer", web_app=WebAppInfo(url=MINI_APP_URL))]
    ])
    
    await update.message.reply_text(
        welcome_message, 
        parse_mode=ParseMode.HTML,
        reply_markup=explorer_keyboard,
        disable_web_page_preview=True
    )
    # Отправляем обычную клавиатуру отдельным сообщением
    await update.message.reply_text(
        " ",
        reply_markup=get_main_keyboard()
    )


async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик для кнопки проверки подписки"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Проверяем подписку на канал
    is_subscribed = await check_channel_subscription(context.bot, user_id, REQUIRED_CHANNEL)
    
    if is_subscribed:
        # Пользователь подписан - сохраняем статус и показываем приветствие
        set_user_verified(user_id, True)
        
        welcome_message = """
✅ <b>Access granted</b>

🤖 <b>Welcome to RemindView!</b>

<b>Available Commands:</b>
📊 /stats - Network statistics
💰 /price - Current CC/USDT price
🔐 /validators - Validators list
🔄 /rounds - Rounds list
🏛️ /governance - Governance list
ℹ️ /help - Command help

<b>For detailed information:</b>
/governance_id &lt;id&gt; - Governance details
/party &lt;id&gt; - Party information
/party_tx &lt;id&gt; - Party transactions

<b>📢 Official Resources:</b>
📢 Channel - @remindnation
🐦 X - <a href="https://x.com/remindnation">https://x.com/remindnation</a>
🌐 Website - <a href="https://remindnation.tech">https://remindnation.tech</a>
"""
        # Создаем inline клавиатуру с кнопкой эксплорера
        explorer_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Explorer", web_app=WebAppInfo(url=MINI_APP_URL))]
        ])
        
        await query.edit_message_text(
            welcome_message,
            parse_mode=ParseMode.HTML,
            reply_markup=explorer_keyboard,
            disable_web_page_preview=True
        )
        # Отправляем обычную клавиатуру отдельным сообщением
        await query.message.reply_text(
            " ",
            reply_markup=get_main_keyboard()
        )
    else:
        # Пользователь не подписан
        await query.answer(
            "❌ You are not subscribed to the channel. Please subscribe and try again.",
            show_alert=True
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /help command"""
    help_text = """
📖 <b>Command Help</b>

<b>Main Commands:</b>
📊 /stats - Get Canton Network statistics
💰 /price - Get current CC/USDT price
🔐 /validators - View validators (opens explorer)
🔄 /rounds - View rounds (opens explorer)
🏛️ /governance - View governance (opens explorer)

<b>Commands with Parameters:</b>
/governance_id &lt;id&gt; - Governance details by ID
/party &lt;id&gt; - Party information by ID
/party_tx &lt;id&gt; [limit] - Party transactions (default limit=20)

<b>📢 Official Resources:</b>
📢 Channel - @remindnation
🐦 X - https://x.com/remindnation
🌐 Website - https://remindnation.tech
"""
    await update.message.reply_text(
        help_text, 
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard()
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /stats command"""
    try:
        await update.message.reply_text("⏳ Getting network statistics...", reply_markup=get_main_keyboard())
    except (NetworkError, TimedOut):
        pass
    
    stats = canton_api.get_stats()
    message = canton_api.format_stats(stats)
    await send_long_message(update, message)


async def validators_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /validators command"""
    try:
        await update.message.reply_text("⏳ Getting validators statistics...", reply_markup=get_main_keyboard())
    except (NetworkError, TimedOut):
        pass
    
    validators = canton_api.get_validators()
    message = canton_api.format_validators(validators)
    message += f"\n\n🔗 <a href=\"{EXPLORER_URL}\">View All Validators in Explorer</a>"
    
    await update.message.reply_text(
        message, 
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard(),
        disable_web_page_preview=False
    )


async def rounds_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /rounds command"""
    try:
        await update.message.reply_text("⏳ Getting rounds...", reply_markup=get_main_keyboard())
    except (NetworkError, TimedOut):
        pass
    
    rounds = canton_api.get_rounds(page=1, limit=5)
    message = canton_api.format_rounds(rounds, limit=5)
    message += f"\n🔗 <a href=\"{EXPLORER_URL}\">View All Rounds in Explorer</a>"
    
    await update.message.reply_text(
        message, 
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard(),
        disable_web_page_preview=False
    )


async def governance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /governance command"""
    try:
        await update.message.reply_text("⏳ Getting governance...", reply_markup=get_main_keyboard())
    except (NetworkError, TimedOut):
        pass
    
    governance = canton_api.get_governance(page=1, limit=5)
    message = canton_api.format_governance(governance, limit=5)
    message += f"\n🔗 <a href=\"{EXPLORER_URL}\">View All Governance in Explorer</a>"
    
    await update.message.reply_text(
        message, 
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard(),
        disable_web_page_preview=False
    )


async def governance_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /governance_id command"""
    if not context.args:
        await update.message.reply_text(
            "❌ Please specify governance ID. Example: /governance_id 123",
            reply_markup=get_main_keyboard()
        )
        return
    
    governance_id = context.args[0]
    try:
        await update.message.reply_text(f"⏳ Getting governance details {governance_id}...", reply_markup=get_main_keyboard())
    except (NetworkError, TimedOut):
        pass
    
    details = canton_api.get_governance_details(governance_id)
    message = canton_api.format_governance_details(details)
    
    await send_long_message(update, message)


async def party_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /party command"""
    if not context.args:
        await update.message.reply_text(
            "❌ Please specify party ID. Example: /party party123",
            reply_markup=get_main_keyboard()
        )
        return
    
    party_id = context.args[0]
    try:
        await update.message.reply_text(f"⏳ Getting party information {party_id}...", reply_markup=get_main_keyboard())
    except (NetworkError, TimedOut):
        pass
    
    info = canton_api.get_party_info(party_id)
    message = canton_api.format_party_info(info)
    
    await send_long_message(update, message)


async def party_tx_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /party_tx command"""
    if not context.args:
        await update.message.reply_text(
            "❌ Please specify party ID. Example: /party_tx party123",
            reply_markup=get_main_keyboard()
        )
        return
    
    party_id = context.args[0]
    limit = int(context.args[1]) if len(context.args) > 1 and context.args[1].isdigit() else 20
    
    try:
        await update.message.reply_text(f"⏳ Getting party transactions {party_id}...", reply_markup=get_main_keyboard())
    except (NetworkError, TimedOut):
        pass
    
    transactions = canton_api.get_party_transactions(party_id, limit=limit)
    message = canton_api.format_party_transactions(transactions, limit=limit)
    
    await send_long_message(update, message)


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /price command"""
    try:
        await update.message.reply_text("⏳ Getting CC/USDT price...", reply_markup=get_main_keyboard())
    except (NetworkError, TimedOut):
        pass
    
    price_data = price_fetcher.get_cc_price()
    message = price_fetcher.format_price_message(price_data)
    await update.message.reply_text(message, parse_mode=ParseMode.HTML, reply_markup=get_main_keyboard())


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for text messages (keyboard buttons)"""
    text = update.message.text
    
    if text == "📊 Stats":
        await stats_command(update, context)
    elif text == "💰 Price":
        await price_command(update, context)
    elif text == "🔐 Validators":
        await validators_command(update, context)
    elif text == "🔄 Rounds":
        await rounds_command(update, context)
    elif text == "🏛️ Governance":
        await governance_command(update, context)
    elif text == "ℹ️ Help":
        await help_command(update, context)
    else:
        await update.message.reply_text(
            "❓ Unknown command. Use /help to see available commands.",
            reply_markup=get_main_keyboard()
        )


async def send_price_to_channel(context: ContextTypes.DEFAULT_TYPE):
    """Sends CC/USDT price to channel"""
    if not TELEGRAM_CHANNEL_ID:
        logger.warning("TELEGRAM_CHANNEL_ID not set, skipping channel send")
        return
    
    try:
        logger.debug("Starting price fetch for channel...")
        price_data = price_fetcher.get_cc_price()
        if price_data:
            # Use simple format - only price
            message = price_fetcher.format_price_simple(price_data)
            
            if message:
                try:
                    await context.bot.send_message(
                        chat_id=TELEGRAM_CHANNEL_ID,
                        text=message
                    )
                    logger.info(f"✅ Price successfully sent to channel {TELEGRAM_CHANNEL_ID}: {message}")
                except BadRequest as e:
                    error_msg = str(e)
                    if "Chat not found" in error_msg:
                        logger.error(f"❌ Channel not found! Check:")
                        logger.error(f"   1. Channel ID in .env: {TELEGRAM_CHANNEL_ID}")
                        logger.error(f"   2. Bot added to channel as administrator")
                        logger.error(f"   3. Correct ID format (numeric ID or @username)")
                        logger.error(f"   Use @userinfobot or @getidsbot to get channel ID")
                    else:
                        logger.error(f"Request error when sending to channel: {e}")
                except Forbidden as e:
                    logger.error(f"❌ Access denied! Bot cannot send messages to channel.")
                    logger.error(f"   Make sure bot is added to channel as administrator.")
                except NetworkError as e:
                    logger.warning(f"⚠️ Network error when sending to channel: {e}")
                except TimedOut as e:
                    logger.warning(f"⚠️ Timeout when sending to channel: {e}")
                except Exception as e:
                    logger.error(f"❌ Error sending message to channel: {e}")
            else:
                logger.warning("Failed to format price message")
        else:
            logger.warning("Failed to get price for channel send")
    except Exception as e:
        logger.error(f"Error getting/sending price to channel: {e}", exc_info=e)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Error handler"""
    error = context.error
    error_type = type(error).__name__
    
    # Handle network errors
    if isinstance(error, NetworkError):
        logger.warning(f"Network error: {error}. Attempting to reconnect...")
        # Don't log as critical error, as these are temporary network issues
        return
    
    # Handle timeout errors
    if isinstance(error, TimedOut):
        logger.warning(f"Timeout when executing request: {error}")
        return
    
    # Handle rate limit errors
    if isinstance(error, RetryAfter):
        logger.warning(f"Rate limit exceeded. Retry after {error.retry_after} seconds")
        return
    
    # If it's a "Text is too long" error, try to send message in parts
    if "Text is too long" in str(error) and update and hasattr(update, 'message') and update.message:
        try:
            # Try to get original message from context
            if hasattr(context, 'user_data') and 'last_message' in context.user_data:
                message = context.user_data['last_message']
                await send_long_message(update, message)
                logger.info("Long message successfully sent in parts")
        except Exception as e:
            logger.error(f"Failed to send long message in parts: {e}")
    
    # Log other errors
    logger.error(f"Exception while handling an update ({error_type}): {error}", exc_info=error)
    
    # Try to send error message to user (if possible)
    if update and hasattr(update, 'message') and update.message:
        try:
            error_msg = "⚠️ An error occurred while processing your request. Please try again later."
            if isinstance(error, NetworkError):
                error_msg = "⚠️ Network issues. Please try again later."
            elif isinstance(error, TimedOut):
                error_msg = "⚠️ Request timeout. Please try again later."
            
            await update.message.reply_text(error_msg, reply_markup=get_main_keyboard())
        except Exception:
            # If we can't send message, just log
            pass


def main():
    """Main bot startup function"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set! Create .env file and add token.")
        return
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("validators", validators_command))
    application.add_handler(CommandHandler("rounds", rounds_command))
    application.add_handler(CommandHandler("governance", governance_command))
    application.add_handler(CommandHandler("governance_id", governance_id_command))
    application.add_handler(CommandHandler("party", party_command))
    application.add_handler(CommandHandler("party_tx", party_tx_command))
    application.add_handler(CommandHandler("price", price_command))
    
    # Handler for callback queries (subscription check button)
    application.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$"))
    
    # Handler for text messages (keyboard buttons)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Setup periodic price sending to channel
    if TELEGRAM_CHANNEL_ID:
        job_queue = application.job_queue
        logger.debug(f"JobQueue object: {job_queue}, type: {type(job_queue)}")
        
        if job_queue is not None:
            try:
                job_queue.run_repeating(
                    send_price_to_channel,
                    interval=PRICE_UPDATE_INTERVAL,
                    first=10  # First send after 10 seconds from startup
                )
                logger.info(f"✅ Automatic price sending to channel configured")
                logger.info(f"   Channel: {TELEGRAM_CHANNEL_ID}")
                logger.info(f"   Interval: {PRICE_UPDATE_INTERVAL} seconds ({PRICE_UPDATE_INTERVAL/60:.1f} minutes)")
                logger.info(f"   First send: after 10 seconds")
            except Exception as e:
                logger.error(f"Error setting up JobQueue: {e}", exc_info=e)
        else:
            logger.error("❌ JobQueue not available (None).")
            logger.error("   Make sure package is installed: pip install 'python-telegram-bot[job-queue]'")
            logger.error("   And that you're using the correct virtual environment.")
    else:
        logger.warning("⚠️ TELEGRAM_CHANNEL_ID not set. Automatic price sending to channel disabled.")
    
    # Start bot
    logger.info("Bot started and ready to work!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
