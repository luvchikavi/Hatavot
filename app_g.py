import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==============================================================================
# 1. הגדרות וקבועים גלובליים (מבוסס על הטבלה המלאה שאושרה)
# ==============================================================================
# --- תעריפים ---
DAILY_ADDITIONAL_GRANT_RATE = 144.43
MINIMUM_NII_DAILY_RATE = 310.5

# --- מענקים ---
FAMILY_GRANT_CHILDREN = 2500
FAMILY_GRANT_COMBATANT = 2000
COUPLES_ASSISTANCE_GRANT = 2500
SPOUSE_GRANT_MAX = 4000

# --- מענק שנתי ---
ANNUAL_GRANT_THRESHOLDS = {
    37: 5400,
    20: 4050,
    15: 2700,
    10: 1350
}

# --- שוברים ---
VACATION_VOUCHER_THRESHOLDS = {
    "לוחם/ת": {"days": 45, "value": 4500},
    "תומכ/ת לחימה": {"days": 45, "value": 3000},
    "עורפי/ת": {"days": 45, "value": 1500}
}
PROFESSIONAL_TRAINING_VOUCHER_VALUE = 7500

# --- תקרות להחזרים ---
EXPENSE_CEILINGS = {
    "therapy": 1500,
    "babysitter_combatant": 2500,
    "babysitter_other": 1500,
    "camps_per_child": 2000,
    "vacation_cancel_family": 5000,
    "vacation_cancel_per_child": 2500,
    "pet_boarding": 500,
    "tuition_combatant": 12000,
    "tuition_other": 5000
}

# --- הטבות אקדמיות ---
ACADEMIC_CREDITS_THRESHOLDS = {28: "4 נ\"ז", 14: "2 נ\"ז"}

# ==============================================================================
# 2. פונקציות עזר (UI ומצב אפליקציה)
# ==============================================================================
def change_app_state(new_state):
    st.session_state.app_state = new_state

def render_expense_input(key, label, max_amount, help_text=""):
    cost = st.number_input(label, min_value=0, step=50, key=key, help=help_text)
    if max_amount > 0:
        st.caption(f"תקרה מירבית להחזר: {max_amount:,.0f} ₪")
    return cost

def add_footer():
    st.markdown("---")
    st.markdown("**@2025 Drishti Consulting | Designed by Dr. Luvchik**")
    st.markdown("All rights reserved")

# ==============================================================================
# 3. פונקציית החישוב המרכזית (יישום מלא של הטבלה)
# ==============================================================================
def calculate_all_benefits(inputs):
    direct, future, potential = [], [], []
    days = inputs["reserve_days"]
    unit = inputs["unit_type"]
    children = inputs["num_children"]

    # לוגיקה מלאה כפי שהייתה בגרסה הקודמת והמלאה...
    # (העתקתי את כל הלוגיקה כדי להבטיח שלא חסר כלום)
    daily_nii = max(inputs["gross_salary"] / 30, MINIMUM_NII_DAILY_RATE)
    direct.append({"רכיב": "תגמול מביטוח לאומי", "פירוט": f"({daily_nii:,.2f} ₪ ליום)", "סכום (₪)": daily_nii * days})
    if inputs["is_tzav_8"]:
        direct.append({"רכיב": "תגמול נוסף (חרבות ברזל)", "פירוט": f"({DAILY_ADDITIONAL_GRANT_RATE} ₪ ליום)", "סכום (₪)": DAILY_ADDITIONAL_GRANT_RATE * days})
    if children > 0 and days >= 8 and inputs["is_tzav_8"]:
        direct.append({"רכיב": "מענק משפחה (ילדים עד גיל 14)", "פירוט": "מענק חד-פעמי", "סכום (₪)": FAMILY_GRANT_CHILDREN})
    if unit == "לוחם/ת" and days >= 10:
        direct.append({"רכיב": "מענק משפחה מוגדל (לוחמים)", "פירוט": "מענק חד-פעמי", "סכום (₪)": FAMILY_GRANT_COMBATANT})
    elif unit != "לוחם/ת" and days >= 30:
         direct.append({"רכיב": "מענק משפחה מוגדל", "פירוט": "עבור שירות של 30+ יום", "סכום (₪)": FAMILY_GRANT_COMBATANT})
    for threshold, amount in ANNUAL_GRANT_THRESHOLDS.items():
        if days >= threshold:
            if threshold == 10 and unit != "לוחם/ת": continue
            future.append({"רכיב": "מענק שנתי", "פירוט": f"עבור {days} ימי שירות, ישולם במאי", "סכום (₪)": amount})
            break
    if inputs["therapy_cost"] > 0:
        potential.append({"זכאות": "החזר טיפול רגשי/נפשי", "פירוט": "מותנה בקבלות", "שווי פוטנציאלי (₪)": min(inputs["therapy_cost"], EXPENSE_CEILINGS["therapy"])})
    if inputs["pet_boarding_cost"] > 0 and days >= 8:
        potential.append({"זכאות": "החזר פנסיון לבע\"ח", "פירוט": "מותנה בקבלות", "שווי פוטנציאלי (₪)": min(inputs["pet_boarding_cost"], EXPENSE_CEILINGS["pet_boarding"])})
    if inputs["babysitter_cost"] > 0:
        if (unit == "לוחם/ת" and days >= 10) or (unit != "לוחם/ת" and days >= 35):
            ceiling = EXPENSE_CEILINGS["babysitter_combatant"] if unit == "לוחם/ת" else EXPENSE_CEILINGS["babysitter_other"]
            potential.append({"זכאות": "החזר בייביסיטר/עזרה בבית", "פירוט": "מותנה בקבלות", "שווי פוטנציאלי (₪)": min(inputs["babysitter_cost"], ceiling)})
    if inputs["camps_cost"] > 0 and inputs["served_during_holidays"]:
         potential.append({"זכאות": "החזר קייטנות/צהרונים", "פירוט": f"עד {EXPENSE_CEILINGS['camps_per_child']:,.0f} ₪ לילד", "שווי פוטנציאלי (₪)": min(inputs["camps_cost"], EXPENSE_CEILINGS["camps_per_child"] * children)})
    if inputs["vacation_cancel_cost"] > 0 and inputs["is_tzav_8"]:
        max_refund = EXPENSE_CEILINGS["vacation_cancel_family"] + (children * EXPENSE_CEILINGS["vacation_cancel_per_child"])
        potential.append({"זכאות": "החזר ביטול חופשה/טיסה", "פירוט": "עקב גיוס בצו 8", "שווי פוטנציאלי (₪)": min(inputs["vacation_cancel_cost"], max_refund)})
    if inputs["is_student"]:
        for d, credits in ACADEMIC_CREDITS_THRESHOLDS.items():
            if days >= d:
                potential.append({"זכאות": "נקודות זכות אקדמיות", "פירוט": "מועבר אוטומטית למוסדות", "שווי פוטנציאלי (₪)": credits})
                break
        if inputs["tuition_cost"] > 0 and days >= 28:
            ceiling = EXPENSE_CEILINGS["tuition_combatant"] if unit == "לוחם/ת" else EXPENSE_CEILINGS["tuition_other"]
            potential.append({"זכאות": "סיוע בשכר לימוד", "פירוט": "דורש הגשת בקשה", "שווי פוטנציאלי (₪)": min(inputs["tuition_cost"], ceiling)})
    if days >= 20:
        potential.append({"זכאות": "הנחה בארנונה", "פירוט": "5-25%, יש לפנות לרשות המקומית", "שווי פוטנציאלי (₪)": "משתנה"})
    unit_vouchers = VACATION_VOUCHER_THRESHOLDS.get(unit)
    if unit_vouchers and days >= unit_vouchers["days"]:
        potential.append({"זכאות": "שובר חופשה", "פירוט": "נשלח אוטומטית לזכאים", "שווי פוטנציאלי (₪)": unit_vouchers["value"]})
    if days >= 45 and inputs["is_tzav_8"]:
         potential.append({"זכאות": "שובר הכשרה מקצועית", "פירוט": "דרך משרד העבודה", "שווי פוטנציאלי (₪)": PROFESSIONAL_TRAINING_VOUCHER_VALUE})
         if inputs["is_married"]:
             potential.append({"זכאות": "סיוע לזוגות", "פירוט": "מענק חד פעמי", "שווי פוטנציאלי (₪)": COUPLES_ASSISTANCE_GRANT})
    if inputs["is_self_employed"] and days >= 8 and inputs["is_tzav_8"]:
        potential.append({"זכאות": "קרן סיוע לעצמאיים", "פירוט": "פיצוי על אובדן הכנסות דרך רשות המיסים", "שווי פוטנציאלי (₪)": "תלוי מחזור"})

    return pd.DataFrame(direct), pd.DataFrame(future), pd.DataFrame(potential)

# ==============================================================================
# 4. הגדרת תצוגות העמודים
# ==============================================================================
def show_landing_page():
    st.image("https://upload.wikimedia.org/wikipedia/he/thumb/c/c8/IDF_Reserve_Component_Insignia.svg/1200px-IDF_Reserve_Component_Insignia.svg.png", width=120)
    st.title("מחשבון זכויות והטבות למשרתי המילואים")
    st.header("כלי עזר להערכת שווי יום מילואים והטבות נלוות (מעודכן \"חרבות ברזל\")")
    st.markdown("---")
    st.info("""
    **לתשומת ליבכם:**
    - מחשבון זה פותח בהתנדבות על ידי **רס\"ן (מיל') אבי לוביק**.
    - הנתונים כאן הם **הערכה בלבד** ואינם מהווים מידע רשמי.
    - יש להתעדכן תמיד מול הגורמים המוסמכים בצה\"ל ובביטוח הלאומי.
    """)
    st.markdown("---")
    st.button("התחל חישוב 🧮", type="primary", on_click=change_app_state, args=('calculator',), use_container_width=True)
    add_footer()

def show_calculator_page():
    st.header("מחשבון הטבות מילואים")
    with st.form(key="input_form"):
        st.subheader("פרטים אישיים ונתוני שירות")
        c1, c2 = st.columns(2)
        with c1:
            gross_salary = st.number_input("שכר חודשי (ברוטו)", help="החישוב מתבצע לפי הברוטו.", min_value=0, value=15000, step=500)
            reserve_days = st.number_input("סה\"כ ימי מילואים ששירתו", min_value=0, value=30, step=1)
            unit_type = st.selectbox("סוג יחידה", ["לוחם/ת", "תומכ/ת לחימה", "עורפי/ת"])
        with c2:
            num_children = st.number_input("מספר ילדים (עד גיל 18)", min_value=0, step=1)
            is_married = st.checkbox("נשוי/אה?", value=True)
            is_tzav_8 = st.checkbox("השירות בוצע בצו 8", value=True)
        
        st.subheader("סטטוסים נוספים")
        c3, c4 = st.columns(2)
        is_student = c3.checkbox("סטודנט/ית?")
        is_self_employed = c4.checkbox("עצמאי/ת?")
        
        st.markdown("---")
        st.subheader("הוצאות נלוות (אופציונלי, למילוי רק אם היו הוצאות)")
        with st.expander("👨‍👩‍👧‍👦 הוצאות משפחה וטיפול"):
            babysitter_cost = render_expense_input('babysitter_cost', 'בייביסיטר/עזרה בבית', EXPENSE_CEILINGS["babysitter_combatant"] if unit_type == "לוחם/ת" else EXPENSE_CEILINGS["babysitter_other"])
            therapy_cost = render_expense_input('therapy_cost', 'טיפול רגשי/נפשי', EXPENSE_CEILINGS["therapy"])
            pet_boarding_cost = render_expense_input('pet_boarding_cost', 'פנסיון לבע\"ח', EXPENSE_CEILINGS["pet_boarding"])
        
        with st.expander("✈️ חופשות, קייטנות ולימודים"):
            vacation_cancel_cost = render_expense_input('vacation_cancel_cost', 'ביטול חופשה/טיסה', EXPENSE_CEILINGS["vacation_cancel_family"] + (num_children * EXPENSE_CEILINGS["vacation_cancel_per_child"]))
            served_during_holidays = st.checkbox("האם השירות כלל את תקופת החופשות (קיץ/חגים)?")
            camps_cost = render_expense_input('camps_cost', 'קייטנות/צהרונים', EXPENSE_CEILINGS["camps_per_child"] * num_children if num_children > 0 else 0)
            tuition_cost = render_expense_input('tuition_cost', 'שכר לימוד (לסטודנטים)', EXPENSE_CEILINGS["tuition_combatant"] if unit_type == "לוחם/ת" else EXPENSE_CEILINGS["tuition_other"])

        submitted = st.form_submit_button("חשב זכויות", use_container_width=True, type="primary")
        if submitted:
            st.session_state.inputs = locals()
            df1, df2, df3 = calculate_all_benefits(st.session_state.inputs)
            st.session_state.results = {"direct": df1, "future": df2, "potential": df3}
            change_app_state('results')

    add_footer()

# [נוסף] פונקציה להזרקת CSS ליישור האפליקציה לימין (RTL)
def apply_rtl_style():
    """
    Applies custom CSS to the Streamlit app to enforce RTL layout.
    """
    rtl_style = """
        <style>
            /* General body and main container */
            body, .main, div[data-testid="stAppViewContainer"] {
                direction: rtl;
            }
            
            /* Align all text elements to the right */
            h1, h2, h3, h4, h5, h6, p, label, li, .st-emotion-cache-1629p8f e1nzilvr5 {
                text-align: right !important;
            }

            /* Ensure input/widget labels are aligned correctly */
            .stTextInput label, .stNumberInput label, .stSelectbox label, .stCheckbox label {
                 text-align: right !important;
                 width: 100%;
            }

            /* Align expander headers */
            .st-emotion-cache-1h9usn1 span {
                text-align: right !important;
            }

            /* Align dataframe headers and content */
            .stDataFrame th, .stDataFrame td {
                text-align: right !important;
                direction: rtl;
            }
            
            /* Align metric labels */
            div[data-testid="stMetricLabel"] {
                text-align: right !important;
            }
        </style>
    """
    st.markdown(rtl_style, unsafe_allow_html=True)

def show_results_page():
    st.header("📊 סיכום הטבות וזכאויות")
    inputs = st.session_state.inputs
    results = st.session_state.results
    
    st.subheader("פרופיל החייל שהוזן:")
    st.markdown(f"""
    - **ימי מילואים:** `{inputs['reserve_days']}` | **סוג יחידה:** `{inputs['unit_type']}` | **צו 8:** `{'כן' if inputs['is_tzav_8'] else 'לא'}`
    - **שכר ברוטו:** `{inputs['gross_salary']:,.0f} ₪` | **מצב משפחתי:** `{'נשוי/אה' if inputs['is_married'] else 'רווק/ה'}`, `{inputs['num_children']} ילדים`
    - **סטטוסים:** `{'סטודנט/ת' if inputs['is_student'] else ''}`, `{'עצמאי/ת' if inputs['is_self_employed'] else ''}`
    """)
    st.markdown("---")
    
    # [חדש] חישוב סכומים כוללים ושוויי יומי
    total_direct = results["direct"]["סכום (₪)"].sum()
    total_future = results["future"]["סכום (₪)"].sum()
    # שווי פוטנציאלי הוא רק מספרים, נתעלם מטקסט
    total_potential = pd.to_numeric(results["potential"]["שווי פוטנציאלי (₪)"], errors='coerce').sum()
    total_all_in = total_direct + total_future + total_potential
    days = inputs['reserve_days'] if inputs['reserve_days'] > 0 else 1 # למנוע חלוקה באפס
    
    st.subheader("שווי יום מילואים")
    col1, col2 = st.columns(2)
    col1.metric("שווי יום (תשלום ישיר)", f"{total_direct / days:,.2f} ₪")
    col2.metric("שווי יום (פוטנציאל מלא)", f"{total_all_in / days:,.2f} ₪", help="כולל תשלומים ישירים, עתידיים ומימוש כל ההטבות הפוטנציאליות")

    st.markdown("---")

    # [חדש] גרף פאי המציג את הרכב השווי הכולל
    st.subheader("הרכב שווי ההטבות הכולל")
    chart_data = pd.DataFrame({
        'קטגוריה': ['תשלומים ישירים', 'תשלומים עתידיים', 'פוטנציאל מימוש'],
        'סכום': [total_direct, total_future, total_potential]
    })
    chart_data = chart_data[chart_data['סכום'] > 0] # הצג רק קטגוריות רלוונטיות
    
    if not chart_data.empty:
        fig = px.pie(
            chart_data, 
            names='קטגוריה', 
            values='סכום',
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig.update_traces(textposition='inside', textinfo='percent+label', insidetextfont=dict(size=14, color='black'))
        fig.update_layout(showlegend=True, title_text='חלוקת שווי ההטבות', title_x=0.5)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("אין נתונים כספיים להצגה בגרף.")

    st.markdown("---")

    # הצגת הטבלאות המפורטות
    if not results["direct"].empty:
        st.subheader("פירוט תשלומים ישירים ומענקים")
        st.dataframe(results["direct"], use_container_width=True)
    if not results["future"].empty:
        st.subheader("פירוט תשלומים עתידיים")
        st.dataframe(results["future"], use_container_width=True)
    if not results["potential"].empty:
        st.subheader("פירוט החזרי הוצאות וזכאויות למימוש יזום")
        st.dataframe(results["potential"], use_container_width=True)

    st.markdown("---")
    st.button("⬅️ בצע חישוב חדש", on_click=change_app_state, args=('calculator',), use_container_width=True)
    add_footer()

# ==============================================================================
# 5. הפונקציה הראשית (Main)
# ==============================================================================
def run_app():
    st.set_page_config(layout="centered", page_title="מחשבון זכויות מילואים")
    
    # [נוסף] הפעלת העיצוב ליישור לימין
    apply_rtl_style()

    if 'app_state' not in st.session_state:
        st.session_state.app_state = 'landing'

    if st.session_state.app_state == 'landing': show_landing_page()
    elif st.session_state.app_state == 'calculator': show_calculator_page()
    elif st.session_state.app_state == 'results': show_results_page()

if __name__ == '__main__':
    run_app()
