import requests
import smtplib
import csv
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from config import API_KEY, SENDER_EMAIL, SENDER_PASSWORD

def fetch_current_aqi(city):
    """Fetch current AQI for a city"""
    try:
        geo = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={city}&appid={API_KEY}").json()
        lat, lon = geo[0]["lat"], geo[0]["lon"]
        
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        data = requests.get(url).json()
        return data["list"][0]["main"]["aqi"]
    except Exception as e:
        print(f"❌ Error fetching AQI for {city}: {e}")
        return 3  # Default to moderate pollution

def map_aqi_to_category(aqi):
    """Map AQI value to category and range exactly as shown in screenshot"""
    if aqi == 1:
        return "Good", "0-50"
    elif aqi == 2:
        return "Moderate", "51-100"
    elif aqi == 3:
        return "Poor", "101-200"
    elif aqi == 4:
        return "Very Poor", "201-300"
    else:
        return "Severe", "300+"

def get_tomorrow_aqi(current_aqi):
    """Predict tomorrow's AQI (simplified logic)"""
    tomorrow_aqi = min(5, current_aqi + 1)
    return map_aqi_to_category(tomorrow_aqi)

def send_email(to_email, subject, html_body):
    """Send email to recipient"""
    try:
        msg = MIMEText(html_body, "html")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"✅ Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
        return False

def send_immediate_alerts():
    """Send immediate pollution alerts to all subscribed users"""
    print("📧 Starting immediate alert process...")
    
    try:
        with open("city_emails.csv") as file:
            reader = csv.DictReader(file)
            email_count = 0
            
            for row in reader:
                city = row["city"]
                email = row["email"]
                
                print(f"📨 Processing {city} -> {email}")
                
                current_aqi = fetch_current_aqi(city)
                current_category, current_range = map_aqi_to_category(current_aqi)
                tomorrow_category, tomorrow_range = get_tomorrow_aqi(current_aqi)

                html_body = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    body {{
        font-family: 'Segoe UI', Arial, sans-serif;
        margin: 0; padding: 0;
        background: #eef2f3;
    }}
    .container {{
        max-width: 620px;
        margin: 20px auto;
        background: #fff;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    .header {{
        background: linear-gradient(90deg, #ff4d4d, #d90429);
        padding: 18px 24px;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 15px;
        font-weight: bold;
    }}
    .content {{
        padding: 25px;
        color: #333;
    }}
    .title {{
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 18px;
        color: #d90429;
    }}
    .aqi-box {{
        background: #fcecec;
        padding: 15px;
        border-radius: 8px;
        font-size: 16px;
        margin-bottom: 20px;
        border-left: 5px solid #d90429;
    }}
    .precautions-title {{
        font-size: 18px;
        font-weight: bold;
        margin: 15px 0 10px;
        color: #222;
    }}
    ul {{
        padding-left: 20px;
    }}
    ul li {{
        margin-bottom: 8px;
        line-height: 1.4;
    }}
    .footer {{
        padding: 18px;
        background: #fafafa;
        text-align: center;
        font-size: 13px;
        color: #666;
        border-top: 1px solid #eee;
    }}
</style>
</head>
<body>

<div class="container">

    <div class="header">
        <div>SmartAir Monitoring System</div>
        <div>{datetime.now().strftime('%I:%M %p')}</div>
    </div>

    <div class="content">
        <div class="title">⚠ Air Quality Alert for {city.upper()}</div>

        <div class="aqi-box">
            <b>Today's AQI:</b> {current_category} ({current_range})<br>
            <b>Tomorrow's Forecast:</b> {tomorrow_category} ({tomorrow_range})
        </div>

        <div class="precautions-title">Recommended Precautions:</div>
        <ul>
            <li>Wear an N95 mask outdoors 😷</li>
            <li>Avoid long outdoor exposure 🚫</li>
            <li>Use air purifiers indoors 🌬️</li>
            <li>Keep windows closed during peak pollution hours 🔒</li>
            <li>Stay hydrated and monitor breathing 💧</li>
        </ul>
    </div>

    <div class="footer">
        Stay safe & monitor air quality regularly.<br>
        <b>SmartAir Monitoring System</b>
    </div>

</div>

</body>
</html>
                """

                if send_email(email, f"AQI Alert for {city.upper()}", html_body):
                    email_count += 1
                
        print(f"✅ Alert process completed! Sent {email_count} emails.")
        return email_count
        
    except Exception as e:
        print(f"❌ Error in send_immediate_alerts: {e}")
        return 0
