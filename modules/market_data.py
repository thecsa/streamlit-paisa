import yfinance as yf
from tefas import Crawler
import pandas as pd
import datetime

def get_tefas_data(fund_code):
    """Fetches the latest price for a TEFAS fund."""
    try:
        crawler = Crawler()
        # Fetch data for the last few days to ensure we get the latest close
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=7)
        
        # tefas-crawler expects date as string 'YYYY-MM-DD' or datetime object
        # The error said: `date` should be a string like 'YYYY-MM-DD' or a `datetime.datetime` object.
        # We were passing datetime.date. Let's convert to datetime.datetime or string.
        
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        result = crawler.fetch(start=start_date_str, end=end_date_str, name=fund_code, columns=["code", "date", "price"])
        if result is not None and not result.empty:
            latest_price = result.iloc[0]['price']
            return latest_price
        return None
    except Exception as e:
        print(f"Error fetching TEFAS data for {fund_code}: {e}")
        return None

def get_market_price(symbol):
    """Fetches price for Crypto, Stocks, or Currency from Yahoo Finance."""
    try:
        # Append -USD for crypto if not present and likely crypto, or assume user provides full ticker
        # For USD/TRY, symbol is 'TRY=X'
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="1d")
        if not history.empty:
            return history['Close'].iloc[-1]
        return None
    except Exception as e:
        print(f"Error fetching market data for {symbol}: {e}")
        return None

def get_usd_try_rate():
    """Helper to get USD/TRY rate."""
    return get_market_price("TRY=X")
