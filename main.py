import requests
from bs4 import BeautifulSoup
import time
import os
import re
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        requests.post(url, data=data, timeout=10)
    except:
        pass

def extract_fio_region(text):
    fio_match = re.search(r'([А-ЯЁ][а-яё]{1,40}\s+[А-ЯЁ][а-яё]{1,40}\s+[А-ЯЁ][а-яё]{1,40})', text)
    fio = fio_match.group(1).strip() if fio_match else "Не указано"
    region_match = re.search(r'(?:г\.|город|обл\.|область|край|республика|р-н)\.?\s*([А-ЯЁ][А-Яа-яЁё\s-]+?)(?:,|\.|$|\s)', text, re.I)
    region = region_match.group(1).strip() if region_match else "Не определён"
    return fio, region

def parse_efrsb():
    url = "https://bankrot.fedresurs.ru/messages.aspx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    for attempt in range(3):
        try:
            print(f"Попытка {attempt + 1}...")
            response = requests.get(url, headers=headers, timeout=60)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                rows = soup.select('table.bankrot-tbl tr')[1:15]
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) < 4: continue
                    msg_type = cells[1].get_text(strip=True)
                    link = "https://bankrot.fedresurs.ru" + cells[1].find('a')['href']
                    text = cells[3].get_text(strip=True)
                    fio, region = extract_fio_region(text + " " + msg_type)
                    message = f"<b>🔔 Новое сообщение</b>\n\n👤 {fio}\n📍 {region}\n📌 {msg_type}\n\n🔗 <a href='{link}'>Открыть</a>"
                    send_to_telegram(message)
                return
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    parse_efrsb()
