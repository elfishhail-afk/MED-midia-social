import re
import socket
import subprocess
import time
import shutil
from pathlib import Path
from threading import Thread
from app import app, init_db

DEFAULT_PORT = 5000
URL_FILE = Path("serveo_url.txt")


def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def start_flask(port):
    init_db()
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


def start_serveo_tunnel(port):
    if shutil.which("ssh") is None:
        raise RuntimeError("Comando 'ssh' não encontrado. Instale o SSH ou use o fallback ngrok.")

    command = [
        "ssh",
        "-o",
        "ExitOnForwardFailure=yes",
        "-o",
        "ServerAliveInterval=60",
        "-o",
        "StrictHostKeyChecking=no",
        "-R",
        f"80:localhost:{port}",
        "serveo.net",
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    public_url = None
    url_pattern = re.compile(r'https://[^\s]+')

    while True:
        line = process.stdout.readline()
        if not line:
            if process.poll() is not None:
                raise RuntimeError("Tunnel process terminated unexpectedly")
            time.sleep(0.1)
            continue

        print(line.strip())
        match = url_pattern.search(line)
        if match:
            public_url = match.group(0)
            break

    if not public_url:
        process.terminate()
        raise RuntimeError("Não foi possível obter a URL pública do túnel serveo.")

    print(f"URL pública: {public_url}")
    URL_FILE.write_text(public_url, encoding="utf-8")
    print("O túnel serveo está ativo. Deixe este script rodando enquanto o acesso remoto estiver disponível.")
    process.wait()


def start_ngrok_tunnel(port):
    try:
        from pyngrok import ngrok
    except ImportError as exc:
        raise RuntimeError(
            "pyngrok não está instalado. Execute 'pip install pyngrok' ou instale a dependência no requirements.txt."
        ) from exc

    public_url = ngrok.connect(port, bind_tls=True).public_url
    if not public_url:
        raise RuntimeError("Não foi possível obter a URL pública do ngrok.")

    URL_FILE.write_text(public_url, encoding="utf-8")
    print(f"URL pública: {public_url}")
    print("O túnel ngrok está ativo. Deixe este script rodando enquanto o acesso remoto estiver disponível.")
    return public_url


if __name__ == "__main__":
    port = DEFAULT_PORT
    if port_in_use(port):
        port = 5001

    flask_thread = Thread(target=start_flask, args=(port,), daemon=True)
    flask_thread.start()
    time.sleep(1)

    try:
        start_serveo_tunnel(port)
    except Exception as exc:
        print(f"Serveo falhou: {exc}")
        print("Tentando fallback com ngrok...")
        public_url = start_ngrok_tunnel(port)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Encerrando túnel ngrok...")
            from pyngrok import ngrok
            ngrok.disconnect(public_url)
            ngrok.kill()
