import os
import io
import json
import requests
import jdatetime
import pytz
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

# =====================================================================
# ۱. دریافت امن کلیدها از سرور گیت‌هاب (GitHub Secrets)
# =====================================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "@shirazlastnews")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "")
BRS_MARKET_API_KEY = os.environ.get("BRS_MARKET_API_KEY", "")
FORCE_TEST = os.environ.get("FORCE_TEST", "false").lower() == "true"

TEHRAN_TZ = pytz.timezone("Asia/Tehran")
STATE_FILE = "state.json"
FONT_FILE = "Vazirmatn-Bold.ttf"
FONT_URL = "https://github.com/rastikerdar/vazirmatn/raw/master/fonts/ttf/Vazirmatn-Bold.ttf"

# شناسه‌های رسمی لیگ‌ها در API-Football
LEAGUES = {
    290: "لیگ برتر ایران",
    495: "جام حذفی ایران",
    39:  "لیگ برتر انگلیس",
    140: "لالیگا اسپانیا",
    78:  "بوندسلیگا آلمان",
    2:   "لیگ قهرمانان اروپا"
}
IRAN_LEAGUES = {290, 495}

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
    "Esteghlal Khuzestan": "استقلال خوزستان", "Mes Shahr-e Babak": "مس شهر بابک"
}


# =====================================================================
# ۲. مدیریت حافظه، فونت خودکار و ابزارهای گرافیکی
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
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def ensure_font():
    if not os.path.exists(FONT_FILE):
        try:
            r = requests.get(FONT_URL, timeout=15)
            with open(FONT_FILE, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print("Font download error:", e)


def get_font(size):
    ensure_font()
    if os.path.exists(FONT_FILE):
        return ImageFont.truetype(FONT_FILE, size)
    return ImageFont.load_default()


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


def open_template(candidates, size, default_color):
    for name in candidates:
        if os.path.exists(name):
            return Image.open(name).convert("RGBA").resize(size)
    return Image.new("RGBA", size, default_color)


def send_telegram_photo(img, caption=""):
    if not TELEGRAM_BOT_TOKEN:
        print("خطا: TELEGRAM_BOT_TOKEN تنظیم نشده است!")
        return
    bio = io.BytesIO()
    img.convert("RGB").save(bio, format="JPEG", quality=95)
    bio.seek(0)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    r = requests.post(
        url,
        data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
        files={"photo": ("report.jpg", bio, "image/jpeg")},
        timeout=25
    )
    print("Telegram response:", r.status_code, r.text)


# =====================================================================
# ۳. دریافت اطلاعات روزانه و ساخت عکس ۱ و ۲
# =====================================================================
def get_persian_date():
    now = jdatetime.datetime.now(TEHRAN_TZ)
    weekdays = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
    months = ["", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
              "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
    wd = weekdays[now.weekday()]
    return f"{wd} {now.day} {months[now.month]} {now.year}", f"{now.day} {months[now.month]} {now.year}"


def get_shiraz_prayers():
    try:
        url = "http://api.aladhan.com/v1/timingsByCity?city=Shiraz&country=Iran&method=7"
        t = requests.get(url, timeout=10).json()["data"]["timings"]
        return t["Fajr"][:5], t["Sunrise"][:5], t["Dhuhr"][:5], t["Maghrib"][:5]
    except Exception:
        return "05:00", "06:21", "11:44", "17:24"


def get_shiraz_weather():
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast?latitude=29.5918&longitude=52.5837"
            "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
            "&daily=temperature_2m_max,temperature_2m_min&timezone=Asia%2FTehran"
        )
        d = requests.get(url, timeout=10).json()
        cur, daily = d["current"], d["daily"]
        code = cur.get("weather_code", 0)
        desc_map = {
            0: "آسمان صاف", 1: "غالباً صاف", 2: "نیمه‌ابری", 3: "ابری",
            45: "مه‌آلود", 61: "بارش خفیف باران", 63: "بارانی", 71: "برفی", 95: "رعد و برق"
        }
        return {
            "temp": round(cur["temperature_2m"], 1),
            "temp_int": round(cur["temperature_2m"]),
            "max": round(daily["temperature_2m_max"][0], 1),
            "min": round(daily["temperature_2m_min"][0], 1),
            "wind": round(cur["wind_speed_10m"]),
            "humidity": round(cur["relative_humidity_2m"]),
            "desc": desc_map.get(code, "آسمان صاف و معتدل")
        }
    except Exception:
        return {"temp": 12.5, "temp_int": 13, "max": 18.0, "min": 6.0, "wind": 5, "humidity": 45, "desc": "آسمان صاف"}


def get_market_data():
    try:
        if BRS_MARKET_API_KEY:
            url = f"https://brsapi.ir/FreeTsetmcBourseApi/Api_Free_Gold_Currency.json?key={BRS_MARKET_API_KEY}"
            data = requests.get(url, timeout=10).json()
            usd = next(x["price"] for x in data.get("currency", []) if "دلار" in x["name"])
            gold = next(x["price"] for x in data.get("gold", []) if "18" in x["name"] or "۱۸" in x["name"])
            coin = next(x["price"] for x in data.get("gold", []) if "امامی" in x["name"])
            return f"{int(usd)*10:,}", f"{int(gold)*10:,}", f"{int(coin)*10:,}"
    except Exception:
        pass
    return "890,000", "64,500,000", "745,000,000"


def build_morning_image():
    full_date, _ = get_persian_date()
    fajr, sunrise, dhuhr, maghrib = get_shiraz_prayers()
    w = get_shiraz_weather()
    usd, gold, coin = get_market_data()

    base = open_template(["1.jpg", "1 (2).jpg", "1.png"], (720, 1280), (18, 60, 50, 255))
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
    w = get_shiraz_weather()

    base = open_template(["2.jpg", "111 (Copy).jfif", "2.png"], (1024, 1820), (30, 24, 50, 255))
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


# =====================================================================
# ۴. ساخت عکس ۳ (فوتبال) و رصد لحظه‌ای گل‌ها و نتایج نهایی
# =====================================================================
def fetch_logo_circle(team_name_fa, fallback_url, diameter=154):
    url = IRAN_LOGOS.get(team_name_fa, fallback_url)
    logo_bg = Image.new("RGBA", (diameter, diameter), (255, 255, 255, 255))
    if url:
        try:
            r = requests.get(url, timeout=10)
            raw = Image.open(io.BytesIO(r.content)).convert("RGBA")
            raw.thumbnail((int(diameter * 0.82), int(diameter * 0.82)), Image.Resampling.LANCZOS)
            logo_bg.paste(raw, ((diameter - raw.width) // 2, (diameter - raw.height) // 2), raw)
        except Exception:
            pass
    mask = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter, diameter), fill=255)
    out = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    out.paste(logo_bg, (0, 0), mask)
    return out


def build_match_image(league_title, home_name, away_name, home_goals, away_goals, home_logo, away_logo, bottom_banner):
    base = open_template(["3.jpg", "11 (Copy).jfif", "3.png"], (1024, 1820), (12, 22, 38, 255))
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


def check_football(state, today_str):
    if not FOOTBALL_API_KEY:
        return
    headers = {"x-apisports-key": FOOTBALL_API_KEY}
    try:
        url = f"https://v3.football.api-sports.io/fixtures?date={today_str}"
        fixtures = requests.get(url, headers=headers, timeout=15).json().get("response", [])
    except Exception as e:
        print("Football API error:", e)
        return

    matches_mem = state.setdefault("matches", {})
    for item in fixtures:
        lid = item["league"]["id"]
        if lid not in LEAGUES:
            continue
        fid = str(item["fixture"]["id"])
        status = item["fixture"]["status"]["short"]
        elapsed = item["fixture"]["status"]["elapsed"] or 90

        raw_h, raw_a = item["teams"]["home"]["name"], item["teams"]["away"]["name"]
        h_name = TEAM_NAME_MAP.get(raw_h, raw_h)
        a_name = TEAM_NAME_MAP.get(raw_a, raw_a)
        h_logo, a_logo = item["teams"]["home"]["logo"], item["teams"]["away"]["logo"]
        h_g, a_g = item["goals"]["home"] or 0, item["goals"]["away"] or 0
        l_fa = LEAGUES[lid]

        if fid not in matches_mem:
            matches_mem[fid] = {"h": h_g, "a": a_g, "ft": (status in ["FT", "AET", "PEN"])}
            continue

        prev = matches_mem[fid]

        # گل‌های زنده لیگ برتر ایران و جام حذفی
        if lid in IRAN_LEAGUES and status in ["1H", "2H", "ET"]:
            if h_g > prev["h"] or a_g > prev["a"]:
                scorer = h_name if h_g > prev["h"] else a_name
                banner = f"انفجار در ورزشگاه! گل برای {scorer} (دقیقه {elapsed})"
                img = build_match_image(f"زنده | {l_fa}", h_name, a_name, h_g, a_g, h_logo, a_logo, banner)
                send_telegram_photo(img, caption=f"⚽️ گل برای {scorer}!\n{h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}")
                prev["h"], prev["a"] = h_g, a_g

        # نتیجه نهایی برای تمام ۶ لیگ
        if status in ["FT", "AET", "PEN"] and not prev["ft"]:
            banner = f"پایان بازی | {h_name} {h_g} - {a_g} {a_name}"
            img = build_match_image(f"نتیجه نهایی | {l_fa}", h_name, a_name, h_g, a_g, h_logo, a_logo, banner)
            send_telegram_photo(img, caption=f"🏁 پایان بازی ({l_fa})\n{h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}")
            prev["ft"] = True
            prev["h"], prev["a"] = h_g, a_g


# =====================================================================
# ۵. اجرای هوشمند در سرور گیت‌هاب
# =====================================================================
if __name__ == "__main__":
    state = load_state()
    now_tehran = jdatetime.datetime.now(TEHRAN_TZ)
    today_gregorian = now_tehran.togregorian().strftime("%Y-%m-%d")

    # ۱) اگر کاربر دکمه تست دستی را در گیت‌هاب زده باشد، هر ۳ عکس را بلافاصله برای تست می‌فرستد
    if FORCE_TEST:
        print("اجرای تست دستی...")
        send_telegram_photo(build_morning_image(), "☀️ صبح بخیر شیراز | تقویم، اوقات شرعی و نبض بازار")
        send_telegram_photo(build_weather_image(), "🌤 وضعیت آب و هوای امروز شیراز")
        sample_match = build_match_image(
            "زنده | لیگ برتر ایران", "پرسپولیس", "استقلال", 1, 2,
            IRAN_LOGOS["پرسپولیس"], IRAN_LOGOS["استقلال"],
            "انفجار در ورزشگاه! ثبت گل در دقیقه ۷۸"
        )
        send_telegram_photo(sample_match, "⚽️ تست گزارش زنده فوتبال")

    # ۲) ارسال خودکار بسته صبحگاهی در ساعت ۷ صبح به وقت تهران (فقط یک بار در روز)
    if now_tehran.hour == 7 and state.get("last_morning_date") != today_gregorian:
        send_telegram_photo(build_morning_image(), "☀️ صبح بخیر شیراز | تقویم، اوقات شرعی و نبض بازار امروز")
        send_telegram_photo(build_weather_image(), "🌤 وضعیت آب و هوای امروز شیراز")
        state["last_morning_date"] = today_gregorian

    # ۳) بررسی بازی‌های فوتبال امروز
    check_football(state, today_gregorian)
    save_state(state)
