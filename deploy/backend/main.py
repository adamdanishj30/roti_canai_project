"""
Frozen Roti Business - AI Customer Service Chatbot Backend
FastAPI + Google Gemini (google-genai SDK)
"""

import os
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
MODEL_NAME = "gemini-2.5-flash"

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
- Frozen Roti Canai Beef: RM7 each (traditional Chinese beef recipe, introductory launch price).
Fulfillment: Self-pickup from our home, or doorstep delivery (delivery fee varies by location).
Orders & inquiries: Call or WhatsApp +60198858627.

Reply rules:
- Only answer what the customer actually asked. Do not list the full menu, fulfillment options, or contact info unless they are relevant to the question.
- For a greeting like "hi" or "hello", reply with a brief, warm welcome and ask what they'd like to know - nothing else.
- Keep every reply to 1-3 short sentences unless the customer asks for full details (e.g. "what's on the menu").
- Plain text only. Do not use markdown, asterisks, bullet points, or bold formatting of any kind - this chat cannot render them.
- If unsure how to answer, direct them to WhatsApp +60198858627."""

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Frozen Roti Chatbot API",
    description="Customer service chatbot backend powered by Gemini",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def health_check():
    """Simple health check / uptime endpoint."""
    return {"status": "ok", "service": "frozen-roti-chatbot", "model": MODEL_NAME}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Receives a customer message and returns the Gemini-generated reply,
    grounded in the business's fixed system instruction (menu, pricing,
    fulfillment, and contact details).
    """
    user_message = (request.message or "").strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.4,
                max_output_tokens=1024,
            ),
        )

        reply_text = (response.text or "").strip()

        if not reply_text:
            reply_text = (
                "Sorry, I couldn't process that. Please reach out to us "
                "directly on WhatsApp at +60198858627 for help."
            )

        return ChatResponse(reply=reply_text)

    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini API call failed: %s", exc)
        return ChatResponse(
            reply=(
                "Sorry, something went wrong on our end. Please contact us on "
                "WhatsApp at +60198858627 and we'll help you right away."
            )
        )


# ---------------------------------------------------------------------------
# Entrypoint (for `python main.py` convenience; normally run via uvicorn CLI)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
