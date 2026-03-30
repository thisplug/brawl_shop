import os
from typing import List
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Токен бота (получите у @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ID администраторов (можно получить у @userinfobot)
# Формат: ADMIN_IDS=123456789,987654321
admin_ids_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: List[int] = []
if admin_ids_str:
    try:
        ADMIN_IDS = [int(uid.strip()) for uid in admin_ids_str.split(",") if uid.strip()]
    except ValueError:
        print("⚠️ Предупреждение: Неверный формат ADMIN_IDS в .env файле. Используйте формат: ADMIN_IDS=123456789,987654321")

# Настройки базы данных
DATABASE_PATH = os.getenv("DATABASE_PATH", "brawl_shop.db")
