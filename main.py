import os
import time
import requests
import pandas as pd

# --- AUTOMATIC CONFIGURATION ---
# Render પર સેટ કરેલા ટોકન આપોઆપ અહીંથી ઉપડી જશે
TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")
INTERVAL = "5m"

# સુપર ટ્રેડિંગ માટે આપણે મલ્ટિપલ બેસ્ટ જોડીઓ સેટ કરી
# ૧. ક્રિપ્ટો (ડેલ્ટા એક્સચેન્જ માટે બેસ્ટ) અને ૨. ફોરેક્સ કરન્સી
SYMBOLS = ["BTCUSDT", "ETHUSDT", "EURUSD", "GBPUSD"]
LAST_SIGNAL_TIMES = {symbol: 0 for symbol in SYMBOLS}  

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_market_data(symbol, interval):
    # ક્રિપ્ટો અને ફોરેક્સ બંને માટે લાઈવ બાઈનાન્સ ડેટા ફીડ
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": 100}
    try:
        response = requests.get(url, params=params)
        df = pd.DataFrame(response.json(), columns=[
            'time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        return df
    except:
        return None

def calculate_badshah_filters(df):
    """ Badshah Bot નું ઓરિજિનલ હાઈ-એક્યુરેસી ગણિત """
    # ફિલ્ટર ૧: MACD (12, 26, 9)
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # ફિલ્ટર ૨: RSI (14)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
    
    # ફિલ્ટર ૩: Stochastic Oscillator (14, 3) - પર્ફેક્ટ રિવર્સલ માટે
    low_14 = df['low'].rolling(window=14).min()
    high_14 = df['high'].max() if 'high' in df else df['close'] # સેફ્ટી ચેક
    high_14 = df['high'].rolling(window=14).max()
    df['stoch_k'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
    df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
    
    return df

def scan_markets():
    global LAST_SIGNAL_TIMES
    print("👑 Badshah Bot બેકગ્રાઉન્ડમાં માર્કેટ સ્કેન કરી રહ્યો છે...")
    
    for symbol in SYMBOLS:
        df = get_market_data(symbol, INTERVAL)
        if df is None or df.empty: continue

        df = calculate_badshah_filters(df)
        current_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        current_time = time.time()
        
        # એક પેર પર ટ્રેડ લીધા પછી ૫ મિનિટ સુધી ફરી મેસેજ ન જાય તે માટે લોક
        if current_time - LAST_SIGNAL_TIMES[symbol] < 300: continue

        # 👑 1. BADSHAH BUY / CALL SIGNAL (બધા જ કન્ફર્મેશન સાથે)
        if prev_row['macd'] <= prev_row['signal'] and current_row['macd'] > current_row['signal']:
            if current_row['rsi'] > 50 and current_row['stoch_k'] > current_row['stoch_d']:
                msg = (
                    f"👑 *BADSHAH HIGH-ACCURACY SIGNAL* 👑\n\n"
                    f"📊 *Asset:* {symbol}\n"
                    f"🎯 *Direction:* BUY / CALL ⬆️\n"
                    f"⏰ *Expiry:* 5 Minutes\n"
                    f"💰 *Entry Price:* {current_row['close']:.5f}\n"
                    f"📈 *RSI:* {current_row['rsi']:.2f} | *Stoch:* OK"
                )
                send_telegram_message(msg)
                print(f"🎯 {symbol} માટે Badshah BUY મેસેજ મોકલ્યો!")
                LAST_SIGNAL_TIMES[symbol] = current_time

        # 👑 2. BADSHAH PUT / SELL SIGNAL (બધા જ કન્ફર્મેશન સાથે)
        elif prev_row['macd'] >= prev_row['signal'] and current_row['macd'] < current_row['signal']:
            if current_row['rsi'] < 50 and current_row['stoch_k'] < current_row['stoch_d']:
                msg = (
                    f"👑 *BADSHAH HIGH-ACCURACY SIGNAL* 👑\n\n"
                    f"📊 *Asset:* {symbol}\n"
                    f"🎯 *Direction:* PUT / SELL ⬇️\n"
                    f"⏰ *Expiry:* 5 Minutes\n"
                    f"💰 *Entry Price:* {current_row['close']:.5f}\n"
                    f"📉 *RSI:* {current_row['rsi']:.2f} | *Stoch:* OK"
                )
                send_telegram_message(msg)
                print(f"🎯 {symbol} માટે Badshah PUT મેસેજ મોકલ્યો!")
                LAST_SIGNAL_TIMES[symbol] = current_time

if __name__ == "__main__":
    from threading import Thread
    from http.server import SimpleHTTPRequestHandler, HTTPServer
    
    def run_dummy_server():
        HTTPServer(('0.0.0.0', int(os.getenv("PORT", 8080))), SimpleHTTPRequestHandler).serve_forever()
        
    Thread(target=run_dummy_server, daemon=True).start()
    send_telegram_message("👑 *Badshah Signalbot Pro v11 તમારા ટેલિગ્રામ પર લાઈવ થઈ ગયો છે!*")
    
    while True:
        scan_markets()
        time.sleep(5) # દર ૫ સેકન્ડે ફાસ્ટ સ્કેન થશે
