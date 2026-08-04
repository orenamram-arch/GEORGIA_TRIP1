import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta, date, datetime
import math
import urllib.parse
import re
import requests
import json
import os
from supabase import create_client, Client

# הגדרת תצורת העמוד (חייב להיות ראשון)
st.set_page_config(page_title="תכנון טיול משפחתי לגאורגיה", page_icon="🇬🇪", layout="wide")

# ==========================================
# חיבור ל-Supabase בענן
# ==========================================
SUPABASE_URL = "https://vobzhjutimeowgsjhgyt.supabase.co"
SUPABASE_KEY = "sb_publishable_OC3UKQ-UdO3ba4yHgvt9RQ_-AZdenBv"

# שם ה-Bucket באחסון Supabase Storage לשמירת קבצים (שוברים, PDF, תמונות)
# חשוב: יש ליצור Bucket בשם הזה בפאנל של Supabase -> Storage, ולסמן אותו כ-Public
STORAGE_BUCKET = "trip-docs"

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

def load_data():
    try:
        # פנייה מפורשת ומדויקת לפי שם הטבלה "app_data"
        response = supabase.table("app_data").select("content").eq("key", "georgia_trip_main_data").execute()
        if response.data and len(response.data) > 0:
            return response.data[0]["content"]
    except Exception as e:
        st.error(f"שגיאה בטעינת הנתונים מ-Supabase: {e}")
    return None

def save_data(data):
    try:
        # פנייה מפורשת ומדויקת לפי שם הטבלה "app_data"
        supabase.table("app_data").upsert(
            {"key": "georgia_trip_main_data", "content": data},
            on_conflict="key"
        ).execute()
        st.toast("💾 נשמר בהצלחה בענן Supabase!", icon="✅")
    except Exception as e:
        st.error(f"שגיאה בשמירת הנתונים ב-Supabase: {e}")

# ==========================================
# פונקציות אחסון קבצים (Supabase Storage)
# ==========================================
def upload_file_to_storage(file_bytes, filename):
    """מעלה קובץ ל-Supabase Storage עם שם קובץ מאובטח ללא עברית או רווחים."""
    try:
        # יוצרים סיומת קובץ בטוחה ושם אנגלי נקי לחלוטין למניעת שגיאות InvalidKey
        ext = filename.split(".")[-1] if "." in filename else "bin"
        safe_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_file.{ext}"
        
        supabase.storage.from_(STORAGE_BUCKET).upload(
            safe_name,
            file_bytes,
            {"upsert": "true"}
        )
        public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(safe_name)
        return safe_name, public_url
    except Exception as e:
        st.error(f"שגיאה בהעלאת הקובץ לאחסון הענן: {e}")
        return None, None

def delete_file_from_storage(storage_path):
    """מוחק קובץ מ-Supabase Storage."""
    try:
        supabase.storage.from_(STORAGE_BUCKET).remove([storage_path])
    except Exception as e:
        st.error(f"שגיאה במחיקת הקובץ מהאחסון: {e}")

# טעינת נתונים קיימים מ-Supabase
saved_data = load_data()

# הגדרת תאריך תחילת הטיול (עם שמירה)
if 'start_date' not in st.session_state:
    if saved_data and "start_date" in saved_data:
        try:
            st.session_state.start_date = date.fromisoformat(saved_data["start_date"])
        except:
            st.session_state.start_date = date.today()
    else:
        st.session_state.start_date = date.today()

if 'expenses' not in st.session_state:
    if saved_data and "expenses" in saved_data:
        st.session_state.expenses = saved_data["expenses"]
    else:
        st.session_state.expenses = [
            {"id": 1, "desc": "מונית משדה התעופה", "category": "תחבורה", "amount": 50, "payer": "אני"},
            {"id": 2, "desc": "ארוחת ערב ראשונה", "category": "אוכל", "amount": 120, "payer": "אני"}
        ]

if 'packing_list' not in st.session_state:
    if saved_data and "packing_list" in saved_data:
        st.session_state.packing_list = saved_data["packing_list"]
    else:
        st.session_state.packing_list = [
            {"item": "דרכונים וביטוח רפואי", "checked": True},
            {"item": "כרטיסי טיסה ושוברים למלונות", "checked": True},
            {"item": "כסף מזומן (דולרים חדשים + לארי)", "checked": False},
            {"item": "תרופות אישיות ועזרה ראשונה", "checked": False},
            {"item": "מתאמים לחשמל ובנקים ניידים", "checked": False},
            {"item": "מעילים חמים (לגודאורי וקזבגי)", "checked": False},
            {"item": "נעלי הליכה נוחות", "checked": False}
        ]

if 'tasks_list' not in st.session_state:
    if saved_data and "tasks_list" in saved_data:
        st.session_state.tasks_list = saved_data["tasks_list"]
    else:
        st.session_state.tasks_list = [
            {"task": "הזמנת רכב השכרה", "checked": True},
            {"task": "וידוא תוקף דרכונים (מעל חצי שנה)", "checked": True},
            {"task": "רכישת חבילת גלישה לחו\"ל", "checked": False},
            {"task": "המרת דולרים חדשים מזומן", "checked": False},
            {"task": "הורדת אפליקציות ניווט וחניה (Waze, ParkMate)", "checked": False}
        ]

if 'journal_notes' not in st.session_state:
    if saved_data and "journal_notes" in saved_data:
        st.session_state.journal_notes = saved_data["journal_notes"]
    else:
        st.session_state.journal_notes = "כאן תוכל לכתוב תובנות, שמות של מסעדות סודיות שמצאתם בדרך, או חוויות מהשטח..."

if 'uploaded_files_meta' not in st.session_state:
    if saved_data and "uploaded_files_meta" in saved_data:
        st.session_state.uploaded_files_meta = saved_data["uploaded_files_meta"]
    else:
        st.session_state.uploaded_files_meta = []

if 'contacts_list' not in st.session_state:
    if saved_data and "contacts_list" in saved_data:
        st.session_state.contacts_list = saved_data["contacts_list"]
    else:
        st.session_state.contacts_list = [
            {"name": "מוקד חירום כללי בגאורגיה", "phone": "112", "role": "משטרה, אמבולנס, כיבוי"},
            {"name": "שגרירות ישראל בטביליסי", "phone": "+995 32 255 65 00", "role": "שגרירות / חירום מדיני"},
            {"name": "חברת השכרת רכב", "phone": "+995 ...", "role": "תמיכה ותקלות רכב"},
            {"name": "ביטוח רפואי (מוקד חו\"ל)", "phone": "+972 ...", "role": "פתיחת תביעות וייעוץ רפואי"}
        ]

if 'total_budget_gel' not in st.session_state:
    if saved_data and "total_budget_gel" in saved_data:
        st.session_state.total_budget_gel = saved_data["total_budget_gel"]
    else:
        st.session_state.total_budget_gel = 4000.0

if 'day_departure_times' not in st.session_state:
    if saved_data and "day_departure_times" in saved_data:
        st.session_state.day_departure_times = saved_data["day_departure_times"]
    else:
        st.session_state.day_departure_times = {}  # ימולא בברירות מחדל בזמן ריצה

def persist_all():
    """שומר את כל הנתונים הדינאמיים ל-Supabase לצמיתות"""
    data = {
        "start_date": st.session_state.start_date.isoformat(),
        "expenses": st.session_state.expenses,
        "packing_list": st.session_state.packing_list,
        "tasks_list": st.session_state.tasks_list,
        "journal_notes": st.session_state.journal_notes,
        "uploaded_files_meta": st.session_state.uploaded_files_meta,
        "contacts_list": st.session_state.contacts_list,
        "total_budget_gel": st.session_state.total_budget_gel,
        "day_departure_times": st.session_state.day_departure_times
    }
    save_data(data)

# ==========================================
# פונקציות עזר
# ==========================================
def calculate_travel_estimation(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    aerial_distance = R * c
    road_distance = aerial_distance * 1.4 
    estimated_hours = road_distance / 55.0 
    
    return road_distance, estimated_hours

def get_departure_hotel_for_day(day_n):
    """המלון שבו התעוררו בבוקר היום הזה (=המלון שכיסה את הלילה הקודם). None ביום ההגעה."""
    if day_n <= 1:
        return None
    for h in hotels_raw:
        if h["check_in_day"] <= (day_n - 1) and h["check_out_day"] >= day_n:
            return h
    return None

def get_night_hotel_for_day(day_n):
    """המלון שבו יישנו בלילה שאחרי היום הזה."""
    for h in hotels_raw:
        if h["check_in_day"] <= day_n <= (h["check_out_day"] - 1):
            return h
    return None

def check_opening_hours(hours_str, arrival_dt, departure_dt):
    """
    בודק אם שעת ההגעה/היציאה המחושבת מתנגשת עם שעות הפתיחה של האתר,
    כשאלו כתובות בפורמט מוכר כמו "10:00 - 17:00". אתרים עם שעות לא-סטנדרטיות
    (24/7, "שעות יום", זמני מופע וכו') לא נבדקים - מוחזר None.
    """
    match = re.search(r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})', hours_str)
    if not match:
        return None
    oh, om, ch, cm = map(int, match.groups())
    open_dt = arrival_dt.replace(hour=oh, minute=om, second=0, microsecond=0)
    close_dt = arrival_dt.replace(hour=ch, minute=cm, second=0, microsecond=0)
    if arrival_dt < open_dt:
        return f"⚠️ מגיעים לפני שעת הפתיחה ({open_dt.strftime('%H:%M')}) - שקלו לצאת מאוחר יותר מהמלון"
    if arrival_dt > close_dt:
        return f"⚠️ מגיעים אחרי שעת הסגירה ({close_dt.strftime('%H:%M')}) - האתר עלול להיות סגור"
    if departure_dt > close_dt:
        return f"⚠️ לפי משך השהות המתוכנן תעזבו ב-{departure_dt.strftime('%H:%M')}, אחרי הסגירה ({close_dt.strftime('%H:%M')}) - קצרו את הביקור או צאו מהמלון מוקדם יותר"
    return None

def build_day_schedule(day_n, day_sites):
    """
    בונה לוח זמנים מפורט ליום נתון: שעת יציאה מהמלון -> נסיעה -> הגעה לאתר -> שהות -> נסיעה לאתר הבא וכו',
    ולבסוף הערכת שעת הגעה למלון הלינה של אותו הלילה.
    day_sites: רשימת שורות (dict-like) מהמסלול של אותו יום, לפי סדר הביקור.
    מחזיר: (departure_hotel, night_hotel, schedule_list, final_arrival_time)
    """
    departure_hotel = get_departure_hotel_for_day(day_n)
    night_hotel = get_night_hotel_for_day(day_n)

    default_time_str = st.session_state.day_departure_times.get(str(day_n), "08:30" if day_n > 1 else "10:00")
    try:
        h, m = map(int, default_time_str.split(":"))
        start_time = datetime.combine(date.today(), datetime.min.time()).replace(hour=h, minute=m)
    except:
        start_time = datetime.combine(date.today(), datetime.min.time()).replace(hour=8, minute=30)

    current_time = start_time
    current_lat, current_lon = (departure_hotel["lat"], departure_hotel["lon"]) if departure_hotel else (None, None)

    schedule = []
    for site in day_sites:
        if current_lat is not None:
            _, travel_h = calculate_travel_estimation(current_lat, current_lon, site["lat"], site["lon"])
        else:
            travel_h = 0.0
        arrival = current_time + timedelta(hours=travel_h)
        departure = arrival + timedelta(hours=float(site["activity_hours"]))
        hours_warning = check_opening_hours(site.get("hours", ""), arrival, departure)
        schedule.append({
            "site": site["site"],
            "icon": site["icon"],
            "travel_minutes": round(travel_h * 60),
            "arrival": arrival,
            "departure": departure,
            "hours_warning": hours_warning,
        })
        current_time = departure
        current_lat, current_lon = site["lat"], site["lon"]

    final_arrival_at_hotel = None
    if night_hotel and current_lat is not None:
        _, travel_h_back = calculate_travel_estimation(current_lat, current_lon, night_hotel["lat"], night_hotel["lon"])
        final_arrival_at_hotel = current_time + timedelta(hours=travel_h_back)

    return departure_hotel, night_hotel, schedule, final_arrival_at_hotel

@st.cache_data(ttl=600)  # מרענן כל 10 דקות בלבד - מונע קריאות רשת מיותרות בכל אינטראקציה
def get_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            temp = data["current_weather"]["temperature"]
            wind = data["current_weather"]["windspeed"]
            return f"{temp}°C, רוח: {wind} קמ\"ש"
    except:
        pass
    return "לא ניתן לטעון תחזית כרגע"

@st.cache_data(ttl=3600)  # שער חליפין חי, מתעדכן פעם בשעה
def get_live_gel_ils_rate():
    try:
        response = requests.get("https://open.er-api.com/v6/latest/GEL", timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get("result") == "success":
                return round(data["rates"]["ILS"], 4)
    except:
        pass
    return None

@st.cache_data(ttl=86400)  # תמונה מוויקיפדיה - נשמרת ביום כדי לא להעמיס בקשות מיותרות
def get_wikipedia_image(page_title, lang="en"):
    """
    שולף את תמונת ה-Infobox הרשמית של ערך בוויקיפדיה (מקור: Wikimedia Commons, רישיון פתוח).
    מחזיר None בשקט אם הערך לא קיים או שאין לו תמונה - כדי שהכרטיס פשוט לא יציג תמונה,
    ולא ישבור את הדף.
    """
    try:
        encoded_title = urllib.parse.quote(page_title.replace(" ", "_"))
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
        response = requests.get(url, timeout=4, headers={"User-Agent": "GeorgiaTripApp/1.0 (family trip planner)"})
        if response.status_code == 200:
            data = response.json()
            thumb = data.get("thumbnail", {}).get("source") or data.get("originalimage", {}).get("source")
            if thumb:
                # מבקשים רזולוציה גבוהה יותר מהתמונה הממוזערת אם אפשר
                thumb = thumb.replace("/220px-", "/600px-").replace("/250px-", "/600px-")
                return thumb
    except:
        pass
    return None

def build_offline_export():
    """בונה קובץ טקסט מלא (מסלול, מלונות, חניות, מסעדות, אנשי קשר) לשימוש אופליין באזורים ללא קליטה."""
    lines = []
    lines.append("=" * 60)
    lines.append("מסלול טיול משפחתי לגאורגיה - קובץ אופליין מלא")
    lines.append(f"תאריך התחלה: {st.session_state.start_date.strftime('%d/%m/%Y')}")
    lines.append("=" * 60)
    lines.append("")

    lines.append("### אנשי קשר וחירום ###")
    for c in st.session_state.contacts_list:
        lines.append(f"- {c['name']} | {c['phone']} | {c.get('role', '')}")
    lines.append("")

    lines.append("### בתי מלון ###")
    for h in df_hotels.itertuples():
        lines.append(f"- {h.hotel} ({h.area}): {h.check_in} עד {h.check_out}")
        lines.append(f"  חניה: {h.parking.split('|')[0].strip()}")
        lines.append(f"  מסעדות: {h.restaurants}")
    lines.append("")

    lines.append("### מסלול יומי מפורט ###")
    for row in df.sort_values("day").itertuples():
        lines.append(f"\nיום {row.day} ({row.actual_date.strftime('%d/%m/%Y')}) - {row.region}")
        lines.append(f"  {row.icon} {row.site}")
        lines.append(f"  שעות: {row.hours} | משך: {row.activity_hours} ש' | נסיעה: {row.travel_time} ש'")
        lines.append(f"  פרטים: {row.details}")
        lines.append(f"  חניה: {row.parking}")
        lines.append(f"  מסעדות: {', '.join(row.restaurants)}")
    lines.append("")

    lines.append("### רשימת ציוד ###")
    for item in st.session_state.packing_list:
        mark = "[V]" if item["checked"] else "[ ]"
        lines.append(f"{mark} {item['item']}")

    return "\n".join(lines)

# ==========================================
# עיצוב מותאם אישית (CSS) - פתרון גלילה לנייד, RTL, ותמיכה ב-Dark Mode
# ==========================================
st.markdown("""
<style>
    .block-container { direction: rtl; text-align: right; }
    
    /* תיקון גלילה בסרגל הצד במובייל */
    section[data-testid="stSidebar"] {
        overflow-y: auto !important;
    }
    section[data-testid="stSidebar"] > div {
        height: 100%;
        overflow-y: auto !important;
    }

    div[data-testid="metric-container"] {
        background: var(--secondary-background-color, #f8f9fa) !important;
        border: 1px solid rgba(128,128,128,0.25);
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        border-right: 5px solid #28a745;
    }
    div[data-testid="metric-container"] label, div[data-testid="metric-container"] div {
        color: var(--text-color, #111111) !important;
    }

    .site-card {
        background-color: var(--secondary-background-color, #ffffff) !important;
        border: 1px solid rgba(128,128,128,0.2);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        margin-bottom: 16px;
        border-right: 6px solid #ff4b4b;
        transition: transform 0.15s ease;
    }
    .site-card:hover { transform: translateX(-2px); }
    .site-card h2, .site-card p, .site-card b {
        color: var(--text-color, #222222) !important;
    }

    .date-badge { background-color: #e3f2fd; color: #1565c0; padding: 4px 10px; border-radius: 15px; font-size: 0.9em; font-weight: bold; margin-right: 10px; }
    .region-badge { color: #ffffff; padding: 3px 10px; border-radius: 15px; font-size: 0.8em; font-weight: bold; margin-right: 8px; }
    .info-box { background-color: rgba(23,162,184,0.08); border-right: 4px solid #17a2b8; padding: 10px 15px; border-radius: 8px; margin-top: 10px; font-size: 0.95em; }

    /* ספירה לאחור עם אנימציית פעימה עדינה */
    @keyframes pulseGlow {
        0%   { box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        50%  { box-shadow: 0 4px 22px rgba(118,75,162,0.45); }
        100% { box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    }
    .countdown-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 15px; border-radius: 12px; text-align: center;
        margin-bottom: 20px; font-weight: bold;
        animation: pulseGlow 3s ease-in-out infinite;
    }

    /* ציר זמן (Timeline) למסלול היומי */
    .timeline-day-header {
        display: flex; align-items: center; gap: 12px;
        margin: 22px 0 12px 0;
    }
    .timeline-day-badge {
        min-width: 42px; height: 42px; border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; display: flex; align-items: center; justify-content: center;
        font-weight: bold; font-size: 1.1em; flex-shrink: 0;
        box-shadow: 0 0 0 4px rgba(118,75,162,0.15);
    }
    .timeline-day-title { font-size: 1.15em; font-weight: bold; }
    .timeline-day-sub { font-size: 0.85em; color: #888; font-weight: normal; }

    /* כפתורי ניווט גדולים ונוחים יותר בסרגל הצד */
    div[role="radiogroup"] label {
        display: block !important;
        padding: 9px 12px !important;
        margin-bottom: 5px !important;
        border-radius: 10px !important;
        background: rgba(128,128,128,0.08) !important;
        transition: all 0.15s ease !important;
        cursor: pointer !important;
    }
    div[role="radiogroup"] label:hover {
        background: rgba(102,126,234,0.18) !important;
        transform: translateX(-3px);
    }
</style>
""", unsafe_allow_html=True)

st.title("🇬🇪 דשבורד טיול משפחתי לגאורגיה")
st.markdown("ניהול מסלול מלא, תקציב הוצאות, פיצול תשלומים, ציוד ארוז, משימות מנהליות, יומן מסע וניהול מסמכים ואנשי קשר.")

# ==========================================
# ווידג'ט ספירה לאחור (Countdown) בראש העמוד
# ==========================================
today_date = date.today()
delta_days = (st.session_state.start_date - today_date).days
if delta_days > 0:
    st.markdown(f"""
    <div class="countdown-box">
        ⏳ עוד {delta_days} ימים בדיוק לתחילת ההרפתקה בגאורגיה! (מתחיל ב-{st.session_state.start_date.strftime('%d/%m/%Y')})
    </div>
    """, unsafe_allow_html=True)
elif delta_days == 0:
    st.markdown("""
    <div class="countdown-box" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
        ✈️ הטיול מתחיל היום! סעו לשלום ותעשו חיים!
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="countdown-box" style="background: linear-gradient(135deg, #4ca1af 0%, #c4e0e5 100%); color: #333;">
        🌟 הטיול בעיצומו או כבר הסתיים! מקווים שנהניתם מכל רגע.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# מסד הנתונים המלא של הטיול
# ==========================================
itinerary = [
    {
        "day": 1, "region": "באטומי (חוף וטיילת)", "site": "שדרות באטומי (Batumi Boulevard)", "hours": "פתוח 24/7", "wiki_title": "Batumi",
        "adult_cost": 0, "child_cost": 0, "activity_hours": 2.5, "travel_time": 0.0, "icon": "🌴", "lat": 41.6530, "lon": 41.6360, 
        "details": "טיול רגלי או רכיבה לאורך הטיילת המרשימה (7 ק\"מ).",
        "parking": "חניה עירונית מוסדרת בבאטומי.",
        "parking_app": "ParkMate Batumi", "parking_link": "https://play.google.com/store/apps/details?id=com.mkakhidze.parkingbatumi",
        "restaurants": ["Retro (מפורסם בזכות האצ'פורי אג'רולי)", "Fanfan (אוכל אירופאי וגאורגי מעוצב)"]
    },
    {
        "day": 1, "region": "באטומי (חוף וטיילת)", "site": "פסל עלי ונינו (Ali and Nino)", "hours": "פתוח 24/7", "wiki_title": "Ali and Nino (sculpture)",
        "adult_cost": 0, "child_cost": 0, "activity_hours": 0.5, "travel_time": 0.3, "icon": "🗿", "lat": 41.6556, "lon": 41.6394, 
        "details": "צפייה בפסל הדינמי המפורסם על קו המים.",
        "parking": "חניה ציבורית סמוך לנמל.",
        "parking_app": "ParkMate Batumi", "parking_link": "https://play.google.com/store/apps/details?id=com.mkakhidze.parkingbatumi",
        "restaurants": ["Chef's Grill", "Batumeti"]
    },
    {
        "day": 2, "region": "באטומי (אטרקציות)", "site": "הדולפינריום של באטומי", "hours": "16:00 / 19:00", "wiki_title": "Batumi",
        "adult_cost": 25, "child_cost": 25, "activity_hours": 2.0, "travel_time": 0.4, "icon": "🐬", "lat": 41.6475, "lon": 41.6231, 
        "details": "מופע דולפינים מרהיב וחווייתי.",
        "parking": "חניון סביב פארק 6 במאי.",
        "parking_app": "ParkMate Batumi", "parking_link": "https://play.google.com/store/apps/details?id=com.mkakhidze.parkingbatumi",
        "restaurants": ["Restaurant 360 (במלון שירטון הסמוך)", "Laguna (מאפיית פחמימות מיתולוגית)"]
    },
    {
        "day": 2, "region": "באטומי (אטרקציות)", "site": "רכבל ארגו (Argo Cable Car)", "hours": "10:00 - 22:00", "wiki_title": "Batumi Cable Car",
        "adult_cost": 30, "child_cost": 15, "activity_hours": 1.5, "travel_time": 0.3, "icon": "🚡", "lat": 41.6472, "lon": 41.6455, "details": "עלייה לתצפית פנורמית מרהיבה.",
        "parking": "חניון רשמי של הרכבל.",
        "parking_app": "ParkMate Batumi", "parking_link": "https://play.google.com/store/apps/details?id=com.mkakhidze.parkingbatumi",
        "restaurants": ["Argo Cafe (בראש ההר)", "Old Boulevard"]
    },
    {
        "day": 2, "region": "באטומי (אטרקציות)", "site": "הגנים הבוטניים של באטומי", "hours": "09:00 - 19:30", "wiki_title": "Batumi Botanical Garden",
        "adult_cost": 30, "child_cost": 30, "activity_hours": 3.0, "travel_time": 0.4, "icon": "🌳", "lat": 41.6963, "lon": 41.7163, "details": "סיור בטבע ירוק ועשיר הנושק לים.",
        "parking": "חניון בכניסה הראשית לגנים.",
        "parking_app": "תשלום במקום", "parking_link": "",
        "restaurants": ["Green Cape Cafe", "מסעדות דגים מקומיות בחוף מחירינגי"]
    },
    {
        "day": 3, "region": "מרטווילי ופרומתאוס", "site": "קניון מרטווילי (Martvili Canyon)", "hours": "10:00 - 17:30", "wiki_title": "Martvili Canyon",
        "adult_cost": 32.25, "child_cost": 32.25, "activity_hours": 2.5, "travel_time": 1.0, "icon": "🛶", "lat": 42.4578, "lon": 42.3767, "details": "שייט בסירות מתנפחות בתוך קניון מים.",
        "parking": "חניון מוסדר של האתר (חינם).",
        "parking_app": "חניה חינם", "parking_link": "",
        "restaurants": ["Dadiani Cafe (בתוך הקניון)", "Oda Family Winery (אוכל ביתי מנגרלואי אותנטי בהזמנה מראש)"]
    },
    {
        "day": 3, "region": "מרטווילי ופרומתאוס", "site": "מערת פרומתאוס (Prometheus Cave)", "hours": "10:00 - 17:00", "wiki_title": "Prometheus Cave",
        "adult_cost": 40, "child_cost": 40, "activity_hours": 2.5, "travel_time": 2.0, "icon": "🦇", "lat": 42.3768, "lon": 42.6009, "details": "מערת נטיפים תת-קרקעית מרהיבה.",
        "parking": "חניון מסודר וחינמי של מתחם המערה.",
        "parking_app": "חניה חינם", "parking_link": "",
        "restaurants": ["Prometheus Cafe", "מסעדות כפריות באזור צקלטובו (Tskaltubo)"]
    },
    {
        "day": 4, "region": "טביליסי", "site": "פארק מתאצמינדה (Mtatsminda Park)", "hours": "11:00 - 22:00", "wiki_title": "Mtatsminda Park",
        "adult_cost": 10, "child_cost": 10, "activity_hours": 3.5, "travel_time": 0.5, "icon": "🎢", "lat": 41.6946, "lon": 44.7865, "details": "פארק שעשועים בראש ההר המשקיף על טביליסי.",
        "parking": "חניון עליון בפארק.",
        "parking_app": "Tbilisi Parking", "parking_link": "https://parking.tbilisi.gov.ge/",
        "restaurants": ["Funicular Restaurant (מסעדה יוקרתית עם נוף מטורף)", "Doner House"]
    },
    {
        "day": 4, "region": "טביליסי", "site": "רכבל ומצודת נריקלה (Narikala)", "hours": "10:00 - 22:00", "wiki_title": "Narikala",
        "adult_cost": 5, "child_cost": 5, "activity_hours": 1.5, "travel_time": 0.3, "icon": "🏰", "lat": 41.6881, "lon": 44.8093, "details": "רכבל, מצודה ופסל אמא גאורגיה.",
        "parking": "חניה עירונית באזור Rike Park.",
        "parking_app": "Tbilisi Parking", "parking_link": "https://parking.tbilisi.gov.ge/",
        "restaurants": ["Machakhela (כיכר הבמבה)", "Samikitno (פתוח 24/7, אוכל גאורגי מעולה)"]
    },
    {
        "day": 5, "region": "דשבשי + קחתי", "site": "גשר היהלום בדשבשי", "hours": "10:00 - 19:00", "wiki_title": "Dashbashi Canyon",
        "adult_cost": 49, "child_cost": 49, "activity_hours": 2.5, "travel_time": 2.0, "icon": "💎", "lat": 41.5975, "lon": 44.0253, "details": "גשר זכוכית שקוף מעל קניון עמוק.",
        "parking": "חניון עפר מסודר בכניסה למתחם.",
        "parking_app": "חניה חינם", "parking_link": "",
        "restaurants": ["Diamond Bridge Panorama Restaurant (מסעדה תלויה עם נוף לקניון)"]
    },
    {
        "day": 5, "region": "דשבשי + קחתי", "site": "מנזר בודבה ועיירת האהבה סיגנאגי", "hours": "שעות יום", "wiki_title": "Bodbe Monastery",
        "adult_cost": 0, "child_cost": 0, "activity_hours": 2.0, "travel_time": 1.5, "icon": "⛪", "lat": 41.6116, "lon": 45.9333, "details": "חומות ציוריות, סמטאות אבן ונוף.",
        "parking": "חניה מוסדרת בכניסה למנזר וברחובות סיגנאגי.",
        "parking_app": "חניה מקומית", "parking_link": "",
        "restaurants": ["Pheasant's Tears (יקב ומסעדה אורגנית מומלצת בסיגנאגי)", "Okro's Wine"]
    },
    {
        "day": 5, "region": "דשבשי + קחתי", "site": "יקב חארבה (Khareba)", "hours": "10:00 - 18:00", "wiki_title": "Kakheti",
        "adult_cost": 25, "child_cost": 10, "activity_hours": 1.5, "travel_time": 0.5, "icon": "🍇", "lat": 41.9366, "lon": 45.8361, "details": "מנהרות אבן לאחסון יין וטעימות.",
        "parking": "חניון ענק ומסודר של היקב.",
        "parking_app": "חניה חינם", "parking_link": "",
        "restaurants": ["Tunnel Restaurant (בתוך המנהרות של היקב)", "Kindzmarauli Marani (בעיר קוורלי - Kvareli)"]
    },
    {
        "day": 6, "region": "הדרך הצבאית וגודאורי", "site": "מסצחתא ומנזר ג'וורי (Mtskheta & Jvari)", "hours": "09:00 - 19:00", "wiki_title": "Mtskheta",
        "adult_cost": 0, "child_cost": 0, "activity_hours": 1.0, "travel_time": 0.4, "icon": "⛰️", "lat": 41.8412, "lon": 44.7196, "details": "הבירה העתיקה של גאורגיה (אתר מורשת עולמית של אונסק\"ו). מנזר ג'וורי יושב על גבעה ומשקיף על מפגש נהרות המטקווארי (קורה) והאראגווי - עוד תופעת \"שני צבעים\" מרהיבה, ונוף מהיפים בגאורגיה.",
        "parking": "חניון מסודר בכניסה לעיר העתיקה ובחניון ג'וורי.",
        "parking_app": "תשלום במקום", "parking_link": "",
        "restaurants": ["מסעדות קטנות ליד כנסיית סווטיצხובלי", "דוכני מאפה מקומי (לוביאני, שוטי פורי)"]
    },
    {
        "day": 6, "region": "הדרך הצבאית וגודאורי", "site": "מצודת אננורי ומאגר ז'ינוואלי", "hours": "09:00 - 19:00", "wiki_title": "Ananuri",
        "adult_cost": 0, "child_cost": 0, "activity_hours": 1.0, "travel_time": 1.5, "icon": "🌊", "lat": 42.1643, "lon": 44.7032, "details": "אגם טורקיז ומצודה היסטורית שמורה.",
        "parking": "חניה לצד הדרך / חניון עפר ליד המצודה.",
        "parking_app": "תשלום במקום", "parking_link": "",
        "restaurants": ["Pasanauri Khinkali House (בדרך, מומלץ לעצור לחינקלי)", "Ananuri Cafe"]
    },
    {
        "day": 6, "region": "הדרך הצבאית וגודאורי", "site": "מפגש נהרות האראגווי הלבן והשחור (Pasanauri)", "hours": "פתוח 24/7", "wiki_title": "Aragvi",
        "adult_cost": 0, "child_cost": 0, "activity_hours": 0.5, "travel_time": 0.2, "icon": "🎨", "lat": 42.3560, "lon": 44.7000, "details": "תופעת טבע נדירה: נהר האראגווי הלבן והשחור נפגשים וזורמים זה לצד זה בלי להתערבב, בגלל הבדלי צפיפות וטמפרטורה - נראה כמו שני צבעים נפרדים באותה גדה. יש דק תצפית קטן עם פסל איילה שמסמן את המקום, ממש בדרך בין אננורי לגודאורי.",
        "parking": "חניה לצד הכביש ליד דק התצפית (עפר, ללא תשלום).",
        "parking_app": "חניה חינם", "parking_link": "",
        "restaurants": ["Pasanauri Khinkali House (באותה עיירה, מומלץ לעצור לחינקלי)", "בקתות קפה קטנות בצד הדרך"]
    },
    {
        "day": 6, "region": "הדרך הצבאית וגודאורי", "site": "אנדרטת גודאורי + רכבת הרים", "hours": "שעות היום", "wiki_title": "Gudauri",
        "adult_cost": 20, "child_cost": 20, "activity_hours": 2.0, "travel_time": 1.0, "icon": "🛷", "lat": 42.4925, "lon": 44.4533, "details": "תצפית נוף וגלישה בקרוניות הרים.",
        "parking": "חניון רחב ידיים לצד האנדרטה.",
        "parking_app": "חניה חינם", "parking_link": "",
        "restaurants": ["Gudauri Lodge Restaurant", "Cafe Quadra"]
    },
    {
        "day": 7, "region": "קזבגי (סטפנצמינדה)", "site": "כנסיית גרגטי", "hours": "אור יום", "wiki_title": "Gergeti Trinity Church",
        "adult_cost": 60, "child_cost": 60, "activity_hours": 2.5, "travel_time": 1.0, "icon": "🏔️", "lat": 42.6629, "lon": 44.6203, "details": "כנסייה מפורסמת למרגלות הר קזבק.",
        "parking": "חניה למעלה ליד הכנסייה (עפר).",
        "parking_app": "חניה חינם", "parking_link": "",
        "restaurants": ["Mountain Freaks Cafe (בסטפנצמינדה)", "Cafe 5047m"]
    },
    {
        "day": 7, "region": "קזבגי (סטפנצמינדה)", "site": "מפל גוולטי (Gveleti Waterfall)", "hours": "אור יום", "wiki_title": "Gveleti Waterfall",
        "adult_cost": 0, "child_cost": 0, "activity_hours": 1.5, "travel_time": 0.3, "icon": "💦", "lat": 42.7194, "lon": 44.6350, "details": "הליכה קלה (כ-45 דקות הלוך-חזור) לעבר מפל מרשים בקניון גוולטי, צפונית לסטפנצמינדה לכיוון גבול רוסיה. טבע יפה ופחות תיירותי מגרגטי.",
        "parking": "חניית עפר קטנה בתחילת השביל.",
        "parking_app": "חניה חינם", "parking_link": "",
        "restaurants": ["אין מסעדות בשטח - מומלץ לחזור לסטפנצמינדה"]
    },
    {
        "day": 7, "region": "קזבגי (סטפנצמינדה)", "site": "מלון Rooms Kazbegi", "hours": "12:00 - 22:00", "wiki_title": "Stepantsminda",
        "adult_cost": 40, "child_cost": 30, "activity_hours": 1.5, "travel_time": 0.3, "icon": "☕", "lat": 42.6566, "lon": 44.6464, "details": "ארוחה או קפה במרפסת המפורסמת עם נוף להר.",
        "parking": "חניה מסודרת לאורחי המלון והמסעדה.",
        "parking_app": "חניה חינם", "parking_link": "",
        "restaurants": ["Rooms Hotel Restaurant (אוכל אירופאי-גאורגי עילי)", "Sno Cafe"]
    },
    {
        "day": 8, "region": "טביליסי העתיקה", "site": "מרחצאות חמי אורבליאני", "hours": "08:00 - 23:00", "wiki_title": "Abanotubani",
        "adult_cost": 75, "child_cost": 0, "activity_hours": 1.5, "travel_time": 0.3, "icon": "🛁", "lat": 41.6880, "lon": 44.8115, "details": "חדר פרטי במרחצאות הגופרית.",
        "parking": "חניון רחוב בתשלום עירוני.",
        "parking_app": "Tbilisi Parking", "parking_link": "https://parking.tbilisi.gov.ge/",
        "restaurants": ["Culinarium Khasheria (שף לוקה טרזני - מעולה)", "Gastro Chef"]
    },
    {
        "day": 8, "region": "טביליסי העתיקה", "site": "מפל לגווטכבי וגשר השלום", "hours": "24/7", "wiki_title": "Bridge of Peace (Tbilisi)",
        "adult_cost": 0, "child_cost": 0, "activity_hours": 2.0, "travel_time": 0.3, "icon": "🌉", "lat": 41.6865, "lon": 44.8090, "details": "מפל טבעי המסתתר בלב העיר.",
        "parking": "חניון Rike Park הסמוך.",
        "parking_app": "Tbilisi Parking", "parking_link": "https://parking.tbilisi.gov.ge/",
        "restaurants": ["Pur Pur (מסעדה וינטג' קסומה במרכז)", "Shavi Lomi (מסעדת גורמה מקומית מדהימה - דורשת הזמנה מראש)"]
    },
    {
        "day": 9, "region": "שקווטילי", "site": "הפארק הדנדרולוגי", "hours": "10:00 - 18:00", "wiki_title": "Shekvetili",
        "adult_cost": 0, "child_cost": 0, "activity_hours": 2.5, "travel_time": 1.0, "icon": "🦩", "lat": 41.9372, "lon": 41.7644, "details": "פארק עצום עם ציפורים ופלמינגו.",
        "parking": "חניון מסודר וחינמי בכניסה לפארק.",
        "parking_app": "חניה חינם", "parking_link": "",
        "restaurants": ["Black Sea Arena Cafe", "מסעדות חוף באזור שקווטילי ואורקיבי"]
    },
    {
        "day": 9, "region": "שקווטילי", "site": "פארק המוזיקאים", "hours": "24/7", "wiki_title": "Shekvetili",
        "adult_cost": 0, "child_cost": 0, "activity_hours": 1.5, "travel_time": 0.3, "icon": "🎵", "lat": 41.9167, "lon": 41.7681, "details": "יער קסום עם פסלי מוזיקאים.",
        "parking": "חניה לצד הפארק ביער.",
        "parking_app": "חניה חינם", "parking_link": "",
        "restaurants": ["Magnetic Beach Cafe", "Paragraph Resort Restaurants"]
    },
    {
        "day": 10, "region": "באטומי (סיום)", "site": "שוק הדגים של באטומי", "hours": "09:00 - 20:00", "wiki_title": "Batumi",
        "adult_cost": 40, "child_cost": 30, "activity_hours": 2.0, "travel_time": 0.0, "icon": "🐟", "lat": 41.6495, "lon": 41.6521, "details": "בוחרים דגים ומבשלים במקום.",
        "parking": "חניון השוק.",
        "parking_app": "ParkMate Batumi", "parking_link": "https://play.google.com/store/apps/details?id=com.mkakhidze.parkingbatumi",
        "restaurants": ["שוק הדגים עצמו (בוחרים דג טרי בצד ומבקשים שיבשלו במסעדות שבתוך השוק)", "Station Cafe"]
    }
]

# ==========================================
# מיפוי צבעים לכל אזור במסלול (לשימוש בכרטיסים ובמפה)
# ==========================================
REGION_PALETTE = ["#ff6b6b", "#4ecdc4", "#ffa62b", "#6c5ce7", "#00b894",
                   "#0984e3", "#e17055", "#fd79a8", "#00cec9", "#fab1a0"]
_region_order = []
for _item in itinerary:
    if _item["region"] not in _region_order:
        _region_order.append(_item["region"])
REGION_COLOR_MAP = {region: REGION_PALETTE[i % len(REGION_PALETTE)] for i, region in enumerate(_region_order)}

# ==========================================
# סרגל צד (Sidebar)
# ==========================================
with st.sidebar:
    try:
        st.image("IMG_1101.jpg", use_container_width=True, caption="המשפחה המטיילת ✈️")
    except FileNotFoundError:
        pass  
        
    st.markdown("---")
    st.header("📅 תאריכים והרכב")
    
    new_start_date = st.date_input("תאריך תחילת הטיול:", value=st.session_state.start_date)
    if new_start_date != st.session_state.start_date:
        st.session_state.start_date = new_start_date
        persist_all()
        st.rerun()
    
    adults = st.number_input("מספר מבוגרים", min_value=1, value=2, step=1)
    children = st.number_input("מספר ילדים", min_value=0, value=2, step=1)
    
    st.markdown("---")
    st.header("💰 בקרת תקציב כללי")
    new_budget = st.number_input("תקציב כולל מוגדר (GEL):", min_value=100.0, value=float(st.session_state.total_budget_gel), step=100.0)
    if new_budget != st.session_state.total_budget_gel:
        st.session_state.total_budget_gel = new_budget
        persist_all()
        
    st.markdown("---")
    st.header("💱 המרת מטבע מהירה")

    live_rate = get_live_gel_ils_rate()
    if live_rate:
        st.caption(f"✅ שער חי מהרשת: 1 GEL = {live_rate} ₪ (מתעדכן כל שעה)")
        default_rate = live_rate
    else:
        st.caption("⚠️ לא ניתן לטעון שער חי כרגע - נעשה שימוש בערך ידני.")
        default_rate = 1.38

    gel_input = st.number_input("סכום בלארי (GEL):", min_value=0.0, value=100.0, step=10.0)
    exchange_rate = st.number_input("שער לארי לשקל:", value=float(default_rate), step=0.01)
    ils_calc = gel_input * exchange_rate
    st.info(f"💡 שווה ערך: **{ils_calc:,.1f} ₪** | טיפ מומלץ (10%): **{gel_input*0.1:.1f} לארי**")

    st.markdown("---")
    st.header("⚙️ בקרת מסלול")
    
    selected_tab = st.radio(
        "בחר מצב תצוגה:", 
        options=[
            "📅 פירוט מסלול ואטרקציות", 
            "🏨 מלונות", 
            "🚗 מחשבון ניווט וזמני נסיעה",
            "📊 דשבורד עלויות ופיצול תשלומים",
            "🎒 רשימת ציוד (Packing List)",
            "📋 משימות טרום-טיול",
            "📓 יומן מסע אישי",
            "📄 שוברים ומסמכים דיגיטליים",
            "📞 אנשי קשר וחירום",
            "🍷 אירוח משפחתי וסופרה",
            "🚨 חירום וטיפים לשטח",
            "🗺️ מפת האטרקציות"
        ],
        index=0
    )
    
    st.markdown("---")
    
    max_days = max([item['day'] for item in itinerary])
    day_options = ["הכל"]
    for d in range(1, max_days + 1):
        actual_date = st.session_state.start_date + timedelta(days=d-1)
        day_options.append(f"יום {d} ({actual_date.strftime('%d/%m/%Y')})")
        
    selected_day_str = st.selectbox("סינון לפי יום בטיול:", options=day_options)
    
    if selected_day_str != "הכל":
        selected_day = int(selected_day_str.split(" ")[1])
    else:
        selected_day = "הכל"

    # אזור גיבוי נתונים
    st.markdown("---")
    st.header("💾 גיבוי ושחזור")
    
    backup_json = json.dumps({
        "start_date": st.session_state.start_date.isoformat(),
        "expenses": st.session_state.expenses,
        "packing_list": st.session_state.packing_list,
        "tasks_list": st.session_state.tasks_list,
        "journal_notes": st.session_state.journal_notes,
        "uploaded_files_meta": st.session_state.uploaded_files_meta,
        "contacts_list": st.session_state.contacts_list,
        "total_budget_gel": st.session_state.total_budget_gel
    }, ensure_ascii=False, indent=4)
    
    st.download_button(
        label="📥 הורד קובץ גיבוי מלא",
        data=backup_json,
        file_name="georgia_trip_backup.json",
        mime="application/json"
    )

# עיבוד הנתונים
df = pd.DataFrame(itinerary)
df['total_cost_gel'] = (adults * df['adult_cost']) + (children * df['child_cost'])
df['total_hours'] = df['activity_hours'] + df['travel_time']
df['actual_date'] = df['day'].apply(lambda d: st.session_state.start_date + timedelta(days=d-1))

# בסיס נתונים למלונות
hotels_raw = [
    {
        "hotel": "King Suite Black Sea View Hotel", "check_in_day": 1, "check_out_day": 3, "area": "באטומי",
        "lat": 41.6500, "lon": 41.6360,
        "parking": "חניה פרטית של המלון / חניה ברחוב סמוך.",
        "parking_app": "ParkMate Batumi", "parking_link": "https://play.google.com/store/apps/details?id=com.mkakhidze.parkingbatumi",
        "restaurants": ["Retro (חצ'פורי)", "Fanfan", "Heart of Batumi"]
    },
    {
        "hotel": "Novotel Tbilisi Center", "check_in_day": 3, "check_out_day": 6, "area": "טביליסי",
        "lat": 41.6941, "lon": 44.8073,
        "parking": "חניון תת-קרקעי פרטי של המלון.",
        "parking_app": "Tbilisi Parking", "parking_link": "https://parking.tbilisi.gov.ge/",
        "restaurants": ["Shavi Lomi", "Culinarium Khasheria", "Pur Pur"]
    },
    {
        "hotel": "Gudauri Lodge", "check_in_day": 6, "check_out_day": 8, "area": "גודאורי",
        "lat": 42.4756, "lon": 44.4770,
        "parking": "חניה מסודרת חינם לאורחי המלון בחזית.",
        "parking_app": "חניה חינם", "parking_link": "",
        "restaurants": ["מסעדת המלון הראשית", "Cafe Quadra"]
    },
    {
        "hotel": "Novotel Tbilisi Center", "check_in_day": 8, "check_out_day": 9, "area": "טביליסי",
        "lat": 41.6941, "lon": 44.8073,
        "parking": "חניון תת-קרקעי פרטי של המלון.",
        "parking_app": "Tbilisi Parking", "parking_link": "https://parking.tbilisi.gov.ge/",
        "restaurants": ["Samikitno", "Machakhela"]
    },
    {
        "hotel": "King Suite Black Sea View Hotel", "check_in_day": 9, "check_out_day": 11, "area": "באטומי",
        "lat": 41.6500, "lon": 41.6360,
        "parking": "חניה פרטית של המלון / ברחוב סמוך.",
        "parking_app": "ParkMate Batumi", "parking_link": "https://play.google.com/store/apps/details?id=com.mkakhidze.parkingbatumi",
        "restaurants": ["Retro", "Chef's Grill"]
    }
]

hotels_processed = []
for h in hotels_raw:
    ci_date = st.session_state.start_date + timedelta(days=h["check_in_day"]-1)
    co_date = st.session_state.start_date + timedelta(days=h["check_out_day"]-1)
    
    parking_display = h["parking"]
    if h["parking_link"]:
        parking_display += f" | <a href='{h['parking_link']}' target='_blank'><b>[אפליקציה: {h['parking_app']}]</b></a>"
        
    hotels_processed.append({
        "hotel": h["hotel"],
        "area": h["area"],
        "check_in": ci_date.strftime('%d/%m/%Y'),
        "check_out": co_date.strftime('%d/%m/%Y'),
        "parking": parking_display,
        "restaurants": ", ".join(h["restaurants"])
    })
df_hotels = pd.DataFrame(hotels_processed)

filtered_df = df.copy()
if selected_day != "הכל":
    filtered_df = filtered_df[filtered_df['day'] == selected_day]

# ==========================================
# תצוגה 1: פירוט מסלול ומזג אוויר חי (בעיצוב ציר-זמן)
# ==========================================
if selected_tab == "📅 פירוט מסלול ואטרקציות":
    st.subheader("📍 אטרקציות המסלול, חניות ואפליקציות תשלום")
    
    with st.expander("🌤️ בדוק תחזית מזג אוויר חיה באזורי הטיול"):
        w_col1, w_col2, w_col3, w_col4 = st.columns(4)
        with w_col1:
            st.metric("באטומי (חוף)", get_weather(41.65, 41.63))
        with w_col2:
            st.metric("טביליסי (בירה)", get_weather(41.69, 44.80))
        with w_col3:
            st.metric("גודאורי (הרים)", get_weather(42.49, 44.45))
        with w_col4:
            st.metric("קזבגי (פסגה)", get_weather(42.65, 44.64))
            
    st.markdown("---")
    
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        csv = filtered_df.drop(columns=['restaurants', 'parking', 'parking_app', 'parking_link']).to_csv(index=False).encode('utf-8-sig')
        st.download_button(label="📥 הורד מסלול לאקסל", data=csv, file_name='georgia_trip.csv', mime='text/csv')
    with col_exp2:
        offline_text = build_offline_export()
        st.download_button(
            label="📴 הורד מסלול מלא לשימוש אופליין (בלי אינטרנט)",
            data=offline_text.encode('utf-8'),
            file_name='georgia_trip_offline.txt',
            mime='text/plain',
            help="קובץ טקסט מלא עם כל המסלול, החניות, המסעדות ואנשי הקשר - שימושי בהרים ללא קליטה."
        )
    st.markdown("---")

    st.caption("📷 תמונות האתרים נשלפות אוטומטית מוויקיפדיה (Wikimedia Commons, רישיון פתוח). לא לכל אתר נמצאה תמונה מתאימה.")

    # מקרא צבעים לפי אזור
    legend_html = "<div style='margin-bottom:18px;'>"
    for region, color in REGION_COLOR_MAP.items():
        legend_html += f"<span class='region-badge' style='background-color:{color};'>{region}</span> "
    legend_html += "</div>"
    st.markdown(legend_html, unsafe_allow_html=True)

    current_day_marker = None
    for idx, row in filtered_df.iterrows():
        # כותרת יום חדשה בציר הזמן כאשר עוברים ליום הבא
        if row['day'] != current_day_marker:
            current_day_marker = row['day']
            date_str_marker = row['actual_date'].strftime("%d/%m/%Y")
            st.markdown(f"""
            <div class="timeline-day-header">
                <div class="timeline-day-badge">{row['day']}</div>
                <div>
                    <div class="timeline-day-title">יום {row['day']} — {row['region']}</div>
                    <div class="timeline-day-sub">{date_str_marker}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if row['day'] == 9:
                st.warning("⚠️ יום נהיגה ארוך: מטביליסי לבאטומי (עם עצירה בשקווטילי) זה כ-370 ק\"מ - כ-5-6 שעות נהיגה נטו, מעבר לזמן שנספר להלן בין העצירות עצמן. מומלץ לצאת מוקדם ולתכנן הפסקות דלק ומנוחה.")

            # ---- לוח זמנים יומי: שעת יציאה מהמלון + חישוב נסיעות ושהות ----
            dep_key = str(row['day'])
            default_dep = st.session_state.day_departure_times.get(dep_key, "08:30" if row['day'] > 1 else "10:00")
            try:
                default_dep_time = datetime.strptime(default_dep, "%H:%M").time()
            except:
                default_dep_time = datetime.strptime("08:30", "%H:%M").time()

            dep_col1, dep_col2 = st.columns([1, 3])
            with dep_col1:
                dep_time_input = st.time_input(
                    "שעת יציאה מהמלון" if row['day'] > 1 else "שעת התחלה (יום הגעה)",
                    value=default_dep_time,
                    key=f"dep_time_{row['day']}"
                )
            new_dep_str = dep_time_input.strftime("%H:%M")
            if st.session_state.day_departure_times.get(dep_key) != new_dep_str:
                st.session_state.day_departure_times[dep_key] = new_dep_str
                persist_all()

            day_sites_for_schedule = filtered_df[filtered_df['day'] == row['day']].to_dict('records')
            departure_hotel, night_hotel, day_schedule, final_arrival = build_day_schedule(row['day'], day_sites_for_schedule)

            with dep_col2:
                if departure_hotel:
                    st.caption(f"🏨 יוצאים מ: {departure_hotel['hotel']} ({departure_hotel['area']})")
                else:
                    st.caption("✈️ יום הגעה - זמני ההתחלה תלויים בשעת הנחיתה שלכם, התאימו את שעת ההתחלה בהתאם")

            timeline_rows = ""
            for s in day_schedule:
                travel_note = f"🚗 {s['travel_minutes']} דק' נסיעה &nbsp;→&nbsp; " if s['travel_minutes'] > 0 else ""
                timeline_rows += f"<div style='padding:4px 0;'>{travel_note}<b>{s['icon']} {s['site']}</b>: הגעה <b>{s['arrival'].strftime('%H:%M')}</b> — יציאה <b>{s['departure'].strftime('%H:%M')}</b></div>"
                if s.get('hours_warning'):
                    timeline_rows += f"<div style='padding:0 0 4px 0; color:#c0392b; font-size:0.9em;'>{s['hours_warning']}</div>"
            if final_arrival and night_hotel:
                timeline_rows += f"<div style='padding:6px 0 0 0; color:#667eea; font-weight:bold;'>🏨 הגעה משוערת ל-{night_hotel['hotel']}: {final_arrival.strftime('%H:%M')}</div>"
            st.markdown(f"<div class='info-box' style='margin-bottom:16px;'>{timeline_rows}</div>", unsafe_allow_html=True)
            st.caption("⏱️ זמני הנסיעה מבוססים על הערכת קו-אווירי + 40% (בקירוב לכביש הררי) במהירות ממוצעת 55 קמ\"ש - התאימו לפי תנאי השטח בפועל. בדיקת שעות הפתיחה עובדת רק לאתרים עם טווח שעות מוגדר (למשל \"10:00 - 17:00\"); אתרים עם \"24/7\", \"שעות יום\" או זמני מופע ספציפיים לא נבדקים אוטומטית.")

        date_str = row['actual_date'].strftime("%d/%m/%Y")
        item_cost_ils = row['total_cost_gel'] * exchange_rate
        region_color = REGION_COLOR_MAP.get(row['region'], '#ff4b4b')
        
        restaurants_html = ""
        for rest in row['restaurants']:
            rest_encoded = urllib.parse.quote(f"{rest}, {row['region']}, Georgia")
            restaurants_html += f"&bull; <a href='https://www.google.com/maps/search/?api=1&query={rest_encoded}' target='_blank'>{rest}</a><br>"
        
        parking_text = row['parking']
        if row['parking_link']:
            parking_text += f" | <a href='{row['parking_link']}' target='_blank'><b>[פתח את {row['parking_app']}]</b></a>"

        # שליפת תמונה חופשית-רישיון מוויקיפדיה עבור האתר (בזמן אמת, עם קאש ל-24 שעות)
        wiki_image_url = get_wikipedia_image(row.get('wiki_title', row['site']))

        card_content = f"<div class='site-card' style='border-right-color: {region_color};'>"
        if wiki_image_url:
            card_content += f"<img src='{wiki_image_url}' style='width:100%; max-height:260px; object-fit:cover; border-radius:10px; margin-bottom:12px;' loading='lazy' alt='{row['site']}'>"
        card_content += f"<h2>{row['icon']} <span class='date-badge'>{date_str}</span> {row['site']}</h2>"
        card_content += f"<p><b>📍 אזור:</b> {row['region']}</p>"
        card_content += f"<p><b>📝 פרטים:</b> {row['details']}</p>"
        card_content += f"<p>🕒 <b>שעות פתיחה:</b> {row['hours']}</p>"
        card_content += f"<p>⏱️ <b>משך פעילות:</b> {row['activity_hours']} שעות &nbsp;&nbsp;|&nbsp;&nbsp; 🚗 <b>זמן נסיעה:</b> {row['travel_time']} שעות</p>"
        card_content += f"<p style='color: #2e7d32; font-weight: bold;'>💰 עלות עבור {adults} מבוגרים ו-{children} ילדים: {row['total_cost_gel']} לארי (~ {item_cost_ils:,.0f} ₪)</p>"
        card_content += "<div class='info-box'>"
        card_content += f"<p><b>🅿️ מידע ואפליקציית חניה:</b> {parking_text}</p>"
        card_content += f"<p><b>🍽️ מסעדות מומלצות בסביבה:</b><br>{restaurants_html}</p>"
        card_content += "</div></div>"
        
        st.markdown(card_content, unsafe_allow_html=True)

# ==========================================
# תצוגה 2: מלונות וניווט
# ==========================================
elif selected_tab == "🏨 מלונות":
    st.subheader("🏨 בתי המלון שלנו, הסדרי חניה ואפליקציות")
    
    for idx, h in df_hotels.iterrows():
        hotel_content = "<div class='site-card' style='border-right-color: #3b82f6;'>"
        hotel_content += f"<h2>🏨 {h['hotel']} ({h['area']})</h2>"
        hotel_content += f"<p><b>📅 תקופת שהייה:</b> {h['check_in']} עד {h['check_out']}</p>"
        hotel_content += "<div class='info-box'>"
        hotel_content += f"<p><b>🅿️ הסדר חניה במלון:</b> {h['parking']}</p>"
        hotel_content += f"<p><b>🍽️ מסעדות באזור המלון:</b> {h['restaurants']}</p>"
        hotel_content += "</div></div>"
        
        st.markdown(hotel_content, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("🚗 תכנון נסיעה מהמלון")
    
    unique_hotels = df_hotels["hotel"].unique()
    origin_hotel = st.selectbox("אנחנו יוצאים מ:", unique_hotels)
    destination = st.text_input("לאן נוסעים? (למשל: Kazbegi, Martvili Canyon)", "Kazbegi")
    
    if st.button("הפק קישורי ניווט", type="primary"):
        if destination:
            origin_encoded = urllib.parse.quote(f"{origin_hotel}, Georgia")
            destination_encoded = urllib.parse.quote(f"{destination}, Georgia")
            
            gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={origin_encoded}&destination={destination_encoded}&travelmode=driving"
            waze_url = f"https://waze.com/ul?q={destination_encoded}&navigate=yes"
            
            st.success("הקישורים מוכנים!")
            col_nav1, col_nav2 = st.columns(2)
            with col_nav1:
                st.markdown(f"""
                <a href="{gmaps_url}" target="_blank" style="display: block; padding: 12px; background-color: #4285F4; color: white; text-align: center; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                    🗺️ פתח ב-Google Maps
                </a>
                """, unsafe_allow_html=True)
            with col_nav2:
                st.markdown(f"""
                <a href="{waze_url}" target="_blank" style="display: block; padding: 12px; background-color: #33ccff; color: white; text-align: center; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                    🚗 פתח ב-Waze
                </a>
                """, unsafe_allow_html=True)
        else:
            st.warning("אנא הזן יעד כדי לחשב מסלול.")

# ==========================================
# תצוגה 3: מחשבון ניווט בין אטרקציות
# ==========================================
elif selected_tab == "🚗 מחשבון ניווט וזמני נסיעה":
    st.subheader("🚗 מחשבון זמני נסיעה וניווט בגאורגיה")
    st.markdown("בחר יעד מוצא ויעד להגעה כדי לקבל הערכת זמן נסיעה וקישורי ניווט ישירים.")
    st.markdown("---")
    
    all_sites = df['site'].tolist()
    
    col1, col2 = st.columns(2)
    with col1:
        origin = st.selectbox("📍 בחר יעד מוצא:", options=all_sites, index=0)
    with col2:
        default_dest_index = 1 if len(all_sites) > 1 else 0
        destination = st.selectbox("🏁 בחר יעד הבא:", options=all_sites, index=default_dest_index)
        
    if origin and destination:
        if origin == destination:
            st.warning("בחרת את אותו היעד במוצא וביעד.")
        else:
            loc1 = df[df['site'] == origin].iloc[0]
            loc2 = df[df['site'] == destination].iloc[0]
            
            km_dist, est_hours = calculate_travel_estimation(loc1['lat'], loc1['lon'], loc2['lat'], loc2['lon'])
            
            hours = int(est_hours)
            minutes = int((est_hours - hours) * 60)
            
            gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={loc1['lat']},{loc1['lon']}&destination={loc2['lat']},{loc2['lon']}"
            waze_url = f"https://waze.com/ul?ll={loc2['lat']},{loc2['lon']}&navigate=yes"
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.success(f"**מרחק משוער בכביש:** {km_dist:.1f} ק\"מ")
            if hours > 0:
                st.info(f"**זמן נסיעה מוערך:** {hours} שעות ו-{minutes} דקות")
            else:
                st.info(f"**זמן נסיעה מוערך:** {minutes} דקות")
                
            st.markdown("<br>", unsafe_allow_html=True)
            col_n1, col_n2 = st.columns(2)
            with col_n1:
                st.markdown(f"""
                <a href="{gmaps_url}" target="_blank" style="display: block; padding: 12px; background-color: #4285F4; color: white; text-align: center; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                    🗺️ פתח ב-Google Maps
                </a>
                """, unsafe_allow_html=True)
            with col_n2:
                st.markdown(f"""
                <a href="{waze_url}" target="_blank" style="display: block; padding: 12px; background-color: #33ccff; color: white; text-align: center; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                    🚗 פתח ב-Waze
                </a>
                """, unsafe_allow_html=True)

# ==========================================
# תצוגה 4: דשבורד עלויות ופיצול תשלומים
# ==========================================
elif selected_tab == "📊 דשבורד עלויות ופיצול תשלומים":
    st.subheader("📊 דשבורד עלויות, פיצול הוצאות משפחתי ובקרת תקציב")
    st.markdown("---")
    
    total_cost_gel = filtered_df['total_cost_gel'].sum()
    total_cost_ils = total_cost_gel * exchange_rate
    
    actual_spent_gel = sum([e['amount'] for e in st.session_state.expenses])
    actual_spent_ils = actual_spent_gel * exchange_rate
    
    # מד התקדמות תקציב
    budget_limit = st.session_state.total_budget_gel
    budget_progress = min(actual_spent_gel / budget_limit, 1.0) if budget_limit > 0 else 0
    
    st.markdown(f"### 🎯 מעקב תקציב: {actual_spent_gel:,.0f} GEL מתוך {budget_limit:,.0f} GEL מוגדרים")
    st.progress(budget_progress)
    if actual_spent_gel > budget_limit:
        st.warning("⚠️ שימו לב! חרגתם מהתקציב שהוגדר לטיול.")
    else:
        st.success(f"✨ נותרו עוד {budget_limit - actual_spent_gel:,.0f} GEL בתקציב.")

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 עלות אטרקציות תאורטית", f"{total_cost_gel:,.0f} GEL", f"~ {total_cost_ils:,.0f} ₪")
    col2.metric("קטגוריית הוצאות שוטפות", f"{actual_spent_gel:,.0f} GEL", f"~ {actual_spent_ils:,.0f} ₪")
    col3.metric("⏱️ סך שעות פעילות", f"{filtered_df['activity_hours'].sum():,.1f} שעות")

    st.markdown("---")
    st.subheader("📈 ניתוח חזותי של ההוצאות")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        if st.session_state.expenses:
            cat_summary = {}
            for e in st.session_state.expenses:
                cat_summary[e['category']] = cat_summary.get(e['category'], 0) + e['amount']
            fig_pie = px.pie(
                names=list(cat_summary.keys()),
                values=list(cat_summary.values()),
                title="התפלגות הוצאות בפועל לפי קטגוריה",
                hole=0.45
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(margin=dict(t=50, b=0, l=0, r=0), showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("אין עדיין הוצאות בפועל כדי להציג גרף.")

    with chart_col2:
        daily_cost = df.groupby('day')['total_cost_gel'].sum().reset_index()
        daily_cost['date_label'] = daily_cost['day'].apply(
            lambda d: (st.session_state.start_date + timedelta(days=d - 1)).strftime('%d/%m')
        )
        fig_bar = px.bar(
            daily_cost, x='date_label', y='total_cost_gel',
            title="עלות אטרקציות תאורטית לפי יום (GEL)",
            labels={'date_label': 'תאריך', 'total_cost_gel': 'עלות (GEL)'},
            color='total_cost_gel',
            color_continuous_scale='Purples'
        )
        fig_bar.update_layout(margin=dict(t=50, b=0, l=0, r=0), coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("---")
    st.subheader("👥 סיכום פיצול הוצאות לפי משלם")
    payer_summary = {}
    for e in st.session_state.expenses:
        p = e.get("payer", "אני")
        payer_summary[p] = payer_summary.get(p, 0) + e['amount']
    
    p_cols = st.columns(max(len(payer_summary), 1))
    for i, (payer, amt) in enumerate(payer_summary.items()):
        with p_cols[i % len(p_cols)]:
            st.metric(f"שולם על ידי: {payer}", f"{amt:,.1f} GEL", f"~ {amt*exchange_rate:,.0f} ₪")

    st.markdown("---")
    st.subheader("➕ הוסף הוצאה חדשה בפועל")
    with st.form("add_expense_form", clear_on_submit=True):
        e_desc = st.text_input("תיאור ההוצאה (למשל: תדלוק, חניה בבאטומי):")
        e_cat = st.selectbox("קטגוריה:", ["אוכל", "תחבורה ודלק", "חניה", "קניות", "שונות"])
        e_amount = st.number_input("סכום בלארי (GEL):", min_value=1.0, value=20.0)
        e_payer = st.selectbox("מי שילם?", ["אני", "משפחה שנייה / חברים", "התחלקנו שווה בשווה"])
        submitted = st.form_submit_button("הוסף הוצאה לרשימה")
        if submitted and e_desc.strip():
            new_id = max([e.get("id", 0) for e in st.session_state.expenses], default=0) + 1
            st.session_state.expenses.append({
                "id": new_id, 
                "desc": e_desc.strip(), 
                "category": e_cat, 
                "amount": e_amount,
                "payer": e_payer
            })
            persist_all()
            st.success("ההוצאה נוספה ונשמרה לצמיתות!")
            st.rerun()
                
    if st.session_state.expenses:
        st.markdown("---")
        st.subheader("📋 ניהול הוצאות קיימות (מחיקה ועריכה)")
        
        for idx, exp in enumerate(st.session_state.expenses):
            with st.expander(f"📝 {exp['desc']} — {exp['amount']} GEL ({exp['category']}) | שולם ע\"י: {exp.get('payer', 'אני')}"):
                with st.form(f"edit_exp_{exp.get('id', idx)}"):
                    ed_desc = st.text_input("תיאור ההוצאה:", value=exp['desc'], key=f"ed_desc_{idx}")
                    categories = ["אוכל", "תחבורה ודלק", "חניה", "קניות", "שונות"]
                    default_cat_idx = categories.index(exp['category']) if exp['category'] in categories else 0
                    ed_cat = st.selectbox("קטגוריה:", categories, index=default_cat_idx, key=f"ed_cat_{idx}")
                    ed_amount = st.number_input("סכום בלארי (GEL):", min_value=1.0, value=float(exp['amount']), key=f"ed_amt_{idx}")
                    
                    payers_list = ["אני", "משפחה שנייה / חברים", "התחלקנו שווה בשווה"]
                    curr_payer = exp.get('payer', 'אני')
                    default_payer_idx = payers_list.index(curr_payer) if curr_payer in payers_list else 0
                    ed_payer = st.selectbox("מי שילם?", payers_list, index=default_payer_idx, key=f"ed_payer_{idx}")
                    
                    col_b1, col_b2 = st.columns(2)
                    save_clicked = col_b1.form_submit_button("💾 שמור שינויים")
                    delete_clicked = col_b2.form_submit_button("🗑️ מחק הוצאה זו")
                    
                    if save_clicked:
                        st.session_state.expenses[idx]["desc"] = ed_desc
                        st.session_state.expenses[idx]["category"] = ed_cat
                        st.session_state.expenses[idx]["amount"] = ed_amount
                        st.session_state.expenses[idx]["payer"] = ed_payer
                        persist_all()
                        st.success("ההוצאה עודכנה בהצלחה!")
                        st.rerun()
                        
                    if delete_clicked:
                        st.session_state.expenses.pop(idx)
                        persist_all()
                        st.success("ההוצאה נמחקה!")
                        st.rerun()

# ==========================================
# תצוגה 5: רשימת ציוד (Packing List)
# ==========================================
elif selected_tab == "🎒 רשימת ציוד (Packing List)":
    st.subheader("🎒 רשימת ציוד ומזוודות למשפחה")

    total_items = len(st.session_state.packing_list)
    checked_items = sum(1 for i in st.session_state.packing_list if i["checked"])
    pack_progress = (checked_items / total_items) if total_items > 0 else 0
    st.markdown(f"### 📦 התקדמות אריזה: {checked_items} מתוך {total_items} פריטים")
    st.progress(pack_progress)

    st.markdown("סמן את הפריטים שכבר ארזתם – השינויים נשמרים באופן אוטומטי לצמיתות:")
    st.markdown("---")
    
    data_changed = False
    for i, item_dict in enumerate(st.session_state.packing_list):
        new_status = st.checkbox(item_dict["item"], value=item_dict["checked"], key=f"pack_{i}")
        if new_status != item_dict["checked"]:
            st.session_state.packing_list[i]["checked"] = new_status
            data_changed = True
            
    if data_changed:
        persist_all()
        
    st.markdown("---")
    st.subheader("➕ הוסף פריט חדש לרשימה")
    with st.form("add_gear_form", clear_on_submit=True):
        new_gear = st.text_input("שם הפריט החדש:")
        gear_submitted = st.form_submit_button("הוסף לפריטים")
        if gear_submitted and new_gear.strip():
            existing_items = [d["item"] for d in st.session_state.packing_list]
            if new_gear.strip() not in existing_items:
                st.session_state.packing_list.append({"item": new_gear.strip(), "checked": False})
                persist_all()
                st.success("הפריט נוסף ונשמר לצמיתות!")
                st.rerun()
            else:
                st.warning("הפריט כבר קיים ברשימה.")

# ==========================================
# תצוגה 6: משימות טרום-טיול
# ==========================================
elif selected_tab == "📋 משימות טרום-טיול":
    st.subheader("📋 משימות ומנהלות לפני היציאה לטיול")

    total_tasks = len(st.session_state.tasks_list)
    checked_tasks = sum(1 for t in st.session_state.tasks_list if t["checked"])
    task_progress = (checked_tasks / total_tasks) if total_tasks > 0 else 0
    st.markdown(f"### ✅ התקדמות משימות: {checked_tasks} מתוך {total_tasks} הושלמו")
    st.progress(task_progress)

    st.markdown("סמן את המשימות שכבר סגרתם לקראת הנסיעה:")
    st.markdown("---")
    
    tasks_changed = False
    for i, t_dict in enumerate(st.session_state.tasks_list):
        t_status = st.checkbox(t_dict["task"], value=t_dict["checked"], key=f"task_{i}")
        if t_status != t_dict["checked"]:
            st.session_state.tasks_list[i]["checked"] = t_status
            tasks_changed = True
            
    if tasks_changed:
        persist_all()
        
    st.markdown("---")
    st.subheader("➕ הוסף משימה חדשה לרשימה")
    with st.form("add_task_form", clear_on_submit=True):
        new_task = st.text_input("תיאור המשימה (למשל: רכישת אינטרנט בחו\"ל):")
        task_submitted = st.form_submit_button("הוסף משימה")
        if task_submitted and new_task.strip():
            existing_tasks = [d["task"] for d in st.session_state.tasks_list]
            if new_task.strip() not in existing_tasks:
                st.session_state.tasks_list.append({"task": new_task.strip(), "checked": False})
                persist_all()
                st.success("המשימה נוספה ונשמרה לצמיתות!")
                st.rerun()
            else:
                st.warning("המשימה כבר קיימת ברשימה.")

# ==========================================
# תצוגה 7: יומן מסע אישי
# ==========================================
elif selected_tab == "📓 יומן מסע אישי":
    st.subheader("📓 יומן מסע ופתקים אישיים מהשטח")
    st.markdown("כאן תוכל לכתוב חופשי תובנות, שמות של מקומות מיוחדים שנתקלתם בהם, או זכרונות מהטיול:")
    st.markdown("---")
    
    current_notes = st.text_area("תוכן היומן:", value=st.session_state.journal_notes, height=250)
    if current_notes != st.session_state.journal_notes:
        st.session_state.journal_notes = current_notes
        persist_all()
        st.success("💾 השינויים ביומן נשמרו אוטומטית!")

# ==========================================
# תצוגה 8: שוברים ומסמכים דיגיטליים
# ==========================================
elif selected_tab == "📄 שוברים ומסמכים דיגיטליים":
    st.subheader("📄 מרכז מסמכים, שוברים והעלאת קבצים")
    st.markdown("כאן תוכלו להעלות ולרכז את כל האישורים, כרטיסי הטיסה, פוליסות הביטוח ושוברי המלונות שלכם.")
    st.caption("הקבצים נשמרים ב-Supabase Storage בענן, כך שהם לא יימחקו כשהשרת מתאתחל.")
    st.markdown("---")
    
    st.markdown("### 📤 העלאת קובץ חדש (PDF, תמונות, מסמכים)")
    uploaded_file = st.file_uploader("בחר קובץ להעלאה:", type=["pdf", "png", "jpg", "jpeg", "txt"])
    file_category = st.selectbox("בחר סוג מסמך:", ["טיסות", "ביטוח רפואי", "מלון", "השכרת רכב", "שונות"])
    
    if uploaded_file is not None:
        if st.button("שמור קובץ במערכת", type="primary"):
            with st.spinner("מעלה לענן..."):
                storage_path, public_url = upload_file_to_storage(uploaded_file.getvalue(), uploaded_file.name)
            
            if storage_path and public_url:
                file_info = {
                    "filename": uploaded_file.name,
                    "category": file_category,
                    "storage_path": storage_path,
                    "url": public_url
                }
                st.session_state.uploaded_files_meta.append(file_info)
                persist_all()
                st.success(f"הקובץ '{uploaded_file.name}' הועלה ונשמר בהצלחה בענן!")
                st.rerun()

    st.markdown("---")
    st.subheader("📁 המסמכים והשוברים השמורים שלך:")
    
    if not st.session_state.uploaded_files_meta:
        st.info("עדיין לא הועלו קבצים. השתמש בטופס למעלה כדי להעלות מסמכים.")
    else:
        for idx, f_meta in enumerate(st.session_state.uploaded_files_meta):
            col_d1, col_d2, col_d3 = st.columns([3, 2, 1])
            with col_d1:
                st.markdown(f"<b>📄 {f_meta['filename']}</b> <span style='color: gray; font-size: 0.85em;'>({f_meta['category']})</span>", unsafe_allow_html=True)
            with col_d2:
                file_url = f_meta.get("url")
                if file_url:
                    st.markdown(f"<a href='{file_url}' target='_blank'>📥 הורד / הצג</a>", unsafe_allow_html=True)
                else:
                    st.warning("קישור לקובץ חסר")
            with col_d3:
                if st.button("🗑️ מחק", key=f"del_file_{idx}"):
                    storage_path = f_meta.get("storage_path")
                    if storage_path:
                        delete_file_from_storage(storage_path)
                    st.session_state.uploaded_files_meta.pop(idx)
                    persist_all()
                    st.success("הקובץ נמחק!")
                    st.rerun()

# ==========================================
# תצוגה 9: אנשי קשר וחירום
# ==========================================
elif selected_tab == "📞 אנשי קשר וחירום":
    st.subheader("📞 ספריית אנשי קשר, מלונות וגורמי חירום")
    st.markdown("כאן תוכלו לשמור, להוסיף ולמחוק את כל מספרי הטלפון החשובים שתרצו שיהיו זמינים בשטח:")
    st.markdown("---")
    
    if st.session_state.contacts_list:
        for idx, contact in enumerate(st.session_state.contacts_list):
            c_col1, c_col2, c_col3 = st.columns([2, 2, 1])
            with c_col1:
                st.markdown(f"**👤 {contact['name']}**<br><span style='color:gray;'>{contact.get('role', '')}</span>", unsafe_allow_html=True)
            with c_col2:
                st.markdown(f"📞 <b>{contact['phone']}</b>", unsafe_allow_html=True)
            with c_col3:
                if st.button("🗑️ מחק", key=f"del_contact_{idx}"):
                    st.session_state.contacts_list.pop(idx)
                    persist_all()
                    st.success("איש הקשר נמחק!")
                    st.rerun()
            st.markdown("---")
    else:
        st.info("אין אנשי קשר שמורים כרגע.")

    st.subheader("➕ הוסף איש קשר חדש")
    with st.form("add_contact_form", clear_on_submit=True):
        c_name = st.text_input("שם איש הקשר / הגורם (למשל: נהג מונית אמין / מלון באטומי):")
        c_phone = st.text_input("מספר טלפון (כולל קידומת):")
        c_role = st.text_input("תפקיד או הערה (למשל: זמין 24/7):")
        contact_submitted = st.form_submit_button("הוסף איש קשר")
        
        if contact_submitted and c_name.strip() and c_phone.strip():
            st.session_state.contacts_list.append({
                "name": c_name.strip(),
                "phone": c_phone.strip(),
                "role": c_role.strip()
            })
            persist_all()
            st.success("איש הקשר נוסף ונשמר לצמיתות!")
            st.rerun()

# ==========================================
# תצוגה 10: חוויית סופרה ואירוח משפחתי
# ==========================================
elif selected_tab == "🍷 אירוח משפחתי וסופרה":
    st.subheader("🍷 חוויית 'סופרה' וארוחות משפחתיות מסורתיות בגאורגיה")
    st.markdown("חוויית חובה בטיול! ארוחת משתה גאורגית אותנטית (סופרה) הכוללת מטעמים ביתיים, יינות מקומיים והופעות פולקלור ריבוי-קולות וריקודים סוערים.")
    st.markdown("---")

    col_sup1, col_sup2 = st.columns(2)
    with col_sup1:
        st.markdown("""
        ### 🍇 חבל קחתי (אזור היין - סיגנאגי ותלביאוי)
        * **מה מחכה לכם:** יקבים בוטיקיים משפחתיים שבהם מכינים יין בכדים טמונים באדמה (קגוורי). המשפחות מארחות בחצרות ירוקות לארוחות שף ביתיות מלאות כל טוב.
        * **איפה לחפש / מומלצים:** 
          * *Pheasant’s Tears (סיגנאגי)* - יקב אורגני מדהים עם אירוח מוקפד ואווירה כפרית.
          * יקבים משפחתיים קטנים לאורך הדרך בקאחתי (ניתן לתאם דרך המלון או במקום).
        """)
    with col_sup2:
        st.markdown("""
        ### 🏔️ הרי אג'ריה (אזור באטומי וההרים)
        * **מה מחכה לכם:** כפרים קסומים בהרים סביב באטומי (כמו אזור Keda). משפחות הרריות מציעות ארוחות כפריות (מאפים מיוחדים, גבינות מקומיות, בשרים) בליווי מוזיקה כפרית.
        * **טיפ:** מושלם לשילוב ביום טיול מבאטומי לכיוון ההרים הפנימיים.
        """)

    st.markdown("---")
    st.markdown("""
    ### 🏙️ טביליסי והסביבה
    * **מסעדת Shavi Lomi (טביליסי):** אמנם זו מסעדה ולא בית פרטי, אבל היא מעוצבת בדיוק כמו חצר טביליסאית עתיקה עם אוכל ביתי אגדי ואווירה משפחתית חמה.
    * **איך מתאמים ערב פולקלור אמיתי?** רוב המשפחות המארחות וההופעות הפרטיות דורשות **תיאום מראש** של כמה ימים. הדרך הקלה והטובה ביותר היא לבקש מבעל המלון שבו תלונו בטביליסי או בבאטומי להרים טלפון למארחים מקומיים שהם מכירים ולסדר עבורכם ערב סופרה מושלם.
    """)

# ==========================================
# תצוגה 11: חירום וטיפים לשטח
# ==========================================
elif selected_tab == "🚨 חירום וטיפים לשטח":
    st.subheader("🚨 מספרי חירום, עזרה ראשונה וטיפים לנהיגה בהרים")
    st.markdown("---")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("""
        ### 📞 מספרי חירום בגאורגיה:
        * **מוקד חירום כללי (משטרה, אמבולנס, כיבוי):** `112` (דוברים אנגלית)
        * **משטרה תיירותית:** חינם דרך מוקד 112
        * **שגרירות ישראל בטביליסי:** `+995 32 255 65 00`
        
        ### 🅿️ טיפים לתשלום חניה בעיר:
        * בטביליסי ובבאטומי אסור להחנות איפה שמסומן באדום-לבן או צהוב בלי אישור.
        * מומלץ להוריד מראש את אפליקציות החניה הרשמיות (`Tbilisi Parking` / `ParkMate Batumi`) ולהזין מספר רכב ואשראי.
        """)
    with col_t2:
        st.markdown("""
        ### 🚗 טיפים חשובים לנהיגה בהרים:
        * **פרות בכביש:** בהרים (במיוחד בדרך הצבאית לקזבגי) פרות וסוסים מסתובבים חופשי על הכביש. להיזהר בסיבובים!
        * **עקיפות מסוכנות:** הנהגים המקומיים לעיתים עוקפים בפראות. שמרו ימין והיו עירניים.
        * **דלק:** מומלץ לתדלק תמיד כשמיכל הדלק יורד מתחת לחצי, בעיקר לפני האזורים ההרריים שבהם תחנות הדלק דלילות יותר.
        """)

    st.markdown("---")
    st.markdown("""
    <a href="https://maps.google.com/?q=hospital" target="_blank" style="display: block; padding: 12px; background-color: #dc3545; color: white; text-align: center; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
        🏥 מצא בית חולים או מרכז רפואי קרוב ב-Google Maps
    </a>
    """, unsafe_allow_html=True)

# ==========================================
# תצוגה 12: מפה אינטראקטיבית (צבועה לפי יום המסלול)
# ==========================================
elif selected_tab == "🗺️ מפת האטרקציות":
    st.subheader("🗺️ מפת האטרקציות האינטראקטיבית")
    st.caption("צבע כל נקודה משקף את יום המסלול - כך ניתן לראות ויזואלית את רצף הנסיעה הגיאוגרפי.")
    st.markdown("---")
    if not filtered_df.empty:
        fig_map = px.scatter_mapbox(
            filtered_df,
            lat="lat",
            lon="lon",
            hover_name="site",
            hover_data=["day", "region", "icon"],
            color="day",
            color_continuous_scale=px.colors.sequential.Viridis,
            zoom=7,
            height=550
        )
        fig_map.update_traces(marker=dict(size=14))
        fig_map.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0,"t":0,"l":0,"b":0},
            coloraxis_colorbar=dict(title="יום")
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("אין אטרקציות להצגה בסינון הנוכחי.")
