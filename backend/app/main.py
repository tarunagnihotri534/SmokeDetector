import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import SNAPSHOTS_DIR, CORS_ORIGINS
from backend.app.db.database import init_db
from backend.app.routers import streams, violations, cameras
from backend.app.ws.live_feed import websocket_live_feed_endpoint

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cigarette Violation Detection API",
    description="Real-time cigarette smoking violation detection service & WebSocket feed",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount snapshots directory for serving violation snapshot images
app.mount("/snapshots", StaticFiles(directory=str(SNAPSHOTS_DIR)), name="snapshots")

# Include REST Routers
app.include_router(streams.router)
app.include_router(violations.router)
app.include_router(cameras.router)

# WebSocket Endpoint
app.add_api_websocket_route("/ws/live", websocket_live_feed_endpoint)


@app.on_event("startup")
def on_startup():
    logger.info("Initializing Database...")
    init_db()
    # Auto-start default stream for out-of-the-box demo
    streams.stream_manager.start_stream(source="0", camera_id="cam-01")


@app.on_event("shutdown")
def on_shutdown():
    logger.info("Stopping stream processors...")
    streams.stream_manager.stop_stream()


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Cigarette Violation Detection System"}
