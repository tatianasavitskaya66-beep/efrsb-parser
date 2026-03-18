import requests
from bs4 import BeautifulSoup
import time
import json
import re
import os
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
LAST_CHECK_FILE = "last_check.json"

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        requests.post(url, data=data, timeout=15)
    except:
        pass

def load_last_date():
    try:
        with open(LAST_CHECK_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get('last_date', '2025-01-01')
    except:
        return "2025-01-01"

def save_last_date(date_str):
    with open(LAST_CHECK_FILE, 'w', encoding='utf-8') as f:
        json.dump({'last_date': date_str}, f, ensure_ascii=False, indent=2)

def extract_fio_region(text):
    fio_match = re.search(r'([А-ЯЁ][а-яё]{1,40}\s+[А-ЯЁ][а-яё]{1,40}\s+[А-ЯЁ][а-яё]{1,40})', text)
    fio = fio_match.group(1).strip() if fio_match else "Не указано"
    region_match = re.search(r'(?:г\.|город|обл\.|область|край|республика|р-н)\.?\s*([А-ЯЁ][А-Яа-яЁё\s-]+?)(?:,|\.|$|\s)', text, re.I)
    region = region_match.group(1).strip() if region_match else "Не определён"
    return fio, region

def parse_efrsb():
    url = "https://bankrot.fedresurs.ru/messages.aspx"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=20)
    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.select('table.bankrot-tbl tr')[1:50]
    last_date = load_last_date()
    newest_date = last_date
    count = 0
    for row in rows:
        try:
            cells = row.find_all('td')
            if len(cells) < 4: continue
            date_text = cells[0].get_text(strip=True)
            if date_text < last_date: continue
            if date_text > newest_date: newest_date = date_text
            link = "https://bankrot.fedresurs.ru" + cells[1].find('a')['href']
            msg_type = cells[1].get_text(strip=True)
            text = cells[3].get_text(strip=True) if len(cells) > 3 else cells[-1].get_text(strip=True)
            fio, region = extract_fio_region(text + " " + msg_type)
            message = f"<b>🔔 Новое сообщение ЕФРСБ</b>\n\n<b>📅 Дата:</b> {date_text}\n<b>👤 ФИО:</b> {fio}\n<b>📍 Регион:</b> {region}\n<b>📌 Тип:</b> {msg_type}\n\n{text[:380]}...\n\n🔗 <a href='{link}'>Открыть на ЕФРСБ</a>"
            send_to_telegram(message)
            count += 1
            time.sleep(2)
        except: continue
    if count > 0:
        save_last_date(newest_date)
        print(f"Отправлено {count} сообщений")

if __name__ == "__main__":
    parse_efrsb()
