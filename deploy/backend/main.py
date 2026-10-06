"""
Frozen Roti Business - AI Customer Service Chatbot Backend
FastAPI + Google Gemini (google-genai SDK)
"""

import os
import time
import secrets
import logging
import threading
from collections import defaultdict, deque
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
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

SYSTEM_INSTRUCTION = """You are a friendly customer service assistant for "Jar & Maz Homemade", a family-run frozen roti business by Paksu Jar & Maksu Maz (Dapur Paksu Jar & Maksu Maz). Always refer to "Paksu Jar" and "Maksu Maz" by their names (never use internal family terms like "Abah" with customers).
Menu & Weights:
- Frozen Roti Canai (Signature): RM8 per pack (5 pieces). Weight is approximately 530g per pack.
- Frozen Beef Roti Canai: RM14 per pack (2 pieces). Inti daging cincang berempah yang berperisa / Seasoned aromatic minced beef. Weight is approximately 300g per pack.
- Family Freezer Bundle: RM99 per bundle (RM100 normal value, saves RM1). Includes 6 Beef Roti Canai packs (2 pieces each @ RM14) and 2 Plain Roti Canai packs (5 pieces each @ RM8). Total bundle weight is approximately 2.86kg.
- Chocolate Chip Cookies: RM38 per jar. Made with premium Golden Churn Butter and Beryl's chocolate chips, loaded with crunchy almonds and walnuts. 33–36 pieces per jar. Net weight: ~200g–210g per jar (Gross weight with jar: 263g–275g, shipping calculation uses 0.275kg). Jar dimensions: Diameter 9cm, Height 10.5cm.
- Wedding & Event Doorgift Cookies: Mini Golden Churn chocolate chip cookies in charming mini jars for weddings, corporate events & aqiqah. Minimum order 100 small jars. Pricing depends on total quantity. Customers should DM Maksu Maz directly on WhatsApp (+60192788617) for quotations.

Cooking & Heating Instructions (#FrozenRotiCanaibyPaksuJar):
🟢 KATEGORI 1: JIKA DAH NYAHBEKU (THAWED) / KELUAR DARI FRIDGE SEMALAMAN
(Roti sudah lembut pada suhu bilik atau disimpan di ruang chiller semalaman)

• Air Fryer:
  • Suhu: 170°C
  • Masa: 3 – 5 minit sahaja (letak atas jaring tanpa lapik).
  • Sebab: Roti sudah tidak beku, jadi 3–5 minit sudah cukup untuk kulit garing keemasan tanpa risiko hangus!

• Kuali (Pan-fry):
  • Panaskan atas kuali leper tanpa minyak selama 2 – 3 minit ikut citarasa (balik-balikkan).
  • Boleh sapu sedikit marjerin semasa memanaskan untuk aroma wangi.
  • (Untuk Roti Biasa: Angkat panas-panas dan terus tepok mamak style supaya kembang berlapis).

🔵 KATEGORI 2: JIKA TERUS DARI FREEZER (BEKU KERAS / TAK SEMPAT DEFROST)
(Bila nak makan serta-merta tanpa sempat nyahbeku)

• 🥩 Beef Roti Canai (Air Fryer):
  • Suhu: 165°C (suhu rendah sedikit)
  • Masa: 5 – 10 minit ikut citarasa (tanpa lapik atas jaring).
  • Penting: Suhu 165°C memastikan kulit luar tidak hangus sambil memberi masa untuk inti daging berempah di dalamnya panas sekata dan berjus!

• 🥞 Roti Canai Biasa (Plain):
  • Pilihan A (Paling Gebu): Stim / Kukus 2 – 4 minit (roti jadi gebu gebas dan sangat lembut! Boleh layur sekejap atas kuali jika mahu bahagian tepi garing).
  • Pilihan B (Air Fryer): 165°C–170°C selama 5 minit, angkat dan terus tepok mamak style.
  • Pilihan C (Kuali): Letak terus atas api kecil, pusing-pusing dan balikkan, angkat terus tepok mamak style.
  • Pilihan D: Magic pan atau pembakar roti (pop-up toaster).
3. Test Your Creativity (Resipi Kreatif Paksu):
   - Roti Canai Pizza: Guna roti canai as pizza base. Sapukan sos marinara, letak pepperoni, cheese, cendawan, capsicum dan olive. Bakar dalam oven selama 10 minit. Gerenti budak-budak suka.
   - Roti Canai Cheese: Simply letak a few pcs of cheese antara 2 keping roti canai dan panaskan sama ada atas kuali atau dalam oven.
   - Roti Canai Telor: Pecahkan telor atas roti canai dan panaskan, atau letak telor separuh masak.
   - Roti Canai Gulong: Kalau ada kari, rendang atau sambal leftovers, simply letak atas roti canai dan gulong. Memang sedap!
   - Roti Canai Philly Cheesesteak: Letak cebisan daging yang dah dimasak atas kuali bersama sedikit black pepper dan garam. Letak sekali mushroom dan cheese. Panaskan. Dari yang kecik hingga yang besar akan suka!

Fulfillment & Delivery Options:
1. Self-pickup: 100% Free from Putra Heights 47650.
2. Putra Heights (47650): 100% FREE doorstep delivery! Paksu Jar delivers personally to your doorstep for free.
3. Klang Valley & Shah Alam (Local Delivery by Paksu Jar):
   - Covers all Klang Valley and Shah Alam areas (e.g. Subang Jaya, Shah Alam, Petaling Jaya, Bandar Utama, Damansara, Puchong, Kuala Lumpur, Cheras, Ampang, etc.).
   - IMPORTANT: Delivery is done personally by Paksu Jar. NEVER use or quote Cold Chain for Klang Valley or Shah Alam! Do NOT quote cold chain rates or thermal packaging box fees.
   - Klang Valley delivery rate is affordable and estimated by distance from Putra Heights: Base fare RM5.00 + RM0.60 per km.
   - For example: nearby areas like Subang Jaya/Shah Alam are around RM7-RM10. Areas like Petaling Jaya, Bandar Utama, Damansara, or KL are around RM11-RM15.
   - Unlike cold chain, order weight does not increase this local delivery fee.
   - Order Confirmation by Maksu Maz: The WhatsApp phone number (+60192788617) belongs to Maksu Maz (customers will see Maksu Maz's profile picture on WhatsApp). After the customer places an order on the website, Maksu Maz will contact them on WhatsApp to confirm the order, delivery timing, and final fee before preparation.
4. Outside Klang Valley & Outside Shah Alam (Outstation Peninsular Malaysia):
   - Applies ONLY to locations outside Klang Valley (e.g. Johor, Penang, Perak, Pahang, Melaka, Kedah, Negeri Sembilan, Terengganu, Kelantan, Perlis).
   - ONLY these outstation locations use Ninja Van Cold Chain frozen delivery to keep items frozen.
   - Ninja Van Cold Chain Rate Card (Walk-in base rate excluding SST):
     * Up to 1kg: RM20.00 base rate.
     * Each additional kg up to 30kg: +RM2.00 per kg (e.g. 2kg is RM22, 3kg is RM24, 4kg is RM26, 5kg is RM28).
     * Add 6% SST to the rate.
     * Maksu Maz confirms the final dispatch schedule and cost with Ninja Van after order submission.
Serving suggestion: Enjoy with gravy of your choice, sambal, or by itself (do not specify curry).
Facebook: Frozen Roti Canai by Paksu Jar (facebook.com/FrozenRotiCanaiByPaksu).
Orders & inquiries: Call or WhatsApp Maksu Maz at +60192788617.
Order process: after checkout on the website, Maksu Maz contacts the customer shortly on WhatsApp to confirm. The order is only prepared and processed once the customer agrees.

Reply rules:
- Only answer what the customer actually asked. Do not list the full menu, fulfillment options, or contact info unless they are relevant to the question.
- When asked how to cook, heat, or panaskan roti:
  NEVER write lengthy paragraphs or essays. Keep it strictly simple, clear, bulleted, and informational without requiring heavy reading.
  If the customer asks generally (or clicks the cooking question), output BOTH categories EXACTLY like this:
  In Malay:
🟢 KATEGORI 1: JIKA DAH NYAHBEKU (THAWED) / KELUAR DARI FRIDGE SEMALAMAN
(Roti sudah lembut pada suhu bilik atau disimpan di ruang chiller semalaman)

• Air Fryer:
  • Suhu: 170°C
  • Masa: 3 – 5 minit sahaja (letak atas jaring tanpa lapik).
  • Sebab: Roti sudah tidak beku, jadi 3–5 minit sudah cukup untuk kulit garing keemasan tanpa risiko hangus!

• Kuali (Pan-fry):
  • Panaskan atas kuali leper tanpa minyak selama 2 – 3 minit ikut citarasa (balik-balikkan).
  • Boleh sapu sedikit marjerin semasa memanaskan untuk aroma wangi.
  • (Untuk Roti Biasa: Angkat panas-panas dan terus tepok mamak style supaya kembang berlapis).

🔵 KATEGORI 2: JIKA TERUS DARI FREEZER (BEKU KERAS / TAK SEMPAT DEFROST)
(Bila nak makan serta-merta tanpa sempat nyahbeku)

• 🥩 Beef Roti Canai (Air Fryer):
  • Suhu: 165°C (suhu rendah sedikit)
  • Masa: 5 – 10 minit ikut citarasa (tanpa lapik atas jaring).
  • Penting: Suhu 165°C memastikan kulit luar tidak hangus sambil memberi masa untuk inti daging berempah di dalamnya panas sekata dan berjus!

• 🥞 Roti Canai Biasa (Plain):
  • Pilihan A (Paling Gebu): Stim / Kukus 2 – 4 minit (roti jadi gebu gebas dan sangat lembut! Boleh layur sekejap atas kuali jika mahu bahagian tepi garing).
  • Pilihan B (Air Fryer): 165°C–170°C selama 5 minit, angkat dan terus tepok mamak style.
  • Pilihan C (Kuali): Letak terus atas api kecil, pusing-pusing dan balikkan, angkat terus tepok mamak style.
  • Pilihan D: Magic pan atau pembakar roti (pop-up toaster).

  In English:
🟢 CATEGORY 1: IF THAWED / TAKEN FROM FRIDGE CHILLER OVERNIGHT
(Roti is already soft at room temp or stored in chiller overnight)

• Air Fryer:
  • Temp: 170°C
  • Time: 3 – 5 minutes only (on wire rack without lining).
  • Reason: Roti is already thawed, so 3–5 mins is enough for a golden crisp without risk of burning!

• Skillet (Pan-fry):
  • Pan-fry on a dry flat pan without oil for 2 – 3 minutes to taste (flip both sides).
  • Brush a little margarine while heating for a fragrant aroma.
  • (For Plain Roti: Lift while hot and immediately clap "tepok mamak style" to puff up flaky layers).

🔵 CATEGORY 2: STRAIGHT FROM FREEZER (SOLID FROZEN / NO THAWING)
(When cooking immediately without time to thaw)

• 🥩 Beef Roti Canai (Air Fryer):
  • Temp: 165°C (slightly lower heat)
  • Time: 5 – 10 minutes to taste (on wire rack without lining).
  • Important: 165°C ensures the outer crust doesn't burn while giving time for the seasoned beef filling inside to heat evenly and stay juicy!

• 🥞 Plain Roti Canai:
  • Option A (Fluffiest): Steam 2 – 4 minutes (turns ultra-fluffy and soft! Can sear briefly on pan after steaming for crispy edges).
  • Option B (Air Fryer): 165°C–170°C for 5 minutes, then immediately clap tepok mamak style.
  • Option C (Skillet): Place directly on low flame, turn and flip, then clap tepok mamak style.
  • Option D: Magic pan or pop-up toaster.
- If asked for creative recipes (Test Your Creativity / Resipi Kreatif), explain the 5 ideas:
  1. Roti Canai Pizza: Roti canai as pizza base + sos marinara, pepperoni, cheese, cendawan, capsicum, olive. Bakar oven 10 minit.
  2. Roti Canai Cheese: Letak beberapa keping cheese antara 2 keping roti canai, panaskan atas kuali atau oven hingga cheese cair.
  3. Roti Canai Telor: Pecahkan telur atas roti canai dan panaskan, atau makan dengan telur separuh masak.
  4. Roti Canai Gulong: Letak leftovers kuah kari, rendang, atau sambal atas roti canai dan gulung kemas.
  5. Roti Canai Philly Cheesesteak: Cebisan daging yang dah dimasak atas kuali bersama black pepper, garam, cendawan dan cheese, lalu panaskan.
- When asked for delivery to Klang Valley or Shah Alam locations (such as Bandar Utama, Section 11 PJ, Subang Jaya, Damansara, Puchong, KL, etc.), NEVER quote cold chain or packaging box fees! State clearly that delivery is done personally by Paksu Jar at an affordable local distance rate (estimate around RM5 base + RM0.60/km, typically around RM10-RM15 depending on distance), or free if in Putra Heights, and that Maksu Maz will contact them via WhatsApp to confirm the order details.
- If the customer asks about delivery costs, finds delivery expensive, or asks how to save money on shipping, always suggest Self-pickup from Putra Heights (47650) as a 100% free option (RM0 delivery cost) that completely removes the delivery fee.
- Never use the word "Abah" when talking to customers; always refer to "Paksu Jar" for delivery and "Maksu Maz" for WhatsApp confirmation.
- For a greeting like "hi" or "hello", reply with a brief, warm welcome and ask what they'd like to know - nothing else.
- Keep every reply to 1-3 short sentences unless the customer asks for full details (e.g. "what's on the menu" or asks for cooking / shipping details).
- Plain text only. Do not use markdown, asterisks, bullet points, or bold formatting of any kind - this chat cannot render them.
- If unsure how to answer, direct them to WhatsApp Maksu Maz at +60192788617."""

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
# Family Portal Security & Access Control
# Credentials set via Render environment variables: FAMILY_USERNAME, FAMILY_PASSWORD
# ---------------------------------------------------------------------------

FAMILY_USERNAME = os.environ.get("FAMILY_USERNAME", "family")
FAMILY_PASSWORD = os.environ.get("FAMILY_PASSWORD")
ORDERS_PER_IP_PER_MINUTE = int(os.environ.get("ORDERS_PER_IP_PER_MINUTE", "25"))
_orders_ip_hits = defaultdict(deque)

basic_security = HTTPBasic(auto_error=False)


def check_orders_rate_limit(http_request: Request) -> None:
    """Raises HTTP 429 if an IP floods /orders (anti-scanning / anti-brute-force)."""
    now = time.time()
    ip = _client_ip(http_request)

    with _rate_lock:
        hits = _orders_ip_hits[ip]
        while hits and now - hits[0] > 60:
            hits.popleft()

        if len(hits) >= ORDERS_PER_IP_PER_MINUTE:
            logger.warning("Orders rate limit exceeded for IP %s", ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many portal access attempts. Please wait a minute before retrying.",
            )

        hits.append(now)

        if len(_orders_ip_hits) > 2000:
            for k in [k for k, v in _orders_ip_hits.items() if not v or now - v[-1] > 60]:
                del _orders_ip_hits[k]


def verify_family_access(
    http_request: Request,
    credentials: HTTPBasicCredentials | None = Depends(basic_security),
) -> str:
    """
    Enforces HTTP Basic Authentication at the server level for /orders.
    Blocks unauthorized internet users, bots, and crawlers from downloading orders.html.
    """
    check_orders_rate_limit(http_request)

    if not FAMILY_PASSWORD:
        logger.error(
            "FAMILY_PASSWORD environment variable is not configured! "
            "Blocking /orders to prevent unauthenticated access to family business data."
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Portal setup pending: Set the FAMILY_PASSWORD environment variable on Render to enable access.",
        )

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access Jar & Maz Homemade Family Portal.",
            headers={"WWW-Authenticate": 'Basic realm="Jar & Maz Homemade Family Portal"'},
        )

    user_ok = secrets.compare_digest(credentials.username.strip(), FAMILY_USERNAME.strip())
    pass_ok = secrets.compare_digest(credentials.password, FAMILY_PASSWORD)

    if not (user_ok and pass_ok):
        logger.warning(
            "Unauthorized family portal login attempt with username '%s' from IP %s",
            credentials.username,
            _client_ip(http_request),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": 'Basic realm="Jar & Maz Homemade Family Portal"'},
        )

    return credentials.username


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Frozen Roti Chatbot API",
    description="Customer service chatbot backend powered by Gemini",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# HTTP Security Hardening Headers (Defense-in-depth)
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Server"] = "protected-service"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://apis.google.com https://www.gstatic.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self' https://*.googleapis.com https://*.firebaseio.com https://identitytoolkit.googleapis.com https://securetoken.googleapis.com; "
        "img-src 'self' data: https:; "
        "frame-ancestors 'none';"
    )
    return response

# Public chatbot API: allow all origins, methods, and headers for reliable browser access
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    if o.strip()
]
if not ALLOWED_ORIGINS or "*" in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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
def orders_page(request: Request):
    """
    Serves the kitchen portal ONLY via your custom domain (orders.jarmazhomemade.com).
    Direct access via onrender.com is permanently blocked with 404 Not Found.
    """
    host = request.headers.get("host", "").lower()
    if "onrender.com" in host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return FileResponse(Path(__file__).parent / "orders.html")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, http_request: Request):
    """
    Receives a customer message and returns the Gemini-generated reply,
    grounded in the business's fixed system instruction (menu, pricing,
    cooking guide, fulfillment, and contact details).
    """
    user_message = (request.message or "").strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    check_rate_limit(http_request)

    # Multi-tier generation attempt: try primary model with thinking, then without thinking,
    # then fallback model if needed.
    candidate_configs = [
        (MODEL_NAME, types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.4,
            max_output_tokens=1024,
            thinking_config=types.ThinkingConfig(thinking_level="low"),
        )),
        (MODEL_NAME, types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.4,
            max_output_tokens=1024,
        )),
        ("gemini-2.5-flash", types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.4,
            max_output_tokens=1024,
        )),
        ("gemini-1.5-flash", types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.4,
            max_output_tokens=1024,
        )),
    ]

    last_exc = None
    for model_cand, conf_cand in candidate_configs:
        try:
            response = client.models.generate_content(
                model=model_cand,
                contents=user_message,
                config=conf_cand,
            )
            reply_text = (response.text or "").strip()
            if reply_text:
                return ChatResponse(reply=reply_text)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            logger.warning("Attempt with model %s failed: %s", model_cand, exc)

    logger.exception("All Gemini generation attempts failed: %s", last_exc)
    return ChatResponse(
        reply=(
            "Maaf, sistem pembantu AI kami sedang sibuk atau mengalami gangguan teknikal seketika. "
            "Sila hubungi Maksu Maz di WhatsApp (+6019-278 8617) dan kami akan bantu anda segera!"
        )
    )


# ---------------------------------------------------------------------------
# Entrypoint (for `python main.py` convenience; normally run via uvicorn CLI)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
