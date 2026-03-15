from twilio.rest import Client
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

client = Client(account_sid, auth_token)

message = client.messages.create(
    body="Hello! This is a test SMS from Twilio.",
    from_="+12526595639",   # your Twilio trial number
    to="+919513838736"      # your verified mobile number
)

print("Message SID:", message.sid)

