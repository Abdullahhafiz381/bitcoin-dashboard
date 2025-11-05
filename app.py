import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from binance.client import Client
import os

# Mobile-friendly setup
st.set_page_config(
    page_title="Bitcoin Tracker",
    page_icon="₿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Simple mobile styling
st.markdown("""
<style>
    .main > div {
        padding: 0.5rem;
    }
    .stMetric {
        padding: 0.5rem;
    }
    .stTextInput input {
        font-size: 16px; /* Better for mobile */
    }
</style>
""", unsafe_allow_html=True)

class BitcoinTracker:
    def __init__(self):
        self.data_file = "bitcoin_data.csv"
        self.load_data()
    
    def load_data(self):
        """Load historical data"""
        try:
            self.df = pd.read_csv(self.data_file)
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        except:
            self.df = pd.DataFrame(columns=[
                'timestamp', 'total_nodes', 'tor_nodes', 
                'tor_percentage', 'node_trend', 'btc_price'
            ])
    
    def save_data(self):
        """Save data to CSV"""
        try:
            self.df.to_csv(self.data_file, index=False)
        except:
            pass
    
    def get_binance_price(self, api_key, secret_key):
        """Get BTC price from Binance with user API keys"""
        try:
            client = Client(api_key, secret_key)
            ticker = client.get_symbol_ticker(symbol="BTCUSDT")
            return float(ticker['price'])
        except Exception as e:
            st.error(f"Binance API error: {e}")
            # Fallback to public API
            return self.get_public_price()
    
    def get_public_price(self):
        """Fallback price from public API"""
        try:
            response = requests.get(
                "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
                timeout=10
            )
            return float(response.json()['price'])
        except:
            try:
                response = requests.get(
                    "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
                    timeout=10
                )
                return float(response.json()['bitcoin']['usd'])
            except:
                return None
    
    def get_node_data(self):
        """Get Bitcoin node data with proper Tor calculation"""
        try:
            response = requests.get(
                "https://bitnodes.io/api/v1/snapshots/latest/",
                timeout=10
            )
            data = response.json()
            
            total_nodes = data['total_nodes']
            
            # Proper Tor node counting
            tor_nodes = 0
            for node_address, node_info in data['nodes'].items():
                # Check if it's a Tor node (.onion address)
                if '.onion' in str(node_address) or '.onion' in str(node_info):
                    tor_nodes += 1
            
            tor_percentage = (tor_nodes / total_nodes) * 100 if total_nodes > 0 else 0
            
            return {
                'total_nodes': total_nodes,
                'tor_nodes': tor_nodes,
                'tor_percentage': tor_percentage,
                'timestamp': datetime.fromtimestamp(data['timestamp'])
            }
        except Exception as e:
            st.error(f"Node data error: {e}")
            return None
    
    def calculate_trend(self, current_nodes):
        """Calculate trend compared to previous snapshot"""
        if len(self.df) < 1:
            return 0, "→"  # No previous data
        
        previous_nodes = self.df.iloc[-1]['total_nodes']
        
        if previous_nodes == 0:
            return 0, "→"
        
        trend = ((current_nodes - previous_nodes) / previous_nodes) * 100
        direction = "↑" if trend > 0 else "↓" if trend < 0 else "→"
        
        return trend, direction
    
    def update_data(self, api_key, secret_key):
        """Update all data and save new snapshot"""
        # Get current data
        node_data = self.get_node_data()
        btc_price = self.get_binance_price(api_key, secret_key)
        
        if not node_data or btc_price is None:
            return False
        
        # Calculate trend
        trend, direction = self.calculate_trend(node_data['total_nodes'])
        
        # Create new entry
        new_entry = {
            'timestamp': datetime.now(),
            'total_nodes': node_data['total_nodes'],
            'tor_nodes': node_data['tor_nodes'],
            'tor_percentage': round(node_data['tor_percentage'], 2),
            'node_trend': round(trend, 2),
            'btc_price': round(btc_price, 2)
        }
        
        # Add to dataframe
        self.df = pd.concat([self.df, pd.DataFrame([new_entry])], ignore_index=True)
        
        # Keep only last 20 entries
        if len(self.df) > 20:
            self.df = self.df.tail(20)
        
        self.save_data()
        return True

def main():
    st.title("₿ Advanced Bitcoin Tracker")
    st.write("Live network data with Binance API")
    
    # Initialize tracker
    tracker = BitcoinTracker()
    
    # API Key Input Section
    with st.expander("🔑 Binance API Settings", expanded=False):
        st.info("Get API keys from Binance → Settings → API Management")
        
        api_key = st.text_input(
            "Binance API Key",
            type="password",
            placeholder="Enter your Binance API Key"
        )
        
        secret_key = st.text_input(
            "Binance Secret Key", 
            type="password",
            placeholder="Enter your Binance Secret Key"
        )
        
        st.caption("🔒 Keys are not stored. They're only used for this session.")
    
    # Refresh button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Live Metrics")
    with col2:
        if st.button("🔄 Update"):
            if api_key and secret_key:
                with st.spinner("Fetching data..."):
                    if tracker.update_data(api_key, secret_key):
                        st.success("Data updated!")
                        st.rerun()
                    else:
                        st.error("Failed to update data")
            else:
                st.warning("Please enter Binance API keys first")
    
    # Display current data
    if len(tracker.df) > 0:
        latest = tracker.df.iloc[-1]
        
        # Calculate trend for display
        current_trend, trend_direction = tracker.calculate_trend(latest['total_nodes'])
        
        # BTC Price (highlighted)
        st.metric(
            label="BTC Price (Binance)",
            value=f"${latest['btc_price']:,.2f}",
            delta=None
        )
        
        # Network stats in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Total Nodes",
                value=f"{latest['total_nodes']:,}",
                delta=f"{trend_direction} {abs(current_trend):.1f}%"
            )
        
        with col2:
            st.metric(
                label="Tor Nodes",
                value=f"{latest['tor_nodes']:,}",
                delta=None
            )
        
        with col3:
            st.metric(
                label="Tor Percentage", 
                value=f"{latest['tor_percentage']:.1f}%",
                delta=None
            )
    
    # Show historical data if available
    if len(tracker.df) > 1:
        st.markdown("---")
        st.subheader("📈 Historical Trends")
        
        # Simple trend chart
        chart_df = tracker.df.tail(10)  # Last 10 entries
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Avg Tor %",
                f"{chart_df['tor_percentage'].mean():.1f}%"
            )
        
        with col2:
            st.metric(
                "Avg Trend", 
                f"{chart_df['node_trend'].mean():.1f}%"
            )
        
        # Data table
        with st.expander("View Raw Data"):
            display_df = tracker.df.copy()
            display_df['timestamp'] = display_df['timestamp'].dt.strftime('%m/%d %H:%M')
            display_df = display_df.rename(columns={
                'timestamp': 'Time',
                'total_nodes': 'Nodes',
                'tor_nodes': 'Tor',
                'tor_percentage': 'Tor %',
                'node_trend': 'Trend %',
                'btc_price': 'Price'
            })
            
            st.dataframe(
                display_df[['Time', 'Nodes', 'Tor %', 'Trend %', 'Price']].sort_values('Time', ascending=False),
                use_container_width=True
            )
    
    # Last update time
    st.markdown("---")
    if len(tracker.df) > 0:
        last_time = tracker.df.iloc[-1]['timestamp']
        if isinstance(last_time, str):
            last_time = pd.to_datetime(last_time)
        st.caption(f"📱 Last update: {last_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.caption("📱 No data yet. Enter API keys and click Update.")
    
    # Info section
    with st.expander("ℹ️ About this app"):
        st.markdown("""
        **What this tracks:**
        - **BTC Price**: From your Binance account (real-time)
        - **Total Nodes**: All Bitcoin network nodes
        - **Tor Nodes**: Nodes using Tor for privacy
        - **Tor Percentage**: (Tor Nodes / Total Nodes) × 100
        - **Node Trend**: % change from previous snapshot
        
        **How to get Binance API keys:**
        1. Go to Binance.com → Settings → API Management
        2. Create new API key
        3. Enable Spot & Margin Trading permissions
        4. Copy keys here
        
        **Data Sources:**
        - Bitnodes.io for node data
        - Binance API for price data
        
        🔒 Your API keys are only used for price data and not stored.
        """)

if __name__ == "__main__":
    main()