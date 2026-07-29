# 🚬 SmokeGuard AI - Cigarette Violation Detection System

> A real-time, web-based cigarette smoking detection dashboard and analytics platform powered by dual-YOLO model inference, spatial containment analysis, ByteTrack multi-object tracking, FastAPI WebSockets, and a Next.js frontend.

---

## 📸 Architecture Overview

```
smoking-detection/
├── ml/
│   ├── models/
│   │   ├── yolo11s.pt          # COCO-pretrained Person Detector & ByteTrack
│   │   └── best.pt             # Custom trained Cigarette Detection Model
│   └── inference/
│       ├── config.py           # Preserved detection thresholds & settings
│       ├── containment.py       # Spatial containment ratio linking algorithm
│       ├── detector.py          # Dual YOLO model inference engine
│       └── stream_processor.py  # Debounced state machine & WebSocket generator
│
├── backend/                     # FastAPI Backend Server
│   ├── app/
│   │   ├── main.py             # Server entrypoint & route registration
│   │   ├── ws/live_feed.py      # Real-time WebSocket event broadcaster
│   │   ├── routers/            # REST APIs (/api/streams, /api/violations, /api/cameras)
│   │   └── db/                 # Database models & SQLite / Postgres engine
│   └── requirements.txt
│
├── frontend/                    # Next.js 14 Web Application
│   ├── app/                    # Dashboard, Violations history, Camera manager
│   ├── components/             # LiveCanvas, StatsCards, ViolationBanner, Table
│   └── lib/                    # WebSocket custom hooks & REST client
│
└── docker-compose.yml           # Production Docker setup (FastAPI GPU + Postgres + Next.js)
```

---

## ⚡ Key Features

- **Dual-Model Inference**:
  - `yolo11s.pt`: COCO-pretrained person detection & persistent ID tracking via **ByteTrack**.
  - `best.pt`: Custom-trained YOLO model specialized for cigarette detection.
- **Spatial Containment Check**:
  - Instead of standard IoU (which fails due to tiny cigarette box sizes), computes the fraction of the cigarette's bounding box area lying inside the person's bounding box (`containment_ratio >= OVERLAP_THRESH`).
- **Debounced State Machine**:
  - Prevents false-positive flickering by requiring **N=5 consecutive smoking frames** before transitioning a person's status from `"smoking"` to confirmed `"violation"`.
- **Low-Bandwidth WebSockets**:
  - Emits structured coordinate JSON events per frame over WebSockets (`ws://localhost:8000/ws/live`) instead of streaming heavy annotated JPEGs.
- **Interactive Live Canvas**:
  - Renders bounding boxes client-side over an MJPEG video feed:
    - 🟢 **Green** (`#22c55e`): Safe person (`ID:N person 0.XX`)
    - 🔴 **Red** (`#ef4444`): Confirmed violation (`ID:N person 0.XX [VIOLATION]`)
    - 🟠 **Orange** (`#f97316`): Cigarette detection (`cigarette 0.XX`)
- **Automated Evidence Capture & Reporting**:
  - Automatically captures JPEG snapshots on violation state transitions and logs violation metadata (`camera_id`, `track_id`, `started_at`, `ended_at`, `confidence`) into SQLite / PostgreSQL.
  - CSV report export support via `GET /api/violations/export`.

---

## ⚙️ Configuration Parameters

Preserved default configuration thresholds in `ml/inference/config.py`:

| Parameter | Default Value | Description |
|---|---|---|
| `PERSON_CONF` | `0.40` | Person detection confidence threshold |
| `CIG_CONF` | `0.25` | Cigarette detection confidence threshold |
| `IOU_THRESH` | `0.45` | NMS IoU threshold |
| `OVERLAP_THRESH` | `0.30` | Containment ratio threshold (`cig_area_inside_person / total_cig_area`) |
| `DEBOUNCE_FRAMES` | `5` | Required consecutive smoking frames before flipping to `"violation"` |

---

## 📡 WebSocket Event Payload Contract

Published over `ws://localhost:8000/ws/live` once per processed frame:

```json
{
  "timestamp": "2026-07-29T14:32:10Z",
  "camera_id": "cam-01",
  "persons": [
    {
      "track_id": 12,
      "bbox": [250.0, 150.0, 550.0, 600.0],
      "status": "violation",
      "confidence": 0.91
    }
  ],
  "cigarettes": [
    {
      "bbox": [290.0, 270.0, 330.0, 300.0],
      "confidence": 0.78
    }
  ],
  "stats": {
    "total_persons": 4,
    "smoking": 1,
    "safe": 3,
    "violations": 1
  }
}
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Git

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/tarunagnihotri534/SmokeDetector.git
cd SmokeDetector

# Install Python dependencies
pip install -r backend/requirements.txt

# Start FastAPI server
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend server will run at `http://localhost:8000`. Access interactive API documentation at `http://localhost:8000/docs`.

### 2. Frontend Setup

```bash
# In a new terminal window
cd frontend

# Install Node dependencies
npm install

# Start Next.js dev server
npm run dev
```

Open `http://localhost:3000` in your web browser to access the dashboard.

---

## 🐳 Docker Deployment

Run the complete stack (FastAPI GPU backend + PostgreSQL + Next.js frontend) with Docker Compose:

```bash
docker-compose up --build
```

---

## 📊 REST API Endpoints

- `GET /health`: System health check
- `POST /api/streams/start`: Start a video stream source (webcam index `0`, video file, or RTSP URL)
- `POST /api/streams/stop`: Stop active stream processor
- `GET /api/streams/feed`: MJPEG live video stream feed
- `GET /api/violations`: List violation audit logs (supports filtering by `camera_id` & pagination)
- `GET /api/violations/stats`: Summary stats (total, today, active counts)
- `GET /api/violations/export`: Download CSV violation report
- `GET /api/cameras`: Manage connected camera sources

---

## 🧪 Testing

Run unit tests for spatial containment math and state machine logic:

```bash
python -m pytest tests/test_ml_inference.py
```

---

## 📜 License

MIT License. Developed for real-time video surveillance and smoking violation monitoring.
