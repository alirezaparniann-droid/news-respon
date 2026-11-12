import os
import io
import re
import time
import json
import threading
import requests
import jdatetime
import pytz
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

# =====================================================================
# ۱. تنظیمات اصلی (خواندن خودکار از Secrets گیت‌هاب)
# =====================================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
TEHRAN_TZ = pytz.timezone("Asia/Tehran")

STATE_FILE = "state.json"
FONT_FILE = "Vazirmatn-Bold.ttf"
FONT_URL = "https://github.com/rastikerdar/vazirmatn/raw/master/fonts/ttf/Vazirmatn-Bold.ttf"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# تعریف ۳ کلید شیشه‌ای (Inline Keyboard) زیر تمام پیام‌ها و عکس‌ها
GLASS_BUTTONS = json.dumps({
    "inline_keyboard": [
        [{"text": "☀️ صبح بخیر (شرعیات، طلا و ارز)", "callback_data": "btn_morning"}],
        [{"text": "🌤 وضعیت آب و هوا", "callback_data": "btn_weather"}],
        [{"text": "⚽️ نتایج زنده فوتبال", "callback_data": "btn_football"}]
    ]
})

# دیکشنری لوگوهای لیگ برتر ایران
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

TEAM_NAME_MAP = {
    "Persepolis": "پرسپولیس", "Esteghlal": "استقلال", "Sepahan": "سپاهان",
    "Tractor": "تراکتور", "Tractor Sazi": "تراکتور", "Foolad": "فولاد",
    "Zob Ahan": "ذوب آهن", "Malavan": "ملوان", "Gol Gohar": "گل گهر",
    "Aluminium Arak": "آلومینیوم", "Shams Azar Qazvin": "شمس آذر",
    "Chadormalu": "چادرملو", "Kheybar Khorramabad": "خیبر",
    "Nassaji Mazandaran": "نساجی", "Havadar": "هوادار", "Paykan": "پیکان",
    "Sanat Naft": "صنعت نفت", "Saipa": "سایپا", "Fajr Sepasi": "فجر سپاسی",
    "Esteghlal Khuzestan": "استقلال خوزستان", "Mes Shahr-e Babak": "مس شهر بابک",
    "Arsenal": "آرسنال", "Liverpool": "لیورپول", "Manchester City": "منچسترسیتی",
    "Manchester United": "منچستریونایتد", "Chelsea": "چلسی", "Tottenham Hotspur": "تاتنهام",
    "Newcastle United": "نیوکاسل", "Aston Villa": "استون ویلا",
    "Real Madrid": "رئال مادرید", "Barcelona": "بارسلونا", "Atlético Madrid": "اتلتیکو مادرید",
    "Girona": "خیرونا", "Athletic Club": "اتلتیک بیلبائو", "Real Sociedad": "رئال سوسیداد",
    "Bayern Munich": "بایرن مونیخ", "Bayer Leverkusen": "لورکوزن", "Borussia Dortmund": "دورتموند",
    "RB Leipzig": "لایپزیگ", "Stuttgart": "اشتوتگارت", "Inter Milan": "اینتر میلان",
    "AC Milan": "میلان", "Juventus": "یوونتوس", "Paris Saint-Germain": "پاری سن ژرمن"
}

# کش در حافظه رم برای پاسخگویی فوری (زیر ۲ ثانیه) به کلیدهای شیشه‌ای
CACHE = {
    "prayers": ("05:00", "06:21", "11:44", "17:24"),
    "weather": {"temp": 14.0, "temp_int": 14, "max": 19.0, "min": 7.0, "wind": 4, "humidity": 42, "desc": "آسمان صاف"},
    "market": ("915,000", "65,400,000", "762,000,000"),
    "featured_match": {
        "league_title": "زنده | لیگ برتر ایران",
        "home_name": "پرسپولیس",
        "away_name": "استقلال",
        "home_goals": 1,
        "away_goals": 2,
        "home_logo": IRAN_LOGOS["پرسپولیس"],
        "away_logo": IRAN_LOGOS["استقلال"],
        "banner": "گزارش زنده و نتایج بازی‌های امروز"
    },
    "matches_summary_text": "⚽️ فهرست بازی‌های ثبت‌شده امروز در ۵ لیگ معتبر و لیگ ایران"
}
TEMPLATES_RAM = {}
LOGO_RAM = {}


# =====================================================================
# ۲. ابزارهای گرافیکی و بارگذاری در RAM برای سرعت فوق‌العاده
# =====================================================================
def ensure_font():
    if not os.path.exists(FONT_FILE):
        try:
            r = requests.get(FONT_URL, timeout=15)
            with open(FONT_FILE, "wb") as f:
                f.write(r.content)
        except Exception:
            pass


def get_font(size):
    ensure_font()
    if os.path.exists(FONT_FILE):
        return ImageFont.truetype(FONT_FILE, size)
    return ImageFont.load_default()


def preload_templates():
    """بارگذاری قالب‌های گرافیکی در رم در لحظه شروع برای حذف تاخیر دیسک"""
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


def to_fa_digits(val):
    en = "0123456789."
    fa = "۰۱۲۳۴۵۶۷۸۹/"
    res = str(val)
    for e, f in zip(en, fa):
        res = res.replace(e, f)
    return res


def fa(text):
    return get_display(arabic_reshaper.reshape(to_fa_digits(text)))


def draw_centered(draw, y, text, font, fill, width):
    processed = fa(text)
    bbox = draw.textbbox((0, 0), processed, font=font)
    w = bbox[2] - bbox[0]
    draw.text(((width - w) / 2, y), processed, font=font, fill=fill)


# =====================================================================
# ۳. توابع ارتباط فوری با تلگرام
# =====================================================================
def send_telegram_photo(chat_id, img, caption=""):
    bio = io.BytesIO()
    img.convert("RGB").save(bio, format="JPEG", quality=92)
    bio.seek(0)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        requests.post(
            url,
            data={"chat_id": chat_id, "caption": caption, "reply_markup": GLASS_BUTTONS},
            files={"photo": ("report.jpg", bio, "image/jpeg")},
            timeout=15
        )
    except Exception as e:
        print("Send photo error:", e)


def send_menu_message(chat_id, text="👇 لطفاً یکی از گزینه‌های شیشه‌ای زیر را انتخاب کنید تا گزارش تصویری بلافاصله ارسال شود:"):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(
            url,
            data={"chat_id": chat_id, "text": text, "reply_markup": GLASS_BUTTONS},
            timeout=10
        )
    except Exception as e:
        print("Send message error:", e)


def answer_callback(callback_id, text="⚡ در حال ارسال تصویر..."):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
    try:
        requests.post(url, data={"callback_query_id": callback_id, "text": text}, timeout=5)
    except Exception:
        pass


# =====================================================================
# ۴. ساخت فوری ۳ تصویر از روی اطلاعات کش‌شده در رم (کمتر از ۰.۳ ثانیه)
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

    f_title, f_sec, f_date, f_body = get_font(56), get_font(32), get_font(40), get_font(30)
    c_green, c_bronze, c_dark = (12, 55, 42), (148, 92, 38), (22, 38, 38)

    draw_centered(draw, 155, "صبح بخیر شیراز", f_title, c_green, 720)
    draw_centered(draw, 240, "تقویم و گزارش روزانه", f_sec, c_bronze, 720)
    draw_centered(draw, 295, full_date, f_date, c_dark, 720)
    draw.line([(190, 368), (530, 368)], fill=(205, 165, 80, 255), width=2)

    draw_centered(draw, 390, "اوقات شرعی به افق شیراز", f_sec, c_bronze, 720)
    draw_centered(draw, 445, f"اذان صبح {fajr}  |  طلوع آفتاب {sunrise}", f_body, c_dark, 720)
    draw_centered(draw, 495, f"اذان ظهر {dhuhr}  |  اذان مغرب {maghrib}", f_body, c_dark, 720)

    draw_centered(draw, 570, "وضعیت آب و هوا", f_sec, c_bronze, 720)
    draw_centered(draw, 625, f"دمای فعلی: {w['temp']} درجه", f_body, c_dark, 720)
    draw_centered(draw, 675, f"بیشینه {w['max']}  |  کمینه {w['min']}", f_body, c_dark, 720)

    draw_centered(draw, 750, "نبض بازار طلا و ارز", f_sec, c_bronze, 720)
    draw_centered(draw, 805, f"دلار آزاد: {usd} ریال", f_body, c_dark, 720)
    draw_centered(draw, 855, f"طلای ۱۸ عیار: {gold} ریال", f_body, c_dark, 720)
    draw_centered(draw, 905, f"سکه امامی: {coin} ریال", f_body, c_dark, 720)

    return Image.alpha_composite(base, overlay)


def build_weather_image():
    _, short_date = get_persian_date()
    w = CACHE["weather"]

    base = TEMPLATES_RAM["t2"].copy()
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    draw.rounded_rectangle([260, 315, 764, 425], radius=18, fill=(32, 26, 52, 255))
    draw_centered(draw, 330, short_date, get_font(64), (255, 255, 255), 1024)

    draw.rounded_rectangle([98, 518, 595, 1048], radius=36, fill=(92, 88, 114, 248), outline=(212, 182, 115, 255), width=4)
    temp_str = fa(f"{w['temp_int']} درجه")
    f_big = get_font(110)
    tb = draw.textbbox((0, 0), temp_str, font=f_big)
    draw.text((346 - (tb[2] - tb[0]) / 2, 720), temp_str, font=f_big, fill=(245, 212, 135))

    draw.rounded_rectangle([600, 905, 960, 1000], radius=15, fill=(44, 38, 64, 255))
    desc_str = fa(w["desc"])
    f_desc = get_font(48)
    db = draw.textbbox((0, 0), desc_str, font=f_desc)
    draw.text((780 - (db[2] - db[0]) / 2, 920), desc_str, font=f_desc, fill=(255, 255, 255))

    bars = [
        (1094, 1212, f"بیشینه روز: {round(w['max'])} درجه / کمینه شب: {round(w['min'])} درجه"),
        (1246, 1364, f"سرعت باد: {w['wind']} کیلومتر بر ساعت"),
        (1396, 1514, f"رطوبت: {w['humidity']} درصد")
    ]
    f_bar = get_font(46)
    for y1, y2, text in bars:
        draw.rounded_rectangle([98, y1, 924, y2], radius=28, fill=(88, 84, 104, 248), outline=(190, 185, 200, 255), width=3)
        draw_centered(draw, y1 + 26, text, f_bar, (255, 255, 255), 1024)

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
    draw_centered(draw, 195, league_title, get_font(44), (255, 255, 255), 1024)

    draw.rounded_rectangle([340, 755, 684, 1005], radius=20, fill=(24, 43, 58, 250))
    draw_centered(draw, 775, f"{away_goals} - {home_goals}", get_font(125), (242, 205, 120), 1024)
    draw_centered(draw, 935, f"{home_name}  |  {away_name}", get_font(30), (210, 225, 240), 1024)

    draw.rounded_rectangle([108, 1114, 916, 1228], radius=26, fill=(22, 27, 36, 250), outline=(215, 180, 105, 255), width=4)
    draw_centered(draw, 1142, bottom_banner, get_font(40), (255, 255, 255), 1024)

    combined = Image.alpha_composite(base, overlay)
    left_circle = fetch_logo_circle(away_name, away_logo, 154)
    right_circle = fetch_logo_circle(home_name, home_logo, 154)
    combined.paste(left_circle, (228 - 77, 878 - 77), left_circle)
    combined.paste(right_circle, (796 - 77, 878 - 77), right_circle)
    return combined


# =====================================================================
# ۵. بروزرسانی خودکار اطلاعات در پس‌زمینه + ارسال خودکار ۷ صبح و گل‌ها
# =====================================================================
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_morning_date": "", "matches": {}}


def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def refresh_daily_data_cache():
    # اوقات شرعی شیراز
    try:
        url = "http://api.aladhan.com/v1/timingsByCity?city=Shiraz&country=Iran&method=7"
        t = requests.get(url, timeout=8).json()["data"]["timings"]
        CACHE["prayers"] = (t["Fajr"][:5], t["Sunrise"][:5], t["Dhuhr"][:5], t["Maghrib"][:5])
    except Exception:
        pass

    # آب و هوای شیراز
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast?latitude=29.5918&longitude=52.5837"
            "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
            "&daily=temperature_2m_max,temperature_2m_min&timezone=Asia%2FTehran"
        )
        d = requests.get(url, timeout=8).json()
        cur, daily = d["current"], d["daily"]
        code = cur.get("weather_code", 0)
        desc_map = {
            0: "آسمان صاف", 1: "غالباً صاف", 2: "نیمه‌ابری", 3: "ابری",
            45: "مه‌آلود", 61: "بارش خفیف باران", 63: "بارانی", 71: "برفی", 95: "رعد و برق"
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

    # قیمت طلا، سکه و دلار
    try:
        html = requests.get("https://www.tgju.org/", headers=HEADERS, timeout=10).text
        def extract_price(slug):
            pattern = rf'data-market-row="{slug}"[^>]*>.*?<td class="nf"[^>]*>([\d,]+)</td>'
            m = re.search(pattern, html, re.DOTALL)
            return m.group(1) if m else None
        usd, gold, coin = extract_price("price_dollar_rl"), extract_price("geram18"), extract_price("sekee")
        if usd and gold and coin:
            CACHE["market"] = (usd, gold, coin)
    except Exception:
        pass


def process_match_event(matches_mem, match_id, league_fa, is_iran, h_name, a_name, h_g, a_g, h_logo, a_logo, is_live, is_finished, minute_str=""):
    # ذخیره آخرین بازی معتبر برای دکمه شیشه‌ای نتایج زنده
    status_label = f"زنده (دقیقه {minute_str})" if is_live else ("پایان بازی" if is_finished else "برنامه بازی امروز")
    CACHE["featured_match"] = {
        "league_title": f"{'زنده' if is_live else 'گزارش'} | {league_fa}",
        "home_name": h_name,
        "away_name": a_name,
        "home_goals": h_g,
        "away_goals": a_g,
        "home_logo": h_logo,
        "away_logo": a_logo,
        "banner": f"{status_label} | {h_name} {h_g} - {a_g} {a_name}"
    }

    if match_id not in matches_mem:
        matches_mem[match_id] = {"h": h_g, "a": a_g, "ft": is_finished}
        return

    prev = matches_mem[match_id]

    if is_iran and is_live and (h_g > prev["h"] or a_g > prev["a"]):
        scorer = h_name if h_g > prev["h"] else a_name
        min_txt = f"در دقیقه {minute_str}" if minute_str else ""
        banner = f"انفجار در ورزشگاه! گل برای {scorer} {min_txt}".strip()
        if TELEGRAM_CHAT_ID:
            img = build_match_image(f"زنده | {league_fa}", h_name, a_name, h_g, a_g, h_logo, a_logo, banner)
            send_telegram_photo(TELEGRAM_CHAT_ID, img, f"⚽️ گل برای {scorer}!\n{h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}")
        prev["h"], prev["a"] = h_g, a_g

    if is_finished and not prev["ft"]:
        banner = f"پایان بازی | {h_name} {h_g} - {a_g} {a_name}"
        if TELEGRAM_CHAT_ID:
            img = build_match_image(f"نتیجه نهایی | {league_fa}", h_name, a_name, h_g, a_g, h_logo, a_logo, banner)
            send_telegram_photo(TELEGRAM_CHAT_ID, img, f"🏁 پایان بازی ({league_fa})\n{h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}")
        prev["ft"] = True
        prev["h"], prev["a"] = h_g, a_g


def check_all_football_free(state):
    matches_mem = state.setdefault("matches", {})
    summary_lines = ["⚽️ نتایج زنده و بازی‌های امروز:\n"]

    # ۱. لیگ برتر ایران و جام حذفی
    try:
        today_compact = jdatetime.datetime.now(TEHRAN_TZ).togregorian().strftime("%Y%m%d")
        f_url = f"https://www.fotmob.com/api/matches?date={today_compact}"
        f_leagues = requests.get(f_url, headers=HEADERS, timeout=10).json().get("leagues", [])
        for lg in f_leagues:
            lid = lg.get("primaryId")
            if lid not in (9090, 9384):
                continue
            l_fa = "لیگ برتر ایران" if lid == 9090 else "جام حذفی ایران"
            summary_lines.append(f"🏆 {l_fa}:")
            for m in lg.get("matches", []):
                mid = f"ir_{m['id']}"
                st = m.get("status", {})
                is_live = st.get("started", False) and not st.get("finished", False)
                is_finished = st.get("finished", False)
                minute_str = st.get("liveTime", {}).get("short", "").replace("'", "")

                h_raw, a_raw = m["home"]["name"], m["away"]["name"]
                h_name, a_name = TEAM_NAME_MAP.get(h_raw, h_raw), TEAM_NAME_MAP.get(a_raw, a_raw)
                h_g, a_g = int(m["home"].get("score", 0) or 0), int(m["away"].get("score", 0) or 0)
                h_logo = f"https://images.fotmob.com/image_resources/logo/teamlogo/{m['home']['id']}.png"
                a_logo = f"https://images.fotmob.com/image_resources/logo/teamlogo/{m['away']['id']}.png"

                icon = "🔴" if is_live else ("🏁" if is_finished else "🕒")
                summary_lines.append(f"{icon} {h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}")
                process_match_event(matches_mem, mid, l_fa, True, h_name, a_name, h_g, a_g, h_logo, a_logo, is_live, is_finished, minute_str)
    except Exception:
        pass

    # ۲. لیگ‌های معتبر اروپایی (انگلیس، اسپانیا، آلمان، قهرمانان اروپا)
    espn_leagues = {
        "eng.1": "لیگ برتر انگلیس",
        "esp.1": "لالیگا اسپانیا",
        "ger.1": "بوندسلیگا آلمان",
        "uefa.champions": "لیگ قهرمانان اروپا"
    }
    for code, l_fa in espn_leagues.items():
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard"
            events = requests.get(url, headers=HEADERS, timeout=10).json().get("events", [])
            if events:
                summary_lines.append(f"\n🏆 {l_fa}:")
            for ev in events[:5]:
                mid = f"espn_{ev['id']}"
                comp = ev["competitions"][0]
                state_type = ev["status"]["type"]["state"]
                is_live = (state_type == "in")
                is_finished = (state_type == "post")
                minute_str = ev["status"]["type"].get("shortDetail", "")

                home = next(c for c in comp["competitors"] if c["homeAway"] == "home")
                away = next(c for c in comp["competitors"] if c["homeAway"] == "away")

                h_raw, a_raw = home["team"]["displayName"], away["team"]["displayName"]
                h_name, a_name = TEAM_NAME_MAP.get(h_raw, h_raw), TEAM_NAME_MAP.get(a_raw, a_raw)
                h_g, a_g = int(home.get("score", 0) or 0), int(away.get("score", 0) or 0)
                h_logo, a_logo = home["team"].get("logo", ""), away["team"].get("logo", "")

                icon = "🔴" if is_live else ("🏁" if is_finished else "🕒")
                summary_lines.append(f"{icon} {h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}")
                process_match_event(matches_mem, mid, l_fa, False, h_name, a_name, h_g, a_g, h_logo, a_logo, is_live, is_finished, minute_str)
        except Exception:
            pass

    if len(summary_lines) > 1:
        CACHE["matches_summary_text"] = "\n".join(summary_lines)[:950]
    else:
        CACHE["matches_summary_text"] = "⚽️ در حال حاضر بازی زنده‌ای در جریان نیست؛ آخرین وضعیت ثبت‌شده روی تصویر نمایش داده شده است."


def background_worker(state):
    """بروزرسانی دائمی کش در پس‌زمینه و ارسال خودکار راس ساعت ۷ صبح"""
    while True:
        try:
            refresh_daily_data_cache()
            check_all_football_free(state)

            now_tehran = jdatetime.datetime.now(TEHRAN_TZ)
            today_gregorian = now_tehran.togregorian().strftime("%Y-%m-%d")

            # ارسال خودکار راس ساعت ۷ صبح به وقت تهران
            if now_tehran.hour == 7 and state.get("last_morning_date") != today_gregorian and TELEGRAM_CHAT_ID:
                send_telegram_photo(TELEGRAM_CHAT_ID, build_morning_image(), "☀️ صبح بخیر شیراز | تقویم، اوقات شرعی و نبض بازار امروز")
                send_telegram_photo(TELEGRAM_CHAT_ID, build_weather_image(), "🌤 وضعیت آب و هوای امروز شیراز")
                state["last_morning_date"] = today_gregorian

            save_state(state)
        except Exception as e:
            print("Background worker error:", e)
        time.sleep(60)


# =====================================================================
# ۶. حلقه اصلی شنود لحظه‌ای کلیدهای شیشه‌ای تلگرام (پاسخگویی زیر ۳ ثانیه)
# =====================================================================
def handle_button_click(chat_id, data):
    if data == "btn_morning":
        img = build_morning_image()
        send_telegram_photo(chat_id, img, "☀️ صبح بخیر شیراز | تقویم، اوقات شرعی و نبض بازار لحظه‌ای")
    elif data == "btn_weather":
        img = build_weather_image()
        send_telegram_photo(chat_id, img, "🌤 وضعیت لحظه‌ای آب و هوای شیراز")
    elif data == "btn_football":
        fm = CACHE["featured_match"]
        img = build_match_image(
            fm["league_title"], fm["home_name"], fm["away_name"],
            fm["home_goals"], fm["away_goals"], fm["home_logo"], fm["away_logo"], fm["banner"]
        )
        send_telegram_photo(chat_id, img, CACHE["matches_summary_text"])


if __name__ == "__main__":
    print("🚀 در حال بارگذاری قالب‌ها و فونت در حافظه رم...")
    preload_templates()
    ensure_font()
    state = load_state()

    # بارگذاری اولیه کش
    refresh_daily_data_cache()
    check_all_football_free(state)

    # ارسال منوی شیشه‌ای اولیه به محض روشن شدن
    if TELEGRAM_CHAT_ID:
        send_menu_message(TELEGRAM_CHAT_ID, "✅ ربات ۲۴ ساعته فعال شد! هر زمان روی یکی از ۳ کلید شیشه‌ای زیر بزنید، گزارش تصویری در کمتر از ۳ ثانیه ارسال می‌شود:")

    # شروع ترد پس‌زمینه برای ساعت ۷ صبح و رصد زنده فوتبال
    bg_thread = threading.Thread(target=background_worker, args=(state,), daemon=True)
    bg_thread.start()

    # شنود لحظه‌ای کلیک روی دکمه‌های شیشه‌ای به مدت ۵.۵ ساعت در هر چرخه گیت‌هاب
    start_ts = time.time()
    offset = 0
    while time.time() - start_ts < 19500:  # ۵ ساعت و ۲۵ دقیقه
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            res = requests.get(url, params={"offset": offset, "timeout": 25}, timeout=30).json()
            for upd in res.get("result", []):
                offset = upd["update_id"] + 1

                # ۱) اگر کاربر پیام متنی مثل /start فرستاد، ۳ کلید شیشه‌ای را نشان بده
                if "message" in upd and "text" in upd["message"]:
                    cid = upd["message"]["chat"]["id"]
                    send_menu_message(cid)

                # ۲) اگر کاربر روی یکی از ۳ کلید شیشه‌ای زد، زیر ۳ ثانیه عکس را بفرست
                elif "callback_query" in upd:
                    cb = upd["callback_query"]
                    cb_id = cb["id"]
                    cid = cb["message"]["chat"]["id"]
                    data = cb.get("data", "")
                    answer_callback(cb_id)
                    threading.Thread(target=handle_button_click, args=(cid, data), daemon=True).start()
        except Exception as e:
            time.sleep(2)
