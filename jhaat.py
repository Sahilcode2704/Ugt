import smtplib
import requests
import pandas as pd
import logging
import csv
import os
import time
from datetime import datetime, timedelta
import pytz
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ================== CONFIG ==================
SENDER_EMAIL = "sahiln27042008@gmail.com"
APP_PASSWORD = "feaylvqzmrfzaoil"  # Your app password
EMAIL_FUNCTION_URL = "https://sahilcode2704.github.io/Email/emailgrt.py"
CONTACTS_CSV_URL = "https://sahilcode2704.github.io/Email/contacts.csv"
GITHUB_ORG = "openai"
LOG_FILE = "email_log.csv"
SEND_HOUR = 19
SEND_MINUTE = 0

# ================== LOGGING ==================
logging.basicConfig(filename="email_errors.log", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ================== EMAIL SENDER ==================
def send_email(receiver_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)

# ================== SCRAPE GITHUB EMAILS ==================
def get_github_emails(org_name):
    print(f"🔍 Scraping emails from GitHub org: {org_name}")
    api_url = f"https://api.github.com/orgs/{org_name}/repos"
    emails = set()

    try:
        repos = requests.get(api_url).json()
        for repo in repos:
            commits_url = repo['commits_url'].replace("{/sha}", "")
            commits = requests.get(commits_url).json()

            for commit in commits:
                try:
                    email = commit['commit']['author']['email']
                    if "noreply" not in email:
                        emails.add(email)
                except:
                    continue
    except Exception as e:
        logging.error(f"GitHub scraping failed: {e}")
        print(f"❌ GitHub scraping failed: {e}")
    return emails

# ================== LOAD CONTACTS ==================
def load_contacts():
    try:
        df = pd.read_csv(CONTACTS_CSV_URL)
        print("✅ Loaded contacts from CSV.")
        return set(df['Email'].dropna().str.strip())
    except Exception as e:
        logging.error(f"Failed to load contacts: {e}")
        print("❌ Failed to load contacts CSV.")
        exit(1)

# ================== SCHEDULER ==================
def schedule_email_if_needed():
    choice = input("⏱ Do you want to schedule the emails for 7:00 PM IST? (y/n): ").strip().lower()
    if choice == 'y':
        timezone = pytz.timezone('Asia/Kolkata')
        now = datetime.now(timezone)
        target_time = timezone.localize(now.replace(hour=SEND_HOUR, minute=SEND_MINUTE, second=0, microsecond=0))
        if now > target_time:
            target_time += timedelta(days=1)
        wait_seconds = int((target_time - now).total_seconds())
        print(f"⏳ Waiting until {target_time.strftime('%Y-%m-%d %H:%M:%S %Z')} to send emails...")
        while wait_seconds > 0:
            hrs, rem = divmod(wait_seconds, 3600)
            mins, secs = divmod(rem, 60)
            print(f"⏳ Time remaining: {hrs:02d}:{mins:02d}:{secs:02d}", end="\r")
            time.sleep(min(30, wait_seconds))
            wait_seconds -= 30
        print("⏰ Time reached. Sending emails now...")
    else:
        print("🚀 Sending emails now without waiting...")

# ================== MAIN EMAIL SENDER ==================
def send_bulk_emails(all_emails):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["Email", "Time Sent", "Status"])
            writer.writeheader()

    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Email", "Time Sent", "Status"])
        for email in all_emails:
            subject = "Seeking Your Insight on Real-World Tech Challenges"
            body = f"""\
Dear Professional,

I hope you're doing well. I'm reaching out as someone who is passionate about solving real-world problems through technology and AI.

I'm currently working on building meaningful projects and believe that the best ideas often come from actual challenges that professionals like you encounter — whether in architecture, development, data handling, or system design.

If there's any issue, inefficiency, or idea you’ve come across — no matter how small — that you feel is worth exploring or solving, I would genuinely appreciate hearing about it.

Warm regards,  
Sahil  
sahiln27042008@gmail.com
"""

            try:
                send_email(email, subject, body)
                writer.writerow({"Email": email, "Time Sent": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "Status": "Sent"})
                print(f"✅ Sent to {email}")
            except Exception as e:
                writer.writerow({"Email": email, "Time Sent": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "Status": f"Failed: {e}"})
                logging.error(f"Failed to send email to {email}: {e}")
                print(f"❌ Failed to send to {email}")

# ================== RUN ==================
if __name__ == "__main__":
    contacts_csv_emails = load_contacts()
    github_emails = get_github_emails(GITHUB_ORG)
    all_emails = contacts_csv_emails.union(github_emails)

    print(f"📬 Total unique emails to send: {len(all_emails)}")
    schedule_email_if_needed()
    send_bulk_emails(all_emails)