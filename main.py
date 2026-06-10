import os
import time
import requests
import pandas as pd

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")
INTERVAL = "5m"

# ૧ કલાકના સેશનમાં વધુ તક મળે એટલે મલ્ટિપલ પેર સેટ કરી
SYMBOLS = ["EURUSD", "GBPUSD"]

# લાઈવ કેન્ડલ પર દરેક પેર માટે અલગ ટાઈમ લોક રાખવા ડિક્શનરી બનાવી
LAST_SIGNAL_TIMES = {symbol: 0 for symbol in SYMBOLS}  

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
        print(f"Data Fetch Error for {symbol}: {e}")
        return None

def calculate_indicators(df):
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df

def check_signals():
    global LAST_SIGNAL_TIMES
    print("સાંજના સેશન માટે EURUSD અને GBPUSD લાઈવ સ્કેન થઈ રહ્યું છે...")
    
    for symbol in SYMBOLS:
        df = get_binance_data(symbol, INTERVAL)
        if df is None or df.empty:
            continue

        df = calculate_indicators(df)
        
        current_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        macd_now = current_row['macd']
        signal_now = current_row['signal']
        rsi_now = current_row['rsi']
        
        macd_prev = prev_row['macd']
        signal_prev = prev_row['signal']
        
        current_time = time.time()
        
        # આ પેર પર છેલ્લો ટ્રેડ લીધાને ૫ મિનિટ ન થઈ હોય તો સ્કીપ કરો
        if current_time - LAST_SIGNAL_TIMES[symbol] < 300:
            continue

        # 1. INSTANT CALL / BUY
        if macd_prev <= signal_prev and macd_now > signal_now:
            if rsi_now > 50:
                msg = (
                    f"🚀 *QUOTEX EVENING CALL* 🚀\n\n"
                    f"📊 *Asset:* {symbol} (Real)\n"
                    f"🎯 *Direction:* BUY / CALL ⬆️\n"
                    f"⏰ *Expiry:* 5 Minutes\n"
                    f"💰 *Price:* {current_row['close']:.5f}\n"
                    f"📈 *RSI:* {rsi_now:.2f}"
                )
                send_telegram_message(msg)
                print(f"{symbol} માટે CALL સિગ્નલ લાઈવ મોકલ્યું!")
                LAST_SIGNAL_TIMES[symbol] = current_time

        # 2. INSTANT PUT / SELL
        elif macd_prev >= signal_prev and macd_now < signal_now:
            if rsi_now < 50:
                msg = (
                    f"🚀 *QUOTEX EVENING CALL* 🚀\n\n"
                    f"📊 *Asset:* {symbol} (Real)\n"
                    f"🎯 *Direction:* PUT / SELL ⬇️\n"
                    f"⏰ *Expiry:* 5 Minutes\n"
                    f"💰 *Price:* {current_row['close']:.5f}\n"
                    f"📉 *RSI:* {rsi_now:.2f}"
                )
                send_telegram_message(msg)
                print(f"{symbol} માટે PUT સિગ્નલ લાઈવ મોકલ્યું!")
                LAST_SIGNAL_TIMES[symbol] = current_time

if __name__ == "__main__":
    from threading import Thread
    from http.server import SimpleHTTPRequestHandler, HTTPServer
    
    def run_dummy_server():
        server_address = ('0.0.0.0', int(os.getenv("PORT", 8080)))
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
        httpd.serve_forever()
        
    Thread(target=run_dummy_server, daemon=True).start()
    send_telegram_message("⚡ *Quotex Evening Dual-Bot (EURUSD + GBPUSD) લાઈવ સેટ થઈ ગયો છે!*")
    
    while True:
        check_signals()
        time.sleep(5)
        
