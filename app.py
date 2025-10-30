from flask import Flask, request, jsonify, session, redirect, send_from_directory
import os
import uuid
import time
import json

app = Flask(__name__)
app.secret_key = 'my_secret_key_123'

# === ТВОИ ЛОГИНЫ И ПАРОЛИ ===
ADMINS = {
    "admin1": "12345",
    "admin2": "qwerty",
    "teacher": "secret"
}

os.makedirs("screenshots", exist_ok=True)
DATA_FILE = "data.json"

def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f)

data = load()

# === CORS ДЛЯ ВСЕХ ДОМЕНОВ ===
@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    return response

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("user", "")
        pw = request.form.get("pass", "")
        if user in ADMINS and ADMINS[user] == pw:
            session["user"] = user
            return redirect("/panel")
        return redirect("/login")
    
    return '''
    <h2 style="text-align:center; margin-top:100px;">Вход для помощников</h2>
    <form action="/login" method="post" style="width:300px; margin:auto;">
        <input name="user" placeholder="Логин" style="width:100%; padding:10px; margin:5px;" autocomplete="username"><br>
        <input name="pass" type="password" placeholder="Пароль" style="width:100%; padding:10px; margin:5px;" autocomplete="current-password"><br>
        <button style="width:100%; padding:12px; background:#4CAF50; color:white; border:none;">Войти</button>
    </form>
    '''

@app.route("/panel")
def panel():
    if "user" not in session:
        return redirect("/login")
    
    blocks = ""
    for uid, info in data.items():
        if not info.get("answered"):
            blocks += f'''
            <div style="border:1px solid #aaa; margin:15px; padding:15px; background:#f9f9f9;">
                <b>ID:</b> {uid}<br>
                <img src="/img/{uid}.png" style="max-width:100%; margin:10px 0;">
                <form action="/answer/{uid}" method="post">
                    <textarea name="answer" placeholder="Напиши ответ..." style="width:100%; height:60px;"></textarea><br>
                    <button style="padding:8px; background:green; color:white; border:none;">Отправить</button>
                </form>
            </div>
            '''
    
    return f'''
    <h1>Панель: {session["user"]} | <a href="/logout">Выйти</a></h1>
    <h3>Ожидают ответа: {len([x for x in data.values() if not x.get("answered")])}</h3>
    {blocks or "<p>Пока никто не спрашивал...</p>"}
    '''

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("image")
    if not file:
        return jsonify({"error": "No image"}), 400
    
    uid = str(uuid.uuid4())[:8]
    filepath = f"screenshots/{uid}.png"
    file.save(filepath)
    
    data[uid] = {"time": time.time(), "answered": False}
    save(data)
    
    return jsonify({"id": uid})

@app.route("/status/<uid>")
def status(uid):
    if uid in data and data[uid].get("answered"):
        return jsonify({"status": "ok", "answer": data[uid]["answer"]})
    return jsonify({"status": "wait"})

@app.route("/answer/<uid>", methods=["POST"])
def answer(uid):
    if "user" in session and uid in data:
        data[uid]["answer"] = request.form.get("answer", "")
        data[uid]["answered"] = True
        save(data)
    return redirect("/panel")

@app.route("/img/<name>")
def img(name):
    return send_from_directory("screenshots", name)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
