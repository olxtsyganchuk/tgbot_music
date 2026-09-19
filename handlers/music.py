from aiogram import Router, types, F
from aiogram.filters import CommandStart

# Імпортуємо функцію конвертації та клавіатуру
from services.converter import convert_link
from keyboards.inline import get_platforms_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Привіт! Надішли мені посилання на трек, і я запропоную платформи для конвертації.")


# 1. Ловимо посилання
@router.message(F.text.startswith('http'))
async def handle_music_link(message: types.Message):
    # Відповідаємо на повідомлення користувача, прикріплюючи клавіатуру
    await message.reply(
        "Оберіть платформу:",
        reply_markup=get_platforms_keyboard()
    )


# 2. Ловимо натискання на кнопки (всі, чия дата починається на "platform_")
@router.callback_query(F.data.startswith("platform_"))
async def process_platform_selection(callback: types.CallbackQuery):
    # Витягуємо назву платформи (наприклад, з 'platform_spotify' дістаємо 'spotify')
    target_platform = callback.data.split("_")[1]

    # Витягуємо посилання з оригінального повідомлення
    # callback.message - це повідомлення з кнопками від бота
    # reply_to_message - це ваше повідомлення, на яке бот відповів
    original_url = callback.message.reply_to_message.text

    # Оновлюємо текст повідомлення з кнопками, показуючи статус
    await callback.message.edit_text("Шукаю... ⏳")

    # Конвертуємо посилання
    new_link = await convert_link(original_url, target_platform)

    # Замінюємо статус на готовий результат (кнопки при цьому зникнуть)
    await callback.message.edit_text(new_link)

    # Повідомляємо Telegram, що клік оброблено (інакше на кнопці висітиме "годинник")
    await callback.answer()