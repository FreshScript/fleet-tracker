from flask import Flask, jsonify, render_template
import sqlite3
import random
import math
import time
from datetime import datetime, timedelta

app = Flask(__name__)
DB = "fleet.db"

# Zambia/Lusaka area coordinates as base
VEHICLES = [
    {"id": "ZM-001", "name": "Truck Alpha",   "type": "truck",  "lat": -15.4167, "lng": 28.2833},
    {"id": "ZM-002", "name": "Van Beta",      "type": "van",    "lat": -15.4250, "lng": 28.3100},
    {"id": "ZM-003", "name": "Car Gamma",     "type": "car",    "lat": -15.4000, "lng": 28.2600},
    {"id": "ZM-004", "name": "Truck Delta",   "type": "truck",  "lat": -15.4400, "lng": 28.3300},
    {"id": "ZM-005", "name": "Van Epsilon",   "type": "van",    "lat": -15.4100, "lng": 28.2950},
]

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id TEXT PRIMARY KEY,
            name TEXT,
            type TEXT,
            status TEXT DEFAULT 'active'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gps_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id TEXT,
            latitude REAL,
            longitude REAL,
            speed REAL,
            heading REAL,
            timestamp TEXT,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id TEXT,
            alert_type TEXT,
            message TEXT,
            timestamp TEXT
        )
    """)
    # Seed vehicles
    for v in VEHICLES:
        conn.execute("INSERT OR IGNORE INTO vehicles (id, name, type) VALUES (?, ?, ?)",
                     (v["id"], v["name"], v["type"]))

    # Seed historical GPS data (last 24 hours)
    now = datetime.now()
    for v in VEHICLES:
        lat, lng = v["lat"], v["lng"]
        for i in range(48):
            ts = now - timedelta(minutes=30 * i)
            lat += random.uniform(-0.005, 0.005)
            lng += random.uniform(-0.005, 0.005)
            speed = random.uniform(0, 100)
            heading = random.uniform(0, 360)
            conn.execute(
                "INSERT INTO gps_data (vehicle_id, latitude, longitude, speed, heading, timestamp) VALUES (?,?,?,?,?,?)",
                (v["id"], round(lat, 6), round(lng, 6), round(speed, 1), round(heading, 1), ts.strftime("%Y-%m-%d %H:%M:%S"))
            )

    # Seed some alerts
    alert_types = [("speeding", "Speed exceeded 90 km/h"), ("geofence", "Vehicle left designated zone"), ("idle", "Engine idle for 30+ minutes")]
    for v in VEHICLES[:3]:
        atype, amsg = random.choice(alert_types)
        conn.execute("INSERT INTO alerts (vehicle_id, alert_type, message, timestamp) VALUES (?,?,?,?)",
                     (v["id"], atype, amsg, (now - timedelta(hours=random.randint(1,5))).strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/vehicles")
def api_vehicles():
    conn = get_db()
    vehicles = conn.execute("SELECT * FROM vehicles").fetchall()
    result = []
    for v in vehicles:
        latest = conn.execute(
            "SELECT * FROM gps_data WHERE vehicle_id=? ORDER BY timestamp DESC LIMIT 1", (v["id"],)
        ).fetchone()
        result.append({
            "id": v["id"],
            "name": v["name"],
            "type": v["type"],
            "status": v["status"],
            "lat": latest["latitude"] if latest else None,
            "lng": latest["longitude"] if latest else None,
            "speed": latest["speed"] if latest else 0,
            "heading": latest["heading"] if latest else 0,
            "last_seen": latest["timestamp"] if latest else "N/A"
        })
    conn.close()
    return jsonify(result)

@app.route("/api/vehicles/<vehicle_id>/history")
def api_vehicle_history(vehicle_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM gps_data WHERE vehicle_id=? ORDER BY timestamp DESC LIMIT 20", (vehicle_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/live")
def api_live():
    """Simulate live GPS updates by slightly moving each vehicle"""
    conn = get_db()
    vehicles = conn.execute("SELECT * FROM vehicles").fetchall()
    updates = []
    for v in vehicles:
        latest = conn.execute(
            "SELECT * FROM gps_data WHERE vehicle_id=? ORDER BY timestamp DESC LIMIT 1", (v["id"],)
        ).fetchone()
        if latest:
            new_lat = latest["latitude"] + random.uniform(-0.001, 0.001)
            new_lng = latest["longitude"] + random.uniform(-0.001, 0.001)
            new_speed = max(0, latest["speed"] + random.uniform(-5, 5))
            new_heading = (latest["heading"] + random.uniform(-10, 10)) % 360
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "INSERT INTO gps_data (vehicle_id, latitude, longitude, speed, heading, timestamp) VALUES (?,?,?,?,?,?)",
                (v["id"], round(new_lat, 6), round(new_lng, 6), round(new_speed, 1), round(new_heading, 1), now)
            )
            updates.append({
                "id": v["id"], "name": v["name"], "type": v["type"],
                "lat": round(new_lat, 6), "lng": round(new_lng, 6),
                "speed": round(new_speed, 1), "heading": round(new_heading, 1),
                "last_seen": now
            })
    conn.commit()
    conn.close()
    return jsonify(updates)

@app.route("/api/alerts")
def api_alerts():
    conn = get_db()
    rows = conn.execute(
        "SELECT a.*, v.name as vehicle_name FROM alerts a JOIN vehicles v ON a.vehicle_id = v.id ORDER BY timestamp DESC LIMIT 10"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/stats")
def api_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) as c FROM vehicles").fetchone()["c"]
    active = conn.execute("SELECT COUNT(DISTINCT vehicle_id) as c FROM gps_data WHERE timestamp >= datetime('now', '-1 hour')").fetchone()["c"]
    total_points = conn.execute("SELECT COUNT(*) as c FROM gps_data").fetchone()["c"]
    alerts = conn.execute("SELECT COUNT(*) as c FROM alerts").fetchone()["c"]
    conn.close()
    return jsonify({
        "total_vehicles": total,
        "active_vehicles": active,
        "total_gps_points": total_points,
        "total_alerts": alerts
    })

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
