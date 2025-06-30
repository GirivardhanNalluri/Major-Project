import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client
import os


class AlertSystem:
    def __init__(self, email_config=None, sms_config=None):
        # Email configuration
        self.smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = email_config.get('smtp_port', 587)
        self.sender_email = email_config.get('sender_email')
        self.sender_password = email_config.get('sender_password')

        # SMS configuration (Twilio)
        self.twilio_account_sid = sms_config.get('account_sid')
        self.twilio_auth_token = sms_config.get('auth_token')
        self.twilio_phone_number = sms_config.get('phone_number')

    def send_email_alert(self, recipient_email, subject, message):
        try:
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = recipient_email

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient_email, msg.as_string())

            print(f"Email alert sent to {recipient_email}")
            return True
        except Exception as e:
            print(f"Email alert failed: {e}")
            return False

    def send_sms_alert(self, recipient_phone, message):
        try:
            client = Client(self.twilio_account_sid, self.twilio_auth_token)

            message = client.messages.create(
                body=message,
                from_=self.twilio_phone_number,
                to=recipient_phone
            )

            print(f"SMS alert sent to {recipient_phone}")
            return True
        except Exception as e:
            print(f"SMS alert failed: {e}")
            return False

    def send_earthquake_alert(self, recipient_email, recipient_phone, earthquake_data):
        # Construct alert message
        subject = "🚨 EARTHQUAKE ALERT 🚨"
        message = f"""
EARTHQUAKE DETECTED!

Location: {earthquake_data.get('location', 'Unknown')}
Time: {earthquake_data.get('timestamp', 'Unknown')}
Magnitude: {earthquake_data.get('magnitude', 'N/A')}

X-Axis: {earthquake_data.get('x_values', 'N/A')}
Y-Axis: {earthquake_data.get('y_values', 'N/A')}
Z-Axis: {earthquake_data.get('z_values', 'N/A')}

TAKE IMMEDIATE SAFETY PRECAUTIONS!
        """.strip()

        # Send email alert
        email_status = self.send_email_alert(recipient_email, subject, message)

        # Send SMS alert
        sms_status = self.send_sms_alert(recipient_phone, message)

        return email_status, sms_status


# Usage Example in main application
def initialize_alert_system():
    email_config = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': 'seelamohan.igt@gmail.com',  # Replace with your email
        'sender_password': 'sjhv gxbn jktv bpes'  # Use App Password
    }

    sms_config = {
        'account_sid': 'your_twilio_account_sid',
        'auth_token': 'your_twilio_auth_token',
        'phone_number': 'your_twilio_phone_number'
    }

    return AlertSystem(email_config, sms_config)

# Note:
# 1. For Gmail, use App Password instead of account password
# 2. Install required libraries:
#    pip install twilio