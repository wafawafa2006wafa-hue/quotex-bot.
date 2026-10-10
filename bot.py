import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

# 1. إعدادات تيليجرام
TOKEN = "8883009013:AAHgGEYkfiwF-dFd1ihN6qrPgZh-aH2q_Iw"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}/"

# 2. خادم وهمي لإبقاء البوت نشطاً 24/7 على منصة Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running 24/7!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# بدء تشغيل الخادم الوهمي في خلفية البوت
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

# 3. المنطق الأساسي للتحليل والأسعار (مع إضافة تصحيح السعر 0.0097 لـ Quotex OTC)
CORRECTION_OFFSET = 0.0097

def get_crypto_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url, timeout=5)
        data = response.json()
        return float(data['price']) + CORRECTION_OFFSET
    except Exception as e:
        print(f"Error fetching crypto price: {e}")
        return None

def send_telegram_message(chat_id, text):
    url = TELEGRAM_API_URL + "sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error sending message: {e}")

# حلقة التشغيل البسيطة للتحقق والرد
def main():
    print("Bot is running...")
    offset = 0
    while True:
        try:
            url = TELEGRAM_API_URL + f"getUpdates?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35)
            data = response.json()
            
            if "result" in data:
                for update in data["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        
                        if text == "/start":
                            send_telegram_message(chat_id, "أهلاً بك! بوت تحليل وتوصيات Quotex يعمل بنجاح على السحابة.")
                        elif text.upper() in ["BTCUSDT", "ETHUSDT"]:
                            price = get_crypto_price(text.upper())
                            if price:
                                send_telegram_message(chat_id, f"سعر {text.upper()} الحالي (مع تعديل Quotex OTC): {price}")
                            else:
                                send_telegram_message(chat_id, "عذراً، حدث خطأ أثناء جلب السعر.")
        except Exception as e:
            print(f"Polling error: {e}")

if __name__ == "__main__":
    main()
