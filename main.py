import os
import time
import requests

TOKEN = "8539958945:AAG21BFKKvi_wYPSMh9Utpx3fAM0tagsd5s" # તમારો નવો ટોકન

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def check_messages():
    last_update_id = 0
    while True:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}"
        try:
            res = requests.get(url).json()
            if res.get("result"):
                for update in res["result"]:
                    last_update_id = update["update_id"]
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"].get("text", "").lower()
                    
                    # હવે તમે ગમે તે મેસેજ લખશો, બોટ જવાબ આપશે
                    send_message(chat_id, f"👑 Badshah Bot એ તમારો મેસેજ '{text}' સાંભળ્યો! બોટ લાઈવ છે.")
        except:
            pass
        time.sleep(2)

if __name__ == "__main__":
    check_messages()
    
