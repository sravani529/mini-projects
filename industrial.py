import streamlit as st
import folium
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
import json
import base64
from datetime import datetime
import time
import plotly.express as px

import os
from dotenv import load_dotenv

load_dotenv(override=True)
st.write("Twilio SID loaded:", bool(os.getenv("TWILIO_ACCOUNT_SID")))
st.write("Twilio Token loaded:", bool(os.getenv("TWILIO_AUTH_TOKEN")))
st.write("Messaging SID loaded:", bool(os.getenv("TWILIO_MESSAGING_SERVICE_SID")))
sid = os.getenv("TWILIO_ACCOUNT_SID")
token = os.getenv("TWILIO_AUTH_TOKEN")
messaging_sid = os.getenv("TWILIO_MESSAGING_SERVICE_SID")

if not sid or not token or not messaging_sid:
    raise Exception("Twilio credentials missing. Check your .env file.")
# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Hazard & Health System",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# FILES
# =========================================================

USER_FILE = "users.json"
ADMIN_FILE = "admins.json"
REPORTS_FILE = "health_reports.xlsx"
BACKGROUND_IMAGE = "indus.jpeg"


# =========================================================
# SESSION STATE
# =========================================================

if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = ""

if "user_phone" not in st.session_state:
    st.session_state.user_phone = ""

if "show_social" not in st.session_state:
    st.session_state.show_social = False


# =========================================================
# BACKGROUND
# =========================================================

def set_bg():
    if os.path.exists(BACKGROUND_IMAGE):
        with open(BACKGROUND_IMAGE, "rb") as img:
            encoded = base64.b64encode(img.read()).decode()

        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpeg;base64,{encoded}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}

            .block-container {{
                padding-top: 2rem;
            }}

            .main-title {{
                font-size: 40px;
                font-weight: bold;
                color: black;
                text-align: center;
                margin-bottom: 20px;
            }}

            .card {{
                background-color: rgba(255,255,255,0.88);
                padding: 25px;
                border-radius: 15px;
                margin-bottom: 20px;
            }}

            .success-box {{
                background-color: rgba(220,255,220,0.95);
                color: black;
                padding: 12px;
                border-radius: 10px;
                font-weight: bold;
                margin: 10px 0;
            }}

            .error-box {{
                background-color: rgba(255,220,220,0.95);
                color: black;
                padding: 12px;
                border-radius: 10px;
                font-weight: bold;
                margin: 10px 0;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning(
            f"Background image '{BACKGROUND_IMAGE}' was not found. "
            "The application will continue without the background."
        )


set_bg()


# =========================================================
# INDUSTRIAL ZONES
# =========================================================

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
        "Visakhapatnam Fertilizer & Petrochemical Belt (Coromandel, Andhra Petrochemicals, HPCL Refinery)",
        "Kakinada Fertilizer Complex (Nagarjuna Fertilizers & Chemicals, LNG Terminal)",
        "Srikakulam Bulk Drug & Chemical Cluster"
    ],

    "lat": [
        13.0339,
        12.8390,
        28.5246,
        18.5204,
        23.0225,
        19.0830,
        29.9457,
        22.8028,
        17.6868,
        16.9891,
        18.2960
    ],

    "lon": [
        77.5132,
        77.6770,
        77.2770,
        73.8567,
        72.5714,
        73.1000,
        78.1642,
        86.1855,
        83.2185,
        82.2475,
        83.8960
    ],

    "hazard_radius": [
        3.0,
        4.0,
        2.5,
        5.0,
        6.0,
        4.5,
        3.5,
        4.0,
        8.0,
        7.0,
        6.0
    ]
}

industrial_df = pd.DataFrame(data)


# =========================================================
# INDUSTRY TYPE
# =========================================================

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

    "Srikakulam Bulk Drug & Chemical Cluster": "bulk_drug"
}


# =========================================================
# FACTORY SYMPTOMS
# =========================================================

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


# =========================================================
# USER / ADMIN FILE FUNCTIONS
# =========================================================

def load_users(file):

    if os.path.exists(file):

        try:
            with open(file, "r") as f:
                return json.load(f)

        except Exception:
            return {}

    return {}


def save_users(file, data):

    with open(file, "w") as f:
        json.dump(data, f, indent=4)


# =========================================================
# REPORT FUNCTIONS
# =========================================================

def save_report(report):

    new_df = pd.DataFrame([report])

    if os.path.exists(REPORTS_FILE):

        try:
            old_df = pd.read_excel(REPORTS_FILE)
            new_df = pd.concat(
                [old_df, new_df],
                ignore_index=True
            )

        except Exception:
            pass

    new_df.to_excel(
        REPORTS_FILE,
        index=False
    )


def load_reports():

    if os.path.exists(REPORTS_FILE):

        try:
            return pd.read_excel(REPORTS_FILE)

        except Exception:
            return pd.DataFrame()

    return pd.DataFrame()


# =========================================================
# LOADING ANIMATION
# =========================================================

def loading_animation(message="Processing..."):

    with st.spinner(message):
        time.sleep(1)


# =========================================================
# TWILIO SMS
# =========================================================
def send_sms_notification(report):

    if not sid:
        raise Exception("TWILIO_ACCOUNT_SID missing from .env")

    if not token:
        raise Exception("TWILIO_AUTH_TOKEN missing from .env")

    if not messaging_sid:
        raise Exception("TWILIO_MESSAGING_SERVICE_SID missing from .env")

    client = Client(
        sid,
        token
    )

    phone = report["phone"]

    if not phone.startswith("+"):
        phone = "+91" + phone

    try:
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
            messaging_service_sid=messaging_sid,
            to="+919513838736"
        )

        client.messages.create(
            body=f"Hello {report['name']}, your health report was received ✅",
            messaging_service_sid=messaging_sid,
            to=phone
        )

        return admin_msg.sid

    except Exception as e:
        raise Exception(f"Twilio Error: {e}")

# =========================================================
# ML MODEL
# =========================================================

X_train = np.array([
    [1, 0.8],
    [3, 0.5],
    [7, 0.2],
    [15, 0.1]
])

y_train = [
    "Critical",
    "High",
    "Moderate",
    "Safe"
]

rf_model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

rf_model.fit(
    X_train,
    y_train
)


# =========================================================
# TELUGU VOICE
# =========================================================

def speak_telugu(text):

    try:

        tts = gTTS(
            text=text,
            lang="te"
        )

        audio_bytes = io.BytesIO()

        tts.write_to_fp(
            audio_bytes
        )

        audio_bytes.seek(0)

        st.audio(
            audio_bytes,
            format="audio/mp3"
        )

    except Exception as e:

        st.error(
            f"Speech synthesis failed: {e}"
        )


# =========================================================
# BEEP ALERT
# =========================================================

def trigger_beep_alert():

    beep_js = """
    <script>
    var context = new (
        window.AudioContext ||
        window.webkitAudioContext
    )();

    var oscillator = context.createOscillator();

    oscillator.type = 'sine';

    oscillator.frequency.setValueAtTime(
        880,
        context.currentTime
    );

    oscillator.connect(
        context.destination
    );

    oscillator.start();

    oscillator.stop(
        context.currentTime + 0.6
    );
    </script>
    """

    components.html(
        beep_js,
        height=0,
        width=0
    )


# =========================================================
# NEAREST FACTORY
# =========================================================

def nearest_factory(
    user_lat: float,
    user_lon: float
):

    min_distance = float("inf")

    nearest = None

    for _, row in industrial_df.iterrows():

        distance = geodesic(
            (user_lat, user_lon),
            (row["lat"], row["lon"])
        ).km

        if distance < min_distance:

            min_distance = distance
            nearest = row

    return nearest, min_distance


# =========================================================
# RISK ASSESSMENT
# =========================================================

def get_risk_assessment(
    distance_km,
    factory_type
):

    if factory_type in [
        "fertilizer",
        "petrochemical",
        "gas"
    ]:

        if distance_km < 2.5:

            return (
                "Critical",
                [
                    "Explosion hazard",
                    "Toxic gas release",
                    "Respiratory health risks",
                    "Skin and eye irritation"
                ],
                "🔴"
            )

        elif distance_km < 6:

            return (
                "High",
                [
                    "Air quality deterioration",
                    "Risk of chemical exposure",
                    "Chronic respiratory problems",
                    "Cardiovascular stress"
                ],
                "🟠"
            )

        elif distance_km < 12:

            return (
                "Moderate",
                [
                    "Dust and minor emissions",
                    "Mild respiratory irritation",
                    "Headaches or nausea"
                ],
                "🟡"
            )

        else:

            return (
                "Safe",
                [
                    "No immediate industrial hazard detected"
                ],
                "🟢"
            )

    elif factory_type in [
        "pharma",
        "bulk_drug"
    ]:

        if distance_km < 2.5:

            return (
                "Critical",
                [
                    "Explosion hazard",
                    "Toxic chemical exposure",
                    "Neurological effects",
                    "Skin allergies"
                ],
                "🔴"
            )

        elif distance_km < 6:

            return (
                "High",
                [
                    "Air quality deterioration",
                    "Chemical storage risks",
                    "Respiratory irritation",
                    "Long-term exposure concerns"
                ],
                "🟠"
            )

        elif distance_km < 12:

            return (
                "Moderate",
                [
                    "Dust exposure",
                    "Minor chemical emissions",
                    "Eye irritation"
                ],
                "🟡"
            )

        else:

            return (
                "Safe",
                [
                    "No immediate industrial hazard detected"
                ],
                "🟢"
            )

    else:

        if distance_km < 2.5:

            return (
                "Critical",
                [
                    "Explosion hazard",
                    "Toxic release"
                ],
                "🔴"
            )

        elif distance_km < 6:

            return (
                "High",
                [
                    "Air quality deterioration"
                ],
                "🟠"
            )

        elif distance_km < 12:

            return (
                "Moderate",
                [
                    "Minor emissions"
                ],
                "🟡"
            )

        else:

            return (
                "Safe",
                [
                    "No immediate industrial hazard"
                ],
                "🟢"
            )


# =========================================================
# GENAI-STYLE ADVISORY
# =========================================================

def genai_summary(
    risk_level,
    distance_km,
    soil_toxicity,
    health_reports
):

    if risk_level == "Critical":

        advisory = (
            f"ఈ ప్రాంతం {distance_km:.1f} కి.మీ "
            "దూరంలో ఉంది. బోరువెల్ త్రవ్వకం "
            "ప్రమాదకరం."
        )

    elif risk_level == "High":

        advisory = (
            f"{distance_km:.1f} కి.మీ దూరంలో "
            "గాలి మరియు నేల నాణ్యత ప్రభావితం "
            "అయ్యే అవకాశం ఉంది."
        )

    elif risk_level == "Moderate":

        advisory = (
            f"మధ్యస్థ ప్రమాదం ఉంది. "
            f"నేల విషపదార్థం స్కోరు "
            f"{soil_toxicity:.2f}."
        )

    else:

        advisory = (
            "ఈ ప్రాంతంలో తక్షణ పరిశ్రమ "
            "ప్రమాదం గుర్తించబడలేదు."
        )

    if health_reports:

        advisory += (
            f" సమీపంలో {len(health_reports)} "
            "ఆరోగ్య సమస్యలు నివేదించబడ్డాయి."
        )

    return advisory


# =========================================================
# REAL TIME ALERT
# =========================================================

def realtime_alert():

    reports_df = load_reports()

    if not reports_df.empty and len(reports_df) > 5:

        st.warning(
            "🚨 High number of complaints detected!"
        )


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown(
    "## 🏭 Industrial Safety System"
)

st.sidebar.markdown("---")


if st.session_state.user_logged_in:

    st.sidebar.success(
        f"👤 {st.session_state.current_user}"
    )

    page = "User Dashboard"

elif st.session_state.admin_logged_in:

    st.sidebar.success(
        "🔐 Admin Logged In"
    )

    page = "Admin Dashboard"

else:

    page = st.sidebar.radio(
        "📌 Navigation",
        [
            "Hazard Analysis",
            "Health Reporting",
            "User Login",
            "Admin Login"
        ]
    )


# =========================================================
# USER LOGIN OPTIONS
# =========================================================

if page == "User Login":

    user_option = st.sidebar.radio(
        "👤 User Access",
        [
            "Login",
            "Signup"
        ],
        key="user_option"
    )


# =========================================================
# ADMIN LOGIN OPTIONS
# =========================================================

if page == "Admin Login":

    admin_option = st.sidebar.radio(
        "🔐 Admin Access",
        [
            "Login",
            "Signup"
        ],
        key="admin_option"
    )


# =========================================================
# HAZARD ANALYSIS
# =========================================================

if page == "Hazard Analysis":

    st.markdown(
        '<div class="main-title">'
        '🌍 INDUSTRIAL HAZARD ANALYSIS'
        '</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(
        [2, 1]
    )

    with col1:

        search_query = st.text_input(
            "🔎 Search Industrial Zone by Name"
        )

        map_center = [
            22.9734,
            78.6569
        ]

        zoom_level = 5

        if search_query:

            matches = industrial_df[
                industrial_df["name"].str.contains(
                    search_query,
                    case=False,
                    na=False
                )
            ]

            if not matches.empty:

                selected = matches.iloc[0]

                map_center = [
                    selected["lat"],
                    selected["lon"]
                ]

                zoom_level = 12

                st.success(
                    f"Found: {selected['name']}"
                )

            else:

                st.warning(
                    "No matching industrial zone found."
                )

        # ---------------- MAP ----------------

        m = folium.Map(
            location=map_center,
            zoom_start=zoom_level
        )

        for _, row in industrial_df.iterrows():

            folium.Marker(
                [
                    row["lat"],
                    row["lon"]
                ],
                popup=row["name"],
                tooltip=row["name"],
                icon=folium.Icon(
                    color="black",
                    icon="industry",
                    prefix="fa"
                )
            ).add_to(m)

            folium.Circle(
                [
                    row["lat"],
                    row["lon"]
                ],
                radius=row["hazard_radius"] * 1000,
                color="red",
                fill=True,
                fill_opacity=0.15
            ).add_to(m)

        HeatMap(
            industrial_df[
                ["lat", "lon"]
            ].values.tolist(),
            radius=25
        ).add_to(m)

        map_data = st_folium(
            m,
            width=800,
            height=550
        )

    # =====================================================
    # LOCATION ANALYSIS
    # =====================================================

    with col2:

        st.subheader(
            "📍 Location Analysis"
        )

        if (
            map_data
            and map_data.get("last_clicked")
        ):

            user_lat = map_data[
                "last_clicked"
            ]["lat"]

            user_lon = map_data[
                "last_clicked"
            ]["lng"]

            nearest, distance_km = nearest_factory(
                user_lat,
                user_lon
            )

            if nearest is None:

                st.error(
                    "Unable to find nearest industrial zone."
                )

                st.stop()

            factory_type = zone_to_industry.get(
                nearest["name"]
            )

            if factory_type is None:

                st.error(
                    "Factory type mapping missing!"
                )

                st.stop()

            risk_level, hazards, emoji = (
                get_risk_assessment(
                    distance_km,
                    factory_type
                )
            )

            # ML prediction

            features = [
                [
                    distance_km,
                    0.5
                ]
            ]

            ml_prediction = rf_model.predict(
                features
            )[0]

            st.markdown(
                f"**Nearest Industrial Zone:** "
                f"{nearest['name']}"
            )

            st.markdown(
                f"**Distance:** "
                f"{distance_km:.2f} km"
            )

            st.markdown(
                f"**Risk Level:** "
                f"{emoji} {risk_level}"
            )

            st.markdown(
                f"**ML Prediction:** "
                f"{ml_prediction}"
            )

            st.write(
                "### ⚠️ Potential Hazards"
            )

            for hazard in hazards:

                st.markdown(
                    f"- {hazard}"
                )

            summary = genai_summary(
                risk_level,
                distance_km,
                0.5,
                []
            )

            st.markdown(
                f"""
                <div style="
                    background-color:rgba(255,255,255,0.85);
                    color:black;
                    padding:15px;
                    border-radius:10px;
                    font-weight:bold;
                    border-left:5px solid purple;
                ">
                🤖 GenAI Advisory:<br>
                {summary}
                </div>
                """,
                unsafe_allow_html=True
            )

            # ---------------- ALERT ----------------

            if risk_level in [
                "Critical",
                "High"
            ]:

                trigger_beep_alert()

                st.markdown(
                    """
                    <div style="
                        background-color:rgba(255,255,255,0.9);
                        color:black;
                        padding:15px;
                        border-radius:10px;
                        font-weight:bold;
                        border-left:5px solid red;
                    ">
                    ⚠️ Borewell drilling may be
                    dangerous at this distance.
                    Please avoid drilling without
                    appropriate environmental assessment.
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            else:

                st.markdown(
                    """
                    <div style="
                        background-color:rgba(255,255,255,0.9);
                        color:black;
                        padding:15px;
                        border-radius:10px;
                        font-weight:bold;
                        border-left:5px solid green;
                    ">
                    ✅ No immediate industrial hazard
                    was detected based on this
                    demo assessment.
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # ---------------- VOICE ----------------

            if st.button(
                "🔊 Voice Advisory",
                key="voice_advisory"
            ):

                speak_telugu(summary)

        else:

            st.markdown(
                """
                <div style="
                    background-color:rgba(255,255,255,0.9);
                    color:black;
                    padding:12px;
                    border-radius:10px;
                    font-weight:bold;
                    border-left:5px solid blue;
                ">
                ℹ️ Click on the map to analyze
                your location.
                </div>
                """,
                unsafe_allow_html=True
            )


# =========================================================
# HEALTH REPORTING
# =========================================================

elif page == "Health Reporting":

    st.markdown(
        '<div class="main-title">'
        '🩺 HEALTH REPORTING'
        '</div>',
        unsafe_allow_html=True
    )

    with st.form("public_health_report"):

        name = st.text_input(
            "Name"
        )

        age = st.number_input(
            "Age",
            min_value=1,
            max_value=120,
            value=18
        )

        phone = st.text_input(
            "Phone Number"
        )

        industry = st.selectbox(
            "🏭 Select Industrial Zone",
            list(zone_to_industry.keys())
        )

        industry_type = zone_to_industry.get(
            industry
        )

        symptom_options = factory_types.get(
            industry_type,
            []
        )

        symptoms = st.multiselect(
            "🩺 Select Symptoms",
            symptom_options
        )

        address = st.text_area(
            "📍 Address"
        )

        submit = st.form_submit_button(
            "Submit Report"
        )

    if submit:

        if not name.strip():

            st.warning(
                "❌ Name required"
            )

        elif not phone.strip():

            st.warning(
                "❌ Phone number required"
            )

        elif (
            not phone.isdigit()
            or len(phone) != 10
        ):

            st.warning(
                "❌ Enter valid 10-digit phone number"
            )

        elif not symptoms:

            st.warning(
                "❌ Select at least one symptom"
            )

        elif not address.strip():

            st.warning(
                "❌ Address required"
            )

        else:

            loading_animation(
                "Submitting report..."
            )

            report = {
                "user": (
                    st.session_state.current_user
                    if st.session_state.user_logged_in
                    else "public"
                ),

                "name": (
                    st.session_state.current_user
                    if st.session_state.user_logged_in
                    else name
                ),

                "age": age,

                "phone": phone,

                "industry": industry,

                "symptoms": ", ".join(
                    symptoms
                ),

                "address": address,

                "time": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            }

            save_report(report)

            try:

                send_sms_notification(
                    report
                )

                st.success(
                    "✅ Report submitted successfully "
                    "and SMS notifications sent."
                )

            except Exception as e:

                st.warning(
                    "✅ Report saved successfully, "
                    "but SMS could not be sent."
                )

                st.error(
                    str(e)
                )


# =========================================================
# USER LOGIN
# =========================================================

elif page == "User Login":

    st.markdown(
        '<div class="main-title">'
        '👤 USER PORTAL'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True
    )

    users = load_users(
        USER_FILE
    )

    option = st.session_state.get(
        "user_option",
        "Login"
    )

    username = st.text_input(
        "Username",
        key="user_username"
    )

    password = st.text_input(
        "Password",
        type="password",
        key="user_password"
    )

    if option == "Signup":

        if st.button(
            "Create Account",
            key="create_user"
        ):

            if not username.strip():

                st.error(
                    "Username required."
                )

            elif not password:

                st.error(
                    "Password required."
                )

            elif username in users:

                st.error(
                    "User already exists."
                )

            else:

                users[username] = password

                save_users(
                    USER_FILE,
                    users
                )

                st.success(
                    "Account created successfully 🎉"
                )

    else:

        if st.button(
            "Login",
            key="user_login"
        ):

            if (
                username in users
                and users[username] == password
            ):

                st.session_state.user_logged_in = True

                st.session_state.current_user = (
                    username
                )

                st.success(
                    "Login Successful 🚀"
                )

                st.rerun()

            else:

                st.error(
                    "Invalid username or password."
                )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

elif page == "Admin Login":

    st.markdown(
        '<div class="main-title">'
        '🔐 ADMIN PORTAL'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True
    )

    admins = load_users(
        ADMIN_FILE
    )

    option = st.session_state.get(
        "admin_option",
        "Login"
    )

    username = st.text_input(
        "Admin Username",
        key="admin_username"
    )

    password = st.text_input(
        "Password",
        type="password",
        key="admin_password"
    )

    if option == "Signup":

        if st.button(
            "Register Admin",
            key="register_admin"
        ):

            if not username.strip():

                st.error(
                    "Admin username required."
                )

            elif not password:

                st.error(
                    "Password required."
                )

            elif username in admins:

                st.error(
                    "Admin already exists."
                )

            else:

                admins[username] = password

                save_users(
                    ADMIN_FILE,
                    admins
                )

                st.success(
                    "Admin registered successfully ✅"
                )

    else:

        if st.button(
            "Login",
            key="admin_login"
        ):

            if (
                username in admins
                and admins[username] == password
            ):

                st.session_state.admin_logged_in = True

                st.success(
                    "Admin Login Successful 🚀"
                )

                st.rerun()

            else:

                st.error(
                    "Invalid admin credentials."
                )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =========================================================
# USER DASHBOARD
# =========================================================

elif page == "User Dashboard":

    st.markdown(
        '<div class="main-title">'
        '📄 USER DASHBOARD'
        '</div>',
        unsafe_allow_html=True
    )

    st.write(
        f"Welcome, "
        f"**{st.session_state.current_user}** 👋"
    )

    st.subheader(
        "➕ Submit New Health Report"
    )

    with st.form("user_report_form"):

        st.write(
            f"👤 Logged in as: "
            f"**{st.session_state.current_user}**"
        )

        name = st.text_input(
            "Name",
            value=st.session_state.current_user
        )

        age = st.number_input(
            "Age",
            min_value=1,
            max_value=120,
            value=18
        )

        phone = st.text_input(
            "Phone Number"
        )

        industry = st.selectbox(
            "🏭 Select Industrial Zone",
            list(zone_to_industry.keys())
        )

        industry_type = zone_to_industry.get(
            industry
        )

        symptom_options = factory_types.get(
            industry_type,
            []
        )

        symptoms = st.multiselect(
            "🩺 Select Symptoms",
            symptom_options
        )

        address = st.text_area(
            "📍 Address"
        )

        submit = st.form_submit_button(
            "Submit Report"
        )

    if submit:

        loading_animation(
            "Submitting report..."
        )

        if not phone:

            st.warning(
                "❌ Phone number required"
            )

        elif (
            not phone.isdigit()
            or len(phone) != 10
        ):

            st.warning(
                "❌ Enter valid 10-digit phone number"
            )

        elif not symptoms:

            st.warning(
                "❌ Select at least one symptom"
            )

        elif not address:

            st.warning(
                "❌ Address required"
            )

        else:

            report = {
                "user": st.session_state.current_user,
                "name": name,
                "age": age,
                "phone": phone,
                "industry": industry,
                "symptoms": ", ".join(symptoms),
                "address": address,
                "time": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            }

            save_report(report)

            st.success(
                "✅ Report submitted successfully"
            )

    # =====================================================
    # USER REPORTS
    # =====================================================

    reports_df = load_reports()

    if not reports_df.empty:

        if "user" in reports_df.columns:

            user_df = reports_df[
                reports_df["user"]
                == st.session_state.current_user
            ]

        else:

            user_df = pd.DataFrame()

        if not user_df.empty:

            if "time" in user_df.columns:

                user_df = user_df.sort_values(
                    by="time",
                    ascending=False
                )

            st.subheader(
                "📋 Your Reports"
            )

            st.dataframe(
                user_df,
                use_container_width=True
            )

        else:

            st.info(
                "You have not submitted any reports yet."
            )

    else:

        st.info(
            "No reports submitted yet."
        )

    # =====================================================
    # SOCIAL MEDIA
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🌐 Connect with Social Media"
    )

    if st.button(
        "🔗 Open Social Media",
        key="social_button"
    ):

        st.session_state.show_social = (
            not st.session_state.show_social
        )

    if st.session_state.show_social:

        st.markdown(
            """
            <div style="
                display:flex;
                gap:20px;
                justify-content:center;
                margin-top:15px;
            ">

            <a href="https://www.instagram.com/"
               target="_blank">
                <button style="
                    padding:10px 20px;
                    border-radius:10px;
                ">
                📸 Instagram
                </button>
            </a>

            <a href="https://www.facebook.com/"
               target="_blank">
                <button style="
                    padding:10px 20px;
                    border-radius:10px;
                ">
                📘 Facebook
                </button>
            </a>

            <a href="https://twitter.com/"
               target="_blank">
                <button style="
                    padding:10px 20px;
                    border-radius:10px;
                ">
                🐦 Twitter
                </button>
            </a>

            </div>
            """,
            unsafe_allow_html=True
        )

    # =====================================================
    # USER LOGOUT
    # =====================================================

    if st.button(
        "🚪 Logout",
        key="user_logout"
    ):

        st.session_state.user_logged_in = False
        st.session_state.current_user = ""

        st.rerun()


# =========================================================
# ADMIN DASHBOARD
# =========================================================

elif page == "Admin Dashboard":

    st.markdown(
        '<div class="main-title">'
        '📊 ADMIN DASHBOARD'
        '</div>',
        unsafe_allow_html=True
    )

    reports_df = load_reports()

    # =====================================================
    # SUMMARY METRICS
    # =====================================================

    if reports_df.empty:

        st.warning(
            "No health reports available."
        )

    else:

        total_reports = len(
            reports_df
        )

        unique_users = (
            reports_df["user"].nunique()
            if "user" in reports_df.columns
            else 0
        )

        unique_industries = (
            reports_df["industry"].nunique()
            if "industry" in reports_df.columns
            else 0
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "📋 Total Reports",
            total_reports
        )

        col2.metric(
            "👥 Users",
            unique_users
        )

        col3.metric(
            "🏭 Industries",
            unique_industries
        )

        # =================================================
        # REPORT TABLE
        # =================================================

        st.subheader(
            "📋 All Health Reports"
        )

        st.dataframe(
            reports_df,
            use_container_width=True
        )

        # =================================================
        # INDUSTRY CHART
        # =================================================

        if "industry" in reports_df.columns:

            st.subheader(
                "📈 Complaints by Industry"
            )

            fig = px.bar(
                reports_df,
                x="industry",
                title="📊 Complaints by Industry",
                color="industry",
                text_auto=True
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # =================================================
        # SYMPTOM CHART
        # =================================================

        if "symptoms" in reports_df.columns:

            symptom_counts = (
                reports_df["symptoms"]
                .fillna("")
                .str.split(", ")
                .explode()
                .value_counts()
                .reset_index()
            )

            symptom_counts.columns = [
                "Symptom",
                "Count"
            ]

            st.subheader(
                "🩺 Reported Symptoms"
            )

            if not symptom_counts.empty:

                fig2 = px.bar(
                    symptom_counts,
                    x="Symptom",
                    y="Count",
                    title="🩺 Most Reported Symptoms",
                    text_auto=True
                )

                st.plotly_chart(
                    fig2,
                    use_container_width=True
                )

        # =================================================
        # REAL-TIME ALERT
        # =================================================

        realtime_alert()

    # =====================================================
    # ADMIN LOGOUT
    # =====================================================

    st.markdown("---")

    if st.button(
        "🚪 Logout",
        key="admin_logout"
    ):

        st.session_state.admin_logged_in = False
        st.session_state.current_user = ""

        st.rerun()