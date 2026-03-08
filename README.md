# FleetTrack — GPS Fleet Management System

A real-time GPS vehicle tracking and fleet management platform built with Python (Flask), SQLite, and Leaflet.js.

## Features

- **Live vehicle tracking** on an interactive dark-themed map
- **Real-time GPS data** updates every 4 seconds
- **Fleet dashboard** showing speed, heading, and last ping per vehicle
- **Alert system** for speeding, geofence violations, and idle detection
- **REST API** for GPS data ingestion, vehicle management, and statistics
- **SQLite database** storing historical GPS points and alert logs

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3, Flask |
| Database | SQLite (easily swappable to PostgreSQL/MySQL) |
| Frontend | HTML5, CSS3, JavaScript |
| Maps | Leaflet.js with CartoDB dark tiles |
| API | RESTful JSON endpoints |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/vehicles` | GET | All vehicles with latest GPS position |
| `/api/vehicles/<id>/history` | GET | Historical GPS trail for a vehicle |
| `/api/live` | GET | Simulate live GPS update tick |
| `/api/alerts` | GET | Recent system alerts |
| `/api/stats` | GET | Fleet-wide statistics |

## Database Schema

```sql
vehicles      — id, name, type, status
gps_data      — vehicle_id, latitude, longitude, speed, heading, timestamp
alerts        — vehicle_id, alert_type, message, timestamp
```

## Setup & Run

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/fleet-tracker.git
cd fleet-tracker

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py

# 4. Open in browser
# http://localhost:5000
```

## Real GPS Device Integration

To connect real GPS hardware (e.g. GT06, Teltonika), replace the `/api/live` simulation with a TCP socket server:

```python
import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 5023))  # Standard GT06 port
server.listen(5)

while True:
    conn, addr = server.accept()
    data = conn.recv(1024)
    # Parse NMEA or proprietary protocol here
    # Insert parsed lat/lng/speed into gps_data table
```

## Screenshots

> Dashboard showing 5 live vehicles on a dark map with real-time speed bars, alert panel, and vehicle details.

## Architecture

```
GPS Devices → TCP Socket Server → Flask API → SQLite DB
                                      ↕
                              Browser Dashboard
                           (Leaflet Map + Live Updates)
```

## License

MIT License — free to use and modify.
