# 🤖 Acordate Bot - Recordatorio de Vencimientos y Pagos

Bot personal de Telegram diseñado para gestionar y recordar el pago de cuotas de **tarjetas de crédito, préstamos bancarios y créditos en general**.
Utiliza **Google Cloud Firestore** como base de datos en la nube y está optimizado para desplegarse **100% GRATIS 24/7 en Koyeb** (Eco Tier) sin requerir tarjeta de crédito.

---

## 🚀 Características

- 🔔 **Alertas preventivas automáticas:** Notificación a Telegram **1 día antes** del vencimiento a la hora configurada (ej. 09:00 AM).
- 🔁 **Soporte para cuotas recurrentes:** Para tarjetas y servicios mensuales; al marcar como pagada, avanza automáticamente al mes siguiente.
- 📋 **Semáforo visual en `/listar`:**
  - 🔴 Vencida o vence hoy
  - 🟡 Vence mañana o en pocos días
  - 🟢 Vencimientos lejanos
- 🔒 **Acceso personal restringido:** Whitelist mediante `ALLOWED_USER_IDS` para que nadie más pueda usar tu bot.
- 🌐 **Koyeb Health-Check integrado:** Servidor HTTP ligero interno en el puerto `8000` para mantener el servicio activo y saludable en Koyeb sin configuraciones extra.

---

## 🛠️ Requisitos Previos

1. **Token de Bot en Telegram:**
   - Abre Telegram y habla con [@BotFather](https://t.me/BotFather).
   - Envía `/newbot`, dale un nombre y un usuario (ej. `mi_acordate_bot`).
   - Copia el `HTTP API Token`.

2. **Tu ID de Usuario en Telegram:**
   - Envía un mensaje a [@userinfobot](https://t.me/userinfobot) en Telegram.
   - Copia el número que figura en `Id:` (ej. `123456789`).

3. **Proyecto en Firebase Firestore (Gratuito):**
   - Ingresa a la [Consola de Firebase](https://console.firebase.google.com/) y crea un proyecto gratuito (Plan Spark).
   - Ve a **Compilación > Firestore Database** y haz clic en **Crear base de datos**.
   - Ve a **Configuración del Proyecto (icono de engranaje) > Cuentas de servicio**.
   - Haz clic en **Generar nueva clave privada**. Se descargará un archivo `.json`.

---

## 💻 Ejecución en Desarrollo Local

1. Clona el repositorio e ingresa a la carpeta:
   ```bash
   cd acordate_bot
   ```

2. Crea y activa un entorno virtual de Python:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # En Linux/Mac
   # .venv\Scripts\activate   # En Windows
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configura el archivo `.env`:
   ```bash
   cp .env.example .env
   ```
   Edita `.env` con tu token de Telegram, tu ID y renombra o copia tu archivo JSON de Firebase como `serviceAccountKey.json`.

5. Inicia el bot:
   ```bash
   python -m src.main
   ```

---

## ☁️ Despliegue 100% Gratis en Koyeb (24/7)

Koyeb ofrece un nivel gratuito (*Free Eco Tier*) que permite mantener un servicio web corriendo continuamente.

### Paso 1: Subir el proyecto a GitHub
```bash
git init
git add .
git commit -m "Initial commit Acordate Bot"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/acordate_bot.git
git push -u origin main
```
*(Nota: `.gitignore` ya está configurado para que nunca se suban tu `.env` ni tu `serviceAccountKey.json`)*.

### Paso 2: Crear el servicio en Koyeb
1. Regístrate o inicia sesión en [Koyeb.com](https://www.koyeb.com/).
2. Haz clic en **Create Service** y selecciona **GitHub**.
3. Selecciona tu repositorio `acordate_bot`.
4. En **Type of deployment**, selecciona **Dockerfile** o **Buildpack** (ambos están configurados).
5. En la sección **Instance**, elige la gratuita: **Nano (Eco)**.
6. En **Environment variables**, agrega las siguientes:
   - `TELEGRAM_BOT_TOKEN`: Tu token de Telegram.
   - `ALLOWED_USER_IDS`: Tu ID numérico de Telegram.
   - `TIMEZONE`: Tu zona horaria (ej. `America/La_Paz` o `America/Argentina/Buenos_Aires`).
   - `NOTIFICATION_HOUR`: `9` (hora de la alerta matutina).
   - `NOTIFICATION_MINUTE`: `0`.
   - `FIREBASE_CREDENTIALS_JSON`: Abre tu archivo `serviceAccountKey.json` descargado de Firebase, copia **todo su contenido** y pégalo como el valor de esta variable en Koyeb.
7. Haz clic en **Deploy**.

¡Listo! En menos de 2 minutos tu bot estará activo 24/7 en la nube sin costo alguno.

---

## 📱 Comandos del Bot

| Comando | Descripción |
|---|---|
| `/start` | Inicia el bot y verifica la autorización |
| `/agregar` | Asistente interactivo paso a paso para añadir un vencimiento |
| `/listar` | Muestra todos los pagos pendientes con botones para pagar o borrar |
| `/test_alerta` | Ejecuta la comprobación de recordatorios inmediatamente para probar |
| `/ayuda` | Muestra la guía rápida de uso |

