import os
import json
import logging
import pytz
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

# Configurar logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("acordate_bot")

# Token de Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
if not TELEGRAM_BOT_TOKEN:
    logger.warning("⚠️ No se ha configurado TELEGRAM_BOT_TOKEN en las variables de entorno.")

# Lista de IDs de usuarios autorizados
raw_allowed = os.getenv("ALLOWED_USER_IDS", "").strip()
ALLOWED_USER_IDS: set[int] = set()
if raw_allowed:
    for uid in raw_allowed.split(","):
        cleaned = uid.strip()
        if cleaned.isdigit():
            ALLOWED_USER_IDS.add(int(cleaned))

# Zona horaria
TIMEZONE_STR = os.getenv("TIMEZONE", "America/La_Paz").strip()
try:
    BOT_TIMEZONE = pytz.timezone(TIMEZONE_STR)
except Exception:
    logger.error(f"Zona horaria '{TIMEZONE_STR}' inválida. Usando UTC.")
    BOT_TIMEZONE = pytz.UTC

# Horario de notificación diaria
NOTIFICATION_HOUR = int(os.getenv("NOTIFICATION_HOUR", "9"))
NOTIFICATION_MINUTE = int(os.getenv("NOTIFICATION_MINUTE", "0"))

# Puerto para health-check de Koyeb
PORT = int(os.getenv("PORT", "8000"))

# Credenciales de Firebase
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "./serviceAccountKey.json").strip()
FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS_JSON", "").strip()

