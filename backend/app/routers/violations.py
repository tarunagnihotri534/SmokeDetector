import csv
import io
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.db.models import Violation
from backend.app.db.schemas import ViolationResponse

router = APIRouter(prefix="/api/violations", tags=["violations"])


@router.get("", response_model=List[ViolationResponse])
def get_violations(
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Violation)
    if camera_id:
        query = query.filter(Violation.camera_id == camera_id)
    violations = query.order_by(Violation.started_at.desc()).offset(offset).limit(limit).all()
    return violations


@router.get("/stats")
def get_violation_stats(db: Session = Depends(get_db)):
    now = datetime.datetime.now(datetime.timezone.utc)
    today_start = datetime.datetime(now.year, now.month, now.day, tzinfo=datetime.timezone.utc)

    total_count = db.query(Violation).count()
    today_count = db.query(Violation).filter(Violation.started_at >= today_start).count()
    active_count = db.query(Violation).filter(Violation.ended_at.is_(None)).count()

    return {
        "total_violations": total_count,
        "violations_today": today_count,
        "active_violations": active_count
    }


@router.get("/export")
def export_violations_csv(db: Session = Depends(get_db)):
    violations = db.query(Violation).order_by(Violation.started_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Violation ID", "Camera ID", "Track ID", "Started At", "Ended At", "Snapshot Path", "Confidence"
    ])

    for v in violations:
        writer.writerow([
            v.id,
            v.camera_id,
            v.track_id,
            v.started_at.isoformat() if v.started_at else "",
            v.ended_at.isoformat() if v.ended_at else "",
            v.snapshot_path or "",
            v.confidence or 0.0
        ])

    output.seek(0)
    response = StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = f"attachment; filename=violations_report_{datetime.date.today()}.csv"
    return response
