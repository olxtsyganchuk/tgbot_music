import os

# Зчитуємо токен з Environment Variables на сервері або з .env локально
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Інші налаштування вебхука (їх можна залишити тут або теж винести в середовище)
TARGET_PLATFORM = "youtubeMusic"
WEB_SERVER_HOST = "0.0.0.0"       # Для сервера важливо слухати всі інтерфейси
WEB_SERVER_PORT = int(os.getenv("PORT", 8080)) # Render часто передає порт динамічно через змінну PORT
WEBHOOK_PATH = "/webhook"

BASE_WEBHOOK_URL = os.getenv("BASE_WEBHOOK_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", None)