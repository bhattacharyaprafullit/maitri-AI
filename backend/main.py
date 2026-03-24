from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.database import init_db
from backend.routes import transcripts, alerts, summaries


@asynccontextmanager
async def lifespan(app: FastAPI):
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


app.include_router(transcripts.router, prefix="/api", tags=["Transcripts"])
app.include_router(alerts.router, prefix="/api", tags=["Alerts"])
app.include_router(summaries.router, prefix="/api", tags=["Summaries"])