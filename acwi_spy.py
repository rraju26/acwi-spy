
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, date
from utils.data_fetcher import DataFetcher
from utils.xirr_calculator import XIRRCalculator
from utils.performance_analyzer import PerformanceAnalyzer

# Page configuration
st.set_page_config(
    page_title="ACWI vs S&P 500 Investment Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("📊 ACWI vs S&P 500 Investment Analysis Tool")
st.markdown("""
This tool analyzes the performance of weekly $1,000 ACWI purchases every Thursday compared to an equivalent S&P 500 (SPY) investment strategy.
Calculate XIRR, compare returns, and visualize your investment performance over time.
""")

# Sidebar for inputs
st.sidebar.header("Investment Parameters")

# Date range selection
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input(
        "Start Date",
        value=date(2025, 1, 1),
        min_value=date(2010, 1, 1),
        max_value=date.today()
    )

with col2:
    end_date = st.date_input(
        "End Date",
        value=date.today(),
        min_value=start_date,
        max_value=date.today()
    )

# Investment amount
investment_amount = st.sidebar.number_input(
    "Weekly Investment Amount ($)",
    min_value=100,
    max_value=10000,
    value=1000,
    step=100
)

# Analysis button
analyze_button = st.sidebar.button("🔍 Run Analysis", type="primary")

# Initialize session state
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None

# Main analysis
if analyze_button:
    if start_date >= end_date:
        st.error("Start date must be before end date.")
    else:
        with st.spinner("Fetching market data and performing analysis..."):
            try:
                # Initialize components
                data_fetcher = DataFetcher()
                xirr_calculator = XIRRCalculator()
                performance_analyzer = PerformanceAnalyzer()
                
                # Fetch historical data
                acwi_data = data_fetcher.fetch_stock_data('ACWI', start_date, end_date)
                spy_data = data_fetcher.fetch_stock_data('SPY', start_date, end_date)
                
                if acwi_data.empty or spy_data.empty:
                    st.error("Unable to fetch stock data. Please check your internet connection and try again.")
                else:
                    # Generate investment schedules (every Thursday)
                    investment_dates = performance_analyzer.generate_thursdays(start_date, end_date)
                    
                    # Calculate ACWI strategy performance
                    acwi_analysis = performance_analyzer.analyze_investment_strategy(
                        acwi_data, investment_dates, investment_amount, 'ACWI'
                    )
                    
                    # Calculate SPY strategy performance
                    spy_analysis = performance_analyzer.analyze_investment_strategy(
                        spy_data, investment_dates, investment_amount, 'SPY'
                    )
                    
                    # Store results in session state
                    st.session_state.analysis_data = {
                        'acwi_analysis': acwi_analysis,
                        'spy_analysis': spy_analysis,
                        'acwi_data': acwi_data,
                        'spy_data': spy_data,
                        'investment_dates': investment_dates,
                        'investment_amount': investment_amount,
                        'start_date': start_date,
                        'end_date': end_date
                    }
                    st.session_state.analysis_complete = True
                    
            except Exception as e:
                st.error(f"An error occurred during analysis: {str(e)}")
                st.session_state.analysis_complete = False

# Display results if analysis is complete
if st.session_state.analysis_complete and st.session_state.analysis_data:
    data = st.session_state.analysis_data
    acwi_analysis = data['acwi_analysis']
    spy_analysis = data['spy_analysis']
    
    # Key Metrics Section
    st.header("📈 Key Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Invested",
            f"${acwi_analysis['total_invested']:,.2f}",
            delta=None
        )
    
    with col2:
        st.metric(
            "ACWI Current Value",
            f"${acwi_analysis['current_value']:,.2f}",
            delta=f"${acwi_analysis['current_value'] - acwi_analysis['total_invested']:,.2f}"
        )
    
    with col3:
        st.metric(
            "SPY Current Value",
            f"${spy_analysis['current_value']:,.2f}",
            delta=f"${spy_analysis['current_value'] - spy_analysis['total_invested']:,.2f}"
        )
    
    with col4:
        difference = spy_analysis['current_value'] - acwi_analysis['current_value']
        st.metric(
            "SPY vs ACWI Difference",
            f"${difference:,.2f}",
            delta=f"{(difference/acwi_analysis['current_value']*100):+.2f}%"
        )
    
    # XIRR Comparison
    st.header("💰 Annualized Returns (XIRR)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "ACWI XIRR",
            f"{acwi_analysis['xirr']*100:.2f}%"
        )
    
    with col2:
        st.metric(
            "SPY XIRR",
            f"{spy_analysis['xirr']*100:.2f}%"
        )
    
    with col3:
        xirr_diff = (spy_analysis['xirr'] - acwi_analysis['xirr']) * 100
        st.metric(
            "XIRR Difference",
            f"{xirr_diff:+.2f}%",
            delta=f"SPY {'outperforms' if xirr_diff > 0 else 'underperforms'} ACWI"
        )
    
    # Investment Timeline Chart
    st.header("📊 Portfolio Value Over Time")
    
    # Create cumulative portfolio value chart
    fig_portfolio = go.Figure()
    
    # Add ACWI portfolio value
    fig_portfolio.add_trace(go.Scatter(
        x=acwi_analysis['portfolio_timeline']['date'],
        y=acwi_analysis['portfolio_timeline']['portfolio_value'],
        mode='lines',
        name='ACWI Portfolio',
        line=dict(color='#1f77b4', width=3)
    ))
    
    # Add SPY portfolio value
    fig_portfolio.add_trace(go.Scatter(
        x=spy_analysis['portfolio_timeline']['date'],
        y=spy_analysis['portfolio_timeline']['portfolio_value'],
        mode='lines',
        name='SPY Portfolio',
        line=dict(color='#ff7f0e', width=3)
    ))
    
    # Add cumulative investment line
    fig_portfolio.add_trace(go.Scatter(
        x=acwi_analysis['portfolio_timeline']['date'],
        y=acwi_analysis['portfolio_timeline']['cumulative_invested'],
        mode='lines',
        name='Cumulative Invested',
        line=dict(color='gray', width=2, dash='dash')
    ))
    
    fig_portfolio.update_layout(
        title="Portfolio Value Comparison Over Time",
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig_portfolio, use_container_width=True)
    
    # Price Performance Chart
    st.header("📈 Stock Price Performance")
    
    fig_prices = go.Figure()
    
    # Normalize prices to start at 100
    acwi_normalized = (data['acwi_data']['Close'] / data['acwi_data']['Close'].iloc[0]) * 100
    spy_normalized = (data['spy_data']['Close'] / data['spy_data']['Close'].iloc[0]) * 100
    
    fig_prices.add_trace(go.Scatter(
        x=data['acwi_data'].index,
        y=acwi_normalized,
        mode='lines',
        name='ACWI (Normalized)',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig_prices.add_trace(go.Scatter(
        x=data['spy_data'].index,
        y=spy_normalized,
        mode='lines',
        name='SPY (Normalized)',
        line=dict(color='#ff7f0e', width=2)
    ))
    
    fig_prices.update_layout(
        title="Stock Price Performance (Normalized to 100 at Start)",
        xaxis_title="Date",
        yaxis_title="Normalized Price",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig_prices, use_container_width=True)
    
    # Detailed Statistics
    st.header("📋 Detailed Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("ACWI Strategy Details")
        st.write(f"**Total Investments:** {len(data['investment_dates'])}")
        st.write(f"**Total Shares Owned:** {acwi_analysis['total_shares']:.2f}")
        st.write(f"**Average Cost per Share:** ${acwi_analysis['average_cost_per_share']:.2f}")
        st.write(f"**Current Price:** ${acwi_analysis['current_price']:.2f}")
        st.write(f"**Total Return:** ${acwi_analysis['current_value'] - acwi_analysis['total_invested']:,.2f}")
        st.write(f"**Total Return %:** {((acwi_analysis['current_value'] / acwi_analysis['total_invested']) - 1) * 100:.2f}%")
    
    with col2:
        st.subheader("SPY Strategy Details")
        st.write(f"**Total Investments:** {len(data['investment_dates'])}")
        st.write(f"**Total Shares Owned:** {spy_analysis['total_shares']:.2f}")
        st.write(f"**Average Cost per Share:** ${spy_analysis['average_cost_per_share']:.2f}")
        st.write(f"**Current Price:** ${spy_analysis['current_price']:.2f}")
        st.write(f"**Total Return:** ${spy_analysis['current_value'] - spy_analysis['total_invested']:,.2f}")
        st.write(f"**Total Return %:** {((spy_analysis['current_value'] / spy_analysis['total_invested']) - 1) * 100:.2f}%")
    
    # Cash Flow Table
    st.header("💵 Investment Cash Flow Summary")
    
    # Show first 10 and last 10 investments
    cash_flows = acwi_analysis['cash_flows']
    if len(cash_flows) > 20:
        display_flows = pd.concat([
            cash_flows.head(10),
            pd.DataFrame({'date': ['...'], 'amount': ['...'], 'type': ['...']}),
            cash_flows.tail(10)
        ]).reset_index(drop=True)
    else:
        display_flows = cash_flows
    
    st.dataframe(display_flows, use_container_width=True)
    
    # Download data option
    st.header("📥 Export Data")
    
    # Prepare data for download
    export_data = {
        'Investment Date': data['investment_dates'],
        'ACWI Price': [acwi_analysis['portfolio_timeline']['acwi_price'][i] for i in range(len(data['investment_dates']))],
        'SPY Price': [spy_analysis['portfolio_timeline']['spy_price'][i] for i in range(len(data['investment_dates']))],
        'ACWI Shares Bought': [data['investment_amount'] / price for price in [acwi_analysis['portfolio_timeline']['acwi_price'][i] for i in range(len(data['investment_dates']))]],
        'SPY Shares Bought': [data['investment_amount'] / price for price in [spy_analysis['portfolio_timeline']['spy_price'][i] for i in range(len(data['investment_dates']))]],
    }
    
    export_df = pd.DataFrame(export_data)
    csv = export_df.to_csv(index=False)
    
    st.download_button(
        label="Download Investment Data as CSV",
        data=csv,
        file_name=f"investment_analysis_{data['start_date']}_{data['end_date']}.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown("""
**Disclaimer:** This tool is for educational and informational purposes only. Past performance does not guarantee future results. 
Please consult with a financial advisor before making investment decisions.
""")
