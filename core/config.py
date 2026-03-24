import os
from dotenv import load_dotenv

load_dotenv()

DEVICE_INDEX = 1
SAMPLE_RATE = 44100
CHUNK_SECONDS = 5
CHANNELS = 1

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

WHISPER_MODEL = "whisper-large-v3-turbo"
LLM_MODEL = "openai/gpt-oss-120b"

TOP_K_RESULTS = 3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSCRIPT_PATH = os.path.join(BASE_DIR, "transcript.txt")
VECTOR_STORE_PATH = os.path.join(BASE_DIR, "chroma_store")
USER_CONFIG_PATH = os.path.join(BASE_DIR, "user_config.json")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/meetingcopilot"
)