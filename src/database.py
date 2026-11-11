import json
import os
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import firebase_admin
from firebase_admin import credentials, firestore
from src.config import FIREBASE_CREDENTIALS_PATH, FIREBASE_CREDENTIALS_JSON, logger

# Inicialización del cliente Firestore
_db = None

def get_db():
    global _db
    if _db is not None:
        return _db

    # Verificar si Firebase ya está inicializado
    if not firebase_admin._apps:
        cred = None
        # 1. Intentar desde variable de entorno con JSON directo (ideal para Koyeb)
        if FIREBASE_CREDENTIALS_JSON:
            try:
                cert_dict = json.loads(FIREBASE_CREDENTIALS_JSON)
                cred = credentials.Certificate(cert_dict)
                logger.info("Credenciales de Firebase cargadas desde FIREBASE_CREDENTIALS_JSON.")
            except Exception as e:
                logger.error(f"Error al parsear FIREBASE_CREDENTIALS_JSON: {e}")

        # 2. Intentar desde archivo local (ideal para desarrollo)
        if cred is None and FIREBASE_CREDENTIALS_PATH and os.path.exists(FIREBASE_CREDENTIALS_PATH):
            try:
                cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
                logger.info(f"Credenciales de Firebase cargadas desde archivo: {FIREBASE_CREDENTIALS_PATH}")
            except Exception as e:
                logger.error(f"Error al cargar archivo de credenciales {FIREBASE_CREDENTIALS_PATH}: {e}")

        # 3. Inicializar app
        if cred:
            firebase_admin.initialize_app(cred)
        else:
            logger.warning("No se encontraron credenciales explícitas. Usando credenciales por defecto del sistema.")
            firebase_admin.initialize_app()

    _db = firestore.client()
    return _db


COLLECTION_NAME = "debts"


def add_debt(
    user_id: int,
    description: str,
    due_date_str: str,
    amount: float | None = None,
    is_recurring: bool = False,
    currency: str = "$"
) -> str:
    """Registra una nueva deuda o vencimiento."""
    db = get_db()
    now_iso = datetime.utcnow().isoformat()
    
    doc_data = {
        "user_id": user_id,
        "description": description.strip(),
        "due_date": due_date_str,  # Formato YYYY-MM-DD
        "amount": amount,
        "currency": currency,
        "is_recurring": is_recurring,
        "status": "pending",
        "reminded_day_before": False,
        "created_at": now_iso,
        "updated_at": now_iso
    }
    
    _, doc_ref = db.collection(COLLECTION_NAME).add(doc_data)
    logger.info(f"Deuda creada [ID: {doc_ref.id}] para usuario {user_id}: {description}")
    return doc_ref.id


def get_pending_debts(user_id: int) -> list[dict]:
    """Obtiene todas las deudas pendientes de un usuario ordenadas por fecha."""
    db = get_db()
    docs = (
        db.collection(COLLECTION_NAME)
        .where("user_id", "==", user_id)
        .where("status", "==", "pending")
        .stream()
    )
    
    debts = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        debts.append(d)
        
    # Ordenar por fecha de vencimiento ascendente
    debts.sort(key=lambda x: x.get("due_date", ""))
    return debts


def get_debt_by_id(debt_id: str) -> dict | None:
    """Recupera una deuda específica por su ID."""
    db = get_db()
    doc_ref = db.collection(COLLECTION_NAME).document(debt_id)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return None


def mark_as_paid(debt_id: str) -> tuple[bool, str]:
    """
    Marca una deuda como pagada.
    Si es recurrente mensual, calcula el vencimiento del siguiente mes y resetea las alertas.
    Retorna (éxito, mensaje descriptivo).
    """
    db = get_db()
    doc_ref = db.collection(COLLECTION_NAME).document(debt_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        return False, "La deuda no existe."
        
    data = doc.to_dict()
    is_recurring = data.get("is_recurring", False)
    current_due_str = data.get("due_date", "")
    description = data.get("description", "Vencimiento")
    now_iso = datetime.utcnow().isoformat()
    
    if is_recurring and current_due_str:
        try:
            curr_date = datetime.strptime(current_due_str, "%Y-%m-%d").date()
            next_date = curr_date + relativedelta(months=1)
            next_due_str = next_date.strftime("%Y-%m-%d")
            
            doc_ref.update({
                "due_date": next_due_str,
                "reminded_day_before": False,
                "updated_at": now_iso
            })
            return True, f"✅ *{description}* marcado como pagado. Al ser recurrente, su próximo vencimiento se fijó para el *{next_date.strftime('%d/%m/%Y')}*."
        except Exception as e:
            logger.error(f"Error calculando fecha recurrente para {debt_id}: {e}")
            
    # Si no es recurrente (o falló cálculo), simplemente se marca pagada
    doc_ref.update({
        "status": "paid",
        "updated_at": now_iso
    })
    return True, f"✅ *{description}* marcado como pagado con éxito."


def delete_debt(debt_id: str) -> bool:
    """Elimina permanentemente un registro de deuda."""
    db = get_db()
    doc_ref = db.collection(COLLECTION_NAME).document(debt_id)
    if not doc_ref.get().exists:
        return False
    doc_ref.delete()
    logger.info(f"Deuda eliminada: {debt_id}")
    return True


def get_debts_due_on(target_date_str: str) -> list[dict]:
    """
    Busca todas las deudas pendientes que vencen en target_date_str
    y que aún no hayan sido notificadas el día anterior.
    """
    db = get_db()
    docs = (
        db.collection(COLLECTION_NAME)
        .where("status", "==", "pending")
        .where("due_date", "==", target_date_str)
        .where("reminded_day_before", "==", False)
        .stream()
    )
    
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        results.append(data)
    return results


def mark_day_before_reminded(debt_id: str):
    """Marca el registro para no repetir la alerta de 1 día antes."""
    db = get_db()
    doc_ref = db.collection(COLLECTION_NAME).document(debt_id)
    doc_ref.update({
        "reminded_day_before": True,
        "updated_at": datetime.utcnow().isoformat()
    })

