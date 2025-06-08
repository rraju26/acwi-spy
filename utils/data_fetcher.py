import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

class DataFetcher:
    """
    Fetch historical stock data using yfinance
    """
    
    def __init__(self):
        pass
    
    def fetch_stock_data(self, symbol, start_date, end_date):
        """
        Fetch historical stock data for a given symbol
        
        Args:
            symbol (str): Stock ticker symbol (e.g., 'ACWI', 'SPY')
            start_date (datetime.date): Start date for data
            end_date (datetime.date): End date for data
            
        Returns:
            pd.DataFrame: Historical stock data with OHLCV columns
        """
        try:
            # Add a buffer to ensure we have enough data
            buffer_start = start_date - timedelta(days=30)
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch historical data
            data = ticker.history(
                start=buffer_start,
                end=end_date + timedelta(days=1),  # Add 1 day to include end_date
                interval='1d'
            )
            
            if data.empty:
                st.error(f"No data found for symbol {symbol}")
                return pd.DataFrame()
            
            # Filter data to exact date range requested
            data = data[data.index.date >= start_date]
            data = data[data.index.date <= end_date]
            
            # Clean the data
            data = data.dropna()
            
            # Ensure we have the required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_columns:
                if col not in data.columns:
                    st.error(f"Missing required column {col} for symbol {symbol}")
                    return pd.DataFrame()
            
            return data
            
        except Exception as e:
            st.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_current_price(self, symbol):
        """
        Get current/latest available price for a symbol
        
        Args:
            symbol (str): Stock ticker symbol
            
        Returns:
            float: Current price
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Try different price fields
            price_fields = ['currentPrice', 'regularMarketPrice', 'previousClose']
            
            for field in price_fields:
                if field in info and info[field] is not None:
                    return float(info[field])
            
            # If info doesn't work, get latest from history
            hist = ticker.history(period='5d')
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
            
            return None
            
        except Exception as e:
            st.error(f"Error getting current price for {symbol}: {str(e)}")
            return None
    
    def validate_symbol(self, symbol):
        """
        Validate if a stock symbol exists and has data
        
        Args:
            symbol (str): Stock ticker symbol
            
        Returns:
            bool: True if symbol is valid, False otherwise
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Check if we got valid info
            if 'symbol' in info or 'shortName' in info:
                return True
            
            # Try to get recent history as another validation
            hist = ticker.history(period='5d')
            return not hist.empty
            
        except:
            return False
    
    def get_stock_info(self, symbol):
        """
        Get basic information about a stock
        
        Args:
            symbol (str): Stock ticker symbol
            
        Returns:
            dict: Stock information
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': info.get('symbol', symbol),
                'name': info.get('longName', info.get('shortName', 'Unknown')),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange', 'Unknown')
            }
            
        except Exception as e:
            return {
                'symbol': symbol,
                'name': 'Unknown',
                'sector': 'Unknown',
                'industry': 'Unknown', 
                'currency': 'USD',
                'exchange': 'Unknown',
                'error': str(e)
            }
