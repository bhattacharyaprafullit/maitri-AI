from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from sqlalchemy.orm import Session
from database import init_db, get_db
from routes import transcripts, alerts, summaries
from setup import generate_variants, save_config
from core.vector_store import VectorStore
from core.config import USER_CONFIG_PATH
import agent.graph as graph_module
from agent.graph import meeting_pipeline
import json
import time
import uuid

MEETING_ID = str(uuid.uuid4())
last_alert_time = 0
COOLDOWN_SECONDS = 30


@asynccontextmanager
async def lifespan(app: FastAPI):
    vector_store = VectorStore()
    graph_module.vector_store = vector_store
    init_db()
    print("✅ Meeting Copilot API started!")
    yield


app = FastAPI(
    title="Maitri AI API",
    description="AI-powered meeting assistant — never miss when your name is called",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
def root():
    return {
        "status": "running",
        "project": "Meeting Copilot",
        "version": "1.0.0"
    }


@app.post("/set-name")
def set_name(data: dict, db: Session = Depends(get_db)):
    name = data["name"]
    result = generate_variants(name)
    save_config(result, db)
    return {"status": "variants generated"}


@app.post("/captions")
async def receive_captions(data: dict):
    global last_alert_time

    text = data.get("text", "")
    if not text:
        return {"alert_sent": False}

    print("CAPTION:", text[:100])

    try:
        with open(USER_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        return {"alert_sent": False, "error": "Pehle naam set karo"}

    now = time.time()
    if now - last_alert_time < COOLDOWN_SECONDS:
        return {"alert_sent": False, "reason": "cooldown"}

    timestamp = time.strftime("%H:%M:%S")

    result = meeting_pipeline.invoke({
        "text": text,
        "timestamp": timestamp,
        "your_name": config["name"],
        "name_variants": config["variants"],
        "name_detected": False,
        "context": text,
        "retrieved_chunks": [],
        "summary": None,
        "meeting_id": MEETING_ID
    })

    if result.get("name_detected"):
        last_alert_time = now
        return {"alert_sent": True}

    return {"alert_sent": False}


app.include_router(transcripts.router, prefix="/api", tags=["Transcripts"])
app.include_router(alerts.router, prefix="/api", tags=["Alerts"])
app.include_router(summaries.router, prefix="/api", tags=["Summaries"])