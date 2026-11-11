from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.config import BOT_TIMEZONE, logger
from src.database import get_pending_debts, mark_as_paid, delete_debt, get_debt_by_id
from src.handlers.common import restricted


def format_debt_item(debt: dict, today) -> tuple[str, str]:
    """Formatea una deuda con estado semafórico según su cercanía."""
    due_str = debt.get("due_date", "")
    desc = debt.get("description", "Vencimiento")
    amount = debt.get("amount")
    currency = debt.get("currency", "$")
    is_recurring = debt.get("is_recurring", False)

    amount_str = f"{currency}{amount:,.2f}" if amount is not None else "Sin monto"
    recur_icon = " 🔁" if is_recurring else ""

    try:
        due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
        diff = (due_date - today).days
        display_date = due_date.strftime("%d/%m/%Y")

        if diff < 0:
            status_badge = f"🔴 *¡VENCIDO hace {-diff} días!*"
        elif diff == 0:
            status_badge = "🔴 *¡VENCE HOY!*"
        elif diff == 1:
            status_badge = "🟡 *¡VENCE MAÑANA!*"
        elif diff <= 5:
            status_badge = f"🟡 *Vence en {diff} días*"
        else:
            status_badge = f"🟢 Vence en {diff} días"

        line = (
            f"{status_badge}\n"
            f"💳 *{desc}*{recur_icon}\n"
            f"📅 Fecha: `{display_date}` | 💰 Monto: `{amount_str}`"
        )
        return line, due_str
    except Exception:
        return f"💳 *{desc}* | 📅 `{due_str}`", due_str


@restricted
async def list_debts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra todas las deudas pendientes del usuario."""
    user_id = update.effective_user.id
    today = datetime.now(BOT_TIMEZONE).date()

    try:
        debts = get_pending_debts(user_id)
        if not debts:
            await update.effective_message.reply_text(
                "🎉 *¡Excelente! No tienes deudas ni vencimientos pendientes.*\n\n"
                "Usa `/agregar` cuando quieras registrar una nueva tarjeta o cuota.",
                parse_mode="Markdown"
            )
            return

        header = f"📋 *Tus Vencimientos Pendientes ({len(debts)}):*\n\n"
        await update.effective_message.reply_text(header, parse_mode="Markdown")

        # Mostrar cada deuda como un bloque interactivo con sus botones
        for debt in debts:
            text_block, _ = format_debt_item(debt, today)
            debt_id = debt.get("id")

            keyboard = [
                [
                    InlineKeyboardButton("✅ Marcar Pagado", callback_data=f"pay:{debt_id}"),
                    InlineKeyboardButton("🗑️ Eliminar", callback_data=f"del:{debt_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.effective_message.reply_text(
                text_block,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

    except Exception as e:
        logger.error(f"Error al listar deudas para usuario {user_id}: {e}")
        await update.effective_message.reply_text(f"❌ Error al consultar la base de datos: {e}")


async def debt_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja las acciones de los botones inline (Pagar y Eliminar)."""
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    action, _, debt_id = data.partition(":")

    if not debt_id:
        return

    if action == "pay":
        success, message = mark_as_paid(debt_id)
        if success:
            await query.edit_message_text(message, parse_mode="Markdown")
        else:
            await query.edit_message_text(f"⚠️ {message}")

    elif action == "del":
        # Confirmación de borrado
        keyboard = [
            [
                InlineKeyboardButton("💥 Sí, eliminar", callback_data=f"delconf:{debt_id}"),
                InlineKeyboardButton("↩️ Cancelar", callback_data=f"cancelact:{debt_id}")
            ]
        ]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == "delconf":
        success = delete_debt(debt_id)
        if success:
            await query.edit_message_text("🗑️ *Vencimiento eliminado correctamente.*", parse_mode="Markdown")
        else:
            await query.edit_message_text("⚠️ No se encontró la deuda para eliminar.")

    elif action == "cancelact":
        # Restaurar botones originales
        today = datetime.now(BOT_TIMEZONE).date()
        debt = get_debt_by_id(debt_id)
        if debt and debt.get("status") == "pending":
            text_block, _ = format_debt_item(debt, today)
            keyboard = [
                [
                    InlineKeyboardButton("✅ Marcar Pagado", callback_data=f"pay:{debt_id}"),
                    InlineKeyboardButton("🗑️ Eliminar", callback_data=f"del:{debt_id}")
                ]
            ]
            await query.edit_message_text(text_block, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("Operación cancelada.")

