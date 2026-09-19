import asyncio
import logging
from aiogram import Bot, Dispatcher

import config
from handlers import music


async def main():
    # Вмикаємо логування, щоб бачити помилки та інформацію про запити в консолі
    logging.basicConfig(level=logging.INFO)

    # Ініціалізуємо бота та диспетчер
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    # Підключаємо роутер з нашими обробниками повідомлень та кнопок
    dp.include_router(music.router)

    # Очищуємо чергу повідомлень, які надійшли, поки бот був вимкнений, і запускаємо його
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())