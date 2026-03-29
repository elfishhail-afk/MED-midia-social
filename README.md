# Social Media Demo

Um aplicativo web simples de rede social em Flask com autenticação básica e proteção contra XSS.

## Como usar

1. Instale dependências:

```bash
python -m pip install -r requirements.txt
```

2. Execute o aplicativo:

```bash
python app.py
```

3. Abra `http://127.0.0.1:5000` no navegador.

4. Para acessar pela rede local, use o IP da máquina:

```bash
http://<seu-ip-local>:5000
```

5. Para permitir acesso de fora da sua rede (internet pública), a forma mais confiável é hospedar o app em um serviço cloud. Exemplo:

- Render
- Railway
- PythonAnywhere

Use `gunicorn` para executar o app em produção.

### Deploy rápido

- `Procfile` foi adicionado para plataformas compatíveis.
- `Dockerfile` foi adicionado para deploy em conteiner.
- `render.yaml` foi adicionado para facilitar o deploy no Render.

```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```

### Deploy no Render

1. Faça push do código para o GitHub.
2. Acesse `https://render.com` e crie conta.
3. Clique em **New** → **Web Service**.
4. Conecte o repositório GitHub.
5. O Render deve detectar `render.yaml` e usar o `Dockerfile`.
6. Escolha a branch `main`.
7. Crie o serviço e aguarde o deploy.

Depois disso, o Render vai fornecer uma URL pública estável.

> Nota: o túnel gratuito `serveo` ou `localhost.run` pode ser instável e gerar erro 502. O método mais seguro é hospedar em um serviço cloud.
> Se o serveo não funcionar, use `python run_with_tunnel.py` ou `python serveo_tunnel.py` após instalar `pyngrok`.

## Recursos

- Registro de usuário
- Login/logout
- Criação de posts
- Exibição de posts em ordem cronológica inversa
- Proteção CSRF em formulários POST
- Cabeçalhos de segurança HTTP (CSP, X-Frame-Options, no-sniff)
- Proteção XSS via autoescape do Jinja2 e SQL parametrizado
