import os
import time
import requests

# તમારી નવી વિગતો અહીં અપડેટ કરો
TOKEN = "8539958945:AAG21BFKKvi_wYPSMh9Utpx3fAM0tagsd5s"
CHAT_ID = "8539958945"

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, json=payload)

def start_bot():
    send_message("👑 Badshah Bot સક્રિય થઈ ગયો છે! હવે હું લાઈવ માર્કેટ સિગ્નલ આપીશ.")
    
    # અહીંથી આપણે દર ૫ સેકન્ડે મેસેજ ચેક કરીશું
    last_update_id = 0
    while True:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}"
        try:
            response = requests.get(url).json()
            if "result" in response and len(response["result"]) > 0:
                for update in response["result"]:
                    last_update_id = update["update_id"]
                    msg = update["message"].get("text", "").lower()
                    
                    if "signal" in msg or "start" in msg:
                        send_message("✅ સિસ્ટમ તૈયાર છે! ટ્રેડિંગ સેશન માટે બધું ઓકે છે.")
        except:
            pass
        time.sleep(2)

if __name__ == "__main__":
    start_bot()
    
