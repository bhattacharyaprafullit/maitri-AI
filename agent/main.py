import sys
import os
import time
import signal
import threading
import queue
import json
import uuid

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import sounddevice as sd
from scipy.signal import resample
from groq import Groq
import wave
import tempfile
import requests

from core.config import (
    DEVICE_INDEX, SAMPLE_RATE, CHUNK_SECONDS,
    CHANNELS, GROQ_API_KEY, WHISPER_MODEL,
    TRANSCRIPT_PATH, USER_CONFIG_PATH
)
from core.vector_store import VectorStore
import agent.graph as graph_module
from agent.graph import meeting_pipeline

# Vector store — ek hi instance, graph ko inject karo
vector_store = VectorStore()
graph_module.vector_store = vector_store

# Global stream — signal handler mein use hoga
stream = None

# Signal handler
def signal_handler(sig, frame):
    global stream
    print(f"\nStopping...")
    if stream:
        stream.stop()
        stream.close()
    os._exit(0)  # forcefully exit — daemon threads bhi band ho jaayenge

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
if hasattr(signal, 'SIGBREAK'):
    signal.signal(signal.SIGBREAK, signal_handler)

# User config
def load_user_config():
    with open(USER_CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config['name'], config['variants']

YOUR_NAME, NAME_VARIANTS = load_user_config()
MEETING_ID = str(uuid.uuid4())
print(f"User: {YOUR_NAME} | {len(NAME_VARIANTS)} variants")
print("=" * 55)
print("   Maitri AI — Your Meeting Companion")
print("=" * 55)
print(f"Detecting   : '{YOUR_NAME}'")
print(f"Meeting ID  : {MEETING_ID}")
print(f"Device      : {DEVICE_INDEX} | {SAMPLE_RATE}Hz")
print("=" * 55)

groq_client = Groq(api_key=GROQ_API_KEY)
audio_queue = queue.Queue(maxsize=200)
transcript_buffer = []
buffer_lock = threading.Lock()


def audio_callback(indata, frames, time_info, status):
    try:
        audio_queue.put_nowait(indata.copy())
    except queue.Full:
        pass


def transcribe_chunk(audio_data):
    target_samples = int(len(audio_data) * 16000 / SAMPLE_RATE)
    audio_resampled = resample(audio_data, target_samples)
    audio_int16 = (audio_resampled * 32767).astype(np.int16)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name
        with wave.open(tmp_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio_int16.tobytes())
        with open(tmp_path, 'rb') as f:
            result = groq_client.audio.transcriptions.create(
                model=WHISPER_MODEL, file=f, language=None)
        return result.text.strip()
    except Exception as e:
        print(f'Whisper error: {e}')
        return ''
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def save_to_backend(text, timestamp):
    try:
        requests.post(
            "http://localhost:8000/api/transcripts",
            json={
                "text": text,
                "timestamp": timestamp,
                "meeting_id": MEETING_ID
            },
            timeout=2
        )
    except Exception:
        pass


def run_pipeline(text, timestamp, context):
    try:
        meeting_pipeline.invoke({
            "text": text,
            "timestamp": timestamp,
            "your_name": YOUR_NAME,
            "name_variants": NAME_VARIANTS,
            "name_detected": False,
            "context": context,
            "retrieved_chunks": [],
            "summary": None,
            "meeting_id": MEETING_ID
        })
    except Exception as e:
        print(f"Pipeline error: {e}")


def worker():
    audio_buffer = np.array([], dtype=np.float32)
    samples_needed = SAMPLE_RATE * CHUNK_SECONDS

    while True:
        try:
            chunk = audio_queue.get(timeout=1)
            chunk_mono = chunk[:, 0] if chunk.ndim > 1 else chunk.flatten()
            audio_buffer = np.concatenate([audio_buffer, chunk_mono])

            if len(audio_buffer) >= samples_needed:
                segment = audio_buffer[:samples_needed]
                audio_buffer = audio_buffer[samples_needed:]

                text = transcribe_chunk(segment)

                if text:
                    timestamp = time.strftime("%H:%M:%S")
                    print(f'[{timestamp}] {text}')

                    with buffer_lock:
                        transcript_buffer.append(text)
                        if len(transcript_buffer) > 12:
                            transcript_buffer.pop(0)
                        context_snapshot = " ".join(transcript_buffer[-12:])

                    threading.Thread(
                        target=vector_store.add,
                        args=(text, timestamp),
                        daemon=True
                    ).start()

                    try:
                        with open(TRANSCRIPT_PATH, 'a', encoding='utf-8') as f:
                            f.write(f'[{timestamp}] {text}\n')
                    except Exception:
                        pass

                    threading.Thread(
                        target=save_to_backend,
                        args=(text, timestamp),
                        daemon=True
                    ).start()

                    threading.Thread(
                        target=run_pipeline,
                        args=(text, timestamp, context_snapshot),
                        daemon=True
                    ).start()

        except queue.Empty:
            continue
        except Exception as e:
            print(f'Error: {e}')
            continue


# Main
t = threading.Thread(target=worker, daemon=True)  # daemon=True
t.start()

stream = sd.InputStream(
    samplerate=SAMPLE_RATE,
    channels=CHANNELS,
    dtype='float32',
    device=DEVICE_INDEX,
    callback=audio_callback
)
stream.start()
print("Maitri AI is listening... (Ctrl+C to stop)")

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nStopping...")
finally:
    stream.stop()
    stream.close()
    print('Done.')