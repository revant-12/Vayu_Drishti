"""
Health Impact Estimator.
Calculates estimated health burden from air pollution exposure
using WHO/IHME-aligned concentration-response functions.

Reference: GBD 2019, Lancet Planetary Health, IHME methodology.
"""

import math

CITY_POPULATIONS = {
    "Delhi": 32000000,
    "Mumbai": 21000000,
    "Kolkata": 15000000,
    "Bengaluru": 13000000,
    "Chennai": 11000000,
    "Lucknow": 3600000,
    "Patna": 2500000,
    "Hyderabad": 10000000,
}

# WHO guideline: annual mean PM2.5 should be ≤ 5 µg/m³
WHO_PM25_GUIDELINE = 5.0
# NAAQS India: annual mean PM2.5 ≤ 40 µg/m³
NAAQS_PM25 = 40.0

# Baseline mortality rate per 100k (India avg from GBD 2019)
BASELINE_MORTALITY_RATE = 784  # per 100k per year
# Fraction attributable to ambient air pollution (India ~10-12%)
BASELINE_AAP_FRACTION = 0.11

# Relative risk per 10 µg/m³ PM2.5 increase (meta-analysis)
RR_PER_10_PM25 = 1.062  # all-cause mortality
RR_RESPIRATORY = 1.098  # respiratory disease
RR_CARDIOVASCULAR = 1.072  # cardiovascular disease
RR_LUNG_CANCER = 1.09  # lung cancer

# Economic cost per statistical life (India, adjusted for PPP)
VSL_INDIA_INR = 18_700_000  # ~₹1.87 crore
# Respiratory hospital admission cost (avg)
HOSP_COST_INR = 35_000
# Lost productivity per sick day
PRODUCTIVITY_LOSS_INR = 1_200


def estimate_health_impact(city: str, avg_aqi: float, pm25: float, pm10: float,
                           population: int | None = None) -> dict:
    pop = population or CITY_POPULATIONS.get(city, 5_000_000)

    # Convert AQI to approximate PM2.5 if not provided
    if pm25 <= 0:
        pm25 = _aqi_to_pm25(avg_aqi)

    excess_pm25 = max(0, pm25 - WHO_PM25_GUIDELINE)

    # Relative Risk calculation (log-linear model)
    rr_mortality = RR_PER_10_PM25 ** (excess_pm25 / 10)
    rr_respiratory = RR_RESPIRATORY ** (excess_pm25 / 10)
    rr_cardiovascular = RR_CARDIOVASCULAR ** (excess_pm25 / 10)

    # Population Attributable Fraction (PAF)
    paf_mortality = (rr_mortality - 1) / rr_mortality
    paf_respiratory = (rr_respiratory - 1) / rr_respiratory
    paf_cardiovascular = (rr_cardiovascular - 1) / rr_cardiovascular

    # Estimated annual premature deaths
    baseline_deaths = pop * BASELINE_MORTALITY_RATE / 100_000
    premature_deaths = round(baseline_deaths * paf_mortality * BASELINE_AAP_FRACTION)

    # Respiratory hospitalizations (approx 3x deaths for respiratory)
    respiratory_cases = round(premature_deaths * 3.2)

    # Cardiovascular events
    cardio_events = round(baseline_deaths * paf_cardiovascular * 0.08)

    # Asthma exacerbations (children <14 ~25% of pop, ~8% asthma prevalence)
    child_pop = pop * 0.25
    asthma_pop = child_pop * 0.08
    asthma_attacks = round(asthma_pop * min(excess_pm25 / 100, 1.5) * 0.3)

    # Lost work days (WHO: ~1.2 days per person per year at India avg PM2.5)
    work_days_lost = round(pop * 0.65 * min(excess_pm25 / 50, 2.0) * 0.008)

    # Economic cost
    mortality_cost = premature_deaths * VSL_INDIA_INR
    hospital_cost = respiratory_cases * HOSP_COST_INR
    productivity_cost = work_days_lost * PRODUCTIVITY_LOSS_INR
    total_economic_cost = mortality_cost + hospital_cost + productivity_cost

    # Life years lost (avg 12 years per premature death from air pollution)
    life_years_lost = premature_deaths * 12

    # NAAQS exceedance
    naaqs_exceeded = pm25 > NAAQS_PM25
    who_exceeded = pm25 > WHO_PM25_GUIDELINE
    who_exceedance_factor = round(pm25 / WHO_PM25_GUIDELINE, 1) if WHO_PM25_GUIDELINE > 0 else 0

    return {
        "city": city,
        "population": pop,
        "current_pm25": round(pm25, 1),
        "current_aqi": round(avg_aqi),
        "who_guideline_pm25": WHO_PM25_GUIDELINE,
        "naaqs_pm25": NAAQS_PM25,
        "who_exceedance_factor": who_exceedance_factor,
        "naaqs_exceeded": naaqs_exceeded,
        "who_exceeded": who_exceeded,
        "health_metrics": {
            "premature_deaths_annual": premature_deaths,
            "respiratory_hospitalizations": respiratory_cases,
            "cardiovascular_events": cardio_events,
            "childhood_asthma_attacks": asthma_attacks,
            "life_years_lost": life_years_lost,
            "work_days_lost": work_days_lost,
        },
        "economic_impact": {
            "total_cost_inr": total_economic_cost,
            "total_cost_crore": round(total_economic_cost / 10_000_000),
            "mortality_cost_crore": round(mortality_cost / 10_000_000),
            "healthcare_cost_crore": round(hospital_cost / 10_000_000),
            "productivity_loss_crore": round(productivity_cost / 10_000_000),
        },
        "risk_factors": {
            "relative_risk_mortality": round(rr_mortality, 3),
            "relative_risk_respiratory": round(rr_respiratory, 3),
            "relative_risk_cardiovascular": round(rr_cardiovascular, 3),
            "paf_mortality": round(paf_mortality, 4),
        },
    }


def _aqi_to_pm25(aqi: float) -> float:
    """Approximate PM2.5 from CPCB AQI (simplified inverse breakpoint)."""
    if aqi <= 50:
        return aqi * 30 / 50
    elif aqi <= 100:
        return 30 + (aqi - 50) * 30 / 50
    elif aqi <= 200:
        return 60 + (aqi - 100) * 30 / 100
    elif aqi <= 300:
        return 90 + (aqi - 200) * 30 / 100
    elif aqi <= 400:
        return 120 + (aqi - 300) * 130 / 100
    else:
        return 250 + (aqi - 400) * 250 / 100
