import requests
import time
import asyncio
import datetime
from telegram import Bot
import config_spx as config  # Import SPX-specific config
import datetime
import pytz  # Time zone handling

# Initialize Telegram bot
bot = Bot(token=config.TELEGRAM_BOT_TOKEN)

# Flag to track if an alert has been sent
alert_sent = False  

def is_market_open():
    """Check if the market is open (Monday to Friday, 9:30 AM - 4:00 PM ET)"""
    ny_tz = pytz.timezone("America/New_York")
    now = datetime.datetime.now(ny_tz)  # Get current time in Eastern Time

    market_open_time = datetime.time(9, 30)  # 9:30 AM ET
    market_close_time = datetime.time(16, 0)  # 4:00 PM ET

    # Market is open if it's a weekday and within trading hours
    return now.weekday() < 5 and market_open_time <= now.time() <= market_close_time

def get_spx_approximation():
    """Fetches SPY price from Finnhub and approximates SPX."""
    url = f"https://finnhub.io/api/v1/quote?symbol=SPY&token={config.FINNHUB_API_KEY}"
    response = requests.get(url).json()

    if 'c' in response and response['c'] is not None:
        spy_price = response['c']
        spx_approx = spy_price * 10  # Approximate SPX
        return spx_approx
    else:
        print("⚠️ Finnhub API Error:", response)
        return None

async def send_alert(price):
    """Sends a Telegram alert when SPX is near the butterfly center."""
    message = f"🚀 SPX ALERT: Approximated {price} is near your butterfly center at {config.BUTTERFLY_CENTER}!"
    await bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=message)

async def monitor_spx():
    """Continuously checks SPX (approximated via SPY) and sends alerts only when needed."""
    global alert_sent  # Track if an alert has been sent

    while True:
        if is_market_open():
            spx_price = get_spx_approximation()
            print(f"Approximated SPX Price: {spx_price}")

            if spx_price:
                if abs(spx_price - config.BUTTERFLY_CENTER) <= config.TOLERANCE:
                    if not alert_sent:  # Only send an alert if it hasn't been sent already
                        await send_alert(spx_price)
                        alert_sent = True  # Mark that we've sent an alert
                else:
                    alert_sent = False  # Reset flag when price moves out of range
        else:
            print("⏳ Market is closed. Waiting for the next session.")

        await asyncio.sleep(60)  # Check every 60 seconds

def main():
    loop = asyncio.new_event_loop()  # Create a new event loop
    asyncio.set_event_loop(loop)  # Set it as the current event loop
    try:
        loop.run_until_complete(monitor_spx())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    finally:
        loop.close()  # Properly close the event loop

if __name__ == "__main__":
    main()
