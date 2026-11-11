import sys
import datetime
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

from src.config import (
    TELEGRAM_BOT_TOKEN,
    NOTIFICATION_HOUR,
    NOTIFICATION_MINUTE,
    BOT_TIMEZONE,
    logger
)
from src.health import start_health_server
from src.scheduler import check_upcoming_debts_job
from src.handlers.common import start_command, help_command, test_alert_command
from src.handlers.add_debt import get_add_debt_conversation_handler
from src.handlers.list_debts import list_debts_command, debt_action_callback


def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.critical(
            "❌ ERROR: La variable TELEGRAM_BOT_TOKEN no está configurada.\n"
            "Crea un archivo .env o define la variable de entorno antes de ejecutar."
        )
        sys.exit(1)

    logger.info("🚀 Iniciando Acordate Bot...")

    # 1. Iniciar servidor de Health Check para Koyeb en segundo plano
    start_health_server()

    # 2. Construir la aplicación de Telegram
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # 3. Configurar la tarea programada diaria (JobQueue)
    if app.job_queue:
        notification_time = datetime.time(
            hour=NOTIFICATION_HOUR,
            minute=NOTIFICATION_MINUTE,
            tzinfo=BOT_TIMEZONE
        )
        app.job_queue.run_daily(
            check_upcoming_debts_job,
            time=notification_time,
            name="daily_debt_reminder"
        )
        logger.info(
            f"⏰ Alerta diaria programada para las {NOTIFICATION_HOUR:02d}:{NOTIFICATION_MINUTE:02d} "
            f"({BOT_TIMEZONE.zone})"
        )
    else:
        logger.warning("⚠️ No se pudo inicializar JobQueue. Instala 'python-telegram-bot[job-queue]'.")

    # 4. Registrar Handlers y Comandos
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("ayuda", help_command))
    app.add_handler(CommandHandler("listar", list_debts_command))
    app.add_handler(CommandHandler("pendientes", list_debts_command))
    app.add_handler(CommandHandler("test_alerta", test_alert_command))

    # Flujo conversacional para /agregar
    app.add_handler(get_add_debt_conversation_handler())

    # Callbacks de botones inline (pagar, borrar)
    app.add_handler(CallbackQueryHandler(debt_action_callback, pattern=r"^(pay|del|delconf|cancelact):"))

    # 5. Iniciar polling 24/7
    logger.info("🤖 Bot listo y escuchando mensajes en Telegram...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

