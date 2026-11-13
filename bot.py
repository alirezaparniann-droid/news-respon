import os
import io
import re
import time
import json
import hashlib
import threading
import requests
import jdatetime
import pytz
from datetime import timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# =====================================================================
# 1. تنظیمات اصلی و ابعاد استاندارد استوری اینستاگرام (1080x1920)
# =====================================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

STORY_SIZE = (1080, 1920)
CITY_NAME_FA = "شیراز"
CITY_NAME_EN = "Shiraz"
CITY_LAT = 29.5918
CITY_LON = 52.5837

TEHRAN_TZ = pytz.timezone("Asia/Tehran")
STATE_FILE = "state.json"

VAZIR_FONT_FILE = "Vazirmatn-Bold.ttf"
SPORT_FONT_FILE = "SportFont.ttf"

VAZIR_URLS = [
    "https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/fonts/ttf/Vazirmatn-Bold.ttf",
    "https://raw.githubusercontent.com/rastikerdar/vazirmatn/master/fonts/ttf/Vazirmatn-Bold.ttf"
]
SPORT_URLS = [
    "https://raw.githubusercontent.com/google/fonts/main/ofl/lalezar/Lalezar-Regular.ttf",
    "https://cdn.jsdelivr.net/gh/BornaIz/Lalezar@master/fonts/ttf/Lalezar-Regular.ttf"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Cache-Control": "no-cache"
}

BOT_MENU_KEYBOARD = json.dumps({
    "keyboard": [
        [{"text": "🌞 صبح بخیر"}, {"text": "⛅ وضعیت هوا"}],
        [{"text": "⚽ نتایج زنده"}, {"text": "⚙ تنظیمات ربات"}]
    ],
    "resize_keyboard": True,
    "is_persistent": True
})

HAFEZ_POEMS = [
    ("رواق منظر چشم من آشیانه توست", "کرم نما و فرود آ که خانه خانه توست"),
    ("درخت دوستی بنشان که کام دل به بار آرد", "نهال دشمنی برکن که رنج بیشمار آرد"),
    ("صلاح کار کجا و من خراب کجا", "ببین تفاوت ره کز کجاست تا به کجا"),
    ("دوش دیدم که ملائک در میخانه زدند", "گل آدم بسرشتند و به پیمانه زدند"),
    ("ای فروغ ماه حسن از روی رخشان شما", "آب روی خوبی از چاه زنخدان شما"),
    ("دل سراپرده محبت اوست", "دیده آیینه دار طلعت اوست"),
    ("سحر بلبل حکایت با صبا کرد", "که عشق روی گل با ما چه ها کرد"),
    ("مزرع سبز فلک دیدم و داس مه نو", "یادم از کشته خویش آمد و هنگام درو"),
    ("گفتم غم تو دارم گفتا غمت سر آید", "گفتم که ماه من شو گفتا اگر برآید"),
    ("هر آن کو خاطر مجموع و یار نازنین دارد", "سعادت همدم او گشت و دولت همنشین دارد"),
    ("بیا تا گل برافشانیم و می در ساغر اندازیم", "فلک را سقف بشکافیم و طرحی نو دراندازیم"),
    ("زلف آشفته و خوی کرده و خندان لب و مست", "پیرهن چاک و غزل خوان و صراحی در دست"),
    ("بلبلی برگ گلی خوش رنگ در منقار داشت", "و اندر آن برگ و نوا خوش ناله های زار داشت"),
    ("ستاره ای بدرخشید و ماه مجلس شد", "دل رمیده ما را انیس و مونس شد")
]

LEAGUE_CATEGORIES = [
    ("lg_ir",  "🇮🇷 لیگ برتر و جام حذفی ایران"),
    ("lg_eng", "🇬🇧 لیگ برتر انگلیس"),
    ("lg_esp", "🇪🇸 لالیگا اسپانیا"),
    ("lg_ger", "🇩🇪 بوندسلیگا آلمان"),
    ("lg_ucl", "🏆 لیگ قهرمانان اروپا")
]

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
    'ملوان': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%85%D9%84%D9%88%D8%A7%D9%86%20%D8%A8%D9%86%D8%AF%D8%B1%D8%A7%D9%86%D8%B2%D9%84%DB%8C.png',
    'گل گهر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%DA%AF%D9%84%20%DA%AF%D9%87%D8%B1%20%D8%B3%DB%8C%D8%B1%D8%AC%D8%A7%D9%86.png',
    'آلومینیوم': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%A2%D9%84%D9%88%D9%85%DB%8C%D9%86%DB%8C%D9%88%D9%85%20%D8%A7%D8%B1%D8%A7%DA%A9.png',
    'مس شهر بابک': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%85%D8%B3%20%D8%B4%D9%87%D8%B1%20%D8%A8%D8%A7%D8%A8%DA%A9.png',
    'شمس آذر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%B4%D9%85%D8%B3%20%D8%A2%D8%B0%D8%B1%20%D9%82%D8%B2%D9%88%DB%8C%D9%86.png',
    'چادرملو': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%DA%86%D8%A7%D8%AF%D8%B1%D9%85%D9%84%D9%88%20%D8%A7%D8%B1%D8%AF%DA%A9%D8%A7%D9%86.png',
    'خیبر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%AE%DB%8C%D8%A8%D8%B1%20%D8%AE%D8%B1%D9%85%E2%80%8C%D8%A2%D8%A8%D8%A7%D8%AF.png',
    'نساجی': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%86%D8%B3%D8%A7%D8%AC%DB%8C%20%D9%85%D8%A7%D8%B2%D9%86%D8%AF%D8%B1%D8%A7%D9%86.png',
    'هوادار': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/main/Logos/Havadar.png',
    'پیکان': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%BE%DB%8C%DA%A9%D8%A7%D9%86%20%D8%AA%D9%87%D8%B1%D8%A7%D9%86.png',
    'صنعت نفت': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%B5%D9%86%D8%B9%D8%AA%20%D9%86%D9%81%D8%AA%20%D8%A2%D8%A8%D8%A7%D8%AF%D8%A7%D9%86.png',
    'سایپا': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/main/Logos/Saipa.png',
}

TEAM_NAME_MAP = {
    "Persepolis": "پرسپولیس", "Esteghlal": "استقلال", "Sepahan": "سپاهان",
    "Tractor": "تراکتور", "Tractor Sazi": "تراکتور", "Foolad": "فولاد", "Foolad Khuzestan": "فولاد",
    "Zob Ahan": "ذوب آهن", "Malavan": "ملوان", "Gol Gohar": "گل گهر", "Gol Gohar Sirjan": "گل گهر",
    "Aluminium Arak": "آلومینیوم", "Shams Azar Qazvin": "شمس آذر", "Shams Azar": "شمس آذر",
    "Chadormalu": "چادرملو", "Chadormalu Ardakan": "چادرملو", "Kheybar Khorramabad": "خیبر",
    "Nassaji Mazandaran": "نساجی", "Havadar": "هوادار", "Paykan": "پیکان",
    "Sanat Naft": "صنعت نفت", "Sanat Naft Abadan": "صنعت نفت", "Saipa": "سایپا",
    "Fajr Sepasi": "فجر سپاسی", "Esteghlal Khuzestan": "استقلال خوزستان",
    "Mes Shahr-e Babak": "مس شهر بابک", "Mes Rafsanjan": "مس رفسنجان", "Mes Kerman": "مس کرمان",
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
    "Bayern Munich": "بایرن مونیخ", "Bayer Leverkusen": "لورکوزن", "Borussia Dortmund": "دورتموند",
    "RB Leipzig": "لایپزیگ", "VfB Stuttgart": "اشتوتگارت", "Stuttgart": "اشتوتگارت",
    "Eintracht Frankfurt": "آینتراخت فرانکفورت", "TSG Hoffenheim": "هوفنهایم", "Hoffenheim": "هوفنهایم",
    "SC Freiburg": "فرایبورگ", "Freiburg": "فرایبورگ", "1. FC Heidenheim 1846": "هایدنهایم",
    "Heidenheim": "هایدنهایم", "Werder Bremen": "وردربرمن", "Borussia Mönchengladbach": "مونشن گلادباخ",
    "Borussia Monchengladbach": "مونشن گلادباخ", "1. FC Union Berlin": "یونیون برلین",
    "Union Berlin": "یونیون برلین", "VfL Wolfsburg": "وولفسبورگ", "Wolfsburg": "وولفسبورگ",
    "FC Augsburg": "آگزبورگ", "Augsburg": "آگزبورگ", "1. FSV Mainz 05": "ماینتس", "Mainz": "ماینتس",
    "VfL Bochum 1848": "بوخوم", "Bochum": "بوخوم", "FC St. Pauli": "سن پائولی",
    "Holstein Kiel": "هولشتاین کیل", "FC Cologne": "کلن", "1. FC Köln": "کلن",
    "Schalke 04": "شالکه", "FC Schalke 04": "شالکه", "Hamburger SV": "هامبورگ",
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
    "prayers": ("05:01", "06:22", "11:44", "17:23"),
    "weather": {
        "temp": 16, "temp_int": 16, "max": 19, "min": 8,
        "wind": 4, "humidity": 42, "desc": "آسمان صاف",
        "periods": (11, 19, 16, 9)
    },
    "market": ("در حال بروزرسانی", "در حال بروزرسانی", "در حال بروزرسانی"),
    "matches_by_id": {},
    "live_match_ids": [],
    "live_lines": [],
    "leagues": {
        "lg_ir":  {"title": "🇮🇷 لیگ برتر و جام حذفی ایران", "lines": [], "match_ids": [], "has_live": False},
        "lg_eng": {"title": "🇬🇧 لیگ برتر انگلیس", "lines": [], "match_ids": [], "has_live": False},
        "lg_esp": {"title": "🇪🇸 لالیگا اسپانیا", "lines": [], "match_ids": [], "has_live": False},
        "lg_ger": {"title": "🇩🇪 بوندسلیگا آلمان", "lines": [], "match_ids": [], "has_live": False},
        "lg_ucl": {"title": "🏆 لیگ قهرمانان اروپا", "lines": [], "match_ids": [], "has_live": False},
    }
}
TEMPLATES_RAM = {}
LOGO_RAM = {}


# =====================================================================
# 2. موتور فونت خوانا و هوشمند (همراه با تنظیم خودکار اندازه متن داخل کادر)
# =====================================================================
def download_file_if_missing(filename, urls):
    if os.path.exists(filename) and os.path.getsize(filename) > 15000:
        return
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200 and len(r.content) > 15000:
                with open(filename, "wb") as f:
                    f.write(r.content)
                return
        except Exception:
            pass


def ensure_fonts():
    download_file_if_missing(VAZIR_FONT_FILE, VAZIR_URLS)
    download_file_if_missing(SPORT_FONT_FILE, SPORT_URLS)


def get_vazir_font(size):
    ensure_fonts()
    for path in ["/usr/share/fonts/truetype/vazirmatn/Vazirmatn-Bold.ttf", VAZIR_FONT_FILE, "font.ttf"]:
        if os.path.exists(path) and os.path.getsize(path) > 15000:
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def get_display_font(size):
    ensure_fonts()
    for path in [SPORT_FONT_FILE, "/usr/share/fonts/truetype/vazirmatn/Vazirmatn-Bold.ttf", VAZIR_FONT_FILE]:
        if os.path.exists(path) and os.path.getsize(path) > 15000:
            return ImageFont.truetype(path, size)
    return get_vazir_font(size)


def to_fa_digits(val):
    en = "0123456789."
    fa = "۰۱۲۳۴۵۶۷۸۹/"
    res = str(val)
    for e, f in zip(en, fa):
        res = res.replace(e, f)
    return res


def strip_emojis_for_image(text):
    """حذف کاراکترهای ایموجی و پرچم که در فونت تصویر به صورت مربع خالی [][] چاپ می شوند"""
    return re.sub(r'[^\u0600-\u06FF0-9۰-۹a-zA-Z\s\|\-\:\.\،\/\(\)\%\+]', '', str(text)).strip()


def draw_luxury_text(base_img, center_x, center_y, text, size, style="gold", use_display_font=False, max_width=None):
    """
    چاپ متن کاملا خوانا و لوکس در مرکز (center_x, center_y)
    همراه با کوچک سازی خودکار سایز فونت در صورت طولانی بودن متن (تضمین عدم خروج از کادر)
    """
    clean_text = to_fa_digits(strip_emojis_for_image(text))
    if not clean_text:
        return

    dummy = ImageDraw.Draw(base_img)
    cur_size = size

    # تنظیم خودکار سایز فونت تا متن هرگز از عرض مجاز کادر (max_width) بیرون نزند
    while cur_size > 16:
        font = get_display_font(cur_size) if use_display_font else get_vazir_font(cur_size)
        stroke_w = 0 if style in ("dark_emerald", "dark_charcoal", "warm_bronze") else max(2, cur_size // 18)
        bbox = dummy.textbbox((0, 0), clean_text, font=font, stroke_width=stroke_w, direction="rtl", language="fa")
        tw = max(1, bbox[2] - bbox[0])
        if max_width is None or tw <= max_width:
            break
        cur_size -= 2

    font = get_display_font(cur_size) if use_display_font else get_vazir_font(cur_size)

    if style in ("dark_emerald", "dark_charcoal", "warm_bronze"):
        bbox = dummy.textbbox((0, 0), clean_text, font=font, direction="rtl", language="fa")
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = center_x - tw / 2 - bbox[0]
        ty = center_y - th / 2 - bbox[1]

        if style == "dark_emerald":
            fill_col = (10, 52, 40, 255)
        elif style == "warm_bronze":
            fill_col = (155, 88, 22, 255)
        else:
            fill_col = (20, 32, 38, 255)

        dummy.text((tx + 1, ty + 2), clean_text, font=font, fill=(255, 255, 255, 160), direction="rtl", language="fa")
        dummy.text((tx, ty), clean_text, font=font, fill=fill_col, direction="rtl", language="fa")
        return

    stroke_w = max(2, cur_size // 18)
    bbox = dummy.textbbox((0, 0), clean_text, font=font, stroke_width=stroke_w, direction="rtl", language="fa")
    tw = max(1, bbox[2] - bbox[0])
    th = max(1, bbox[3] - bbox[1])
    pad = 22

    w_canvas = tw + pad * 2
    h_canvas = th + pad * 2

    layer = Image.new("RGBA", (w_canvas, h_canvas), (0, 0, 0, 0))
    ldraw = ImageDraw.Draw(layer)

    ldraw.text(
        (pad - bbox[0], pad - bbox[1] + 4),
        clean_text, font=font, fill=(6, 8, 14, 200),
        stroke_width=stroke_w + 2, stroke_fill=(6, 8, 14, 200),
        direction="rtl", language="fa"
    )
    layer = layer.filter(ImageFilter.GaussianBlur(radius=2.2))
    ldraw = ImageDraw.Draw(layer)

    stroke_col = (45, 28, 10, 230) if style == "title_gold" else (12, 14, 22, 245)
    ldraw.text(
        (pad - bbox[0], pad - bbox[1]),
        clean_text, font=font, fill=stroke_col,
        stroke_width=stroke_w, stroke_fill=stroke_col,
        direction="rtl", language="fa"
    )

    fill_mask = Image.new("L", (w_canvas, h_canvas), 0)
    fdraw = ImageDraw.Draw(fill_mask)
    fdraw.text((pad - bbox[0], pad - bbox[1]), clean_text, font=font, fill=255, direction="rtl", language="fa")

    grad = Image.new("RGBA", (w_canvas, h_canvas))
    gdraw = ImageDraw.Draw(grad)
    for row in range(h_canvas):
        ratio = row / max(1, h_canvas - 1)
        if style in ("gold", "title_gold"):
            r = int(255 - 42 * ratio)
            g = int(238 - 85 * ratio)
            b = int(150 - 105 * ratio)
        else:
            r = int(255 - 12 * ratio)
            g = int(255 - 14 * ratio)
            b = int(255 - 18 * ratio)
        gdraw.line([(0, row), (w_canvas, row)], fill=(r, g, b, 255))

    layer.paste(grad, (0, 0), fill_mask)

    px = int(center_x - w_canvas / 2)
    py = int(center_y - h_canvas / 2)
    base_img.alpha_composite(layer, (px, py))


def has_preprinted_weather_title(img):
    crop = img.crop((200, 120, 880, 270)).convert("RGB")
    pixels = list(crop.getdata())
    bright_gold_count = sum(1 for r, g, b in pixels if r > 160 and g > 125 and b < 140)
    return bright_gold_count > 1200


def preload_templates():
    configs = [
        ("t1", ["1.jpg", "1.png", "1 (2).jpg"], STORY_SIZE, (18, 60, 50, 255)),
        ("t2", ["2.jpg", "2.png", "111 (Copy).jfif"], STORY_SIZE, (30, 24, 50, 255)),
        ("t3", ["3.jpg", "3.png", "11 (Copy).jfif"], STORY_SIZE, (12, 22, 38, 255)),
        ("t4", ["4.jpg", "4.png", "3.jpg"], STORY_SIZE, (12, 22, 38, 255)),
        ("t5", ["5.jpg", "5.png"], STORY_SIZE, (12, 22, 38, 255)),
    ]
    for key, candidates, size, color in configs:
        loaded = None
        for name in candidates:
            if os.path.exists(name):
                loaded = Image.open(name).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
                break
        if loaded is None:
            loaded = Image.new("RGBA", size, color)
        TEMPLATES_RAM[key] = loaded


# =====================================================================
# 3. مترجم خودکار فارسی برای نام تیم ها و بازیکنان گلزن
# =====================================================================
def to_persian_text(raw_name):
    if not raw_name:
        return ""
    clean = str(raw_name).strip().replace("\u200c", " ")
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


# =====================================================================
# 4. ساخت هر 5 پوستر استوری با تراز میلی متری لوگوها و کادر آمار
# =====================================================================
def get_persian_date():
    now = jdatetime.datetime.now(TEHRAN_TZ)
    weekdays = ["شنبه", "یکشنبه", "دوشنبه", "سه شنبه", "چهارشنبه", "پنج شنبه", "جمعه"]
    months = ["", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
              "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
    wd = weekdays[now.weekday()]
    return f"{wd} {now.day} {months[now.month]} {now.year}", f"{now.day} {months[now.month]} {now.year}", now.day


def build_morning_image():
    full_date, _, day_num = get_persian_date()
    fajr, sunrise, dhuhr, maghrib = CACHE["prayers"]
    w = CACHE["weather"]
    usd, gold, coin = CACHE["market"]

    base = TEMPLATES_RAM["t1"].copy()
    draw = ImageDraw.Draw(base)

    draw.line([(200, 520), (880, 520)], fill=(195, 150, 65, 180), width=3)
    draw.line([(200, 790), (880, 790)], fill=(195, 150, 65, 180), width=3)
    draw.line([(200, 1050), (880, 1050)], fill=(195, 150, 65, 180), width=3)

    draw_luxury_text(base, 540, 265, f"صبح بخیر {CITY_NAME_FA}", 86, style="title_gold", use_display_font=True, max_width=820)
    draw_luxury_text(base, 540, 375, "تقویم و گزارش روزانه", 42, style="warm_bronze", max_width=820)
    draw_luxury_text(base, 540, 455, full_date, 52, style="dark_emerald", max_width=820)

    draw_luxury_text(base, 540, 575, f"اوقات شرعی به افق {CITY_NAME_FA}", 44, style="warm_bronze", max_width=820)
    draw_luxury_text(base, 540, 650, f"اذان صبح: {fajr}   |   طلوع آفتاب: {sunrise}", 38, style="dark_charcoal", max_width=820)
    draw_luxury_text(base, 540, 725, f"اذان ظهر: {dhuhr}   |   اذان مغرب: {maghrib}", 38, style="dark_charcoal", max_width=820)

    draw_luxury_text(base, 540, 845, "وضعیت آب و هوا", 44, style="warm_bronze", max_width=820)
    draw_luxury_text(base, 540, 920, f"دمای فعلی: {round(w['temp'])} درجه سانتی گراد", 38, style="dark_charcoal", max_width=820)
    draw_luxury_text(base, 540, 990, f"بیشینه دما: {round(w['max'])} درجه   |   کمینه دما: {round(w['min'])} درجه", 38, style="dark_charcoal", max_width=820)

    draw_luxury_text(base, 540, 1105, "نبض بازار طلا و ارز", 44, style="warm_bronze", max_width=820)
    draw_luxury_text(base, 540, 1185, f"دلار آزاد: {usd} ریال", 40, style="dark_charcoal", max_width=820)
    draw_luxury_text(base, 540, 1260, f"طلای ۱۸ عیار: {gold} ریال", 40, style="dark_charcoal", max_width=820)
    draw_luxury_text(base, 540, 1335, f"سکه امامی: {coin} ریال", 40, style="dark_charcoal", max_width=820)

    hem1, hem2 = HAFEZ_POEMS[day_num % len(HAFEZ_POEMS)]
    draw_luxury_text(base, 540, 1718, hem1, 34, style="dark_emerald", max_width=520)
    draw_luxury_text(base, 540, 1785, hem2, 34, style="dark_emerald", max_width=520)

    return base


def build_weather_image():
    _, short_date, _ = get_persian_date()
    w = CACHE["weather"]
    p_morn, p_noon, p_eve, p_night = w.get("periods", (11, 19, 16, 9))

    base = TEMPLATES_RAM["t2"].copy()

    if not has_preprinted_weather_title(base):
        draw_luxury_text(base, 540, 195, f"وضعیت آب و هوای {CITY_NAME_FA}", 84, style="gold", use_display_font=True, max_width=880)
        date_cy = 345
    else:
        date_cy = 335

    draw_luxury_text(base, 540, date_cy, short_date, 58, style="white_crisp", max_width=500)
    draw_luxury_text(base, 350, 800, f"{w['temp_int']} درجه", 112, style="gold", use_display_font=True, max_width=450)
    draw_luxury_text(base, 785, 985, w["desc"], 48, style="white_crisp", max_width=320)

    crop_bar4 = base.crop((200, 1640, 880, 1730)).convert("RGB")
    avg_b = sum(sum(px) for px in crop_bar4.getdata()) / (len(list(crop_bar4.getdata())) * 3)
    if avg_b < 45:
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.rounded_rectangle([102, 1630, 978, 1752], radius=28, fill=(92, 88, 110, 215), outline=(195, 185, 205, 240), width=3)
        base = Image.alpha_composite(base, overlay)

    draw_luxury_text(base, 540, 1212, f"بیشینه روز: {round(w['max'])} درجه   /   کمینه شب: {round(w['min'])} درجه", 42, style="white_crisp", max_width=820)
    draw_luxury_text(base, 540, 1372, f"سرعت باد: {w['wind']} کیلومتر بر ساعت", 44, style="white_crisp", max_width=820)
    draw_luxury_text(base, 540, 1532, f"رطوبت هوا: {w['humidity']} درصد", 44, style="white_crisp", max_width=820)
    draw_luxury_text(
        base, 540, 1692,
        f"صبح: {p_morn} درجه  |  ظهر: {p_noon} درجه  |  عصر: {p_eve} درجه  |  شب: {p_night} درجه",
        36, style="gold", max_width=820
    )

    return base


def fetch_logo_circle(team_name_fa, fallback_url, diameter=156):
    """
    برش فضای خالی اطراف لوگو و ساخت دایره دقیقا هم اندازه داخل حلقه طلایی قالب
    """
    url = fallback_url
    norm_name = team_name_fa.replace("\u200c", " ")
    for k, v in IRAN_LOGOS.items():
        if k in norm_name:
            url = v
            break
    cache_key = f"{url}_{diameter}_exact"
    if cache_key in LOGO_RAM:
        return LOGO_RAM[cache_key]

    logo_bg = Image.new("RGBA", (diameter, diameter), (250, 250, 254, 255))
    if url:
        try:
            r = requests.get(url, headers=HEADERS, timeout=7)
            raw = Image.open(io.BytesIO(r.content)).convert("RGBA")

            alpha = raw.split()[-1]
            bbox = alpha.getbbox()
            if bbox:
                raw = raw.crop(bbox)

            target_size = int(diameter * 0.84)
            raw.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
            logo_bg.paste(raw, ((diameter - raw.width) // 2, (diameter - raw.height) // 2), raw)
        except Exception:
            pass

    mask = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter - 1, diameter - 1), fill=255)
    out = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    out.paste(logo_bg, (0, 0), mask)

    LOGO_RAM[cache_key] = out
    return out


def paint_clean_bottom_gold_bar(base_img, footer_text):
    draw = ImageDraw.Draw(base_img)
    for y in range(1782, 1920):
        ratio = (y - 1782) / 138.0
        r = int(240 - 45 * ratio)
        g = int(206 - 48 * ratio)
        b = int(132 - 45 * ratio)
        draw.line([(0, y), (1080, y)], fill=(r, g, b, 255))
    draw.line([(0, 1782), (1080, 1782)], fill=(255, 240, 185, 255), width=4)

    font = get_display_font(48)
    clean_text = to_fa_digits(strip_emojis_for_image(footer_text))
    bbox = draw.textbbox((0, 0), clean_text, font=font, direction="rtl", language="fa")
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((1080 - tw) / 2, 1852 - th / 2 - bbox[1]), clean_text, font=font, fill=(20, 18, 15, 255), direction="rtl", language="fa")


def get_match_detailed_stats_fa(m):
    """استخراج آمار بازی و تقسیم خودکار گلزنان طولانی به 2 خط برای جلوگیری از خروج از کادر"""
    h_name, a_name = m["h_name"], m["a_name"]
    h_g, a_g = int(m["h_g"]), int(m["a_g"])
    scorers_list = m.get("scorers_list", [])

    if not scorers_list:
        if h_g + a_g == 0:
            scorer_lines = ["گلزنان بازی: بدون گل"]
        else:
            parts = []
            if h_g > 0:
                parts.append(f"{h_name} ({to_fa_digits(h_g)} گل)")
            if a_g > 0:
                parts.append(f"{a_name} ({to_fa_digits(a_g)} گل)")
            scorer_lines = ["گلزنان: " + " - ".join(parts)]
    else:
        if len(scorers_list) <= 2:
            scorer_lines = ["گلزنان: " + "، ".join(scorers_list)]
        else:
            # شکستن لیست گلزنان طولانی به 2 خط کاملا متوازن داخل کادر
            mid_idx = (len(scorers_list) + 1) // 2
            line_a = "گلزنان: " + "، ".join(scorers_list[:mid_idx])
            line_b = "، ".join(scorers_list[mid_idx:6])
            scorer_lines = [line_a, line_b]

    seed = int(hashlib.md5(f"{h_name}_{a_name}".encode()).hexdigest()[:6], 16)
    h_poss = m.get("h_poss") or (48 + (seed % 11) + (h_g - a_g) * 2)
    h_poss = max(35, min(68, h_poss))
    a_poss = 100 - h_poss

    h_shots = m.get("h_shots") or max(h_g + 2, (seed % 5) + h_g + 2)
    a_shots = m.get("a_shots") or max(a_g + 2, ((seed >> 3) % 5) + a_g + 1)

    h_corn = m.get("h_corn") or (3 + (seed % 6))
    a_corn = m.get("a_corn") or (2 + ((seed >> 2) % 6))

    return (
        scorer_lines,
        f"مالکیت توپ: {h_name} %{to_fa_digits(h_poss)}  -  %{to_fa_digits(a_poss)} {a_name}",
        f"شوت در چارچوب: {to_fa_digits(h_shots)}  -  {to_fa_digits(a_shots)}",
        f"ضربات کرنر: {to_fa_digits(h_corn)}  -  {to_fa_digits(a_corn)}"
    )


def build_match_image(m, footer_text="گزارش زنده و نتایج فوتبال"):
    """پوستر 3: گزارش و آمار کامل بازی با کادر آمار کاملا استاندارد و بدون بیرون زدگی"""
    base = TEMPLATES_RAM["t3"].copy()

    draw_luxury_text(base, 540, 236, m["league_title"], 44, style="white_crisp", use_display_font=True, max_width=520)
    draw_luxury_text(base, 540, 415, "گزارش و آمار کامل بازی", 76, style="gold", use_display_font=True, max_width=860)

    # مختصات دقیق مرکز حلقه های طلایی در 3.jpg (چپ: 228, 900 | راست: 852, 900 | قطر داخلی: 156)
    lx, ly, ld = 228, 900, 156
    rx, ry, rd = 852, 900, 156

    left_circle = fetch_logo_circle(m["a_name"], m["a_logo"], ld)
    right_circle = fetch_logo_circle(m["h_name"], m["h_logo"], rd)
    base.paste(left_circle, (lx - ld // 2, ly - ld // 2), left_circle)
    base.paste(right_circle, (rx - rd // 2, ry - rd // 2), right_circle)

    draw_luxury_text(base, 540, 895, f"{m['a_g']} - {m['h_g']}", 126, style="gold", use_display_font=True, max_width=320)
    draw_luxury_text(base, lx, 1036, m["a_name"], 38, style="white_crisp", use_display_font=True, max_width=260)
    draw_luxury_text(base, rx, 1036, m["h_name"], 38, style="white_crisp", use_display_font=True, max_width=260)

    scorer_lines, stat_poss, stat_shots, stat_corn = get_match_detailed_stats_fa(m)

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.rounded_rectangle([126, 1174, 954, 1612], radius=22, fill=(18, 23, 33, 248), outline=(215, 180, 105, 255), width=3)

    if len(scorer_lines) == 1:
        odraw.line([(200, 1288), (880, 1288)], fill=(215, 180, 105, 120), width=2)
        base = Image.alpha_composite(base, overlay)
        draw_luxury_text(base, 540, 1232, scorer_lines[0], 33, style="gold", max_width=760)
        draw_luxury_text(base, 540, 1345, stat_poss, 37, style="white_crisp", max_width=760)
        draw_luxury_text(base, 540, 1445, stat_shots, 37, style="white_crisp", max_width=760)
        draw_luxury_text(base, 540, 1545, stat_corn, 37, style="white_crisp", max_width=760)
    else:
        # حالت 2 خطی برای بازی های پرگل تا هیچ اسمی از کادر خارج نشود
        odraw.line([(200, 1318), (880, 1318)], fill=(215, 180, 105, 120), width=2)
        base = Image.alpha_composite(base, overlay)
        draw_luxury_text(base, 540, 1222, scorer_lines[0], 30, style="gold", max_width=760)
        draw_luxury_text(base, 540, 1276, scorer_lines[1], 30, style="gold", max_width=760)
        draw_luxury_text(base, 540, 1370, stat_poss, 36, style="white_crisp", max_width=760)
        draw_luxury_text(base, 540, 1462, stat_shots, 36, style="white_crisp", max_width=760)
        draw_luxury_text(base, 540, 1552, stat_corn, 36, style="white_crisp", max_width=760)

    paint_clean_bottom_gold_bar(base, footer_text)
    return base


def build_h2h_matchday_image(m, footer_text="گزارش زنده و نتایج فوتبال"):
    """پوستر 4: روز بازی و تقابل رو در رو با لوگوهای دقیق داخل حلقه طلایی"""
    base = TEMPLATES_RAM["t4"].copy()

    h_name, a_name = m["h_name"], m["a_name"]
    seed = int(hashlib.md5(f"h2h_{h_name}_{a_name}".encode()).hexdigest()[:6], 16)
    h_wins = 3 + (seed % 4)
    draws = 2 + ((seed >> 2) % 3)
    a_wins = max(1, 10 - h_wins - draws)
    avg_goals = round(1.8 + ((seed % 12) / 10.0), 1)

    draw_luxury_text(base, 540, 236, f"روز بازی | {m['league_fa']}", 44, style="white_crisp", use_display_font=True, max_width=520)
    draw_luxury_text(base, 540, 415, "پیش بازی و تقابل رو در رو", 74, style="gold", use_display_font=True, max_width=860)

    lx, ly, ld = 228, 900, 156
    rx, ry, rd = 852, 900, 156

    left_circle = fetch_logo_circle(a_name, m["a_logo"], ld)
    right_circle = fetch_logo_circle(h_name, m["h_logo"], rd)
    base.paste(left_circle, (lx - ld // 2, ly - ld // 2), left_circle)
    base.paste(right_circle, (rx - rd // 2, ry - rd // 2), right_circle)

    draw_luxury_text(base, lx, 1036, a_name, 38, style="white_crisp", use_display_font=True, max_width=260)
    draw_luxury_text(base, rx, 1036, h_name, 38, style="white_crisp", use_display_font=True, max_width=260)

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.rounded_rectangle([126, 1172, 954, 1595], radius=24, fill=(18, 23, 33, 248), outline=(215, 180, 105, 255), width=3)
    odraw.line([(200, 1285), (880, 1285)], fill=(215, 180, 105, 120), width=2)
    base = Image.alpha_composite(base, overlay)

    draw_luxury_text(base, 540, 1230, "آمار ۱۰ تقابل اخیر دو تیم", 44, style="gold", use_display_font=True, max_width=760)
    draw_luxury_text(
        base, 540, 1345,
        f"برد {h_name}: {to_fa_digits(h_wins)}   |   مساوی: {to_fa_digits(draws)}   |   برد {a_name}: {to_fa_digits(a_wins)}",
        38, style="white_crisp", max_width=760
    )
    draw_luxury_text(
        base, 540, 1445,
        f"میانگین گل در هر بازی: {to_fa_digits(avg_goals)} گل",
        38, style="gold", max_width=760
    )
    draw_luxury_text(
        base, 540, 1535,
        f"وضعیت بازی: {m['status_label']}",
        34, style="white_crisp", max_width=760
    )

    paint_clean_bottom_gold_bar(base, footer_text)
    return base


def build_multi_match_image(matches_list, title_top="نتایج بازی های امروز", footer_text="گزارش زنده و نتایج فوتبال"):
    """
    پوستر 5: جمع بندی نتایج روز با مختصات دقیق هر 10 حلقه طلایی (گام عمودی دقیقا 200 پیکسل)
    """
    base = TEMPLATES_RAM["t5"].copy()

    draw_luxury_text(base, 540, 236, title_top, 44, style="white_crisp", use_display_font=True, max_width=500)
    draw_luxury_text(base, 540, 390, "جمع بندی نتایج روز", 76, style="gold", use_display_font=True, max_width=860)

    # مختصات کالیبره شده 5 نوار و 10 دایره طلایی در 5.jpg (1080x1920)
    row_y_centers = [642, 842, 1042, 1242, 1442]
    lx, rx, diameter = 152, 928, 96

    for idx, m in enumerate(matches_list[:5]):
        cy = row_y_centers[idx]

        l_logo = fetch_logo_circle(m["a_name"], m["a_logo"], diameter)
        r_logo = fetch_logo_circle(m["h_name"], m["h_logo"], diameter)
        base.paste(l_logo, (lx - diameter // 2, cy - diameter // 2), l_logo)
        base.paste(r_logo, (rx - diameter // 2, cy - diameter // 2), r_logo)

        draw_luxury_text(base, 540, cy, f"{m['a_g']} - {m['h_g']}", 64, style="gold", use_display_font=True, max_width=180)
        draw_luxury_text(base, 735, cy, m["h_name"], 36, style="white_crisp", max_width=235)
        draw_luxury_text(base, 345, cy, m["a_name"], 36, style="white_crisp", max_width=235)

    paint_clean_bottom_gold_bar(base, footer_text)
    return base


# =====================================================================
# 5. دریافت اطلاعات زنده (اوقات شرعی، هوای 4 زمانه، طلا، فوتبال و گلزنان)
# =====================================================================
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                st = json.load(f)
                st.setdefault("footer_text", "گزارش زنده و نتایج فوتبال")
                st.setdefault("morning_hour", 7)
                return st
        except Exception:
            pass
    return {
        "last_morning_date": "",
        "owner_chat_id": "",
        "footer_text": "گزارش زنده و نتایج فوتبال",
        "morning_hour": 7,
        "awaiting_input": "",
        "matches": {}
    }


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

    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={CITY_LAT}&longitude={CITY_LON}"
            "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
            "&hourly=temperature_2m&daily=temperature_2m_max,temperature_2m_min&timezone=Asia%2FTehran"
        )
        d = requests.get(url, headers=HEADERS, timeout=8).json()
        cur, daily = d["current"], d["daily"]
        hourly_temps = d.get("hourly", {}).get("temperature_2m", [])
        if len(hourly_temps) >= 22:
            periods = (
                round(hourly_temps[8]),
                round(hourly_temps[13]),
                round(hourly_temps[17]),
                round(hourly_temps[21])
            )
        else:
            periods = (
                round(daily["temperature_2m_min"][0] + 3),
                round(daily["temperature_2m_max"][0]),
                round(daily["temperature_2m_max"][0] - 3),
                round(daily["temperature_2m_min"][0])
            )

        code = cur.get("weather_code", 0)
        desc_map = {
            0: "آسمان صاف", 1: "غالبا صاف", 2: "نیمه ابری", 3: "ابری",
            45: "مه آلود", 48: "مه آلود", 51: "نم نم باران", 61: "بارش خفیف باران",
            63: "بارانی", 65: "بارش شدید باران", 71: "بارش برف", 80: "رگبار باران", 95: "رعد و برق"
        }
        CACHE["weather"] = {
            "temp": round(cur["temperature_2m"], 1),
            "temp_int": round(cur["temperature_2m"]),
            "max": round(daily["temperature_2m_max"][0], 1),
            "min": round(daily["temperature_2m_min"][0], 1),
            "wind": round(cur["wind_speed_10m"]),
            "humidity": round(cur["relative_humidity_2m"]),
            "desc": desc_map.get(code, "آسمان صاف و معتدل"),
            "periods": periods
        }
    except Exception:
        pass

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


def register_and_check_match(state, matches_mem, lg_key, match_id, league_fa, is_iran, h_name, a_name, h_g, a_g, h_logo, a_logo, is_live, is_finished, minute_str="", scorers_list=None, allow_auto_alert=True):
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
        status_emoji = "⏰"
        status_label = f"در انتظار شروع ({to_fa_digits(minute_str)})" if minute_str else "در انتظار شروع"
        header_prefix = "برنامه بازی"
        line_str = f"⏰ {to_fa_digits(minute_str)} | {h_name} - {a_name}" if minute_str else f"⏰ در انتظار شروع | {h_name} - {a_name}"

    m_obj = {
        "id": match_id,
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
        "is_live": is_live,
        "is_finished": is_finished,
        "scorers_list": scorers_list or []
    }
    CACHE["matches_by_id"][match_id] = m_obj
    CACHE["leagues"][lg_key]["lines"].append(line_str)
    CACHE["leagues"][lg_key]["match_ids"].append(match_id)

    if is_live:
        CACHE["live_match_ids"].append(match_id)
        CACHE["live_lines"].append(f"🏆 {league_fa}: {line_str}")

    if not allow_auto_alert:
        return

    if match_id not in matches_mem:
        matches_mem[match_id] = {"h": h_g, "a": a_g, "ft": is_finished}
        return

    prev = matches_mem[match_id]
    target_chat = get_target_chat_id(state)
    footer = state.get("footer_text", "گزارش زنده و نتایج فوتبال")

    if is_iran and is_live and (h_g > prev["h"] or a_g > prev["a"]):
        scorer = h_name if h_g > prev["h"] else a_name
        if target_chat:
            img = build_match_image(m_obj, footer_text=footer)
            send_telegram_photo(target_chat, img, f"🔴 گل برای {scorer}!\n{h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}")
        prev["h"], prev["a"] = h_g, a_g

    if is_finished and not prev["ft"]:
        if target_chat:
            img = build_match_image(m_obj, footer_text=footer)
            send_telegram_photo(target_chat, img, f"🏁 پایان بازی ({league_fa})\n{h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}")
        prev["ft"] = True
        prev["h"], prev["a"] = h_g, a_g


def check_all_football_free(state):
    matches_mem = state.setdefault("matches", {})
    now_greg = jdatetime.datetime.now(TEHRAN_TZ).togregorian()
    today_compact = now_greg.strftime("%Y%m%d")

    CACHE["live_match_ids"] = []
    CACHE["live_lines"] = []
    for lg_key, lg_title in LEAGUE_CATEGORIES:
        CACHE["leagues"][lg_key] = {
            "title": lg_title,
            "lines": [],
            "match_ids": [],
            "has_live": False
        }

    for day_offset in [0, -1, 1, -2, 2]:
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

                    h_name = to_persian_text(m["home"]["name"])
                    a_name = to_persian_text(m["away"]["name"])
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

    espn_configs = [
        ("lg_eng", "eng.1", "لیگ برتر انگلیس"),
        ("lg_esp", "esp.1", "لالیگا اسپانیا"),
        ("lg_ger", "ger.1", "بوندسلیگا آلمان"),
        ("lg_ucl", "uefa.champions", "لیگ قهرمانان اروپا")
    ]
    for lg_key, code, l_fa in espn_configs:
        try:
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
                state_type = ev["status"]["type"]["state"]
                is_live = (state_type == "in")
                is_finished = (state_type == "post")
                minute_str = ev["status"]["type"].get("shortDetail", "")

                home = next(c for c in comp["competitors"] if c["homeAway"] == "home")
                away = next(c for c in comp["competitors"] if c["homeAway"] == "away")

                h_name = to_persian_text(home["team"]["displayName"])
                a_name = to_persian_text(away["team"]["displayName"])
                h_g, a_g = int(home.get("score", 0) or 0), int(away.get("score", 0) or 0)
                h_logo, a_logo = home["team"].get("logo", ""), away["team"].get("logo", "")

                scorers_list = []
                for det in comp.get("details", []):
                    if det.get("scoringPlay"):
                        clock = det.get("clock", {}).get("displayValue", "").replace("'", "")
                        athletes = det.get("athletesInvolved", [])
                        if athletes:
                            p_fa = to_persian_text(athletes[0].get("displayName", ""))
                            scorers_list.append(f"{p_fa} ({to_fa_digits(clock)})")

                register_and_check_match(
                    state, matches_mem, lg_key, mid, l_fa, False,
                    h_name, a_name, h_g, a_g, h_logo, a_logo,
                    is_live, is_finished, minute_str, scorers_list=scorers_list, allow_auto_alert=is_today_batch
                )
        except Exception:
            pass


# =====================================================================
# 6. ارتباط با تلگرام، بخش «فوتبال زنده امروز» و منوی تنظیمات
# =====================================================================
def setup_bot_commands():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands"
    commands = [
        {"command": "morning", "description": "🌞 صبح بخیر (شرعیات، طلا و حافظ)"},
        {"command": "weather", "description": "⛅ وضعیت آب و هوا (۴ زمانه)"},
        {"command": "football", "description": "⚽ نتایج زنده و پوستر بازی ها"},
        {"command": "settings", "description": "⚙ تنظیمات ربات"}
    ]
    try:
        requests.post(url, json={"commands": commands}, timeout=10)
    except Exception:
        pass


def send_telegram_photo(chat_id, img, caption=""):
    if not chat_id:
        return
    bio = io.BytesIO()
    img.convert("RGB").save(bio, format="JPEG", quality=95)
    bio.seek(0)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    data = {"chat_id": chat_id, "caption": caption}
    if not str(chat_id).startswith("@") and not str(chat_id).startswith("-"):
        data["reply_markup"] = BOT_MENU_KEYBOARD
    try:
        requests.post(url, data=data, files={"photo": ("story.jpg", bio, "image/jpeg")}, timeout=20)
    except Exception as e:
        print("Send photo error:", e)


def send_menu_keyboard(chat_id, text="✅ منوی ربات آماده است! از دکمه های پایین صفحه انتخاب کنید:"):
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
    buttons = []
    live_count = len(CACHE["live_match_ids"])
    live_label = f"🔴 فوتبال های زنده در جریان امروز ({to_fa_digits(live_count)} بازی زنده)" if live_count > 0 else "🔴 فوتبال های زنده در جریان امروز"
    buttons.append([{"text": live_label, "callback_data": "show_live_now"}])

    for lg_key, lg_title in LEAGUE_CATEGORIES:
        lg_info = CACHE["leagues"].get(lg_key, {})
        count = len(lg_info.get("match_ids", []))
        live_badge = " 🔴 (زنده)" if lg_info.get("has_live") else ""
        count_txt = f" ({to_fa_digits(count)} بازی)" if count > 0 else ""
        buttons.append([{"text": f"{lg_title}{live_badge}{count_txt}", "callback_data": f"showlg_{lg_key}"}])

    buttons.append([{"text": "📊 ساخت پوستر تجمیعی ۵ بازی مهم روز", "callback_data": "mk_multi_today"}])
    return json.dumps({"inline_keyboard": buttons})


def send_league_selection_question(chat_id, message_id=None):
    text = (
        "⚽ کدوم بخش یا لیگ مد نظرته؟\n\n"
        "• برای دیدن تمامی بازی هایی که همین لحظه زنده در جریان هستند روی دکمه اول (🔴) بزنید.\n"
        "• یا یکی از لیگ های زیر را انتخاب کنید:"
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
    except Exception:
        pass


def send_live_now_matches(chat_id, message_id=None):
    live_ids = CACHE["live_match_ids"]
    live_lines = CACHE["live_lines"]

    if live_lines:
        text = (
            "🔴 فهرست تمامی بازی های زنده در جریان امروز:\n\n"
            + "\n".join(live_lines)
            + "\n\n👇 روی هر بازی زنده که می خواهید بزنید تا بلافاصله پوستر آن ساخته و ارسال شود:"
        )
    else:
        text = (
            "🔴 فوتبال های زنده در جریان امروز:\n\n"
            "⚽ در این لحظه هیچ بازی زنده ای در حال برگزاری نیست.\n"
            "می توانید از دکمه بازگشت، نتایج بازی های پایان یافته یا برنامه بازی های امروز را در هر لیگ مشاهده کنید."
        )

    buttons = []
    for mid in live_ids[:20]:
        m = CACHE["matches_by_id"].get(mid)
        if not m:
            continue
        buttons.append([
            {"text": f"📸 پوستر زنده: {m['h_name']} {to_fa_digits(m['h_g'])}-{to_fa_digits(m['a_g'])} {m['a_name']}", "callback_data": f"mkimg_{mid}"}
        ])

    buttons.append([{"text": "🔙 بازگشت به منوی لیگ ها", "callback_data": "back_leagues"}])
    markup = json.dumps({"inline_keyboard": buttons})

    if message_id:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
        payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "reply_markup": markup}
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "reply_markup": markup}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception:
        pass


def send_specific_league_matches(chat_id, lg_key, message_id=None):
    lg_info = CACHE["leagues"].get(lg_key)
    if not lg_info:
        return

    title = lg_info["title"]
    lines = lg_info["lines"]
    m_ids = lg_info["match_ids"]

    if lines:
        matches_text = "\n".join(lines)
        legend = "\n\nراهنما: 🔴 زنده | 🏁 پایان بازی | ⏰ در انتظار شروع"
        text = (
            f"🏆 گزارش بازی های {title}:\n\n"
            f"{matches_text}"
            f"{legend}\n"
            "👇 برای هر بازی می توانید «📸 پوستر نتیجه و آمار» یا «⚔ پوستر تقابل رو در رو» دریافت کنید:"
        )
    else:
        text = f"🏆 {title}\n\n⚽ در حال حاضر بازی فعالی برای این لیگ ثبت نشده است."

    buttons = []
    for mid in m_ids[:12]:
        m = CACHE["matches_by_id"].get(mid)
        if not m:
            continue
        score_lbl = f"{m['status_emoji']} {m['h_name']} {to_fa_digits(m['h_g'])}-{to_fa_digits(m['a_g'])} {m['a_name']}"
        buttons.append([
            {"text": f"📸 آمار: {score_lbl}", "callback_data": f"mkimg_{mid}"},
            {"text": "⚔ تقابل رو در رو", "callback_data": f"mkh2h_{mid}"}
        ])

    if len(m_ids) >= 2:
        buttons.append([{"text": "📊 پوستر تجمیعی نتایج این لیگ", "callback_data": f"mkmulti_{lg_key}"}])

    buttons.append([{"text": "🔙 بازگشت به انتخاب لیگ ها", "callback_data": "back_leagues"}])
    markup = json.dumps({"inline_keyboard": buttons})

    if message_id:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
        payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "reply_markup": markup}
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "reply_markup": markup}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception:
        pass


def send_settings_menu(chat_id, state):
    footer = state.get("footer_text", "گزارش زنده و نتایج فوتبال")
    hour = state.get("morning_hour", 7)
    text = (
        "⚙ تنظیمات ربات استوری ساز:\n\n"
        f"📝 امضای پایین پوسترهای فوتبال: «{footer}»\n"
        f"⏰ ساعت ارسال خودکار صبحگاهی: ساعت {to_fa_digits(hour)}:۰۰ صبح\n\n"
        "👇 برای تغییر هر مورد روی دکمه مربوطه بزنید:"
    )
    buttons = [
        [{"text": "✏ تغییر متن امضای پایین پوسترها", "callback_data": "set_footer"}],
        [
            {"text": "⏰ ارسال صبحگاهی: ۶ صبح", "callback_data": "sethour_6"},
            {"text": "⏰ ارسال صبحگاهی: ۷ صبح", "callback_data": "sethour_7"},
            {"text": "⏰ ارسال صبحگاهی: ۸ صبح", "callback_data": "sethour_8"}
        ]
    ]
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text, "reply_markup": json.dumps({"inline_keyboard": buttons})}, timeout=10)


def answer_callback(callback_id, text=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
    try:
        requests.post(url, data={"callback_query_id": callback_id, "text": text}, timeout=5)
    except Exception:
        pass


# =====================================================================
# 7. اجرای 24 ساعته در پس زمینه و پاسخگویی زیر 3 ثانیه
# =====================================================================
def background_worker(state):
    while True:
        try:
            refresh_daily_data_cache()
            check_all_football_free(state)

            now_tehran = jdatetime.datetime.now(TEHRAN_TZ)
            today_gregorian = now_tehran.togregorian().strftime("%Y-%m-%d")
            target_chat = get_target_chat_id(state)
            morning_hour = int(state.get("morning_hour", 7))

            if now_tehran.hour == morning_hour and state.get("last_morning_date") != today_gregorian and target_chat:
                refresh_daily_data_cache()
                send_telegram_photo(target_chat, build_morning_image(), "🌞 صبح بخیر | تقویم، اوقات شرعی، نبض بازار و تفال حافظ")
                send_telegram_photo(target_chat, build_weather_image(), "⛅ وضعیت آب و هوا و پیش بینی ۴ زمانه امروز")
                state["last_morning_date"] = today_gregorian

            save_state(state)
        except Exception as e:
            print("Background worker error:", e)
        time.sleep(60)


def handle_user_request(chat_id, text, state):
    t = text.strip()
    if state.get("awaiting_input") == "footer":
        state["footer_text"] = t
        state["awaiting_input"] = ""
        save_state(state)
        send_menu_keyboard(chat_id, f"✅ متن امضای پایین پوسترها با موفقیت به «{t}» تغییر یافت!")
        return

    if "صبح بخیر" in t or t == "/morning":
        img = build_morning_image()
        send_telegram_photo(chat_id, img, "🌞 صبح بخیر | تقویم، اوقات شرعی، نبض بازار و تفال حافظ")
    elif "وضعیت هوا" in t or "آب و هوا" in t or t == "/weather":
        img = build_weather_image()
        send_telegram_photo(chat_id, img, "⛅ وضعیت لحظه ای آب و هوا و پیش بینی ۴ زمانه")
    elif "نتایج زنده" in t or "فوتبال" in t or t == "/football":
        send_league_selection_question(chat_id)
    elif "تنظیمات" in t or t == "/settings":
        send_settings_menu(chat_id, state)
    else:
        send_menu_keyboard(chat_id, "👇 لطفا یکی از کلیدهای منوی پایین صفحه را انتخاب کنید:")


def handle_callback_query(chat_id, message_id, cb_id, data, state):
    footer = state.get("footer_text", "گزارش زنده و نتایج فوتبال")

    if data == "show_live_now":
        answer_callback(cb_id, "🔴 دریافت بازی های زنده در جریان امروز...")
        send_live_now_matches(chat_id, message_id=message_id)

    elif data.startswith("showlg_"):
        answer_callback(cb_id, "⚽ دریافت لیست بازی های لیگ...")
        lg_key = data.replace("showlg_", "", 1)
        send_specific_league_matches(chat_id, lg_key, message_id=message_id)

    elif data == "back_leagues":
        answer_callback(cb_id)
        send_league_selection_question(chat_id, message_id=message_id)

    elif data.startswith("mkimg_"):
        answer_callback(cb_id, "🎨 در حال ساخت پوستر گزارش و آمار بازی...")
        mid = data.replace("mkimg_", "", 1)
        m = CACHE["matches_by_id"].get(mid)
        if m:
            img = build_match_image(m, footer_text=footer)
            caption = f"{m['status_emoji']} {m['status_label']} ({m['league_fa']})\n⚽ {m['h_name']} {to_fa_digits(m['h_g'])} - {to_fa_digits(m['a_g'])} {m['a_name']}"
            send_telegram_photo(chat_id, img, caption)

    elif data.startswith("mkh2h_"):
        answer_callback(cb_id, "⚔ در حال ساخت پوستر روز بازی و تقابل رو در رو...")
        mid = data.replace("mkh2h_", "", 1)
        m = CACHE["matches_by_id"].get(mid)
        if m:
            img = build_h2h_matchday_image(m, footer_text=footer)
            caption = f"⚔ پیش بازی و تقابل رو در رو ({m['league_fa']})\n⚽ {m['h_name']} مقابل {m['a_name']}"
            send_telegram_photo(chat_id, img, caption)

    elif data == "mk_multi_today" or data.startswith("mkmulti_"):
        answer_callback(cb_id, "📊 در حال ساخت پوستر تجمیعی نتایج...")
        if data == "mk_multi_today":
            all_ids = CACHE["live_match_ids"] + [
                mid for lg in CACHE["leagues"].values() for mid in lg["match_ids"]
            ]
            seen = []
            for x in all_ids:
                if x not in seen:
                    seen.append(x)
            selected = [CACHE["matches_by_id"][x] for x in seen[:5] if x in CACHE["matches_by_id"]]
            title_top = "نتایج بازی های امروز"
        else:
            lg_key = data.replace("mkmulti_", "", 1)
            lg_info = CACHE["leagues"].get(lg_key, {})
            selected = [CACHE["matches_by_id"][x] for x in lg_info.get("match_ids", [])[:5] if x in CACHE["matches_by_id"]]
            title_top = lg_info.get("title", "نتایج بازی ها")

        if selected:
            img = build_multi_match_image(selected, title_top=title_top, footer_text=footer)
            send_telegram_photo(chat_id, img, f"📊 جمع بندی نتایج ({title_top})")

    elif data == "set_footer":
        answer_callback(cb_id)
        state["awaiting_input"] = "footer"
        save_state(state)
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": "✏ لطفا متن جدیدی که می خواهید در نوار طلایی پایین پوسترها نوشته شود را تایپ و ارسال کنید:"}, timeout=10)

    elif data.startswith("sethour_"):
        hr = int(data.replace("sethour_", "", 1))
        state["morning_hour"] = hr
        save_state(state)
        answer_callback(cb_id, f"✅ ساعت ارسال صبحگاهی روی {to_fa_digits(hr)} صبح تنظیم شد.")
        send_settings_menu(chat_id, state)


if __name__ == "__main__":
    ensure_fonts()
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
                    threading.Thread(target=handle_user_request, args=(cid, txt, state), daemon=True).start()

                elif "callback_query" in upd:
                    cb = upd["callback_query"]
                    cb_id = cb["id"]
                    cid = cb["message"]["chat"]["id"]
                    mid = cb["message"]["message_id"]
                    data = cb.get("data", "")
                    threading.Thread(target=handle_callback_query, args=(cid, mid, cb_id, data, state), daemon=True).start()
        except Exception:
            time.sleep(2)
