import socket
from threading import Thread
from pyngrok import ngrok
from app import app, init_db


DEFAULT_PORT = 5000


def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def start_flask(port):
    init_db()
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    port = DEFAULT_PORT
    if port_in_use(port):
        port = 5001

    flask_thread = Thread(target=start_flask, args=(port,), daemon=True)
    flask_thread.start()

    public_url = ngrok.connect(port, bind_tls=True).public_url
    print(f"Flask rodando na porta {port}.")
    print(f"Acesso público: {public_url}")
    print("Copie essa URL e envie para seu amigo.")
    print("Pressione Enter para encerrar.")
    input()
    ngrok.disconnect(public_url)
    ngrok.kill()
