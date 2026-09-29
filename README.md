# 🥟 Jar & Maz Homemade (Dapur Paksu Jar & Maksu Maz)

Official web storefront, order management dashboard, and AI customer service assistant for **Jar & Maz Homemade** — a family-run artisanal frozen roti canai and bakery kitchen based in Putra Heights (47650), Subang Jaya, Malaysia.

🌐 **Production Website:** [jarmazhomemade.com](https://jarmazhomemade.com)

---

## 📌 Project Overview

This repository powers the complete digital operations of **Jar & Maz Homemade**:
1. **Interactive Customer Storefront (`index.html`)**: Menu browsing, shopping cart, smart delivery fee estimator, interactive cooking guide, and bilingual Malay/English support.
2. **Serverless AI Assistant (`functions/api/chat.js`)**: An edge-deployed AI customer service assistant ("Roti Helper AI") powered by Google Gemini, equipped with business rules, cooking instructions, pricing, and delivery logic.
3. **Kitchen & Orders Portal (`orders.html`)**: Real-time order tracker and fulfillment dashboard for the family kitchen, synchronized via Firebase Realtime Database.
4. **Customer Reviews & Testimonials (`feedback.html`)**: Story and customer feedback portal.
5. **Alternative Python Backend (`deploy/backend/main.py`)**: A production-ready FastAPI backend with Google GenAI SDK, rate limiting, and HTTP Basic Authentication (designed for Render/VPS deployments).

---

## 🚀 Key Features

### 🛒 1. Customer Storefront (`index.html`)
- **Product Catalog & Cart**: Handcrafted Signature Frozen Plain Roti Canai (RM8), Frozen Beef Roti Canai (RM14), Family Combo Bundles (RM99), and Golden Churn Butter Chocolate Chip Cookies (RM38).
- **Multi-Option Delivery Calculator**:
  - **Putra Heights (47650)**: 100% Free doorstep delivery by Paksu Jar.
  - **Klang Valley & Shah Alam**: Local personal delivery in thermal cooler boxes calculated by distance (base RM5.00 + RM0.60/km).
  - **GrabExpress**: Live app rate with zero markup (WhatsApp receipt verification).
  - **Self-Pickup**: Free collection at Putra Heights (47650).
  - **Peninsular Outstation**: Ninja Van Cold Chain frozen delivery with SST calculation.
- **WhatsApp Checkout Automation**: Formats complete itemized orders and sends them directly to Maksu Maz's WhatsApp (`+6019-278 8617`) for instant confirmation.
- **Interactive Cooking & Preparation Guide**:
  - Step-by-step instructions for Thawed/Chilled vs. Direct-from-Freezer cooking.
  - Specific parameters for Air Fryer, Pan-fry (with Mamak-style clap), Steaming, and Magic Pan.
  - Paksu's 5 Creative Recipes: Roti Pizza, Cheese Roti, Egg Roti, Curry Roll, and Philly Cheesesteak Roti.

### 🤖 2. Roti Helper AI Chatbot (`/api/chat`)
- **Serverless Edge Execution**: Runs on Cloudflare Pages Functions with 0ms cold-start latency.
- **Model Redundancy**: Multi-tier cascade through active Google Gemini models:
  - `gemini-3.6-flash`
  - `gemini-3.8-flash`
  - `gemini-3.7-flash`
  - `gemini-3.5-flash`
  - `gemini-2.5-pro`
- **Instant Client-Side Fallback Engine**: If the Gemini API is temporarily offline, rate-limited, or unreachable, the frontend automatically intercepts queries and answers FAQs (pricing, cooking, delivery, recipes) locally without dead ends.

### 📋 3. Kitchen & Order Dashboard (`orders.html`)
- **Live Firebase Integration**: Automatically tracks customer orders and status updates in real-time.
- **Order Lifecycle Management**: Order entry, status toggles (Pending, Preparing, Out for Delivery, Completed), and live metrics.
- **Receipt Printing & Export**: Single-click receipt formatting for kitchen packing and logistics.
- **Theme & Offline Support**: Adaptive Light/Dark mode with offline local storage cache.

---

## 📁 Repository Structure

```text
roti_canai_project/
├── index.html                  # Main customer-facing storefront and chat interface
├── orders.html                 # Family kitchen orders and management portal
├── feedback.html               # Customer review and brand story page
├── favicon.ico / favicon.png   # Website branding favicons
├── functions/                  # Cloudflare Pages Functions (Edge API)
│   └── api/
│       └── chat.js             # Serverless Gemini AI chatbot endpoint (POST /api/chat)
├── assets/                     # Media and static assets
│   ├── logo.jpg                # Jar & Maz brand logo
│   ├── roti_canai.jpg          # Signature Plain Roti Canai image
│   ├── roti_beef.jpg           # Beef Roti Canai image
│   ├── cookies.jpg / .png      # Golden Churn Cookies imagery
│   ├── doorgift.jpg / .png     # Wedding doorgift samples
│   ├── bundle_hero.png         # Family bundle promotional graphic
│   └── qr_code.svg             # Quick-access QR code
└── deploy/                     # Backend deployment configurations
    ├── backend/
    │   ├── main.py             # FastAPI backend (alternative to Cloudflare Functions)
    │   ├── requirements.txt    # Python dependencies (fastapi, uvicorn, google-genai)
    │   ├── Procfile            # Render / Railway startup command
    │   ├── .env.example        # Environment variable templates
    │   └── orders.html         # Protected portal file for Python backend
    └── functions/
        └── api/
            └── chat.js         # Deployment mirror for edge functions
```

---

## ⚙️ Configuration & Environment Variables

### Cloudflare Pages Deployment (Recommended / Current)

Set the following in your **Cloudflare Dashboard > Pages > Settings > Environment Variables**:

| Variable | Description | Required |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Google AI Studio Gemini API Key | **Yes** (for AI chatbot) |

### Alternative FastAPI Deployment (`deploy/backend`)

If hosting the backend on Render, Railway, or VPS:

```bash
# Copy template
cp deploy/backend/.env.example deploy/backend/.env
```

| Variable | Description | Default |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Google Gemini API Key | Required |
| `FAMILY_USERNAME` | HTTP Basic Auth username for `/orders` | `family` |
| `FAMILY_PASSWORD` | Strong password protecting kitchen portal | Required |
| `CHAT_PER_IP_PER_MINUTE` | Rate limit per client IP per minute | `6` |
| `CHAT_GLOBAL_PER_DAY` | Hard global quota limit per day | `500` |
| `ALLOWED_ORIGINS` | Permitted CORS origins | `*` |

---

## 💻 Local Development

### Option A: Static Frontend Preview
You can run any local HTTP server from the project directory:

```bash
# Using Python
python -m http.server 8080

# Using Node.js npx
npx serve .
```
Open [http://localhost:8080](http://localhost:8080) in your browser.

### Option B: Full Edge Simulation (with Cloudflare Functions)
To test the `/api/chat` function locally using Cloudflare Wrangler:

```bash
# Run Wrangler Pages dev with your Gemini API Key
npx wrangler pages dev . --binding GEMINI_API_KEY="your_api_key_here"
```

### Option C: Python FastAPI Backend
If developing or testing the Python backend:

```bash
cd deploy/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
export GEMINI_API_KEY="your_api_key_here"
uvicorn main:app --reload --port 8000
```

---

## 📦 Deployment Instructions

### Deploying to Cloudflare Pages (Production)
1. Push this repository to **GitHub**.
2. Log in to the [Cloudflare Dashboard](https://dash.cloudflare.com) and navigate to **Workers & Pages** > **Create application** > **Pages** > **Connect to Git**.
3. Select your repository:
   - **Framework preset**: `None`
   - **Build command**: *(leave blank)*
   - **Build output directory**: `/` (root directory containing `index.html`)
4. Add the `GEMINI_API_KEY` variable under **Environment variables**.
5. Click **Save and Deploy**. Cloudflare automatically serves the static assets and routes `/api/chat` to `functions/api/chat.js`.

---

## 📞 Business & Contact Information

- **Kitchen**: Dapur Paksu Jar & Maksu Maz (Jar & Maz Homemade)
- **Base Location**: Putra Heights (47650), Subang Jaya, Selangor, Malaysia
- **WhatsApp Inquiries & Orders**: Maksu Maz (`+6019-278 8617`)
- **Facebook**: [facebook.com/FrozenRotiCanaiByPaksu](https://facebook.com/FrozenRotiCanaiByPaksu)
