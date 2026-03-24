import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Maitri AI",
    page_icon="🤝",
    layout="wide"
)

st.title("🤝 Maitri AI")
st.markdown("Your AI-powered meeting companion — never miss a moment")
st.divider()

# --- SIDEBAR ---
st.sidebar.header("Settings")
meeting_id = st.sidebar.text_input(
    "Meeting ID",
    placeholder="Paste your meeting ID here..."
)

if st.sidebar.button("Refresh"):
    st.rerun()

auto_refresh = st.sidebar.checkbox("Auto Refresh (every 5s)", value=False)

if not meeting_id:
    st.info("Enter your Meeting ID in the sidebar to view data.")
    st.stop()

# --- FETCH DATA ---
def fetch(endpoint):
    try:
        r = requests.get(f"{API_URL}{endpoint}", timeout=3)
        if r.status_code == 200:
            return r.json()
        return []
    except Exception as e:
        st.error(f"API Error: {e}")
        return []

transcripts = fetch(f"/api/transcripts/{meeting_id}")
alerts = fetch(f"/api/alerts/{meeting_id}")
summaries = fetch(f"/api/summaries/{meeting_id}")

# --- METRICS ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Transcripts", len(transcripts))
with col2:
    st.metric("Name Detected", len(alerts))
with col3:
    st.metric("AI Summaries", len(summaries))

st.divider()

# --- SUMMARIES ---
st.header("🤖 AI Summaries")
if summaries:
    for s in reversed(summaries):
        with st.container(border=True):
            st.markdown(f"**Time:** {s['timestamp']}")
            st.markdown(f"**Topic:** {s['topic']}")
            st.markdown(f"**Why Called:** {s['why_called']}")
            st.markdown(f"**Action:** {s['action']}")
else:
    st.info("No summaries yet.")

st.divider()

# --- ALERTS ---
st.header("🔔 Alerts")
if alerts:
    df = pd.DataFrame(alerts)
    st.dataframe(
        df[["timestamp", "user_name", "meeting_id"]],
        use_container_width=True
    )
else:
    st.info("No alerts yet.")

st.divider()

# --- TRANSCRIPTS ---
st.header("📝 Live Transcript")
if transcripts:
    transcript_text = "\n".join([
        f"[{t['timestamp']}] {t['text']}"
        for t in transcripts
    ])
    st.text_area(
        "Transcript",
        value=transcript_text,
        height=400,
        disabled=True
    )
else:
    st.info("No transcript yet.")

# --- AUTO REFRESH ---
if auto_refresh:
    import time
    time.sleep(5)
    st.rerun()