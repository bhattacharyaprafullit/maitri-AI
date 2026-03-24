from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Summary
from pydantic import BaseModel


router = APIRouter()


class SummaryIn(BaseModel):
    topic: str
    why_called: str
    action: str
    timestamp: str
    meeting_id: str


@router.post("/summaries")
def save_summary(data: SummaryIn, db: Session = Depends(get_db)):
    summary = Summary(
        topic=data.topic,
        why_called=data.why_called,
        action=data.action,
        timestamp=data.timestamp,
        meeting_id=data.meeting_id
    )
    db.add(summary)
    db.commit()
    return {"status": "saved"}


@router.get("/summaries/{meeting_id}")
def get_summaries(meeting_id: str, db: Session = Depends(get_db)):
    summaries = db.query(Summary).filter(
        Summary.meeting_id == meeting_id
    ).all()
    return summaries