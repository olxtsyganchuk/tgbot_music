import logging
import sys
from datetime import datetime, timezone
from aiohttp import web
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

import config
from handlers import music

# Отримуємо налаштування з config з fallback-значеннями за замовчуванням
WEB_SERVER_HOST = getattr(config, "WEB_SERVER_HOST", "127.0.0.1")
WEB_SERVER_PORT = getattr(config, "WEB_SERVER_PORT", 8080)
WEBHOOK_PATH = getattr(config, "WEBHOOK_PATH", "/webhook")
BASE_WEBHOOK_URL = getattr(config, "BASE_WEBHOOK_URL", "https://your-domain.com")
WEBHOOK_SECRET = getattr(config, "WEBHOOK_SECRET", None)


# --- Мідлваря для перевірки "холодного старту" ---
class WakeUpMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        # Рахуємо різницю між поточним часом і часом відправки повідомлення
        delay = (datetime.now(timezone.utc) - event.date).total_seconds()

        # Якщо затримка більша за 20 секунд — це 100% холодний старт Render
        if delay > 20:
            await event.answer(
                "🥱 Ох, потягуюся... Я трохи подрімав, але твоє повідомлення мене розбудило! "
                "Тепер я онлайн, давай сюди свої запити 🚀"
            )

        # Передаємо повідомлення далі, щоб бот виконав свою звичну роботу
        return await handler(event, data)


async def on_startup(bot: Bot) -> None:
    # Формуємо повну адресу Webhook: https://domain.com/webhook
    webhook_url = f"{BASE_WEBHOOK_URL.rstrip('/')}{WEBHOOK_PATH}"

    # Встановлюємо вебхук у Telegram
    await bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=False  # <--- Змінено на False: не видаляємо повідомлення при старті!
    )
    logging.info(f"🚀 Webhook успішно встановлено на: {webhook_url}")


async def on_shutdown(bot: Bot) -> None:
    # Закоментовано видалення вебхука, щоб Телеграм не втрачав зв'язок під час сну сервера
    # await bot.delete_webhook()
    logging.info("🛑 Сервер зупинено (заснув), але вебхук залишається в Телеграмі")


def main():
    # Вмикаємо логування, щоб бачити події та запити
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    # Ініціалізуємо бота та диспетчер
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    # Підключаємо наш "будильник" до всіх повідомлень
    dp.message.middleware(WakeUpMiddleware())

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