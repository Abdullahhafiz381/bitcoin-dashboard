import streamlit as st
import requests
from datetime import datetime

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
</style>
""", unsafe_allow_html=True)

def main():
    st.title("₿ Bitcoin Tracker")
    st.write("Live network data and price")
    
    # Refresh button at top
    if st.button("🔄 Refresh Now"):
        st.rerun()
    
    # Get Bitcoin price
    try:
        price_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        price_data = requests.get(price_url, timeout=10).json()
        btc_price = price_data['bitcoin']['usd']
        
        st.metric(
            label="BTC Price",
            value=f"${btc_price:,.0f}",
            delta="Live"
        )
    except:
        st.error("❌ Price data unavailable")
        btc_price = None
    
    # Get node data
    try:
        node_url = "https://bitnodes.io/api/v1/snapshots/latest/"
        node_data = requests.get(node_url, timeout=10).json()
        
        total_nodes = node_data['total_nodes']
        
        # Count Tor nodes efficiently
        tor_count = 0
        for node_info in node_data['nodes'].values():
            if 'onion' in str(node_info):
                tor_count += 1
        
        tor_percent = (tor_count / total_nodes) * 100
        
        # Display in columns for mobile
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Nodes", f"{total_nodes:,}")
            st.metric("Tor Nodes", f"{tor_count:,}")
        
        with col2:
            st.metric("Tor %", f"{tor_percent:.1f}%")
            st.metric("Status", "✅ Live")
            
    except Exception as e:
        st.error("❌ Node data unavailable")
    
    # Last update time
    st.write("---")
    st.caption(f"📱 Last update: {datetime.now().strftime('%H:%M:%S')}")
    
    # Info section
    with st.expander("ℹ️ About this app"):
        st.markdown("""
        **What this tracks:**
        - **Bitcoin Price**: Current USD value
        - **Network Nodes**: Computers running Bitcoin
        - **Tor Nodes**: Privacy-focused nodes
        
        **Data Sources:**
        - Bitnodes.io for node data
        - CoinGecko for price data
        
        Refresh to get latest data!
        """)

if __name__ == "__main__":
    main()
