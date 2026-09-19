import logging
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

import config
from handlers import music

# Отримуємо налаштування з config з fallback-значеннями за замовчуванням
WEB_SERVER_HOST = getattr(config, "WEB_SERVER_HOST", "127.0.0.1")
WEB_SERVER_PORT = getattr(config, "WEB_SERVER_PORT", 8080)
WEBHOOK_PATH = getattr(config, "WEBHOOK_PATH", "/webhook")
BASE_WEBHOOK_URL = getattr(config, "BASE_WEBHOOK_URL", "https://your-domain.com")
WEBHOOK_SECRET = getattr(config, "WEBHOOK_SECRET", None)


async def on_startup(bot: Bot) -> None:
    # Формуємо повну адресу Webhook: https://domain.com/webhook
    webhook_url = f"{BASE_WEBHOOK_URL.rstrip('/')}{WEBHOOK_PATH}"

    # Встановлюємо вебхук у Telegram
    await bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True
    )
    logging.info(f"🚀 Webhook успішно встановлено на: {webhook_url}")


async def on_shutdown(bot: Bot) -> None:
    # Видаляємо вебхук при зупинці бота
    await bot.delete_webhook()
    logging.info("🛑 Webhook видалено")


def main():
    # Вмикаємо логування, щоб бачити події та запити
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    # Ініціалізуємо бота та диспетчер
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    # Підключаємо роутери з обробниками
    dp.include_router(music.router)

    # Реєструємо хуки запуску та зупинки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Створюємо aiohttp веб-додаток
    app = web.Application()

    # Налаштовуємо обробник запитів від Telegram
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    # Інтегруємо диспетчер з aiohttp
    setup_application(app, dp, bot=bot)

    # Запускаємо веб-сервер
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    main()