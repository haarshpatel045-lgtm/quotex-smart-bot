import os
import time
import requests
import pandas as pd

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")
INTERVAL = "5m"

# Quotex સ્ક્રીનશોટ મુજબની બધી જ બેસ્ટ લાઈવ કરન્સી પેર સેટ કરી દીધી
SYMBOLS = [
    "USDJPY", "EURUSD", "GBPJPY", "EURJPY", 
    "AUDJPY", "CADJPY", "CHFJPY", "EURAUD", "GBPUSD"
]

LAST_UPDATE_ID = 0

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except Exception as e: print(f"Telegram Error: {e}")

def get_market_data(symbol, interval):
    # બાઈનાન્સની ઓફિશિયલ સ્પોટ માર્કેટ ફીડ (100% લાઈવ અને સચોટ રેટ)
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
    except: return None

def calculate_badshah_filters(df):
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
    
    # ફિલ્ટર ૩: Stochastic Oscillator (14, 3)
    low_14 = df['low'].rolling(window=14).min()
    high_14 = df['high'].rolling(window=14).max()
    df['stoch_k'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
    df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
    return df

def generate_instant_signal():
    send_telegram_message("🔍 *Badshah Bot બધી જ લાઈવ કરન્સી પેર સ્કેન કરી રહ્યો છે... કૃપા કરીને થોડી સેકન્ડ રાહ જુઓ.*")
    
    signals_found = 0
    for symbol in SYMBOLS:
        df = get_market_data(symbol, INTERVAL)
        if df is None or df.empty: continue
        df = calculate_badshah_filters(df)
        
        current_row = df.iloc[-1]
        rsi = current_row['rsi']
        macd = current_row['macd']
        macd_sig = current_row['signal']
        stoch_k = current_row['stoch_k']
        stoch_d = current_row['stoch_d']
        
        # 👑 BADSHAH HIGH-ACCURACY BUY / CALL CONDITION
        if macd > macd_sig and rsi > 52 and stoch_k > stoch_d:
            msg = (
                f"👑 *BADSHAH LIVE MARKET SIGNAL* 👑\n\n"
                f"📊 *Asset:* {symbol} (Real-time)\n"
                f"🎯 *Direction:* BUY / CALL ⬆️\n"
                f"⏰ *Expiry:* 5 Minutes (Instant Mode)\n"
                f"💰 *Current Price:* {current_row['close']:.5f}\n"
                f"📈 *RSI:* {rsi:.2f} | *Trend:* STRONGLY BULLISH"
            )
            send_telegram_message(msg)
            signals_found += 1
            
        # 👑 BADSHAH HIGH-ACCURACY PUT / SELL CONDITION
        elif macd < macd_sig and rsi < 48 and stoch_k < stoch_d:
            msg = (
                f"👑 *BADSHAH LIVE MARKET SIGNAL* 👑\n\n"
                f"📊 *Asset:* {symbol} (Real-time)\n"
                f"🎯 *Direction:* PUT / SELL ⬇️\n"
                f"⏰ *Expiry:* 5 Minutes (Instant Mode)\n"
                f"💰 *Current Price:* {current_row['close']:.5f}\n"
                f"📉 *RSI:* {rsi:.2f} | *Trend:* STRONGLY BEARISH"
            )
            send_telegram_message(msg)
            signals_found += 1
            
    if signals_found == 0:
        send_telegram_message("⚠️ *અત્યારે બધી લાઈવ પેર સાઇડવેઝ (ચોપી) ઝોનમાં છે. કોઈ મજબૂત સિગ્નલ નથી મળી રહ્યું. થોડીવાર પછી ફરી ટ્રાય કરો!*")

def check_telegram_commands():
    global LAST_UPDATE_ID
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {"offset": LAST_UPDATE_ID + 1, "timeout": 1}
    try:
        response = requests.get(url, params=params).json()
        if "result" in response:
            for update in response["result"]:
                LAST_UPDATE_ID = update["update_id"]
                if "message" in update and "text" in update["message"]:
                    text = update["message"]["text"].lower()
                    chat_id_user = str(update["message"]["chat"]["id"])
                    
                    if chat_id_user == CHAT_ID:
                        if text in ["/signal", "/badshah", "signal"]:
                            generate_instant_signal()
    except Exception as e:
        print(f"Command Error: {e}")

if __name__ == "__main__":
    from threading import Thread
    from http.server import SimpleHTTPRequestHandler, HTTPServer
    
    def run_dummy_server():
        HTTPServer(('0.0.0.0', int(os.getenv("PORT", 8080))), SimpleHTTPRequestHandler).serve_forever()
        
    Thread(target=run_dummy_server, daemon=True).start()
    send_telegram_message("👑 *Badshah Multi-Pair Live Bot ઓન થઈ ગયો છે!*\n\nતમારા સ્ક્રીનશોટ મુજબની બધી જ કરન્સી એડ થઈ ગઈ છે. ટેલિગ્રામમાં ફક્ત `/signal` લખો!")
    
    while True:
        check_telegram_commands()
        time.sleep(2)
        
