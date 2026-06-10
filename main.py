import os
import time
import requests
import pandas as pd

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")
SYMBOLS = ["EURUSD", "GBPUSD"]
INTERVAL = "5m"

# લાઈવ કેન્ડલ પર વારંવાર સિગ્નલ ન પડે તે માટેનો ટાઈમ લોક
LAST_SIGNAL_TIME = 0  

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_binance_data(symbol, interval, limit=100):
    url = f"https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    try:
        response = requests.get(url, params=params)
        data = response.json()
        df = pd.DataFrame(data, columns=[
            'time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        return df
    except Exception as e:
        print(f"Data Fetch Error: {e}")
        return None

def calculate_indicators(df):
    # MACD ગણતરી (12, 26, 9)
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # RSI ગણતરી (14)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df

def check_signals():
    global LAST_SIGNAL_TIME
    print("સુપરફાસ્ટ લાઈવ માર્કેટ સ્કેન થઈ રહ્યું છે...")
    df = get_binance_data(SYMBOL, INTERVAL)
    if df is None or df.empty:
        return

    df = calculate_indicators(df)
    
    # --- ૧૦૦% સુપરફાસ્ટ સેટિંગ ---
    # `df.iloc[-1]` એટલે અત્યારની ચાલુ લાઈવ સેકન્ડની કેન્ડલ
    current_row = df.iloc[-1]
    # `df.iloc[-2]` એટલે એની બરાબર પાછળની કેન્ડલ
    prev_row = df.iloc[-2]
    
    macd_now = current_row['macd']
    signal_now = current_row['signal']
    rsi_now = current_row['rsi']
    
    macd_prev = prev_row['macd']
    signal_prev = prev_row['signal']
    
    current_time = time.time()
    
    # જો છેલ્લો ટ્રેડ લીધાને હજી ૫ મિનિટ (300 સેકન્ડ) ન થઈ હોય, તો નવું સિગ્નલ બ્લોક રાખવું
    if current_time - LAST_SIGNAL_TIME < 300:
        return

    # 1. INSTANT CALL / BUY (લાઈવ કેન્ડલ પર જેવો ક્રોસઓવર થાય કે તરત જ)
    if macd_prev <= signal_prev and macd_now > signal_now:
        if rsi_now > 50:
            msg = (
                f"🚀 *QUOTEX INSTANT CALL* 🚀\n\n"
                f"📊 *Asset:* {SYMBOL} (Real)\n"
                f"🎯 *Direction:* BUY / CALL ⬆️\n"
                f"⏰ *Expiry:* 5 Minutes\n"
                f"💰 *Price:* {current_row['close']:.5f}\n"
                f"📈 *RSI:* {rsi_now:.2f}"
            )
            send_telegram_message(msg)
            print("ઇન્સ્ટન્ટ CALL સિગ્નલ લાઈવ મોકલ્યું!")
            LAST_SIGNAL_TIME = current_time

    # 2. INSTANT PUT / SELL (લાઈવ કેન્ડલ પર જેવો ક્રોસઓવર થાય કે તરત જ)
    elif macd_prev >= signal_prev and macd_now < signal_now:
        if rsi_now < 50:
            msg = (
                f"🚀 *QUOTEX INSTANT CALL* 🚀\n\n"
                f"📊 *Asset:* {SYMBOL} (Real)\n"
                f"🎯 *Direction:* PUT / SELL ⬇️\n"
                f"⏰ *Expiry:* 5 Minutes\n"
                f"💰 *Price:* {current_row['close']:.5f}\n"
                f"📉 *RSI:* {rsi_now:.2f}"
            )
            send_telegram_message(msg)
            print("ઇન્સ્ટન્ટ PUT સિગ્નલ લાઈવ મોકલ્યું!")
            LAST_SIGNAL_TIME = current_time

if __name__ == "__main__":
    from threading import Thread
    from http.server import SimpleHTTPRequestHandler, HTTPServer
    
    def run_dummy_server():
        server_address = ('0.0.0.0', int(os.getenv("PORT", 8080)))
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
        httpd.serve_forever()
        
    Thread(target=run_dummy_server, daemon=True).start()
    send_telegram_message("⚡ *Quotex SuperFast Bot v9 (લાઈવ કેન્ડલ મોડ) ઓન થઈ ગયો છે!*")
    
    while True:
        check_signals()
        time.sleep(5)  # દર ૫ સેકન્ડે લાઈવ રેટ ચેક થશે જેથી ટાઇમિંગ એકદમ પરફેક્ટ રહે
