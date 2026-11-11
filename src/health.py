import http.server
import socketserver
import threading
from src.config import PORT, logger

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        response = b'{"status": "ok", "app": "acordate_bot"}'
        self.wfile.write(response)

    def log_message(self, format, *args):
        # Silenciar logs ruidosos de health-checks automáticos
        return


def start_health_server():
    """Inicia un servidor HTTP ligero en un hilo independiente para responder a Koyeb."""
    try:
        # Permitir reutilizar la dirección rápidamente si se reinicia el proceso
        socketserver.TCPServer.allow_reuse_address = True
        server = socketserver.TCPServer(("0.0.0.0", PORT), HealthCheckHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        logger.info(f"🌐 Servidor de Health Check activo en el puerto {PORT} (para Koyeb)")
    except Exception as e:
        logger.error(f"Error al iniciar servidor de health check: {e}")

