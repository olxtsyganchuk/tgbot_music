from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_platforms_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Створюємо кнопки. callback_data - це те, що бот отримає при натисканні (ліміт 64 байти)
    builder.button(text="YouTube Music", callback_data="platform_youtubeMusic")
    builder.button(text="Spotify", callback_data="platform_spotify")
    builder.button(text="Apple Music", callback_data="platform_appleMusic")

    # Розташовуємо кнопки по одній у рядок (можете змінити на 2, якщо хочете у два стовпці)
    builder.adjust(1)

    return builder.as_markup()