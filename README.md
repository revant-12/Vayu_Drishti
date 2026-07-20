# VayuDrishti - AI-Powered Urban Air Quality Intelligence Platform

> From reactive monitoring to proactive, evidence-based intervention.

**VayuDrishti** (meaning "Air Vision" in Sanskrit) is a full-stack AI-powered air quality intelligence platform that transforms India's scattered pollution data into actionable intelligence for smart city administrators. Built for **ET AI Hackathon 2026 — Problem Statement 5**.

## Key Numbers

| Metric | Value |
|--------|-------|
| Live CPCB Stations | 114 |
| Cities Monitored | 8 |
| ML Accuracy | 96.84% |
| R² Score | 0.995 |
| Training Samples | 98,112 |
| AI Agents | 5 |
| Forecast Horizon | 72 hours |
| Languages Supported | 5 |
| Backend Services | 10 |

## Six Intelligence Layers

1. **Real-Time Data Fusion** — Live data from 114 CPCB CAAQMS stations across 8 major Indian cities via data.gov.in API. 3-tier fallback (CPCB → WAQI → Model-generated) ensures 100% uptime with 10-minute refresh.

2. **ML Forecasting Engine** — XGBoost ensemble model trained on 98,112 real CPCB samples. Generates 72-hour AQI predictions with 96.84% accuracy. Top features: PM2.5 (59.4%), PM10 (25.6%), seasonal patterns (7.3%).

3. **Source Attribution** — Algorithmic source apportionment identifying pollution contributors: vehicular traffic, industrial emissions, construction dust, biomass burning, and secondary aerosols.

4. **Satellite Intelligence** — NASA FIRMS thermal hotspot integration for fire and industrial emission detection, overlaid on the live map.

5. **Atmospheric Dispersion Modelling** — Gaussian plume model with Pasquill-Gifford stability classes showing how pollutants spread from point sources based on wind and atmospheric conditions.

6. **Enforcement Intelligence** — Auto-generated evidence-backed enforcement actions with priority levels, supporting evidence, estimated impact, and downloadable PDF reports.

## Cities Monitored

Delhi | Mumbai | Kolkata | Bengaluru | Chennai | Lucknow | Patna | Hyderabad

## Tech Stack

### Frontend
- Next.js 16 (App Router)
- Tailwind CSS + shadcn/ui
- Leaflet (interactive maps + heatmap)
- Recharts (data visualization)
- motion/react (animations)
- Canvas-based scroll-driven frame animation with spring-damper physics

### Backend
- Python FastAPI + Uvicorn
- SQLite (persistent storage)
- XGBoost (ML model)
- 10 microservices: CPCB Data, Prediction, Attribution, Satellite, Dispersion, Enforcement, Chat, Report, Health Impact, Alert

### AI/ML
- 5-Agent Orchestrated Pipeline: Data Fusion → Analysis → Prediction → Advisory → Enforcement
- XGBoost ensemble (4.1MB trained model)
- Gemini 2.0 Flash (multilingual citizen chat)

### Data Sources
- CPCB via data.gov.in API (primary)
- WAQI API (fallback)
- NASA FIRMS (satellite thermal data)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  DATA SOURCES                                           │
│  CPCB data.gov.in │ WAQI API │ NASA FIRMS │ Gemini 2.0  │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│  FASTAPI BACKEND (10 Services)                          │
│  CPCB │ Prediction │ Attribution │ Satellite │ Dispersion│
│  Enforcement │ Chat │ Report │ Health Impact │ Alert     │
│  SQLite + 10-min Cache │ 12+ REST API Endpoints         │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│  MULTI-AGENT AI ORCHESTRATOR                            │
│  Agent 1: Data Fusion → Agent 2: Analysis →             │
│  Agent 3: Prediction → Agent 4: Advisory →              │
│  Agent 5: Enforcement                                   │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│  NEXT.JS 16 FRONTEND                                    │
│  Interactive Map │ City Rankings │ Station Detail        │
│  Citizen Chat │ Enforcement │ Comparative Dashboard     │
│  Health Impact │ Alerts │ Animated Landing Page          │
└─────────────────────────────────────────────────────────┘
```

## Setup & Run

### Prerequisites
- Node.js 18+
- Python 3.12

### 1. Frontend
```bash
npm install
npm run dev
```

### 2. Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # Add your API keys
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Train ML Model (optional — pre-trained model included)
```bash
cd backend
python -c "from app.services.prediction_service import train_model; train_model(force=True)"
```

### Environment Variables
See `.env.example` for required API keys:
- `DATAGOV_API_KEY` — data.gov.in API key (free registration)
- `WAQI_API_TOKEN` — World Air Quality Index API token
- `GEMINI_API_KEY` — Google Gemini API key (for citizen chat)

## Features

- **Interactive Map** — Leaflet map with color-coded AQI markers, heatmap layer, and NASA FIRMS fire overlay
- **City Rankings** — All 8 cities ranked by AQI with population, station count, and trend indicators
- **Station Detail** — Pollutant breakdown, source attribution pie chart, and 72-hour prediction line chart
- **Citizen AI Chat** — Gemini-powered multilingual chatbot (English, Hindi, Tamil, Kannada, Telugu)
- **Enforcement Panel** — Auto-generated enforcement actions with PDF export
- **Comparative Dashboard** — Multi-city bar charts and radar charts
- **Health Impact** — Pollution-attributable mortality and morbidity estimates
- **Alerts** — Real-time threshold monitoring and notifications
- **Animated Landing** — 48-frame scroll-driven canvas animation with spring-damper physics

## License

MIT

---

**ET AI Hackathon 2026 — Problem Statement 5: AI-Powered Urban Air Quality Intelligence for Smart City Intervention**
