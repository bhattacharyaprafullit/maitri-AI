from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.tools import tool
from fuzzywuzzy import fuzz
import requests

from core.config import GROQ_API_KEY, LLM_MODEL, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from core.models import MeetingSummary

# vector_store — main.py se inject hoga, yahan initialize nahi hoga
# Ye None rahega jab tak main.py set na kare
vector_store = None

# --- LLM SETUP ---
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=LLM_MODEL,
    timeout=10,        # 10 seconds mein response nahi aaya toh fail
    max_retries=1
)
parser = PydanticOutputParser(pydantic_object=MeetingSummary)

prompt = ChatPromptTemplate.from_template("""
You are an AI assistant helping a meeting participant named {name} who was distracted.
{name} just heard their name called in the meeting but missed the context.

Recent meeting transcript (last 60 seconds):
{context}

Retrieved relevant context from earlier in the meeting:
{retrieved}

Analyze everything and help {name} respond confidently.

{format_instructions}

Rules:
- Be concise and actionable
- If transcript is unclear, make best guess
- Write as if directly briefing {name} in real time
- Action should be a specific sentence {name} can say immediately
""")

summary_chain = prompt | llm | parser


# --- STATE ---
class GraphState(TypedDict):
    text: str
    timestamp: str
    your_name: str
    name_variants: List[str]
    name_detected: bool
    context: str
    retrieved_chunks: List[str]
    summary: Optional[MeetingSummary]
    meeting_id: str


# --- LANGCHAIN TOOLS ---
@tool
def detect_name_tool(text: str, name: str, variants: str) -> bool:
    """Detect if a person's name is mentioned in the transcript"""
    text_lower = text.lower()

    for variant in variants.split(","):
        if variant.strip().lower() in text_lower:
            return True

    for word in text_lower.split():
        if fuzz.ratio(name.lower(), word) >= 70:
            return True

    return False


@tool
def send_telegram_tool(message: str) -> str:
    """Send a meeting alert notification via Telegram"""
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            }
        )
        if response.status_code == 200:
            return "Notification sent!"
        return f"Failed: {response.text}"
    except Exception as e:
        return f"Error: {e}"


@tool
def save_to_backend_tool(
    user_name: str,
    timestamp: str,
    meeting_id: str,
    topic: str,
    why_called: str,
    action: str
) -> str:
    """Save alert and summary to FastAPI backend"""
    try:
        requests.post("http://localhost:8000/api/alerts", json={
            "user_name": user_name,
            "timestamp": timestamp,
            "meeting_id": meeting_id
        })
        requests.post("http://localhost:8000/api/summaries", json={
            "topic": topic,
            "why_called": why_called,
            "action": action,
            "timestamp": timestamp,
            "meeting_id": meeting_id
        })
        return "Saved to backend!"
    except Exception as e:
        return f"Backend error: {e}"


# --- NODE 1: DETECT ---
def detect_node(state: GraphState) -> GraphState:
    detected = detect_name_tool.invoke({
        "text": state["text"],
        "name": state["your_name"],
        "variants": ",".join(state["name_variants"])
    })
    if detected:
        print("Name detected!")
    return {**state, "name_detected": detected}


# --- NODE 2: RETRIEVE ---
def retrieve_node(state: GraphState) -> GraphState:
    # main.py se inject kiya hua vector_store use karo
    # Agar None hai toh empty list return karo — crash nahi
    if vector_store is None:
        return {**state, "retrieved_chunks": []}
    try:
        retrieved = vector_store.search(state["context"], top_k=3)
        print(f"Retrieved {len(retrieved)} chunks")
        return {**state, "retrieved_chunks": retrieved}
    except Exception:
        return {**state, "retrieved_chunks": []}


# --- NODE 3: SUMMARIZE ---
def summarize_node(state: GraphState) -> GraphState:
    print("Generating summary...")
    retrieved_text = (
        "\n".join(state["retrieved_chunks"][:3])
        if state["retrieved_chunks"]
        else "No previous context available"
    )
    try:
        result = summary_chain.invoke({
            "context": state["context"],
            "retrieved": retrieved_text,
            "name": state["your_name"],
            "format_instructions": parser.get_format_instructions()
        })
        print("Summary ready!")
        return {**state, "summary": result}
    except Exception as e:
        print(f"LLM timeout/error: {e}")
        return {**state, "summary": MeetingSummary(
            topic="Meeting in progress",
            why_called="Your name was called",
            action="Please check the meeting"
        )}


# --- NODE 4: NOTIFY ---
def notify_node(state: GraphState) -> GraphState:
    summary = state["summary"]
    message = f"""Meeting Alert - {state['your_name']}!

Time: {state['timestamp']}

Topic: {summary.topic}
Why Called: {summary.why_called}
Action: {summary.action}

Meeting Copilot - Powered by LangGraph + RAG"""

    send_telegram_tool.invoke({"message": message})

    save_to_backend_tool.invoke({
        "user_name": state["your_name"],
        "timestamp": state["timestamp"],
        "meeting_id": state["meeting_id"],
        "topic": summary.topic,
        "why_called": summary.why_called,
        "action": summary.action
    })
    return state


# --- ROUTING ---
def should_process(state: GraphState) -> str:
    return "retrieve" if state["name_detected"] else "end"


# --- BUILD GRAPH ---
def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("detect", detect_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("summarize", summarize_node)
    graph.add_node("notify", notify_node)

    graph.set_entry_point("detect")

    graph.add_conditional_edges(
        "detect",
        should_process,
        {
            "retrieve": "retrieve",
            "end": END
        }
    )

    graph.add_edge("retrieve", "summarize")
    graph.add_edge("summarize", "notify")
    graph.add_edge("notify", END)

    return graph.compile()


meeting_pipeline = build_graph()
print("LangGraph pipeline ready!")