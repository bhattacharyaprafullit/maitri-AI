from pydantic import BaseModel, Field


class MeetingSummary(BaseModel):
    topic: str = Field(description="One line — what the meeting is currently about")
    why_called: str = Field(description="One line — exactly why was the person called or mentioned")
    action: str = Field(description="One line — what the person should say or do right now to respond confidently")


