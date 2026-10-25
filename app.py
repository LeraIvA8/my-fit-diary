import hashlib
import os
import secrets

import psycopg
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from psycopg.rows import dict_row

load_dotenv()                              # прочитать .env
DATABASE_URL = os.environ["DATABASE_URL"]  # достать адрес базы по имени

app = Flask(__name__)
app.json.ensure_ascii = False  # русские буквы в JSON без Л...
ph = PasswordHasher()          # хешировщик паролей


def hash_token(token):
    # в базе храним не сам токен, а его хеш (64 символа)
    return hashlib.sha256(token.encode()).hexdigest()


def current_user():
    # кто прислал запрос: по токену из cookie находим живую сессию и её пользователя
    token = request.cookies.get("session")
    if not token:
        return None
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        return conn.execute(
            "SELECT users.id, users.name, users.email "
            "FROM sessions JOIN users ON users.id = sessions.user_id "
            "WHERE sessions.token_hash = %s AND sessions.expires_at > now()",
            (hash_token(token),),
        ).fetchone()  # None, если сессии нет или она истекла


@app.route("/")  # декоратор: связывает главную страницу сайта с функцией ниже
def hello_world():
    return "<p>Hello, World</p>"


@app.route("/api/test")
def api_test():
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        users = conn.execute("SELECT id, name, email FROM users").fetchall()
    return users


@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}  # данные от браузера; {} если прислали не JSON
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "Заполните все поля"}), 400

    if len(password) < 8:
        return jsonify({"error": "Пароль должен содержать не менее 8 символов"}), 400

    password_hash = ph.hash(password)

    try:
        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
            user = conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                (name, email, password_hash),
            ).fetchone()
    except psycopg.errors.UniqueViolation:
        return jsonify({"error": "Почта уже занята"}), 409
    return jsonify({"id": user["id"]}), 201


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Заполните все поля"}), 400

    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        user = conn.execute(
            "SELECT id, password_hash FROM users WHERE email = %s", (email,)
        ).fetchone()

    # одинаковый ответ, чтобы нельзя было узнать, какие почты зарегистрированы
    if not user:
        return jsonify({"error": "Неверная почта или пароль"}), 401
    try:
        ph.verify(user["password_hash"], password)
    except VerifyMismatchError:
        return jsonify({"error": "Неверная почта или пароль"}), 401

    token = secrets.token_urlsafe(32)  # случайный «пропуск»

    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) "
            "VALUES (%s, %s, now() + interval '30 days')",
            (hash_token(token), user["id"]),
        )

    # браузеру отдаём сам токен, httponly — JavaScript не сможет его прочитать
    response = jsonify({"id": user["id"]})
    response.set_cookie("session", token, httponly=True, samesite="Lax", max_age=30 * 24 * 3600)
    return response


@app.get("/api/me")
def me():
    user = current_user()
    if not user:
        return jsonify({"error": "Нужно войти"}), 401
    return user


@app.post("/api/logout")
def logout():
    token = request.cookies.get("session")
    if token:
        # удаляем сессию из базы — старый токен больше не сработает
        with psycopg.connect(DATABASE_URL) as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = %s", (hash_token(token),))
    response = jsonify({"ok": True})
    response.delete_cookie("session")  # и стираем cookie в браузере
    return response


if __name__ == "__main__":
    app.run(port=5000, debug=True)
