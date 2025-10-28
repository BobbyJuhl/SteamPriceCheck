# app.py
from flask import Flask, request, jsonify
import requests, pymysql, os, time
from datetime import datetime, timedelta

app = Flask(__name__)

# Config from environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASS = os.getenv("MYSQL_PASS", "")
MYSQL_DB   = os.getenv("MYSQL_DB", "steamapp")

def get_db():
    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASS,
        database=MYSQL_DB,
        autocommit=True
    )

def extract_steamid(url):
    try:
        if "/profiles/" in url:
            return url.split("/profiles/")[1].split("/")[0]
        elif "/id/" in url:
            return url.split("/id/")[1].split("/")[0]
    except Exception:
        return None

def get_cached_value(db, steamid):
    with db.cursor() as c:
        c.execute("SELECT value FROM inventory_values WHERE steamid=%s AND expires_at > NOW()", (steamid,))
        row = c.fetchone()
        return row[0] if row else None

def set_cached_value(db, steamid, value, ttl=300):
    expires = datetime.utcnow() + timedelta(seconds=ttl)
    with db.cursor() as c:
        c.execute("""REPLACE INTO inventory_values (steamid, value, expires_at)
                     VALUES (%s, %s, %s)""", (steamid, value, expires))

@app.route("/value", methods=["POST"])
def value():
    trade_url = request.form.get("trade_url") or request.json.get("trade_url")
    steamid = extract_steamid(trade_url)
    if not steamid:
        return jsonify({"error": "Invalid URL"}), 400

    db = get_db()
    cached = get_cached_value(db, steamid)
    if cached is not None:
        return jsonify({"steamid": steamid, "total": float(cached), "cached": True})

    # Fetch inventory
    inv_url = f"https://steamcommunity.com/inventory/{steamid}/730/2?l=english&count=5000"
    inv = requests.get(inv_url).json()

    # Placeholder logic
    total_value = 42.50  # Replace with real market API calls

    set_cached_value(db, steamid, total_value)
    return jsonify({"steamid": steamid, "total": total_value, "cached": False})

@app.route("/health")
def health():
    return "OK", 200
