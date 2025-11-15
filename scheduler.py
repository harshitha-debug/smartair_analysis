import schedule
import time
from email_alerts import check_alerts

schedule.every().day.at("21:37").do(check_alerts)

while True:
    schedule.run_pending()
    time.sleep(60)
