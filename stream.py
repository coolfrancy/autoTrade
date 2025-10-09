from schwab.auth import client_from_manual_flow
from schwab.streaming import StreamClient
import os
import asyncio
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
from atrFunction import atr_wilder

load_dotenv()

API_KEY = os.getenv("ACC_APP_KEY")
APP_SECRET = os.getenv("ACC_SECRET_KEY")
CALLBACK = "https://127.0.0.1:8182"
TOKEN_PATH = "token.json"
ACCOUNT_ID = os.getenv("ACC_NUMBER")

# Global DataFrame to store bars
bars_df = pd.DataFrame(columns=['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume'])

async def run_stream():
    global bars_df
    
    client = client_from_manual_flow(
        api_key=API_KEY,
        app_secret=APP_SECRET,
        callback_url=CALLBACK,
        token_path=TOKEN_PATH,
        asyncio=True
    )
    
    stream = StreamClient(client, account_id=ACCOUNT_ID)

    def on_bar(msg):
        global bars_df
        
        for item in msg.get("content", []):
            print("BAR:", item)
            
            # Extract data (adjust field names based on your actual data)
            new_bar = pd.DataFrame([{
                'timestamp': datetime.fromtimestamp(item.get('timestamp', 0) / 1000),
                'symbol': item.get('key', 'AAPL'),
                'open': item.get('OPEN_PRICE', 0),
                'high': item.get('HIGH_PRICE', 0),
                'low': item.get('LOW_PRICE', 0),
                'close': item.get('CLOSE_PRICE', 0),
                'volume': item.get('VOLUME', 0)
            }])

            if len(bars_df) >= 1:
                new_bar["atr"] = atr_wilder(bars_df, 2)
            
            bars_df = pd.concat([bars_df, new_bar], ignore_index=True)
            
            # Print summary
            print(f"Total bars: {len(bars_df)}")
            print(bars_df.tail())  # Show last 5 bars

    await stream.login()
    stream.add_chart_equity_handler(on_bar)
    await stream.chart_equity_subs(["AAPL"])
    
    while True:
        await stream.handle_message()

if __name__ == "__main__":
    asyncio.run(run_stream())