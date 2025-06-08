import numpy as np
from scipy.optimize import newton
import pandas as pd
from datetime import datetime

class XIRRCalculator:
    """
    Calculate Extended Internal Rate of Return (XIRR) for irregular cash flows
    """
    
    def __init__(self):
        pass
    
    def calculate_xirr(self, cash_flows, dates, guess=0.1):
        """
        Calculate XIRR given cash flows and dates
        
        Args:
            cash_flows (list): List of cash flows (negative for investments, positive for returns)
            dates (list): List of corresponding dates
            guess (float): Initial guess for the rate
            
        Returns:
            float: XIRR as a decimal (e.g., 0.10 for 10%)
        """
        try:
            # Convert dates to days since first date
            first_date = min(dates)
            days = [(date - first_date).days for date in dates]
            
            # Define the NPV function
            def npv(rate):
                return sum(cf / (1 + rate) ** (day / 365.0) for cf, day in zip(cash_flows, days))
            
            # Use Newton's method to find the rate where NPV = 0
            rate = newton(npv, guess, maxiter=1000)
            return rate
            
        except (ValueError, RuntimeError, OverflowError):
            # If calculation fails, return a reasonable estimate
            total_invested = sum(cf for cf in cash_flows if cf < 0)
            total_return = sum(cf for cf in cash_flows if cf > 0)
            
            if total_invested == 0:
                return 0
            
            # Simple annualized return calculation as fallback
            years = (max(dates) - min(dates)).days / 365.0
            if years == 0:
                return 0
                
            simple_return = (total_return / abs(total_invested)) - 1
            return simple_return / years if years > 0 else 0
    
    def prepare_cash_flows_for_xirr(self, investments, current_value, investment_dates, end_date):
        """
        Prepare cash flows for XIRR calculation
        
        Args:
            investments (list): List of investment amounts (positive values)
            current_value (float): Current portfolio value
            investment_dates (list): List of investment dates
            end_date (datetime): End date for analysis
            
        Returns:
            tuple: (cash_flows, dates) ready for XIRR calculation
        """
        cash_flows = []
        dates = []
        
        # Add investment cash flows (negative values)
        for investment, date in zip(investments, investment_dates):
            cash_flows.append(-investment)  # Negative because it's money going out
            dates.append(date)
        
        # Add current value as final cash flow (positive value)
        cash_flows.append(current_value)  # Positive because it's money coming in
        dates.append(end_date)
        
        return cash_flows, dates
    
    def calculate_simple_annualized_return(self, initial_value, final_value, years):
        """
        Calculate simple annualized return
        
        Args:
            initial_value (float): Initial investment value
            final_value (float): Final investment value  
            years (float): Number of years
            
        Returns:
            float: Annualized return as decimal
        """
        if initial_value <= 0 or years <= 0:
            return 0
        
        return (final_value / initial_value) ** (1/years) - 1
