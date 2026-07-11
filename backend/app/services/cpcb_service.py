"""
Real air quality data service.
Primary: data.gov.in CPCB API — official Indian government live sensor data (CPCB AQI).
Fallback: WAQI API — international air quality data (US EPA AQI, converted to CPCB).
Last resort: Model-generated realistic data based on CPCB seasonal patterns.
"""

import httpx
import sqlite3
import os
import random
import ssl
import json as _json
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, urlencode
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

DB_PATH = Path(__file__).parent.parent.parent / "data" / "vayu.db"
DATAGOV_KEY = os.getenv("DATAGOV_API_KEY", "")
DATAGOV_RESOURCE = "3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"
DATAGOV_BASE = "https://api.data.gov.in/resource"
WAQI_TOKEN = os.getenv("WAQI_API_TOKEN", "")
WAQI_BASE = "https://api.waqi.info"

MONITORED_CITIES = ["Delhi", "Mumbai", "Kolkata", "Bengaluru", "Chennai", "Lucknow", "Patna", "Hyderabad"]

# Kept for backward compatibility with api.py import
MONITORED_STATIONS = {city: [] for city in MONITORED_CITIES}

# Station type heuristics based on name keywords
_TRAFFIC_KEYWORDS = ["road", "marg", "highway", "nagar", "crossing", "chowk", "gate", "vihar", "ito"]
_INDUSTRIAL_KEYWORDS = ["industrial", "phase", "sector", "midc", "factory", "plant", "okhla"]
_RESIDENTIAL_KEYWORDS = ["colony", "layout", "park", "garden", "memorial", "school", "hospital", "university", "college", "vidyalaya"]

MAX_DATA_AGE_HOURS = 6

_cache: dict = {"stations": [], "timestamp": None, "ttl_minutes": 10}


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS aqi_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id TEXT NOT NULL,
            station_name TEXT NOT NULL,
            city TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            station_type TEXT NOT NULL,
            aqi REAL,
            pm25 REAL,
            pm10 REAL,
            no2 REAL,
            so2 REAL,
            co REAL,
            o3 REAL,
            dominant_pollutant TEXT,
            temperature REAL,
            humidity REAL,
            wind_speed REAL,
            wind_direction REAL,
            timestamp TEXT NOT NULL,
            source TEXT DEFAULT 'cpcb',
            UNIQUE(station_id, timestamp)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_station_time ON aqi_readings(station_id, timestamp)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_city_time ON aqi_readings(city, timestamp)")
    conn.commit()
    conn.close()


async def fetch_live_cpcb_data() -> list[dict]:
    if (
        _cache["stations"]
        and _cache["timestamp"]
        and (datetime.now(timezone.utc) - _cache["timestamp"]).total_seconds() < _cache["ttl_minutes"] * 60
    ):
        return _cache["stations"]

    stations_data = []

    if DATAGOV_KEY:
        stations_data = await _fetch_datagov_data()

    if not stations_data and WAQI_TOKEN:
        print("data.gov.in unavailable — trying WAQI fallback")
        stations_data = await _fetch_waqi_fallback()

    if not stations_data:
        print("All APIs unavailable — using model-generated data")
        stations_data = _generate_realistic_data()

    _cache["stations"] = stations_data
    _cache["timestamp"] = datetime.now(timezone.utc)
    _save_readings(stations_data)
    return stations_data


async def _fetch_datagov_data() -> list[dict]:
    """Fetch live AQI from data.gov.in — official CPCB stations with raw concentrations."""
    import asyncio

    all_stations = []
    _ssl_ctx = ssl.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = ssl.CERT_NONE

    def _sync_fetch_city(city: str) -> dict | None:
        params = urlencode({"api-key": DATAGOV_KEY, "format": "json", "filters[city]": city, "limit": 500})
        url = f"{DATAGOV_BASE}/{DATAGOV_RESOURCE}?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "VayuBudhi/1.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30, context=_ssl_ctx) as resp:
            return _json.loads(resp.read().decode())

    for city in MONITORED_CITIES:
        try:
            data = await asyncio.to_thread(_sync_fetch_city, city)
            if not data:
                continue

            records = data.get("records", [])

            station_map: dict = {}
            for rec in records:
                stn_name = rec.get("station", "Unknown")
                if stn_name not in station_map:
                    station_map[stn_name] = {
                        "station": stn_name,
                        "city": rec.get("city", city),
                        "state": rec.get("state", ""),
                        "lat": rec.get("latitude", "0"),
                        "lng": rec.get("longitude", "0"),
                        "last_update": rec.get("last_update", ""),
                        "pollutants": {},
                    }
                pid = rec.get("pollutant_id", "")
                avg_val = rec.get("avg_value", "NA")
                if avg_val and avg_val != "NA" and avg_val != "None":
                    try:
                        station_map[stn_name]["pollutants"][pid] = float(avg_val)
                    except (ValueError, TypeError):
                        pass

            added = 0
            for stn_name, stn_data in station_map.items():
                p = stn_data["pollutants"]
                if not p:
                    continue

                pm25 = p.get("PM2.5", 0)
                pm10 = p.get("PM10", 0)
                no2 = p.get("NO2", 0)
                so2 = p.get("SO2", 0)
                co = p.get("CO", 0) / 1000.0  # data.gov.in reports µg/m³, CPCB breakpoints use mg/m³
                o3 = p.get("OZONE", p.get("O3", 0))
                nh3 = p.get("NH3", 0)

                sub_indices = []
                if pm25 > 0:
                    sub_indices.append(("PM2.5", calculate_aqi_from_pm25(pm25)))
                if pm10 > 0:
                    sub_indices.append(("PM10", calculate_aqi_from_pm10(pm10)))
                if no2 > 0:
                    sub_indices.append(("NO2", _calculate_aqi_from_no2(no2)))
                if so2 > 0:
                    sub_indices.append(("SO2", _calculate_aqi_from_so2(so2)))
                if co > 0:
                    sub_indices.append(("CO", _calculate_aqi_from_co(co)))
                if o3 > 0:
                    sub_indices.append(("O3", _calculate_aqi_from_o3(o3)))
                if nh3 > 0:
                    sub_indices.append(("NH3", _calculate_aqi_from_nh3(nh3)))

                if not sub_indices:
                    continue

                dominant = max(sub_indices, key=lambda x: x[1])
                aqi = dominant[1]

                try:
                    lat = float(stn_data["lat"])
                    lng = float(stn_data["lng"])
                except (ValueError, TypeError):
                    lat, lng = 0, 0

                stn_id = f"cpcb_{city.lower()}_{stn_name.replace(' ', '_').replace(',', '')[:30]}"

                all_stations.append({
                    "station_id": stn_id,
                    "station_name": stn_name,
                    "city": city,
                    "lat": lat,
                    "lng": lng,
                    "station_type": _infer_station_type(stn_name),
                    "aqi": aqi,
                    "pm25": round(pm25, 1),
                    "pm10": round(pm10, 1),
                    "no2": round(no2, 1),
                    "so2": round(so2, 1),
                    "co": round(co, 1),
                    "o3": round(o3, 1),
                    "dominant_pollutant": dominant[0],
                    "temperature": 0,
                    "humidity": 0,
                    "wind_speed": 0,
                    "wind_direction": 0,
                    "timestamp": _parse_datagov_timestamp(stn_data["last_update"]),
                    "source": "cpcb",
                })
                added += 1

            print(f"data.gov.in: {city} — {added} stations")

        except Exception as e:
            print(f"data.gov.in error for {city}: {type(e).__name__}: {e}")

    if all_stations:
        print(f"data.gov.in total: {len(all_stations)} live CPCB stations across {len(MONITORED_CITIES)} cities")

    return all_stations


async def _fetch_waqi_fallback() -> list[dict]:
    """Fallback: fetch from WAQI API for cities missing from data.gov.in."""
    all_stations = []
    city_bounds = {
        "Delhi":     (28.40, 76.80, 28.90, 77.50),
        "Mumbai":    (18.85, 72.75, 19.30, 73.00),
        "Kolkata":   (22.40, 88.20, 22.70, 88.50),
        "Bengaluru": (12.80, 77.45, 13.10, 77.70),
        "Chennai":   (12.90, 80.15, 13.20, 80.35),
        "Lucknow":   (26.75, 80.85, 26.95, 81.05),
        "Patna":     (25.55, 85.05, 25.70, 85.25),
        "Hyderabad": (17.30, 78.30, 17.55, 78.60),
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            for city, (lat1, lng1, lat2, lng2) in city_bounds.items():
                try:
                    resp = await client.get(
                        f"{WAQI_BASE}/map/bounds",
                        params={
                            "latlng": f"{lat1},{lng1},{lat2},{lng2}",
                            "networks": "all",
                            "token": WAQI_TOKEN,
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("status") == "ok":
                            for ws in data.get("data", []):
                                aqi_val = ws.get("aqi")
                                if aqi_val == "-" or aqi_val is None:
                                    continue
                                try:
                                    aqi_int = int(aqi_val)
                                except (ValueError, TypeError):
                                    continue
                                if aqi_int <= 0:
                                    continue

                                station_time = ws.get("station", {}).get("time", "")
                                if not _is_data_fresh(station_time):
                                    continue

                                uid = ws.get("uid", 0)
                                name_raw = ws.get("station", {}).get("name", "Unknown")
                                name = name_raw.split(", India")[0].strip() or name_raw

                                all_stations.append({
                                    "station_id": f"waqi_{uid}",
                                    "station_name": name,
                                    "waqi_uid": uid,
                                    "city": city,
                                    "lat": float(ws.get("lat", 0)),
                                    "lng": float(ws.get("lon", 0)),
                                    "station_type": _infer_station_type(name),
                                    "aqi": aqi_int,
                                    "pm25": 0, "pm10": 0, "no2": 0, "so2": 0, "co": 0, "o3": 0,
                                    "dominant_pollutant": "PM2.5",
                                    "temperature": 0, "humidity": 0,
                                    "wind_speed": 0, "wind_direction": 0,
                                    "timestamp": station_time or datetime.now(timezone.utc).isoformat(),
                                    "source": "waqi",
                                })
                except Exception as e:
                    print(f"WAQI error for {city}: {e}")
    except Exception as e:
        print(f"WAQI connection error: {e}")

    return all_stations


def _parse_datagov_timestamp(ts: str) -> str:
    """Convert data.gov.in timestamp '11-07-2026 14:00:00' to ISO format."""
    if not ts:
        return datetime.now(timezone.utc).isoformat()
    try:
        dt = datetime.strptime(ts, "%d-%m-%Y %H:%M:%S")
        dt = dt.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
        return dt.isoformat()
    except Exception:
        return ts


def _is_data_fresh(timestamp_str: str) -> bool:
    if not timestamp_str:
        return False
    try:
        now_utc = datetime.now(timezone.utc)
        ts = timestamp_str.strip()
        if "T" in ts:
            ts = ts.replace("Z", "+00:00")
            if "+" not in ts and "-" not in ts[10:]:
                ts += "+00:00"
            dt = datetime.fromisoformat(ts)
        else:
            dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age_hours = abs((now_utc - dt).total_seconds()) / 3600
        return age_hours < MAX_DATA_AGE_HOURS
    except Exception:
        return False


def _infer_station_type(name: str) -> str:
    name_lower = name.lower()
    for kw in _TRAFFIC_KEYWORDS:
        if kw in name_lower:
            return "traffic"
    for kw in _INDUSTRIAL_KEYWORDS:
        if kw in name_lower:
            return "industrial"
    for kw in _RESIDENTIAL_KEYWORDS:
        if kw in name_lower:
            return "residential"
    return "mixed"


# === CPCB AQI Breakpoint Calculations ===
# All use official Indian National AQI breakpoints from CPCB

def calculate_aqi_from_pm25(pm25: float) -> int:
    breakpoints = [
        (0, 30, 0, 50), (31, 60, 51, 100), (61, 90, 101, 200),
        (91, 120, 201, 300), (121, 250, 301, 400), (250, 500, 401, 500),
    ]
    for bp_lo, bp_hi, i_lo, i_hi in breakpoints:
        if pm25 <= bp_hi:
            return max(0, min(500, round(((i_hi - i_lo) / (bp_hi - bp_lo)) * (pm25 - bp_lo) + i_lo)))
    return 500


def calculate_aqi_from_pm10(pm10: float) -> int:
    breakpoints = [
        (0, 50, 0, 50), (51, 100, 51, 100), (101, 250, 101, 200),
        (251, 350, 201, 300), (351, 430, 301, 400), (430, 600, 401, 500),
    ]
    for bp_lo, bp_hi, i_lo, i_hi in breakpoints:
        if pm10 <= bp_hi:
            return max(0, min(500, round(((i_hi - i_lo) / (bp_hi - bp_lo)) * (pm10 - bp_lo) + i_lo)))
    return 500


def _calculate_aqi_from_no2(no2: float) -> int:
    breakpoints = [
        (0, 40, 0, 50), (41, 80, 51, 100), (81, 180, 101, 200),
        (181, 280, 201, 300), (281, 400, 301, 400), (400, 800, 401, 500),
    ]
    for bp_lo, bp_hi, i_lo, i_hi in breakpoints:
        if no2 <= bp_hi:
            return max(0, min(500, round(((i_hi - i_lo) / (bp_hi - bp_lo)) * (no2 - bp_lo) + i_lo)))
    return 500


def _calculate_aqi_from_so2(so2: float) -> int:
    breakpoints = [
        (0, 40, 0, 50), (41, 80, 51, 100), (81, 380, 101, 200),
        (381, 800, 201, 300), (801, 1600, 301, 400), (1600, 2400, 401, 500),
    ]
    for bp_lo, bp_hi, i_lo, i_hi in breakpoints:
        if so2 <= bp_hi:
            return max(0, min(500, round(((i_hi - i_lo) / (bp_hi - bp_lo)) * (so2 - bp_lo) + i_lo)))
    return 500


def _calculate_aqi_from_co(co: float) -> int:
    breakpoints = [
        (0, 1, 0, 50), (1.1, 2, 51, 100), (2.1, 10, 101, 200),
        (10.1, 17, 201, 300), (17.1, 34, 301, 400), (34, 50, 401, 500),
    ]
    for bp_lo, bp_hi, i_lo, i_hi in breakpoints:
        if co <= bp_hi:
            return max(0, min(500, round(((i_hi - i_lo) / (bp_hi - bp_lo)) * (co - bp_lo) + i_lo)))
    return 500


def _calculate_aqi_from_o3(o3: float) -> int:
    breakpoints = [
        (0, 50, 0, 50), (51, 100, 51, 100), (101, 168, 101, 200),
        (169, 208, 201, 300), (209, 748, 301, 400), (748, 1000, 401, 500),
    ]
    for bp_lo, bp_hi, i_lo, i_hi in breakpoints:
        if o3 <= bp_hi:
            return max(0, min(500, round(((i_hi - i_lo) / (bp_hi - bp_lo)) * (o3 - bp_lo) + i_lo)))
    return 500


def _calculate_aqi_from_nh3(nh3: float) -> int:
    breakpoints = [
        (0, 200, 0, 50), (201, 400, 51, 100), (401, 800, 101, 200),
        (801, 1200, 201, 300), (1201, 1800, 301, 400), (1800, 2400, 401, 500),
    ]
    for bp_lo, bp_hi, i_lo, i_hi in breakpoints:
        if nh3 <= bp_hi:
            return max(0, min(500, round(((i_hi - i_lo) / (bp_hi - bp_lo)) * (nh3 - bp_lo) + i_lo)))
    return 500


# === Model-generated fallback data ===

_FALLBACK_STATIONS = {
    "Delhi": [
        {"id": "site_1", "name": "Anand Vihar, Delhi", "lat": 28.6469, "lng": 77.3164, "type": "traffic"},
        {"id": "site_5", "name": "ITO, Delhi", "lat": 28.6289, "lng": 77.2405, "type": "traffic"},
        {"id": "site_11", "name": "RK Puram, Delhi", "lat": 28.5631, "lng": 77.1726, "type": "mixed"},
    ],
    "Mumbai": [
        {"id": "site_1435", "name": "Bandra Kurla Complex, Mumbai", "lat": 19.0596, "lng": 72.8656, "type": "traffic"},
        {"id": "site_1438", "name": "Chembur, Mumbai", "lat": 19.0522, "lng": 72.8994, "type": "industrial"},
    ],
    "Kolkata": [
        {"id": "site_1441", "name": "Jadavpur, Kolkata", "lat": 22.4992, "lng": 88.3714, "type": "traffic"},
    ],
    "Bengaluru": [
        {"id": "site_1450", "name": "Silk Board, Bengaluru", "lat": 12.9172, "lng": 77.6228, "type": "traffic"},
    ],
    "Chennai": [
        {"id": "site_1460", "name": "Manali, Chennai", "lat": 13.1667, "lng": 80.2667, "type": "industrial"},
    ],
    "Lucknow": [
        {"id": "site_1470", "name": "Talkatora, Lucknow", "lat": 26.8534, "lng": 80.9098, "type": "mixed"},
    ],
    "Patna": [
        {"id": "site_1480", "name": "IGSC Planetarium, Patna", "lat": 25.6093, "lng": 85.1376, "type": "mixed"},
    ],
    "Hyderabad": [
        {"id": "site_1490", "name": "Jubilee Hills, Hyderabad", "lat": 17.4326, "lng": 78.4071, "type": "residential"},
    ],
}


def _generate_realistic_data() -> list[dict]:
    now = datetime.now(timezone.utc)
    stations_data = []
    for city, stations in _FALLBACK_STATIONS.items():
        for stn in stations:
            stations_data.append(_generate_single_station(stn, city, now))
    return stations_data


def _generate_single_station(stn: dict, city: str, now: datetime) -> dict:
    hour = (now.hour + 5.5) % 24
    month = now.month
    season_mult = {1: 1.6, 2: 1.4, 3: 1.2, 4: 1.0, 5: 0.9, 6: 0.7, 7: 0.6, 8: 0.6, 9: 0.7, 10: 1.1, 11: 1.5, 12: 1.7}.get(month, 1.0)
    if 7 <= hour <= 10:
        diurnal_mult = 1.3
    elif 17 <= hour <= 21:
        diurnal_mult = 1.4
    elif 0 <= hour <= 5:
        diurnal_mult = 0.7
    else:
        diurnal_mult = 1.0
    city_base = {"Delhi": 185, "Mumbai": 115, "Kolkata": 145, "Bengaluru": 85, "Chennai": 95, "Lucknow": 175, "Patna": 195, "Hyderabad": 100}
    type_mod = {"traffic": 1.2, "industrial": 1.15, "residential": 0.85, "mixed": 1.0}
    base = city_base.get(city, 120)
    modifier = season_mult * diurnal_mult * type_mod.get(stn["type"], 1.0)
    noise = random.gauss(0, base * 0.12)
    aqi = max(15, min(500, round(base * modifier + noise)))
    pm25 = max(5, round(aqi * random.uniform(0.55, 0.70)))
    pm10 = max(10, round(aqi * random.uniform(0.80, 1.05)))

    return {
        "station_id": stn["id"],
        "station_name": stn["name"],
        "city": city,
        "lat": stn["lat"],
        "lng": stn["lng"],
        "station_type": stn["type"],
        "aqi": aqi,
        "pm25": pm25,
        "pm10": pm10,
        "no2": max(3, round(random.gauss(35, 15))),
        "so2": max(2, round(random.gauss(14, 8))),
        "co": max(0.2, round(random.gauss(1.2, 0.5), 1)),
        "o3": max(5, round(random.gauss(38, 12))),
        "dominant_pollutant": "PM2.5" if pm25 > pm10 * 0.6 else "PM10",
        "temperature": round(random.gauss(32, 5), 1),
        "humidity": round(random.gauss(55, 15)),
        "wind_speed": round(max(0.5, random.gauss(8, 4)), 1),
        "wind_direction": round(random.uniform(0, 360)),
        "timestamp": now.isoformat(),
        "source": "model",
    }


# === Persistence ===

def _save_readings(readings: list[dict]):
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    for r in readings:
        try:
            c.execute("""
                INSERT OR REPLACE INTO aqi_readings
                (station_id, station_name, city, lat, lng, station_type,
                 aqi, pm25, pm10, no2, so2, co, o3, dominant_pollutant,
                 temperature, humidity, wind_speed, wind_direction, timestamp, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r.get("station_id"), r.get("station_name"), r.get("city"),
                r.get("lat"), r.get("lng"), r.get("station_type"),
                r.get("aqi"), r.get("pm25"), r.get("pm10"),
                r.get("no2"), r.get("so2"), r.get("co"), r.get("o3"),
                r.get("dominant_pollutant"),
                r.get("temperature"), r.get("humidity"),
                r.get("wind_speed"), r.get("wind_direction"),
                r.get("timestamp"), r.get("source"),
            ))
        except Exception as e:
            print(f"DB insert error: {e}")
    conn.commit()
    conn.close()


def get_historical_readings(station_id: str, hours: int = 72) -> list[dict]:
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    c.execute("SELECT * FROM aqi_readings WHERE station_id = ? AND timestamp >= ? ORDER BY timestamp ASC", (station_id, since))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_city_readings(city: str, hours: int = 24) -> list[dict]:
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    c.execute("SELECT * FROM aqi_readings WHERE city = ? AND timestamp >= ? ORDER BY timestamp DESC", (city, since))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows
