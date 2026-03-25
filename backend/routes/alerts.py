from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Alert
from pydantic import BaseModel


router = APIRouter()


class AlertIn(BaseModel):
    user_name: str
    timestamp: str
    meeting_id: str


@router.post("/alerts")
def save_alert(data: AlertIn, db: Session = Depends(get_db)):
    alert = Alert(
        user_name=data.user_name,
        timestamp=data.timestamp,
        meeting_id=data.meeting_id
    )
    db.add(alert)
    db.commit()
    return {"status": "saved"}


@router.get("/alerts/{meeting_id}")
def get_alerts(meeting_id: str, db: Session = Depends(get_db)):
    alerts = db.query(Alert).filter(
        Alert.meeting_id == meeting_id
    ).all()
    return alerts