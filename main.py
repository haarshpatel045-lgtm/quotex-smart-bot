import os
import time
import requests
import pandas as pd

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")
SYMBOL = "EURUSD"
INTERVAL = "5m"

# સાચા ક્રોસઓવરને ફિલ્ટર કરવા માટેનો પાકો ગેપ (Threshold)
# આનાથી લાઈનો માત્ર ટચ થશે તો ફેક સિગ્નલ નહીં બને
GAP_THRESHOLD = 0.00005  

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
    print("લાઈવ માર્કેટ ડેટા સ્કેન થઈ રહ્યો છે...")
    df = get_binance_data(SYMBOL, INTERVAL)
    if df is None or df.empty:
        return

    df = calculate_indicators(df)
    
    # છેલ્લી પૂરી થયેલી કેન્ડલનો ડેટા (Index -2)
    last_row = df.iloc[-2]
    # તેની આગળની કેન્ડલનો ડેટા (Index -3) જેથી ક્રોસઓવર ખબર પડે
    prev_row = df.iloc[-3]
    
    macd_now = last_row['macd']
    signal_now = last_row['signal']
    rsi_now = last_row['rsi']
    
    macd_prev = prev_row['macd']
    signal_prev = prev_row['signal']
    
    # --- ફિલ્ટર સાથે ચેકિંગ ---
    
    # 1. CALL / BUY સિગ્નલ (MACD એ સિગ્નલ લાઇનને નીચેથી ઉપર ક્રોસ કરી અને પાકો ગેપ બનાવ્યો)
    if macd_prev <= signal_prev and (macd_now - signal_now) > GAP_THRESHOLD:
        if rsi_now > 50:  # RSI કન્ફર્મેશન
            msg = (
                f"🚀 *QUOTEX CLOUD CALL* 🚀\n\n"
                f"📊 *Asset:* {SYMBOL} (Real)\n"
                f"🎯 *Direction:* BUY / CALL ⬆️\n"
                f"⏰ *Expiry:* 5 Minutes\n"
                f"💰 *Price:* {last_row['close']:.5f}\n"
                f"📈 *RSI:* {rsi_now:.2f}"
            )
            send_telegram_message(msg)
            print("CALL સિગ્નલ મોકલી દીધું!")
            time.sleep(300) # 5 મિનિટ માટે બોટ શાંત થઈ જશે

    # 2. PUT / SELL સિગ્નલ (MACD એ સિગ્નલ લાઇનને ઉપરથી નીચે ક્રોસ કરી અને પાકો ગેપ બનાવ્યો)
    elif macd_prev >= signal_prev and (signal_now - macd_now) > GAP_THRESHOLD:
        if rsi_now < 50:  # RSI કન્ફર્મેશન
            msg = (
                f"🚀 *QUOTEX CLOUD CALL* 🚀\n\n"
                f"📊 *Asset:* {SYMBOL} (Real)\n"
                f"🎯 *Direction:* PUT / SELL ⬇️\n"
                f"⏰ *Expiry:* 5 Minutes\n"
                f"💰 *Price:* {last_row['close']:.5f}\n"
                f"📉 *RSI:* {rsi_now:.2f}"
            )
            send_telegram_message(msg)
            print("PUT સિગ્નલ મોકલી દીધું!")
            time.sleep(300) # 5 મિનિટ માટે બોટ શાંત થઈ જશે

if __name__ == "__main__":
    # ક્લાઉડ પર રન કરવા માટે સિમ્પલ વેબ સર્વર પોર્ટ બાઈન્ડિંગ (Render માટે જરૂરી)
    from threading import Thread
    from http.server import SimpleHTTPRequestHandler, HTTPServer
    
    def run_dummy_server():
        server_address = ('0.0.0.0', int(os.getenv("PORT", 8080)))
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
        httpd.serve_forever()
        
    Thread(target=run_dummy_server, daemon=True).start()
    send_telegram_message("⚡ *Quotex Smart Bot v8 (ફિલ્ટર અપડેટ) લાઈવ થઈ ગયો છે!*")
    
    while True:
        check_signals()
        time.sleep(10)  # દર ૧૦ સેકન્ડે માર્કેટ ચેક થશે
