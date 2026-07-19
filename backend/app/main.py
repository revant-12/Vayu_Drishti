"""
VayuDrishti — Urban Air Quality Intelligence Platform
FastAPI Backend Server
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers import api
from app.services.cpcb_service import init_db
from app.services.prediction_service import train_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB, train ML model if needed."""
    print("Initializing VayuDrishti backend...")
    init_db()
    print("Training ML model (first run may take ~30s)...")
    metrics = train_model()
    print(f"Model ready — Accuracy: {metrics.get('accuracy_pct', 'N/A')}%")
    yield
    print("VayuDrishti shutting down.")


app = FastAPI(
    title="VayuDrishti API",
    description="AI-Powered Urban Air Quality Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "VayuDrishti API",
        "version": "1.0.0",
        "description": "AI-Powered Urban Air Quality Intelligence",
        "endpoints": {
            "stations": "/api/stations",
            "station_detail": "/api/stations/{station_id}",
            "predictions": "/api/predictions/{station_id}",
            "enforcement": "/api/enforcement",
            "cities": "/api/cities",
            "model_info": "/api/model/info",
        },
    }
