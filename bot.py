import asyncio
import logging
from os import getenv

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# --- Настройки из переменных окружения (Railway подставит их сам) ---
BOT_TOKEN = getenv("BOT_TOKEN")
ADMIN_ID = int(getenv("ADMIN_ID", "0"))
# Railway предоставит этот домен автоматически
BASE_WEBHOOK_URL = f"https://{getenv('RAILWAY_PUBLIC_DOMAIN')}"
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = getenv("WEBHOOK_SECRET", "my-secret-key")  # Защита от посторонних запросов

# --- Инициализация ---
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- Импорт вашей базы данных (не трогаем) ---
import sqlite3
# ... здесь может быть код init_db() и get_products() из вашего database.py ...

# --- Ваши обработчики (оставляем как было, меняем только хвост файла) ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(f"Привет, {message.from_user.first_name}! 👋\n\nЭто магазин. Нажми /catalog, чтобы посмотреть товары.")

@dp.message(Command("catalog"))
async def cmd_catalog(message: Message):
    # Вставьте сюда вашу логику вывода товаров
    # Например:
    # products = get_products()
    # for prod in products:
    #     await message.answer(f"{prod[1]} - {prod[2]} руб.")
    await message.answer("Здесь будет каталог (код из вашего database.py).")

# --- НОВАЯ ЧАСТЬ: Запуск через Webhook ---
async def on_startup(bot: Bot):
    """Регистрируем вебхук при старте приложения"""
    await bot.set_webhook(
        f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True  # Сбросить старые сообщения, пока бот спал
    )
    logging.info(f"Webhook установлен на {BASE_WEBHOOK_URL}{WEBHOOK_PATH}")

def main():
    # Регистрируем действие при старте
    dp.startup.register(on_startup)

    # Создаем веб-приложение
    app = web.Application()

    # Настраиваем обработчик вебхуков от Telegram
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    # Связываем aiogram с aiohttp
    setup_application(app, dp, bot=bot)

    # Railway сам скажет, на каком порту слушать (обычно через переменную PORT)
    port = int(getenv("PORT", 8080))
    logging.info(f"Запуск веб-сервера на порту {port}")
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()