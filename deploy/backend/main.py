"""
Frozen Roti Business - AI Customer Service Chatbot Backend
FastAPI + Google Gemini (google-genai SDK)
"""

import os
import time
import logging
import threading
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# Setup & Configuration
# ---------------------------------------------------------------------------

load_dotenv()  # Loads variables from a local .env file if present

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("roti-chatbot")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.6-flash"

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY environment variable is not set. "
        "Set it before starting the server, e.g. `export GEMINI_API_KEY=your_key_here`."
    )

# Official google-genai client, configured once at startup and reused.
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """You are a friendly customer service assistant for a family-run frozen roti business.
Menu:
- Frozen Roti Canai (Signature): RM8 per pack (5 pieces).
- Frozen Beef Roti Canai: RM14 per pack (2 pieces).
- Family Freezer Bundle: RM50 per bundle. Includes 3 Signature Roti Canai packs (5 pieces each) and 2 Beef Roti Canai packs (2 pieces each).
Fulfillment: Self-pickup from our home, or doorstep delivery (delivery fee varies by location).
Orders & inquiries: Call or WhatsApp +60192788617.
Order process: after checkout on the website, the seller contacts the customer shortly on WhatsApp to confirm. The order is only prepared and processed once the customer agrees.

Reply rules:
- Only answer what the customer actually asked. Do not list the full menu, fulfillment options, or contact info unless they are relevant to the question.
- For a greeting like "hi" or "hello", reply with a brief, warm welcome and ask what they'd like to know - nothing else.
- Keep every reply to 1-3 short sentences unless the customer asks for full details (e.g. "what's on the menu").
- Plain text only. Do not use markdown, asterisks, bullet points, or bold formatting of any kind - this chat cannot render them.
- If unsure how to answer, direct them to WhatsApp +60192788617."""

# ---------------------------------------------------------------------------
# Quota protection: caps how much Gemini usage anyone can trigger.
# All limits can be changed from Render environment variables.
# ---------------------------------------------------------------------------

MAX_MESSAGE_CHARS = int(os.environ.get("MAX_MESSAGE_CHARS", "500"))
PER_IP_PER_MINUTE = int(os.environ.get("CHAT_PER_IP_PER_MINUTE", "6"))
PER_IP_PER_DAY = int(os.environ.get("CHAT_PER_IP_PER_DAY", "40"))
GLOBAL_PER_DAY = int(os.environ.get("CHAT_GLOBAL_PER_DAY", "500"))  # hard backstop

_rate_lock = threading.Lock()
_ip_hits = defaultdict(deque)  # ip -> timestamps of requests in the last 24h
_global_day = {"date": None, "count": 0}


def _client_ip(http_request: Request) -> str:
    # Behind Render's proxy the real client IP is in X-Forwarded-For.
    fwd = http_request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return http_request.client.host if http_request.client else "unknown"


def check_rate_limit(http_request: Request) -> None:
    """Raises HTTP 429 if this request would exceed a usage cap."""
    now = time.time()
    today = time.strftime("%Y-%m-%d", time.gmtime(now))
    ip = _client_ip(http_request)

    with _rate_lock:
        if _global_day["date"] != today:
            _global_day["date"] = today
            _global_day["count"] = 0

        if _global_day["count"] >= GLOBAL_PER_DAY:
            logger.warning("Global daily chat cap reached")
            raise HTTPException(status_code=429, detail="Chat is busy right now. Please try again later.")

        hits = _ip_hits[ip]
        while hits and now - hits[0] > 86400:
            hits.popleft()

        if len(hits) >= PER_IP_PER_DAY:
            raise HTTPException(status_code=429, detail="Daily chat limit reached. Please try again tomorrow.")
        if sum(1 for t in hits if now - t <= 60) >= PER_IP_PER_MINUTE:
            raise HTTPException(status_code=429, detail="Too many messages. Please wait a minute.")

        hits.append(now)
        _global_day["count"] += 1

        # Keep memory bounded if someone floods with many different IPs.
        if len(_ip_hits) > 5000:
            for k in [k for k, v in _ip_hits.items() if not v or now - v[-1] > 86400]:
                del _ip_hits[k]


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Frozen Roti Chatbot API",
    description="Customer service chatbot backend powered by Gemini",
    version="1.0.0",
)

# Set ALLOWED_ORIGINS in Render to your website(s), comma-separated, e.g.
#   https://yourshop.com,https://www.yourshop.com
# If unset it stays "*" so the site keeps working until you configure it.
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=MAX_MESSAGE_CHARS)


class ChatResponse(BaseModel):
    reply: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def health_check():
    """Simple health check / uptime endpoint."""
    return {"status": "ok", "service": "frozen-roti-chatbot", "model": MODEL_NAME}


@app.get("/orders")
def orders_page():
    """Serves the internal family order-tracking app (mom/sis order entry
    and dad's kitchen view). Protected by Firebase Authentication inside orders.html."""
    return FileResponse(Path(__file__).parent / "orders.html")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, http_request: Request):
    """
    Receives a customer message and returns the Gemini-generated reply,
    grounded in the business's fixed system instruction (menu, pricing,
    fulfillment, and contact details).
    """
    user_message = (request.message or "").strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    check_rate_limit(http_request)

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.4,
                max_output_tokens=1024,
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        )

        reply_text = (response.text or "").strip()

        if not reply_text:
            reply_text = (
                "Sorry, I couldn't process that. Please reach out to us "
                "directly on WhatsApp at +60192788617 for help."
            )

        return ChatResponse(reply=reply_text)

    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini API call failed: %s", exc)
        return ChatResponse(
            reply=(
                "Sorry, something went wrong on our end. Please contact us on "
                "WhatsApp at +60192788617 and we'll help you right away."
            )
        )


# ---------------------------------------------------------------------------
# Entrypoint (for `python main.py` convenience; normally run via uvicorn CLI)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
