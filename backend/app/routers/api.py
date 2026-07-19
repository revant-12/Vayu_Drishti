"""
VayuDrishti API Routes.
All endpoints that the frontend consumes.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path

from app.services.cpcb_service import (
    fetch_live_cpcb_data,
    get_historical_readings,
    get_city_readings,
    MONITORED_STATIONS,
)
from app.services.prediction_service import predict_aqi, train_model
from app.services.attribution_service import attribute_sources
from app.services.enforcement_service import generate_enforcement_actions
from app.services.satellite_service import get_satellite_hotspots
from app.services.dispersion_service import calculate_dispersion
from app.services.agent_orchestrator import get_intelligence_report, get_city_intelligence
from app.services.chat_service import process_chat_message
from app.services.report_service import generate_enforcement_pdf
from app.services.health_impact_service import estimate_health_impact
from app.services.alert_service import generate_alerts

router = APIRouter()

# City base AQI for prediction model (from CPCB annual averages)
CITY_BASE_AQI = {
    "Delhi": 185, "Mumbai": 115, "Kolkata": 145,
    "Bengaluru": 85, "Chennai": 95, "Lucknow": 175,
    "Patna": 195, "Hyderabad": 100,
}


@router.get("/stations")
async def get_all_stations(city: Optional[str] = None):
    """Get current AQI data for all monitored stations."""
    stations = await fetch_live_cpcb_data()

    if city:
        stations = [s for s in stations if s.get("city", "").lower() == city.lower()]

    # Add source attribution to each station
    enriched = []
    for s in stations:
        sources = attribute_sources(
            station_name=s.get("station_name", ""),
            city=s.get("city", ""),
            station_type=s.get("station_type", "mixed"),
            aqi=s.get("aqi", 0),
            pm25=s.get("pm25", 0),
            pm10=s.get("pm10", 0),
            no2=s.get("no2", 0),
            so2=s.get("so2", 0),
            co=s.get("co", 0),
            wind_speed=s.get("wind_speed", 8),
            wind_direction=s.get("wind_direction", 180),
            temperature=s.get("temperature", 32),
            humidity=s.get("humidity", 55),
        )
        s["sources"] = sources

        # Add AQI category
        aqi = s.get("aqi", 0)
        s["category"] = _aqi_category(aqi)
        s["category_label"] = _aqi_label(aqi)

        # Determine trend from historical data
        s["trend"] = _determine_trend(s.get("station_id", ""), aqi)

        enriched.append(s)

    return {
        "stations": enriched,
        "count": len(enriched),
        "timestamp": enriched[0].get("timestamp") if enriched else None,
        "source": enriched[0].get("source", "model") if enriched else "model",
    }


@router.get("/stations/{station_id}")
async def get_station_detail(station_id: str):
    """Get detailed info for a specific station including history."""
    stations = await fetch_live_cpcb_data()
    station = next((s for s in stations if s.get("station_id") == station_id), None)

    if not station:
        raise HTTPException(status_code=404, detail=f"Station {station_id} not found")

    # Add attribution
    station["sources"] = attribute_sources(
        station_name=station.get("station_name", ""),
        city=station.get("city", ""),
        station_type=station.get("station_type", "mixed"),
        aqi=station.get("aqi", 0),
        pm25=station.get("pm25", 0),
        pm10=station.get("pm10", 0),
        no2=station.get("no2", 0),
        so2=station.get("so2", 0),
        co=station.get("co", 0),
        wind_speed=station.get("wind_speed", 8),
        wind_direction=station.get("wind_direction", 180),
    )

    # Add historical data
    station["history"] = get_historical_readings(station_id, hours=48)

    station["category"] = _aqi_category(station.get("aqi", 0))
    station["trend"] = _determine_trend(station_id, station.get("aqi", 0))

    return station


@router.get("/predictions/{station_id}")
async def get_predictions(
    station_id: str,
    hours: int = Query(default=72, ge=1, le=168),
):
    """Get ML-powered AQI predictions for a station."""
    stations = await fetch_live_cpcb_data()
    station = next((s for s in stations if s.get("station_id") == station_id), None)

    if not station:
        raise HTTPException(status_code=404, detail=f"Station {station_id} not found")

    city = station.get("city", "Unknown")
    base_aqi = CITY_BASE_AQI.get(city, 150)

    predictions = predict_aqi(
        current_aqi=station.get("aqi", 150),
        current_pm25=station.get("pm25", 80),
        current_pm10=station.get("pm10", 120),
        station_type=station.get("station_type", "mixed"),
        city_base_aqi=base_aqi,
        hours_ahead=hours,
        temperature=station.get("temperature", 32),
        humidity=station.get("humidity", 55),
        wind_speed=station.get("wind_speed", 8),
        wind_direction=station.get("wind_direction", 180),
    )

    # Find peak and trough
    peak = max(predictions, key=lambda p: p["predicted_aqi"])
    trough = min(predictions, key=lambda p: p["predicted_aqi"])

    return {
        "station_id": station_id,
        "station_name": station.get("station_name"),
        "city": city,
        "current_aqi": station.get("aqi"),
        "predictions": predictions,
        "summary": {
            "peak_aqi": peak["predicted_aqi"],
            "peak_time": peak["time_label"],
            "lowest_aqi": trough["predicted_aqi"],
            "lowest_time": trough["time_label"],
            "avg_predicted": round(sum(p["predicted_aqi"] for p in predictions) / len(predictions)),
            "hours_above_200": sum(1 for p in predictions if p["predicted_aqi"] > 200),
            "hours_above_300": sum(1 for p in predictions if p["predicted_aqi"] > 300),
        },
    }


@router.get("/enforcement")
async def get_enforcement_actions(city: Optional[str] = None):
    """Get AI-generated enforcement action recommendations."""
    stations = await fetch_live_cpcb_data()

    # Add source attribution
    for s in stations:
        s["sources"] = attribute_sources(
            station_name=s.get("station_name", ""),
            city=s.get("city", ""),
            station_type=s.get("station_type", "mixed"),
            aqi=s.get("aqi", 0),
            pm25=s.get("pm25", 0),
            pm10=s.get("pm10", 0),
            no2=s.get("no2", 0),
            so2=s.get("so2", 0),
            co=s.get("co", 0),
            wind_speed=s.get("wind_speed", 8),
            wind_direction=s.get("wind_direction", 180),
        )

    if city:
        stations = [s for s in stations if s.get("city", "").lower() == city.lower()]

    actions = generate_enforcement_actions(stations)

    return {
        "actions": actions,
        "count": len(actions),
        "critical_count": sum(1 for a in actions if a["priority"] == "critical"),
        "high_count": sum(1 for a in actions if a["priority"] == "high"),
    }


@router.get("/cities")
async def get_city_overview():
    """Get aggregated AQI overview for all monitored cities."""
    stations = await fetch_live_cpcb_data()

    cities = {}
    for s in stations:
        city = s.get("city", "Unknown")
        if city not in cities:
            cities[city] = {
                "city": city,
                "stations": [],
                "total_aqi": 0,
                "count": 0,
            }
        cities[city]["stations"].append(s)
        cities[city]["total_aqi"] += s.get("aqi", 0)
        cities[city]["count"] += 1

    populations = {
        "Delhi": "32M", "Mumbai": "21M", "Kolkata": "15M",
        "Bengaluru": "13M", "Chennai": "11M", "Lucknow": "3.6M",
        "Patna": "2.5M", "Hyderabad": "10M",
    }

    overview = []
    for city, data in cities.items():
        avg_aqi = round(data["total_aqi"] / data["count"])
        overview.append({
            "city": city,
            "avg_aqi": avg_aqi,
            "category": _aqi_category(avg_aqi),
            "category_label": _aqi_label(avg_aqi),
            "station_count": data["count"],
            "critical_stations": sum(1 for s in data["stations"] if s.get("aqi", 0) > 200),
            "population": populations.get(city, "N/A"),
            "worst_station": max(data["stations"], key=lambda s: s.get("aqi", 0)).get("station_name"),
            "worst_aqi": max(s.get("aqi", 0) for s in data["stations"]),
        })

    overview.sort(key=lambda x: x["avg_aqi"], reverse=True)
    return {"cities": overview}


@router.get("/model/info")
async def get_model_info():
    """Get ML model performance metrics."""
    metrics_path = Path(__file__).parent.parent.parent / "ml" / "model_metrics.json"
    if metrics_path.exists():
        return json.loads(metrics_path.read_text())
    return {"status": "model_not_trained"}


@router.post("/model/retrain")
async def retrain_model():
    """Force retrain the ML model."""
    metrics = train_model(force=True)
    return {"status": "retrained", "metrics": metrics}


def _aqi_category(aqi: float) -> str:
    if aqi <= 50: return "good"
    if aqi <= 100: return "satisfactory"
    if aqi <= 200: return "moderate"
    if aqi <= 300: return "poor"
    if aqi <= 400: return "very_poor"
    return "severe"


def _aqi_label(aqi: float) -> str:
    labels = {
        "good": "Good", "satisfactory": "Satisfactory", "moderate": "Moderate",
        "poor": "Poor", "very_poor": "Very Poor", "severe": "Severe",
    }
    return labels.get(_aqi_category(aqi), "Unknown")


def _determine_trend(station_id: str, current_aqi: float) -> str:
    """Determine if AQI is trending up, down, or stable."""
    history = get_historical_readings(station_id, hours=6)
    if len(history) < 2:
        return "stable"

    recent_avg = sum(r.get("aqi", 0) for r in history[-3:]) / min(3, len(history))
    if current_aqi > recent_avg * 1.1:
        return "worsening"
    elif current_aqi < recent_avg * 0.9:
        return "improving"
    return "stable"


# === Satellite Hotspots ===

@router.get("/satellite/hotspots")
async def get_hotspots(city: Optional[str] = None):
    """Get NASA FIRMS satellite fire/thermal hotspot data."""
    data = await get_satellite_hotspots(city)
    return data


# === Atmospheric Dispersion ===

@router.get("/dispersion/{city}")
async def get_dispersion(
    city: str,
    wind_speed: float = Query(default=5.0, ge=0.1, le=30),
    wind_direction: float = Query(default=270, ge=0, le=360),
):
    """Get Gaussian plume dispersion model results for a city."""
    result = await calculate_dispersion(city, wind_speed, wind_direction)
    return result


# === Multi-Agent Intelligence ===

@router.get("/agents/report")
async def get_full_report():
    """Get full multi-agent intelligence report for all cities."""
    stations = await fetch_live_cpcb_data()
    satellite = await get_satellite_hotspots()
    report = await get_intelligence_report(stations, satellite)
    return report


@router.get("/agents/report/{city}")
async def get_city_report(city: str):
    """Get focused multi-agent intelligence report for a single city."""
    stations = await fetch_live_cpcb_data()
    satellite = await get_satellite_hotspots(city)
    report = await get_city_intelligence(city, stations, {city: satellite})
    return report


# === Citizen Advisory Chat ===

class ChatRequest(BaseModel):
    message: str
    language: str = "en"
    city: Optional[str] = None


@router.post("/chat")
async def chat(req: ChatRequest):
    """Process citizen health advisory chat message."""
    stations = await fetch_live_cpcb_data()

    city_data = {}
    for s in stations:
        c = s.get("city", "")
        if c not in city_data:
            city_data[c] = {"avg_aqi": 0, "count": 0, "pm25_sum": 0, "pm10_sum": 0}
        city_data[c]["count"] += 1
        city_data[c]["avg_aqi"] += s.get("aqi", 0)
        city_data[c]["pm25_sum"] += s.get("pm25", 0)
        city_data[c]["pm10_sum"] += s.get("pm10", 0)

    for c, d in city_data.items():
        n = d["count"]
        d["avg_aqi"] = round(d["avg_aqi"] / n) if n else 0
        d["pm25_avg"] = round(d["pm25_sum"] / n, 1) if n else 0
        d["pm10_avg"] = round(d["pm10_sum"] / n, 1) if n else 0
        d["station_count"] = n

    ctx = {"city": req.city} if req.city else {}
    result = await process_chat_message(req.message, req.language, city_data, ctx)
    return result


# === Comparative Dashboard ===

@router.get("/comparative")
async def get_comparative():
    """Get multi-city comparative analytics data."""
    stations = await fetch_live_cpcb_data()

    cities = {}
    for s in stations:
        c = s.get("city", "Unknown")
        if c not in cities:
            cities[c] = {"aqis": [], "pm25": [], "pm10": [], "no2": [], "so2": [], "o3": []}
        cities[c]["aqis"].append(s.get("aqi", 0))
        if s.get("pm25", 0) > 0: cities[c]["pm25"].append(s["pm25"])
        if s.get("pm10", 0) > 0: cities[c]["pm10"].append(s["pm10"])
        if s.get("no2", 0) > 0: cities[c]["no2"].append(s["no2"])
        if s.get("so2", 0) > 0: cities[c]["so2"].append(s["so2"])
        if s.get("o3", 0) > 0: cities[c]["o3"].append(s["o3"])

    populations = {
        "Delhi": 32000000, "Mumbai": 21000000, "Kolkata": 15000000,
        "Bengaluru": 13000000, "Chennai": 11000000, "Lucknow": 3600000,
        "Patna": 2500000, "Hyderabad": 10000000,
    }

    comparative = []
    for city, data in cities.items():
        n = len(data["aqis"])
        avg_aqi = round(sum(data["aqis"]) / n) if n else 0
        pop = populations.get(city, 5000000)

        comparative.append({
            "city": city,
            "avg_aqi": avg_aqi,
            "max_aqi": max(data["aqis"]) if data["aqis"] else 0,
            "min_aqi": min(data["aqis"]) if data["aqis"] else 0,
            "station_count": n,
            "population": pop,
            "category": _aqi_category(avg_aqi),
            "pollutants": {
                "pm25": round(sum(data["pm25"]) / len(data["pm25"]), 1) if data["pm25"] else 0,
                "pm10": round(sum(data["pm10"]) / len(data["pm10"]), 1) if data["pm10"] else 0,
                "no2": round(sum(data["no2"]) / len(data["no2"]), 1) if data["no2"] else 0,
                "so2": round(sum(data["so2"]) / len(data["so2"]), 1) if data["so2"] else 0,
                "o3": round(sum(data["o3"]) / len(data["o3"]), 1) if data["o3"] else 0,
            },
            "aqi_per_million": round(avg_aqi * 1000000 / pop, 2) if pop else 0,
            "critical_stations": sum(1 for a in data["aqis"] if a > 200),
            "compliance_rate": round(sum(1 for a in data["aqis"] if a <= 100) / n * 100) if n else 0,
        })

    comparative.sort(key=lambda x: x["avg_aqi"], reverse=True)
    return {"cities": comparative}


# === Health Impact Estimator ===

@router.get("/health-impact")
async def get_health_impact(city: Optional[str] = None):
    """Get estimated health burden from current air pollution levels."""
    stations = await fetch_live_cpcb_data()

    cities = {}
    for s in stations:
        c = s.get("city", "Unknown")
        if c not in cities:
            cities[c] = {"aqis": [], "pm25": [], "pm10": []}
        cities[c]["aqis"].append(s.get("aqi", 0))
        cities[c]["pm25"].append(s.get("pm25", 0))
        cities[c]["pm10"].append(s.get("pm10", 0))

    if city:
        cities = {k: v for k, v in cities.items() if k.lower() == city.lower()}

    results = []
    for c, data in cities.items():
        n = len(data["aqis"])
        avg_aqi = sum(data["aqis"]) / n if n else 0
        avg_pm25 = sum(data["pm25"]) / n if n else 0
        avg_pm10 = sum(data["pm10"]) / n if n else 0

        impact = estimate_health_impact(c, avg_aqi, avg_pm25, avg_pm10)
        results.append(impact)

    results.sort(key=lambda x: x["health_metrics"]["premature_deaths_annual"], reverse=True)

    total_deaths = sum(r["health_metrics"]["premature_deaths_annual"] for r in results)
    total_cost = sum(r["economic_impact"]["total_cost_crore"] for r in results)

    return {
        "cities": results,
        "summary": {
            "total_premature_deaths": total_deaths,
            "total_economic_cost_crore": total_cost,
            "cities_analyzed": len(results),
        },
    }


# === Real-Time Alerts ===

@router.get("/alerts")
async def get_alerts():
    """Get real-time AQI alerts and threshold crossings."""
    stations = await fetch_live_cpcb_data()
    alerts = generate_alerts(stations)
    return {
        "alerts": alerts,
        "count": len(alerts),
        "emergency_count": sum(1 for a in alerts if a["level"] == "emergency"),
        "critical_count": sum(1 for a in alerts if a["level"] == "critical"),
    }


# === PDF Report Generation ===

@router.get("/report/pdf")
async def download_enforcement_pdf(city: Optional[str] = None):
    """Generate and download a PDF enforcement report."""
    stations = await fetch_live_cpcb_data()

    for s in stations:
        s["sources"] = attribute_sources(
            station_name=s.get("station_name", ""),
            city=s.get("city", ""),
            station_type=s.get("station_type", "mixed"),
            aqi=s.get("aqi", 0),
            pm25=s.get("pm25", 0),
            pm10=s.get("pm10", 0),
            no2=s.get("no2", 0),
            so2=s.get("so2", 0),
            co=s.get("co", 0),
            wind_speed=s.get("wind_speed", 8),
            wind_direction=s.get("wind_direction", 180),
        )

    target_stations = stations
    if city:
        target_stations = [s for s in stations if s.get("city", "").lower() == city.lower()]

    actions = generate_enforcement_actions(target_stations)

    cities_overview = await get_city_overview()
    cities_data = cities_overview.get("cities", [])

    pdf_bytes = generate_enforcement_pdf(
        city=city,
        stations_data=stations,
        enforcement_actions=actions,
        cities_data=cities_data,
    )

    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"VayuDrishti_Enforcement_{city or 'All'}_{ts}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
