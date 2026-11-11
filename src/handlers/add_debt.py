from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from src.config import BOT_TIMEZONE, logger
from src.database import add_debt
from src.handlers.common import restricted

# Estados de la conversación
STATE_DESC, STATE_DATE, STATE_AMOUNT, STATE_RECURRING = range(4)


def parse_flexible_date(text: str) -> tuple[str | None, str | None]:
    """
    Parsea una fecha ingresada por el usuario en formatos comunes:
    - DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD
    - DD/MM o DD-MM (deduce el año actual o el siguiente si ya pasó este mes)
    Retorna (YYYY-MM-DD, mensaje_error)
    """
    cleaned = text.strip()
    today = datetime.now(BOT_TIMEZONE).date()

    # Formatos completos
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(cleaned, fmt).date()
            return parsed.strftime("%Y-%m-%d"), None
        except ValueError:
            pass

    # Formato día/mes sin año (DD/MM o DD-MM)
    for sep in ("/", "-"):
        if sep in cleaned:
            parts = cleaned.split(sep)
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                day, month = int(parts[0]), int(parts[1])
                try:
                    # Probar con el año actual
                    target_date = datetime(today.year, month, day).date()
                    if target_date < today:
                        # Si ya pasó este año, asumir el siguiente
                        target_date = datetime(today.year + 1, month, day).date()
                    return target_date.strftime("%Y-%m-%d"), None
                except ValueError:
                    return None, f"Día o mes inválido en '{cleaned}'."

    return None, "Formato no reconocido. Usa por ejemplo `25/11` o `25/11/2026`."


@restricted
async def start_add_debt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia el flujo de registro de un nuevo vencimiento."""
    context.user_data.clear()
    await update.effective_message.reply_text(
        "📝 *Paso 1 de 4: Descripción*\n\n"
        "Escribe el nombre o concepto del gasto a recordar.\n"
        "_(Ejemplos: `Tarjeta Visa Galicia`, `Cuota crédito auto`, `Alquiler`)_\n\n"
        "Puedes escribir `/cancelar` en cualquier momento para abortar.",
        parse_mode="Markdown"
    )
    return STATE_DESC


async def receive_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guarda la descripción y pide la fecha."""
    desc = update.effective_message.text.strip()
    if len(desc) < 2:
        await update.effective_message.reply_text("Por favor escribe una descripción un poco más clara:")
        return STATE_DESC

    context.user_data["description"] = desc
    await update.effective_message.reply_text(
        f"📅 *Paso 2 de 4: Fecha de Vencimiento*\n\n"
        f"Concepto: *{desc}*\n\n"
        f"¿Qué día vence? Puedes escribir:\n"
        f"• `25/11` (asume el mes/año más cercano)\n"
        f"• `25/11/2026` (fecha completa)",
        parse_mode="Markdown"
    )
    return STATE_DATE


async def receive_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Valida y guarda la fecha de vencimiento."""
    text = update.effective_message.text.strip()
    date_iso, error = parse_flexible_date(text)

    if error:
        await update.effective_message.reply_text(
            f"❌ {error}\nPor favor intenta nuevamente (ejemplo: `28/11`):",
            parse_mode="Markdown"
        )
        return STATE_DATE

    context.user_data["due_date"] = date_iso
    parsed_date = datetime.strptime(date_iso, "%Y-%m-%d").strftime("%d/%m/%Y")

    await update.effective_message.reply_text(
        f"💰 *Paso 3 de 4: Monto de la Cuota (Opcional)*\n\n"
        f"Vencimiento fijado para: *{parsed_date}*\n\n"
        f"Indica el monto a pagar (ej: `45000` o `12500.50`).\n"
        f"Si no tienes el importe exacto o no deseas registrarlo, escribe `/omitir`.",
        parse_mode="Markdown"
    )
    return STATE_AMOUNT


async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guarda el monto o lo omite."""
    text = update.effective_message.text.strip()
    amount = None

    if text != "/omitir":
        # Limpiar posibles signos $ o comas
        cleaned = text.replace("$", "").replace(" ", "").replace(",", ".")
        try:
            amount = float(cleaned)
        except ValueError:
            await update.effective_message.reply_text(
                "❌ Número no válido. Escribe una cifra como `35000` o escribe `/omitir`:"
            )
            return STATE_AMOUNT

    context.user_data["amount"] = amount

    keyboard = [
        [
            InlineKeyboardButton("🔁 Sí, mensual", callback_data="recur:yes"),
            InlineKeyboardButton("📌 No, cuota única", callback_data="recur:no")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_message.reply_text(
        f"🔄 *Paso 4 de 4: Recurrencia*\n\n"
        f"¿Es un pago recurrente mensual? (ej. tarjetas de crédito o servicios que vencen todos los meses):",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    return STATE_RECURRING


async def receive_recurring(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Finaliza el guardado de la deuda en Firestore."""
    query = update.callback_query
    await query.answer()

    is_recurring = query.data == "recur:yes"
    user_id = update.effective_user.id
    desc = context.user_data.get("description", "Vencimiento")
    due_date = context.user_data.get("due_date")
    amount = context.user_data.get("amount")

    try:
        debt_id = add_debt(
            user_id=user_id,
            description=desc,
            due_date_str=due_date,
            amount=amount,
            is_recurring=is_recurring
        )

        display_date = datetime.strptime(due_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        amount_str = f"${amount:,.2f}" if amount is not None else "Sin especificar"
        recur_str = "🔁 Mensual (se renovará cada mes al pagar)" if is_recurring else "📌 Cuota única"

        resumen = (
            f"🎉 *¡Vencimiento guardado con éxito!*\n\n"
            f"💳 *Concepto:* {desc}\n"
            f"📅 *Vence:* {display_date}\n"
            f"💰 *Monto:* {amount_str}\n"
            f"ℹ️ *Tipo:* {recur_str}\n\n"
            f"🔔 _Te enviaré un recordatorio 1 día antes del vencimiento._"
        )
        await query.edit_message_text(resumen, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error al guardar deuda en Firestore: {e}")
        await query.edit_message_text(f"❌ Ocurrió un error al guardar en la base de datos: {e}")

    context.user_data.clear()
    return ConversationHandler.END


async def cancel_add_debt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela el proceso de agregar deuda."""
    context.user_data.clear()
    await update.effective_message.reply_text("❌ Operación cancelada. No se guardó ningún cambio.")
    return ConversationHandler.END


def get_add_debt_conversation_handler() -> ConversationHandler:
    """Construye el ConversationHandler para el comando /agregar."""
    return ConversationHandler(
        entry_points=[CommandHandler("agregar", start_add_debt)],
        states={
            STATE_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_desc)
            ],
            STATE_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_date)
            ],
            STATE_AMOUNT: [
                CommandHandler("omitir", receive_amount),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount)
            ],
            STATE_RECURRING: [
                CallbackQueryHandler(receive_recurring, pattern=r"^recur:(yes|no)$")
            ]
        },
        fallbacks=[CommandHandler("cancelar", cancel_add_debt)],
        allow_reentry=True
    )

