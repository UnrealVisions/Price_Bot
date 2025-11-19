import telebot
import requests
from bs4 import BeautifulSoup
import schedule
import time
import os
import json
from datetime import datetime
import threading

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
bot = telebot.TeleBot(BOT_TOKEN)
DATA_FILE = 'products.json'

def load_products():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_products(products):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

def get_amazon_price(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        price = soup.find("span", class_="a-price-whole")
        fraction = soup.find("span", class_="a-price-fraction")
        if price and fraction:
            p = price.get_text(strip=True) + "." + fraction.get_text(strip=True)
            return float(p.replace(",", ""))
    except:
        pass
    return None

def get_noon_price(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        price = soup.find("span", {"data-testid": "price"})
        if price:
            p = price.get_text(strip=True).replace("SAR","").replace("EGP","").replace("AED","").replace(",","").strip()
            return float(p)
    except:
        pass
    return None

def check_prices():
    products = load_products()
    if not products:
        return
    for key, item in list(products.items()):
        url = item['url']
        target = item['target_price']
        price = get_amazon_price(url) if "amazon" in url else get_noon_price(url) if "noon" in url else None
        if price and price <= target:
            bot.send_message(CHAT_ID, f"السعر نزل!\n\n{item['name']}\nالسعر الحالي: {price}\nالمطلوب: {target}\n{url}")
            del products[key]
            save_products(products)

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "أهلاً بك!\nأرسل رابط المنتج ثم السعر في سطر جديد\nمثال:\nhttps://www.noon.com/...\n4500")

@bot.message_handler(commands=['list'])
def list_cmd(m):
    products = load_products()
    if not products:
        bot.reply_to(m, "مفيش منتجات متابعة")
        return
    text = "المنتجات اللي بتابعها:\n\n"
    for p in products.values():
        text += f"• {p['name'][:60]}...\nالمطلوب: {p['target_price']}\n{p['url']}\n\n"
    bot.reply_to(m, text)

@bot.message_handler(func=lambda m: True)
def add_product(m):
    lines = m.text.strip().splitlines()
    if len(lines) < 2:
        return
    url = lines[0].strip()
    try:
        target_price = float(lines[1])
    except:
        bot.reply_to(m, "اكتب السعر في سطر لوحده")
        return

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.find("h1") or soup.find("title")
        name = title.get_text(strip=True)[:100] if title else "منتج"
    except:
        name = "منتج"

    products = load_products()
    products[url] = {"name": name, "url": url, "target_price": target_price}
    save_products(products)
    bot.reply_to(m, f"تمت الإضافة!\n{name}\nالمطلوب: {target_price} ريال")

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(60)

schedule.every().hour.do(check_prices)

if __name__ == "__main__":
    print("البوت شغال 24/7...")
    threading.Thread(target=run_schedule, daemon=True).start()
    bot.infinity_polling()

