from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Transcript
from pydantic import BaseModel


router = APIRouter()


class TranscriptIn(BaseModel):
    text: str
    timestamp: str
    meeting_id: str


@router.post("/transcripts")
def save_transcript(data: TranscriptIn, db: Session = Depends(get_db)):
    transcript = Transcript(
        text=data.text,
        timestamp=data.timestamp,
        meeting_id=data.meeting_id
    )
    db.add(transcript)
    db.commit()
    return {"status": "saved"}


@router.get("/transcripts/{meeting_id}")
def get_transcripts(meeting_id: str, db: Session = Depends(get_db)):
    transcripts = db.query(Transcript).filter(
        Transcript.meeting_id == meeting_id
    ).all()
    return transcripts