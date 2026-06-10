import time
import requests
import pandas as pd
import numpy as np
import datetime
from threading import Thread
from flask import Flask

# ========================================================
# ⚙️ વેબ સર્વર સેટિંગ (ક્લાઉડ બોટને જીવતો રાખવા માટે)
# ========================================================
app = Flask('')

@app.route('/')
def home():
    return "Quotex Smart Bot is running live 24/7!"

def run_web_server():
    # ક્લાઉડ સર્વર આપોઆપ પોર્ટ સેટ કરશે, ડિફોલ્ટ ૮૦૮૦ રાખ્યો છે
    app.run(host='0.0.0.0', port=8080)

# ========================================================
# ⚙️ તમારા ટેલિગ્રામ સેટિંગ્સ
# ========================================================
TELEGRAM_TOKEN = "8539958945:AAG2lBFKKvi_wYPSMh9Utpx3fAMOtagsd5s"
TELEGRAM_CHAT_ID = "647373758"

last_signal_minutes = {
    "EURUSDT": -1,
    "GBPUSDT": -1
}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def get_real_live_data(symbol):
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": "5m", "limit": 50}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        candles = []
        for c in data:
            candles.append({
                'close': float(c[4]),
                'high': float(c[2]),
                'low': float(c[3]),
                'volume': float(c[5])
            })
        return pd.DataFrame(candles)
    except:
        return None

def calculate_indicators(df):
    if df is None or len(df) < 20:
        return None
        
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    df['EMA_12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD_Line'] = df['EMA_12'] - df['EMA_26']
    df['Signal_Line'] = df['MACD_Line'].ewm(span=9, adjust=False).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
    rs = gain / (loss + 1e-10)
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    df['Vol_SMA'] = df['volume'].rolling(window=10, min_periods=1).mean()
    return df

def process_live_signals(df, display_symbol, binance_symbol):
    global last_signal_minutes
    if df is None:
        return
        
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    current_price = last_row['close']
    ema20 = last_row['EMA_20']
    ema50 = last_row['EMA_50']
    macd_line = last_row['MACD_Line']
    signal_line = last_row['Signal_Line']
    rsi = last_row['RSI_14']
    
    volume_ok = last_row['volume'] > last_row['Vol_SMA']
    
    macd_crossed_up = (prev_row['MACD_Line'] <= prev_row['Signal_Line']) and (macd_line > signal_line)
    macd_crossed_down = (prev_row['MACD_Line'] >= prev_row['Signal_Line']) and (macd_line < signal_line)

    now = datetime.datetime.now()
    current_minute = now.minute

    if current_minute == last_signal_minutes.get(binance_symbol, -1):
        return

    # 🟢 SMART CALL SIGNAL
    if (current_price > ema50) and (current_price > ema20) and macd_crossed_up and (53 < rsi < 68) and volume_ok:
        msg = f"🚀 *QUOTEX CLOUD CALL* 🚀\n\n📊 *Asset:* {display_symbol} (Real)\n🎯 *Direction:* BUY / CALL ⬆️\n⏰ *Expiry:* 5 Minutes\n💰 *Price:* {current_price:.5f}"
        send_telegram_message(msg)
        print(f"💥 {display_symbol} CALL સિગ્નલ મોકલ્યો!")
        last_signal_minutes[binance_symbol] = current_minute
        
    # 🔴 SMART PUT SIGNAL
    elif (current_price < ema50) and (current_price < ema20) and macd_crossed_down and (32 < rsi < 47) and volume_ok:
        msg = f"🚀 *QUOTEX CLOUD PUT* 🚀\n\n📊 *Asset:* {display_symbol} (Real)\n🎯 *Direction:* SELL / PUT ⬇️\n⏰ *Expiry:* 5 Minutes\n💰 *Price:* {current_price:.5f}"
        send_telegram_message(msg)
        print(f"💥 {display_symbol} PUT સિગ્નલ મોકલ્યો!")
        last_signal_minutes[binance_symbol] = current_minute

def run_live_bot():
    print("🚀 Cloud Bot મુખ્ય સ્કેનિંગ શરૂ થઈ ગયું છે...")
    markets = {"EURUSDT": "EUR/USD", "GBPUSDT": "GBP/USD"}
    
    while True:
        for symbol, display_name in markets.items():
            try:
                df_live = get_real_live_data(symbol)
                if df_live is not None:
                    df_indicators = calculate_indicators(df_live)
                    process_live_signals(df_indicators, display_name, symbol)
            except:
                pass
            time.sleep(0.5)
        time.sleep(2)

if __name__ == "__main__":
    # વેબ સર્વરને અલગ બેકગ્રાઉન્ડ થ્રેડમાં ચાલુ કરો
    t = Thread(target=run_web_server)
    t.start()
    
    # મુખ્ય બોટ લોજિક ચાલુ કરો
    run_live_bot()
  
