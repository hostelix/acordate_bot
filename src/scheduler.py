from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.config import BOT_TIMEZONE, logger
from src.database import get_debts_due_on, mark_day_before_reminded

async def check_upcoming_debts_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Tarea programada diaria:
    Busca deudas que venzan mañana y envía una alerta a Telegram 1 día antes.
    """
    now = datetime.now(BOT_TIMEZONE)
    tomorrow = now.date() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")
    tomorrow_display = tomorrow.strftime("%d/%m/%Y")

    logger.info(f"🔎 Ejecutando revisión de recordatorios para mañana ({tomorrow_str})...")

    try:
        debts_due_tomorrow = get_debts_due_on(tomorrow_str)
        if not debts_due_tomorrow:
            logger.info("No se encontraron deudas pendientes con vencimiento para mañana.")
            return

        for debt in debts_due_tomorrow:
            debt_id = debt.get("id")
            user_id = debt.get("user_id")
            description = debt.get("description", "Vencimiento")
            amount = debt.get("amount")
            currency = debt.get("currency", "$")
            is_recurring = debt.get("is_recurring", False)

            amount_text = f"{currency} {amount:,.2f}" if amount is not None else "No especificado"
            recurrence_text = "🔁 Mensual recurrente" if is_recurring else "📌 Cuota única"

            message = (
                f"⚠️ *¡RECORDATORIO DE PAGO! VENCE MAÑANA*\n\n"
                f"💳 *Concepto:* {description}\n"
                f"📅 *Vencimiento:* {tomorrow_display}\n"
                f"💰 *Monto:* {amount_text}\n"
                f"ℹ️ *Tipo:* {recurrence_text}\n\n"
                f"_No olvides realizar el pago a tiempo para evitar intereses o recargos._"
            )

            keyboard = [
                [InlineKeyboardButton("✅ Ya lo pagué", callback_data=f"pay:{debt_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
                # Marcar en Firestore para no repetir la alerta de 1 día antes
                mark_day_before_reminded(debt_id)
                logger.info(f"Alerta enviada a usuario {user_id} para deuda '{description}' [{debt_id}].")
            except Exception as send_err:
                logger.error(f"Error al enviar mensaje de recordatorio al usuario {user_id}: {send_err}")

    except Exception as e:
        logger.error(f"Error crítico en check_upcoming_debts_job: {e}")

