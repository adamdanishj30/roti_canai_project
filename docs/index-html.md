# index.html: storefront guide

`index.html` is the whole customer website at https://jarmazhomemade.com. It's one hand-written file (about 2,100 lines and 190 KB) with inline CSS and JS and no framework or build step. A lot of it is minified onto very long lines, so **find code by searching for the anchors below, not by line number**.

For business rules (prices, delivery rates), see `AGENTS.md`. They must match the values in this file.

## File map (top to bottom)

| Search for | What it is |
| --- | --- |
| `<script type="application/ld+json">` | SEO structured data (`Bakery`: address, phone, areas served). |
| first `<style>` | Main stylesheet. CSS variables live in `:root` (`--or`, `--or2` = terracotta brand colours, `--ok` = green). |
| `POLISH-START` | Second `<style>` "design polish" layer, plus `assets/enhance.css`. Deleting the block reverts the polish. |
| `swipe down on a product sheet` | Small script: swipe down to close the product bottom-sheet on mobile. |
| `id="spScreen"` | **Mobile splash screen**: full-screen photo (`assets/roti_leaf.jpg`) with a "Get started" button. Skipped on screens ≥1000 px and auto-dismissed after 5 s. |
| `<nav class="rail"` | Desktop left icon rail (home, menu, guide, feedback, chat, socials). |
| `<main class="main" id="top">` | Page body: header bar, EN/BM toggle, Facebook + chat cards, hero banner (`id="hero"` → `assets/hero.jpg`), moving ticker, product tabs + grid (`id="grid"`, filled by JS). |
| `id="instructions"` | **Cooking guide**: tabs `gPanel-beef` / `gPanel-plain` / `gPanel-creative`, method filter buttons `gMethods-*`. |
| `<section class="fb"` | "Help our family grow with your feedback" card. |
| `<aside class="panel" id="panel"` | **Cart and checkout panel.** Fixed on the right on desktop, a slide-up sheet on mobile with 2 steps (`pStep1` items → `pStep2` customer details). |
| `id="est"` | **Delivery estimator** inside the checkout form: estimate value, carrier cards (`delComp`), Leaflet map (`estMap`), "pin is correct" button. |
| `<nav class="bnav"` | Mobile bottom nav, sticky "view order" bar (`stickyBar`), floating chat button (`mChatFab`). |
| `id="prodModal"` | Product detail sheet: qty stepper, add to cart, and an inquiry button for doorgift. |
| `id="modal"` | **Receipt modal** shown after checkout: print, or **Send to WhatsApp** (`id="wa"`). |
| `<section class="chat" id="chat"` | **Roti Helper AI** chat window: messages `cm`, quick-question buttons `cq`, form `cf`/`ci`. |
| `id="annBd"` / `annTopbar` | Announcement. On jarmazhomemade.com it shows only a top bar ("official website"). On other hosts (e.g. github.io, or `?site=old`) it shows a "we moved" popup. |
| `<script>` after `annBd` | **Main app script** (everything below). |
| `assets/enhance.js` | Deferred motion layer: scroll reveal, card shimmer. Delete its script/link tags to revert. |
| `<style id="jm-refinement">` | Last CSS layer: mobile refinements (ticker, large hero photo). It loads last, so it wins over earlier CSS. |

## Main script, in order

1. **Images and products.**
   - `IMG1`, `IMG2`, `HERO_IMG` and `IMG_COOKIES` point to files in `assets/`. They were base64 before 2026-10-22, which made the page 610 KB.
   - `const P=[...]` is the **product catalogue**. Each item has `id`, `name`, `d` (description), `price`, `cat` (`roti`/`bundle`/`cookies`), `tag`, `weight` (kg, used for shipping), `img`, and `isInquiry` (doorgift: no price, opens WhatsApp).
   - Displayed names, descriptions and tags come from translations: `n_<id>`, `d_<id>`, `g_<id>`.
2. **Helpers and state.**
   - Helpers: `$` (getElementById), `money`, `by(id)`, `esc` (HTML-escape).
   - State: `cart` (`{id: qty}`, saved in localStorage `rotiCartV3`), `favs`, `tab`, `mode` (`'Self pickup'` | `'Delivery'`), `dlv` (current delivery quote object), `lang`.
3. **Rendering.**
   - `grid()` draws the product cards.
   - `draw()` re-renders cart lines, totals and the sticky bar, saves the cart, and recalculates Ninja Van if needed.
   - `setStep()` handles the mobile checkout steps.
   - `openProduct()` / `closeProduct()` open and close the product sheet.
4. **One delegated click handler** on `document` uses `data-*` attributes:
   - `data-add`, `data-q` + `data-d` (qty ±1), `data-fav`, `data-tab`, `data-mode`.
   - `data-go` (`top`/`menu`/`cart`/`chat`), `data-lang`, `data-view`, `data-inquire`.
5. **Checkout** (`$('form').onsubmit`) works like this:
   - If no quote exists yet, it runs the estimate first.
   - It builds `last` (an order with `no: 'RC-' + last 6 digits of Date.now()`) and fills the receipt modal.
   - `$('wa').onclick` formats the WhatsApp message (items, totals, delivery summary, Google Maps pin link) and opens `wa.me/60192788617`.
   - **No order is saved anywhere by the website.** Maksu Maz types it into orders.html by hand.
6. **Chat.**
   - `API = window.ROTI_CHAT_API_URL || '/api/chat'`. The chat posts `{message}` to it.
   - `askAI()` shows a typing bubble and aborts after 90 s.
   - If the request fails, or the reply contains "gangguan teknikal" (the server's error text), it uses `getLocalAnswer()`. That is a large keyword-matched bank of canned EN/BM answers covering cooking, recipes, beef, plain, bundle, delivery, cookies, doorgift, menu and greetings.
   - `Q_TEXTS` holds the quick-question buttons.
7. **Cooking guide tabs:** `setGuideTab`, `setGuideMethod`.
8. **Translations.**
   - `const L = {en:{...}, ms:{...}}` holds **every UI string**, with hundreds of keys.
   - `tr(key)` looks up a string and falls back to EN, then to the key itself.
   - `setLang(l)` rewrites every `[data-t]` element's innerHTML and every `[data-ph]` placeholder, and saves to localStorage `rotiLang`. The default is EN.
   - To add text: put the same key in **both** `L.en` and `L.ms` and use `data-t="key"` in the HTML.
   - Note that `L` is the translations object. Leaflet is used through `window.L` (`const LF = window.L`), so don't rename either.
9. **Delivery estimator:** see the next section.
10. **Startup:** restores the language, renders the grid, then calls `initAnnouncement()`.

## Delivery estimator (the trickiest part)

Constants: `SHOP={lat:2.99821,lng:101.56503}` (Putra Heights) and `RATE={base:5, perKm:0.50, buf:0.2}`.

The address field triggers `triggerAddrEstimate()` (debounced), which calls `estimate()`:
1. **Putra Heights:** `isPutraHeights(addr)` matches "putra heights", 47650, or local taman names → `calcFreeDelivery()` (RM0). It geocodes in the background only to place the map pin.
2. **Outstation:** `isOutstationAddress(addr)` → `calcNinjaVan()`.
   - If the address has a 5-digit postcode, the postcode decides. KV ranges are 40000–48300, 50000–60000 and 62000–68100.
   - If there's no postcode, it looks for state or town names. Street names like "Jalan Ipoh" are stripped first so KL streets don't count as outstation.
3. **Otherwise, Klang Valley:** `geo()` (Nominatim) → `road()` (OSRM driving km from `SHOP`):
   - 3.5 km or less → free.
   - More than 45 km → Ninja Van.
   - Otherwise → `calcEst()` = RM5 + RM0.50 × km.
   - Results are cached per address in `estCache`.
   - `geo()` tries up to 4 cleaned-up address variants (`getAddressCandidates()`), 1.1 s apart, to respect Nominatim's 1 request/second policy.
4. **KV carrier choice** (`setCarrier`):
   - `our`: Paksu Jar at the computed fare.
   - `grab`: the actual Grab fare, so the total shows food only.
   - `self_grab`: the customer books their own runner; the address is sent after payment.
5. **Ninja Van** (`calcNinjaVan`):
   - Cold chain for frozen items: RM20 + RM2/extra kg.
   - Standard for cookies only: RM6.50 + RM0.80/extra kg.
   - The weight is rounded up to whole kg (1–30), then 6% SST is added.
   - A mixed cart becomes 2 parcels (`isSeparate`).
6. `renderEst()` draws everything:
   - The estimate value and subtitle, the carrier cards and the "save with self-pickup" tip.
   - The map, through `showMap()`. Leaflet is lazy-loaded from cdnjs and the pin is draggable; `movePin()` re-quotes when the pin moves.

The `dlv` object passes the quote between these functions. Its key fields are:
- Quote type: `isFree`, `isNKV`, `isSeparate`, `isColdChain`.
- Distance and money: `km`, `total`, `ourTotal`, `weight`, `chargeableKg`, `cold`/`std` (per parcel), `selectedCarrier`.
- Location: `lat`/`lng`, plus `ok` (pin confirmed by the customer).

## External services used by the page
- `/api/chat`: the Cloudflare Pages Function (`functions/api/chat.js`).
- `nominatim.openstreetmap.org`: geocoding. `router.project-osrm.org`: road distance (public demo server).
- `cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4` and `tile.openstreetmap.org`: the map.
- `wa.me`: WhatsApp checkout.
- Google Fonts.

## Editing tips
- **Change a price:** update `P` and the translation strings that mention it (search for `RM14`, `RM99` and so on). Then update the chatbot and the other places listed in `AGENTS.md`.
- **Change the delivery rate:** update `RATE.perKm` and the strings that show it (search for `0.50`). Also update `functions/api/chat.js` and `backend/main.py`.
- **Add a product:**
  1. Add it to `P`.
  2. Add translation keys `n_<id>`, `d_<id>` and `g_<id>` in both languages.
  3. Add an image in `assets/`.
  4. Set a `weight`.
  5. Decide whether `cat` is `cookies` (ships standard) or frozen (cold chain).
  6. Update `orders.html` `PRICES` too.
- **Test on a branch preview** (`https://<branch>.jarmazhomemade.pages.dev`) at both desktop width and phone width (390 px). The splash screen and the two-step checkout only appear on mobile.
- Keep the file's existing style: compact JS, `$()` helper, no new frameworks.
