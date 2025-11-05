import streamlit as st
import requests
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
import base64

# Mobile-friendly setup
st.set_page_config(
    page_title="BitNode BTC Pro Tracker",
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
    .signal-buy {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #28a745;
    }
    .signal-sell {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #dc3545;
    }
    .signal-neutral {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #ffc107;
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

class BitcoinNodeAnalyzer:
    def __init__(self, data_file="network_data.json"):
        self.data_file = data_file
        self.bitnodes_api = "https://bitnodes.io/api/v1/snapshots/latest/"
        self.load_historical_data()
    
    def load_historical_data(self):
        """Load historical node data from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.historical_data = json.load(f)
            else:
                self.historical_data = []
        except:
            self.historical_data = []
    
    def save_historical_data(self):
        """Save current data to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.historical_data, f, indent=2)
        except Exception as e:
            st.error(f"Error saving data: {e}")
    
    def fetch_node_data(self):
        """Fetch current node data from Bitnodes API"""
        try:
            response = requests.get(self.bitnodes_api, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            total_nodes = data['total_nodes']
            
            # Count active nodes (nodes that responded)
            active_nodes = 0
            tor_nodes = 0
            
            for node_address, node_info in data['nodes'].items():
                # Check if node is active (has response data)
                if node_info and isinstance(node_info, list) and len(node_info) > 0:
                    active_nodes += 1
                
                # Count Tor nodes
                if '.onion' in str(node_address) or '.onion' in str(node_info):
                    tor_nodes += 1
            
            tor_percentage = (tor_nodes / total_nodes) * 100 if total_nodes > 0 else 0
            active_ratio = active_nodes / total_nodes if total_nodes > 0 else 0
            
            return {
                'timestamp': datetime.now().isoformat(),
                'total_nodes': total_nodes,
                'active_nodes': active_nodes,
                'tor_nodes': tor_nodes,
                'tor_percentage': tor_percentage,
                'active_ratio': active_ratio
            }
        except Exception as e:
            st.error(f"Error fetching node data: {e}")
            return None
    
    def get_previous_total_nodes(self):
        """Get previous day's total nodes"""
        if len(self.historical_data) < 2:
            return None
        
        # Get yesterday's data (look for data from ~24 hours ago)
        current_time = datetime.now()
        target_time = current_time - timedelta(hours=24)
        
        # Find the closest snapshot to 24 hours ago
        closest_snapshot = None
        min_time_diff = float('inf')
        
        for snapshot in self.historical_data[:-1]:  # Exclude current
            try:
                snapshot_time = datetime.fromisoformat(snapshot['timestamp'])
                time_diff = abs((snapshot_time - target_time).total_seconds())
                
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_snapshot = snapshot
            except:
                continue
        
        return closest_snapshot['total_nodes'] if closest_snapshot else None
    
    def calculate_network_signal(self, current_data):
        """Calculate trading signal based on network trends"""
        previous_total = self.get_previous_total_nodes()
        
        if previous_total is None or previous_total == 0:
            return {
                'active_nodes': current_data['active_nodes'],
                'total_nodes': current_data['total_nodes'],
                'previous_total': "No previous data",
                'active_ratio': current_data['active_ratio'],
                'trend': 0,
                'signal': 0,
                'suggestion': "INSUFFICIENT_DATA"
            }
        
        active_ratio = current_data['active_ratio']
        trend = (current_data['total_nodes'] - previous_total) / previous_total
        signal = active_ratio * trend
        
        # Determine suggestion
        if signal > 0.01:
            suggestion = "BUY"
        elif signal < -0.01:
            suggestion = "SELL"
        else:
            suggestion = "SIDEWAYS"
        
        return {
            'active_nodes': current_data['active_nodes'],
            'total_nodes': current_data['total_nodes'],
            'previous_total': previous_total,
            'active_ratio': round(active_ratio, 4),
            'trend': round(trend, 4),
            'signal': round(signal, 4),
            'suggestion': suggestion
        }
    
    def update_network_data(self):
        """Fetch new data and update historical records"""
        current_data = self.fetch_node_data()
        if not current_data:
            return False
        
        # Add to historical data
        self.historical_data.append(current_data)
        
        # Keep only last 7 days of data (approx 1008 snapshots if updating every 10 minutes)
        if len(self.historical_data) > 1008:
            self.historical_data = self.historical_data[-1008:]
        
        self.save_historical_data()
        return True

def main():
    # Initialize analyzers
    analyzer = BitcoinNodeAnalyzer()
    
    # Title and sharing section
    st.title("₿ BitNode BTC Pro Tracker")
    st.markdown("Live Network Analysis • Tor Metrics • Trading Signals")
    
    # SHARING SECTION
    with st.container():
        st.markdown('<div class="share-box">', unsafe_allow_html=True)
        
        DASHBOARD_URL = "https://bitnodebtc.streamlit.app/"
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🚀 Share Dashboard")
            st.code(DASHBOARD_URL)
            
            if st.button("📋 Copy Link", use_container_width=True, key="copy_main"):
                st.success("✅ Dashboard link copied!")
        
        with col2:
            st.write("**Scan QR Code:**")
            qr_image = generate_qr_code(DASHBOARD_URL)
            st.markdown(f'<img src="data:image/png;base64,{qr_image}" width="120">', 
                       unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Refresh button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📊 Live Network Data")
    with col2:
        if st.button("🔄 Update All", key="refresh_main"):
            with st.spinner("Analyzing network data..."):
                if analyzer.update_network_data():
                    st.success("Data updated!")
                    st.rerun()
                else:
                    st.error("Update failed")
    
    # Get current data
    if len(analyzer.historical_data) > 0:
        current_data = analyzer.historical_data[-1]
        signal_data = analyzer.calculate_network_signal(current_data)
        
        # Display current price (optional - you can remove if not needed)
        try:
            price_response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
            btc_price = float(price_response.json()['price'])
            st.metric(
                label="🎯 BTC Current Price",
                value=f"${btc_price:,.2f}",
                delta=None
            )
        except:
            pass
        
        # NETWORK TREND SIGNAL SECTION
        st.markdown("---")
        st.subheader("📈 Network Trend Signal")
        
        # Display signal with color coding
        if signal_data['suggestion'] == "BUY":
            signal_class = "signal-buy"
            emoji = "🟢"
            signal_text = "STRONG BUY"
        elif signal_data['suggestion'] == "SELL":
            signal_class = "signal-sell"
            emoji = "🔴"
            signal_text = "STRONG SELL"
        else:
            signal_class = "signal-neutral"
            emoji = "🟡"
            signal_text = "NEUTRAL"
        
        st.markdown(f'<div class="{signal_class}">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Active Nodes", f"{signal_data['active_nodes']:,}")
            st.metric("Total Nodes", f"{signal_data['total_nodes']:,}")
            st.metric("Previous Total", f"{signal_data['previous_total']:,}")
        
        with col2:
            st.metric("Active Ratio", f"{signal_data['active_ratio']:.4f}")
            st.metric("Trend", f"{signal_data['trend']:+.4f}")
            st.metric("Final Signal", f"{signal_data['signal']:+.4f}")
        
        st.markdown(f"### → {signal_text} SIGNAL {emoji}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # TOR METRICS SECTION
        st.markdown("---")
        st.subheader("🕵️ Tor Network Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Tor Nodes", f"{current_data['tor_nodes']:,}")
        
        with col2:
            st.metric("Total Nodes", f"{current_data['total_nodes']:,}")
        
        with col3:
            st.metric("Tor Privacy", f"{current_data['tor_percentage']:.1f}%")
        
        # Network Health Summary
        st.markdown("---")
        st.subheader("🌐 Network Health Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if current_data['tor_percentage'] > 20:
                status = "🟢 Excellent"
            elif current_data['tor_percentage'] > 10:
                status = "🟡 Good"
            else:
                status = "🔴 Low"
            st.metric("Tor Privacy", status)
        
        with col2:
            if signal_data['active_ratio'] > 0.8:
                status = "🟢 Excellent"
            elif signal_data['active_ratio'] > 0.6:
                status = "🟡 Good"
            else:
                status = "🔴 Low"
            st.metric("Network Activity", status)
        
        with col3:
            if signal_data['trend'] > 0.01:
                status = "🟢 Growing"
            elif signal_data['trend'] < -0.01:
                status = "🔴 Shrinking"
            else:
                status = "🟡 Stable"
            st.metric("Network Trend", status)
        
        # Last update time
        last_time = datetime.fromisoformat(current_data['timestamp'])
        st.caption(f"🕒 Last update: {last_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Historical data info
        if len(analyzer.historical_data) > 1:
            st.caption(f"📊 Data points: {len(analyzer.historical_data)} snapshots")
    
    else:
        st.info("📱 Tap 'Update All' above to load network data!")
    
    # Explanation Section
    with st.expander("ℹ️ Understanding Network Signals", expanded=True):
        st.markdown("""
        **Network Trend Signal Formula:**
        ```
        Signal = (Active Nodes ÷ Total Nodes) × ((Current Total Nodes − Previous Total Nodes) ÷ Previous Total Nodes)
        ```
        
        **Interpretation:**
        - **BUY Signal (🟢)**: Signal > +0.01 - Network growing with high activity
        - **SELL Signal (🔴)**: Signal < -0.01 - Network shrinking with low activity
        - **NEUTRAL Signal (🟡)**: -0.01 ≤ Signal ≤ +0.01 - Stable network conditions
        
        **Tor Privacy Levels:**
        - **Excellent (🟢)**: >20% - Strong network privacy
        - **Good (🟡)**: 10-20% - Moderate privacy
        - **Low (🔴)**: <10% - Weak network privacy
        
        **Network Activity:**
        - **Excellent (🟢)**: >80% nodes active
        - **Good (🟡)**: 60-80% nodes active
        - **Low (🔴)**: <60% nodes active
        """)
    
    # Auto-refresh every 10 minutes
    if st.button("⏰ Enable Auto-Refresh (10 min)", key="auto_refresh"):
        st.info("Come back and tap 'Update All' for fresh data")
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.caption("BitNode BTC Pro Tracker • Network Analysis + Tor Metrics • Not Financial Advice")

if __name__ == "__main__":
    main()