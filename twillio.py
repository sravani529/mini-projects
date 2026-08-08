from twilio.rest import Client
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

client = Client(account_sid, auth_token)

def send_sms(message_body):
    message = client.messages.create(
        body=message_body,
        messaging_service_sid="MG4fea662af68407f0a138ac1ec40c27ed",  # ✅ Your Messaging Service SID
        to="+919513838736"  # ✅ Your verified mobile number
    )

    print("Message SID:", message.sid)
    print("Message Status:", message.status)  # helpful for debugging
    return message.sid
