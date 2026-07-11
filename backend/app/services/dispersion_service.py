"""
Atmospheric Dispersion Modeling Service.
Implements a simplified Gaussian Plume Model for ground-level pollutant
concentration estimation. Uses Pasquill-Gifford stability classes and
standard dispersion coefficients for urban environments.

Reference: Turner, D.B. (1970). Workbook of Atmospheric Dispersion Estimates.
EPA AP-26, US Environmental Protection Agency.
"""

import math
import random
from datetime import datetime, timezone, timedelta


PASQUILL_CLASSES = {
    "A": {"name": "Very Unstable", "conditions": "Strong insolation, light winds"},
    "B": {"name": "Moderately Unstable", "conditions": "Moderate insolation, light winds"},
    "C": {"name": "Slightly Unstable", "conditions": "Weak insolation, moderate winds"},
    "D": {"name": "Neutral", "conditions": "Overcast or windy conditions"},
    "E": {"name": "Slightly Stable", "conditions": "Night, light winds, partial cloud"},
    "F": {"name": "Stable", "conditions": "Night, light winds, clear sky"},
}

PG_COEFFICIENTS = {
    "A": {"ay": 0.3658, "by": 0.2500, "az": 0.192, "bz": 1.0857},
    "B": {"ay": 0.2751, "by": 0.2500, "az": 0.156, "bz": 0.8650},
    "C": {"ay": 0.2090, "by": 0.2500, "az": 0.116, "bz": 0.6890},
    "D": {"ay": 0.1471, "by": 0.2500, "az": 0.079, "bz": 0.5650},
    "E": {"ay": 0.1046, "by": 0.2500, "az": 0.063, "bz": 0.4510},
    "F": {"ay": 0.0722, "by": 0.2500, "az": 0.053, "bz": 0.3830},
}


def _sigma_y(x_m: float, stability: str) -> float:
    coeff = PG_COEFFICIENTS.get(stability, PG_COEFFICIENTS["D"])
    return coeff["ay"] * x_m ** (1.0 - coeff["by"])


def _sigma_z(x_m: float, stability: str) -> float:
    coeff = PG_COEFFICIENTS.get(stability, PG_COEFFICIENTS["D"])
    return coeff["az"] * x_m ** coeff["bz"]


def gaussian_plume_concentration(
    x: float, y: float, z: float,
    Q: float, u: float, H: float,
    stability: str = "D"
) -> float:
    """
    Calculate ground-level concentration using Gaussian plume equation.

    Args:
        x: downwind distance (meters)
        y: crosswind distance (meters)
        z: receptor height (meters, usually 0 for ground level)
        Q: emission rate (µg/s)
        u: wind speed (m/s)
        H: effective stack height (meters)
        stability: Pasquill stability class (A-F)

    Returns:
        Concentration in µg/m³
    """
    if x <= 0 or u <= 0:
        return 0.0

    sy = _sigma_y(x, stability)
    sz = _sigma_z(x, stability)

    if sy <= 0 or sz <= 0:
        return 0.0

    lateral = math.exp(-0.5 * (y / sy) ** 2)

    vertical = (
        math.exp(-0.5 * ((z - H) / sz) ** 2) +
        math.exp(-0.5 * ((z + H) / sz) ** 2)
    )

    C = (Q / (2 * math.pi * u * sy * sz)) * lateral * vertical

    return max(0.0, C)


def _determine_stability_class(wind_speed: float, hour_ist: float, cloud_cover: float = 0.5) -> str:
    is_day = 6 <= hour_ist <= 18

    if is_day:
        if wind_speed < 2:
            return "A" if cloud_cover < 0.3 else "B"
        elif wind_speed < 3:
            return "B" if cloud_cover < 0.5 else "C"
        elif wind_speed < 5:
            return "C" if cloud_cover < 0.5 else "D"
        else:
            return "D"
    else:
        if wind_speed < 2:
            return "F" if cloud_cover < 0.4 else "E"
        elif wind_speed < 3:
            return "E"
        else:
            return "D"


EMISSION_SOURCES = {
    "Delhi": [
        {"name": "Badarpur Thermal Power Station", "lat": 28.5108, "lng": 77.3037,
         "Q": 5000000, "H": 120, "type": "power_plant", "pollutant": "PM2.5"},
        {"name": "Bawana Industrial Complex", "lat": 28.7965, "lng": 77.0345,
         "Q": 800000, "H": 30, "type": "industrial", "pollutant": "PM10"},
        {"name": "Okhla Waste-to-Energy", "lat": 28.5415, "lng": 77.2850,
         "Q": 600000, "H": 45, "type": "waste", "pollutant": "PM2.5"},
        {"name": "Wazirpur Steel Rolling", "lat": 28.6997, "lng": 77.1648,
         "Q": 1200000, "H": 25, "type": "industrial", "pollutant": "SO2"},
        {"name": "Anand Vihar Bus Terminal", "lat": 28.6469, "lng": 77.3164,
         "Q": 400000, "H": 5, "type": "traffic", "pollutant": "NO2"},
    ],
    "Mumbai": [
        {"name": "Chembur BPCL Refinery", "lat": 19.0522, "lng": 72.8994,
         "Q": 3000000, "H": 80, "type": "industrial", "pollutant": "SO2"},
        {"name": "Deonar Waste Dump", "lat": 19.0558, "lng": 72.9229,
         "Q": 900000, "H": 10, "type": "waste", "pollutant": "PM2.5"},
        {"name": "Mahul Petrochemical Belt", "lat": 19.0215, "lng": 72.9071,
         "Q": 2000000, "H": 60, "type": "industrial", "pollutant": "NO2"},
    ],
    "Kolkata": [
        {"name": "Howrah Industrial Belt", "lat": 22.5958, "lng": 88.2636,
         "Q": 1500000, "H": 35, "type": "industrial", "pollutant": "PM10"},
        {"name": "Dhapa Solid Waste", "lat": 22.5455, "lng": 88.4032,
         "Q": 700000, "H": 8, "type": "waste", "pollutant": "PM2.5"},
    ],
    "Bengaluru": [
        {"name": "Peenya Industrial Area", "lat": 13.0285, "lng": 77.5190,
         "Q": 600000, "H": 25, "type": "industrial", "pollutant": "PM10"},
    ],
    "Chennai": [
        {"name": "Ennore Thermal Power", "lat": 13.2124, "lng": 80.3177,
         "Q": 4000000, "H": 100, "type": "power_plant", "pollutant": "SO2"},
        {"name": "Manali Refinery Complex", "lat": 13.1667, "lng": 80.2667,
         "Q": 2500000, "H": 70, "type": "industrial", "pollutant": "NO2"},
    ],
    "Lucknow": [
        {"name": "Amausi Industrial", "lat": 26.7665, "lng": 80.8881,
         "Q": 500000, "H": 20, "type": "industrial", "pollutant": "PM10"},
    ],
    "Patna": [
        {"name": "Hajipur Industrial", "lat": 25.6858, "lng": 85.2065,
         "Q": 400000, "H": 20, "type": "industrial", "pollutant": "PM10"},
    ],
    "Hyderabad": [
        {"name": "Jeedimetla Pharma Zone", "lat": 17.4997, "lng": 78.4378,
         "Q": 800000, "H": 30, "type": "industrial", "pollutant": "SO2"},
        {"name": "Patancheru CETP", "lat": 17.5341, "lng": 78.2656,
         "Q": 1000000, "H": 35, "type": "industrial", "pollutant": "NO2"},
    ],
}


def _rotate_point(x: float, y: float, angle_rad: float) -> tuple[float, float]:
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    return x * cos_a - y * sin_a, x * sin_a + y * cos_a


async def calculate_dispersion(
    city: str,
    wind_speed: float = 5.0,
    wind_direction: float = 270.0,
    grid_resolution_m: float = 500,
    grid_extent_km: float = 15
) -> dict:
    """
    Calculate pollutant dispersion plumes for all emission sources in a city.
    Returns a concentration grid for map overlay.
    """
    now = datetime.now(timezone.utc)
    hour_ist = (now.hour + 5.5) % 24
    month = now.month

    stability = _determine_stability_class(wind_speed, hour_ist)

    seasonal_factor = {1: 1.5, 2: 1.3, 3: 1.1, 4: 0.9, 5: 0.8, 6: 0.6,
                       7: 0.5, 8: 0.5, 9: 0.7, 10: 1.2, 11: 1.6, 12: 1.7}.get(month, 1.0)

    sources = EMISSION_SOURCES.get(city, [])
    if not sources:
        return {"city": city, "plumes": [], "grid": [], "metadata": {}}

    wind_rad = math.radians((270 - wind_direction) % 360)

    plumes = []
    for source in sources:
        Q = source["Q"] * seasonal_factor * (1 + random.gauss(0, 0.1))
        H = source["H"]

        concentrations = []
        max_conc = 0
        max_dist = 0

        distances = [100, 250, 500, 1000, 2000, 3000, 5000, 7500, 10000, 15000]
        for x_m in distances:
            c_center = gaussian_plume_concentration(x_m, 0, 0, Q, max(0.5, wind_speed), H, stability)

            dx = x_m * math.cos(wind_rad)
            dy = x_m * math.sin(wind_rad)

            lat_offset = dy / 111320
            lng_offset = dx / (111320 * math.cos(math.radians(source["lat"])))

            sy = _sigma_y(x_m, stability)

            concentrations.append({
                "distance_m": x_m,
                "lat": round(source["lat"] + lat_offset, 6),
                "lng": round(source["lng"] + lng_offset, 6),
                "concentration_ugm3": round(c_center, 2),
                "sigma_y_m": round(sy, 1),
                "sigma_z_m": round(_sigma_z(x_m, stability), 1),
                "plume_width_m": round(4 * sy, 0),
            })

            if c_center > max_conc:
                max_conc = c_center
                max_dist = x_m

        plumes.append({
            "source": source["name"],
            "source_lat": source["lat"],
            "source_lng": source["lng"],
            "source_type": source["type"],
            "pollutant": source["pollutant"],
            "emission_rate_ug_s": round(Q, 0),
            "stack_height_m": H,
            "max_ground_concentration_ugm3": round(max_conc, 2),
            "max_concentration_distance_m": max_dist,
            "concentrations": concentrations,
            "wind_direction_to": wind_direction,
        })

    metadata = {
        "city": city,
        "timestamp": now.isoformat(),
        "wind_speed_ms": wind_speed,
        "wind_direction_deg": wind_direction,
        "stability_class": stability,
        "stability_name": PASQUILL_CLASSES[stability]["name"],
        "stability_conditions": PASQUILL_CLASSES[stability]["conditions"],
        "seasonal_factor": seasonal_factor,
        "model": "Gaussian Plume (Pasquill-Gifford)",
        "reference": "Turner (1970) EPA AP-26",
        "grid_resolution_m": grid_resolution_m,
        "num_sources": len(sources),
    }

    return {"city": city, "plumes": plumes, "metadata": metadata}
