import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from utils.xirr_calculator import XIRRCalculator

class PerformanceAnalyzer:
    """
    Analyze investment performance for different strategies
    """
    
    def __init__(self):
        self.xirr_calculator = XIRRCalculator()
    
    def generate_thursdays(self, start_date, end_date):
        """
        Generate all Thursday dates between start_date and end_date
        
        Args:
            start_date (datetime.date): Start date
            end_date (datetime.date): End date
            
        Returns:
            list: List of Thursday dates
        """
        thursdays = []
        
        # Convert to datetime if needed
        if isinstance(start_date, date):
            current_date = datetime.combine(start_date, datetime.min.time())
        else:
            current_date = start_date
            
        if isinstance(end_date, date):
            end_datetime = datetime.combine(end_date, datetime.min.time())
        else:
            end_datetime = end_date
        
        # Find the first Thursday on or after start_date
        # Thursday is weekday 3 (Monday is 0)
        days_until_thursday = (3 - current_date.weekday()) % 7
        if days_until_thursday == 0 and current_date.weekday() != 3:
            days_until_thursday = 7
        
        first_thursday = current_date + timedelta(days=days_until_thursday)
        
        # Generate all Thursdays
        current_thursday = first_thursday
        while current_thursday <= end_datetime:
            thursdays.append(current_thursday.date())
            current_thursday += timedelta(weeks=1)
        
        return thursdays
    
    def analyze_investment_strategy(self, stock_data, investment_dates, investment_amount, symbol):
        """
        Analyze a dollar-cost averaging investment strategy
        
        Args:
            stock_data (pd.DataFrame): Historical stock price data
            investment_dates (list): List of investment dates
            investment_amount (float): Amount invested each period
            symbol (str): Stock symbol for reference
            
        Returns:
            dict: Analysis results including XIRR, total return, etc.
        """
        investments = []
        shares_purchased = []
        portfolio_timeline = []
        
        total_shares = 0
        total_invested = 0
        
        # Process each investment date
        for inv_date in investment_dates:
            # Find the closest trading day price
            price = self._get_price_for_date(stock_data, inv_date)
            
            if price is not None and price > 0:
                shares_bought = investment_amount / price
                total_shares += shares_bought
                total_invested += investment_amount
                
                investments.append(investment_amount)
                shares_purchased.append(shares_bought)
                
                # Calculate portfolio value at this point
                portfolio_value = total_shares * price
                
                portfolio_timeline.append({
                    'date': inv_date,
                    'investment_amount': investment_amount,
                    'price': price,
                    'shares_bought': shares_bought,
                    'total_shares': total_shares,
                    'cumulative_invested': total_invested,
                    'portfolio_value': portfolio_value,
                    f'{symbol.lower()}_price': price
                })
        
        # Get current/final price
        current_price = stock_data['Close'].iloc[-1] if not stock_data.empty else 0
        current_value = total_shares * current_price
        
        # Calculate XIRR
        if len(investments) > 0:
            # Prepare cash flows for XIRR calculation
            cash_flows = [-amt for amt in investments]  # Negative for investments
            cash_flows.append(current_value)  # Positive for current value
            
            # Prepare dates for XIRR
            dates = investment_dates.copy()
            dates.append(stock_data.index[-1].date() if not stock_data.empty else investment_dates[-1])
            
            xirr = self.xirr_calculator.calculate_xirr(cash_flows, dates)
        else:
            xirr = 0
        
        # Create portfolio timeline DataFrame
        portfolio_df = pd.DataFrame(portfolio_timeline)
        
        # Calculate additional metrics
        average_cost_per_share = total_invested / total_shares if total_shares > 0 else 0
        total_return_pct = ((current_value / total_invested) - 1) * 100 if total_invested > 0 else 0
        
        # Create cash flows summary for display
        cash_flows_df = pd.DataFrame({
            'date': investment_dates,
            'amount': [-amt for amt in investments],
            'type': ['Investment'] * len(investments)
        })
        
        # Add final value row
        final_row = pd.DataFrame({
            'date': [stock_data.index[-1].date() if not stock_data.empty else investment_dates[-1]],
            'amount': [current_value],
            'type': ['Current Value']
        })
        
        cash_flows_df = pd.concat([cash_flows_df, final_row], ignore_index=True)
        
        return {
            'symbol': symbol,
            'total_invested': total_invested,
            'total_shares': total_shares,
            'current_price': current_price,
            'current_value': current_value,
            'average_cost_per_share': average_cost_per_share,
            'total_return_pct': total_return_pct,
            'xirr': xirr,
            'investments': investments,
            'shares_purchased': shares_purchased,
            'portfolio_timeline': portfolio_df,
            'cash_flows': cash_flows_df,
            'number_of_investments': len(investments)
        }
    
    def _get_price_for_date(self, stock_data, target_date):
        """
        Get stock price for a specific date, or closest available trading day
        
        Args:
            stock_data (pd.DataFrame): Stock price data
            target_date (datetime.date): Target date
            
        Returns:
            float: Stock price for the date
        """
        if stock_data.empty:
            return None
        
        # Convert target_date to datetime if it's a date
        if isinstance(target_date, date):
            target_datetime = datetime.combine(target_date, datetime.min.time())
        else:
            target_datetime = target_date
        
        # Convert stock_data index to dates for comparison
        stock_dates = [d.date() for d in stock_data.index]
        
        # Try exact match first
        if target_date in stock_dates:
            matching_datetime = datetime.combine(target_date, datetime.min.time())
            # Find the row with matching date
            for i, stock_datetime in enumerate(stock_data.index):
                if stock_datetime.date() == target_date:
                    return stock_data['Close'].iloc[i]
        
        # If no exact match, find the closest previous trading day
        available_dates = [d for d in stock_dates if d <= target_date]
        
        if available_dates:
            closest_date = max(available_dates)
            # Find the row with the closest date
            for i, stock_datetime in enumerate(stock_data.index):
                if stock_datetime.date() == closest_date:
                    return stock_data['Close'].iloc[i]
        
        # If no previous date available, use the first available date
        if stock_dates:
            first_date = min(stock_dates)
            for i, stock_datetime in enumerate(stock_data.index):
                if stock_datetime.date() == first_date:
                    return stock_data['Close'].iloc[i]
        
        return None
    
    def compare_strategies(self, strategy1_results, strategy2_results):
        """
        Compare two investment strategies
        
        Args:
            strategy1_results (dict): Results from first strategy
            strategy2_results (dict): Results from second strategy
            
        Returns:
            dict: Comparison results
        """
        return {
            'strategy1_symbol': strategy1_results['symbol'],
            'strategy2_symbol': strategy2_results['symbol'],
            'value_difference': strategy2_results['current_value'] - strategy1_results['current_value'],
            'return_difference_pct': strategy2_results['total_return_pct'] - strategy1_results['total_return_pct'],
            'xirr_difference': strategy2_results['xirr'] - strategy1_results['xirr'],
            'better_strategy': strategy2_results['symbol'] if strategy2_results['xirr'] > strategy1_results['xirr'] else strategy1_results['symbol'],
            'outperformance_pct': ((strategy2_results['current_value'] / strategy1_results['current_value']) - 1) * 100
        }
