from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, abort
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "social.db")
SECRET_FILE = os.path.join(BASE_DIR, ".secret_key")

app = Flask(__name__)


def load_or_create_secret_key():
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key

    if os.path.exists(SECRET_FILE):
        with open(SECRET_FILE, "r", encoding="utf-8") as secret_file:
            return secret_file.read().strip()

    secret_key = secrets.token_urlsafe(32)
    with open(SECRET_FILE, "w", encoding="utf-8") as secret_file:
        secret_file.write(secret_key)
    return secret_key


app.config["SECRET_KEY"] = load_or_create_secret_key()
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() in ("1", "true", "yes")
app.config["TEMPLATES_AUTO_RELOAD"] = False


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


app.teardown_appcontext(close_db)


def get_csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


@app.context_processor
def inject_csrf_token():
    return {"csrf_token": get_csrf_token()}


def validate_csrf():
    if request.method == "POST":
        token = session.get("csrf_token")
        form_token = request.form.get("csrf_token", "")
        if not token or not form_token or not secrets.compare_digest(token, form_token):
            abort(400)


@app.after_request
def set_secure_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self';"
    if request.is_secure:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    return response


def query_db(query, args=(), one=False):
    db = get_db()
    cursor = db.execute(query, args)
    rows = cursor.fetchall()
    cursor.close()
    if one:
        return rows[0] if rows else None
    return rows


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )
    db.commit()
    db.close()


def ensure_database():
    if not os.path.exists(DB_PATH):
        init_db()


ensure_database()


@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = query_db(
        "SELECT id, username FROM users WHERE id = ?",
        (user_id,),
        one=True,
    ) if user_id else None


@app.context_processor
def inject_user():
    return {"user": g.get("user")}


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped_view


def get_posts():
    return query_db(
        "SELECT posts.id, posts.message, posts.created_at, users.username "
        "FROM posts JOIN users ON posts.user_id = users.id "
        "ORDER BY posts.created_at DESC"
    )


def create_user(username, password):
    db = get_db()
    db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, generate_password_hash(password)),
    )
    db.commit()


def add_post(user_id, message):
    db = get_db()
    db.execute(
        "INSERT INTO posts (user_id, message) VALUES (?, ?)",
        (user_id, message),
    )
    db.commit()


@app.route("/")
@login_required
def index():
    posts = get_posts()
    return render_template("index.html", posts=posts, stats={"posts_count": len(posts)})


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        validate_csrf()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "error")
            return render_template("register.html")

        if len(username) > 30:
            flash("Username must be at most 30 characters.", "error")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must have at least 8 characters.", "error")
            return render_template("register.html")

        try:
            create_user(username, password)
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists.", "error")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        validate_csrf()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = query_db(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,),
            one=True,
        )

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("index"))

        flash("Login failed. Check your username and password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/create-post", methods=["POST"])
@login_required
def create_post():
    validate_csrf()
    message = request.form.get("message", "").strip()
    if not message:
        flash("A post cannot be empty.", "error")
        return redirect(url_for("index"))

    if len(message) > 500:
        flash("Post cannot be longer than 500 characters.", "error")
        return redirect(url_for("index"))

    add_post(g.user["id"], message)
    flash("Post created successfully.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
