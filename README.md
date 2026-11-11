# 🤖 Acordate Bot - Recordatorio de Vencimientos y Pagos

Bot personal de Telegram diseñado para gestionar y recordar el pago de cuotas de **tarjetas de crédito, préstamos bancarios y créditos en general**.
Utiliza **Google Cloud Firestore** como base de datos en la nube y está optimizado para desplegarse **100% GRATIS 24/7 en Render (Free Web Service)** sin costo.

---

## 🚀 Características

- 🔔 **Alertas preventivas automáticas:** Notificación a Telegram **1 día antes** del vencimiento a la hora configurada (ej. 09:00 AM).
- 🔁 **Soporte para cuotas recurrentes:** Para tarjetas y préstamos mensuales; al marcar como pagada, avanza automáticamente al mes siguiente.
- 📋 **Semáforo visual en `/listar`:**
  - 🔴 Vencida o vence hoy
  - 🟡 Vence mañana o en pocos días
  - 🟢 Vencimientos lejanos
- 🔒 **Acceso personal restringido:** Whitelist mediante `ALLOWED_USER_IDS` para que nadie más pueda usar tu bot.
- 🌐 **Health-Check HTTP integrado:** Servidor web ligero en el puerto `$PORT` (`10000` por defecto en Render) listo para mantener el servicio activo.

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

## ☁️ Despliegue 100% Gratis en Render (24/7)

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

---

### Paso 2: Crear el Web Service en Render
1. Regístrate o inicia sesión en [Render.com](https://render.com/).
2. Haz clic en **New + > Web Service**.
3. Conecta tu repositorio de GitHub `acordate_bot`.
4. Render detectará automáticamente el archivo `render.yaml` o puedes configurarlo manualmente:
   - **Name:** `acordate-bot`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -m src.main`
   - **Instance Type:** `Free`
5. En la sección **Environment Variables**, añade:
   - `TELEGRAM_BOT_TOKEN`: Tu token de Telegram.
   - `ALLOWED_USER_IDS`: Tu ID numérico de Telegram.
   - `TIMEZONE`: `America/La_Paz` (o tu zona horaria local).
   - `NOTIFICATION_HOUR`: `9`
   - `NOTIFICATION_MINUTE`: `0`
   - `FIREBASE_CREDENTIALS_JSON`: Abre tu archivo `serviceAccountKey.json` descargado de Firebase, copia **todo su contenido** en una sola línea y pégalo como el valor de esta variable en Render.
6. Haz clic en **Deploy Web Service**.

---

### Paso 3: Mantener Render despierto 24/7 (Gratis)
Los Web Services gratuitos de Render entran en suspensión tras 15 minutos sin recibir visitas HTTP.
Dado que nuestro bot incluye un servidor web en segundo plano respondiendo en `/`, puedes mantenerlo activo 24/7 de forma 100% gratuita:

1. Copia la URL pública que Render le asigna a tu servicio (ej. `https://acordate-bot.onrender.com`).
2. Crea una cuenta gratuita en [UptimeRobot.com](https://uptimerobot.com/) o [cron-job.org](https://cron-job.org/).
3. Añade un nuevo monitor:
   - **Tipo:** `HTTP(s)`
   - **URL:** `https://acordate-bot.onrender.com/`
   - **Intervalo de monitoreo:** cada **10 minutos**.
4. ¡Listo! UptimeRobot enviará un ping ligero cada 10 minutos, impidiendo que Render se duerma y asegurando que tu bot de Telegram y sus alarmas diarias funcionen las 24 horas del día.

---

## 📱 Comandos del Bot

| Comando | Descripción |
|---|---|
| `/start` | Inicia el bot y verifica la autorización |
| `/agregar` | Asistente interactivo paso a paso para añadir un vencimiento |
| `/listar` | Muestra todos los pagos pendientes con botones para pagar o borrar |
| `/test_alerta` | Ejecuta la comprobación de recordatorios inmediatamente para probar |
| `/ayuda` | Muestra la guía rápida de uso |
