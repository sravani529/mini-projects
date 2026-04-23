import streamlit as st
import folium
from typing import Tuple
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd
from geopy.distance import geodesic
from sklearn.ensemble import RandomForestClassifier
import numpy as np
from gtts import gTTS
import io
import streamlit.components.v1 as components
from dotenv import load_dotenv
from twilio.rest import Client
import os
import firebase_admin 
from firebase_admin import credentials, messaging
import json
import base64
import matplotlib.pyplot as plt
from datetime import datetime
import time
import plotly.express as px
# ----------- sms reply message function-----------
def send_sms_notification(report):
    load_dotenv(override=True)

    # ✅ Validate credentials
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")

    if not sid or not token:
        raise Exception("Twilio credentials missing")

    client = Client(sid, token)

    # ✅ Fix phone format
    phone = report['phone']
    if not phone.startswith("+"):
        phone = "+91" + phone

    try:
        # 📩 Admin message
        admin_msg = client.messages.create(
    body=(
        "NEW HEALTH REPORT\n"
        "----------------------\n"
        f"Name: {report['name']}\n"
        f"Age: {report['age']}\n"
        f"Phone: {report['phone']}\n"
        f"Industry: {report['industry']}\n"
        f"Symptoms: {report['symptoms']}\n"
        f"Address: {report['address']}\n"
        f"Time: {report['time']}\n"
        "----------------------"
    ),
    messaging_service_sid="MG4fea662af68407f0a138ac1ec40c27ed",
    to="+919513838736"
)
        

        # 📲 User message
        client.messages.create(
            body=f"Hello {report['name']}, your report received ✅",
            messaging_service_sid="MG4fea662af68407f0a138ac1ec40c27ed",
            to=phone
        )

        return admin_msg.sid

    except Exception as e:
        raise Exception(f"Twilio Error: {e}")
#-----------------------------------------
#background
#---------------------------------
def set_bg():
    with open("indus.jpeg", "rb") as img:
        encoded = base64.b64encode(img.read()).decode()

    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """, unsafe_allow_html=True)
# ---------------- CSS---------------
st.markdown("""
<style>


/* 🚫 REMOVE ALL TOP SPACE COMPLETELY */
html, body, [class*="css"] {
    margin: 0 !important;
    padding: 0 !important;
}

/* Main container */
.block-container {
    padding-top: 0rem !important;
    margin-top: 0rem !important;
}

/* Remove header space (VERY IMPORTANT) */
header[data-testid="stHeader"] {
    background: transparent !important;
}
/* Fix spacing above first element */
div[data-testid="stVerticalBlock"] > div:first-child {
    margin-top: 0rem !important;
    padding-top: 0rem !important;
}

/* 🏷️ FIX LABEL VISIBILITY (STRONG FIX) */
label {
    color: Black !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    margin-bottom: 6px !important;
}

/* Fix for specific inputs */
.stTextInput label,
.stNumberInput label,
.stSelectbox label,
.stMultiSelect label,
.stTextArea label {
    color: white !important;;
}

/* Improve placeholder visibility */
input::placeholder,
textarea::placeholder {
    color: #888 !important;
}

/* Input box styling */
input, textarea {
    background-color: Black!important;
    color: black !important;
    border-radius: 10px !important;
}

/* Titles spacing fix */
h1, h2, h3 {
    margin-top: 0px !important;
    padding-top: 0px !important;
}


/* Input text color */
input, textarea {
    color: black !important;
    background-color: white!important;
}


 /* ===== Sidebar Text Fix ===== */

/* Sidebar headings (Navigation, etc.) */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] h5,
section[data-testid="stSidebar"] h6,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div {
    color: white !important;
}

/* Radio button labels */
section[data-testid="stSidebar"] .stRadio label {
    color: Black !important;
}

/* Selected radio option */
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    color: white!important;
}

/* Sidebar markdown text */
section[data-testid="stSidebar"] p {
    color:white!important;
} 

/* ===== Titles ===== */
h1, h2, h3, h4, h5, h6 {
    color: Black !important;
}

.main-title {
    color: Black!important;
    text-align: center;
    font-size: 38px;
    font-weight: 700;
    margin-bottom: 20px;
}

.sub-title {
    color: white!important;
    font-size: 18px;
    text-align: center;
}

/* ===== Inputs ===== */
input, textarea {
    border-radius: 10px !important;
    padding: 8px !important;
}

/* ===== Buttons ===== */
.stButton>button {
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    color: white;
    border-radius: 12px;
    padding: 10px 22px;
    border: none;
    font-weight: bold;
    transition: 0.3s;
}

.stButton>button:hover {
    transform: scale(1.05);
}

/* ===== Sidebar ===== */
section[data-testid="stSidebar"] {
    background: rgba(0, 0, 128, 0.4);
    color: white;
}

/* ===== Alerts ===== */
.success-box {
    background: rgba(0, 255, 150, 0.15);
    padding: 15px;
    border-left: 5px solid #00ff95;
    border-radius: 10px;
}

.error-box {
    background: rgba(255, 0, 0, 0.15);
    padding: 15px;
    border-left: 5px solid red;
    border-radius: 10px;
}

/* ===== Tables ===== */
[data-testid="stDataFrame"] {
    background-color: rgba(255,255,255,0.05);
    border-radius: 10px;
}

/* ===== Scrollbar ===== */
::-webkit-scrollbar {
    width: 8px;
}
::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# ---------------- FILES ----------------
USER_FILE = "users.json"
ADMIN_FILE = "admins.json"
REPORTS_FILE = "health_reports.xlsx"

# ---------------- SESSION ----------------
for key in ["user_logged_in", "admin_logged_in", "current_user"]:
    if key not in st.session_state:
        st.session_state[key] = False if "logged" in key else ""

# --- INDUSTRIAL ZONES DATASET ---
data = {
    "name": [
        "Peenya Industrial Area, Bangalore",
        "Electronic City, Bangalore",
        "Okhla Industrial Area, Delhi",
        "MIDC, Pune",
        "GIDC, Ahmedabad",
        "Taloja Industrial Area, Navi Mumbai",
        "SIDCUL, Haridwar",
        "Adityapur Industrial Area, Jamshedpur",
        # Andhra Pradesh high‑risk gas/chemical factories
        "Visakhapatnam Fertilizer & Petrochemical Belt (Coromandel, Andhra Petrochemicals, HPCL Refinery)",
        "Kakinada Fertilizer Complex (Nagarjuna Fertilizers & Chemicals, LNG Terminal)",
        "Srikakulam Bulk Drug & Chemical Cluster"
    ],
    "lat": [
        13.0339, 12.8390, 28.5246, 18.5204, 23.0225, 19.0830, 29.9457, 22.8028,
        17.6868, 16.9891, 18.2960
    ],
    "lon": [
        77.5132, 77.6770, 77.2770, 73.8567, 72.5714, 73.1000, 78.1642, 86.1855,
        83.2185, 82.2475, 83.8960
    ],
    "hazard_radius": [
        3.0, 4.0, 2.5, 5.0, 6.0, 4.5, 3.5, 4.0,
        8.0, 7.0, 6.0
    ]
}
df = pd.DataFrame(data)

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Hazard & Health System",
    layout="wide",
    initial_sidebar_state="expanded"
)
set_bg()
REPORTS_FILE = "health_reports.xlsx"

# ---------------- SESSION ----------------
if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if "user_phone" not in st.session_state:
    st.session_state.user_phone = ""

# ---------------- SAVE/LOAD ----------------
def save_report(report):
    df = pd.DataFrame([report])
    if os.path.exists(REPORTS_FILE):
        old = pd.read_excel(REPORTS_FILE)
        df = pd.concat([old, df], ignore_index=True)
    df.to_excel(REPORTS_FILE, index=False)

def load_reports():
    if os.path.exists(REPORTS_FILE):
        try:
            return pd.read_excel(REPORTS_FILE)
        except:
            return pd.DataFrame()
    return pd.DataFrame()
# ---------------- LOAD/SAVE USERS ----------------
def load_users(file):
    if os.path.exists(file):
        return json.load(open(file))
    return {}

def save_users(file, data):
    json.dump(data, open(file, "w"))


#==================================================
#animation
#===================================================
def loading_animation(msg="Processing..."):
    with st.spinner(msg):
        time.sleep(1.5)

#===================================================
# real time alerts
#===================================================
def realtime_alert():
    placeholder = st.empty()

    for i in range(3):
        df = load_reports()

        if not df.empty and len(df) > 5:
            placeholder.warning("🚨 High number of complaints detected!")

        time.sleep(5)
#============================================================
#page title function
#============================================================
def page_title(text):
    st.markdown(f"""
    <h1 style='color:white; font-size:42px; text-align:center;'>
        {text}
    </h1>
    """, unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
st.sidebar.markdown("## 🏭 Industrial Safety System")
st.sidebar.markdown("---")

if st.session_state.user_logged_in:
    st.sidebar.success(f"👤 {st.session_state.current_user}")
    page = "User Dashboard"

elif st.session_state.admin_logged_in:
    st.sidebar.success("🔐 Admin Logged In")
    page = "Admin Dashboard"

else:
    page = st.sidebar.radio(
        "📌 Navigation",
        ["Hazard Analysis", "Health Reporting", "User Login", "Admin Login"]
    )

    # 👇 Dynamic login/signup in sidebar
    if page == "User Login":
        st.sidebar.markdown("### 👤 User Access")
        user_option = st.sidebar.radio("", ["Login", "Signup"], key="user_option")

    if page == "Admin Login":
        st.sidebar.markdown("### 🔐 Admin Access")
        admin_option = st.sidebar.radio("", ["Login", "Signup"], key="admin_option")
# =========================================================
# 🌍 HAZARD ANALYSIS
# =========================================================
# Map each industrial zone to its type
st.title("INDUSTRIAL HAZARD ANALYSIS")

zone_to_industry = {
    "Peenya Industrial Area, Bangalore": "chemical",
    "Electronic City, Bangalore": "chemical",
    "Okhla Industrial Area, Delhi": "chemical",
    "MIDC, Pune": "chemical",
    "GIDC, Ahmedabad": "chemical",
    "Taloja Industrial Area, Navi Mumbai": "chemical",
    "SIDCUL, Haridwar": "chemical",
    "Adityapur Industrial Area, Jamshedpur": "chemical",
    "Visakhapatnam Fertilizer & Petrochemical Belt (Coromandel, Andhra Petrochemicals, HPCL Refinery)": "fertilizer",
    "Kakinada Fertilizer Complex (Nagarjuna Fertilizers & Chemicals, LNG Terminal)": "fertilizer",
    "Srikakulam Bulk Drug & Chemical Cluster": "bulk_drug",
}
# --- Factory type to relevant symptoms ---
factory_types = {
    "chemical": [
        "Severe Breathing Difficulty (Asthma, COPD)",
        "Chest Pain & Cardiovascular Stress",
        "Chemical Burns / Severe Skin Rash",
        "Neurological Effects (Seizures, Confusion)"
    ],
    "fertilizer": [
        "Chronic Bronchitis",
        "Liver/Kidney Damage (long-term exposure)",
        "Chemical Burns / Severe Skin Rash",
        "Air Quality Deterioration"
    ],
    "bulk_drug": [
        "Neurological Effects (Seizures, Confusion)",
        "Eye Damage / Vision Loss",
        "Extreme Fatigue & Weakness",
        "Cancer Risk (due to carcinogenic chemicals)"
    ]
}
# --- ML MODEL (Dummy Training for Demo) ---
X_train = np.array([[1,0.8],[3,0.5],[7,0.2],[15,0.1]])  # distance, soil toxicity
y_train = ["Critical","High","Moderate","Safe"]
rf_model = RandomForestClassifier()
rf_model.fit(X_train, y_train)

# --- Telugu Voice Output (gTTS) ---
def speak_telugu(text):
    try:
        tts = gTTS(text=text, lang="te")
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        st.audio(audio_bytes, format="audio/mp3")
    except Exception as e:
        st.error(f"Speech synthesis failed: {e}")
# Global style: all text black on white background
def genai_summary(risk_level, dist_km, soil_toxicity, health_reports):
    if risk_level == "Critical":
        advisory = f"ఈ ప్రాంతం {dist_km:.1f} కి.మీ దూరంలో ఉంది. బోరువెల్ త్రవ్వకం ప్రమాదకరం."
    elif risk_level == "High":
        advisory = f"{dist_km:.1f} కి.మీ దూరంలో గాలి మరియు నేల నాణ్యత ప్రభావితం అవుతోంది."
    elif risk_level == "Moderate":
        advisory = f"మధ్యస్థ ప్రమాదం ఉంది. నేల విషపదార్థం స్కోరు {soil_toxicity:.2f}."
    else:
        advisory = "ఈ ప్రాంతం సురక్షితం. తక్షణ పరిశ్రమ ప్రమాదం లేదు."
    if health_reports:
        advisory += f" సమీపంలో {len(health_reports)} ఆరోగ్య సమస్యలు నివేదించబడ్డాయి."
    return advisory

# --- BEEP ALERT ---
def trigger_beep_alert():
    beep_js = """
    <script>
    var context = new (window.AudioContext || window.webkitAudioContext)();
    var oscillator = context.createOscillator();
    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(880, context.currentTime);
    oscillator.connect(context.destination);
    oscillator.start();
    oscillator.stop(context.currentTime + 0.6);
    </script>
    """
    components.html(beep_js, height=0, width=0)
def nearest_factory(u_lat: float, u_lon: float) -> Tuple[pd.Series, float]:
    min_dist = float("inf")
    nearest = None
    for _, row in df.iterrows():
        dist = geodesic((u_lat, u_lon), (row["lat"], row["lon"])).km
        if dist < min_dist:
            min_dist = dist
            nearest = row
    return nearest, min_dist
# --- HAZARD ASSESSMENT ---
def get_risk_assessment(dist_km, factory_type):
    if factory_type == "fertilizer" or factory_type == "petrochemical" or factory_type == "gas":
        if dist_km < 2.5:
            return "Critical", [
                "Explosion hazard",
                "Toxic gas release (Ammonia, Chlorine)",
                "Respiratory diseases (Asthma, COPD)",
                "Skin/eye irritation"
            ], "🔴"
        elif dist_km < 6.0:
            return "High", [
                "Air quality deterioration",
                "Risk of chemical burns",
                "Chronic bronchitis",
                "Cardiovascular stress"
            ], "🟠"
        elif dist_km < 12.0:
            return "Moderate", [
                "Dust and minor emissions",
                "Mild respiratory irritation",
                "Headaches, nausea"
            ], "🟡"
        else:
            return "Safe", ["No immediate industrial hazard"], "🟢"

    elif factory_type == "pharma" or factory_type == "bulk_drug":
        if dist_km < 2.5:
            return "Critical", [
                "Explosion hazard (solvent vapors)",
                "Toxic chemical exposure",
                "Neurological effects",
                "Skin allergies"
            ], "🔴"
        elif dist_km < 6.0:
            return "High", [
                "Air quality deterioration",
                "Chemical storage risks",
                "Respiratory irritation",
                "Liver/kidney stress (long term)"
            ], "🟠"
        elif dist_km < 12.0:
            return "Moderate", [
                "Dust exposure",
                "Minor solvent emissions",
                "Eye irritation"
            ], "🟡"
        else:
            return "Safe", ["No immediate industrial hazard"], "🟢"

    else:
        # Default fallback
        if dist_km < 2.5:
            return "Critical", ["Explosion hazard","Toxic release"], "🔴"
        elif dist_km < 6.0:
            return "High", ["Air quality deterioration"], "🟠"
        elif dist_km < 12.0:
            return "Moderate", ["Minor emissions"], "🟡"
        else:
            return "Safe", ["No immediate industrial hazard"], "🟢"

# --- Excel Storage ---
def save_report_to_excel(new_report):
    df_report = pd.DataFrame([new_report])
    if os.path.exists(REPORTS_FILE):
        existing = pd.read_excel(REPORTS_FILE)
        updated = pd.concat([existing, df_report], ignore_index=True)
        updated.to_excel(REPORTS_FILE, index=False)
    else:
        df_report.to_excel(REPORTS_FILE, index=False)

# --- Twilio SMS Notification ---
if page == "Hazard Analysis":
    col1, col2 = st.columns([2,1])
    with col1:
        search_query = st.text_input("🔎 Search Industrial Zone by Name")
        map_center = [22.9734, 78.6569]
        zoom_level = 5
        if search_query:
            matches = df[df["name"].str.contains(search_query, case=False, na=False)]
            if not matches.empty:
                selected = matches.iloc[0]
                map_center = [selected["lat"], selected["lon"]]
                zoom_level = 12
                st.success(f"Found: {selected['name']}")
            else:
                st.warning("No matching industrial zone found.")

        m = folium.Map(location=map_center, zoom_start=zoom_level)
        for _, row in df.iterrows():
            folium.Marker([row["lat"], row["lon"]],
                popup=row["name"],
                icon=folium.Icon(color='black', icon='industry', prefix='fa')).add_to(m)
            folium.Circle([row["lat"], row["lon"]],
                radius=row["hazard_radius"]*1000,
                color="red", fill=True, opacity=0.2).add_to(m)

        HeatMap(df[["lat","lon"]].values.tolist(), radius=25).add_to(m)
        map_data = st_folium(m, width=800, height=500)
        
            

       # --- PAGE 1: Location Analysis ---
    with col2:
        st.subheader("📍 Location Analysis")

        if map_data and map_data["last_clicked"]:
            u_lat = map_data["last_clicked"]["lat"]
            u_lon = map_data["last_clicked"]["lng"]

            nearest, dist_km = nearest_factory(u_lat, u_lon)
            factory_type = zone_to_industry.get(nearest['name'])

            if factory_type is None:
                st.error("⚠️ Factory type mapping missing!")
                st.stop()

            risk_level, hazards, emoji = get_risk_assessment(dist_km, factory_type)
            features = [[dist_km, 0.5]]
            ml_pred = rf_model.predict(features)[0]

            st.markdown(f"**Nearest Industrial Zone:** {nearest['name']}")
            st.markdown(f"**Distance:** {dist_km:.2f} km")
            st.markdown(f"**Risk Level:** {emoji} {risk_level} (ML says: {ml_pred})")

            st.write("### Potential Hazards:")
            for h in hazards:
                st.markdown(f"- {h}")

            summary = genai_summary(risk_level, dist_km, 0.5, [])
            st.markdown(
    f'<div style="background-color:rgba(255,255,255,0.6); color:black; padding:15px; border-radius:10px; font-weight:bold; border-left:5px solid purple;">🤖 GenAI Advisory: {summary}</div>',
    unsafe_allow_html=True
)

            # 🔴 Alert
            if risk_level in ["Critical", "High"]:
                trigger_beep_alert()
                st.markdown(
    '<div style="background-color:rgba(255,255,255,0.6); color:black; padding:15px; border-radius:10px; font-weight:bold; border-left:5px solid red;">⚠️ Borewell drilling is dangerous at this distance! Please avoid.</div>',
    unsafe_allow_html=True
)
    
            else:
                st.markdown(
    '<div style="background-color:rgba(255,255,255,0.6); color:black; padding:15px; border-radius:10px; font-weight:bold; border-left:5px solid green;">✅ Borewell drilling is considered safe here.</div>',
    unsafe_allow_html=True
)
    

            # 🔊 Voice
            if st.button("🔊 Voice Advisory"):
                speak_telugu(summary)

        else:
            st.markdown(
    '<div style="background-color:rgba(255,255,255,0.6); color:black; padding:12px; border-radius:10px; font-weight:bold; border-left:5px solid blue;">ℹ️ Click on the map to analyze your location.</div>',
    unsafe_allow_html=True
)

# =========================================================
# 🩺 HEALTH REPORTING
# ========================================================
elif page == "Health Reporting":
    
    st.title("🩺 Health Reporting")

    with st.form("report"):
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=1, max_value=120)
        phone = st.text_input("Phone Number")
        industry = st.selectbox("🏭 Select Industrial Zone", list(zone_to_industry.keys()))
        industry_type = zone_to_industry.get(industry)
        symptom_options = factory_types.get(industry_type, [])
        symptoms = st.multiselect("🩺 Select Symptoms", symptom_options)
        address = st.text_area("📍 Address")
        submit = st.form_submit_button("Submit")

    # ✅ MUST BE INSIDE THIS BLOCK
    if submit:

        if not name:
            st.warning("❌ Name required")

        elif not phone:
            st.warning("❌ Phone number required")

        elif not phone.isdigit() or len(phone) != 10:
            st.warning("❌ Enter valid 10-digit phone number")

        elif not symptoms:
            st.warning("❌ Select at least one symptom")

        elif not address:
            st.warning("❌ Address required")

        else:
            report = {
    "user": st.session_state.current_user if st.session_state.user_logged_in else "public",
    "name": st.session_state.current_user if st.session_state.user_logged_in else name,
    "age": age,
    "phone": phone,
    "industry": industry,
    "symptoms": ", ".join(symptoms),
    "address": address,
    "time": datetime.now()
}

            save_report(report)

            try:
                send_sms_notification(report)
                st.markdown(
    '<div style="background-color:rgba(255,255,255,0.6); color:black; padding:12px; border-radius:10px; font-weight:bold; border-left:5px solid green;">✅ Report submitted successfully</div>',
    unsafe_allow_html=True
)
            except Exception as e:
                st.error(f"SMS failed: {e}")
# =========================================================
# 👤 USER LOGIN / SIGNUP
# ====================================================
elif page == "User Login":

    st.markdown('<div class="main-title">👤 User Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    users = load_users(USER_FILE)
    option = st.session_state.get("user_option", "Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if option == "Signup":
        if st.button("Create Account"):
            if username in users:
                st.markdown('<div class="error-box">User already exists</div>', unsafe_allow_html=True)
            else:
                users[username] = password
                save_users(USER_FILE, users)
                st.markdown('<div class="success-box">Account created successfully 🎉</div>', unsafe_allow_html=True)

    else:
        if st.button("Login"):
            if username in users and users[username] == password:
                st.session_state.user_logged_in = True
                st.session_state.current_user = username
                st.markdown('<div class="success-box">Login Successful 🚀</div>', unsafe_allow_html=True)
                
            else:
                st.markdown('<div class="error-box">Invalid credentials!!!</div>',unsafe_allow_html=True)
                
                

# =========================================================
# 🔐 ADMIN LOGIN / SIGNUP
# =========================================================
elif page == "Admin Login":

    st.markdown('<div class="main-title">🔐 Admin Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)

    admins = load_users(ADMIN_FILE)
    option = st.session_state.get("admin_option", "Login")

    username = st.text_input("Admin Username")
    password = st.text_input("Password", type="password")

    if option == "Signup":
        if st.button("Register Admin"):
            if username in admins:
                st.markdown('<div class="error-box">Admin already exists</div>', unsafe_allow_html=True)
            else:
                admins[username] = password
                save_users(ADMIN_FILE, admins)
                st.markdown('<div class="success-box">Admin registered successfully ✅</div>', unsafe_allow_html=True)

    else:
        if st.button("Login"):
            if username in admins and admins[username] == password:
                st.session_state.admin_logged_in = True
                st.markdown('<div class="success-box">Admin Login Successful 🚀</div>', unsafe_allow_html=True)
                
            else:
                st.markdown('<div class="error-box">Invalid credentials</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
   

# =========================================================
# 📄 USER DASHBOARD
# =========================================================
# =========================================================
# 📄 USER DASHBOARD
# =========================================================
elif page == "User Dashboard":

    st.markdown('<div class="main-title">📄 User Dashboard</div>', unsafe_allow_html=True)
    st.write(f"Welcome {st.session_state.current_user}")

    # ➕ Submit New Report
    st.subheader("➕ Submit New Report")

    with st.form("report_form"):
        st.write(f"👤 Logged in as: {st.session_state.current_user}")

        name = st.text_input("Name", value=st.session_state.current_user)
        age = st.number_input("Age", min_value=1, max_value=120)
        phone = st.text_input("Phone Number")

        industry = st.selectbox(
            "🏭 Select Industrial Zone",
            list(zone_to_industry.keys())
        )

        industry_type = zone_to_industry.get(industry)
        symptom_options = factory_types.get(industry_type, [])

        symptoms = st.multiselect("🩺 Select Symptoms", symptom_options)
        address = st.text_area("📍 Address")

        submit = st.form_submit_button("Submit")

    # =====================================================
    # SUBMIT LOGIC
    # =====================================================
    if submit:

        loading_animation("Submitting report...")

        if not phone:
            st.warning("❌ Phone number required")

        elif not phone.isdigit() or len(phone) != 10:
            st.warning("❌ Enter valid 10-digit phone number")

        elif not symptoms:
            st.warning("❌ Select at least one symptom")

        elif not address:
            st.warning("❌ Address required")

        else:
            report = {
                "user": st.session_state.current_user,
                "name": name,
                "age": age,
                "phone": phone,
                "industry": industry,
                "symptoms": ", ".join(symptoms),
                "address": address,
                "time": datetime.now()
            }

            # Save report
            save_report(report)

            st.success("✅ Report submitted successfully")

    # =====================================================
    # SHOW REPORTS (AUTO REFRESH AFTER SUBMIT)
    # =====================================================
    df = load_reports()

    if not df.empty:

        user_df = df[
            (df["user"] == st.session_state.current_user) |
            (df["name"] == st.session_state.current_user)
        ]

        # latest report first
        if "time" in user_df.columns:
            user_df = user_df.sort_values(by="time", ascending=False)

        st.subheader("📋 Your Reports")
        st.dataframe(user_df, use_container_width=True)

    else:
        st.info("No reports submitted yet.")

    # =====================================================
    # SOCIAL MEDIA
    # =====================================================
    st.markdown("---")
    st.subheader("🌐 Connect with Social Media")

    if "show_social" not in st.session_state:
        st.session_state.show_social = False

    if st.button("🔗 Open Social Media"):
        st.session_state.show_social = not st.session_state.show_social

    if st.session_state.show_social:
        st.markdown("""
        <div style="display:flex; gap:20px; justify-content:center; margin-top:15px;">
            <a href="https://www.instagram.com/accounts/login/" target="_blank">
                <button style="padding:10px 20px; border-radius:10px;">📸 Instagram</button>
            </a>

            <a href="https://www.facebook.com/login/" target="_blank">
                <button style="padding:10px 20px; border-radius:10px;">📘 Facebook</button>
            </a>

            <a href="https://twitter.com/login" target="_blank">
                <button style="padding:10px 20px; border-radius:10px;">🐦 Twitter</button>
            </a>
        </div>
        """, unsafe_allow_html=True)

    # =====================================================
    # LOGOUT
    # =====================================================
    if st.button("🚪 Logout", key="user_logout1"):
        st.session_state.user_logged_in = False
        st.session_state.current_user = ""
        st.rerun()
# =========================================================
# 📊 ADMIN DASHBOARD
# =========================================================
elif page == "Admin Dashboard":
    

    st.markdown('<div class="main-title">📊 Admin Dashboard</div>', unsafe_allow_html=True)

    reports_df = load_reports()

    if reports_df.empty:
        st.warning("No data available")
    else:
        st.dataframe(reports_df)

        st.subheader("📈 Complaints by Industry")

        fig = px.bar(
            reports_df,
            x="industry",
            title="📊 Complaints by Industry",
            color="industry",
            text_auto=True
        )

        st.plotly_chart(fig, use_container_width=True)

    realtime_alert()
    # =====================================================
# ADMIN LOGOUT FIX
# =====================================================
    if st.button("🚪 Logout", key="admin_logout"):

       st.session_state.admin_logged_in = False
       st.session_state.current_user = ""

       st.rerun()


