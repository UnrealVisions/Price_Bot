import telebot
import requests
from bs4 import BeautifulSoup
import schedule
import time
import os
import json
from datetime import datetime
import threading

# التوكن والـ ID من Render Environment Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

bot = telebot.TeleBot(BOT_TOKEN)
DATA_FILE = 'products.json'

# تحميل المنتجات
def load_products():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

# حفظ المنتجات
def save_products(products):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

# جلب سعر أمازون
def get_amazon_price(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        price = soup.find("span", class_="a-price