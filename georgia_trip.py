import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta, date
import math
import urllib.parse

# הגדרת תצורת העמוד (חייב להיות ראשון)
st.set_page_config(page_title="תכנון טיול משפחתי לגאורגיה", page_icon="🇬🇪", layout="wide")

# ==========================================
# פונקציית עזר: חישוב מרחק וזמן משוער בין קואורדינטות (נוסחת Haversine)
# ==========================================
def calculate_travel_estimation(lat1, lon1, lat2, lon2):
    R = 6371.0  # רדיוס כדור הארץ בקילומטרים
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

# ==========================================
# עיצוב מותאם אישית (CSS) - צבעוני ו-RTL
# ==========================================
st.markdown("""
<style>
    .block-container { direction: rtl; text-align: right; }
    
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
        border: 1px solid #dee2e6;
        padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;
        border-right: 5px solid #28a745;
    }
    div[data-testid="metric-container"] label, div[data-testid="metric-container"] div { 
        color: #111111 !important; 
    }
    
    .site-card {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        margin-bottom: 20px;
        border-right: 6px solid #ff4b4b;
    }
    .site-card h2, .site-card p, .site-card b {
        color: #222222 !important;
    }
    .date-badge {
        background-color: #e3f2fd; color: #1565c0; padding: 4px 10px; 
        border-radius: 15px; font-size: 0.9em; font-weight: bold; margin-right: 10px;
    }
    .info-box {
        background-color: #f8f9fa;
        border-right: 4px solid #17a2b8;
        padding: 10px 15px;
        border-radius: 8px;
        margin-top: 10px;
        font-size: 0.95em;
    }
</style>
""", unsafe_allow_html=True)

st.title("🇬🇪 דשבורד טיול משפחתי לגאורגיה")
st.markdown("ניהול מסלול, עלויות, זמני נסיעה, חניות, מסעדות מומלצות ומפה דינמית.")
st.markdown("---")

# ==========================================
# מסד הנתונים המלא של הטיול (כולל חניות ומסעדות)
# ==========================================
itinerary = [
    {
        "day": 1, "region": "באטומי (חוף וטיילת)", "site": "שדרות באטומי (Batumi Boulevard)", "hours": "פתוח 24/7", 
        "adult_cost": 0, "child_cost": 0, "activity_hours": 2.5, "travel_time": 0.0, "icon": "🌴", "lat": 41.6530, "lon": 41.6360, 
        "details": "טיול רגלי או רכיבה לאורך הטיילת המרשימה (7 ק\"מ).",
        "parking": "חניה רחוב מסודרת (בתשלום עירוני סביב 1-2 לארי לשעה באמצעות אפליקציה מקומית או כרטיס).",
        "restaurants": ["Retro (מפורסם בזכות האצ'פורי אג'רולי)", "Fanfan (אוכל אירופאי וגאורגי מעוצב)"]
    },
    {
        "day": 1, "region": "באטומי (חוף וטיילת)", "site": "פסל עלי ונינו (Ali and Nino)", "hours": "פתוח 24/7", 
        "adult_cost": 0, "child_cost": 0, "activity_hours": 0.5, "travel_time": 0.3, "icon": "🗿", "lat": 41.6556, "lon": 41.6394, 
        "details": "צפייה בפסל הדינמי המפורסם על קו המים.",
        "parking": "חניה ציבורית סמוך לנמל (בתשלום, כ-2 לארי לשעה).",
        "restaurants": ["Chef's Grill", "Batumeti"]
    },
    {
        "day": 2, "region": "באטומי (אטרקציות)", "site": "הדולפינריום של באטומי", "hours": "16:00 / 19:00", 
        "adult_cost": 25, "child_cost": 25, "activity_hours": 2.0, "travel_time": 0.4, "icon": "🐬", "lat": 41.6475, "lon": 41.6231, 
        "details": "מופע דולפינים מרהיב וחווייתי.",
        "parking": "חניון מסודר סביב פארק 6 במאי (חינם או בעלות סמלית של 1 לארי).",
        "restaurants": ["Restaurant 360 (במלון שירטון הסמוך)", "Laguna (מאפיית פחמימות מיתולוגית)"]
    },
    {
        "day": 2, "region": "באטומי (אטרקציות)", "site": "רכבל ארגו (Argo Cable Car)", "hours": "10:00 - 22:00", 
        "adult_cost": 30, "child_cost": 15, "activity_hours": 1.5, "travel_time": 0.3, "icon": "🚡", "lat": 41.6472, "lon": 41.6455, "details": "עלייה לתצפית פנורמית מרהיבה.",
        "parking": "חניון רשמי של הרכבל (בתשלום, כ-2-3 לארי).",
        "restaurants": ["Argo Cafe (בראש ההר)", "Old Boulevard"]
    },
    {
        "day": 2, "region": "באטומי (אטרקציות)", "site": "הגנים הבוטניים של באטומי", "hours": "09:00 - 19:30", 
        "adult_cost": 30, "child_cost": 30, "activity_hours": 3.0, "travel_time": 0.4, "icon": "🌳", "lat": 41.6963, "lon": 41.7163, "details": "סיור בטבע ירוק ועשיר הנושק לים.",
        "parking": "חניון מסודר בכניסה הראשית לגנים (בתשלום סמלי של 2 לארי ליום).",
        "restaurants": ["Green Cape Cafe", "מסעדות דגים מקומיות בחוף מחירינגי"]
    },
    {
        "day": 3, "region": "מרטווילי ופרומתאוס", "site": "מערת פרומתאוס (Prometheus Cave)", "hours": "10:00 - 17:00", 
        "adult_cost": 40, "child_cost": 40, "activity_hours": 2.5, "travel_time": 2.0, "icon": "🦇", "lat": 42.3768, "lon": 42.6009, "details": "מערת נטיפים תת-קרקעית מרהיבה.",
        "parking": "חניון מסודר וחינמי של מתחם המערה.",
        "restaurants": ["Prometheus Cafe", "מסעדות כפריות באזור צקלטובו (Tskaltubo)"]
    },
    {
        "day": 3, "region": "מרטווילי ופרומתאוס", "site": "קניון מרטווילי (Martvili Canyon)", "hours": "10:00 - 17:30", 
        "adult_cost": 32.25, "child_cost": 32.25, "activity_hours": 2.5, "travel_time": 1.0, "icon": "🛶", "lat": 42.4578, "lon": 42.3767, "details": "שייט בסירות מתנפחות בתוך קניון מים.",
        "parking": "חניון מוסדר של האתר (חינם, ייתכן טיפים לשומרים מקומיים).",
        "restaurants": ["Dadiani Cafe (בתוך הקניון)", "Oda Family Winery (אוכל ביתי מנגרלואי אותנטי בהזמנה מראש)"]
    },
    {
        "day": 4, "region": "טביליסי", "site": "פארק מתאצמינדה (Mtatsminda Park)", "hours": "11:00 - 22:00", 
        "adult_cost": 10, "child_cost": 10, "activity_hours": 3.5, "travel_time": 0.5, "icon": "🎢", "lat": 41.6946, "lon": 44.7865, "details": "פארק שעשועים בראש ההר המשקיף על טביליסי.",
        "parking": "חניון עליון בפארק (בתשלום סמלי של כ-5 לארי לכל השהות).",
        "restaurants": ["Funicular Restaurant (מסעדה יוקרתית עם נוף מטורף)", "Doner House"]
    },
    {
        "day": 4, "region": "טביליסי", "site": "רכבל ומצודת נריקלה (Narikala)", "hours": "10:00 - 22:00", 
        "adult_cost": 5, "child_cost": 5, "activity_hours": 1.5, "travel_time": 0.3, "icon": "🏰", "lat": 41.6881, "lon": 44.8093, "details": "רכבל, מצודה ופסל אמא גאורגיה.",
        "parking": "אין חניה נוחה באתר עצמו. מומלץ לחנות באזור Rike Park למטה (חניה בתשלום עירוני).",
        "restaurants": ["Machakhela (כיכר הבמבה)", "Samikitno (פתוח 24/7, אוכל גאורגי מעולה)"]
    },
    {
        "day": 5, "region": "דשבשי + קחתי", "site": "גשר היהלום בדשבשי", "hours": "10:00 - 19:00", 
        "adult_cost": 49, "child_cost": 49, "activity_hours": 2.5, "travel_time": 2.0, "icon": "💎", "lat": 41.5975, "lon": 44.0253, "details": "גשר זכוכית שקוף מעל קניון עמוק.",
        "parking": "חניון עפר מסודר בכניסה למתחם (חינם).",
        "restaurants": ["Diamond Bridge Panorama Restaurant (מסעדה תלויה עם נוף לקניון)"]
    },
    {
        "day": 5, "region": "דשבשי + קחתי", "site": "מנזר בודבה ועיירת האהבה סיגנאגי", "hours": "שעות יום", 
        "adult_cost": 0, "child_cost": 0, "activity_hours": 2.0, "travel_time": 1.5, "icon": "⛪", "lat": 41.6116, "lon": 45.9333, "details": "חומות ציוריות, סמטאות אבן ונוף.",
        "parking": "חניה מוסדרת בכניסה למנזר וברחובות סיגנאגי (חינם או תשלום סמלי של 2 לארי).",
        "restaurants": ["Pheasant's Tears (יקב ומסעדה אורגנית מומלצת בסיגנאגי)", "Okro's Wine"]
    },
    {
        "day": 5, "region": "דשבשי + קחתי", "site": "יקב חארבה (Khareba)", "hours": "10:00 - 18:00", 
        "adult_cost": 25, "child_cost": 10, "activity_hours": 1.5, "travel_time": 0.5, "icon": "🍇", "lat": 41.9366, "lon": 45.8361, "details": "מנהרות אבן לאחסון יין וטעימות.",
        "parking": "חניון ענק ומסודר של היקב (חינם למבקרים).",
        "restaurants": ["Tunnel Restaurant (בתוך המנהרות של היקב)", "Kindzmarauli Marani (בעיר קוור렐ิ)"]
    },
    {
        "day": 6, "region": "הדרך הצבאית וגודאורי", "site": "מצודת אננורי ומאגר ז'ינוואלי", "hours": "09:00 - 19:00", 
        "adult_cost": 0, "child_cost": 0, "activity_hours": 1.0, "travel_time": 1.5, "icon": "🌊", "lat": 42.1643, "lon": 44.7032, "details": "אגם טורקיז ומצודה היסטורית שמורה.",
        "parking": "חניה לצד הדרך / חניון עפר ליד המצודה (בתשלום מקומי קטן של 2-3 לארי לשומרים).",
        "restaurants": ["Pasanauri Khinkali House (בדרך, מומלץ לעצור לחינקלי)", "Ananuri Cafe"]
    },
    {
        "day": 6, "region": "הדרך הצבאית וגודאורי", "site": "אנדרטת גודאורי + רכבת הרים", "hours": "שעות היום", 
        "adult_cost": 20, "child_cost": 20, "activity_hours": 2.0, "travel_time": 1.0, "icon": "🛷", "lat": 42.4925, "lon": 44.4533, "details": "תצפית נוף וגלישה בקרוניות הרים.",
        "parking": "חניון רחב ידיים לצד האנדרטה (חינם).",
        "restaurants": ["Gudauri Lodge Restaurant", "Cafe Quadra"]
    },
    {
        "day": 7, "region": "קזבגי (סטפנצמינדה)", "site": "כנסיית גרגטי", "hours": "אור יום", 
        "adult_cost": 60, "child_cost": 60, "activity_hours": 2.5, "travel_time": 1.0, "icon": "🏔️", "lat": 42.6629, "lon": 44.6203, "details": "כנסייה מפורסמת למרגלות הר קזבק (הכביש משובש, מומלץ ג'יפ מקומי או הליכה).",
        "parking": "חניה למעלה ליד הכנסייה (עפר, חינם). לרכבים פרטיים לא קשוחים מומלץ לחנות למטה בעיירה ולקחת מונית שירות מקומית.",
        "restaurants": ["Mountain Freaks Cafe (בסטפנצמינדה)", "Cafe 5047m"]
    },
    {
        "day": 7, "region": "קזבגי (סטפנצמינדה)", "site": "מלון Rooms Kazbegi", "hours": "12:00 - 22:00", 
        "adult_cost": 40, "child_cost": 30, "activity_hours": 1.5, "travel_time": 0.3, "icon": "☕", "lat": 42.6566, "lon": 44.6464, "details": "ארוחה או קפה במרפסת המפורסמת עם נוף להר.",
        "parking": "חניה מסודרת לאורחי המלון והמסעדה (חינם).",
        "restaurants": ["Rooms Hotel Restaurant (אוכל אירופאי-גאורגי עילי)", "Sno Cafe"]
    },
    {
        "day": 8, "region": "טביליסי העתיקה", "site": "מרחצאות חמי אורבליאני", "hours": "08:00 - 23:00", 
        "adult_cost": 75, "child_cost": 0, "activity_hours": 1.5, "travel_time": 0.3, "icon": "🛁", "lat": 41.6880, "lon": 44.8115, "details": "חדר פרטי במרחצאות הגופרית.",
        "parking": "חניון רחוב בתשלום עירוני (קשה מאוד למצוא חניה באזור העתיק, עדיף להגיע במונית או לחנות בחניון מסודר מרוחק).",
        "restaurants": ["Culinarium Khasheria (שף לוקה טרזני - מעולה)", "Gastro Chef"]
    },
    {
        "day": 8, "region": "טביליסי העתיקה", "site": "מפל לגווטכבי וגשר השלום", "hours": "24/7", 
        "adult_cost": 0, "child_cost": 0, "activity_hours": 2.0, "travel_time": 0.3, "icon": "🌉", "lat": 41.6865, "lon": 44.8090, "details": "מפל טבעי המסתתר בלב העיר.",
        "parking": "חניון Rike Park הסמוך (בתשלום עירוני).",
        "restaurants": ["Pur Pur (מסעדה וינטג' קסומה במרכז)", "Shavi Lomi (מסעדת גורמה מקומית מדהימה - דורשת הזמנה מראש)"]
    },
    {
        "day": 9, "region": "שקווטילי", "site": "הפארק הדנדרולוגי", "hours": "10:00 - 18:00", 
        "adult_cost": 0, "child_cost": 0, "activity_hours": 2.5, "travel_time": 1.0, "icon": "🦩", "lat": 41.9372, "lon": 41.7644, "details": "פארק עצום עם ציפורים ופלמינגו.",
        "parking": "חניון מסודר וחינמי בכניסה לפארק.",
        "restaurants": ["Black Sea Arena Cafe", "מסעדות חוף באזור שקווטילי ואורקיבי"]
    },
    {
        "day": 9, "region": "שקווטילי", "site": "פארק המוזיקאים", "hours": "24/7", 
        "adult_cost": 0, "child_cost": 0, "activity_hours": 1.5, "travel_time": 0.3, "icon": "🎵", "lat": 41.9167, "lon": 41.7681, "details": "יער קסום עם פסלי מוזיקאים.",
        "parking": "חניה לצד הפארק ביער (חינם).",
        "restaurants": ["Magnetic Beach Cafe", "Paragraph Resort Restaurants"]
    },
    {
        "day": 10, "region": "באטומי (סיום)", "site": "שוק הדגים של באטומי", "hours": "09:00 - 20:00", 
        "adult_cost": 40, "child_cost": 30, "activity_hours": 2.0, "travel_time": 0.0, "icon": "🐟", "lat": 41.6495, "lon": 41.6521, "details": "בוחרים דגים ומבשלים במקום.",
        "parking": "חניון השוק (חינם או תשלום סמלי של 1-2 לארי).",
        "restaurants": ["שוק הדגים עצמו (בוחרים דג טרי בצד ומבקשים שיבשלו במסעדות שבתוך השוק)", "Station Cafe"]
    }
]

# ==========================================
# סרגל צד - תאריכים, ניווט וסינון
# ==========================================
with st.sidebar:
    try:
        st.image("IMG_1101.jpg", use_container_width=True, caption="המשפחה המטיילת ✈️")
    except FileNotFoundError:
        pass  
        
    st.markdown("---")
    st.header("📅 תאריכים והרכב")
    
    start_date = st.date_input("תאריך תחילת הטיול:", value=date.today())
    
    adults = st.number_input("מספר מבוגרים", min_value=1, value=2, step=1)
    children = st.number_input("מספר ילדים", min_value=0, value=2, step=1)
    
    st.markdown("---")
    st.header("💱 מטבע ושער")
    exchange_rate = st.number_input("שער לארי (GEL) לשקל:", value=1.38, step=0.01)
        
    st.markdown("---")
    st.header("⚙️ בקרת מסלול")
    
    selected_tab = st.selectbox(
        "בחר מצב תצוגה:", 
        options=[
            "📅 פירוט מסלול ואטרקציות", 
            "🏨 מלונות", 
            "🚗 מחשבון ניווט וזמני נסיעה",
            "📊 דשבורד עלויות וזמנים",
            "🗺️ מפת האטרקציות"
        ]
    )
    
    st.markdown("---")
    
    max_days = max([item['day'] for item in itinerary])
    day_options = ["הכל"]
    for d in range(1, max_days + 1):
        actual_date = start_date + timedelta(days=d-1)
        day_options.append(f"יום {d} ({actual_date.strftime('%d/%m/%Y')})")
        
    selected_day_str = st.selectbox("סינון לפי יום בטיול:", options=day_options)
    
    if selected_day_str != "הכל":
        selected_day = int(selected_day_str.split(" ")[1])
    else:
        selected_day = "הכל"

# עיבוד הנתונים
df = pd.DataFrame(itinerary)
df['total_cost_gel'] = (adults * df['adult_cost']) + (children * df['child_cost'])
df['total_hours'] = df['activity_hours'] + df['travel_time']
df['actual_date'] = df['day'].apply(lambda d: start_date + timedelta(days=d-1))

# בסיס נתונים מעודכן למלונות
hotels_raw = [
    {
        "מלון": "King Suite Black Sea View Hotel", "check_in_day": 1, "check_out_day": 3, "אזור": "באטומי",
        "parking": "חניה פרטית של המלון / חניה ברחוב סמוך (חינם לאורחי המלון על בסיס מקום פנוי).",
        "restaurants": ["Retro (חצ'פורי)", "Fanfan", "Heart of Batumi"]
    },
    {
        "מלון": "Novotel Tbilisi Center", "check_in_day": 3, "check_out_day": 6, "אזור": "טביליסי",
        "parking": "חניון תת-קרקעי פרטי של המלון (בתשלום יומי של כ-20-30 לארי).",
        "restaurants": ["Shavi Lomi", "Culinarium Khasheria", "Pur Pur"]
    },
    {
        "מלון": "Gudauri Lodge", "check_in_day": 6, "check_out_day": 8, "אזור": "גודאורי",
        "parking": "חניה מסודרת חינם לאורחי המלון בחזית.",
        "restaurants": ["מסעדת המלון הראשית", "Cafe Quadra"]
    },
    {
        "מלון": "Novotel Tbilisi Center", "check_in_day": 8, "check_out_day": 9, "אזור": "טביליסי",
        "parking": "חניון תת-קרקעי פרטי של המלון (בתשלום יומי).",
        "restaurants": ["Samikitno", "Machakhela"]
    },
    {
        "מלון": "King Suite Black Sea View Hotel", "check_in_day": 9, "check_out_day": 11, "אזור": "באטומי",
        "parking": "חניה פרטית של המלון / ברחוב סמוך.",
        "restaurants": ["Retro", "Chef's Grill"]
    }
]

hotels_processed = []
for h in hotels_raw:
    ci_date = start_date + timedelta(days=h["check_in_day"]-1)
    co_date = start_date + timedelta(days=h["check_out_day"]-1)
    hotels_processed.append({
        "מלון": h["מלון"],
        "אזור": h["אזור"],
        "צ'ק אין": ci_date.strftime('%d/%m/%Y'),
        "צ'ק אאוט": co_date.strftime('%d/%m/%Y'),
        "חניה": h["parking"],
        "מסעדות באזור": ", ".join(h["restaurants"])
    })
df_hotels = pd.DataFrame(hotels_processed)

filtered_df = df.copy()
if selected_day != "הכל":
    filtered_df = filtered_df[filtered_df['day'] == selected_day]

# ==========================================
# תצוגה 1: פירוט מסלול
# ==========================================
if selected_tab == "📅 פירוט מסלול ואטרקציות":
    st.subheader("📍 אטרקציות המסלול, חניות ומסעדות")
    
    csv = filtered_df.drop(columns=['restaurants', 'parking']).to_csv(index=False).encode('utf-8-sig')
    st.download_button(label="📥 הורד מסלול לאקסל", data=csv, file_name='georgia_trip.csv', mime='text/csv')
    st.markdown("---")
    
    for idx, row in filtered_df.iterrows():
        date_str = row['actual_date'].strftime("%d/%m/%Y")
        item_cost_ils = row['total_cost_gel'] * exchange_rate
        
        restaurants_html = ""
        for rest in row['restaurants']:
            rest_encoded = urllib.parse.quote(f"{rest}, {row['region']}, Georgia")
            restaurants_html += f"&bull; <a href='https://www.google.com/maps/search/?api=1&query={rest_encoded}' target='_blank'>{rest}</a><br>"
        
        card_content = f"""
        <div class="site-card">
            <h2>{row['icon']} <span class="date-badge">{date_str}</span> יום {row['day']} | {row['site']}</h2>
            <p><b>📍 אזור:</b> {row['region']}</p>
            <p><b>📝 פרטים:</b> {row['details']}</p>
            <p>🕒 <b>שעות פתיחה:</b> {row['hours']}</p>
            <p>⏱️ <b>משך פעילות:</b> {row['activity_hours']} שעות &nbsp;&nbsp;|&nbsp;&nbsp; 🚗 <b>זמן נסיעה:</b> {row['travel_time']} שעות</p>
            <p style="color: #2e7d32; font-weight: bold;">💰 עלות עבור {adults} מבוגרים ו-{children} ילדים: {row['total_cost_gel']} לארי (~ {item_cost_ils:,.0f} ₪)</p>
            <div class="info-box">
                <p><b>🅿️ מידע על חניה:</b> {row['parking']}</p>
                <p><b>🍽️ מסעדות מומלצות בסביבה:</b><br>{restaurants_html}</p>
            </div>
        </div>
        """
        st.markdown(card_content, unsafe_allow_html=True)

# ==========================================
# תצוגה 2: מלונות וניווט
# ==========================================
elif selected_tab == "🏨 מלונות":
    st.subheader("🏨 בתי המלון שלנו, חניות ומסעדות סביבם")
    
    for idx, h in df_hotels.iterrows():
        st.markdown(f"""
        <div class="site-card" style="border-right-color: #3b82f6;">
            <h2>🏨 {h['מלון']} ({h['אזור']})</h2>
            <p><b>📅 תקופת שהייה:</b> {h['צ'ק אין']} עד {h['צ'ק אאוט']}</p>
            <div class="info-box">
                <p><b>🅿️ הסדר חניה במלון:</b> {h['חניה']}</p>
                <p><b>🍽️ מסעדות באזור המלון:</b> {h['מסעדות באזור']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("🚗 תכנון נסיעה מהמלון")
    
    unique_hotels = df_hotels["מלון"].unique()
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
# תצוגה 4: דשבורד עלויות
# ==========================================
elif selected_tab == "📊 דשבורד עלויות וזמנים":
    st.subheader("📊 דשבורד עלויות וזמנים")
    st.markdown("---")
    
    total_cost_gel = filtered_df['total_cost_gel'].sum()
    total_cost_ils = total_cost_gel * exchange_rate
    
    col1, col2 = st.columns(2)
    col1.metric("💰 סך עלות אטרקציות", f"{total_cost_gel:,.0f} GEL", f"~ {total_cost_ils:,.0f} ₪")
    col2.metric("⏱️ סך שעות פעילות", f"{filtered_df['activity_hours'].sum():,.1f} שעות")
    
    daily_summary = filtered_df.groupby('day')['total_cost_gel'].sum().reset_index()
    if not daily_summary.empty:
        fig = px.bar(daily_summary, x='day', y='total_cost_gel', text='total_cost_gel', labels={'day': 'יום', 'total_cost_gel': 'עלות בלארי'}, color_discrete_sequence=['#2ecc71'])
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(tickmode='linear', dtick=1))
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# תצוגה 5: מפה אינטראקטיבית
# ==========================================
elif selected_tab == "🗺️ מפת האטרקציות":
    st.subheader("🗺️ מפת האטרקציות האינטראקטיבית")
    st.markdown("---")
    if not filtered_df.empty:
        fig_map = px.scatter_mapbox(
            filtered_df,
            lat="lat",
            lon="lon",
            hover_name="site",
            hover_data=["day", "region", "icon"],
            zoom=7,
            height=500
        )
        fig_map.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("אין אטרקציות להצגה בסינון הנוכחי.")
