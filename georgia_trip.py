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
    R = 6371.0 # רדיוס כדור הארץ בקילומטרים
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    aerial_distance = R * c
    # מרחק כביש בגאורגיה (הרים ופיתולים) הוא לרוב כ-1.4 מהמרחק האווירי
    road_distance = aerial_distance * 1.4 
    # מהירות ממוצעת משוערת בכבישי גאורגיה היא כ-55 קמ"ש
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
</style>
""", unsafe_allow_html=True)

st.title("🇬🇪 דשבורד טיול משפחתי לגאורגיה")
st.markdown("ניהול מסלול, עלויות יומיות, זמני נסיעה, מפה דינמית ופעילות בקצות האצבעות.")
st.markdown("---")

# ==========================================
# מסד הנתונים של המלונות (חדש!)
# ==========================================
hotels_data = [
    {"מלון": "King Suite Black Sea View Hotel", "צ'ק אין": "14 באוגוסט", "צ'ק אאוט": "16 באוגוסט", "אזור": "באטומי"},
    {"מלון": "Novotel Tbilisi Center", "צ'ק אין": "16 באוגוסט", "צ'ק אאוט": "19 באוגוסט", "אזור": "טביליסי"},
    {"מלון": "Gudauri Lodge", "צ'ק אין": "19 באוגוסט", "צ'ק אאוט": "21 באוגוסט", "אזור": "גודאורי"},
    {"מלון": "Novotel Tbilisi Center", "צ'ק אין": "21 באוגוסט", "צ'ק אאוט": "22 באוגוסט", "אזור": "טביליסי"},
    {"מלון": "King Suite Black Sea View Hotel", "צ'ק אין": "22 באוגוסט", "צ'ק אאוט": "23 באוגוסט", "אזור": "באטומי"}
]
df_hotels = pd.DataFrame(hotels_data)


# ==========================================
# מסד הנתונים המלא של הטיול
# ==========================================
itinerary = [
    {"day": 1, "region": "באטומי (חוף וטיילת)", "site": "שדרות באטומי (Batumi Boulevard)", "hours": "פתוח 24/7", "adult_cost": 0, "child_cost": 0, "activity_hours": 2.5, "travel_time": 0.0, "icon": "🌴", "lat": 41.6530, "lon": 41.6360, "details": "טיול רגלי או רכיבה לאורך הטיילת המרשימה (7 ק\"מ)."},
    {"day": 1, "region": "באטומי (חוף וטיילת)", "site": "פסל עלי ונינו (Ali and Nino)", "hours": "פתוח 24/7", "adult_cost": 0, "child_cost": 0, "activity_hours": 0.5, "travel_time": 0.3, "icon": "🗿", "lat": 41.6556, "lon": 41.6394, "details": "צפייה בפסל הדינמי המפורסם על קו המים."},
    {"day": 2, "region": "באטומי (אטרקציות)", "site": "הדולפינריום של באטומי", "hours": "16:00 / 19:00", "adult_cost": 25, "child_cost": 25, "activity_hours": 2.0, "travel_time": 0.4, "icon": "🐬", "lat": 41.6475, "lon": 41.6231, "details": "מופע דולפינים מרהיב וחווייתי."},
    {"day": 2, "region": "באטומי (אטרקציות)", "site": "רכבל ארגו (Argo Cable Car)", "hours": "10:00 - 22:00", "adult_cost": 30, "child_cost": 15, "activity_hours": 1.5, "travel_time": 0.3, "icon": "🚡", "lat": 41.6472, "lon": 41.6455, "details": "עלייה לתצפית פנורמית מרהיבה."},
    {"day": 2, "region": "באטומי (אטרקציות)", "site": "הגנים הבוטניים של באטומי", "hours": "09:00 - 19:30", "adult_cost": 30, "child_cost": 30, "activity_hours": 3.0, "travel_time": 0.4, "icon": "🌳", "lat": 41.6963, "lon": 41.7163, "details": "סיור בטבע ירוק ועשיר הנושק לים."},
    {"day": 3, "region": "מרטווילי ופרומתאוס", "site": "מערת פרומתאוס (Prometheus Cave)", "hours": "10:00 - 17:00", "adult_cost": 40, "child_cost": 40, "activity_hours": 2.5, "travel_time": 2.0, "icon": "🦇", "lat": 42.3768, "lon": 42.6009, "details": "מערת נטיפים תת-קרקעית מרהיבה."},
    {"day": 3, "region": "מרטווילי ופרומתאוס", "site": "קניון מרטווילי (Martvili Canyon)", "hours": "10:00 - 17:30", "adult_cost": 32.25, "child_cost": 32.25, "activity_hours": 2.5, "travel_time": 1.0, "icon": "🛶", "lat": 42.4578, "lon": 42.3767, "details": "שייט בסירות מתנפחות בתוך קניון מים."},
    {"day": 4, "region": "טביליסי", "site": "פארק מתאצמינדה (Mtatsminda Park)", "hours": "11:00 - 22:00", "adult_cost": 10, "child_cost": 10, "activity_hours": 3.5, "travel_time": 0.5, "icon": "🎢", "lat": 41.6946, "lon": 44.7865, "details": "פארק שעשועים בראש ההר המשקיף על טביליסי."},
    {"day": 4, "region": "טביליסי", "site": "רכבל ומצודת נריקלה (Narikala)", "hours": "10:00 - 22:00", "adult_cost": 5, "child_cost": 5, "activity_hours": 1.5, "travel_time": 0.3, "icon": "🏰", "lat": 41.6881, "lon": 44.8093, "details": "רכבל, מצודה ופסל אמא גאורגיה."},
    {"day": 5, "region": "דשבשי + קחתי", "site": "גשר היהלום בדשבשי", "hours": "10:00 - 19:00", "adult_cost": 49, "child_cost": 49, "activity_hours": 2.5, "travel_time": 2.0, "icon": "💎", "lat": 41.5975, "lon": 44.0253, "details": "גשר זכוכית שקוף מעל קניון עמוק."},
    {"day": 5, "region": "דשבשי + קחתי", "site": "מנזר בודבה ועיירת האהבה סיגנאגי", "hours": "שעות יום", "adult_cost": 0, "child_cost": 0, "activity_hours": 2.0, "travel_time": 1.5, "icon": "⛪", "lat": 41.6116, "lon": 45.9333, "details": "חומות ציוריות, סמטאות אבן ונוף."},
    {"day": 5, "region": "דשבשי + קחתי", "site": "יקב חארבה (Khareba)", "hours": "10:00 - 18:00", "adult_cost": 25, "child_cost": 10, "activity_hours": 1.5, "travel_time": 0.5, "icon": "🍇", "lat": 41.9366, "lon": 45.8361, "details": "מנהרות אבן לאחסון יין וטעימות."},
    {"day": 6, "region": "הדרך הצבאית וגודאורי", "site": "מצודת אננורי ומאגר ז'ינוואלי", "hours": "09:00 - 19:00", "adult_cost": 0, "child_cost": 0, "activity_hours": 1.0, "travel_time": 1.5, "icon": "🌊", "lat": 42.1643, "lon": 44.7032, "details": "אגם טורקיז ומצודה היסטורית שמורה."},
    {"day": 6, "region": "הדרך הצבאית וגודאורי", "site": "אנדרטת גודאורי + רכבת הרים", "hours": "שעות היום", "adult_cost": 20, "child_cost": 20, "activity_hours": 2.0, "travel_time": 1.0, "icon": "🛷", "lat": 42.4925, "lon": 44.4533, "details": "תצפית נוף וגלישה בקרוניות הרים."},
    {"day": 7, "region": "קזבגי (סטפנצמינדה)", "site": "כנסיית גרגטי", "hours": "אור יום", "adult_cost": 60, "child_cost": 60, "activity_hours": 2.5, "travel_time": 1.0, "icon": "🏔️", "lat": 42.6629, "lon": 44.6203, "details": "כנסייה מפורסמת למרגלות הר קזבק."},
    {"day": 7, "region": "קזבגי (סטפנצמינדה)", "site": "מלון Rooms Kazbegi", "hours": "12:00 - 22:00", "adult_cost": 40, "child_cost": 30, "activity_hours": 1.5, "travel_time": 0.3, "icon": "☕", "lat": 42.6566, "lon": 44.6464, "details": "ארוחה או קפה במרפסת המפורסמת."},
    {"day": 8, "region": "טביליסי העתיקה", "site": "מרחצאות חמי אורבליאני", "hours": "08:00 - 23:00", "adult_cost": 75, "child_cost": 0, "activity_hours": 1.5, "travel_time": 0.3, "icon": "🛁", "lat": 41.6880, "lon": 44.8115, "details": "חדר פרטי במרחצאות הגופרית."},
    {"day": 8, "region": "טביליסי העתיקה", "site": "מפל לגווטכבי וגשר השלום", "hours": "24/7", "adult_cost": 0, "child_cost": 0, "activity_hours": 2.0, "travel_time": 0.3, "icon": "🌉", "lat": 41.6865, "lon": 44.8090, "details": "מפל טבעי המסתתר בלב העיר."},
    {"day": 9, "region": "שקווטילי", "site": "הפארק הדנדרולוגי", "hours": "10:00 - 18:00", "adult_cost": 0, "child_cost": 0, "activity_hours": 2.5, "travel_time": 1.0, "icon": "🦩", "lat": 41.9372, "lon": 41.7644, "details": "פארק עצום עם ציפורים ופלמינגו."},
    {"day": 9, "region": "שקווטילי", "site": "פארק המוזיקאים", "hours": "24/7", "adult_cost": 0, "child_cost": 0, "activity_hours": 1.5, "travel_time": 0.3, "icon": "🎵", "lat": 41.9167, "lon": 41.7681, "details": "יער קסום עם פסלי מוזיקאים."},
    {"day": 10, "region": "באטומי (סיום)", "site": "שוק הדגים של באטומי", "hours": "09:00 - 20:00", "adult_cost": 40, "child_cost": 30, "activity_hours": 2.0, "travel_time": 0.0, "icon": "🐟", "lat": 41.6495, "lon": 41.6521, "details": "בוחרים דגים ומבשלים במקום."}
]

# ==========================================
# סרגל צד - תאריכים, ניווט וסינון
# ==========================================
with st.sidebar:
    try:
        st.image("IMG_1101.jpg", use_container_width=True, caption="המשפחה המטיילת ✈️")
    except FileNotFoundError:
        pass # מתעלם בשקט אם אין תמונה
        
    st.markdown("---")
    st.header("📅 תאריכים והרכב")
    
    # 1. בחירת תאריך תחילת הטיול
    start_date = st.date_input("תאריך תחילת הטיול:", value=date.today())
    
    adults = st.number_input("מספר מבוגרים", min_value=1, value=2, step=1)
    children = st.number_input("מספר ילדים", min_value=0, value=2, step=1)
        
    st.markdown("---")
    st.header("⚙️ בקרת מסלול")
    
    selected_tab = st.selectbox(
        "בחר מצב תצוגה:", 
        options=[
            "📅 פירוט מסלול ואטרקציות", 
            "🏨 מלונות", # התצוגה החדשה למלונות
            "🚗 מחשבון ניווט וזמני נסיעה",
            "📊 דשבורד עלויות וזמנים",
            "🗺️ מפת האטרקציות"
        ]
    )
    
    st.markdown("---")
    
    # בניית אפשרויות הסינון הכוללות את התאריך בפועל
    max_days = max([item['day'] for item in itinerary])
    day_options = ["הכל"]
    for d in range(1, max_days + 1):
        actual_date = start_date + timedelta(days=d-1)
        day_options.append(f"יום {d} ({actual_date.strftime('%d/%m/%Y')})")
        
    selected_day_str = st.selectbox("סינון לפי יום בטיול:", options=day_options)
    
    # חילוץ מספר היום מתוך המחרוזת (אם לא נבחר "הכל")
    if selected_day_str != "הכל":
        selected_day = int(selected_day_str.split(" ")[1])
    else:
        selected_day = "הכל"

# עיבוד הנתונים
df = pd.DataFrame(itinerary)
df['total_cost_gel'] = (adults * df['adult_cost']) + (children * df['child_cost'])
df['total_hours'] = df['activity_hours'] + df['travel_time']
# הוספת תאריך לכל שורה בדאטה פריים
df['actual_date'] = df['day'].apply(lambda d: start_date + timedelta(days=d-1))

# סינון הנתונים
filtered_df = df.copy()
if selected_day != "הכל":
    filtered_df = filtered_df[filtered_df['day'] == selected_day]

# ==========================================
# תצוגה 1: פירוט מסלול
# ==========================================
if selected_tab == "📅 פירוט מסלול ואטרקציות":
    st.subheader(f"📍 אטרקציות המסלול")
    
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(label="📥 הורד מסלול לאקסל", data=csv, file_name='georgia_trip.csv', mime='text/csv')
    st.markdown("---")
    
    for idx, row in filtered_df.iterrows():
        date_str = row['actual_date'].strftime("%d/%m/%Y")
        day_name = row['actual_date'].strftime("%A") # ניתן לתרגם לעברית אם רוצים
        
        st.markdown(f"""
        <div class="site-card">
            <h2>{row['icon']} <span class="date-badge">{date_str}</span> יום {row['day']} | {row['site']}</h2>
            <p><b>📍 אזור:</b> {row['region']}</p>
            <p><b>📝 פרטים:</b> {row['details']}</p>
            <p>🕒 <b>שעות פתיחה:</b> {row['hours']}</p>
            <p>⏱️ <b>משך פעילות:</b> {row['activity_hours']} שעות &nbsp;&nbsp;|&nbsp;&nbsp; 🚗 <b>זמן נסיעה:</b> {row['travel_time']} שעות</p>
            <p style="color: #2e7d32; font-weight: bold;">💰 עלות עבור {adults} מבוגרים ו-{children} ילדים: {row['total_cost_gel']} לארי</p>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# תצוגה 2: מלונות וניווט (חדש)
# ==========================================
elif selected_tab == "🏨 מלונות":
    st.subheader("🏨 בתי המלון שלנו")
    
    # הצגת טבלת המלונות
    st.dataframe(df_hotels, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # ניווט ל-Google Maps מהמלון
    st.subheader("🚗 תכנון נסיעה מהמלון")
    st.write("בחר את המלון שבו תהיו, הקלד לאן תרצו לנסוע - וקבל קישור ישיר ל-Google Maps.")
    
    unique_hotels = df_hotels["מלון"].unique()
    origin_hotel = st.selectbox("אנחנו יוצאים מ:", unique_hotels)
    destination = st.text_input("לאן נוסעים? (למשל: Kazbegi, Martvili Canyon)", "Kazbegi")
    
    if st.button("חשב מסלול ב-Google Maps", type="primary"):
        if destination:
            origin_encoded = urllib.parse.quote(f"{origin_hotel}, Georgia")
            destination_encoded = urllib.parse.quote(f"{destination}, Georgia")
            
            gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={origin_encoded}&destination={destination_encoded}&travelmode=driving"
            
            st.success("הקישור מוכן! לחץ עליו כדי לפתוח את אפליקציית הניווט בטלפון.")
            st.markdown(f"### [📍 פתח ניווט למסלול]({gmaps_url})")
        else:
            st.warning("אנא הזן יעד כדי לחשב מרחק.")

# ==========================================
# תצוגה 3: מחשבון ניווט בין אטרקציות
# ==========================================
elif selected_tab == "🚗 מחשבון ניווט וזמני נסיעה":
    st.subheader("🚗 מחשבון זמני נסיעה וניווט בגאורגיה")
    st.markdown("בחר יעד מוצא ויעד יעד כדי לקבל הערכת זמן נסיעה וקישור ישיר לניווט ב-Google Maps.")
    st.markdown("---")
    
    all_sites = df['site'].tolist()
    
    col1, col2 = st.columns(2)
    with col1:
        origin = st.selectbox("📍 בחר יעד מוצא:", options=all_sites, index=0)
    with col2:
        # ברירת המחדל ליעד הבא תהיה האתר הבא ברשימה (אם יש)
        default_dest_index = 1 if len(all_sites) > 1 else 0
        destination = st.selectbox("🏁 בחר יעד הבא:", options=all_sites, index=default_dest_index)
        
    if origin and destination:
        if origin == destination:
            st.warning("בחרת את אותו היעד במוצא וביעד.")
        else:
            loc1 = df[df['site'] == origin].iloc[0]
            loc2 = df[df['site'] == destination].iloc[0]
            
            # חישוב 
            km_dist, est_hours = calculate_travel_estimation(loc1['lat'], loc1['lon'], loc2['lat'], loc2['lon'])
            
            hours = int(est_hours)
            minutes = int((est_hours - hours) * 60)
            
            # קישור ל-Google Maps (לפי קואורדינטות כדי להיות מדויק)
            gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={loc1['lat']},{loc1['lon']}&destination={loc2['lat']},{loc2['lon']}"
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.success(f"**מרחק משוער בכביש:** {km_dist:.1f} ק\"מ")
            if hours > 0:
                st.info(f"**זמן נסיעה מוערך:** {hours} שעות ו-{minutes} דקות")
            else:
                st.info(f"**זמן נסיעה מוערך:** {minutes} דקות")
                
            st.markdown(f"""
            <a href="{gmaps_url}" target="_blank" style="display: inline-block; padding: 10px 20px; background-color: #4285F4; color: white; text-align: center; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                🗺️ פתח ניווט ב-Google Maps
            </a>
            <br><br>
            <small style="color:gray;">* הנתונים מבוססים על חישוב סטטיסטי (מהירות ממוצעת של 55 קמ"ש עקב תנאי השטח בגאורגיה). הזמן בפועל עשוי להשתנות עקב פקקים או עצירות.</small>
            """, unsafe_allow_html=True)

# ==========================================
# תצוגה 4: דשבורד עלויות
# ==========================================
elif selected_tab == "📊 דשבורד עלויות וזמנים":
    st.subheader(f"📊 דשבורד עלויות וזמנים")
    st.markdown("---")
    
    total_cost = filtered_df['total_cost_gel'].sum()
    col1, col2 = st.columns(2)
    col1.metric("💰 סך עלות אטרקציות", f"{total_cost:,.0f} GEL", f"~ {total_cost * 1.38:,.0f} ₪")
    col2.metric("⏱️ סך שעות פעילות", f"{filtered_df['activity_hours'].sum():,.1f} שעות")
    
    daily_summary = filtered_df.groupby('day')['total_cost_gel'].sum().reset_index()
    if not daily_summary.empty:
        fig = px.bar(daily_summary, x='day', y='total_cost_gel', text='total_cost_gel', labels={'day': 'יום', 'total_cost_gel': 'עלות בלארי'}, color_discrete_sequence=['#2ecc71'])
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(tickmode='linear', dtick=1))
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# תצוגה 5: מפה
# ==========================================
elif selected_tab == "🗺️ מפת האטרקציות":
    st.subheader(f"🗺️ מפת הטיול")
    st.markdown("---")
    if not filtered_df.empty:
        st.map(filtered_df[['lat', 'lon']], zoom=6)
