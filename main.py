import os
import time
import requests
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

# 1. તમારું કન્ફિગરેશન
TOKEN = "8539958945:AAG21BFKKvi_wYPSMh9Utpx3fAM0tagsd5s"
CHAT_ID = "8539958945"

# 2. ડમી વેબ સર્વર જે પોર્ટની એરરને રોકશે
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"Server running on port {port}")
    server.serve_forever()

# 3. બોટનું મુખ્ય લોજિક
def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text})

def bot_logic():
    send_message("👑 Badshah Bot ઇઝ ઓનલાઇન અને તૈયાર છે!")
    last_update_id = 0
    while True:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}"
        try:
            res = requests.get(url).json()
            if res.get("result"):
                for update in res["result"]:
                    last_update_id = update["update_id"]
                    msg = update["message"].get("text", "").lower()
                    if "signal" in msg or "start" in msg:
                        send_message("🚀 સિગ્નલ સ્કેનિંગ ચાલુ છે... ટૂંક સમયમાં રિઝલ્ટ આવશે!")
        except:
            pass
        time.sleep(2)

# 4. બંને પ્રોસેસ એકસાથે ચલાવો
if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot_logic()
    
