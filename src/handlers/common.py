from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from src.config import ALLOWED_USER_IDS, logger
from src.scheduler import check_upcoming_debts_job


def restricted(func):
    """Decorador para restringir el uso del bot únicamente a los IDs autorizados."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        user_id = user.id if user else None

        if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
            logger.warning(f"Intento de acceso no autorizado desde ID {user_id} (@{user.username if user else 'desconocido'})")
            if update.effective_message:
                await update.effective_message.reply_text(
                    f"⛔ *Acceso Denegado*\n\n"
                    f"Este es un bot personal privado.\n"
                    f"Tu ID de Telegram es: `{user_id}`\n\n"
                    f"Para autorizarte, agrega este ID a `ALLOWED_USER_IDS` en la configuración.",
                    parse_mode="Markdown"
                )
            return
        return await func(update, context, *args, **kwargs)
    return wrapped


@restricted
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /start."""
    user = update.effective_user
    first_name = user.first_name if user else "Amigo"

    mensaje = (
        f"👋 ¡Hola, *{first_name}*! Te doy la bienvenida a *Acordate Bot* 🤖💳\n\n"
        f"Tu asistente personal para no volver a olvidarte de pagar tus tarjetas de crédito y préstamos.\n\n"
        f"📌 *Comandos disponibles:*\n"
        f"➕ `/agregar` - Registrar un nuevo vencimiento (paso a paso)\n"
        f"📋 `/listar` - Ver tus pagos pendientes y próximos vencimientos\n"
        f"🔔 `/test_alerta` - Probar el chequeo de recordatorios ahora mismo\n"
        f"❓ `/ayuda` - Instrucciones detalladas de uso\n\n"
        f"💡 _Te avisaré automáticamente 1 día antes de cada vencimiento._"
    )
    await update.effective_message.reply_text(mensaje, parse_mode="Markdown")


@restricted
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /ayuda."""
    mensaje = (
        f"📖 *Guía de uso de Acordate Bot:*\n\n"
        f"1️⃣ *Registrar vencimientos:*\n"
        f"Escribe `/agregar` y el bot te pedirá:\n"
        f"  • Descripción (ej. *Tarjeta Visa Santander*)\n"
        f"  • Fecha de vencimiento (ej. *25/11* o *25/11/2026*)\n"
        f"  • Monto aproximado (puedes enviar `/omitir`)\n"
        f"  • Si es cuota mensual recurrente (se renovará cada mes automáticamente)\n\n"
        f"2️⃣ *Listar y gestionar:*\n"
        f"Usa `/listar` para ver todas tus deudas activas.\n"
        f"Podrás marcar como pagada o eliminar con los botones que acompañan la lista.\n\n"
        f"3️⃣ *Alertas automáticas:*\n"
        f"Todos los días a la hora programada, revisaré tus vencimientos y te enviaré un aviso *1 día antes* con un botón para tacharlo."
    )
    await update.effective_message.reply_text(mensaje, parse_mode="Markdown")


@restricted
async def test_alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando manual para probar la lógica de recordatorios inmediatamente."""
    await update.effective_message.reply_text("🔄 Ejecutando revisión manual de alertas para mañana...")
    await check_upcoming_debts_job(context)
    await update.effective_message.reply_text("✔️ Revisión manual finalizada.")

