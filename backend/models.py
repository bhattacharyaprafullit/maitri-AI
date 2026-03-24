from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from backend.database import Base


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    timestamp = Column(String, nullable=False)
    meeting_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    meeting_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(Text, nullable=False)
    why_called = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    timestamp = Column(String, nullable=False)
    meeting_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())