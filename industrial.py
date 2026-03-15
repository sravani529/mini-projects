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
from twilio.rest import Client
import firebase_admin 
from firebase_admin import credentials, messaging

# --- CONFIGURATION ---
st.set_page_config(page_title="AI-Powered Hazard & Health Dashboard", layout="wide")

# --- PAGE NAVIGATION ---
page = st.sidebar.radio("📑 Select Page", ["Hazard Analysis", "Health Reporting"])

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
        "Adityapur Industrial Area, Jamshedpur"
    ],
    "lat": [13.0339, 12.8390, 28.5246, 18.5204, 23.0225, 19.0830, 29.9457, 22.8028],
    "lon": [77.5132, 77.6770, 77.2770, 73.8567, 72.5714, 73.1000, 78.1642, 86.1855],
    "hazard_radius": [3.0, 4.0, 2.5, 5.0, 6.0, 4.5, 3.5, 4.0]
}
df = pd.DataFrame(data)

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

# --- GENAI SIMULATION FUNCTION ---
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

# --- HAZARD ASSESSMENT ---
def get_risk_assessment(dist_km):
    if dist_km < 2.5:
        return "Critical", ["Explosion hazard","Toxic gas release","Heavy metal contamination"], "🔴"
    elif dist_km < 6.0:
        return "High", ["Air quality deterioration","Noise pollution","Chemical storage risks"], "🟠"
    elif dist_km < 12.0:
        return "Moderate", ["Dust exposure","Minor emissions"], "🟡"
    else:
        return "Safe", ["No immediate industrial hazard"], "🟢"

def nearest_factory(u_lat, u_lon):
    min_dist = float("inf")
    nearest = None
    for _, row in df.iterrows():
        dist = geodesic((u_lat, u_lon), (row["lat"], row["lon"])).km
        if dist < min_dist:
            min_dist = dist
            nearest = row
    return nearest, min_dist

# --- Excel Storage ---
REPORTS_FILE = "health_reports.xlsx"

def save_report_to_excel(new_report):
    df_report = pd.DataFrame([new_report])
    if os.path.exists(REPORTS_FILE):
        existing = pd.read_excel(REPORTS_FILE)
        updated = pd.concat([existing, df_report], ignore_index=True)
        updated.to_excel(REPORTS_FILE, index=False)
    else:
        df_report.to_excel(REPORTS_FILE, index=False)

# --- Twilio SMS Notification ---
def send_sms_notification(report):
# Load environment variables from .env file
    load_dotenv()
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    client = Client(account_sid, auth_token)

    message_body = (
        f"🚨 New Health Report 🚨\n"
        f"Name: {report['name']}\n"
        f"Age: {report['age']}\n"
        f"State: {report['state']}\n"
        f"Symptoms: {', '.join(report['symptoms'])}\n"
        f"Address: {report['address']}"
    )

    message = client.messages.create(
        body=message_body,
        from_="+12526595639",     # your Twilio trial number
        to="+919513838736"        # your verified mobile number
    )
    return message.sid

# --- PAGE 1: Hazard Analysis ---
if page == "Hazard Analysis":
    st.title("Hazard Analysis")
    col1, col2 = st.columns([2, 1])

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

    with col2:
        st.subheader("📍 Location Analysis")
        if map_data and map_data["last_clicked"]:
            u_lat = map_data["last_clicked"]["lat"]
            u_lon = map_data["last_clicked"]["lng"]
            nearest, dist_km = nearest_factory(u_lat, u_lon)
            risk_level, hazards, emoji = get_risk_assessment(dist_km)

            features = [[dist_km, 0.5]]
            ml_pred = rf_model.predict(features)[0]

            st.markdown(f"**Nearest Industrial Zone:** {nearest['name']}")
            st.markdown(f"**Distance:** {dist_km:.2f} km")
            st.markdown(f"**Risk Level:** {emoji} {risk_level} (ML says: {ml_pred})")

            st.write("### Potential Hazards:")
            for h in hazards:
                st.markdown(f"- {h}")

            health_reports = st.session_state.get("health_reports", [])
            summary = genai_summary(risk_level, dist_km, 0.5, health_reports)

            # Text advisory always shown
            st.info(f"🤖 GenAI Advisory (Text): {summary}")

                     # Alert sound for borewell danger
            if risk_level in ["Critical", "High"]:
                trigger_beep_alert()
                st.error("⚠️ Borewell drilling is dangerous at this distance! Please avoid.")
            else:
                st.success("✅ Borewell drilling is considered safe here.")

            # Voice advisory button (gTTS)
            if st.button("🔊 Voice Advisory"):
                speak_telugu(summary)

        else:
            st.info("Click on the map to analyze your location.")
# --- PAGE 2: Health Reporting ---
elif page == "Health Reporting":
    st.title("🩺 Health Reporting System")

    states_list = [
        "Andhra Pradesh", "Telangana", "Karnataka", "Tamil Nadu", "Kerala",
        "Maharashtra", "Delhi", "Uttar Pradesh", "West Bengal", "Gujarat",
        "Rajasthan", "Punjab", "Haryana", "Madhya Pradesh", "Odisha"
    ]

    symptoms_list = [
        "Cough", "Fever", "Stomach Pain", "Headache", "Skin Rash",
        "Breathing Difficulty", "Fatigue", "Diarrhea", "Chest Pain"
    ]

    with st.form("health_report_form"):
        name = st.text_input("Name")
        age = st.slider("Age", min_value=1, max_value=120, value=25)
        phone = st.text_input("Phone Number")
        state = st.selectbox("Select State", states_list)
        symptoms = st.multiselect("Select Symptoms", symptoms_list)
        address = st.text_area("Address")
        submitted = st.form_submit_button("Submit Report")

    if submitted:
        new_report = {
            "name": name,
            "age": age,
            "phone": phone,
            "state": state,
            "symptoms": symptoms,
            "address": address
        }
        st.success("✅ Health report submitted successfully!")
        st.json(new_report)  # Display submitted data for confirmation

        # Save to Excel
        save_report_to_excel(new_report)

        # Send SMS notification
        try:
            sid = send_sms_notification(new_report)
            st.success(f"📲 SMS notification sent to Health Secretary (SID: {sid})")
        except Exception as e:
            st.error(f"Failed to send SMS: {e}")
# Initialize Firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

# --- Add your push notification function here ---
def send_push_notification(token, report):
    # token = FCM device token captured from browser/app
    message = messaging.Message(
        notification=messaging.Notification(
            title="🚨 New Health Report",
            body=f"{report['name']} ({report['age']} yrs) - {', '.join(report['symptoms'])}"
        ),
        token=token,
    )
    response = messaging.send(message)
    return response


