# Jar & Maz Homemade: project guide for AI assistants (and humans)

Read this file first (any AI tool: ChatGPT/Codex, Claude, Gemini, Cursor, Copilot). It explains the whole project so you don't need to open the large HTML files to understand it. Two more detailed guides:
- `docs/index-html.md` explains the storefront page, section by section.
- `README.md` is the human-facing overview and setup guide.

## What this is

**Jar & Maz Homemade** (also "Dapur Paksu Jar & Maksu Maz", "Frozen Roti Canai by Paksu Jar") is a family business in **Putra Heights 47650, Subang Jaya, Selangor, Malaysia**. It sells handmade frozen roti canai and cookies. Adam, the son and a university student, built and maintains the website.

- Live site: https://jarmazhomemade.com (Cloudflare Pages)
- Orders are **not paid online**. Checkout builds a WhatsApp message to Maksu Maz (+60 19-278 8617). She confirms, takes payment and arranges delivery by hand.
- Paksu Jar does local deliveries in person. Maksu Maz handles WhatsApp.
- Never use the word "Abah" in customer-facing text. It's an internal family term.

## Business facts (single source of truth: keep every file consistent with this)

| Product | Price | Pack | Weight used for shipping |
| --- | --- | --- | --- |
| Frozen Roti Canai (Signature / Plain) | RM8 | 5 pcs | 0.53 kg |
| Frozen Beef Roti Canai | RM14 | 2 pcs | 0.30 kg |
| Family Freezer Bundle | RM99 (RM100 value) | 6 beef + 2 plain packs | 2.86 kg |
| Chocolate Chip Cookies (Golden Churn butter, Beryl's chips, almonds, walnuts) | RM38 | 33–36 pcs/jar, nett ~200–210 g, gross 263–275 g, jar Ø9 × H10.5 cm | 0.275 kg |
| Wedding/Event Doorgift Cookies | quote via WhatsApp | min 100 mini jars | 0.15 kg |

**Delivery rules** (decided by Adam on 2026-10-22):
1. **Self-pickup** in Putra Heights is free. The full house address is only sent after payment.
2. **Putra Heights (47650)**, or any address within 3.5 km by road, gets free doorstep delivery.
3. **Klang Valley / Shah Alam**: Paksu Jar delivers in a cooler box for **RM5 + RM0.50/km**. This is the standard rate. Never quote cold chain for Klang Valley.
   - The customer can choose GrabExpress instead (they pay the actual Grab fare, and Maksu Maz sends a screenshot).
   - Or they can book their own Grab/Lalamove runner.
4. **Outstation** (non-KV postcode, or more than 45 km by road) uses **Ninja Van**:
   - Cold Chain for frozen items: RM20 for the first kg, then +RM2/kg, max 30 kg.
   - Standard for cookies only: RM6.50 for the first kg, then +RM0.80/kg.
   - Add 6% SST to either rate. A mixed cart ships as 2 parcels.

If a price or rule changes, update **all** of these places:
- `index.html`: the `P` product array, the `RATE` constant, `calcNinjaVan`, the `L.en`/`L.ms` translation strings and `getLocalAnswer`.
- `functions/api/chat.js`: `SYSTEM_INSTRUCTION` and `getQuickAnswer`.
- `backend/main.py`: `SYSTEM_INSTRUCTION`.
- `orders.html`: `PRICES` / `itemPrices`.
- The Drive-only `mcp_server/mcp_server.py`, if it is still in use.

## Repository layout

Cloudflare Pages serves the **repo root as-is** (no build step). Every file in the repo is publicly downloadable, so never commit secrets.

```
index.html            Customer storefront: menu, cart, delivery estimator, WhatsApp checkout,
                      cooking guide, chat widget, EN/BM language toggle. See docs/index-html.md
orders.html           Family kitchen portal (Firebase Auth + Firestore): order entry, kanban
                      (new → packed → done), calendar, stats, inventory. noindex.
feedback.html         Customer reviews + family story page
functions/api/chat.js Cloudflare Pages Function → POST /api/chat → Google Gemini
                      (env var GEMINI_API_KEY in Cloudflare dashboard)
assets/               Images, favicons, enhance.js/css (scroll/motion polish layer for index.html)
robots.txt, sitemap.xml, favicon.ico
backend/              Older FastAPI alternative (Render): /chat with rate limits, /orders behind
                      HTTP Basic auth. Serves its own copy of orders.html, so keep it in sync
                      with the root orders.html. firestore.rules lives here too.
archive/              Files no longer used by the site. Kept for reference only; see archive/README.md
docs/                 Detailed docs for AI/humans
AGENTS.md             This file (AI/project guide). CLAUDE.md just imports it
```

### Things that live in Adam's Google Drive (`G:\My Drive\RotiCanai_ChatBot`) but NOT in GitHub
- `mcp_server/`: a Python MCP server so ChatGPT or Claude can query the menu, delivery quotes and cooking guide. It still uses RM0.60/km, so update it if it's revived.
- `social_agent/`: a Python bot that writes and publishes Threads/Instagram posts through the Meta Graph API, using `.env` tokens.
- `posters/`, `poster.html`: printable marketing flyers (HTML/PNG/PDF).
- `tools/`: one-off image recovery scripts and scratch files.
- `.env`: real secrets. **Never upload it.**

These aren't needed by the website. If they are ever added to GitHub, put them where Cloudflare won't serve them publicly, or move the site into its own folder first.

## How the pieces talk to each other

```
Customer browser ──index.html──► /api/chat (functions/api/chat.js) ──► Gemini API
        │                              └─ falls back to getQuickAnswer() canned replies
        ├─► nominatim.openstreetmap.org (geocode address) ─► router.project-osrm.org (road km)
        ├─► Leaflet + OSM tiles (map pin, loaded on demand)
        └─► wa.me/60192788617?text=... (checkout = WhatsApp message)

Family ──orders.html──► Firebase Auth (email/password) ──► Firestore: orders, inventory_logs
```

- **Firebase project:** `roti-canai-project`. The web config in `orders.html` is public by design; security comes from Firestore rules (`backend/firestore.rules`).
  - Status as of 2026-10-22: the repo version allows only `roticanai@gmail.com`, but it is **not yet published** in the Firebase console. Adam put that on hold.
  - The portal login auto-appends `@roticanai.com` when the username has no `@`.
- **Order documents** (`orders` collection):
  - Customer: `customerName`, `phone`, `source`, `fulfilment` (`pickup`/`delivery`), `address`, `notes`.
  - Items and money: `items[]`, `itemSubtotal`, `discount`, `discountNote`, `deliveryCost`, `total`.
  - Payment: `paymentStatus`, `paidAt`.
  - Timing: `orderDate`, `pickupTime`, `createdAt`.
  - Status: `status` goes `new` → `packed` → `done`, with timestamps `packedAt` and `doneAt`.
  - The portal loads the latest 500 orders with `.limit(500)`.

## Working conventions

- **GitHub is the source of truth.** The Drive folder held an older copy of the site (as of 2026-10-22). Edit in the repo or pull from it first. Uploading old Drive files through GitHub's web UI overwrites newer work.
- **Branch previews:** pushing a branch triggers a Cloudflare preview at `https://<branch>.jarmazhomemade.pages.dev`. Previews have **no `GEMINI_API_KEY`**, so the chatbot answers "setup in progress" there. Test chat logic locally with a mocked `fetch`.
- **No build tooling.** The pages are hand-written HTML with inline CSS/JS, and some lines are 10k+ characters. Use targeted search-and-replace edits and keep the existing minified style in `index.html`.
- **Line endings:** `orders.html`, `backend/*.py` and the HTML files use **CRLF**. Edit in binary-safe mode, or a whole file will show as changed.
- **Bilingual:** every customer-facing string exists in English and Bahasa Malaysia. `L.en` / `L.ms` in index.html, and both languages in the chatbot quick answers.
- The chatbot prompt must keep its rules: answer only what was asked, no markdown asterisks or bold, use Paksu Jar / Maksu Maz names, and suggest free self-pickup when someone thinks delivery costs too much.

## Known open items (2026-10-22)
- Publish the Firestore rules, and add more family accounts later. On hold by Adam.
- `/api/chat` has no rate limit. A Cloudflare dashboard rate-limiting rule is recommended.
- `orders.html` only reads the latest 500 orders, so stats will undercount once there are more.
- Is the Render FastAPI backend still used, and is `orders.jarmazhomemade.com` live? Unconfirmed, so `backend/` is kept.
