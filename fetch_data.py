import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time

# ============================================
# DASHBOARD DATA FETCHER
# ============================================

def get_stock_data(ticker, period='3mo'):
    """Get all data needed for dashboard"""
    stock = yf.Ticker(ticker)
    
    # Get historical data
    hist = stock.history(period=period)
    
    # Calculate moving averages
    hist['MA20'] = hist['Close'].rolling(window=20).mean()
    hist['MA50'] = hist['Close'].rolling(window=50).mean()
    
    # Get current info
    info = stock.info
    
    current_data = {
        'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
        'change': info.get('regularMarketChange', 0),
        'change_pct': info.get('regularMarketChangePercent', 0),
        'volume': info.get('volume', 0),
        'market_cap': info.get('marketCap', 0),
        'pe_ratio': info.get('trailingPE', 0),
        'day_high': info.get('dayHigh', 0),
        'day_low': info.get('dayLow', 0)
    }
    
    return hist, current_data


def create_dashboard(tickers):
    """Create interactive dashboard HTML"""
    
    # Start HTML
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Stock Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            h1 {
                color: white;
                text-align: center;
                font-size: 3em;
                margin-bottom: 10px;
            }
            .subtitle {
                color: rgba(255,255,255,0.8);
                text-align: center;
                margin-bottom: 30px;
            }
            .cards {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .card {
                background: white;
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            .stock-name {
                font-size: 1.5em;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
            }
            .price {
                font-size: 2.5em;
                font-weight: bold;
                color: #667eea;
            }
            .change {
                font-size: 1.2em;
                margin-top: 5px;
            }
            .positive { color: #10b981; }
            .negative { color: #ef4444; }
            .stats {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                margin-top: 15px;
                font-size: 0.9em;
            }
            .stat-label {
                color: #666;
            }
            .stat-value {
                font-weight: bold;
                color: #333;
            }
            .chart-container {
                background: white;
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            .update-time {
                text-align: center;
                color: white;
                margin-top: 20px;
                font-size: 0.9em;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📈 Live Stock Dashboard</h1>
            <div class="subtitle">Real-time market data and analysis</div>
            
            <div class="cards">
    """
    
    # Create cards for each stock
    for ticker in tickers:
        hist, current = get_stock_data(ticker)
        
        change_class = "positive" if current['change'] >= 0 else "negative"
        change_sign = "+" if current['change'] >= 0 else ""
        
        # Format large numbers
        def format_number(num):
            if num >= 1e12:
                return f"${num/1e12:.2f}T"
            elif num >= 1e9:
                return f"${num/1e9:.2f}B"
            elif num >= 1e6:
                return f"${num/1e6:.2f}M"
            else:
                return f"${num:,.0f}"
        
        html += f"""
            <div class="card">
                <div class="stock-name">{ticker}</div>
                <div class="price">${current['price']:.2f}</div>
                <div class="change {change_class}">
                    {change_sign}${current['change']:.2f} ({change_sign}{current['change_pct']:.2f}%)
                </div>
                <div class="stats">
                    <div><span class="stat-label">Volume:</span></div>
                    <div class="stat-value">{current['volume']:,}</div>
                    
                    <div><span class="stat-label">Market Cap:</span></div>
                    <div class="stat-value">{format_number(current['market_cap'])}</div>
                    
                    <div><span class="stat-label">Day Range:</span></div>
                    <div class="stat-value">${current['day_low']:.2f} - ${current['day_high']:.2f}</div>
                    
                    <div><span class="stat-label">P/E Ratio:</span></div>
                    <div class="stat-value">{current['pe_ratio']:.2f}</div>
                </div>
            </div>
        """
    
    html += """
            </div>
    """
    
    # Create charts for each stock
    for ticker in tickers:
        hist, current = get_stock_data(ticker)
        
        # Create candlestick chart with moving averages
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{ticker} Price & Moving Averages', 'Volume')
        )
        
        # Candlestick
        fig.add_trace(
            go.Candlestick(
                x=hist.index,
                open=hist['Open'],
                high=hist['High'],
                low=hist['Low'],
                close=hist['Close'],
                name='Price'
            ),
            row=1, col=1
        )
        
        # Moving averages
        fig.add_trace(
            go.Scatter(x=hist.index, y=hist['MA20'], name='MA20', 
                      line=dict(color='orange', width=2)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=hist.index, y=hist['MA50'], name='MA50',
                      line=dict(color='blue', width=2)),
            row=1, col=1
        )
        
        # Volume bars
        colors = ['red' if hist['Close'].iloc[i] < hist['Open'].iloc[i] 
                 else 'green' for i in range(len(hist))]
        fig.add_trace(
            go.Bar(x=hist.index, y=hist['Volume'], name='Volume',
                  marker_color=colors),
            row=2, col=1
        )
        
        fig.update_layout(
            height=600,
            showlegend=True,
            xaxis_rangeslider_visible=False,
            template='plotly_white'
        )
        
        chart_html = fig.to_html(include_plotlyjs=False, div_id=f'chart_{ticker}')
        
        html += f"""
            <div class="chart-container">
                {chart_html}
            </div>
        """
    
    # Close HTML
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html += f"""
            <div class="update-time">
                Last updated: {current_time}
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    print("🚀 Creating your stock dashboard...")
    
    tickers = ['AAPL', 'GOOGL', 'TSLA']
    
    # Generate dashboard
    dashboard_html = create_dashboard(tickers)
    
    # Save to file
    with open('dashboard.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    
    print("✅ Dashboard created successfully!")
    print("📁 Open 'dashboard.html' in your browser to view it")
    print("\nTo add more stocks, edit the 'tickers' list in the code")
    
    # Optional: Auto-refresh version
    print("\n" + "="*50)
    print("Want auto-refresh? Press Enter to start (Ctrl+C to stop)")
    input()
    
    try:
        while True:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Updating dashboard...")
            dashboard_html = create_dashboard(tickers)
            with open('dashboard.html', 'w', encoding='utf-8') as f:
                f.write(dashboard_html)
            print("✅ Updated! Refresh your browser to see changes")
            time.sleep(30)  # Update every 30 seconds
    except KeyboardInterrupt:
        print("\n👋 Dashboard monitoring stopped")


