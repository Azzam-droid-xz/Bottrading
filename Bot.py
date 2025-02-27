import asyncio
import ccxt
import pandas as pd
import ta
import schedule
import time
import threading
from telegram import Bot

# Konfigurasi bot Telegram
TOKEN = "5840991870:AAEs7pC8wTdZEwInNeIhPPCNPBVhSsK_Mno"
CHAT_ID = "898342901"  # Ganti dengan chat ID atau grup Telegram
bot = Bot(token=TOKEN)

# Konfigurasi exchange Binance
exchange = ccxt.binance()

# List koin yang dipantau
COINS = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "SOL/USDT", "XRP/USDT",
    "DOGE/USDT", "LTC/USDT", "MATIC/USDT", "DOT/USDT", "AVAX/USDT", "LINK/USDT",
    "SHIB/USDT", "TRX/USDT", "ATOM/USDT", "XLM/USDT", "NEAR/USDT", "FTM/USDT"
]

# Fungsi untuk mendapatkan data historis
def get_ohlcv(symbol, timeframe='1h', limit=100):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"❌ Error fetch data {symbol}: {e}")
        return None

# Fungsi untuk analisis RSI dan MACD
def analyze_coin(symbol):
    df = get_ohlcv(symbol)
    if df is None:
        return symbol, None, None, "ERROR"

    try:
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        last_rsi = df['rsi'].iloc[-1]

        macd = ta.trend.MACD(df['close']).macd()
        last_macd = macd.iloc[-1]

        signal = "Tunggu"
        if last_rsi < 30 and last_macd > 0:
            signal = "BUY 📈"
        elif last_rsi > 70 and last_macd < 0:
            signal = "SELL 📉"

        return symbol, last_rsi, last_macd, signal
    except Exception as e:
        print(f"❌ Error analisis {symbol}: {e}")
        return symbol, None, None, "ERROR"

# Fungsi untuk mendapatkan harga terkini dan perubahan harga dalam 24 jam
def get_price_info(symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        change = ticker['change']
        high = ticker['high']
        low = ticker['low']
        return price, change, high, low
    except Exception as e:
        print(f"❌ Error fetch harga {symbol}: {e}")
        return None, None, None, None

# Fungsi utama untuk analisis dan notifikasi Telegram
async def check_signals():
    print("🔍 Memulai scan market...")
    try:
        await bot.send_message(chat_id=CHAT_ID, text="🔍 Memulai scan market...")

        message = "📢 **Analisis Pasar Saat Ini:**\n"

        for coin in COINS:
            price, change, high, low = get_price_info(coin)
            if price is None:
                continue

            symbol, rsi, macd, signal = analyze_coin(coin)
            trend = "⬆️ Bullish" if change > 0 else "⬇️ Bearish"

            message += (
                f"\n💰 **{symbol}**\n"
                f"📌 Harga Saat Ini: **${price:,.2f}**\n"
                f"📉 Perubahan 24 Jam: **{'+' if change > 0 else ''}{change:,.2f}%** {trend}\n"
                f"📊 Tertinggi: **${high:,.2f}** | Terendah: **${low:,.2f}**\n"
                f"📈 RSI: **{rsi:.2f}** | MACD: **{macd:.4f}**\n"
                f"⚠️ **Sinyal Trading:** *{signal}*\n"
            )

        print("📤 Mengirim pesan ke Telegram...")
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
    except Exception as e:
        print(f"❌ Error Telegram: {e}")

# Fungsi untuk menjalankan asyncio dengan threading
def run_asyncio():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(check_signals())

# Jadwal menjalankan fungsi setiap 1 jam
schedule.every(1).hours.do(lambda: threading.Thread(target=run_asyncio).start())

print("🤖 Bot berjalan...")

while True:
    schedule.run_pending()
    time.sleep(5)
