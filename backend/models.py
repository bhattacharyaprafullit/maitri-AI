from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from sqlalchemy.sql import func
from database import Base

class UserMetaData(Base):
    __tablename__ = "user_metadata"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    telegram_user_name = Column(String, nullable=False)
    english_variants = Column(ARRAY(String), nullable=True, default=list)
    hindi_variants = Column(ARRAY(String), nullable=True, default=list)
    variants = Column(ARRAY(String), nullable=True, default=list)

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