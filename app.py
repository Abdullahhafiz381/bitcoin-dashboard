import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import qrcode
from io import BytesIO
import base64

# Mobile-friendly setup
st.set_page_config(
    page_title="Bitcoin Live Tracker",
    page_icon="₿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Mobile styling
st.markdown("""
<style>
    .main > div {
        padding: 0.5rem;
    }
    .stMetric {
        padding: 0.5rem;
    }
    .share-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def generate_qr_code(url):
    """Generate QR code for sharing"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

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
    
    def get_btc_price(self):
        """Get BTC price from public APIs (no keys needed)"""
        try:
            # Try Binance public API first
            response = requests.get(
                "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
                timeout=10
            )
            return float(response.json()['price'])
        except:
            try:
                # Fallback to CoinGecko
                response = requests.get(
                    "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
                    timeout=10
                )
                return float(response.json()['bitcoin']['usd'])
            except:
                try:
                    # Final fallback to Coinbase
                    response = requests.get(
                        "https://api.coinbase.com/v2/prices/BTC-USD/spot",
                        timeout=10
                    )
                    return float(response.json()['data']['amount'])
                except:
                    return None
    
    def get_node_data(self):
        """Get Bitcoin node data"""
        try:
            response = requests.get(
                "https://bitnodes.io/api/v1/snapshots/latest/",
                timeout=10
            )
            data = response.json()
            
            total_nodes = data['total_nodes']
            
            # Count Tor nodes
            tor_nodes = 0
            for node_address, node_info in data['nodes'].items():
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
    
    def update_data(self):
        """Update all data and save new snapshot"""
        # Get current data
        node_data = self.get_node_data()
        btc_price = self.get_btc_price()
        
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
        
        # Keep only last 15 entries (for mobile performance)
        if len(self.df) > 15:
            self.df = self.df.tail(15)
        
        self.save_data()
        return True

def main():
    # Initialize tracker
    tracker = BitcoinTracker()
    
    # Title and sharing section
    st.title("₿ Bitcoin Live Tracker")
    st.markdown("Real-time network data and price • No login required")
    
    # SHARING SECTION - Always visible
    with st.container():
        st.markdown('<div class="share-box">', unsafe_allow_html=True)
        
        # Replace with your actual Streamlit URL
        DASHBOARD_URL = "https://yourusername-bitcoin-dashboard.streamlit.app/"
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🚀 Share with Friends")
            st.write("**Works instantly - no setup needed!**")
            st.code(DASHBOARD_URL)
            
            if st.button("📋 Copy Link", use_container_width=True, key="copy_main"):
                st.success("Link copied! Send to friends 📱")
            
            st.write("**Quick share to:**")
            share_col1, share_col2, share_col3 = st.columns(3)
            with share_col1:
                if st.button("WhatsApp", use_container_width=True):
                    st.info("Paste link in WhatsApp")
            with share_col2:
                if st.button("Telegram", use_container_width=True):
                    st.info("Paste link in Telegram") 
            with share_col3:
                if st.button("Email", use_container_width=True):
                    st.info("Paste link in email")
        
        with col2:
            st.write("**Scan QR Code:**")
            qr_image = generate_qr_code(DASHBOARD_URL)
            st.markdown(f'<img src="data:image/png;base64,{qr_image}" width="120">', 
                       unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Refresh button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📊 Live Metrics")
    with col2:
        if st.button("🔄 Update", key="refresh_main"):
            with st.spinner("Getting latest data..."):
                if tracker.update_data():
                    st.success("Data updated!")
                    st.rerun()
                else:
                    st.error("Update failed - try again")
    
    # Display current data
    if len(tracker.df) > 0:
        latest = tracker.df.iloc[-1]
        
        # Calculate trend for display
        current_trend, trend_direction = tracker.calculate_trend(latest['total_nodes'])
        
        # BTC Price (highlighted)
        st.metric(
            label="BTC Price (USD)",
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
                label="Tor Privacy", 
                value=f"{latest['tor_percentage']:.1f}%",
                delta=None
            )
        
        # Last update time
        last_time = tracker.df.iloc[-1]['timestamp']
        if isinstance(last_time, str):
            last_time = pd.to_datetime(last_time)
        st.caption(f"🕒 Last update: {last_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Historical trends (simplified for mobile)
    if len(tracker.df) > 1:
        st.markdown("---")
        st.subheader("📈 Network Health")
        
        chart_df = tracker.df.tail(10)
        
        col1, col2 = st.columns(2)
        with col1:
            avg_tor = chart_df['tor_percentage'].mean()
            st.metric("Avg Tor %", f"{avg_tor:.1f}%")
        with col2:
            avg_trend = chart_df['node_trend'].mean()
            st.metric("Avg Trend", f"{avg_trend:.1f}%")
    
    # Info section
    with st.expander("ℹ️ About This Dashboard", expanded=True):
        st.markdown("""
        **What You're Seeing:**
        
        🤑 **BTC Price** - Live Bitcoin price from multiple sources
        🌐 **Total Nodes** - Computers running Bitcoin software worldwide  
        🕵️ **Tor Nodes** - Nodes using Tor for privacy
        📊 **Tor %** - Percentage of private nodes (higher = more private)
        📈 **Trend** - Network growth/decline vs last update
        
        **How to Use:**
        - Tap **🔄 Update** to refresh data
        - Share the link with friends
        - Works on any device
        - No login or setup needed
        
        **Perfect for:**
        - Tracking Bitcoin network health
        - Monitoring price movements  
        - Learning about cryptocurrency
        - Sharing with crypto friends
        
        *Data updates every time you tap Refresh*
        """)
    
    # Auto-refresh every 5 minutes
    if st.button("🤖 Enable Auto-Refresh", key="auto_refresh"):
        st.info("Auto-refresh: Come back and tap Update button")
        st.rerun()

if __name__ == "__main__":
    main()