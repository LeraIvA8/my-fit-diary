import os
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row
from flask import Flask
load_dotenv()                              # прочитать .env
DATABASE_URL = os.environ["DATABASE_URL"]  # достать адрес базы по имени
app = Flask(__name__)

@app.route("/") #декоратор кот связывает главн страницу сайта с функцией ниже
def hello_world():
    return "<p>Hello , Word</p>"

@app.route("/api/test")
def api_test():
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        users = conn.execute("SELECT id, name, email FROM users").fetchall()
    return users

if __name__ == "__main__":
    app.run(port=5000, debug=True)