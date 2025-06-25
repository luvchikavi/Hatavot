import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px # Import plotly for the pie chart
from datetime import date # Import date for date inputs

# הגדרת קבועים עבור סכומי ההטבות (יש לעדכן מספרים אלה על פי הנתונים הרשמיים העדכניים)
# Constants for benefit amounts (these should be updated with official, current figures)
ANNUAL_GRANT_PER_DAY_THRESHOLD = 32  # סף ימים למענק שנתי
ANNUAL_GRANT_AMOUNT_THRESHOLD_1 = 1200 # סכום מענק ראשון
ANNUAL_GRANT_AMOUNT_THRESHOLD_2 = 2500 # סכום מענק שני
ANNUAL_GRANT_AMOUNT_THRESHOLD_3 = 4000 # סכום מענק שלישי

FAMILY_GRANT_PER_10_DAYS = 1000  # מענק משפחה מוגדלת לכל 10 ימים
PERSONAL_EXPENSES_GRANT_PER_10_DAYS = 466  # מענק הוצאות אישיות מוגדל לכל 10 ימים
ROAD_6_MAX_REFUND = 300  # החזר כביש 6 מקסימלי לחודש קלנדרי

BABYSITTER_MAX_COMBATANT = 3500  # מקסימום בייביסיטר ללוחם
BABYSITTER_MAX_REAR = 2000  # מקסימום בייביסיטר לעורף

DOG_BOARDING_MAX = 500  # מקסימום פנסיון כלבים

THERAPY_MAX_LOW_DAYS = 1500  # מקסימום טיפול רגשי - סכום נמוך יותר
THERAPY_MAX_HIGH_DAYS = 2500  # מקסימום טיפול רגשי - סכום גבוה יותר (לרוב לוחמים ו/או מעל ימי שירות מסוימים)
THERAPY_DAYS_THRESHOLD = 20 # ימי שירות לטיפול רגשי בסכום גבוה

TUITION_PERCENT_COMBATANT = 1.0  # 100% החזר שכר לימוד ללוחמים
TUITION_DAYS_THRESHOLD = 20 # ימי שירות להחזר שכר לימוד

CAMPS_MAX_COMBATANT_FAMILY = 2000  # מקסימום קייטנות למשפחת לוחם
SPOUSE_ONE_TIME_GRANT = 4500  # מענק חד פעמי לבן זוג לא עובד

TZAV_8_DAYS_FOR_TRAINING = 45 # ימי שירות בצו 8 להכשרה מקצועית

# פונקציה לחישוב זכאויות והטבות כספיות
def calculate_benefits(
    avg_salary, reserve_days, unit_type, num_children, is_married,
    has_non_working_spouse, is_student, tuition_cost, used_road_6, road_6_cost,
    babysitter_cost, dog_boarding_cost, vacation_cancel_cost, therapy_cost,
    camps_cost, is_tzav_8, mortgage_rent_cost_input, needs_dedicated_medical_assistance, needs_preferred_loans
):
    entitlements = []
    total_monetary_benefits_immediate = 0
    total_monetary_benefits_future = 0
    monetary_breakdown_for_chart = []

    daily_salary_compensation = 0
    if avg_salary > 0 and reserve_days > 0:
        daily_salary_compensation = (avg_salary / 30) * reserve_days
        entitlements.append({
            "קטגוריה": "תשלום שכר",
            "הטבה / תגמול": "תגמול ביטוח לאומי",
            "פירוט והערות": f"תשלום עבור {reserve_days} ימי מילואים לפי ממוצע שכר.",
            "סכום משוער (ש״ח)": daily_salary_compensation,
            "סוג תשלום": "מיידי"
        })
        total_monetary_benefits_immediate += daily_salary_compensation

    annual_grant = 0
    if reserve_days >= ANNUAL_GRANT_PER_DAY_THRESHOLD:
        if reserve_days >= 200:
            annual_grant = ANNUAL_GRANT_AMOUNT_THRESHOLD_3
        elif reserve_days >= 60:
            annual_grant = ANNUAL_GRANT_AMOUNT_THRESHOLD_2
        elif reserve_days >= ANNUAL_GRANT_PER_DAY_THRESHOLD:
            annual_grant = ANNUAL_GRANT_AMOUNT_THRESHOLD_1

    if annual_grant > 0:
        entitlements.append({
            "קטגוריה": "מענקים שנתיים",
            "הטבה / תגמול": "מענק שנתי",
            "פירוט והערות": f"מענק שנתי המשולם ב-1 במאי לשנה העוקבת עבור {reserve_days} ימי שירות.",
            "סכום משוער (ש״ח)": annual_grant,
            "סוג תשלום": "עתידי (מאי)"
        })
        total_monetary_benefits_future += annual_grant
        monetary_breakdown_for_chart.append({"name": "מענק שנתי", "value": annual_grant})

    family_grant = 0
    if is_married and reserve_days > 30 and num_children > 0:
        additional_days = reserve_days - 30
        family_grant = (additional_days // 10) * FAMILY_GRANT_PER_10_DAYS
        if family_grant > 0:
            entitlements.append({
                "קטגוריה": "מענקים מיוחדים",
                "הטבה / תגמול": "מענק משפחה מוגדלת",
                "פירוט והערות": f"תשלום נוסף למשפחות עבור כל 10 ימי שירות לאחר 30 יום שירות רצופים.",
                "סכום משוער (ש״ח)": family_grant,
                "סוג תשלום": "מיידי"
            })
            total_monetary_benefits_immediate += family_grant
            monetary_breakdown_for_chart.append({"name": "מענק משפחה מוגדלת", "value": family_grant})

    personal_expenses_grant = 0
    if reserve_days > 0:
        personal_expenses_grant = (reserve_days // 10) * PERSONAL_EXPENSES_GRANT_PER_10_DAYS
        if personal_expenses_grant > 0:
            entitlements.append({
                "קטגוריה": "מענקים מיוחדים",
                "הטבה / תגמול": "מענק הוצאות אישיות מוגדל",
                "פירוט והערות": f"מענק מוגדל בהתאם לימי השירות ({PERSONAL_EXPENSES_GRANT_PER_10_DAYS} ש\"ח לכל 10 ימים).",
                "סכום משוער (ש״ח)": personal_expenses_grant,
                "סוג תשלום": "מיידי"
            })
            total_monetary_benefits_immediate += personal_expenses_grant
            monetary_breakdown_for_chart.append({"name": "מענק הוצאות אישיות מוגדל", "value": personal_expenses_grant})

    road_6_refund = 0
    if used_road_6 and road_6_cost > 0:
        road_6_refund = min(road_6_cost, ROAD_6_MAX_REFUND)
        entitlements.append({
            "קטגוריה": "מענקי הוצאות",
            "הטבה / תגמול": "החזר כביש 6",
            "פירוט והערות": f"החזר עד {ROAD_6_MAX_REFUND} ש\"ח לחודש קלנדרי.",
            "סכום משוער (ש״ח)": road_6_refund,
            "סוג תשלום": "מיידי"
        })
        total_monetary_benefits_immediate += road_6_refund
        monetary_breakdown_for_chart.append({"name": "החזר כביש 6", "value": road_6_refund})

    babysitter_refund = 0
    if num_children > 0 and babysitter_cost > 0:
        max_babysitter_refund = BABYSITTER_MAX_COMBATANT if unit_type == "לוחם" else BABYSITTER_MAX_REAR
        babysitter_refund = min(babysitter_cost, max_babysitter_refund)
        entitlements.append({
            "קטגוריה": "החזרי הוצאות אישיות",
            "הטבה / תגמול": "בייביסיטר",
            "פירוט והערות": f"החזר עד {max_babysitter_refund} ש\"ח לחודש (ללוחמים/עורף).",
            "סכום משוער (ש״ח)": babysitter_refund,
            "סוג תשלום": "מיידי"
        })
        total_monetary_benefits_immediate += babysitter_refund
        monetary_breakdown_for_chart.append({"name": "בייביסיטר", "value": babysitter_refund})

    dog_boarding_refund = 0
    if dog_boarding_cost > 0:
        dog_boarding_refund = min(dog_boarding_cost, DOG_BOARDING_MAX)
        entitlements.append({
            "קטגוריה": "החזרי הוצאות אישיות",
            "הטבה / תגמול": "פנסיון כלבים",
            "פירוט והערות": f"החזר עד {DOG_BOARDING_MAX} ש\"ח.",
            "סכום משוער (ש״ח)": dog_boarding_refund,
            "סוג תשלום": "מיידי"
        })
        total_monetary_benefits_immediate += dog_boarding_refund
        monetary_breakdown_for_chart.append({"name": "פנסיון כלבים", "value": dog_boarding_refund})

    vacation_cancel_refund = 0
    if vacation_cancel_cost > 0:
        vacation_cancel_refund = vacation_cancel_cost
        entitlements.append({
            "קטגוריה": "החזרי הוצאות",
            "הטבה / תגמול": "ביטול חופשה וטיסה",
            "פירוט והערות": "פיצוי מלא או חלקי בהתאם לתנאים.",
            "סכום משוער (ש״ח)": vacation_cancel_refund,
            "סוג תשלום": "מיידי"
        })
        total_monetary_benefits_immediate += vacation_cancel_refund
        monetary_breakdown_for_chart.append({"name": "ביטול חופשה וטיסה", "value": vacation_cancel_refund})

    therapy_refund = 0
    if therapy_cost > 0:
        max_therapy_refund = THERAPY_MAX_HIGH_DAYS if (unit_type == "לוחם" and reserve_days >= THERAPY_DAYS_THRESHOLD) else THERAPY_MAX_LOW_DAYS
        therapy_refund = min(therapy_cost, max_therapy_refund)
        entitlements.append({
            "קטגוריה": "טיפול רגשי ונפשי",
            "הטבה / תגמול": "טיפול אישי וזוגי",
            "פירוט והערות": f"החזר עד {max_therapy_refund} ש\"ח, תלוי בימי השירות ובסוג היחידה.",
            "סכום משוער (ש״ח)": therapy_refund,
            "סוג תשלום": "מיידי"
        })
        total_monetary_benefits_immediate += therapy_refund
        monetary_breakdown_for_chart.append({"name": "טיפול רגשי ונפשי", "value": therapy_refund})

    tuition_refund = 0
    if is_student and tuition_cost > 0 and unit_type == "לוחם" and reserve_days >= TUITION_DAYS_THRESHOLD:
        tuition_refund = tuition_cost * TUITION_PERCENT_COMBATANT
        entitlements.append({
            "קטגוריה": "זכאות מיוחדת לסטודנטים",
            "הטבה / תגמול": "החזר שכר לימוד",
            "פירוט והערות": f"עד 100% ללוחמים (תלוי במספר ימי שירות).",
            "סכום משוער (ש״ח)": tuition_refund,
            "סוג תשלום": "מיידי"
        })
        total_monetary_benefits_immediate += tuition_refund
        monetary_breakdown_for_chart.append({"name": "החזר שכר לימוד", "value": tuition_refund})

    camps_refund = 0
    if num_children > 0 and camps_cost > 0 and unit_type == "לוחם":
        camps_refund = min(camps_cost, CAMPS_MAX_COMBATANT_FAMILY)
        entitlements.append({
            "קטגוריה": "הטבות משפחתיות",
            "הטבה / תגמול": "השתתפות בקייטנות",
            "פירוט והערות": f"עד {CAMPS_MAX_COMBATANT_FAMILY} ש\"ח בשנה למשפחה (לוחמים).",
            "סכום משוער (ש״ח)": camps_refund,
            "סוג תשלום": "מיידי"
        })
        total_monetary_benefits_immediate += camps_refund
        monetary_breakdown_for_chart.append({"name": "השתתפות בקייטנות", "value": camps_refund})

    if has_non_working_spouse and is_married:
        entitlements.append({
            "קטגוריה": "מענקים מיוחדים",
            "הטבה / תגמול": "מענק חד פעמי לבן זוג לא עובד",
            "פירוט והערות": f"{SPOUSE_ONE_TIME_GRANT} ש\"ח חד פעמי.",
            "סכום משוער (ש״ח)": SPOUSE_ONE_TIME_GRANT,
            "סוג תשלום": "מיידי"
        })
        total_monetary_benefits_immediate += SPOUSE_ONE_TIME_GRANT
        monetary_breakdown_for_chart.append({"name": "מענק חד פעמי לבן זוג לא עובד", "value": SPOUSE_ONE_TIME_GRANT})

    if is_tzav_8 and reserve_days >= TZAV_8_DAYS_FOR_TRAINING:
        entitlements.append({
            "קטגוריה": "הטבות תעסוקתיות",
            "הטבה / תגמול": "שוברים להכשרה מקצועית",
            "פירוט והערות": f"למשרתים {TZAV_8_DAYS_FOR_TRAINING} ימים ומעלה בצו 8. (הטבה שאינה כספית ישירה)",
            "סכום משוער (ש״ח)": "לא כספי",
            "סוג תשלום": "שובר"
        })

    if reserve_days >= 20:
        entitlements.append({
            "קטגוריה": "הטבות נוספות",
            "הטבה / תגמול": "שוברי חופשה",
            "פירוט והערות": "שוברים לחופשה/נופש. (הטבה שאינה כספית ישירה)",
            "סכום משוער (ש״ח)": "לא כספי",
            "סוג תשלום": "שובר"
        })

    mortgage_rent_refund = 0
    if mortgage_rent_cost_input > 0:
        mortgage_rent_refund = mortgage_rent_cost_input
        entitlements.append({
            "קטגוריה": "הטבות מגורים",
            "הטבה / תגמול": "סיוע בשכר דירה/משכנתא",
            "פירוט והערות": f"סיוע עד {mortgage_rent_cost_input} ש״ח.",
            "סכום משוער (ש״ח)": mortgage_rent_refund,
            "סוג תשלום": "מיידי"
        })
        total_monetary_benefits_immediate += mortgage_rent_refund
        monetary_breakdown_for_chart.append({"name": "סיוע שכר דירה/משכנתא", "value": mortgage_rent_refund})


    if reserve_days >= 10:
        entitlements.append({
            "קטגוריה": "הטבות כלליות",
            "הטבה / תגמול": "הנחות באגרות רישוי",
            "פירוט והערות": "הנחות אפשריות באגרות רישוי רכב.",
            "סכום משוער (ש״ח)": "לא כספי",
            "סוג תשלום": "הטבה"
        })
        entitlements.append({
            "קטגוריה": "הטבות כלליות",
            "הטבה / תגמול": "הטבות בתחבורה ציבורית",
            "פירוט והערות": "הטבות בשימוש בתחבורה ציבורית.",
            "סכום משוער (ש״ח)": "לא כספי",
            "סוג תשלום": "הטבה"
        })
        entitlements.append({
            "קטגוריה": "הטבות כלליות",
            "הטבה / תגמול": "הטבות בביטוחי בריאות משלימים",
            "פירוט והערות": "הנחות או הטבות בהצטרפות לביטוחי בריאות משלימים.",
            "סכום משוער (ש״ח)": "לא כספי",
            "סוג תשלום": "הטבה"
        })
        entitlements.append({
            "קטגוריה": "הטבות כלליות",
            "הטבה / תגמול": "הטבות בארנונה / מים (רשות מקומית)",
            "פירוט והערות": "הנחות אפשריות בתשלומי ארנונה או מים.",
            "סכום משוער (ש״ח)": "לא כספי",
            "סוג תשלום": "הטבה"
        })
        entitlements.append({
            "קטגוריה": "הטבות כלליות",
            "הטבה / תגמול": "הטבות במוסדות תרבות ופנאי",
            "פירוט והערות": "הנחות או כניסה חינם למוזיאונים, תיאטראות וכדומה.",
            "סכום משוער (ש״ח)": "לא כספי",
            "סוג תשלום": "הטבה"
        })
        entitlements.append({
            "קטגוריה": "הטבות כלליות",
            "הטבה / תגמול": "הטבות בנופש ואירוח",
            "פירוט והערות": "הנחות בבתי מלון, צימרים או אתרי נופש.",
            "סכום משוער (ש״ח)": "לא כספי",
            "סוג תשלום": "הטבה"
        })

    if needs_dedicated_medical_assistance:
        entitlements.append({
            "קטגוריה": "בריאות",
            "הטבה / תגמול": "סיוע רפואי ייעודי",
            "פירוט והערות": "סיוע רפואי ייעודי דרך אגף שיקום במשרד הביטחון במידה של פציעה/מחלה הקשורה לשירות.",
            "סכום משוער (ש״ח)": "לא כספי",
            "סוג תשלום": "הטבה"
        })

    if needs_preferred_loans:
        entitlements.append({
            "קטגוריה": "הטבות כלכליות",
            "הטבה / תגמול": "הלוואות בתנאים מועדפים",
            "פירוט והערות": "הלוואות בתנאים מועדפים דרך בנקים או קרנות מסוימות.",
            "סכום משוער (ש״ח)": "לא כספי",
            "סוג תשלום": "הטבה"
        })

    return entitlements, daily_salary_compensation, total_monetary_benefits_immediate, total_monetary_benefits_future, monetary_breakdown_for_chart

# ==================== FOOTER ====================
def add_footer():
    st.markdown("---")
    st.markdown("**@2025 Drishti Consulting | Designed by Dr. Luvchik**", unsafe_allow_html=True)
    st.markdown("All right reserved", unsafe_allow_html=True)

# Set application title and page configuration
st.set_page_config(layout="wide", page_title="מחשבון הטבות ושווי יום מילואים")

st.markdown("""
    <style>
        /* General styles for headers */
        .main-header {
            font-size: 3.5em; /* Increased size */
            color: black; /* Changed to black */
            text-align: center; /* Center for more impact */
            margin-bottom: 10px; /* Reduced margin */
            font-weight: bold;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.2); /* Softer shadow */
            -webkit-background-clip: unset; /* Remove gradient effect */
            -webkit-text-fill-color: initial; /* Reset text fill color */
            animation: fadeInScale 1s ease-out; /* Simple animation */
        }
        @keyframes fadeInScale {
            from { opacity: 0; transform: scale(0.9); }
            to { opacity: 1; transform: scale(1); }
        }

        .app-subtitle {
            font-size: 1.5em; /* Larger */
            color: #333; /* Darker color (almost black) */
            text-align: right; /* Aligned right as requested */
            margin-top: -10px; /* Pull closer to title */
            margin-bottom: 20px;
            font-weight: bold; /* Bold */
            animation: slideInRight 0.8s ease-out; /* Animation */
        }
        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(20px); }
            to { opacity: 1; transform: translateX(0); }
        }

        .developed-by-logo-placeholder {
            /* This div is a placeholder for where the logo might go */
            text-align: right;
            margin-bottom: 20px;
            /* Add styling for the image itself if needed, e.g., max-width */
        }

        .subheader {
            font-size: 1.8em;
            color: #333; /* Changed to black */
            margin-top: 15px;
            margin-bottom: 10px;
            border-bottom: 2px solid #E0F2F1;
            padding-bottom: 5px;
        }

        /* Button styling */
        .stButton>button {
            background-color: #00796B;
            color: white;
            border-radius: 10px;
            padding: 10px 20px;
            font-size: 1.1em;
            border: none;
            cursor: pointer;
            transition: background-color 0.3s ease, transform 0.2s ease;
        }
        .stButton>button:hover {
            background-color: #004D40;
            transform: translateY(-2px); /* Lift effect */
        }

        /* Input field styling (for a softer, less "boxy" look) */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > div[data-baseweb="select"] { /* Specific target for selectbox */
            border: 1px solid #B2DFDB; /* Subtle border */
            border-radius: 12px; /* More rounded */
            padding: 12px 18px; /* Increased padding */
            background-color: #F0FBF9; /* Very light background, slightly off-white */
            box-shadow: 0 2px 4px rgba(0,0,0,0.05); /* Very soft shadow */
            transition: all 0.3s ease-in-out;
            font-size: 1em; /* Ensure text is readable */
        }
        /* Focus state for input fields */
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stSelectbox > div > div > div[data-baseweb="select"]:focus-within {
            outline: none;
            border-color: #00796B; /* Highlight border on focus */
            box-shadow: 0 0 0 3px rgba(0,121,107,0.2); /* Soft blue glow on focus */
        }

        /* Table styling */
        .stTable, .dataframe {
            font-size: 1.0em;
        }

        /* Metric card styling */
        .metric-card {
            background-color: #E0F2F1;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 10px;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .metric-card h3 {
            color: #004D40;
            font-size: 1.2em;
            margin-bottom: 5px;
        }
        .metric-card p {
            font-size: 1.5em;
            font-weight: bold;
            color: #00796B;
        }

        /* Tab text styling - simplified as requested */
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 1.3em; /* Larger font for tab names */
            font-weight: normal; /* No bold */
            color: #333; /* Black/dark grey */
            padding: 8px 15px;
            transition: color 0.3s ease;
        }
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] [data-testid="stMarkdownContainer"] p {
            color: #000; /* Black for active tab */
            border-bottom: 2px solid #000; /* Subtle black border for active */
        }
        .stTabs [data-baseweb="tab-list"] button:hover [data-testid="stMarkdownContainer"] p {
            color: #555; /* Slight hover effect */
        }

        /* Footer styling */
        .footer {
            text-align: center;
            padding: 20px;
            margin-top: 50px;
            color: #555;
            font-size: 1em;
            border-top: 1px solid #ddd;
        }
    </style>
""", unsafe_allow_html=True)

# Placeholder for logo (local paths cannot be accessed directly by web apps)
st.markdown('<div class="developed-by-logo-placeholder"></div>', unsafe_allow_html=True)
# If you host your logo online, you can use:
# st.image("URL_TO_YOUR_LOGO.png", width=150)
# Example placeholder if you want to see an image:
# st.image("https://placehold.co/150x50/aabbcc/ffffff?text=Drishti+Logo", width=150)


# Main header with "טיל" styling
st.markdown('<h1 class="main-header">מחשבון הטבות ושווי יום מילואים</h1>', unsafe_allow_html=True)
st.markdown('<p class="app-subtitle">כלי עזר לחיילי מילואים להערכת הטבות וחישוב שווי יום שירות.</p>', unsafe_allow_html=True)
st.markdown("---")

# Initialize session state variables if not already present
if 'results_calculated' not in st.session_state:
    st.session_state.results_calculated = False
    st.session_state.entitlements = []
    st.session_state.daily_salary_compensation_val = 0
    st.session_state.total_monetary_benefits_immediate = 0
    st.session_state.total_monetary_benefits_future = 0
    st.session_state.monetary_breakdown_for_chart = []
    st.session_state.avg_salary_display = 0
    st.session_state.reserve_days_display = 0
    st.session_state.selected_tab_index = 0 # Default to the first tab (Input Data)

# Create tabs with English names
tab_names = ["Input Data", "Summary"]
# Removed the 'key' argument from st.tabs() as it's not supported directly here.
# Removed default_index as it causes TypeError in older versions and handling selection via session state in button.
tab1, tab2 = st.tabs(tab_names)


with tab1:
    st.markdown('<h2 class="subheader">פרטים אישיים ונתוני שירות</h2>', unsafe_allow_html=True)

    col1_input, col2_input = st.columns(2)

    with col1_input:
        st.markdown("### נתוני שכר ושירות")
        avg_salary = st.number_input("שכר ממוצע ב-3 חודשים אחרונים (נטו, בשקלים):", min_value=0, value=10000, step=100, key="avg_salary_input")
        reserve_days = st.number_input("מספר ימי מילואים ששירתו השנה:", min_value=0, value=30, step=1, key="reserve_days_input")
        unit_type = st.selectbox("סוג יחידה:", ["לוחם", "עורף"], key="unit_type_select")

        # Added date inputs for reserve period
        st.markdown("### תקופת שירות מילואים")
        start_date = st.date_input("תאריך תחילת שירות מילואים:", value=date.today(), key="start_date_input")
        end_date = st.date_input("תאריך סיום שירות מילואים:", value=date.today(), key="end_date_input")


    with col2_input:
        st.markdown("### פרטים משפחתיים וסטטוס")
        is_married_str = st.selectbox("האם נשואים?", ["לא", "כן"], key="is_married_select")
        is_married = (is_married_str == "כן")
        num_children = st.number_input("מספר ילדים (מתחת לגיל 18):", min_value=0, value=0, step=1, key="num_children_input")
        has_non_working_spouse_str = st.selectbox("האם בן/בת הזוג לא עובד/ת?", ["לא", "כן"], key="has_non_working_spouse_select")
        has_non_working_spouse = (has_non_working_spouse_str == "כן")
        is_student_str = st.selectbox("האם סטודנט/ית?", ["לא", "כן"], key="is_student_select")
        is_student = (is_student_str == "כן")
        is_tzav_8_str = st.selectbox("האם שירתו בצו 8 השנה?", ["לא", "כן"], key="is_tzav_8_select")
        is_tzav_8 = (is_tzav_8_str == "כן")


    st.markdown('<h2 class="subheader">הוצאות נלוות</h2>', unsafe_allow_html=True)

    road_6_cost_enabled_str = st.selectbox("האם השתמשו בכביש 6?", ["לא", "כן"], key="road_6_enabled_select")
    road_6_cost_enabled = (road_6_cost_enabled_str == "כן")
    road_6_cost = 0
    if road_6_cost_enabled:
        road_6_cost = st.number_input("עלות שימוש בכביש 6 לחודש (בשקלים):", min_value=0, value=0, step=10, key="road_6_cost_input")

    babysitter_cost_enabled_str = st.selectbox("האם שילמו על בייביסיטר?", ["לא", "כן"], key="babysitter_enabled_select")
    babysitter_cost_enabled = (babysitter_cost_enabled_str == "כן")
    babysitter_cost = 0
    if babysitter_cost_enabled:
        babysitter_cost = st.number_input("עלות בייביסיטר לחודש (בשקלים):", min_value=0, value=0, step=50, key="babysitter_cost_input")

    dog_boarding_cost_enabled_str = st.selectbox("האם שילמו על פנסיון כלבים?", ["לא", "כן"], key="dog_boarding_enabled_select")
    dog_boarding_cost_enabled = (dog_boarding_cost_enabled_str == "כן")
    dog_boarding_cost = 0
    if dog_boarding_cost_enabled:
        dog_boarding_cost = st.number_input("עלות פנסיון כלבים (בשקלים):", min_value=0, value=0, step=50, key="dog_boarding_cost_input")

    vacation_cancel_cost_enabled_str = st.selectbox("האם נאלצו לבטל חופשה/טיסה עקב שירות מילואים?", ["לא", "כן"], key="vacation_cancel_enabled_select")
    vacation_cancel_cost_enabled = (vacation_cancel_cost_enabled_str == "כן")
    vacation_cancel_cost = 0
    if vacation_cancel_cost_enabled:
        vacation_cancel_cost = st.number_input("עלות ביטול חופשה/טיסה (בשקלים, סכום הפיצוי המגיע):", min_value=0, value=0, step=100, key="vacation_cancel_cost_input")

    therapy_cost_enabled_str = st.selectbox("האם שילמו על טיפול רגשי/נפשי?", ["לא", "כן"], key="therapy_enabled_select")
    therapy_cost_enabled = (therapy_cost_enabled_str == "כן")
    therapy_cost = 0
    if therapy_cost_enabled:
        therapy_cost = st.number_input("עלות טיפול רגשי/נפשי (בשקלים):", min_value=0, value=0, step=50, key="therapy_cost_input")

    camps_cost_enabled_str = st.selectbox("האם שילמו על קייטנות לילדים?", ["לא", "כן"], key="camps_enabled_select")
    camps_cost_enabled = (camps_cost_enabled_str == "כן")
    camps_cost = 0
    if camps_cost_enabled:
        camps_cost = st.number_input("עלות קייטנות (בשקלים, לשנה):", min_value=0, value=0, step=50, key="camps_cost_input")

    tuition_cost_enabled_str = st.selectbox("האם שילמו על שכר לימוד (לסטודנטים)?", ["לא", "כן"], key="tuition_enabled_select")
    tuition_cost_enabled = (tuition_cost_enabled_str == "כן")
    tuition_cost = 0
    if tuition_cost_enabled:
        tuition_cost = st.number_input("עלות שכר לימוד שנתית (בשקלים):", min_value=0, value=0, step=100, key="tuition_cost_input")

    mortgage_rent_cost_enabled_str = st.selectbox("האם זקוקים/קיבלו סיוע בשכר דירה/משכנתא?", ["לא", "כן"], key='mortgage_rent_checkbox_input')
    mortgage_rent_cost_enabled = (mortgage_rent_cost_enabled_str == "כן")
    mortgage_rent_cost_input = 0
    if mortgage_rent_cost_enabled:
        mortgage_rent_cost_input = st.number_input("סכום סיוע בשכר דירה/משכנתא (בשקלים):", min_value=0, value=0, step=50, key='mortgage_rent_input_field')

    needs_dedicated_medical_assistance_str = st.selectbox("האם יש צורך בסיוע רפואי ייעודי עקב פציעה/מחלה הקשורה לשירות?", ["לא", "כן"], key="dedicated_medical_select")
    needs_dedicated_medical_assistance = (needs_dedicated_medical_assistance_str == "כן")
    needs_preferred_loans_str = st.selectbox("האם מעוניינים לבדוק זכאות להלוואות בתנאים מועדפים?", ["לא", "כן"], key="preferred_loans_select")
    needs_preferred_loans = (needs_preferred_loans_str == "כן")

    if st.button("חשב הטבות", key="calculate_button"):
        st.session_state.entitlements, \
        st.session_state.daily_salary_compensation_val, \
        st.session_state.total_monetary_benefits_immediate, \
        st.session_state.total_monetary_benefits_future, \
        st.session_state.monetary_breakdown_for_chart = calculate_benefits(
            avg_salary, reserve_days, unit_type, num_children, is_married,
            has_non_working_spouse, is_student, tuition_cost, road_6_cost_enabled, road_6_cost,
            babysitter_cost_enabled, dog_boarding_cost, vacation_cancel_cost, therapy_cost,
            camps_cost, is_tzav_8, mortgage_rent_cost_input, needs_dedicated_medical_assistance, needs_preferred_loans
        )
        st.session_state.results_calculated = True
        # Setting the tab index to switch to the Summary tab
        st.session_state.selected_tab_index = 1
        st.session_state.avg_salary_display = avg_salary
        st.session_state.reserve_days_display = reserve_days
        st.rerun() # Trigger a rerun to update the displayed tab

    add_footer() # Add footer to Input Data tab as well

with tab2:
    # This block will be displayed if the results_calculated is True, regardless of how the tab was selected.
    if st.session_state.results_calculated:
        st.markdown('<h2 class="subheader">סיכום הטבות וחישובים</h2>', unsafe_allow_html=True)

        daily_salary_value = 0
        if st.session_state.avg_salary_display > 0:
            daily_salary_value = st.session_state.avg_salary_display / 30

        total_monetary_all_benefits = st.session_state.daily_salary_compensation_val + st.session_state.total_monetary_benefits_immediate + st.session_state.total_monetary_benefits_future
        daily_value_with_benefits = 0
        if st.session_state.reserve_days_display > 0:
            daily_value_with_benefits = total_monetary_all_benefits / st.session_state.reserve_days_display

        col3, col4 = st.columns(2)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>שווי יום מילואים (משכר בלבד)</h3>
                <p>{daily_salary_value:,.2f} ש"ח</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>שווי יום מילואים (כולל כל ההטבות, מיידיות ועתידיות)</h3>
                <p>{daily_value_with_benefits:,.2f} ש"ח</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('---')

        chart_data = [item for item in st.session_state.monetary_breakdown_for_chart if item["value"] > 0]
        
        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            st.markdown('<h3 style="text-align: center; color: #333;">הרכב התוספות הכספיות (למעט תגמול שכר)</h3>', unsafe_allow_html=True) # Color changed to black
            fig = px.pie(df_chart, values='value', names='name',
                         title='פירוט התוספות הכספיות באחוזים',
                         hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_traces(textinfo='percent+label', pull=[0.05]*len(df_chart))
            fig.update_layout(showlegend=True, title_x=0.5)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("אין תוספות כספיות נוספות (מלבד תגמול שכר) לחישוב תרשים פאי, או שלא הוזנו נתונים רלוונטיים.")
        
        st.markdown('---')

        if st.session_state.entitlements:
            df_entitlements = pd.DataFrame(st.session_state.entitlements)
            df_entitlements = df_entitlements[['קטגוריה', 'הטבה / תגמול', 'פירוט והערות', 'סוג תשלום', 'סכום משוער (ש״ח)']]
            st.write("### הטבות והטבות כספיות משוערות שאתם זכאים להן:")
            st.dataframe(df_entitlements, use_container_width=True)
        else:
            st.info("נראה שכרגע אין הטבות כספיות משוערות על בסיס הנתונים שהוזנו. ייתכן שאתם עדיין זכאים להטבות לא כספיות או שהנתונים דורשים בירור נוסף.")

    else:
        st.info("אנא מלאו את הפרטים בטאב 'Input Data' ולחצו על 'חשב הטבות' כדי לראות את התוצאות.")

    st.markdown("---")
    st.info("""
        **הערה חשובה**:
        * החישובים והנתונים באפליקציה זו הינם **הערכה בלבד** ואינם מהווים ייעוץ משפטי או תחליף לבירור רשמי מול הגופים הרלוונטיים (כגון ביטוח לאומי, אגף כוח אדם בצה"ל, רשויות מקומיות, וכדומה).
        * סכומי ההטבות המדויקים, תנאי הזכאות והעדכונים משתנים מעת לעת.
        * מומלץ לבדוק תמיד את המידע העדכני ביותר באתרי האינטרנט הרשמיים של צה"ל, הביטוח הלאומי וגופים ממשלתיים נוספים.
        """)
    
    add_footer()
