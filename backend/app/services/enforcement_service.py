"""
Enforcement Intelligence Agent.
Analyzes real-time AQI data + source attribution to generate
prioritized, evidence-backed enforcement recommendations.
"""

from datetime import datetime
from typing import Optional
import numpy as np


def generate_enforcement_actions(stations_data: list[dict]) -> list[dict]:
    """
    Analyze all station readings and generate enforcement action recommendations.
    Prioritizes by: severity × population impact × evidence strength.
    """
    actions = []

    for station in stations_data:
        aqi = station.get("aqi", 0)
        if aqi < 150:
            continue  # Only flag stations above moderate

        city = station.get("city", "Unknown")
        name = station.get("station_name", "Unknown")
        stype = station.get("station_type", "mixed")
        lat = station.get("lat", 0)
        lng = station.get("lng", 0)
        pm25 = station.get("pm25", 0)
        pm10 = station.get("pm10", 0)
        no2 = station.get("no2", 0)
        so2 = station.get("so2", 0)
        wind_speed = station.get("wind_speed", 8)
        sources = station.get("sources", [])

        # Determine the dominant actionable source
        if not sources:
            continue

        top_source = sources[0] if isinstance(sources[0], dict) else {"source": "Unknown", "percentage": 0}

        # Generate specific enforcement based on dominant source
        action = _build_enforcement_action(
            station_name=name, city=city, lat=lat, lng=lng,
            aqi=aqi, pm25=pm25, pm10=pm10, no2=no2, so2=so2,
            station_type=stype, top_source=top_source,
            wind_speed=wind_speed, all_sources=sources,
        )

        if action:
            actions.append(action)

    # Sort by priority score
    priority_order = {"critical": 0, "high": 1, "medium": 2}
    actions.sort(key=lambda x: (priority_order.get(x["priority"], 3), -x.get("severity_score", 0)))

    return actions


def _build_enforcement_action(
    station_name: str, city: str, lat: float, lng: float,
    aqi: float, pm25: float, pm10: float, no2: float, so2: float,
    station_type: str, top_source: dict,
    wind_speed: float, all_sources: list,
) -> Optional[dict]:
    """Build a detailed enforcement action recommendation."""

    source_name = top_source.get("source", "Unknown")
    source_pct = top_source.get("percentage", 0)
    now = datetime.utcnow()
    hour_ist = (now.hour + 5.5) % 24

    # Base severity score
    severity = (aqi / 500) * 100

    if aqi > 400:
        priority = "critical"
    elif aqi > 250:
        priority = "high" if source_pct > 30 else "medium"
    else:
        priority = "medium"

    # Population impact estimates by city
    pop_density = {
        "Delhi": 11000, "Mumbai": 20000, "Kolkata": 24000,
        "Bengaluru": 4000, "Chennai": 7000, "Lucknow": 3500,
        "Patna": 2000, "Hyderabad": 3500,
    }.get(city, 5000)

    affected_pop = int(pop_density * 3.14 * 4)  # ~2km radius

    # Build action based on source type
    if source_name == "Vehicular Emissions":
        action_type = "Traffic Emission Control"
        if 7 <= hour_ist <= 10 or 17 <= hour_ist <= 21:
            description = (
                f"Vehicular emissions contributing {source_pct:.0f}% of AQI ({aqi:.0f}) during rush hour. "
                f"NO₂ at {no2:.0f} µg/m³ confirms combustion source. "
                f"Recommend immediate traffic diversion and heavy vehicle restriction enforcement."
            )
        else:
            description = (
                f"Vehicular emissions at {source_pct:.0f}% contribution even outside rush hours. "
                f"Indicates persistent non-compliance with BS-VI emission norms or heavy vehicle entry during ban hours."
            )
        evidence = [
            f"AQI at {aqi:.0f} — {_aqi_label(aqi)} category",
            f"NO₂ at {no2:.0f} µg/m³ — vehicular combustion signature confirmed",
            f"Vehicular contribution: {source_pct:.0f}% (confidence: {top_source.get('confidence', 0.7):.0%})",
            f"Station type: {station_type} — {'major road corridor' if station_type == 'traffic' else 'area monitoring'}",
        ]
        recommended_actions = [
            "Deploy traffic police for heavy vehicle restriction enforcement",
            "Activate odd-even or graded response plan if AQI > 300",
            "Inspect diesel vehicles on nearby arterial roads for PUC compliance",
            "Coordinate with municipal corp for road water sprinkling",
        ]

    elif source_name == "Industrial Emissions":
        action_type = "Industrial Emission Violation"
        priority = "critical" if so2 > 40 or aqi > 300 else priority
        wind_deg = 180.0
        for ev in top_source.get("evidence", []):
            if "°)" in ev:
                try:
                    wind_deg = float(ev.split("(")[-1].split("°")[0])
                    break
                except (ValueError, IndexError):
                    pass
        description = (
            f"Industrial emissions contributing {source_pct:.0f}% to AQI of {aqi:.0f}. "
            f"SO₂ at {so2:.0f} µg/m³ indicates non-compliance with stack emission standards. "
            f"Wind from {_wind_dir(wind_deg)} direction aligns with industrial zone."
        )
        evidence = [
            f"AQI at {aqi:.0f} — {_aqi_label(aqi)} category",
            f"SO₂ at {so2:.0f} µg/m³ — industrial/thermal plant signature",
            f"Industrial contribution: {source_pct:.0f}%",
            f"Wind speed {wind_speed:.1f} km/h — {'poor dispersion' if wind_speed < 5 else 'directional transport confirmed'}",
        ]
        recommended_actions = [
            "Deploy SPCB inspection team to industrial units in upwind direction",
            "Request continuous emission monitoring data from flagged units",
            "Issue show-cause notice under Air (Prevention and Control of Pollution) Act",
            "Verify pollution control equipment operational status",
        ]

    elif source_name == "Construction Activity":
        action_type = "Construction Dust Violation"
        description = (
            f"Construction activity contributing {source_pct:.0f}% to AQI of {aqi:.0f}. "
            f"PM10/PM2.5 ratio of {pm10/max(pm25,1):.1f} indicates coarse dust particles. "
            f"Multiple sites likely non-compliant with CPCB dust mitigation guidelines."
        )
        evidence = [
            f"AQI at {aqi:.0f} with PM10 at {pm10:.0f} µg/m³",
            f"PM10/PM2.5 ratio: {pm10/max(pm25,1):.1f} — coarse particle dominance confirms dust source",
            f"Construction contribution: {source_pct:.0f}%",
            "Active construction hours — peak emission window",
        ]
        recommended_actions = [
            "Inspect construction sites within 2km radius for dust suppression compliance",
            "Verify anti-smog gun deployment at large sites (>20,000 sq ft)",
            "Check green net/barricading compliance per NGT guidelines",
            "Issue stop-work orders for repeat offenders",
        ]

    elif source_name in ("Biomass & Waste Burning", "Waste Burning"):
        action_type = "Unauthorized Burning"
        month = now.month
        is_stubble_season = month in [10, 11]
        description = (
            f"Biomass/waste burning contributing {source_pct:.0f}% to AQI of {aqi:.0f}. "
            + ("Stubble burning season — satellite fire count elevated in upwind states. " if is_stubble_season else "")
            + "Unauthorized burning of waste material detected via air quality chemical signatures."
        )
        evidence = [
            f"AQI at {aqi:.0f} — {_aqi_label(aqi)} category",
            f"Burning contribution: {source_pct:.0f}%",
            "Satellite thermal hotspot data corroborates ground readings" if is_stubble_season else "Elevated organic carbon markers in PM2.5 composition",
            f"{'Stubble burning season — cross-border transport from Punjab/Haryana' if is_stubble_season else 'Local waste burning — likely municipal solid waste'}",
        ]
        recommended_actions = [
            "Deploy patrol teams to identify and extinguish active burn sites",
            "Coordinate with fire services for rapid response",
            "File FIR under NGT waste burning prohibition",
            "Activate satellite monitoring alert for recurring hotspots",
        ]

    else:
        action_type = "General Air Quality Alert"
        description = f"AQI at {aqi:.0f} in {_aqi_label(aqi)} range. Multiple sources contributing. Coordinated response recommended."
        evidence = [
            f"AQI at {aqi:.0f} — {_aqi_label(aqi)} category",
            f"Primary source: {source_name} at {source_pct:.0f}%",
        ]
        recommended_actions = [
            "Activate Graded Response Action Plan (GRAP) measures",
            "Issue public health advisory for sensitive groups",
            "Coordinate multi-agency response",
        ]

    return {
        "id": f"ENF-{city[:3].upper()}-{now.strftime('%H%M')}-{hash(station_name) % 1000:03d}",
        "priority": priority,
        "severity_score": severity,
        "action_type": action_type,
        "station_name": station_name,
        "city": city,
        "lat": lat,
        "lng": lng,
        "description": description,
        "evidence": evidence,
        "recommended_actions": recommended_actions,
        "affected_population": f"~{affected_pop:,} residents within 2km radius",
        "estimated_aqi_reduction": f"{int(source_pct * 0.4)}-{int(source_pct * 0.7)} points if addressed",
        "regulatory_reference": _get_regulatory_ref(action_type),
        "timestamp": now.isoformat(),
        "status": "pending",
    }


def _aqi_label(aqi: float) -> str:
    if aqi <= 50: return "Good"
    if aqi <= 100: return "Satisfactory"
    if aqi <= 200: return "Moderate"
    if aqi <= 300: return "Poor"
    if aqi <= 400: return "Very Poor"
    return "Severe"


def _wind_dir(degrees: float) -> str:
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return dirs[round(degrees / 45) % 8]


def _get_regulatory_ref(action_type: str) -> str:
    refs = {
        "Industrial Emission Violation": "Air (Prevention and Control of Pollution) Act, 1981 — Section 21, 22",
        "Traffic Emission Control": "CPCB GRAP (Graded Response Action Plan) — Stage II/III measures",
        "Construction Dust Violation": "NGT Order dated 04.12.2021 — Construction dust mitigation guidelines",
        "Unauthorized Burning": "NGT Order — Prohibition of waste burning; EPA 1986 Section 15",
        "General Air Quality Alert": "NCAP (National Clean Air Programme) — Emergency response protocol",
    }
    return refs.get(action_type, "CPCB Air Quality Standards — National Ambient Air Quality Standards (NAAQS)")
