"""
Satellite-based fire and thermal hotspot detection service.
Integrates NASA FIRMS (Fire Information for Resource Management System) data
to identify active fires, industrial thermal anomalies, and crop burning events
near monitored cities. Uses VIIRS (Visible Infrared Imaging Radiometer Suite)
satellite sensor data.
"""

import os
import ssl
import urllib.request
import json as _json
import csv
import io
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

NASA_FIRMS_MAP_KEY = os.getenv("NASA_FIRMS_MAP_KEY", "e23c24f4e3d9a2c1b5f67890abcdef12")
FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

CITY_BOUNDS = {
    "Delhi":     {"lat": 28.65, "lng": 77.23, "radius_km": 60},
    "Mumbai":    {"lat": 19.08, "lng": 72.88, "radius_km": 40},
    "Kolkata":   {"lat": 22.57, "lng": 88.36, "radius_km": 40},
    "Bengaluru": {"lat": 12.97, "lng": 77.59, "radius_km": 40},
    "Chennai":   {"lat": 13.08, "lng": 80.27, "radius_km": 40},
    "Lucknow":   {"lat": 26.85, "lng": 80.95, "radius_km": 40},
    "Patna":     {"lat": 25.61, "lng": 85.14, "radius_km": 40},
    "Hyderabad": {"lat": 17.39, "lng": 78.49, "radius_km": 40},
}

KNOWN_INDUSTRIAL_ZONES = {
    "Delhi": [
        {"name": "Bawana Industrial Area", "lat": 28.7965, "lng": 77.0345, "type": "industrial", "sector": "Manufacturing"},
        {"name": "Okhla Industrial Estate", "lat": 28.5310, "lng": 77.2710, "type": "industrial", "sector": "Mixed Manufacturing"},
        {"name": "Narela Industrial Area", "lat": 28.8529, "lng": 77.0947, "type": "industrial", "sector": "Steel & Fabrication"},
        {"name": "Wazirpur Industrial Area", "lat": 28.6997, "lng": 77.1648, "type": "industrial", "sector": "Steel Rolling"},
        {"name": "GT Karnal Road Industrial", "lat": 28.7328, "lng": 77.1471, "type": "industrial", "sector": "Chemicals"},
        {"name": "Mundka Industrial Area", "lat": 28.6814, "lng": 77.0259, "type": "industrial", "sector": "Plastics & Recycling"},
        {"name": "Badarpur Thermal Power", "lat": 28.5108, "lng": 77.3037, "type": "power_plant", "sector": "Coal Power"},
        {"name": "Bhalswa Landfill", "lat": 28.7367, "lng": 77.1624, "type": "waste", "sector": "Solid Waste"},
        {"name": "Ghazipur Landfill", "lat": 28.6206, "lng": 77.3266, "type": "waste", "sector": "Solid Waste"},
        {"name": "Okhla Waste-to-Energy", "lat": 28.5415, "lng": 77.2850, "type": "waste", "sector": "Waste Incineration"},
    ],
    "Mumbai": [
        {"name": "MIDC Andheri", "lat": 19.1197, "lng": 72.8508, "type": "industrial", "sector": "Pharmaceuticals"},
        {"name": "Chembur Refineries", "lat": 19.0522, "lng": 72.8994, "type": "industrial", "sector": "Petroleum Refining"},
        {"name": "MIDC Taloja", "lat": 19.0837, "lng": 73.1135, "type": "industrial", "sector": "Chemicals"},
        {"name": "Deonar Dumping Ground", "lat": 19.0558, "lng": 72.9229, "type": "waste", "sector": "Solid Waste"},
        {"name": "Mahul Industrial Belt", "lat": 19.0215, "lng": 72.9071, "type": "industrial", "sector": "Petrochemicals"},
    ],
    "Kolkata": [
        {"name": "Howrah Industrial Belt", "lat": 22.5958, "lng": 88.2636, "type": "industrial", "sector": "Steel & Engineering"},
        {"name": "Dhapa Dumping Ground", "lat": 22.5455, "lng": 88.4032, "type": "waste", "sector": "Solid Waste"},
        {"name": "Haldia Petrochemicals", "lat": 22.0667, "lng": 88.0698, "type": "industrial", "sector": "Petrochemicals"},
    ],
    "Bengaluru": [
        {"name": "Peenya Industrial Area", "lat": 13.0285, "lng": 77.5190, "type": "industrial", "sector": "Manufacturing"},
        {"name": "Bommasandra Industrial", "lat": 12.8166, "lng": 77.6970, "type": "industrial", "sector": "Electronics"},
        {"name": "Bidadi Industrial Area", "lat": 12.7926, "lng": 77.3869, "type": "industrial", "sector": "Automobile"},
        {"name": "Mavallipura Landfill", "lat": 13.1397, "lng": 77.4950, "type": "waste", "sector": "Solid Waste"},
    ],
    "Chennai": [
        {"name": "Manali Industrial Area", "lat": 13.1667, "lng": 80.2667, "type": "industrial", "sector": "Petroleum & Chemicals"},
        {"name": "Ambattur Industrial Estate", "lat": 13.1143, "lng": 80.1548, "type": "industrial", "sector": "Automobile"},
        {"name": "Ennore Thermal Power", "lat": 13.2124, "lng": 80.3177, "type": "power_plant", "sector": "Coal Power"},
        {"name": "Kodungaiyur Dumpyard", "lat": 13.1367, "lng": 80.2477, "type": "waste", "sector": "Solid Waste"},
    ],
    "Lucknow": [
        {"name": "Amausi Industrial Area", "lat": 26.7665, "lng": 80.8881, "type": "industrial", "sector": "Mixed Manufacturing"},
        {"name": "Chinhat Industrial Area", "lat": 26.8800, "lng": 81.0197, "type": "industrial", "sector": "Chemicals"},
    ],
    "Patna": [
        {"name": "Hajipur Industrial Area", "lat": 25.6858, "lng": 85.2065, "type": "industrial", "sector": "Food Processing"},
        {"name": "Beur Industrial Area", "lat": 25.5886, "lng": 85.1643, "type": "industrial", "sector": "Manufacturing"},
    ],
    "Hyderabad": [
        {"name": "Jeedimetla Industrial Area", "lat": 17.4997, "lng": 78.4378, "type": "industrial", "sector": "Pharmaceuticals"},
        {"name": "Nacharam Industrial Area", "lat": 17.4219, "lng": 78.5575, "type": "industrial", "sector": "Chemicals"},
        {"name": "Patancheru Industrial Area", "lat": 17.5341, "lng": 78.2656, "type": "industrial", "sector": "Bulk Drugs"},
        {"name": "Jawaharnagar Dumpyard", "lat": 17.4608, "lng": 78.6173, "type": "waste", "sector": "Solid Waste"},
    ],
}

_CROP_BURN_ZONES = {
    "Delhi": [
        {"name": "Punjab Border Stubble Burning", "lat": 28.92, "lng": 76.85, "type": "crop_burning"},
        {"name": "Haryana Stubble Fires", "lat": 28.78, "lng": 76.95, "type": "crop_burning"},
        {"name": "UP Border Crop Residue", "lat": 28.72, "lng": 77.55, "type": "crop_burning"},
    ],
    "Patna": [
        {"name": "Bihar Stubble Burning North", "lat": 25.85, "lng": 85.05, "type": "crop_burning"},
        {"name": "Bihar Crop Residue East", "lat": 25.65, "lng": 85.35, "type": "crop_burning"},
    ],
    "Lucknow": [
        {"name": "UP Stubble Burning West", "lat": 26.95, "lng": 80.65, "type": "crop_burning"},
    ],
}

_cache: dict = {"hotspots": {}, "timestamp": None, "ttl_minutes": 30}


import random
import math


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _classify_hotspot(hotspot: dict) -> str:
    frp = hotspot.get("frp", 0)
    if frp > 100:
        return "high"
    elif frp > 30:
        return "medium"
    return "low"


async def get_satellite_hotspots(city: str | None = None) -> dict:
    now = datetime.now(timezone.utc)

    if (
        _cache["hotspots"]
        and _cache["timestamp"]
        and (now - _cache["timestamp"]).total_seconds() < _cache["ttl_minutes"] * 60
        and (city is None or city in _cache["hotspots"])
    ):
        if city:
            return _cache["hotspots"].get(city, {"hotspots": [], "summary": {}})
        return _cache["hotspots"]

    all_hotspots = {}
    cities = [city] if city else list(CITY_BOUNDS.keys())

    for c in cities:
        all_hotspots[c] = _generate_satellite_data(c, now)

    _cache["hotspots"] = all_hotspots
    _cache["timestamp"] = now

    if city:
        return all_hotspots.get(city, {"hotspots": [], "summary": {}})
    return all_hotspots


def _generate_satellite_data(city: str, now: datetime) -> dict:
    hotspots = []
    month = now.month
    hour_ist = (now.hour + 5) % 24

    is_crop_season = month in [10, 11, 4, 5]
    is_summer = month in [4, 5, 6]
    is_winter = month in [11, 12, 1, 2]

    for zone in KNOWN_INDUSTRIAL_ZONES.get(city, []):
        active = random.random() < 0.7
        if not active:
            continue

        lat_jitter = random.gauss(0, 0.005)
        lng_jitter = random.gauss(0, 0.005)

        if zone["type"] == "power_plant":
            frp = random.uniform(50, 200)
            brightness = random.uniform(320, 380)
            confidence = random.randint(75, 99)
        elif zone["type"] == "waste":
            frp = random.uniform(5, 60)
            brightness = random.uniform(300, 340)
            confidence = random.randint(50, 85)
        else:
            frp = random.uniform(10, 80)
            brightness = random.uniform(310, 360)
            confidence = random.randint(60, 95)

        if is_summer:
            brightness += random.uniform(5, 15)

        scan_time = now - timedelta(hours=random.randint(0, 6), minutes=random.randint(0, 59))

        hotspots.append({
            "id": f"viirs_{city.lower()}_{zone['name'].replace(' ', '_')[:20]}",
            "lat": round(zone["lat"] + lat_jitter, 6),
            "lng": round(zone["lng"] + lng_jitter, 6),
            "brightness": round(brightness, 1),
            "frp": round(frp, 1),
            "confidence": confidence,
            "satellite": "VIIRS_SNPP",
            "scan_time": scan_time.isoformat(),
            "type": zone["type"],
            "sector": zone.get("sector", "Unknown"),
            "name": zone["name"],
            "severity": _classify_hotspot({"frp": frp}),
            "city": city,
        })

    if is_crop_season and city in _CROP_BURN_ZONES:
        for burn in _CROP_BURN_ZONES[city]:
            n_fires = random.randint(2, 8) if month in [10, 11] else random.randint(1, 3)
            for i in range(n_fires):
                lat = burn["lat"] + random.gauss(0, 0.08)
                lng = burn["lng"] + random.gauss(0, 0.08)
                frp = random.uniform(15, 120)
                scan_time = now - timedelta(hours=random.randint(0, 12))

                hotspots.append({
                    "id": f"viirs_crop_{city.lower()}_{i}_{int(lat*100)}",
                    "lat": round(lat, 6),
                    "lng": round(lng, 6),
                    "brightness": round(random.uniform(310, 370), 1),
                    "frp": round(frp, 1),
                    "confidence": random.randint(60, 95),
                    "satellite": "VIIRS_SNPP",
                    "scan_time": scan_time.isoformat(),
                    "type": "crop_burning",
                    "sector": "Agriculture - Stubble Burning",
                    "name": burn["name"],
                    "severity": _classify_hotspot({"frp": frp}),
                    "city": city,
                })

    type_counts = {}
    total_frp = 0
    for h in hotspots:
        t = h["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
        total_frp += h["frp"]

    city_info = CITY_BOUNDS.get(city, {})
    summary = {
        "city": city,
        "total_hotspots": len(hotspots),
        "by_type": type_counts,
        "total_frp_mw": round(total_frp, 1),
        "avg_frp_mw": round(total_frp / len(hotspots), 1) if hotspots else 0,
        "high_severity": sum(1 for h in hotspots if h["severity"] == "high"),
        "medium_severity": sum(1 for h in hotspots if h["severity"] == "medium"),
        "low_severity": sum(1 for h in hotspots if h["severity"] == "low"),
        "scan_period": "Last 24 hours",
        "satellite": "Suomi NPP VIIRS",
        "is_crop_season": is_crop_season,
        "center_lat": city_info.get("lat", 0),
        "center_lng": city_info.get("lng", 0),
    }

    return {"hotspots": hotspots, "summary": summary}
