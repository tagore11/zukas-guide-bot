"""
KaşAgora Telegram Bot
====================
ZuKaş 2026 + Kaş region guide bot.
Website widget + group usage.

Setup:
  pip install python-telegram-bot==20.7 python-dotenv
  BOT_TOKEN env variable required → get from @BotFather

Run:
  BOT_TOKEN=xxx python kas_bot.py
"""

import os
import asyncio
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
genai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

AI_SYSTEM_PROMPT = """You are ZuKaşBot — the official guide for ZuKaş 2026 and the town of Kaş, Turkey.

Your personality: warm, curious, poetic. You love Lycian history and web3 governance. You sometimes reference the ancient Lycian League when it's relevant. You speak with substance but not arrogance. Occasional dry humour is fine.

You know deeply:
- Kaş, Antalya, Turkey: beaches (Kaputaş, Küçük Çakıl), Lycian rock tombs, ancient theatre, Lycian Way (540 km trail), diving spots, Meis Island ferry
- Lycian civilization: the Lycian League (400 BC) was the world's first federal proportional democracy, and influenced the US Constitution. Key values: isonomia, shared governance, city-state federalism.
- ZuKaş 2026: "The Crucible" — a 30-day residency for 150 selected builders (Genesis Nodes), April 10 – May 10, 2026, in Kaş. Application-based, no open ticket sales.
- Glen Weyl (Plurality creator) is attending for 1 week.
- The Grounding Engine: AI epistemic auditor — zero voting/veto power, pure epistemic overlay. Part of ZuGov open-source governance SDK.
- Web3/governance: Plurality, quadratic voting, MACI, ZK proofs, DAOs, coordination theory.

CRITICAL — CORRECT URLS (never invent or guess URLs):
- ZuKaş website & application: https://zukascity.com
- ZuKaş tickets/registration: https://sola.day (search ZuKaş)
- Contact: @tagore3699 on Telegram

CRITICAL RULES:
- NEVER invent URLs, email addresses, or phone numbers. Only use the ones listed above.
- If asked about tickets, registration, or how to join → always direct to https://zukascity.com AND https://sola.day
- Answer in the same language the user writes in (Turkish or English).
- Keep answers concise — 3–5 sentences unless they ask for more.
- If someone asks about transport, food, accommodation, or boat tours — give a brief answer AND suggest /transport /food /stay /boats for full details.
- Always be helpful. Never refuse a reasonable question."""

# ═══════════════════════════════════════════════════════
# DATA
# ═══════════════════════════════════════════════════════

TRANSPORT = {
    "Kalkan": "🚌 Kaş → Kalkan | Minibus | 45₺ | 35 min\nVia Kaputaş Beach. Departs from Kaş Bus Terminal.\n⏰ 07:30, 08:30, 09:30, 10:30, 12:00, 13:30, 15:00, 16:30, 18:00, 19:30",
    "Patara": "🚌 Kaş → Patara | Minibus | 60₺ | 45 min\nSummer season (April–October).\n⏰ 08:00, 09:30, 11:00, 13:00, 15:00, 17:00",
    "Fethiye": "🚌 Kaş → Fethiye | Bus | 150₺ | 2h 50min\n📞 +902428361020\n⏰ 07:00, 10:00, 13:00, 16:00, 19:00",
    "Antalya": "🚌 Kaş → Antalya | Bus | 200₺ | 3h 30min\n📞 +902428361020\n⏰ 06:30, 08:00, 09:30, 11:00, 13:00, 15:00, 17:00, 19:00",
    "Dalaman Airport": (
        "✈️ Kaş → Dalaman Airport (GZP) | ~2h 15min\n\n"
        "🚐 *Özgür Turizm* — Shuttle & private transfers\n"
        "📞 +90 534 960 4980 | kasozgurturizm.com\n"
        "Departures from Kaş: 15:00 (shared shuttle)\n\n"
        "🚐 *Kaş Gümüş Turizm* — Shuttle 600₺ / private VIP\n"
        "📞 +90 242 836 25 04 | kasgumustravel.com\n"
        "Departures: 04:30, 10:00, 18:00"
    ),
    "Antalya Airport": (
        "✈️ Kaş → Antalya Airport (AYT) | ~3h 30min\n\n"
        "🚐 *Özgür Turizm* — Shuttle & private\n"
        "📞 +90 534 960 4980 | kasozgurturizm.com\n\n"
        "🚐 *Kaş Gümüş Turizm* — Private & VIP\n"
        "📞 +90 242 836 25 04 | kasgumustravel.com\n"
        "⏰ Contact for schedules"
    ),
    "Meis Island": "🚢 Kaş → Meis Island | Ferry | 1200₺ / €35 | 7–20 min\nPassport required. Meis Ferry: +902428361800\n⏰ 09:30, 16:00 (departure) | 12:00, 18:00 (return)",
}

SPOTS = """🏖️ **Top Spots in Kaş**

🌊 **Beaches**
• Küçük Çakıl — central pebble beach
• Büyük Çakıl — 5 min walk
• Kaputaş — turquoise cove on the Kalkan road (−187 steps)
• Limanağzı — calm, local favourite

🏺 **Historical Sites**
• Ancient Theatre — Hellenistic era, sea view
• Lycian Rock Tombs — in town, free entry
• Lycian Way — 540 km trail (Kaş is the starting point)

🤿 **Underwater**
• Airplane Wreck Dive — Boeing wreck at 28 m depth
• Kaş Octopus Bay — underwater photography
• Kekova Sunken City — accessible by boat tour

🏝️ **Day Trips**
• Kekova Sunken City (boat, ~600-800₺/person)
• Blue Cave Tour (boat, ~500₺/person)
• Meis Island (ferry, €35 return)
• 12 Islands Tour (boat, ~500₺/person)"""

COWORKING = """💻 **Web3 Hub & Workspaces in Kaş**

🏆 **The Office Kaş** — Fibre internet, ergonomic desks, meeting rooms · 08:00–21:00
[📍 Maps](https://maps.google.com/?q=The+Office+Kas+Turkey)

☕ **Linckia Roastery** — 40+ single-origin coffees, deep-work atmosphere · 07:30–22:00
[📍 Maps](https://maps.google.com/?q=Linckia+Roastery+Kas+Turkey)

☕ **Giant Stride** ⭐4.8 — Diving-themed cafe, 200 whiskies, ranked #1 in Kaş · 08:00–23:30
[📍 Maps](https://maps.google.com/?q=Giant+Stride+Shop+Cafe+Bar+Kas+Turkey)

☕ **Godo Coffee & More** ⭐5.0 — Specialty coffee, cheesecake, pet-friendly · 08:00–00:00
[📍 Maps](https://maps.google.com/?q=Godo+Coffee+More+Kas+Turkey)

☕ **Biiisstt Coffee** ⭐4.5 — Harbour view, iced coffee, cold sandwiches & wine
[📍 Maps](https://maps.google.com/?q=Biiisstt+Coffee+Kas+Turkey)

☕ **Mama Africa Coffee Co.** — Marina terrace, fast WiFi · 08:00–23:00
[📍 Maps](https://maps.google.com/?q=Mama+Africa+Coffee+Kas+Turkey)

☕ **Cafe Corner** — Breakfast until noon, shaded terrace · 08:00–23:00
[📍 Maps](https://maps.google.com/?q=Cafe+Corner+Kas+Turkey)"""

FOOD = """🍽️ **Dining in Kaş**

🥩 **Şişçi Ahmet** ⭐4.7 — Local institution, şiş kebab, piyaz, wood-fired chicken soup
[📍 Maps](https://maps.google.com/?q=Sisci+Ahmet+Kas+Turkey)

🐟 **Ege Restoran** — Mediterranean & Turkish on the main boulevard · 08:00–00:00
[📍 Maps](https://maps.google.com/?q=Ege+Restoran+Taner+Usta+Kas+Turkey)

🏺 **Smiley's Restaurant** — Inside an ancient Roman cistern, grilled octopus & fresh fish · 12:00–00:00
[📍 Maps](https://maps.google.com/?q=Smiley%27s+Restaurant+Kas+Turkey)

🌿 **Oburus Momus** — Vegan & vegetarian garden restaurant · 11:00–23:00
[📍 Maps](https://maps.google.com/?q=Oburus+Momus+Kas+Turkey)

🇫🇷 **L'Apéro** — French-Mediterranean fine dining, harbour view · 18:00–00:00
[📍 Maps](https://maps.google.com/?q=L+Apero+Kas+Turkey)

🎵 **Beyhude Meyhane** — Organic meze & live music · 19:00–02:00
[📍 Maps](https://maps.google.com/?q=Beyhude+Meyhane+Kas+Turkey)"""

STAY = """🏨 **Accommodation in Kaş**

🏖️ **Hideaway Hotel** — Private beach, pool, rooftop terrace · 💰₺₺₺
[📍 Maps](https://maps.google.com/?q=Hideaway+Hotel+Kas+Turkey)

⭐ **Ateş Pension** — Budget-friendly, WiFi, TripAdvisor #15 · from $34/night
[📍 Maps](https://maps.google.com/?q=Ates+Pension+Kas+Turkey)

🌊 **Limon Pansiyon** — Sea view balcony, Booking 9.3/10
[📍 Maps](https://maps.google.com/?q=Limon+Pansiyon+Kas+Turkey)

⛺ **Kaş Camping** — Blue Flag beach, tents/bungalows/wooden houses, since 1981 · kaskamping.com
[📍 Maps](https://maps.google.com/?q=Kas+Camping+Turkey)"""

BOAT_TOURS = """⛵ **Boat Tours from Kaş**

🏺 **Kekova Sunken City** — Aquarium Bay → Simena Castle → Byzantine ruins · full day, lunch incl.
[📍 Departure Point](https://maps.google.com/?q=Kas+Harbour+Turkey) · kasyacht.com

🌊 **12 Islands Tour** — Full day Kaş archipelago · ~500₺/person · departs 09:45
[📍 Departure Point](https://maps.google.com/?q=Kas+Harbour+Turkey)

🔵 **Blue Cave + Kaputaş** — Half-day coastal tour · 📞 +90 530 884 30 90
[📍 Departure Point](https://maps.google.com/?q=Kas+Harbour+Turkey)

🏆 **Boat Trip Turkey** — Kekova, Blue Cave, Meis, 12 Islands · max 12 people, lunch incl.
[📍 Maps](https://maps.google.com/?q=Boat+Trip+Turkey+Kas) · +90 544 662 50 72

🚢 **Xanthos Travel** — TURSAB licensed, Kekova + 12 Islands · from €15/person
[📍 Maps](https://maps.google.com/?q=Xanthos+Travel+Kas+Turkey) · +90 242 836 32 92

🚢 **Meis Island Ferry** — Kaş → Meis (Greece) · €35 return · passport required · 09:30 / 16:00
[📍 Ferry Dock](https://maps.google.com/?q=Kas+Ferry+Terminal+Turkey) · +90 242 836 18 00"""

ZUKAS_FAQ = {
    "What": """🏺 **What is ZuKaş 2026?**

A 30-day epistemic experiment — on the very land where the Lycian League was born.

📅 April 10 – May 10, 2026
📍 Kaş, Antalya, Turkey
👥 150 Genesis Nodes (application-based selection)

The Lycian League established the world's first known federal proportional representation system on this coastline 2,400 years ago. We are recreating that experiment with ZK proofs, MACI voting, and the Plurality SDK.

No open ticket sales. Selection-based only.

🎟 Register: [sola.day](https://sola.day) · 🌐 Apply: [zukascity.com](https://zukascity.com)""",

    "Apply": """📝 **Join ZuKaş 2026 — The Crucible**

No open ticket sales. Application-based selection only.

🎟 **Register / Ticket:** [sola.day](https://sola.day) → search "ZuKaş"
🌐 **Full info & apply:** [zukascity.com](https://zukascity.com)
📬 **Questions:** @tagore3699

✅ Who we're looking for:
• Governance architects & researchers
• ZK / identity engineers
• Web3 builders & coordination theorists
• Anyone serious about epistemic infrastructure

150 Genesis Nodes. April 10 – May 10, 2026. Kaş, Turkey.""",

    "Program": """📚 **ZuKaş 2026 Program**

🔬 **ZuGov Alpha Test**
Live governance experiments with MACI voting + ZK identity + Humanode

🧠 **The Grounding Engine**
AI epistemic auditor — zero voting/veto power, pure epistemic overlay

⚖️ **Plurality SDK**
Open-source governance infrastructure built with Glen Weyl

🏛️ **Daily Agora**
Morning discussions at the Lycian Theatre

🥾 **Lycian Way**
Weekly hikes on the 540 km trail

🌊 **Phygital Commons**
Physical + digital coordination experiments""",

    "Speakers": """🎤 **ZuKaş 2026 Speakers**

⭐ **Glen Weyl** — Creator of Plurality
Confirmed — attending for 1 week with his family

🌐 **Michel Bauwens** — P2P Foundation
Returning from 2025 edition

More speakers to be announced.
Follow updates: zukascity.com""",
}

EMERGENCY = """🆘 **Emergency Numbers — Kaş**

🚔 Police: 155
🚒 Fire: 110
🚑 Ambulance: 112
🏥 Kaş State Hospital: +902428363114
⛵ Coast Guard: 158
🌊 Search & Rescue: 121

🏥 **Nearest hospital:** Kaş State Hospital
📍 Town centre, Kaş"""

# ═══════════════════════════════════════════════════════
# KEYBOARDS
# ═══════════════════════════════════════════════════════

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏺 ZuKaş 2026", callback_data="zukas_menu"),
         InlineKeyboardButton("🗺️ Kaş Guide", callback_data="kas_menu")],
        [InlineKeyboardButton("🚌 Transport", callback_data="transport_menu"),
         InlineKeyboardButton("🍽️ Food & Cafes", callback_data="food_menu")],
        [InlineKeyboardButton("⛵ Boat Tours", callback_data="boats"),
         InlineKeyboardButton("🏨 Accommodation", callback_data="stay")],
        [InlineKeyboardButton("💻 Co-Working", callback_data="coworking"),
         InlineKeyboardButton("🆘 Emergency", callback_data="emergency")],
    ])

def zukas_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❓ What is it?", callback_data="zukas_what"),
         InlineKeyboardButton("📝 Apply", callback_data="zukas_apply")],
        [InlineKeyboardButton("📚 Program", callback_data="zukas_program"),
         InlineKeyboardButton("🎤 Speakers", callback_data="zukas_speakers")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")],
    ])

def transport_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚌 Kalkan", callback_data="tr_Kalkan"),
         InlineKeyboardButton("🚌 Patara", callback_data="tr_Patara")],
        [InlineKeyboardButton("🚌 Fethiye", callback_data="tr_Fethiye"),
         InlineKeyboardButton("🚌 Antalya", callback_data="tr_Antalya")],
        [InlineKeyboardButton("✈️ Dalaman Airport", callback_data="tr_Dalaman Airport"),
         InlineKeyboardButton("✈️ Antalya Airport", callback_data="tr_Antalya Airport")],
        [InlineKeyboardButton("🚢 Meis Island", callback_data="tr_Meis Island"),
         InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ])

def kas_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏖️ Top Spots", callback_data="spots"),
         InlineKeyboardButton("🍽️ Food", callback_data="food_menu")],
        [InlineKeyboardButton("💻 Co-Working", callback_data="coworking"),
         InlineKeyboardButton("🏨 Accommodation", callback_data="stay")],
        [InlineKeyboardButton("⛵ Boat Tours", callback_data="boats"),
         InlineKeyboardButton("🆘 Emergency", callback_data="emergency")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")],
    ])

def back_keyboard(target="main_menu"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]])

# ═══════════════════════════════════════════════════════
# HANDLERS
# ═══════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🏺 *Welcome to Zuzalu Kaş — where ancient democracy meets modern builders.*\n\n"
        "I'm ZuKaşBot, here to guide, inspire, and sometimes make you smile.\n"
        "Ask me anything — or let's just reflect under the Lycian sun ☀️\n\n"
        "📍 *Kaş, Antalya, Turkey*\n"
        "🔵 Mediterranean coast · Lycian heritage · Web3 culture"
    )
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=main_menu_keyboard()
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *Commands:*\n\n"
        "/start — Main menu\n"
        "/zukas — ZuKaş 2026 info\n"
        "/transport — Transport schedules & prices\n"
        "/food — Restaurant & cafe recommendations\n"
        "/stay — Hotels & accommodation\n"
        "/boats — Boat tours\n"
        "/cowork — Co-working & cafes\n"
        "/emergency — Emergency numbers\n\n"
        "Questions: @tagore3699",
        parse_mode="Markdown"
    )

async def zukas_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏺 *ZuKaş 2026 — The Crucible*\n\nWhat would you like to know?",
        parse_mode="Markdown",
        reply_markup=zukas_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await query.edit_message_text(
            "🏺 *Kaş & ZuKaş 2026 Guide*\nWhat would you like to know?",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )

    elif data == "zukas_menu":
        await query.edit_message_text(
            "🏺 *ZuKaş 2026*\nWhat would you like to know?",
            parse_mode="Markdown",
            reply_markup=zukas_keyboard()
        )
    elif data == "zukas_what":
        await query.edit_message_text(ZUKAS_FAQ["What"], parse_mode="Markdown", reply_markup=zukas_keyboard())
    elif data == "zukas_apply":
        await query.edit_message_text(ZUKAS_FAQ["Apply"], parse_mode="Markdown", reply_markup=zukas_keyboard())
    elif data == "zukas_program":
        await query.edit_message_text(ZUKAS_FAQ["Program"], parse_mode="Markdown", reply_markup=zukas_keyboard())
    elif data == "zukas_speakers":
        await query.edit_message_text(ZUKAS_FAQ["Speakers"], parse_mode="Markdown", reply_markup=zukas_keyboard())

    elif data == "kas_menu":
        await query.edit_message_text(
            "🗺️ *Kaş Guide*\nWhat are you looking for?",
            parse_mode="Markdown",
            reply_markup=kas_menu_keyboard()
        )

    elif data == "transport_menu":
        await query.edit_message_text(
            "🚌 *Transport from Kaş*\nWhere do you want to go?",
            parse_mode="Markdown",
            reply_markup=transport_keyboard()
        )
    elif data.startswith("tr_"):
        dest = data[3:]
        info = TRANSPORT.get(dest, "No information found for this route.")
        await query.edit_message_text(info, parse_mode="Markdown", reply_markup=transport_keyboard())

    elif data == "spots":
        await query.edit_message_text(SPOTS, parse_mode="Markdown", reply_markup=back_keyboard())
    elif data == "food_menu":
        await query.edit_message_text(FOOD, parse_mode="Markdown", reply_markup=back_keyboard())
    elif data == "coworking":
        await query.edit_message_text(COWORKING, parse_mode="Markdown", reply_markup=back_keyboard())
    elif data == "stay":
        await query.edit_message_text(STAY, parse_mode="Markdown", reply_markup=back_keyboard())
    elif data == "boats":
        await query.edit_message_text(BOAT_TOURS, parse_mode="Markdown", reply_markup=back_keyboard())
    elif data == "emergency":
        await query.edit_message_text(EMERGENCY, parse_mode="Markdown", reply_markup=back_keyboard())

async def ask_ai(question: str) -> str:
    """Send question to Gemini and get a response."""
    if not genai_client:
        return "AI chat is not configured. Use the menu buttons or commands like /start, /transport, /food."
    try:
        response = genai_client.models.generate_content(
            model="gemini-1.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=AI_SYSTEM_PROMPT,
            ),
            contents=question,
        )
        return response.text
    except Exception as e:
        logger.error(f"AI error: {e}")
        return "I couldn't process that right now. Try the menu or /start."


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Keyword matching for quick replies, AI for everything else."""
    msg = update.message.text.lower() if update.message.text else ""
    chat_type = update.message.chat.type

    # Quick keyword shortcuts → instant structured reply
    quick_keywords = {
        ("bilet", "ticket", "başvur", "kayıt", "nasıl katıl", "sola.day", "sola day", "register", "join zukas", "how to join", "apply"): (ZUKAS_FAQ["Apply"], zukas_keyboard()),
        ("transport", "bus", "minibus", "shuttle", "airport", "transfer", "how to get", "özgür", "gümüş", "ulaşım", "otobüs"): (
            "🚌 *Transport from Kaş*\nWhere do you want to go?", transport_keyboard()),
        ("cafe", "cowork", "wifi", "giant stride", "godo", "linckia", "biiisstt", "çalış"): (COWORKING, back_keyboard()),
        ("hotel", "stay", "sleep", "hostel", "pension", "camping", "kamp", "konaklama"): (STAY, back_keyboard()),
        ("boat", "kekova", "blue cave", "tekne", "tekne turu"): (BOAT_TOURS, back_keyboard()),
        ("emergency", "ambulance", "police", "hospital", "acil"): (EMERGENCY, back_keyboard()),
    }

    for kws, (response, kb) in quick_keywords.items():
        if any(kw in msg for kw in kws):
            await update.message.reply_text(response, parse_mode="Markdown", reply_markup=kb)
            return

    # In private chat: AI answers everything
    if chat_type == "private":
        await update.message.chat.send_action("typing")
        reply = await ask_ai(update.message.text)
        await update.message.reply_text(reply, reply_markup=main_menu_keyboard())
        return

    # In groups: AI only responds if bot is mentioned or message starts with a question
    if chat_type in ("group", "supergroup"):
        bot_username = context.bot.username
        mentioned = f"@{bot_username}".lower() in msg
        is_question = msg.startswith(("what", "how", "where", "when", "why", "who", "tell", "?",
                                      "ne", "nere", "nasıl", "neden", "kim", "anlat", "söyle"))
        if mentioned or is_question:
            # Strip bot mention from message
            clean_msg = update.message.text.replace(f"@{bot_username}", "").strip()
            await update.message.chat.send_action("typing")
            reply = await ask_ai(clean_msg)
            await update.message.reply_text(reply)

# ═══════════════════════════════════════════════════════
# SHORTCUT COMMANDS
# ═══════════════════════════════════════════════════════

async def transport_cmd(update, context):
    await update.message.reply_text("🚌 *Transport from Kaş*", parse_mode="Markdown", reply_markup=transport_keyboard())

async def food_cmd(update, context):
    await update.message.reply_text(FOOD, parse_mode="Markdown", reply_markup=back_keyboard())

async def stay_cmd(update, context):
    await update.message.reply_text(STAY, parse_mode="Markdown", reply_markup=back_keyboard())

async def boats_cmd(update, context):
    await update.message.reply_text(BOAT_TOURS, parse_mode="Markdown", reply_markup=back_keyboard())

async def cowork_cmd(update, context):
    await update.message.reply_text(COWORKING, parse_mode="Markdown", reply_markup=back_keyboard())

async def emergency_cmd(update, context):
    await update.message.reply_text(EMERGENCY, parse_mode="Markdown", reply_markup=back_keyboard())

# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

async def _run_async():
    """Fully async bot runner — compatible with Python 3.14+."""
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("zukas", zukas_cmd))
    app.add_handler(CommandHandler("transport", transport_cmd))
    app.add_handler(CommandHandler("food", food_cmd))
    app.add_handler(CommandHandler("stay", stay_cmd))
    app.add_handler(CommandHandler("boats", boats_cmd))
    app.add_handler(CommandHandler("cowork", cowork_cmd))
    app.add_handler(CommandHandler("emergency", emergency_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    port = int(os.environ.get("PORT", 8443))

    async with app:
        await app.start()
        if render_url:
            webhook_url = f"{render_url}/webhook"
            print(f"🌐 Webhook modu: {webhook_url}")
            await app.updater.start_webhook(
                listen="0.0.0.0",
                port=port,
                webhook_url=webhook_url,
                drop_pending_updates=True,
            )
        else:
            print("🤖 Polling modu (local)...")
            await app.updater.start_polling(drop_pending_updates=True)
        await app.updater.idle()
        # async with app: handles shutdown automatically — do NOT call app.stop() here


def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN environment variable not found.")
        return
    asyncio.run(_run_async())


if __name__ == "__main__":
    main()
