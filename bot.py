import os
import io
import re
import time
import json
import threading
import requests
import jdatetime
import pytz
from datetime import timedelta
from PIL import Image, ImageDraw, ImageFont

# =====================================================================
# ۱. تنظیمات اصلی
# =====================================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

CITY_NAME_FA = "شیراز"
CITY_NAME_EN = "Shiraz"
CITY_LAT = 29.5918
CITY_LON = 52.5837

TEHRAN_TZ = pytz.timezone("Asia/Tehran")
STATE_FILE = "state.json"

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/vazirmatn/Vazirmatn-Bold.ttf",
    "Vazirmatn-Bold.ttf",
    "font.ttf"
]
FONT_URL = "https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/fonts/ttf/Vazirmatn-Bold.ttf"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Cache-Control": "no-cache"
}

# منوی ثابت پایین صفحه ربات (۳ کلید اصلی)
BOT_MENU_KEYBOARD = json.dumps({
    "keyboard": [
        [{"text": "☀️ صبح بخیر"}, {"text": "🌤 وضعیت هوا"}],
        [{"text": "⚽️ نتایج زنده"}]
    ],
    "resize_keyboard": True,
    "is_persistent": True
})

# دسته‌بندی ۵ گانه لیگ‌ها برای منوی انتخاب لیگ
LEAGUE_CATEGORIES = [
    ("lg_ir",  "🇮🇷 لیگ برتر و جام حذفی ایران"),
    ("lg_eng", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 لیگ برتر انگلیس"),
    ("lg_esp", "🇪🇸 لالیگا اسپانیا"),
    ("lg_ger", "🇩🇪 بوندسلیگا آلمان"),
    ("lg_ucl", "🏆 لیگ قهرمانان اروپا")
]

# لوگوهای تیم‌های لیگ برتر ایران
IRAN_LOGOS = {
    'فجر سپاسی': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%81%D8%AC%D8%B1%20%D8%B4%D9%87%DB%8C%D8%AF%20%D8%B3%D9%BE%D8%A7%D8%B3%DB%8C.png',
    'فجرسپاسی': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%81%D8%AC%D8%B1%20%D8%B4%D9%87%DB%8C%D8%AF%20%D8%B3%D9%BE%D8%A7%D8%B3%DB%8C.png',
    'فجر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%81%D8%AC%D8%B1%20%D8%B4%D9%87%DB%8C%D8%AF%20%D8%B3%D9%BE%D8%A7%D8%B3%DB%8C.png',
    'پرسپولیس': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%BE%D8%B1%D8%B3%D9%BE%D9%88%D9%84%DB%8C%D8%B3%20%D8%AA%D9%87%D8%B1%D8%A7%D9%86.png',
    'استقلال خوزستان': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%A7%D8%B3%D8%AA%D9%82%D9%84%D8%A7%D9%84%20%D8%AE%D9%88%D8%B2%D8%B3%D8%AA%D8%A7%D9%86.png',
    'استقلال': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%A7%D8%B3%D8%AA%D9%82%D9%84%D8%A7%D9%84%20%D8%AA%D9%87%D8%B1%D8%A7%D9%86.png',
    'سپاهان': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%B3%D9%BE%D8%A7%D9%87%D8%A7%D9%86%20%D8%A7%D8%B5%D9%81%D9%87%D8%A7%D9%86.png',
    'تراکتور': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%AA%D8%B1%D8%A7%DA%A9%D8%AA%D9%88%D8%B1%20%D8%AA%D8%A8%D8%B1%DB%8C%D8%B2.png',
    'فولاد': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%81%D9%88%D9%84%D8%A7%D8%AF%20%D8%AE%D9%88%D8%B2%D8%B3%D8%AA%D8%A7%D9%86.png',
    'ذوب آهن': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%B0%D9%88%D8%A8%20%D8%A2%D9%87%D9%86%20%D8%A7%D8%B5%D9%81%D9%87%D8%A7%D9%86.png',
    'ذوب‌آهن': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%B0%D9%88%D8%A8%20%D8%A2%D9%87%D9%86%20%D8%A7%D8%B5%D9%81%D9%87%D8%A7%D9%86.png',
    'ملوان': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%85%D9%84%D9%88%D8%A7%D9%86%20%D8%A8%D9%86%D8%AF%D8%B1%D8%A7%D9%86%D8%B2%D9%84%DB%8C.png',
    'گل گهر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%DA%AF%D9%84%20%DA%AF%D9%87%D8%B1%20%D8%B3%DB%8C%D8%B1%D8%AC%D8%A7%D9%86.png',
    'گل‌گهر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%DA%AF%D9%84%20%DA%AF%D9%87%D8%B1%20%D8%B3%DB%8C%D8%B1%D8%AC%D8%A7%D9%86.png',
    'آلومینیوم': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%A2%D9%84%D9%88%D9%85%DB%8C%D9%86%DB%8C%D9%88%D9%85%20%D8%A7%D8%B1%D8%A7%DA%A9.png',
    'مس شهر بابک': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%85%D8%B3%20%D8%B4%D9%87%D8%B1%20%D8%A8%D8%A7%D8%A8%DA%A9.png',
    'شمس آذر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%B4%D9%85%D8%B3%20%D8%A2%D8%B0%D8%B1%20%D9%82%D8%B2%D9%88%DB%8C%D9%86.png',
    'شمس‌آذر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%B4%D9%85%D8%B3%20%D8%A2%D8%B0%D8%B1%20%D9%82%D8%B2%D9%88%DB%8C%D9%86.png',
    'چادرملو': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%DA%86%D8%A7%D8%AF%D8%B1%D9%85%D9%84%D9%88%20%D8%A7%D8%B1%D8%AF%DA%A9%D8%A7%D9%86.png',
    'خیبر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%AE%DB%8C%D8%A8%D8%B1%20%D8%AE%D8%B1%D9%85%E2%80%8C%D8%A2%D8%A8%D8%A7%D8%AF.png',
    'نساجی': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%86%D8%B3%D8%A7%D8%AC%DB%8C%20%D9%85%D8%A7%D8%B2%D9%86%D8%AF%D8%B1%D8%A7%D9%86.png',
    'هوادار': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/main/Logos/Havadar.png',
    'پیکان': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%BE%DB%8C%DA%A9%D8%A7%D9%86%20%D8%AA%D9%87%D8%B1%D8%A7%D9%86.png',
    'صنعت نفت': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%B5%D9%86%D8%B9%D8%AA%20%D9%86%D9%81%D8%AA%20%D8%A2%D8%A8%D8%A7%D8%AF%D8%A7%D9%86.png',
    'سایپا': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/main/Logos/Saipa.png',
}

# دیکشنری جامع فارسی‌ساز تیم‌های ایران و اروپا
TEAM_NAME_MAP = {
    # ایران
    "Persepolis": "پرسپولیس", "Esteghlal": "استقلال", "Sepahan": "سپاهان",
    "Tractor": "تراکتور", "Tractor Sazi": "تراکتور", "Foolad": "فولاد", "Foolad Khuzestan": "فولاد",
    "Zob Ahan": "ذوب آهن", "Malavan": "ملوان", "Gol Gohar": "گل گهر", "Gol Gohar Sirjan": "گل گهر",
    "Aluminium Arak": "آلومینیوم", "Shams Azar Qazvin": "شمس آذر", "Shams Azar": "شمس آذر",
    "Chadormalu": "چادرملو", "Chadormalu Ardakan": "چادرملو", "Kheybar Khorramabad": "خیبر",
    "Nassaji Mazandaran": "نساجی", "Havadar": "هوادار", "Paykan": "پیکان",
    "Sanat Naft": "صنعت نفت", "Sanat Naft Abadan": "صنعت نفت", "Saipa": "سایپا",
    "Fajr Sepasi": "فجر سپاسی", "Esteghlal Khuzestan": "استقلال خوزستان",
    "Mes Shahr-e Babak": "مس شهر بابک", "Mes Rafsanjan": "مس رفسنجان", "Mes Kerman": "مس کرمان",
    # انگلیس
    "Arsenal": "آرسنال", "Liverpool": "لیورپول", "Manchester City": "منچسترسیتی",
    "Manchester United": "منچستریونایتد", "Chelsea": "چلسی", "Tottenham Hotspur": "تاتنهام",
    "Newcastle United": "نیوکاسل", "Aston Villa": "استون ویلا",
    "Brighton & Hove Albion": "برایتون", "Brighton": "برایتون",
    "Brentford": "برنتفورد", "Crystal Palace": "کریستال پالاس",
    "Ipswich Town": "ایپسویچ تاون", "AFC Bournemouth": "بورنموث", "Bournemouth": "بورنموث",
    "Sunderland": "ساندرلند", "Everton": "اورتون", "Fulham": "فولام",
    "West Ham United": "وستهام", "Wolverhampton Wanderers": "ولورهمپتون",
    "Nottingham Forest": "ناتینگهام فارست", "Leicester City": "لسترسیتی",
    "Southampton": "ساوتهمپتون", "Leeds United": "لیدز یونایتد", "Burnley": "برنلی",
    "Sheffield United": "شفیلد یونایتد", "West Bromwich Albion": "وست برومویچ",
    # اسپانیا
    "Real Madrid": "رئال مادرید", "Barcelona": "بارسلونا", "Atlético Madrid": "اتلتیکو مادرید",
    "Atletico Madrid": "اتلتیکو مادرید", "Girona": "خیرونا", "Athletic Club": "اتلتیک بیلبائو",
    "Athletic Bilbao": "اتلتیک بیلبائو", "Real Sociedad": "رئال سوسیداد",
    "Real Betis": "رئال بتیس", "Villarreal": "ویارئال", "Valencia": "والنسیا",
    "Sevilla": "سویا", "Osasuna": "اوساسونا", "Celta Vigo": "سلتاویگو",
    "Rayo Vallecano": "رایو وایکانو", "Mallorca": "مایورکا", "RCD Mallorca": "مایورکا",
    "Getafe": "ختافه", "Alavés": "آلاوس", "Deportivo Alavés": "آلاوس",
    "Las Palmas": "لاس پالماس", "Leganés": "لگانس", "CD Leganés": "لگانس",
    "Espanyol": "اسپانیول", "RCD Espanyol": "اسپانیول", "Real Valladolid": "وایادولید",
    "Elche": "الچه", "Levante": "لوانته", "Real Oviedo": "رئال اوویدو",
    # آلمان
    "Bayern Munich": "بایرن مونیخ", "Bayer Leverkusen": "لورکوزن", "Borussia Dortmund": "دورتموند",
    "RB Leipzig": "لایپزیگ", "VfB Stuttgart": "اشتوتگارت", "Stuttgart": "اشتوتگارت",
    "Eintracht Frankfurt": "آینتراخت فرانکفورت", "TSG Hoffenheim": "هوفنهایم", "Hoffenheim": "هوفنهایم",
    "SC Freiburg": "فرایبورگ", "Freiburg": "فرایبورگ", "1. FC Heidenheim 1846": "هایدنهایم",
    "Heidenheim": "هایدنهایم", "Werder Bremen": "وردربرمن", "Borussia Mönchengladbach": "مونشن‌گلادباخ",
    "Borussia Monchengladbach": "مونشن‌گلادباخ", "1. FC Union Berlin": "یونیون برلین",
    "Union Berlin": "یونیون برلین", "VfL Wolfsburg": "وولفسبورگ", "Wolfsburg": "وولفسبورگ",
    "FC Augsburg": "آگزبورگ", "Augsburg": "آگزبورگ", "1. FSV Mainz 05": "ماینتس", "Mainz": "ماینتس",
    "VfL Bochum 1848": "بوخوم", "Bochum": "بوخوم", "FC St. Pauli": "سن پائولی",
    "Holstein Kiel": "هولشتاین کیل", "FC Cologne": "کلن", "1. FC Köln": "کلن",
    "Schalke 04": "شالکه", "FC Schalke 04": "شالکه", "Hamburger SV": "هامبورگ",
    # لیگ قهرمانان اروپا
    "Inter Milan": "اینتر میلان", "Internazionale": "اینتر میلان", "AC Milan": "میلان",
    "Juventus": "یوونتوس", "Napoli": "ناپولی", "Atalanta": "آتالانتا", "AS Roma": "آاس رم",
    "Roma": "آاس رم", "Lazio": "لاتزیو", "Bologna": "بولونیا", "Fiorentina": "فیورنتینا",
    "Como": "کومو", "Torino": "تورینو", "Udinese": "اودینزه", "Genoa": "جنوا",
    "Paris Saint-Germain": "پاری سن ژرمن", "Monaco": "موناکو", "AS Monaco": "موناکو",
    "Marseille": "مارسی", "Olympique Marseille": "مارسی", "Lille": "لیل", "LOSC Lille": "لیل",
    "Lyon": "لیون", "Olympique Lyonnais": "لیون", "Nice": "نیس", "OGC Nice": "نیس",
    "Lens": "لانس", "RC Lens": "لانس", "Brest": "برست", "Stade Brestois": "برست",
    "FC Porto": "پورتو", "Porto": "پورتو", "Benfica": "بنفیکا", "SL Benfica": "بنفیکا",
    "Sporting CP": "اسپورتینگ لیسبون", "Ajax": "آژاکس", "PSV Eindhoven": "آیندهوون",
    "Feyenoord": "فاینورد", "Celtic": "سلتیک", "Rangers": "رنجرز",
    "Fenerbahce": "فنرباغچه", "Fenerbahçe": "فنرباغچه", "Galatasaray": "گالاتاسرای",
    "Besiktas": "بشیکتاش", "Beşiktaş": "بشیکتاش", "AEK Athens": "آاک آتن",
    "Olympiacos": "المپیاکوس", "Panathinaikos": "پاناتینایکوس", "PAOK": "پائوک",
    "Club Brugge": "کلوب بروژ", "Red Bull Salzburg": "سالزبورگ", "RB Salzburg": "سالزبورگ",
    "Shakhtar Donetsk": "شاختار دونتسک", "Dinamo Zagreb": "دینامو زاگرب",
    "Sparta Prague": "اسپارتا پراگ", "Slovan Bratislava": "اسلوان براتیسلاوا",
    "Young Boys": "یانگ بویز", "Crvena Zvezda": "ستاره سرخ بلگراد", "Red Star Belgrade": "ستاره سرخ بلگراد",
    "Sturm Graz": "اشتورم گراتس", "Bodo/Glimt": "بودو گلیمت", "Bodø/Glimt": "بودو گلیمت",
    "Anderlecht": "آندرلخت", "Twente": "توئنته", "AZ Alkmaar": "آلکمار"
}

TRANSLATE_RAM = {}

CACHE = {
    "prayers": ("05:00", "06:21", "12:04", "17:40"),
    "weather": {"temp": 15.0, "temp_int": 15, "max": 20.0, "min": 8.0, "wind": 5, "humidity": 40, "desc": "آسمان صاف"},
    "market": ("در حال بروزرسانی", "در حال بروزرسانی", "در حال بروزرسانی"),
    "matches_by_id": {},
    "leagues": {
        "lg_ir":  {"title": "🇮🇷 لیگ برتر و جام حذفی ایران", "lines": [], "match_ids": [], "has_live": False},
        "lg_eng": {"title": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 لیگ برتر انگلیس", "lines": [], "match_ids": [], "has_live": False},
        "lg_esp": {"title": "🇪🇸 لالیگا اسپانیا", "lines": [], "match_ids": [], "has_live": False},
        "lg_ger": {"title": "🇩🇪 بوندسلیگا آلمان", "lines": [], "match_ids": [], "has_live": False},
        "lg_ucl": {"title": "🏆 لیگ قهرمانان اروپا", "lines": [], "match_ids": [], "has_live": False},
    }
}
TEMPLATES_RAM = {}
LOGO_RAM = {}


# =====================================================================
# ۲. مترجم خودکار فارسی + ابزارهای فونت و تاریخ
# =====================================================================
def to_persian_team(raw_name):
    if not raw_name:
        return ""
    clean = raw_name.strip()
    if clean in TEAM_NAME_MAP:
        return TEAM_NAME_MAP[clean]
    if clean in TRANSLATE_RAM:
        return TRANSLATE_RAM[clean]
    if re.search(r'[\u0600-\u06FF]', clean):
        return clean

    simplified = re.sub(r'\b(FC|AFC|SC|TSG|1\.\s*FC|RCD|CD|VfB|VfL|SV|RB|AS|AC|SL|RC)\b', '', clean).strip()
    if simplified in TEAM_NAME_MAP:
        TRANSLATE_RAM[clean] = TEAM_NAME_MAP[simplified]
        return TEAM_NAME_MAP[simplified]

    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": "en", "tl": "fa", "dt": "t", "q": simplified or clean}
        r = requests.get(url, params=params, timeout=4).json()
        fa_name = r[0][0][0].strip()
        TRANSLATE_RAM[clean] = fa_name
        return fa_name
    except Exception:
        return simplified or clean


def get_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path) and os.path.getsize(path) > 10000:
            return ImageFont.truetype(path, size)
    try:
        r = requests.get(FONT_URL, timeout=15)
        if r.status_code == 200 and len(r.content) > 10000:
            with open("Vazirmatn-Bold.ttf", "wb") as f:
                f.write(r.content)
            return ImageFont.truetype("Vazirmatn-Bold.ttf", size)
    except Exception:
        pass
    return ImageFont.load_default()


def to_fa_digits(val):
    en = "0123456789"
    fa = "۰۱۲۳۴۵۶۷۸۹"
    res = str(val)
    for e, f in zip(en, fa):
        res = res.replace(e, f)
    return res


def draw_rtl_centered(draw, y, text, font, fill, width):
    clean_text = to_fa_digits(text)
    bbox = draw.textbbox((0, 0), clean_text, font=font, direction="rtl", language="fa")
    w = bbox[2] - bbox[0]
    draw.text(((width - w) / 2, y), clean_text, font=font, fill=fill, direction="rtl", language="fa")


def draw_rtl_at_center_x(draw, center_x, y, text, font, fill):
    clean_text = to_fa_digits(text)
    bbox = draw.textbbox((0, 0), clean_text, font=font, direction="rtl", language="fa")
    w = bbox[2] - bbox[0]
    draw.text((center_x - w / 2, y), clean_text, font=font, fill=fill, direction="rtl", language="fa")


def preload_templates():
    configs = [
        ("t1", ["1.jpg", "1 (2).jpg", "1.png"], (720, 1280), (18, 60, 50, 255)),
        ("t2", ["2.jpg", "111 (Copy).jfif", "2.png"], (1024, 1820), (30, 24, 50, 255)),
        ("t3", ["3.jpg", "11 (Copy).jfif", "3.png"], (1024, 1820), (12, 22, 38, 255)),
    ]
    for key, candidates, size, color in configs:
        loaded = None
        for name in candidates:
            if os.path.exists(name):
                loaded = Image.open(name).convert("RGBA").resize(size)
                break
        if loaded is None:
            loaded = Image.new("RGBA", size, color)
        TEMPLATES_RAM[key] = loaded


# =====================================================================
# ۳. ارتباط با تلگرام و منوی دسته‌بندی لیگ‌ها
# =====================================================================
def setup_bot_commands():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands"
    commands = [
        {"command": "morning", "description": "☀️ صبح بخیر (شرعیات، طلا و ارز)"},
        {"command": "weather", "description": "🌤 وضعیت آب و هوا"},
        {"command": "football", "description": "⚽️ نتایج زنده (انتخاب لیگ)"}
    ]
    try:
        requests.post(url, json={"commands": commands}, timeout=10)
    except Exception:
        pass


def send_telegram_photo(chat_id, img, caption=""):
    if not chat_id:
        return
    bio = io.BytesIO()
    img.convert("RGB").save(bio, format="JPEG", quality=93)
    bio.seek(0)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    data = {"chat_id": chat_id, "caption": caption}
    if not str(chat_id).startswith("@") and not str(chat_id).startswith("-"):
        data["reply_markup"] = BOT_MENU_KEYBOARD
    try:
        requests.post(url, data=data, files={"photo": ("report.jpg", bio, "image/jpeg")}, timeout=15)
    except Exception as e:
        print("Send photo error:", e)


def send_menu_keyboard(chat_id, text="✅ منوی ربات آماده است! از دکمه‌های پایین صفحه انتخاب کنید:"):
    if not chat_id:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(
            url,
            data={"chat_id": chat_id, "text": text, "reply_markup": BOT_MENU_KEYBOARD},
            timeout=10
        )
    except Exception:
        pass


def build_league_selector_markup():
    """ساخت دکمه‌های دسته‌بندی لیگ‌ها برای سوال «کدوم لیگ مد نظرته؟»"""
    buttons = []
    for lg_key, lg_title in LEAGUE_CATEGORIES:
        lg_info = CACHE["leagues"].get(lg_key, {})
        count = len(lg_info.get("match_ids", []))
        live_badge = " 🔴 (زنده)" if lg_info.get("has_live") else ""
        count_txt = f" ({to_fa_digits(count)} بازی)" if count > 0 else ""
        btn_text = f"{lg_title}{live_badge}{count_txt}"
        buttons.append([{"text": btn_text, "callback_data": f"showlg_{lg_key}"}])
    return json.dumps({"inline_keyboard": buttons})


def send_league_selection_question(chat_id, message_id=None):
    """پرسیدن سوال «کدوم لیگ مد نظرته؟» به همراه لیست لیگ‌ها"""
    text = (
        "⚽️ کدوم لیگ مد نظرته؟\n\n"
        "لطفاً یکی از لیگ‌های زیر را انتخاب کنید تا بازی‌های زنده (🔴)، "
        "پایان‌یافته (🏁) و در انتظار شروع (⏳) همان لیگ نمایش داده شود:"
    )
    markup = build_league_selector_markup()
    if message_id:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
        payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "reply_markup": markup}
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "reply_markup": markup}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Send league selector error:", e)


def send_specific_league_matches(chat_id, lg_key, message_id=None):
    """نمایش بازی‌های لیگ انتخاب‌شده با ایموجی وضعیت + دکمه تبدیل هر بازی به عکس"""
    lg_info = CACHE["leagues"].get(lg_key)
    if not lg_info:
        return

    title = lg_info["title"]
    lines = lg_info["lines"]
    m_ids = lg_info["match_ids"]

    if lines:
        matches_text = "\n".join(lines)
        legend = "\n\nراهنما: 🔴 در حال برگزاری (زنده) | 🏁 پایان بازی | ⏳ در انتظار شروع"
        text = (
            f"🏆 گزارش بازی‌های {title}:\n\n"
            f"{matches_text}"
            f"{legend}\n"
            "👇 روی هر بازی که می‌خواهید بزنید تا بلافاصله عکس آن ساخته و ارسال شود:"
        )
    else:
        text = f"🏆 {title}\n\n⚽️ در حال حاضر بازی فعالی برای این لیگ ثبت نشده است."

    buttons = []
    for mid in m_ids[:20]:
        m = CACHE["matches_by_id"].get(mid)
        if not m:
            continue
        btn_label = f"📸 {m['status_emoji']} {m['h_name']} {to_fa_digits(m['h_g'])} - {to_fa_digits(m['a_g'])} {m['a_name']}"
        buttons.append([{"text": btn_label, "callback_data": f"mkimg_{mid}"}])

    # دکمه بازگشت به لیست لیگ‌ها
    buttons.append([{"text": "🔙 بازگشت به انتخاب لیگ‌ها", "callback_data": "back_leagues"}])
    markup = json.dumps({"inline_keyboard": buttons})

    if message_id:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
        payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "reply_markup": markup}
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "reply_markup": markup}

    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Send league matches error:", e)


def answer_callback(callback_id, text=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
    try:
        requests.post(url, data={"callback_query_id": callback_id, "text": text}, timeout=5)
    except Exception:
        pass


# =====================================================================
# ۴. ساخت فوری ۳ تصویر گرافیکی
# =====================================================================
def get_persian_date():
    now = jdatetime.datetime.now(TEHRAN_TZ)
    weekdays = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
    months = ["", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
              "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
    wd = weekdays[now.weekday()]
    return f"{wd} {now.day} {months[now.month]} {now.year}", f"{now.day} {months[now.month]} {now.year}"


def build_morning_image():
    full_date, _ = get_persian_date()
    fajr, sunrise, dhuhr, maghrib = CACHE["prayers"]
    w = CACHE["weather"]
    usd, gold, coin = CACHE["market"]

    base = TEMPLATES_RAM["t1"].copy()
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    draw.rounded_rectangle([46, 128, 674, 976], radius=28, fill=(242, 238, 226, 248), outline=(205, 165, 80, 255), width=3)
    draw.rounded_rectangle([175, 1142, 545, 1210], radius=22, fill=(22, 62, 52, 255), outline=(205, 165, 80, 255), width=2)
    draw_rtl_centered(draw, 1156, "روز خوبی داشته باشید", get_font(28), (245, 225, 170), 720)

    f_title, f_sec, f_date, f_body = get_font(54), get_font(32), get_font(40), get_font(30)
    c_green, c_bronze, c_dark = (12, 55, 42), (148, 92, 38), (22, 38, 38)

    draw_rtl_centered(draw, 155, f"صبح بخیر {CITY_NAME_FA}", f_title, c_green, 720)
    draw_rtl_centered(draw, 240, "تقویم و گزارش روزانه", f_sec, c_bronze, 720)
    draw_rtl_centered(draw, 295, full_date, f_date, c_dark, 720)
    draw.line([(190, 368), (530, 368)], fill=(205, 165, 80, 255), width=2)

    draw_rtl_centered(draw, 390, f"اوقات شرعی به افق {CITY_NAME_FA}", f_sec, c_bronze, 720)
    draw_rtl_centered(draw, 445, f"اذان صبح {fajr} | طلوع آفتاب {sunrise}", f_body, c_dark, 720)
    draw_rtl_centered(draw, 495, f"اذان ظهر {dhuhr} | اذان مغرب {maghrib}", f_body, c_dark, 720)

    draw_rtl_centered(draw, 570, "وضعیت آب و هوا", f_sec, c_bronze, 720)
    draw_rtl_centered(draw, 625, f"دمای فعلی: {w['temp']} درجه", f_body, c_dark, 720)
    draw_rtl_centered(draw, 675, f"بیشینه {w['max']} | کمینه {w['min']}", f_body, c_dark, 720)

    draw_rtl_centered(draw, 750, "نبض بازار طلا و ارز", f_sec, c_bronze, 720)
    draw_rtl_centered(draw, 805, f"دلار آزاد: {usd} ریال", f_body, c_dark, 720)
    draw_rtl_centered(draw, 855, f"طلای ۱۸ عیار: {gold} ریال", f_body, c_dark, 720)
    draw_rtl_centered(draw, 905, f"سکه امامی: {coin} ریال", f_body, c_dark, 720)

    return Image.alpha_composite(base, overlay)


def build_weather_image():
    _, short_date = get_persian_date()
    w = CACHE["weather"]

    base = TEMPLATES_RAM["t2"].copy()
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    draw.rounded_rectangle([250, 315, 774, 425], radius=18, fill=(32, 26, 52, 255))
    draw_rtl_centered(draw, 330, short_date, get_font(62), (255, 255, 255), 1024)

    draw.rounded_rectangle([98, 518, 595, 1048], radius=36, fill=(92, 88, 114, 248), outline=(212, 182, 115, 255), width=4)
    draw_rtl_at_center_x(draw, 346, 720, f"{w['temp_int']} درجه", get_font(105), (245, 212, 135))

    draw.rounded_rectangle([600, 905, 960, 1000], radius=15, fill=(44, 38, 64, 255))
    draw_rtl_at_center_x(draw, 780, 920, w["desc"], get_font(46), (255, 255, 255))

    bars = [
        (1094, 1212, f"بیشینه روز: {round(w['max'])} درجه / کمینه شب: {round(w['min'])} درجه"),
        (1246, 1364, f"سرعت باد: {w['wind']} کیلومتر بر ساعت"),
        (1396, 1514, f"رطوبت: {w['humidity']} درصد")
    ]
    f_bar = get_font(44)
    for y1, y2, text in bars:
        draw.rounded_rectangle([98, y1, 924, y2], radius=28, fill=(88, 84, 104, 248), outline=(190, 185, 200, 255), width=3)
        draw_rtl_centered(draw, y1 + 28, text, f_bar, (255, 255, 255), 1024)

    return Image.alpha_composite(base, overlay)


def fetch_logo_circle(team_name_fa, fallback_url, diameter=154):
    url = fallback_url
    for k, v in IRAN_LOGOS.items():
        if k in team_name_fa:
            url = v
            break
    cache_key = f"{url}_{diameter}"
    if cache_key in LOGO_RAM:
        return LOGO_RAM[cache_key]

    logo_bg = Image.new("RGBA", (diameter, diameter), (255, 255, 255, 255))
    if url:
        try:
            r = requests.get(url, headers=HEADERS, timeout=6)
            raw = Image.open(io.BytesIO(r.content)).convert("RGBA")
            raw.thumbnail((int(diameter * 0.82), int(diameter * 0.82)), Image.Resampling.LANCZOS)
            logo_bg.paste(raw, ((diameter - raw.width) // 2, (diameter - raw.height) // 2), raw)
        except Exception:
            pass
    mask = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter, diameter), fill=255)
    out = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    out.paste(logo_bg, (0, 0), mask)
    LOGO_RAM[cache_key] = out
    return out


def build_match_image(league_title, home_name, away_name, home_goals, away_goals, home_logo, away_logo, bottom_banner):
    base = TEMPLATES_RAM["t3"].copy()
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    draw.rounded_rectangle([230, 174, 794, 278], radius=50, fill=(150, 22, 22, 250), outline=(230, 190, 110, 255), width=5)
    draw_rtl_centered(draw, 195, league_title, get_font(42), (255, 255, 255), 1024)

    draw.rounded_rectangle([340, 755, 684, 1005], radius=20, fill=(24, 43, 58, 250))
    draw_rtl_centered(draw, 775, f"{away_goals} - {home_goals}", get_font(120), (242, 205, 120), 1024)
    draw_rtl_centered(draw, 935, f"{home_name} | {away_name}", get_font(30), (210, 225, 240), 1024)

    draw.rounded_rectangle([108, 1114, 916, 1228], radius=26, fill=(22, 27, 36, 250), outline=(215, 180, 105, 255), width=4)
    draw_rtl_centered(draw, 1142, bottom_banner, get_font(38), (255, 255, 255), 1024)

    draw.rectangle([0, 1695, 1024, 1820], fill=(222, 192, 118, 255))
    draw.line([(0, 1695), (1024, 1695)], fill=(250, 230, 170, 255), width=4)
    draw_rtl_centered(draw, 1722, "گزارش زنده و نتایج فوتبال", get_font(48), (20, 20, 20), 1024)

    combined = Image.alpha_composite(base, overlay)
    left_circle = fetch_logo_circle(away_name, away_logo, 154)
    right_circle = fetch_logo_circle(home_name, home_logo, 154)
    combined.paste(left_circle, (228 - 77, 878 - 77), left_circle)
    combined.paste(right_circle, (796 - 77, 878 - 77), right_circle)
    return combined


# =====================================================================
# ۵. بروزرسانی لحظه‌ای اطلاعات و دسته‌بندی بازی‌ها بر اساس لیگ
# =====================================================================
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_morning_date": "", "owner_chat_id": "", "matches": {}}


def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_target_chat_id(state):
    return TELEGRAM_CHAT_ID or state.get("owner_chat_id", "")


def refresh_daily_data_cache():
    now_greg = jdatetime.datetime.now(TEHRAN_TZ).togregorian()
    date_ddmmyyyy = now_greg.strftime("%d-%m-%Y")

    # ۱. اوقات شرعی دقیق روز جاری
    try:
        url = f"https://api.aladhan.com/v1/timingsByCity/{date_ddmmyyyy}?city={CITY_NAME_EN}&country=Iran&method=7"
        t = requests.get(url, headers=HEADERS, timeout=8).json()["data"]["timings"]
        clean_time = lambda s: re.sub(r"\s*\(.*?\)", "", s).strip()[:5]
        CACHE["prayers"] = (
            clean_time(t["Fajr"]),
            clean_time(t["Sunrise"]),
            clean_time(t["Dhuhr"]),
            clean_time(t["Maghrib"])
        )
    except Exception:
        pass

    # ۲. وضعیت آب و هوای لحظه‌ای
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={CITY_LAT}&longitude={CITY_LON}"
            "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
            "&daily=temperature_2m_max,temperature_2m_min&timezone=Asia%2FTehran"
        )
        d = requests.get(url, headers=HEADERS, timeout=8).json()
        cur, daily = d["current"], d["daily"]
        code = cur.get("weather_code", 0)
        desc_map = {
            0: "آسمان صاف", 1: "غالباً صاف", 2: "نیمه‌ابری", 3: "ابری",
            45: "مه‌آلود", 48: "مه‌آلود", 51: "نم‌نم باران", 61: "بارش خفیف باران",
            63: "بارانی", 65: "بارش شدید باران", 71: "بارش برف", 80: "رگبار باران", 95: "رعد و برق"
        }
        CACHE["weather"] = {
            "temp": round(cur["temperature_2m"], 1),
            "temp_int": round(cur["temperature_2m"]),
            "max": round(daily["temperature_2m_max"][0], 1),
            "min": round(daily["temperature_2m_min"][0], 1),
            "wind": round(cur["wind_speed_10m"]),
            "humidity": round(cur["relative_humidity_2m"]),
            "desc": desc_map.get(code, "آسمان صاف و معتدل")
        }
    except Exception:
        pass

    # ۳. قیمت زنده دلار، طلا و سکه (ریال)
    try:
        ts = int(time.time())
        r_json = requests.get(f"https://call1.tgju.org/ajax.json?rev={ts}", headers=HEADERS, timeout=8).json()
        cur_m = r_json.get("current", {})
        usd = cur_m.get("price_dollar_rl", {}).get("p")
        gold = cur_m.get("geram18", {}).get("p")
        coin = cur_m.get("sekee", {}).get("p")
        if usd and gold and coin:
            CACHE["market"] = (usd, gold, coin)
            return
    except Exception:
        pass

    try:
        html = requests.get(f"https://www.tgju.org/?t={int(time.time())}", headers=HEADERS, timeout=10).text
        def extract_price(slug):
            p1 = rf'data-market-row="{slug}"[^>]*data-price="([\d,]+)"'
            m1 = re.search(p1, html)
            if m1:
                return m1.group(1)
            p2 = rf'data-market-row="{slug}"[^>]*>.*?<td class="nf"[^>]*>([\d,]+)</td>'
            m2 = re.search(p2, html, re.DOTALL)
            return m2.group(1) if m2 else None
        usd, gold, coin = extract_price("price_dollar_rl"), extract_price("geram18"), extract_price("sekee")
        if usd and gold and coin:
            CACHE["market"] = (usd, gold, coin)
    except Exception:
        pass


def register_and_check_match(state, matches_mem, lg_key, match_id, league_fa, is_iran, h_name, a_name, h_g, a_g, h_logo, a_logo, is_live, is_finished, minute_str="", allow_auto_alert=True):
    if is_live:
        status_emoji = "🔴"
        status_label = f"زنده (دقیقه {to_fa_digits(minute_str)})" if minute_str else "زنده"
        header_prefix = "زنده"
        line_str = f"🔴 زنده ({to_fa_digits(minute_str)}') | {h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}" if minute_str else f"🔴 زنده | {h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}"
        CACHE["leagues"][lg_key]["has_live"] = True
    elif is_finished:
        status_emoji = "🏁"
        status_label = "پایان بازی"
        header_prefix = "نتیجه نهایی"
        line_str = f"🏁 پایان | {h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}"
    else:
        status_emoji = "⏳"
        status_label = f"در انتظار شروع ({to_fa_digits(minute_str)})" if minute_str else "در انتظار شروع"
        header_prefix = "برنامه بازی"
        line_str = f"⏳ {to_fa_digits(minute_str)} | {h_name} - {a_name}" if minute_str else f"⏳ در انتظار شروع | {h_name} - {a_name}"

    CACHE["matches_by_id"][match_id] = {
        "status_emoji": status_emoji,
        "status_label": status_label,
        "league_title": f"{header_prefix} | {league_fa}",
        "league_fa": league_fa,
        "h_name": h_name,
        "a_name": a_name,
        "h_g": h_g,
        "a_g": a_g,
        "h_logo": h_logo,
        "a_logo": a_logo,
        "banner": f"{status_label} | {h_name} {h_g} - {a_g} {a_name}"
    }
    CACHE["leagues"][lg_key]["lines"].append(line_str)
    CACHE["leagues"][lg_key]["match_ids"].append(match_id)

    if not allow_auto_alert:
        return

    if match_id not in matches_mem:
        matches_mem[match_id] = {"h": h_g, "a": a_g, "ft": is_finished}
        return

    prev = matches_mem[match_id]
    target_chat = get_target_chat_id(state)

    # ارسال خودکار عکس برای هر گل در لیگ برتر و جام حذفی ایران
    if is_iran and is_live and (h_g > prev["h"] or a_g > prev["a"]):
        scorer = h_name if h_g > prev["h"] else a_name
        min_txt = f"در دقیقه {minute_str}" if minute_str else ""
        banner = f"انفجار در ورزشگاه! گل برای {scorer} {min_txt}".strip()
        if target_chat:
            img = build_match_image(f"زنده | {league_fa}", h_name, a_name, h_g, a_g, h_logo, a_logo, banner)
            send_telegram_photo(target_chat, img, f"🔴 گل برای {scorer}!\n{h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}")
        prev["h"], prev["a"] = h_g, a_g

    # ارسال خودکار عکس پایان بازی برای تمام لیگ‌ها
    if is_finished and not prev["ft"]:
        banner = f"پایان بازی | {h_name} {h_g} - {a_g} {a_name}"
        if target_chat:
            img = build_match_image(f"نتیجه نهایی | {league_fa}", h_name, a_name, h_g, a_g, h_logo, a_logo, banner)
            send_telegram_photo(target_chat, img, f"🏁 پایان بازی ({league_fa})\n{h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}")
        prev["ft"] = True
        prev["h"], prev["a"] = h_g, a_g


def check_all_football_free(state):
    matches_mem = state.setdefault("matches", {})
    now_greg = jdatetime.datetime.now(TEHRAN_TZ).togregorian()
    today_compact = now_greg.strftime("%Y%m%d")

    # پاکسازی لیست موقت هر لیگ پیش از بروزرسانی جدید
    for lg_key, lg_title in LEAGUE_CATEGORIES:
        CACHE["leagues"][lg_key] = {
            "title": lg_title,
            "lines": [],
            "match_ids": [],
            "has_live": False
        }

    # ۱. لیگ برتر ایران و جام حذفی (ابتدا امروز؛ اگر امروز بازی نبود، نزدیک‌ترین روز هفته جاری)
    for day_offset in [0, -1, 1, -2, 2, -3]:
        target_date = (now_greg + timedelta(days=day_offset)).strftime("%Y%m%d")
        is_today = (day_offset == 0)
        found_iran = False
        try:
            f_url = f"https://www.fotmob.com/api/matches?date={target_date}"
            f_leagues = requests.get(f_url, headers=HEADERS, timeout=10).json().get("leagues", [])
            for lg in f_leagues:
                lid = lg.get("primaryId")
                if lid not in (9090, 9384):
                    continue
                found_iran = True
                l_fa = "لیگ برتر ایران" if lid == 9090 else "جام حذفی ایران"
                for m in lg.get("matches", []):
                    mid = f"ir_{m['id']}"
                    st = m.get("status", {})
                    is_live = st.get("started", False) and not st.get("finished", False)
                    is_finished = st.get("finished", False)
                    minute_str = st.get("liveTime", {}).get("short", "").replace("'", "")

                    h_name = to_persian_team(m["home"]["name"])
                    a_name = to_persian_team(m["away"]["name"])
                    h_g, a_g = int(m["home"].get("score", 0) or 0), int(m["away"].get("score", 0) or 0)
                    h_logo = f"https://images.fotmob.com/image_resources/logo/teamlogo/{m['home']['id']}.png"
                    a_logo = f"https://images.fotmob.com/image_resources/logo/teamlogo/{m['away']['id']}.png"

                    register_and_check_match(
                        state, matches_mem, "lg_ir", mid, l_fa, True,
                        h_name, a_name, h_g, a_g, h_logo, a_logo,
                        is_live, is_finished, minute_str, allow_auto_alert=is_today
                    )
        except Exception:
            pass
        if found_iran:
            break

    # ۲. چهار لیگ معتبر اروپایی (لیگ برتر انگلیس، لالیگا، بوندسلیگا، لیگ قهرمانان اروپا)
    espn_Configs = [
        ("lg_eng", "eng.1", "لیگ برتر انگلیس"),
        ("lg_esp", "esp.1", "لالیگا اسپانیا"),
        ("lg_ger", "ger.1", "بوندسلیگا آلمان"),
        ("lg_ucl", "uefa.champions", "لیگ قهرمانان اروپا")
    ]
    for lg_key, code, l_fa in espn_Configs:
        try:
            # ابتدا بازی‌های روز جاری را بررسی می‌کنیم؛ اگر امروز بازی نبود، هفته جاری همان لیگ را می‌آوریم
            url_today = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={today_compact}"
            events = requests.get(url_today, headers=HEADERS, timeout=10).json().get("events", [])
            is_today_batch = True
            if not events:
                url_current = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard"
                events = requests.get(url_current, headers=HEADERS, timeout=10).json().get("events", [])
                is_today_batch = False

            for ev in events[:10]:
                mid = f"eu_{ev['id']}"
                comp = ev["competitions"][0]
                state_type = ev["status"]["type"]["state"]  # pre, in, post
                is_live = (state_type == "in")
                is_finished = (state_type == "post")
                minute_str = ev["status"]["type"].get("shortDetail", "")

                home = next(c for c in comp["competitors"] if c["homeAway"] == "home")
                away = next(c for c in comp["competitors"] if c["homeAway"] == "away")

                h_name = to_persian_team(home["team"]["displayName"])
                a_name = to_persian_team(away["team"]["displayName"])
                h_g, a_g = int(home.get("score", 0) or 0), int(away.get("score", 0) or 0)
                h_logo, a_logo = home["team"].get("logo", ""), away["team"].get("logo", "")

                register_and_check_match(
                    state, matches_mem, lg_key, mid, l_fa, False,
                    h_name, a_name, h_g, a_g, h_logo, a_logo,
                    is_live, is_finished, minute_str, allow_auto_alert=is_today_batch
                )
        except Exception:
            pass


def background_worker(state):
    """اجرای ۲۴ ساعته در تمام روزهای هفته: بروزرسانی هر ۶۰ ثانیه + ارسال خودکار راس ساعت ۷ صبح"""
    while True:
        try:
            refresh_daily_data_cache()
            check_all_football_free(state)

            now_tehran = jdatetime.datetime.now(TEHRAN_TZ)
            today_gregorian = now_tehran.togregorian().strftime("%Y-%m-%d")
            target_chat = get_target_chat_id(state)

            if now_tehran.hour == 7 and state.get("last_morning_date") != today_gregorian and target_chat:
                refresh_daily_data_cache()
                send_telegram_photo(target_chat, build_morning_image(), "☀️ صبح بخیر | تقویم، اوقات شرعی و نبض بازار امروز")
                send_telegram_photo(target_chat, build_weather_image(), "🌤 وضعیت آب و هوای امروز")
                state["last_morning_date"] = today_gregorian

            save_state(state)
        except Exception as e:
            print("Background worker error:", e)
        time.sleep(60)


# =====================================================================
# ۶. پاسخگویی فوری به منوی ربات، انتخاب لیگ و ساخت عکس بازی‌ها
# =====================================================================
def handle_user_request(chat_id, text):
    t = text.strip()
    if "صبح بخیر" in t or t == "/morning":
        img = build_morning_image()
        send_telegram_photo(chat_id, img, "☀️ صبح بخیر | تقویم، اوقات شرعی و نبض بازار لحظه‌ای")
    elif "وضعیت هوا" in t or "آب و هوا" in t or t == "/weather":
        img = build_weather_image()
        send_telegram_photo(chat_id, img, "🌤 وضعیت لحظه‌ای آب و هوا")
    elif "نتایج زنده" in t or "فوتبال" in t or t == "/football":
        send_league_selection_question(chat_id)
    else:
        send_menu_keyboard(chat_id, "👇 لطفاً یکی از ۳ کلید موجود در منوی پایین صفحه را انتخاب کنید:")


def handle_callback_query(chat_id, message_id, cb_id, data):
    # ۱. کاربر یکی از ۵ لیگ را انتخاب کرده است
    if data.startswith("showlg_"):
        answer_callback(cb_id, "⚽️ دریافت لیست بازی‌های لیگ...")
        lg_key = data.replace("showlg_", "", 1)
        send_specific_league_matches(chat_id, lg_key, message_id=message_id)

    # ۲. کاربر دکمه «بازگشت به انتخاب لیگ‌ها» را زده است
    elif data == "back_leagues":
        answer_callback(cb_id)
        send_league_selection_question(chat_id, message_id=message_id)

    # ۳. کاربر روی یک بازی زده تا عکس گرافیکی آن ساخته و ارسال شود
    elif data.startswith("mkimg_"):
        answer_callback(cb_id, "🎨 در حال ساخت و ارسال عکس بازی...")
        mid = data.replace("mkimg_", "", 1)
        m = CACHE["matches_by_id"].get(mid)
        if m:
            img = build_match_image(
                m["league_title"], m["h_name"], m["a_name"],
                m["h_g"], m["a_g"], m["h_logo"], m["a_logo"], m["banner"]
            )
            caption = f"{m['status_emoji']} {m['status_label']} ({m['league_fa']})\n⚽️ {m['h_name']} {to_fa_digits(m['h_g'])} - {to_fa_digits(m['a_g'])} {m['a_name']}"
            send_telegram_photo(chat_id, img, caption)


if __name__ == "__main__":
    preload_templates()
    setup_bot_commands()
    state = load_state()

    refresh_daily_data_cache()
    check_all_football_free(state)

    target = get_target_chat_id(state)
    if target:
        send_menu_keyboard(target)

    bg_thread = threading.Thread(target=background_worker, args=(state,), daemon=True)
    bg_thread.start()

    start_ts = time.time()
    offset = 0
    while time.time() - start_ts < 19500:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            res = requests.get(url, params={"offset": offset, "timeout": 25}, timeout=30).json()
            for upd in res.get("result", []):
                offset = upd["update_id"] + 1

                if "message" in upd and "text" in upd["message"]:
                    cid = upd["message"]["chat"]["id"]
                    txt = upd["message"]["text"]
                    if not state.get("owner_chat_id"):
                        state["owner_chat_id"] = cid
                        save_state(state)
                    threading.Thread(target=handle_user_request, args=(cid, txt), daemon=True).start()

                elif "callback_query" in upd:
                    cb = upd["callback_query"]
                    cb_id = cb["id"]
                    cid = cb["message"]["chat"]["id"]
                    mid = cb["message"]["message_id"]
                    data = cb.get("data", "")
                    threading.Thread(target=handle_callback_query, args=(cid, mid, cb_id, data), daemon=True).start()
        except Exception:
            time.sleep(2)
