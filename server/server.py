#!/usr/bin/env python3
"""Muse Control - servidor local (Termux / Ubuntu con proot-distro).

Escucha SOLO en 127.0.0.1:8080 (localhost, nunca internet) y ejecuta
comandos de una lista blanca fija. Cada peticion necesita el token
secreto; sin el token correcto no se ejecuta nada.

Uso:
    python3 server.py

El token se configura con la variable de entorno MUSE_TOKEN.
Si no se define, usa el valor de ejemplo (cambialo).

Solo usa la biblioteca estandar de Python 3, sin dependencias.
"""
import hmac
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"  # Nunca 0.0.0.0: solo este mismo equipo.
PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUNS_DIR = os.path.join(BASE_DIR, "runs")
LOG_FILE = os.path.join(BASE_DIR, "commands.log")
MAX_BODY = 64 * 1024  # 64 KB, suficiente para token + comando.

# Token esperado. Define el tuyo asi antes de arrancar:
#   export MUSE_TOKEN="tu-token-largo-y-aleatorio"
EXPECTED_TOKEN = os.environ.get("MUSE_TOKEN", "MI_TOKEN_SECRETO_123")

# Lista blanca: los UNICOS comandos que el servidor acepta.
# Comparacion exacta; cualquier otra cosa se rechaza sin ejecutar.
ALLOWED_COMMANDS = {
    "muse",
    "muse --yolo",
    "proot-distro login ubuntu",
    "proot-distro login ubuntu -c muse --yolo",
}


def log_command(entry):
    """Agrega una linea JSON al log. Nunca se guarda el token."""
    entry = dict(entry)
    entry.pop("token", None)
    entry["time"] = datetime.now(timezone.utc).isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


class Handler(BaseHTTPRequestHandler):
    server_version = "MuseControl/1.0"

    def log_message(self, fmt, *args):  # noqa: N802 - firma de http.server
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _is_local(self):
        # Defensa en profundidad: aunque el socket solo escucha en
        # loopback, se vuelve a comprobar el origen de cada peticion.
        return self.client_address[0] in ("127.0.0.1", "::1")

    def do_GET(self):  # noqa: N802 - firma de http.server
        if self.path in ("/", "/health"):
            self._send(200, {"status": "ok",
                             "message": "Muse Control corriendo en localhost"})
        else:
            self._send(404, {"status": "error",
                             "message": "ruta no encontrada"})

    def do_POST(self):  # noqa: N802 - firma de http.server
        if not self._is_local():
            self._send(403, {"status": "error",
                             "message": "solo se acepta localhost"})
            return
        if self.path != "/run":
            self._send(404, {"status": "error",
                             "message": "ruta no encontrada"})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY:
            self._send(400, {"status": "error",
                             "message": "cuerpo vacio o demasiado grande"})
            return
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._send(400, {"status": "error",
                             "message": "JSON invalido"})
            return
        token = data.get("token", "")
        command = data.get("command", "")
        if not isinstance(token, str) or not hmac.compare_digest(
                token.encode("utf-8"), EXPECTED_TOKEN.encode("utf-8")):
            log_command({"client": self.client_address[0],
                         "command": command if isinstance(command, str)
                         else "<no-texto>",
                         "allowed": False, "reason": "token-invalido"})
            self._send(403, {"status": "error",
                             "message": "token invalido"})
            return
        if command not in ALLOWED_COMMANDS:
            log_command({"client": self.client_address[0],
                         "command": command if isinstance(command, str)
                         else "<no-texto>",
                         "allowed": False, "reason": "no-en-lista-blanca"})
            self._send(400, {"status": "error",
                             "message": "comando no permitido"})
            return
        try:
            os.makedirs(RUNS_DIR, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            log_name = "run-%s.log" % stamp
            log_path = os.path.join(RUNS_DIR, log_name)
            with open(log_path, "ab") as out:
                proc = subprocess.Popen(
                    shlex.split(command),
                    stdin=subprocess.DEVNULL,
                    stdout=out,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    cwd=os.path.expanduser("~"),
                )
        except FileNotFoundError:
            log_command({"client": self.client_address[0],
                         "command": command,
                         "allowed": True, "reason": "ejecutable-no-encontrado"})
            self._send(500, {"status": "error",
                             "message": "ejecutable no encontrado en este "
                             "equipo (¿esta instalado?)"})
            return
        except Exception as exc:  # noqa: BLE001 - reportar sin tumbar
            log_command({"client": self.client_address[0],
                         "command": command,
                         "allowed": True,
                         "reason": "error-al-ejecutar: %s" % exc})
            self._send(500, {"status": "error",
                             "message": "no se pudo ejecutar: %s" % exc})
            return
        log_command({"client": self.client_address[0], "command": command,
                     "allowed": True, "pid": proc.pid, "log": log_name})
        self._send(200, {"status": "ok",
                         "message": "comando iniciado",
                         "pid": proc.pid,
                         "log": "runs/" + log_name})


def main():
    if EXPECTED_TOKEN == "MI_TOKEN_SECRETO_123":
        print("AVISO: usando el token de ejemplo. Define el tuyo con:")
        print('  export MUSE_TOKEN="tu-token-largo-y-aleatorio"')
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print("Muse Control escuchando SOLO en http://%s:%d (localhost)" %
          (HOST, PORT))
    print("Log de comandos: %s" % LOG_FILE)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
