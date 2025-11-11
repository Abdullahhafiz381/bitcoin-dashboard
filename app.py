import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import json

# Page configuration
st.set_page_config(
    page_title="Abdullah's Bitnode Tracker",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for futuristic design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');
    
    .main {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
        color: #ffffff;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    .header {
        font-family: 'Orbitron', sans-serif;
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(45deg, #00ffff, #ff00ff, #00ff00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
    }
    
    .subheader {
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.2rem;
        color: #8892b0;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .signal-card {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid #00ffff;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
        backdrop-filter: blur(10px);
    }
    
    .buy-signal {
        border-color: #00ff00;
        box-shadow: 0 0 25px rgba(0, 255, 0, 0.3);
        background: rgba(0, 255, 0, 0.05);
    }
    
    .sell-signal {
        border-color: #ff4444;
        box-shadow: 0 0 25px rgba(255, 68, 68, 0.3);
        background: rgba(255, 68, 68, 0.05);
    }
    
    .neutral-signal {
        border-color: #ffaa00;
        box-shadow: 0 0 25px rgba(255, 170, 0, 0.3);
        background: rgba(255, 170, 0, 0.05);
    }
    
    .refresh-btn {
        background: linear-gradient(45deg, #00ffff, #0077ff);
        border: none;
        color: white;
        padding: 12px 30px;
        border-radius: 25px;
        font-family: 'Rajdhani', sans-serif;
        font-weight: 700;
        font-size: 1.1rem;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
    }
    
    .refresh-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 30px rgba(0, 255, 255, 0.6);
    }
    
    .node-stats {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(0, 255, 255, 0.3);
    }
    
    .price-positive {
        color: #00ff00;
        font-weight: bold;
    }
    
    .price-negative {
        color: #ff4444;
        font-weight: bold;
    }
    
    .metric-value {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.4rem;
        font-weight: 700;
        color: #00ffff;
    }
    
    .metric-label {
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.9rem;
        color: #8892b0;
    }
</style>
""", unsafe_allow_html=True)

class BitnodeTracker:
    def __init__(self):
        self.coins = ['bitcoin', 'ethereum', 'litecoin', 'bitcoin-cash', 'solana', 
                     'cardano', 'avalanche-2', 'dogecoin', 'polkadot', 'chainlink', 'binancecoin']
        self.coin_names = ['BTC', 'ETH', 'LTC', 'BCH', 'SOL', 'ADA', 'AVAX', 'DOGE', 'DOT', 'LINK', 'BNB']
        
    def get_bitnodes_data(self):
        """Fetch real Bitnodes.io data"""
        try:
            # Current snapshot
            current_url = "https://bitnodes.io/api/v1/snapshots/latest/"
            current_response = requests.get(current_url, timeout=10)
            current_data = current_response.json()
            
            # Previous snapshot (24 hours ago)
            previous_timestamp = current_data['timestamp'] - 86400  # 24 hours in seconds
            previous_url = f"https://bitnodes.io/api/v1/snapshots/{previous_timestamp}/"
            previous_response = requests.get(previous_url, timeout=10)
            previous_data = previous_response.json() if previous_response.status_code == 200 else current_data
            
            return current_data, previous_data
        except Exception as e:
            st.error(f"Error fetching Bitnodes data: {e}")
            return None, None
    
    def calculate_tor_trend(self, current_data, previous_data):
        """Calculate Tor Trend signal"""
        try:
            current_tor_nodes = sum(1 for node in current_data['nodes'].values() 
                                  if isinstance(node, list) and len(node) > 7 and node[7] == 'Tor')
            previous_tor_nodes = sum(1 for node in previous_data['nodes'].values() 
                                   if isinstance(node, list) and len(node) > 7 and node[7] == 'Tor')
            
            current_total = len(current_data['nodes'])
            previous_total = len(previous_data['nodes'])
            
            current_tor_pct = (current_tor_nodes / current_total) * 100
            previous_tor_pct = (previous_tor_nodes / previous_total) * 100
            
            tor_trend = ((current_tor_pct - previous_tor_pct) / previous_tor_pct) * 100 if previous_tor_pct > 0 else 0
            
            return {
                'current_tor': current_tor_nodes,
                'previous_tor': previous_tor_nodes,
                'current_total': current_total,
                'previous_total': previous_total,
                'tor_trend': tor_trend,
                'signal': 'SELL' if tor_trend > 0.1 else 'BUY' if tor_trend < -0.1 else 'NEUTRAL'
            }
        except Exception as e:
            st.error(f"Error calculating Tor trend: {e}")
            return None
    
    def calculate_network_signal(self, current_data, previous_data):
        """Calculate Network Signal"""
        try:
            current_total = len(current_data['nodes'])
            previous_total = len(previous_data['nodes'])
            
            # Calculate active nodes (nodes that responded recently)
            current_active = sum(1 for node in current_data['nodes'].values() 
                               if isinstance(node, list) and len(node) > 2 and node[2] == 1)
            
            node_growth = (current_total - previous_total) / previous_total if previous_total > 0 else 0
            active_ratio = current_active / current_total if current_total > 0 else 0
            
            signal = active_ratio * node_growth
            
            return {
                'current_active': current_active,
                'current_total': current_total,
                'previous_total': previous_total,
                'node_growth': node_growth,
                'active_ratio': active_ratio,
                'signal_value': signal,
                'signal': 'BUY' if signal > 0.01 else 'SELL' if signal < -0.01 else 'SIDEWAYS'
            }
        except Exception as e:
            st.error(f"Error calculating network signal: {e}")
            return None
    
    def get_coingecko_prices(self):
        """Fetch real-time prices from CoinGecko"""
        try:
            coin_ids = ','.join(self.coins)
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_ids}&vs_currencies=usd&include_24h_change=true"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            prices = []
            for i, coin_id in enumerate(self.coins):
                if coin_id in data:
                    prices.append({
                        'coin': self.coin_names[i],
                        'price': data[coin_id]['usd'],
                        'change_24h': data[coin_id]['usd_24h_change'],
                        'time': datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
            return prices
        except Exception as e:
            st.error(f"Error fetching price data: {e}")
            return None

def main():
    # Initialize tracker
    tracker = BitnodeTracker()
    
    # Header
    st.markdown('<div class="header">Abdullah\'s Bitnode Tracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="subheader">Professional Cryptocurrency Trading Signals Powered by Bitcoin Network Metrics</div>', unsafe_allow_html=True)
    
    # Refresh button at top
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button('🔄 REFRESH DATA', key='refresh', use_container_width=True):
            st.rerun()
    
    # Auto-refresh every 5 minutes
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    if time.time() - st.session_state.last_refresh > 300:  # 5 minutes
        st.session_state.last_refresh = time.time()
        st.rerun()
    
    # Fetch data
    with st.spinner('🔄 Fetching real-time network data...'):
        current_data, previous_data = tracker.get_bitnodes_data()
        prices = tracker.get_coingecko_prices()
    
    if current_data and previous_data and prices:
        # Calculate signals
        tor_data = tracker.calculate_tor_trend(current_data, previous_data)
        network_data = tracker.calculate_network_signal(current_data, previous_data)
        
        if tor_data and network_data:
            # Determine master BTC signal
            btc_signal = network_data['signal']  # Primary signal from network metrics
            
            # Display node statistics
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="node-stats">
                    <div class="metric-label">Total Nodes</div>
                    <div class="metric-value">{network_data['current_total']:,}</div>
                    <div style="color: {'#00ff00' if network_data['current_total'] > network_data['previous_total'] else '#ff4444'}">
                        {('📈' if network_data['current_total'] > network_data['previous_total'] else '📉')} 
                        {abs(network_data['node_growth']*100):.2f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="node-stats">
                    <div class="metric-label">Active Nodes</div>
                    <div class="metric-value">{network_data['current_active']:,}</div>
                    <div class="metric-label">{network_data['active_ratio']*100:.1f}% of total</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="node-stats">
                    <div class="metric-label">Tor Nodes</div>
                    <div class="metric-value">{tor_data['current_tor']:,}</div>
                    <div style="color: {'#ff4444' if tor_data['tor_trend'] > 0 else '#00ff00'}">
                        {('📈' if tor_data['tor_trend'] > 0 else '📉')} 
                        {abs(tor_data['tor_trend']):.2f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="node-stats">
                    <div class="metric-label">Network Signal</div>
                    <div class="metric-value" style="color: {'#00ff00' if btc_signal == 'BUY' else '#ff4444' if btc_signal == 'SELL' else '#ffaa00'}">
                        {btc_signal}
                    </div>
                    <div class="metric-label">Strength: {abs(network_data['signal_value']*100):.3f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Display trading signals
            st.markdown("---")
            st.markdown("### 🎯 LIVE TRADING SIGNALS")
            
            # BTC first as master signal
            btc_price = next((p for p in prices if p['coin'] == 'BTC'), None)
            if btc_price:
                signal_class = "buy-signal" if btc_signal == "BUY" else "sell-signal" if btc_signal == "SELL" else "neutral-signal"
                
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                with col1:
                    st.markdown(f"<h3>🎯 BITCOIN (BTC) - MASTER SIGNAL</h3>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<h3 style='color: {'#00ff00' if btc_signal == 'BUY' else '#ff4444' if btc_signal == 'SELL' else '#ffaa00'}'>{btc_signal}</h3>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<h3>${btc_price['price']:,.2f}</h3>", unsafe_allow_html=True)
                with col4:
                    change_color = "price-positive" if btc_price['change_24h'] > 0 else "price-negative"
                    st.markdown(f"<h3 class='{change_color}'>{btc_price['change_24h']:+.2f}%</h3>", unsafe_allow_html=True)
                with col5:
                    st.markdown(f"<h3>{btc_price['time']}</h3>", unsafe_allow_html=True)
            
            # Altcoins following BTC signal
            st.markdown("### 🔄 FOLLOWING COINS (Mirroring BTC Signal)")
            
            for price_data in prices:
                if price_data['coin'] != 'BTC':
                    signal_class = "buy-signal" if btc_signal == "BUY" else "sell-signal" if btc_signal == "SELL" else "neutral-signal"
                    
                    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                    with col1:
                        st.markdown(f"<h4>{price_data['coin']}</h4>", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"<h4 style='color: {'#00ff00' if btc_signal == 'BUY' else '#ff4444' if btc_signal == 'SELL' else '#ffaa00'}'>{btc_signal}</h4>", unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"<h4>${price_data['price']:,.2f}</h4>", unsafe_allow_html=True)
                    with col4:
                        change_color = "price-positive" if price_data['change_24h'] > 0 else "price-negative"
                        st.markdown(f"<h4 class='{change_color}'>{price_data['change_24h']:+.2f}%</h4>", unsafe_allow_html=True)
                    with col5:
                        st.markdown(f"<h4>{price_data['time']}</h4>", unsafe_allow_html=True)
            
if __name__ == "__main__":
    main()