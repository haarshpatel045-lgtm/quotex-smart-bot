import os
import time
import requests
import pandas as pd

TOKEN = "7759530514:AAHwG6g1yM7Z_r70e5_1Cg3Z3Rlh5vG1p7A"
CHAT_ID = "1265811796"
INTERVAL = "5m"

# બધી જ લાઈવ પેર્સ
SYMBOLS = ["USDJPY", "EURUSD", "GBPJPY", "EURJPY", "AUDJPY", "CADJPY", "CHFJPY", "EURAUD", "GBPUSD", "BTCUSDT", "ETHUSDT"]
LAST_SIGNALS = {symbol: None for symbol in SYMBOLS}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except: pass

def get_market_data(symbol, interval):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": 100}
    try:
        response = requests.get(url, params=params)
        df = pd.DataFrame(response.json(), columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        return df
    except: return None

def calculate_indicators(df):
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
    low_14 = df['low'].rolling(window=14).min()
    high_14 = df['high'].rolling(window=14).max()
    df['stoch_k'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
    df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
    return df

def auto_scan_loop():
    global LAST_SIGNALS
    while True:
        for symbol in SYMBOLS:
            df = get_market_data(symbol, INTERVAL)
            if df is None or df.empty: continue
            df = calculate_indicators(df)
            current = df.iloc[-1]
            
            # સિગ્નલ લોજિક
            if current['macd'] > current['signal'] and current['rsi'] > 52 and current['stoch_k'] > current['stoch_d']:
                if LAST_SIGNALS[symbol] != "BUY":
                    send_telegram_message(f"🚀 *AUTO SIGNAL - BUY/CALL*\n📊 *Asset:* {symbol}\n💰 *Price:* {current['close']:.5f}")
                    LAST_SIGNALS[symbol] = "BUY"
            
            elif current['macd'] < current['signal'] and current['rsi'] < 48 and current['stoch_k'] < current['stoch_d']:
                if LAST_SIGNALS[symbol] != "SELL":
                    send_telegram_message(f"🔻 *AUTO SIGNAL - SELL/PUT*\n📊 *Asset:* {symbol}\n💰 *Price:* {current['close']:.5f}")
                    LAST_SIGNALS[symbol] = "SELL"
        
        time.sleep(60) # દર ૧ મિનિટે માર્કેટ ચેક કરશે

if __name__ == "__main__":
    from threading import Thread
    from http.server import SimpleHTTPRequestHandler, HTTPServer
    def run_dummy_server(): HTTPServer(('0.0.0.0', int(os.getenv("PORT", 8080))), SimpleHTTPRequestHandler).serve_forever()
    Thread(target=run_dummy_server, daemon=True).start()
    
    send_telegram_message("👑 *Badshah 24/7 Auto-Scanner ઓન થઈ ગયો છે!* હવે દર મિનિટે માર્કેટ સ્કેન થશે.")
    auto_scan_loop()
    
