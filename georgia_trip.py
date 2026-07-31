import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# הגדרת תצורת העמוד (חייב להיות ראשון)
st.set_page_config(page_title="תכנון טיול משפחתי לגאורגיה", page_icon="🇬🇪", layout="wide")

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
</style>
""", unsafe_allow_html=True)

st.title("🇬🇪 דשבורד טיול משפחתי לגאורגיה")
st.markdown("ניהול מסלול, עלויות יומיות, זמני נסיעה, מפה דינמית ופעילות בקצות האצבעות.")
st.markdown("---")

# ==========================================
# מסד הנתונים המלא של הטיול (כולל קואורדינטות למפה)
# ==========================================
itinerary = [
    {
        "day": 1, "region": "באטומי (חוף וטיילת)", "site": "שדרות באטומי (Batumi Boulevard)",
        "hours": "פתוח 24/7", "adult_cost": 0, "child_cost": 0, 
        "activity_hours": 2.5, "travel_time": 0.0, "icon": "🌴",
        "lat": 41.6530, "lon": 41.6360,
        "details": "טיול רגלי או רכיבה לאורך הטיילת המרשימה (7 ק\"מ) עם פארקים, מזרקות ומודרניות."
    },
    {
        "day": 1, "region": "באטומי (חוף וטיילת)", "site": "פסל עלי ונינו (Ali and Nino)",
        "hours": "פתוח 24/7", "adult_cost": 0, "child_cost": 0, 
        "activity_hours": 0.5, "travel_time": 0.3, "icon": "🗿",
        "lat": 41.6556, "lon": 41.6394,
        "details": "צפייה בפסל הדינמי המפורסם על קו המים."
    },
    {
        "day": 2, "region": "באטומי (אטרקציות)", "site": "הדולפינריום של באטומי",
        "hours": "16:00 / 19:00 (סגור שני)", "adult_cost": 25, "child_cost": 25, 
        "activity_hours": 2.0, "travel_time": 0.4, "icon": "🐬",
        "lat": 41.6475, "lon": 41.6231,
        "details": "מופע דולפינים מרהיב וחווייתי. אטרקציה נהדרת לילדות."
    },
    {
        "day": 2, "region": "באטומי (אטרקציות)", "site": "רכבל ארגו (Argo Cable Car)",
        "hours": "10:00 - 22:00", "adult_cost": 30, "child_cost": 15, 
        "activity_hours": 1.5, "travel_time": 0.3, "icon": "🚡",
        "lat": 41.6472, "lon": 41.6455,
        "details": "עלייה לתצפית פנורמית מרהיבה על כל העיר והים השחור בפארק הניסים."
    },
    {
        "day": 2, "region": "באטומי (אטרקציות)", "site": "הגנים הבוטניים של באטומי",
        "hours": "09:00 - 19:30", "adult_cost": 30, "child_cost": 30, 
        "activity_hours": 3.0, "travel_time": 0.4, "icon": "🌳",
        "lat": 41.6963, "lon": 41.7163,
        "details": "סיור בטבע ירוק ועשיר הנושק לים. מומלץ לקחת שאטל בשל השטח התלול."
    },
    {
        "day": 3, "region": "מרטווילי ופרומתאוס", "site": "מערת פרומתאוס (Prometheus Cave)",
        "hours": "10:00 - 17:00 (סגור שני)", "adult_cost": 40, "child_cost": 40, 
        "activity_hours": 2.5, "travel_time": 2.0, "icon": "🦇",
        "lat": 42.3768, "lon": 42.6009,
        "details": "מערת נטיפים תת-קרקעית מרהיבה עם תאורה צבעונית ושייט בסירה."
    },
    {
        "day": 3, "region": "מרטווילי ופרומתאוס", "site": "קניון מרטווילי (Martvili Canyon)",
        "hours": "10:00 - 17:30 (סגור שני)", "adult_cost": 32.25, "child_cost": 32.25, 
        "activity_hours": 2.5, "travel_time": 1.0, "icon": "🛶",
        "lat": 42.4578, "lon": 42.3767,
        "details": "שייט בסירות מתנפחות בתוך קניון מים ירוק וציורי."
    },
    {
        "day": 4, "region": "טביליסי", "site": "פארק מתאצמינדה (Mtatsminda Park)",
        "hours": "11:00 - 22:00", "adult_cost": 10, "child_cost": 10, 
        "activity_hours": 3.5, "travel_time": 0.5, "icon": "🎢",
        "lat": 41.6946, "lon": 44.7865,
        "details": "פארק שעשועים בראש ההר המשקיף על טביליסי, הגעה באמצעות פוניקולור."
    },
    {
        "day": 4, "region": "טביליסי", "site": "רכבל ומצודת נריקלה (Narikala)",
        "hours": "10:00 - 22:00", "adult_cost": 5, "child_cost": 5, 
        "activity_hours": 1.5, "travel_time": 0.3, "icon": "🏰",
        "lat": 41.6881, "lon": 44.8093,
        "details": "רכבל נריקלה, מצודת נריקלה ופסל אמא גאורגיה - תצפית מרשימה וטיול קל."
    },
    {
        "day": 5, "region": "דשבשי + קחתי", "site": "גשר היהלום בדשבשי (Dashbashi Canyon)",
        "hours": "10:00 - 19:00", "adult_cost": 49, "child_cost": 49, 
        "activity_hours": 2.5, "travel_time": 2.0, "icon": "💎",
        "lat": 41.5975, "lon": 44.0253,
        "details": "גשר זכוכית שקוף מעל קניון עמוק עם בר מסעדה בצורת יהלום."
    },
    {
        "day": 5, "region": "דשבשי + קחתי", "site": "מנזר בודבה ועיירת האהבה סיגנאגי",
        "hours": "שעות יום", "adult_cost": 0, "child_cost": 0, 
        "activity_hours": 2.0, "travel_time": 1.5, "icon": "⛪",
        "lat": 41.6116, "lon": 45.9333,
        "details": "חומות ציוריות, סמטאות אבן ונוף לעמק אלזאני."
    },
    {
        "day": 5, "region": "דשבשי + קחתי", "site": "יקב חארבה (Khareba)",
        "hours": "10:00 - 18:00", "adult_cost": 25, "child_cost": 10, 
        "activity_hours": 1.5, "travel_time": 0.5, "icon": "🍇",
        "lat": 41.9366, "lon": 45.8361,
        "details": "מנהרות אבן לאחסון יין וטעימות (כולל מיץ ענבים טבעי לילדות)."
    },
    {
        "day": 6, "region": "הדרך הצבאית וגודאורי", "site": "מצודת אננורי ומאגר ז'ינוואלי",
        "hours": "09:00 - 19:00", "adult_cost": 0, "child_cost": 0, 
        "activity_hours": 1.0, "travel_time": 1.5, "icon": "🌊",
        "lat": 42.1643, "lon": 44.7032,
        "details": "אגם טורקיז ומצודה היסטורית שמורה."
    },
    {
        "day": 6, "region": "הדרך הצבאית וגודאורי", "site": "אנדרטת גודאורי + רכבת הרים אלפינית",
        "hours": "שעות היום", "adult_cost": 20, "child_cost": 20, 
        "activity_hours": 2.0, "travel_time": 1.0, "icon": "🛷",
        "lat": 42.4925, "lon": 44.4533,
        "details": "תצפית נוף אלפינית עוצרת נשימה וגלישה בקרוניות במורד ההר."
    },
    {
        "day": 7, "region": "קזבגי (סטפנצמינדה)", "site": "כנסיית גרגטי (Gergeti Trinity Church)",
        "hours": "אור יום", "adult_cost": 60, "child_cost": 60, 
        "activity_hours": 2.5, "travel_time": 1.0, "icon": "🏔️",
        "lat": 42.6629, "lon": 44.6203,
        "details": "כנסייה מפורסמת למרגלות הר קזבק (הגעה בג'יפ 4x4 מקומי)."
    },
    {
        "day": 7, "region": "קזבגי (סטפנצמינדה)", "site": "מלון Rooms Kazbegi (קפה ותצפית)",
        "hours": "12:00 - 22:00", "adult_cost": 40, "child_cost": 30, 
        "activity_hours": 1.5, "travel_time": 0.3, "icon": "☕",
        "lat": 42.6566, "lon": 44.6464,
        "details": "ארוחה או קפה במרפסת המפורסמת מול ההרים."
    },
    {
        "day": 8, "region": "טביליסי העתיקה", "site": "מרחצאות חמי אורבליאני",
        "hours": "08:00 - 23:00", "adult_cost": 75, "child_cost": 0, 
        "activity_hours": 1.5, "travel_time": 0.3, "icon": "🛁",
        "lat": 41.6880, "lon": 44.8115,
        "details": "חדר פרטי משפחתי במרחצאות הגופרית ההיסטוריים."
    },
    {
        "day": 8, "region": "טביליסי העתיקה", "site": "מפל לגווטכבי וגשר השלום",
        "hours": "24/7", "adult_cost": 0, "child_cost": 0, 
        "activity_hours": 2.0, "travel_time": 0.3, "icon": "🌉",
        "lat": 41.6865, "lon": 44.8090,
        "details": "מפל טבעי המסתתר בלב העיר העתיקה וגשר הזכוכית."
    },
    {
        "day": 9, "region": "שקווטילי", "site": "הפארק הדנדרולוגי (Dendrological Park)",
        "hours": "10:00 - 18:00 (סגור שני/רביעי)", "adult_cost": 0, "child_cost": 0, 
        "activity_hours": 2.5, "travel_time": 1.0, "icon": "🦩",
        "lat": 41.9372, "lon": 41.7644,
        "details": "פארק עצום עם עצי ענק עתיקים ואגם ציפורים ופלמינגו."
    },
    {
        "day": 9, "region": "שקווטילי", "site": "פארק המוזיקאים (Musicians Park)",
        "hours": "24/7", "adult_cost": 0, "child_cost": 0, 
        "activity_hours": 1.5, "travel_time": 0.3, "icon": "🎵",
        "lat": 41.9167, "lon": 41.7681,
        "details": "יער קסום עם פסלי מוזיקאים מפורסמים המנגנים את יצירותיהם."
    },
    {
        "day": 10, "region": "באטומי (סיום)", "site": "שוק הדגים של באטומי (Batumi Fish Market)",
        "hours": "09:00 - 20:00", "adult_cost": 40, "child_cost": 30, 
        "activity_hours": 2.0, "travel_time": 0.0, "icon": "🐟",
        "lat": 41.6495, "lon": 41.6521,
        "details": "בוחרים דגים טריים ושוק ומבשלים לכם אותם במסעדה הצמודה לארוחת סיום."
    }
]

# ==========================================
# סרגל צד - ניווט, הרכב משפחתי וסינון
# ==========================================
with st.sidebar:
    # הצגת תמונת המשפחה שהעלית בסרגל הצד
    try:
        st.image("IMG_1101.jpg", use_container_width=True, caption="המשפחה המטיילת ✈️")
    except FileNotFoundError:
        st.warning("⚠️ לא נמצאה התמונה IMG_1101.jpg באותה תיקייה.")
        
    st.markdown("---")
    st.header("👨‍👩‍👧‍👧 הרכב משפחתי")
    adults = st.number_input("מספר מבוגרים", min_value=1, value=2, step=1)
    children = st.number_input("מספר ילדים", min_value=0, value=2, step=1)
        
    st.markdown("---")
    st.header("⚙️ בקרת מסלול")
    
    selected_tab = st.selectbox(
        "בחר מצב תצוגה:", 
        options=[
            "📅 פירוט מסלול ואטרקציות", 
            "📊 דשבורד עלויות וזמנים (גרפים)",
            "🗺️ מפת האטרקציות"
        ]
    )
    
    st.markdown("---")
    selected_day = st.selectbox("סינון לפי יום בטיול:", options=["הכל"] + list(range(1, 11)))

# המרת הנתונים ל-DataFrame (תוך התחשבות בהרכב המשפחתי הדינמי)
df = pd.DataFrame(itinerary)
df['total_cost_gel'] = (adults * df['adult_cost']) + (children * df['child_cost'])
df['total_hours'] = df['activity_hours'] + df['travel_time']

# סינון נתונים לפי סרגל הצד (רלוונטי לכל התצוגות)
filtered_df = df.copy()
if selected_day != "הכל":
    filtered_df = filtered_df[filtered_df['day'] == int(selected_day)]

# סיכום יומי נגזר מהנתונים המסוננים
daily_summary = filtered_df.groupby('day').agg({
    'total_cost_gel': 'sum',
    'activity_hours': 'sum',
    'travel_time': 'sum',
    'total_hours': 'sum',
    'site': 'count'
}).reset_index().rename(columns={'site': 'num_sites'})

# ==========================================
# תצוגה 1: פירוט מלא של אטרקציות המסלול
# ==========================================
if selected_tab == "📅 פירוט מסלול ואטרקציות":
    day_title = f"לכל הימים (כל הטיול)" if selected_day == "הכל" else f"עבור יום {selected_day}"
    st.subheader(f"📍 הצגת אטרקציות ({len(filtered_df)} פריטים מוצגים) — {day_title}")
    
    # כפתור הורדה לקובץ CSV
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 הורד את המסלול לקובץ Excel/CSV (אופליין)",
        data=csv,
        file_name='georgia_trip_itinerary.csv',
        mime='text/csv',
    )
    st.markdown("---")
    
    if filtered_df.empty:
        st.warning("לא נמצאו אטרקציות לסינון הנבחר.")
    
    for idx, row in filtered_df.iterrows():
        st.markdown(f"""
        <div class="site-card">
            <h2>{row['icon']} יום {row['day']} | {row['site']}</h2>
            <p><b>📍 אזור:</b> {row['region']}</p>
            <p><b>📝 פרטים:</b> {row['details']}</p>
            <p>🕒 <b>שעות פתיחה:</b> {row['hours']}</p>
            <p>⏱️ <b>משך פעילות:</b> {row['activity_hours']} שעות &nbsp;&nbsp;|&nbsp;&nbsp; 🚗 <b>זמן נסיעה אל האתר:</b> {row['travel_time']} שעות</p>
            <p style="color: #2e7d32; font-weight: bold;">💰 עלות משפחתית (עבור {adults} מבוגרים ו-{children} ילדים): {row['total_cost_gel']} לארי (GEL)</p>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# תצוגה 2: דשבורד עלויות וזמנים (גרפים)
# ==========================================
elif selected_tab == "📊 דשבורד עלויות וזמנים (גרפים)":
    dashboard_title = "סיכום לכלל הטיול" if selected_day == "הכל" else f"סיכום עבור יום {selected_day} בלבד"
    st.subheader(f"📊 דשבורד עלויות וזמנים ({dashboard_title})")
    st.markdown("---")
    
    if selected_day != "הכל":
        st.info(f"💡 אתה צופה כעת בנתונים ממוקדים ל**יום {selected_day}**. כדי לראות את כל הימים והגרפים המלאים של הטיול, בחר ב'הכל' בסרגל הצד.")
    
    # מדדי KPI
    col1, col2, col3 = st.columns(3)
    total_cost_sel = filtered_df['total_cost_gel'].sum()
    total_hours_sel = filtered_df['total_hours'].sum()
    total_activity_sel = filtered_df['activity_hours'].sum()
    total_travel_sel = filtered_df['travel_time'].sum()
    
    # שער המרה ל-₪
    GEL_TO_ILS = 1.38
    total_cost_ils = total_cost_sel * GEL_TO_ILS
    
    col1.metric("💰 סך עלות אטרקציות", f"{total_cost_sel:,.0f} GEL", f"~ {total_cost_ils:,.0f} ₪", delta_color="off")
    col2.metric("⏱️ סך שעות פעילות ונסיעות", f"{total_hours_sel:,.1f} שעות")
    col3.metric("🚗 זמן נסיעה מול ⏱️ פעילות", f"{total_travel_sel} נסיעה / {total_activity_sel} פעילות")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if not daily_summary.empty:
        st.subheader("💵 עלות משפחתית (לארי GEL)")
        fig_cost = px.bar(
            daily_summary, x='day', y='total_cost_gel',
            text='total_cost_gel', color='total_cost_gel',
            color_continuous_scale='Greens',
            labels={'day': 'יום בטיול', 'total_cost_gel': 'עלות בלארי (GEL)'}
        )
        fig_cost.update_traces(textposition='outside')
        fig_cost.update_layout(plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(tickmode='linear', tick0=1, dtick=1))
        st.plotly_chart(fig_cost, use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.subheader("🚗 חלוקת זמנים: פעילות באטרקציות מול זמן נסיעה (שעות)")
        fig_time = go.Figure()
        fig_time.add_trace(go.Bar(x=daily_summary['day'], y=daily_summary['activity_hours'], name='שעות פעילות באטרקציות', marker_color='#1f77b4'))
        fig_time.add_trace(go.Bar(x=daily_summary['day'], y=daily_summary['travel_time'], name='זמני נסיעה בין אתרים', marker_color='#ff7f0e'))
        
        fig_time.update_layout(
            barmode='stack',
            xaxis_title='יום בטיול',
            yaxis_title='שעות',
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickmode='linear', tick0=1, dtick=1)
        )
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.warning("אין נתונים להצגה.")

# ==========================================
# תצוגה 3: מפת האטרקציות 
# ==========================================
elif selected_tab == "🗺️ מפת האטרקציות":
    map_title = "כל האטרקציות ברחבי גאורגיה" if selected_day == "הכל" else f"האטרקציות ביום {selected_day}"
    st.subheader(f"🗺️ {map_title}")
    st.markdown("המפה מציגה את הנקודות שבהן תבקרו. תוכלו להתקרב ולהתרחק (Zoom in/out) כדי לראות את המיקום המדויק.")
    st.markdown("---")
    
    if not filtered_df.empty:
        # Streamlit st.map מזהה אוטומטית עמודות בשם lat ו-lon ומציירת נקודות
        st.map(filtered_df[['lat', 'lon']], zoom=6)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.write("📌 **פירוט הנקודות המוצגות במפה (לפי סדר המסלול):**")
        for idx, row in filtered_df.iterrows():
            st.write(f"- {row['icon']} **יום {row['day']}:** {row['site']} ({row['region']})")
    else:
        st.warning("אין נקודות ציון להצגה עבור היום הנבחר.")
