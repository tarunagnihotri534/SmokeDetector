from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.db.models import Camera
from backend.app.db.schemas import CameraCreate, CameraResponse

router = APIRouter(prefix="/api/cameras", tags=["cameras"])


@router.get("", response_model=List[CameraResponse])
def get_cameras(db: Session = Depends(get_db)):
    cameras = db.query(Camera).all()
    if not cameras:
        # Seed default demo cameras
        cam1 = Camera(
            id="cam-01",
            name="Sample HD Feed (6570562)",
            source_type="file",
            source_url="6570562-hd_1080_1920_25fps.mp4",
            status="active"
        )
        cam2 = Camera(
            id="cam-02",
            name="Webcam / Primary Input",
            source_type="webcam",
            source_url="0",
            status="active"
        )
        db.add_all([cam1, cam2])
        db.commit()
        db.refresh(cam1)
        db.refresh(cam2)
        cameras = [cam1, cam2]
    return cameras


@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
def create_camera(cam: CameraCreate, db: Session = Depends(get_db)):
    existing = db.query(Camera).filter(Camera.id == cam.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Camera ID already exists")

    new_cam = Camera(
        id=cam.id,
        name=cam.name,
        source_type=cam.source_type,
        source_url=cam.source_url,
        status="active"
    )
    db.add(new_cam)
    db.commit()
    db.refresh(new_cam)
    return new_cam


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camera(camera_id: str, db: Session = Depends(get_db)):
    cam = db.query(Camera).filter(Camera.id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    db.delete(cam)
    db.commit()
    return None
