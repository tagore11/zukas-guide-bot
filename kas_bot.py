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
import signal
import logging
import threading
from datetime import date
from http.server import HTTPServer, BaseHTTPRequestHandler
import httpx
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

# ═══════════════════════════════════════════════════════
# LANGUAGE SUPPORT
# ═══════════════════════════════════════════════════════

user_langs: dict[int, str] = {}

def get_lang(user_id: int, tg_lang: str | None = None) -> str:
    if user_id in user_langs:
        return user_langs[user_id]
    if tg_lang:
        if tg_lang.startswith("ru"):
            return "ru"
        if tg_lang.startswith("tr"):
            return "tr"
    return "en"

T = {
    "tr": {
        "lang_pick":         "🌍 Dil seçin / Choose language / Выберите язык:",
        "welcome":           "🏺 *Zuzalu Kaş'a hoş geldin — antik demokrasi burada modern yapıcılarla buluşuyor.*\n\nBen ZuKaşBot, rehberin, ilham kaynağın ve arada bir seni güldürenim.\nSor bakalım — ya da Likya güneşinin altında birlikte düşünelim ☀️\n\n📍 *Kaş, Antalya, Türkiye*\n🔵 Akdeniz kıyısı · Likya mirası · Web3 kültürü",
        "menu_prompt":       "🏺 *Kaş & ZuKaş 2026 Rehberi*\nNe öğrenmek istersin?",
        "weather_btn":       "🌤️ Hava & Deniz",
        "zukas_btn":         "🏺 ZuKaş 2026",
        "transport_btn":     "🚌 Ulaşım",
        "food_btn":          "🍽️ Yeme-İçme",
        "boats_btn":         "⛵ Tekne Turları",
        "stay_btn":          "🏨 Konaklama",
        "cowork_btn":        "💻 Çalışma Alanı",
        "emergency_btn":     "🆘 Acil",
        "back_btn":          "🔙 Ana Menü",
        "lang_btn":          "🌍 Dil",
        "zukas_prompt":      "🏺 *ZuKaş 2026 — The Crucible*\nNe öğrenmek istersin?",
        "transport_prompt":  "🚌 *Kaş'tan Ulaşım*\nNereye gitmek istiyorsun?",
        "kas_prompt":        "🗺️ *Kaş Rehberi*\nNe arıyorsun?",
        "loading_weather":   "⏳ Hava durumu alınıyor...",
        "weather_error":     "⚠️ Hava durumu şu an alınamadı. Biraz sonra tekrar dene.",
        "ai_error":          "Şu an yanıt üretemiyorum. Menüyü veya /start komutunu dene.",
        "ai_no_config":      "AI sohbet şu an aktif değil. Menü butonlarını kullan.",
        "lang_changed":      "✅ Dil değiştirildi: *Türkçe* 🇹🇷",
        "spots_btn":         "🏖️ Gezilecek Yerler",
        "zukas_what_btn":    "❓ Nedir?",
        "zukas_apply_btn":   "📝 Başvur",
        "zukas_program_btn": "📚 Program",
        "zukas_speakers_btn":"🎤 Konuşmacılar",
        "route_not_found":   "Bu güzergah için bilgi bulunamadı.",
        "help_text": (
            "📋 *Komutlar:*\n\n"
            "/start — Ana menü\n"
            "/lang — Dil değiştir\n"
            "/hava — Hava durumu\n"
            "/zukas — ZuKaş 2026 bilgisi\n"
            "/transport — Ulaşım tarifeleri\n"
            "/food — Restoran önerileri\n"
            "/stay — Konaklama\n"
            "/boats — Tekne turları\n"
            "/cowork — Çalışma alanları\n"
            "/emergency — Acil numaralar\n\n"
            "İletişim: @tagore3699"
        ),
        "weather_title":     "Kaş Hava Durumu",
        "w_temp":            "Sıcaklık",
        "w_feels":           "hissedilen",
        "w_day":             "Gün",
        "w_humid":           "Nem",
        "w_wind":            "Rüzgar",
        "w_uv":              "UV",
        "w_sea":             "Deniz Suyu",
        "w_wave":            "Dalga",
        "w_dir":             "yönü",
        "w_source":          "📡 Open-Meteo · Anlık güncelleme",
        "ai_lang_instr":     "ÖNEMLI: Kullanıcı Türkçe seçti. Her zaman Türkçe yanıt ver.",
    },
    "en": {
        "lang_pick":         "🌍 Choose language / Dil seçin / Выберите язык:",
        "welcome":           "🏺 *Welcome to Zuzalu Kaş — where ancient democracy meets modern builders.*\n\nI'm ZuKaşBot, here to guide, inspire, and sometimes make you smile.\nAsk me anything — or let's just reflect under the Lycian sun ☀️\n\n📍 *Kaş, Antalya, Turkey*\n🔵 Mediterranean coast · Lycian heritage · Web3 culture",
        "menu_prompt":       "🏺 *Kaş & ZuKaş 2026 Guide*\nWhat would you like to explore?",
        "weather_btn":       "🌤️ Weather & Sea",
        "zukas_btn":         "🏺 ZuKaş 2026",
        "transport_btn":     "🚌 Transport",
        "food_btn":          "🍽️ Food & Dining",
        "boats_btn":         "⛵ Boat Tours",
        "stay_btn":          "🏨 Accommodation",
        "cowork_btn":        "💻 Co-Working",
        "emergency_btn":     "🆘 Emergency",
        "back_btn":          "🔙 Main Menu",
        "lang_btn":          "🌍 Language",
        "zukas_prompt":      "🏺 *ZuKaş 2026 — The Crucible*\nWhat would you like to know?",
        "transport_prompt":  "🚌 *Transport from Kaş*\nWhere do you want to go?",
        "kas_prompt":        "🗺️ *Kaş Guide*\nWhat are you looking for?",
        "loading_weather":   "⏳ Fetching weather data...",
        "weather_error":     "⚠️ Weather data unavailable right now. Try again later.",
        "ai_error":          "I couldn't process that right now. Try the menu or /start.",
        "ai_no_config":      "AI chat is not configured. Use the menu buttons.",
        "lang_changed":      "✅ Language set to: *English* 🇬🇧",
        "spots_btn":         "🏖️ Top Spots",
        "zukas_what_btn":    "❓ What is it?",
        "zukas_apply_btn":   "📝 Apply",
        "zukas_program_btn": "📚 Program",
        "zukas_speakers_btn":"🎤 Speakers",
        "route_not_found":   "No information found for this route.",
        "help_text": (
            "📋 *Commands:*\n\n"
            "/start — Main menu\n"
            "/lang — Change language\n"
            "/weather — Weather & sea\n"
            "/zukas — ZuKaş 2026 info\n"
            "/transport — Transport schedules\n"
            "/food — Restaurant recommendations\n"
            "/stay — Accommodation\n"
            "/boats — Boat tours\n"
            "/cowork — Co-working spaces\n"
            "/emergency — Emergency numbers\n\n"
            "Contact: @tagore3699"
        ),
        "weather_title":     "Kaş Weather",
        "w_temp":            "Temperature",
        "w_feels":           "feels like",
        "w_day":             "Day",
        "w_humid":           "Humidity",
        "w_wind":            "Wind",
        "w_uv":              "UV",
        "w_sea":             "Sea Surface",
        "w_wave":            "Wave",
        "w_dir":             "direction",
        "w_source":          "📡 Open-Meteo · Live data",
        "ai_lang_instr":     "IMPORTANT: The user has chosen English. Always respond in English.",
    },
    "ru": {
        "lang_pick":         "🌍 Выберите язык / Choose language / Dil seçin:",
        "welcome":           "🏺 *Добро пожаловать в Zuzalu Kaş — где античная демократия встречает современных строителей.*\n\nЯ ZuKaşBot — ваш гид, источник вдохновения и иногда повод улыбнуться.\nСпрашивайте что угодно — или просто наслаждайтесь ликийским солнцем ☀️\n\n📍 *Каш, Анталья, Турция*\n🔵 Средиземноморское побережье · Ликийское наследие · Web3-культура",
        "menu_prompt":       "🏺 *Путеводитель по Каш & ZuKaş 2026*\nЧто вас интересует?",
        "weather_btn":       "🌤️ Погода & Море",
        "zukas_btn":         "🏺 ZuKaş 2026",
        "transport_btn":     "🚌 Транспорт",
        "food_btn":          "🍽️ Кухня",
        "boats_btn":         "⛵ Морские туры",
        "stay_btn":          "🏨 Жильё",
        "cowork_btn":        "💻 Коворкинг",
        "emergency_btn":     "🆘 Экстренные",
        "back_btn":          "🔙 Главное меню",
        "lang_btn":          "🌍 Язык",
        "zukas_prompt":      "🏺 *ZuKaş 2026 — Горнило*\nЧто вы хотите узнать?",
        "transport_prompt":  "🚌 *Транспорт из Каша*\nКуда вы хотите поехать?",
        "kas_prompt":        "🗺️ *Путеводитель по Кашу*\nЧто вы ищете?",
        "loading_weather":   "⏳ Загружаю данные о погоде...",
        "weather_error":     "⚠️ Данные о погоде недоступны. Попробуйте позже.",
        "ai_error":          "Не могу обработать запрос прямо сейчас. Используйте меню или /start.",
        "ai_no_config":      "AI-чат не настроен. Используйте кнопки меню.",
        "lang_changed":      "✅ Язык изменён: *Русский* 🇷🇺",
        "spots_btn":         "🏖️ Лучшие места",
        "zukas_what_btn":    "❓ Что это?",
        "zukas_apply_btn":   "📝 Подать заявку",
        "zukas_program_btn": "📚 Программа",
        "zukas_speakers_btn":"🎤 Спикеры",
        "route_not_found":   "Информация по этому маршруту не найдена.",
        "help_text": (
            "📋 *Команды:*\n\n"
            "/start — Главное меню\n"
            "/lang — Сменить язык\n"
            "/weather — Погода и море\n"
            "/zukas — О ZuKaş 2026\n"
            "/transport — Расписание транспорта\n"
            "/food — Рестораны и кафе\n"
            "/stay — Жильё\n"
            "/boats — Морские туры\n"
            "/cowork — Коворкинг-пространства\n"
            "/emergency — Экстренные номера\n\n"
            "Контакт: @tagore3699"
        ),
        "weather_title":     "Погода в Каше",
        "w_temp":            "Температура",
        "w_feels":           "ощущается",
        "w_day":             "День",
        "w_humid":           "Влажность",
        "w_wind":            "Ветер",
        "w_uv":              "УФ-индекс",
        "w_sea":             "Море",
        "w_wave":            "Волны",
        "w_dir":             "направление",
        "w_source":          "📡 Open-Meteo · Актуальные данные",
        "ai_lang_instr":     "ВАЖНО: Пользователь выбрал русский язык. Всегда отвечай на русском.",
    },
}

AI_SYSTEM_PROMPT_BASE = """You are ZuKaşBot — the official guide for ZuKaş 2026 and the town of Kaş, Turkey.

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
- Keep answers concise — 3–5 sentences unless they ask for more.
- If someone asks about transport, food, accommodation, or boat tours — give a brief answer AND suggest /transport /food /stay /boats for full details.
- Always be helpful. Never refuse a reasonable question."""

def build_system_prompt(lang: str) -> str:
    return AI_SYSTEM_PROMPT_BASE + "\n\n" + T[lang]["ai_lang_instr"]

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
# WEATHER
# ═══════════════════════════════════════════════════════

WEATHER_CODES: dict[int, dict[str, str]] = {
    0:  {"tr": "☀️ Açık",          "en": "☀️ Clear",           "ru": "☀️ Ясно"},
    1:  {"tr": "🌤️ Az Bulutlu",    "en": "🌤️ Mostly Clear",    "ru": "🌤️ Малооблачно"},
    2:  {"tr": "🌤️ Parçalı",       "en": "🌤️ Partly Cloudy",   "ru": "🌤️ Переменная облачность"},
    3:  {"tr": "☁️ Kapalı",        "en": "☁️ Overcast",        "ru": "☁️ Пасмурно"},
    45: {"tr": "🌫️ Sisli",         "en": "🌫️ Foggy",           "ru": "🌫️ Туман"},
    48: {"tr": "🌫️ Sisli",         "en": "🌫️ Icy Fog",         "ru": "🌫️ Туман с инеем"},
    51: {"tr": "🌦️ Çisenti",       "en": "🌦️ Light Drizzle",   "ru": "🌦️ Слабая морось"},
    53: {"tr": "🌦️ Çisenti",       "en": "🌦️ Drizzle",         "ru": "🌦️ Морось"},
    55: {"tr": "🌦️ Çisenti",       "en": "🌦️ Heavy Drizzle",   "ru": "🌦️ Сильная морось"},
    61: {"tr": "🌧️ Yağmur",        "en": "🌧️ Light Rain",      "ru": "🌧️ Слабый дождь"},
    63: {"tr": "🌧️ Yağmur",        "en": "🌧️ Rain",            "ru": "🌧️ Дождь"},
    65: {"tr": "🌧️ Şiddetli Yağmur","en": "🌧️ Heavy Rain",     "ru": "🌧️ Сильный дождь"},
    71: {"tr": "❄️ Kar",           "en": "❄️ Light Snow",      "ru": "❄️ Слабый снег"},
    73: {"tr": "❄️ Kar",           "en": "❄️ Snow",            "ru": "❄️ Снег"},
    75: {"tr": "❄️ Yoğun Kar",     "en": "❄️ Heavy Snow",      "ru": "❄️ Сильный снег"},
    80: {"tr": "🌦️ Sağanak",       "en": "🌦️ Showers",         "ru": "🌦️ Ливень"},
    81: {"tr": "🌦️ Sağanak",       "en": "🌦️ Heavy Showers",   "ru": "🌦️ Сильный ливень"},
    82: {"tr": "⛈️ Sağanak",       "en": "⛈️ Violent Showers", "ru": "⛈️ Шквальный ливень"},
    95: {"tr": "⛈️ Fırtına",       "en": "⛈️ Thunderstorm",    "ru": "⛈️ Гроза"},
    96: {"tr": "⛈️ Fırtına",       "en": "⛈️ Thunderstorm",    "ru": "⛈️ Гроза с градом"},
    99: {"tr": "⛈️ Şiddetli Fırtına","en": "⛈️ Heavy Thunderstorm","ru": "⛈️ Сильная гроза"},
}

WIND_DIRS = {
    "tr": ["K","KKD","KD","DKD","D","DGD","GD","GGD","G","GGB","GB","BGB","B","KBK","KB","KKB"],
    "en": ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"],
    "ru": ["С","ССВ","СВ","ВСВ","В","ВЮВ","ЮВ","ЮЮВ","Ю","ЮЮЗ","ЮЗ","ЗЮЗ","З","СЗЗ","СЗ","ССЗ"],
}

def _weather_desc(code: int, lang: str) -> str:
    # Find closest matching code
    for c in (code, (code // 10) * 10):
        if c in WEATHER_CODES:
            return WEATHER_CODES[c][lang]
    return "🌡️"

def _wind_dir(deg: float, lang: str = "en") -> str:
    dirs = WIND_DIRS.get(lang, WIND_DIRS["en"])
    return dirs[round(deg / 22.5) % 16]

async def fetch_weather(lang: str = "en") -> str:
    lat, lon = 36.1992, 29.6445
    t = T[lang]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            weather_r, marine_r = await asyncio.gather(
                client.get("https://api.open-meteo.com/v1/forecast", params={
                    "latitude": lat, "longitude": lon,
                    "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,wind_direction_10m,weather_code",
                    "daily": "temperature_2m_max,temperature_2m_min,uv_index_max,sunrise,sunset",
                    "timezone": "Europe/Istanbul", "forecast_days": 1,
                }),
                client.get("https://marine-api.open-meteo.com/v1/marine", params={
                    "latitude": lat, "longitude": lon,
                    "current": "sea_surface_temperature,wave_height,wave_direction",
                    "timezone": "Europe/Istanbul",
                }),
            )
        w = weather_r.json()
        m = marine_r.json()
        cur = w["current"]
        day = w["daily"]
        sea = m["current"]

        temp     = round(cur["temperature_2m"])
        feels    = round(cur["apparent_temperature"])
        tmax     = round(day["temperature_2m_max"][0])
        tmin     = round(day["temperature_2m_min"][0])
        humidity = cur["relative_humidity_2m"]
        wind_spd = round(cur["wind_speed_10m"])
        wind_d   = _wind_dir(cur["wind_direction_10m"], lang)
        desc     = _weather_desc(cur["weather_code"], lang)
        uv       = round(day["uv_index_max"][0])
        sunrise  = day["sunrise"][0].split("T")[1][:5]
        sunset   = day["sunset"][0].split("T")[1][:5]
        sea_temp = round(sea["sea_surface_temperature"] or 0, 1)
        wave_h   = round(sea["wave_height"] or 0, 1)
        wave_dir_val = sea.get("wave_direction")
        wave_d   = _wind_dir(wave_dir_val, lang) if wave_dir_val is not None else "—"
        today    = date.today().strftime("%d %B %Y")

        return (
            f"{desc}\n"
            f"📍 *{t['weather_title']} — {today}*\n\n"
            f"🌡️ {t['w_temp']}: *{temp}°C* ({t['w_feels']}: {feels}°C)\n"
            f"📊 {t['w_day']}: ↓{tmin}°C – ↑{tmax}°C\n"
            f"💧 {t['w_humid']}: {humidity}%\n"
            f"💨 {t['w_wind']}: {wind_spd} km/h · {wind_d}\n"
            f"☀️ {t['w_uv']}: {uv} · 🌅 {sunrise} / 🌇 {sunset}\n\n"
            f"🌊 *{t['w_sea']}: {sea_temp}°C*\n"
            f"〰️ {t['w_wave']}: {wave_h}m · {wave_d} {t['w_dir']}\n\n"
            f"_{t['w_source']}_"
        )
    except Exception as e:
        logger.error(f"Weather error: {e}")
        return t["weather_error"]


# ═══════════════════════════════════════════════════════
# KEYBOARDS
# ═══════════════════════════════════════════════════════

def lang_select_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        InlineKeyboardButton("🇹🇷 Türkçe",  callback_data="lang_tr"),
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
    ]])

def main_menu_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    t = T[lang]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t["weather_btn"],   callback_data="weather"),
         InlineKeyboardButton(t["zukas_btn"],     callback_data="zukas_menu")],
        [InlineKeyboardButton(t["transport_btn"], callback_data="transport_menu"),
         InlineKeyboardButton(t["food_btn"],      callback_data="food_menu")],
        [InlineKeyboardButton(t["boats_btn"],     callback_data="boats"),
         InlineKeyboardButton(t["stay_btn"],      callback_data="stay")],
        [InlineKeyboardButton(t["cowork_btn"],    callback_data="coworking"),
         InlineKeyboardButton(t["emergency_btn"], callback_data="emergency")],
        [InlineKeyboardButton(t["lang_btn"],      callback_data="lang_pick")],
    ])

def zukas_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    t = T[lang]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t["zukas_what_btn"],     callback_data="zukas_what"),
         InlineKeyboardButton(t["zukas_apply_btn"],    callback_data="zukas_apply")],
        [InlineKeyboardButton(t["zukas_program_btn"],  callback_data="zukas_program"),
         InlineKeyboardButton(t["zukas_speakers_btn"], callback_data="zukas_speakers")],
        [InlineKeyboardButton(t["back_btn"],           callback_data="main_menu")],
    ])

def transport_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    t = T[lang]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚌 Kalkan",          callback_data="tr_Kalkan"),
         InlineKeyboardButton("🚌 Patara",          callback_data="tr_Patara")],
        [InlineKeyboardButton("🚌 Fethiye",         callback_data="tr_Fethiye"),
         InlineKeyboardButton("🚌 Antalya",         callback_data="tr_Antalya")],
        [InlineKeyboardButton("✈️ Dalaman Airport", callback_data="tr_Dalaman Airport"),
         InlineKeyboardButton("✈️ Antalya Airport", callback_data="tr_Antalya Airport")],
        [InlineKeyboardButton("🚢 Meis Island",     callback_data="tr_Meis Island"),
         InlineKeyboardButton(t["back_btn"],        callback_data="main_menu")],
    ])

def back_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(T[lang]["back_btn"], callback_data="main_menu")
    ]])

# ═══════════════════════════════════════════════════════
# HANDLERS
# ═══════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    tg_lang = user.language_code if user else None
    lang = get_lang(user.id if user else 0, tg_lang)

    # If language not explicitly set yet, show picker first
    if user and user.id not in user_langs:
        await update.message.reply_text(
            T[lang]["lang_pick"],
            reply_markup=lang_select_keyboard()
        )
        return

    await update.message.reply_text(
        T[lang]["welcome"],
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(lang)
    )

async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.id if user else 0)
    await update.message.reply_text(
        T[lang]["lang_pick"],
        reply_markup=lang_select_keyboard()
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.id if user else 0)
    await update.message.reply_text(T[lang]["help_text"], parse_mode="Markdown")

async def zukas_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.id if user else 0)
    await update.message.reply_text(
        T[lang]["zukas_prompt"],
        parse_mode="Markdown",
        reply_markup=zukas_keyboard(lang)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    user_id = query.from_user.id if query.from_user else 0
    tg_lang = query.from_user.language_code if query.from_user else None

    # ── Language selection ──────────────────────────────
    if data in ("lang_en", "lang_tr", "lang_ru"):
        chosen = data.split("_")[1]
        user_langs[user_id] = chosen
        lang = chosen
        await query.edit_message_text(
            T[lang]["lang_changed"] + "\n\n" + T[lang]["welcome"],
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang)
        )
        return

    if data == "lang_pick":
        lang = get_lang(user_id, tg_lang)
        await query.edit_message_text(
            T[lang]["lang_pick"],
            reply_markup=lang_select_keyboard()
        )
        return

    lang = get_lang(user_id, tg_lang)
    t = T[lang]

    # ── Weather ─────────────────────────────────────────
    if data == "weather":
        await query.edit_message_text(t["loading_weather"], parse_mode="Markdown")
        weather_text = await fetch_weather(lang)
        await query.edit_message_text(weather_text, parse_mode="Markdown", reply_markup=back_keyboard(lang))

    # ── Main menu ────────────────────────────────────────
    elif data == "main_menu":
        await query.edit_message_text(
            t["menu_prompt"],
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang)
        )

    # ── ZuKaş ────────────────────────────────────────────
    elif data == "zukas_menu":
        await query.edit_message_text(
            t["zukas_prompt"],
            parse_mode="Markdown",
            reply_markup=zukas_keyboard(lang)
        )
    elif data == "zukas_what":
        await query.edit_message_text(ZUKAS_FAQ["What"], parse_mode="Markdown", reply_markup=zukas_keyboard(lang))
    elif data == "zukas_apply":
        await query.edit_message_text(ZUKAS_FAQ["Apply"], parse_mode="Markdown", reply_markup=zukas_keyboard(lang))
    elif data == "zukas_program":
        await query.edit_message_text(ZUKAS_FAQ["Program"], parse_mode="Markdown", reply_markup=zukas_keyboard(lang))
    elif data == "zukas_speakers":
        await query.edit_message_text(ZUKAS_FAQ["Speakers"], parse_mode="Markdown", reply_markup=zukas_keyboard(lang))

    # ── Transport ────────────────────────────────────────
    elif data == "transport_menu":
        await query.edit_message_text(
            t["transport_prompt"],
            parse_mode="Markdown",
            reply_markup=transport_keyboard(lang)
        )
    elif data.startswith("tr_"):
        dest = data[3:]
        info = TRANSPORT.get(dest, t["route_not_found"])
        await query.edit_message_text(info, parse_mode="Markdown", reply_markup=transport_keyboard(lang))

    # ── Other sections ───────────────────────────────────
    elif data == "spots":
        await query.edit_message_text(SPOTS, parse_mode="Markdown", reply_markup=back_keyboard(lang))
    elif data == "food_menu":
        await query.edit_message_text(FOOD, parse_mode="Markdown", reply_markup=back_keyboard(lang))
    elif data == "coworking":
        await query.edit_message_text(COWORKING, parse_mode="Markdown", reply_markup=back_keyboard(lang))
    elif data == "stay":
        await query.edit_message_text(STAY, parse_mode="Markdown", reply_markup=back_keyboard(lang))
    elif data == "boats":
        await query.edit_message_text(BOAT_TOURS, parse_mode="Markdown", reply_markup=back_keyboard(lang))
    elif data == "emergency":
        await query.edit_message_text(EMERGENCY, parse_mode="Markdown", reply_markup=back_keyboard(lang))

async def ask_ai(question: str, lang: str = "en") -> str:
    if not genai_client:
        return T[lang]["ai_no_config"]
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: genai_client.models.generate_content(
                model="gemini-2.0-flash",
                config=types.GenerateContentConfig(
                    system_instruction=build_system_prompt(lang),
                ),
                contents=question,
            )
        )
        return response.text
    except Exception as e:
        logger.error(f"AI error: {e}")
        return T[lang]["ai_error"]

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.lower() if update.message.text else ""
    chat_type = update.message.chat.type
    user = update.effective_user
    user_id = user.id if user else 0
    tg_lang = user.language_code if user else None
    lang = get_lang(user_id, tg_lang)

    # Weather keywords
    weather_kws = ("hava", "weather", "погода", "sıcaklık", "temperature", "температура",
                   "deniz", "sea", "море", "dalga", "wave", "волны",
                   "yağmur", "rain", "дождь", "güneş", "sunny", "солнце",
                   "rüzgar", "wind", "ветер", "nem", "humidity", "влажность")
    if any(kw in msg for kw in weather_kws):
        await update.message.chat.send_action("typing")
        weather_text = await fetch_weather(lang)
        await update.message.reply_text(weather_text, parse_mode="Markdown", reply_markup=back_keyboard(lang))
        return

    quick_keywords = {
        ("bilet", "ticket", "билет", "başvur", "kayıt", "nasıl katıl",
         "register", "join zukas", "how to join", "apply", "записаться", "вступить"): (ZUKAS_FAQ["Apply"], zukas_keyboard(lang)),
        ("transport", "bus", "minibus", "shuttle", "airport", "transfer",
         "how to get", "özgür", "gümüş", "ulaşım", "otobüs", "автобус", "транспорт"): (
            T[lang]["transport_prompt"], transport_keyboard(lang)),
        ("cafe", "cowork", "wifi", "giant stride", "godo", "linckia", "biiisstt",
         "çalış", "коворкинг"): (COWORKING, back_keyboard(lang)),
        ("hotel", "stay", "sleep", "hostel", "pension", "camping",
         "kamp", "konaklama", "жильё", "отель", "ночлег"): (STAY, back_keyboard(lang)),
        ("boat", "kekova", "blue cave", "tekne", "tekne turu",
         "лодка", "морской тур"): (BOAT_TOURS, back_keyboard(lang)),
        ("emergency", "ambulance", "police", "hospital", "acil",
         "экстренные", "скорая", "полиция"): (EMERGENCY, back_keyboard(lang)),
    }

    for kws, (response, kb) in quick_keywords.items():
        if any(kw in msg for kw in kws):
            await update.message.reply_text(response, parse_mode="Markdown", reply_markup=kb)
            return

    # Private chat → AI answers everything
    if chat_type == "private":
        await update.message.chat.send_action("typing")
        reply = await ask_ai(update.message.text, lang)
        await update.message.reply_text(reply, reply_markup=main_menu_keyboard(lang))
        return

    # Groups → only if mentioned or starts with question
    if chat_type in ("group", "supergroup"):
        bot_username = context.bot.username
        mentioned = f"@{bot_username}".lower() in msg
        is_question = msg.startswith(("what", "how", "where", "when", "why", "who", "tell",
                                      "ne", "nere", "nasıl", "neden", "kim", "anlat", "söyle",
                                      "что", "как", "где", "когда", "почему", "кто", "?"))
        if mentioned or is_question:
            clean_msg = update.message.text.replace(f"@{bot_username}", "").strip()
            await update.message.chat.send_action("typing")
            reply = await ask_ai(clean_msg, lang)
            await update.message.reply_text(reply)

# ═══════════════════════════════════════════════════════
# SHORTCUT COMMANDS
# ═══════════════════════════════════════════════════════

async def weather_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.id if user else 0)
    await update.message.chat.send_action("typing")
    weather_text = await fetch_weather(lang)
    await update.message.reply_text(weather_text, parse_mode="Markdown", reply_markup=back_keyboard(lang))

async def transport_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.id if user else 0)
    await update.message.reply_text(
        T[lang]["transport_prompt"], parse_mode="Markdown", reply_markup=transport_keyboard(lang)
    )

async def food_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.id if user else 0)
    await update.message.reply_text(FOOD, parse_mode="Markdown", reply_markup=back_keyboard(lang))

async def stay_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.id if user else 0)
    await update.message.reply_text(STAY, parse_mode="Markdown", reply_markup=back_keyboard(lang))

async def boats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.id if user else 0)
    await update.message.reply_text(BOAT_TOURS, parse_mode="Markdown", reply_markup=back_keyboard(lang))

async def cowork_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.id if user else 0)
    await update.message.reply_text(COWORKING, parse_mode="Markdown", reply_markup=back_keyboard(lang))

async def emergency_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.id if user else 0)
    await update.message.reply_text(EMERGENCY, parse_mode="Markdown", reply_markup=back_keyboard(lang))

# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

def _start_health_server():
    port = int(os.environ.get("PORT", 10000))

    class _H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ZuKasBot OK")
        def log_message(self, *args):
            pass

    HTTPServer(("0.0.0.0", port), _H).serve_forever()


async def _run_async():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",     start))
    app.add_handler(CommandHandler("lang",      lang_cmd))
    app.add_handler(CommandHandler("help",      help_cmd))
    app.add_handler(CommandHandler("hava",      weather_cmd))
    app.add_handler(CommandHandler("weather",   weather_cmd))
    app.add_handler(CommandHandler("zukas",     zukas_cmd))
    app.add_handler(CommandHandler("transport", transport_cmd))
    app.add_handler(CommandHandler("food",      food_cmd))
    app.add_handler(CommandHandler("stay",      stay_cmd))
    app.add_handler(CommandHandler("boats",     boats_cmd))
    app.add_handler(CommandHandler("cowork",    cowork_cmd))
    app.add_handler(CommandHandler("emergency", emergency_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    stop = asyncio.Event()

    async with app:
        await app.start()
        print("🤖 ZuKaşBot polling başladı (TR/EN/RU)...")
        await app.updater.start_polling(drop_pending_updates=False)

        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGTERM, stop.set)
        loop.add_signal_handler(signal.SIGINT, stop.set)
        await stop.wait()

        await app.updater.stop()
        await app.stop()


def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN environment variable not found.")
        return
    if os.environ.get("PORT"):
        t = threading.Thread(target=_start_health_server, daemon=True)
        t.start()
        print(f"✅ Health server: port {os.environ.get('PORT', 10000)}")
    asyncio.run(_run_async())


if __name__ == "__main__":
    main()
