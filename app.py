import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time
import json
import math
import streamlit.components.v1 as components

# -------------------------
# Config
# -------------------------
st.set_page_config(page_title="Abdullah's Bitnode Tracker", layout='wide')

BITNODES_SNAPSHOTS = "https://bitnodes.io/api/v1/snapshots/"
BITNODES_LATEST = "https://bitnodes.io/api/v1/snapshots/latest/"
COINGECKO_SIMPLE = "https://api.coingecko.com/api/v3/simple/price"

TRACK_COINS = ["BTC", "ETH", "LTC", "BCH", "SOL", "ADA", "AVAX", "DOGE", "DOT", "LINK", "BNB"]
COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "LTC": "litecoin",
    "BCH": "bitcoin-cash",
    "SOL": "solana",
    "ADA": "cardano",
    "AVAX": "avalanche-2",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "LINK": "chainlink",
    "BNB": "binancecoin",
}

# -------------------------
# Styles - dark futuristic
# -------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@400;700&display=swap');
    .reportview-container {background: linear-gradient(180deg,#081124 0%, #0b1020 100%);} 
    .stApp { color: #dbe9ff }
    .neon-box { background: rgba(10,12,20,0.6); border-radius:12px; padding:16px; box-shadow: 0 8px 30px rgba(94,120,255,0.06); border:1px solid rgba(94,120,255,0.12);} 
    .title {font-family: 'Orbitron', sans-serif; font-size:28px; color: #b8c7ff}
    .subtitle {font-family: 'Rajdhani', sans-serif; color:#9fb0ff}
    .small {font-size:12px; color:#9aa9d9}
    .refresh-btn {display:flex; justify-content:flex-end}
    .signal-buy { color: #7ef7a6; font-weight:700 }
    .signal-sell { color: #ff8b8b; font-weight:700 }
    .signal-side { color: #ffd97e; font-weight:700 }
    </style>
    
    """,
    unsafe_allow_html=True
)

# JS auto refresh every 300000 ms (5 minutes)
components.html("<script>setTimeout(()=>{ window.location.reload(); }, 300000);</script>", height=0)

# -------------------------
# Helper functions
# -------------------------
@st.cache_data(ttl=600)
def fetch_bitnodes_snapshots(limit=2, timeout=15):
    """Fetch the latest `limit` snapshots from Bitnodes API.
    Returns list sorted newest first. Each item is the JSON object returned by Bitnodes for the snapshot summary.
    """
    params = {"limit": limit}
    try:
        resp = requests.get(BITNODES_SNAPSHOTS, params=params, timeout=timeout)
        data = resp.json()
        # bitnodes returns object with 'results' (list)
        results = data.get('results') if isinstance(data, dict) else data
        if isinstance(results, list) and len(results) >= 1:
            return results
        # fallback: try latest endpoint
        resp2 = requests.get(BITNODES_LATEST, timeout=timeout)
        data2 = resp2.json()
        # wrap it
        return [data2]
    except Exception as e:
        st.session_state['bitnodes_error'] = str(e)
        return []

@st.cache_data(ttl=600)
def fetch_coingecko_prices(symbols):
    ids = ','.join([COINGECKO_IDS[s] for s in symbols if s in COINGECKO_IDS])
    params = {
        'ids': ids,
        'vs_currencies': 'usd',
        'include_24hr_change': 'true'
    }
    try:
        r = requests.get(COINGECKO_SIMPLE, params=params, timeout=15)
        return r.json()
    except Exception as e:
        st.session_state['coingecko_error'] = str(e)
        return {}


def safe_get(d, *keys, default=None):
    cur = d
    for k in keys:
        if cur is None:
            return default
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur


# -------------------------
# Top bar: title + refresh
# -------------------------
col1, col2 = st.columns([3,1])
with col1:
    st.markdown('<div class="title">Abdullah\'s Bitnode Tracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Network-driven cryptocurrency signals — BTC is master</div>', unsafe_allow_html=True)
with col2:
    if st.button('Refresh', key='manual_refresh'):
        st.experimental_rerun()

st.markdown("---")

# -------------------------
# Fetch data
# -------------------------
snapshots = fetch_bitnodes_snapshots(limit=2)
prices_raw = fetch_coingecko_prices(TRACK_COINS)

now = datetime.utcnow()

# Determine current and previous snapshot
if len(snapshots) >= 2:
    current_snap = snapshots[0]
    previous_snap = snapshots[1]
elif len(snapshots) == 1:
    current_snap = snapshots[0]
    previous_snap = {}
else:
    current_snap = {}
    previous_snap = {}

# Helper to extract counts with fallbacks
def extract_counts(snap):
    # Try common keys
    total = safe_get(snap, 'nodes') or safe_get(snap, 'total_nodes') or safe_get(snap, 'total')
    onion = safe_get(snap, 'onion') or safe_get(snap, 'tor') or safe_get(snap, 'onion_nodes')
    full = safe_get(snap, 'full_nodes') or safe_get(snap, 'reachable_nodes') or total
    pruned = safe_get(snap, 'pruned_nodes') or safe_get(snap, 'pruned') or 0
    # If nodes is a dict of node entries, compute counts
    if isinstance(total, dict):
        total = len(total)
    try:
        total = int(total) if total is not None else None
    except:
        total = None
    if isinstance(onion, dict):
        onion = len(onion)
    try:
        onion = int(onion) if onion is not None else 0
    except:
        onion = 0
    try:
        full = int(full) if full is not None else (total or 0)
    except:
        full = total or 0
    try:
        pruned = int(pruned)
    except:
        pruned = 0
    return {
        'total': total or 0,
        'onion': onion,
        'full': full,
        'pruned': pruned
    }

cur_counts = extract_counts(current_snap)
prev_counts = extract_counts(previous_snap)

# Calculate percentages
def pct(part, whole):
    try:
        return (part/whole)*100 if whole else 0
    except:
        return 0

cur_tor_pct = pct(cur_counts['onion'], cur_counts['total'])
prev_tor_pct = pct(prev_counts['onion'], prev_counts['total'])

# Tor Trend
tor_trend = None
tor_trend_label = 'NEUTRAL'
try:
    if prev_tor_pct == 0:
        tor_trend = 0.0
    else:
        tor_trend = (cur_tor_pct - prev_tor_pct) / prev_tor_pct
    if tor_trend > 0.0001:
        tor_trend_label = 'SELL'  # More privacy usage -> bearish
    elif tor_trend < -0.0001:
        tor_trend_label = 'BUY'
    else:
        tor_trend_label = 'NEUTRAL'
except Exception:
    tor_trend = None
    tor_trend_label = 'NEUTRAL'

# Network Signal
active_nodes = cur_counts.get('full') or cur_counts.get('total')
total_nodes = cur_counts.get('total') or 1
prev_total_nodes = prev_counts.get('total') or total_nodes

signal = None
signal_label = 'SIDEWAYS'
try:
    change_ratio = ((total_nodes - prev_total_nodes) / prev_total_nodes) if prev_total_nodes else 0
    signal = (active_nodes / total_nodes) * change_ratio if total_nodes else 0
    if signal > 0.01:
        signal_label = 'BUY'
    elif signal < -0.01:
        signal_label = 'SELL'
    else:
        signal_label = 'SIDEWAYS'
except Exception:
    signal = None
    signal_label = 'SIDEWAYS'

# BTC master signal: combine tor_trend and network signal according to spec.
# We'll prioritize Network Signal thresholds, but tor_trend inverts buy/sell logic described: Tor Trend >0 => SELL

btc_signal = 'SIDEWAYS'
# Merge rules: if either metric strongly indicates BUY or SELL, use that. Network signal has primary thresholds.
if signal_label in ['BUY','SELL']:
    btc_signal = signal_label
else:
    btc_signal = tor_trend_label if tor_trend_label in ['BUY','SELL'] else 'SIDEWAYS'

# Build JSON output for all coins
output = []
for coin in TRACK_COINS:
    coin_id = COINGECKO_IDS.get(coin)
    price = None
    change24 = None
    if coin_id and prices_raw.get(coin_id):
        price = prices_raw[coin_id].get('usd')
        change24 = prices_raw[coin_id].get('usd_24h_change')
    signal_for_coin = btc_signal if coin != 'BTC' else btc_signal
    output.append({
        'coin': coin,
        'signal': signal_for_coin,
        'price': round(price, 6) if isinstance(price, (int,float)) else None,
        'change_24h': round(change24, 3) if isinstance(change24, (int,float)) else None,
        'time': now.strftime('%Y-%m-%d %H:%M:%S')
    })

# -------------------------
# UI layout
# -------------------------
left, right = st.columns([2,1])
with left:
    st.markdown('<div class="neon-box">', unsafe_allow_html=True)
    st.markdown(f"**Master BTC Signal:** <span class='{ 'signal-buy' if btc_signal=='BUY' else 'signal-sell' if btc_signal=='SELL' else 'signal-side'}'>{btc_signal}</span>")
    st.markdown(f"**Signal (network formula):** {signal_label} — value {signal if signal is not None else 'N/A'}")
    st.markdown(f"**Tor Trend:** {tor_trend_label} — value {round(tor_trend,6) if tor_trend is not None else 'N/A'}")
    st.markdown('---')
    st.markdown('**Node tracking (current vs previous)**')
    st.write('Current Total Nodes: ', cur_counts['total'], '  ', 'Previous Total Nodes:', prev_counts['total'])
    st.write('Current Tor (.onion) Nodes: ', cur_counts['onion'], '  ', 'Previous Tor Nodes:', prev_counts['onion'])
    # arrows
    def arrow(a,b):
        if b is None:
            return ''
        if a > b:
            return '📈'
        elif a < b:
            return '📉'
        else:
            return '➡️'
    st.write('Tor change: ', arrow(cur_counts['onion'], prev_counts['onion']))
    st.write('Normal nodes change: ', arrow(cur_counts['total']-cur_counts['onion'], prev_counts['total']-prev_counts['onion']))
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="neon-box">', unsafe_allow_html=True)
    st.markdown('**Snapshot times**')
    cs_time = safe_get(current_snap, 'snapshot_date') or safe_get(current_snap, 'timestamp') or 'N/A'
    ps_time = safe_get(previous_snap, 'snapshot_date') or safe_get(previous_snap, 'timestamp') or 'N/A'
    st.write('Current snapshot:', cs_time)
    st.write('Previous snapshot:', ps_time)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('---')

# Signals table
signals_df = pd.DataFrame(output)

# Display table with styling
st.markdown('<div class="neon-box">', unsafe_allow_html=True)
st.write('Signals and prices')

# Format the table
def format_signal_cell(s):
    if s == 'BUY':
        return f"BUY"
    if s == 'SELL':
        return f"SELL"
    return s

st.dataframe(signals_df.style.format({'price': '{:.6f}', 'change_24h': '{:.3f}'}), use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# JSON output (as required)
st.markdown('---')
st.markdown('**JSON Output (export-ready)**')
st.code(json.dumps(output, indent=2), language='json')

# Error indicators
if 'bitnodes_error' in st.session_state:
    st.error('Bitnodes API error: ' + st.session_state['bitnodes_error'])
if 'coingecko_error' in st.session_state:
    st.error('CoinGecko API error: ' + st.session_state['coingecko_error'])

# Footer: short usage tips
st.markdown('<div class="small">Auto-refresh: every 5 minutes. API results cached for 10 minutes. BTC is master signal; all listed alts follow BTC.</div>', unsafe_allow_html=True)

# End of app