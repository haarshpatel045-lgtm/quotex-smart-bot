import os
import time
import requests
import pandas as pd
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

TOKEN = "8539958945:AAG21BFKKvi_wYPSMh9Utpx3fAM0tagsd5s"
CHAT_ID = "8539958945"

# 1. તમારી સ્ટ્રેટેજી ફંક્શન
def check_strategy(df):
    current = df.iloc[-1]
    
    # RSI ફિલ્ટર
    rsi_condition = current['rsi'] > 55 if 'buy' else current['rsi'] < 45
    # MACD ફિલ્ટર
    macd_condition = current['macd'] > current['signal']
    # Stochastic ફિલ્ટર
    stoch_condition = current['stoch_k'] > current['stoch_d']
    
    return rsi_condition and macd_condition and stoch_condition

# 2. Telegram Notification ફંક્શન
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

# 3. મેઈન સ્કેનિંગ લૂપ
def run_bot():
    send_telegram("👑 *Badshah Sniper Bot Start!* માર્કેટ સ્કેનિંગ ચાલુ છે...")
    while True:
        try:
            # અહીં તમારી માર્કેટ પેરનો ડેટા લાવો (Binance/TradingView API)
            # આ એક સેમ્પલ લોજિક છે
            send_telegram("🚀 *Sniper Signal:* EUR/USD પર બાય એન્ટ્રી લો! (1 મિનિટ)")
            time.sleep(60) # દર 1 મિનિટે સ્કેન
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

# 4. સર્વર ચાલુ રાખવા માટે
def run_server():
    HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 8080))), SimpleHTTPRequestHandler).serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    run_bot()
    
