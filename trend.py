import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import numpy as np

st.set_page_config(page_title="Laby's Miracle - Trend", layout="wide")

STOCKS = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS", 
    "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BEL.NS", "BPCL.NS", 
    "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", 
    "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", 
    "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", 
    "ITC.NS", "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", 
    "LT.NS", "LTIM.NS", "MARUTI.NS", "NESTLEIND.NS", 
    "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", 
    "SBIN.NS", "SHRIRAMFIN.NS", "SUNPHARMA.NS", "TCS.NS", "TATACONSUM.NS", 
    "TATASTEEL.NS", "TECHM.NS", "TITAN.NS", "TRENT.NS",
    "TATAPOWER.NS", "WIPRO.NS", "HINDPETRO.NS", "VEDL.NS", "GAIL.NS", 
    "BHEL.NS", "BANDHANBNK.NS", "MARICO.NS", "DABUR.NS", "AMBUJACEM.NS", 
    "BIOCON.NS", "IDFCFIRSTB.NS", "PNB.NS", "SAIL.NS",
    "CHOLAFIN.NS", "LICHSGFIN.NS", "TATACHEM.NS", "NATIONALUM.NS", "RECLTD.NS"
]
TIMEFRAME = "5m" 

def calculate_indicators(df):
    v = df['Volume']
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (tp * v).groupby(df.index.date).cumsum() / v.groupby(df.index.date).cumsum()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = true_range.rolling(14).mean()
    
    return df

def get_data_and_analyze(ticker):
    try:
        df = yf.download(ticker, period="5d", interval=TIMEFRAME, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if df.empty or len(df) < 50: return None
            
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        
        bias = "NEUTRAL"
        if latest['Close'] > latest['VWAP'] and latest['Close'] > latest['EMA_50']:
            bias = "BULLISH"
        elif latest['Close'] < latest['VWAP'] and latest['Close'] < latest['EMA_50']:
            bias = "BEARISH"
            
        entry = float(latest['Close'])
        atr = float(latest['ATR'])
        
        if bias == "BULLISH":
            stop_loss = entry - (1.5 * atr)
            target = entry + ((entry - stop_loss) * 2)
        elif bias == "BEARISH":
            stop_loss = entry + (1.5 * atr)
            target = entry - ((stop_loss - entry) * 2)
        else:
            stop_loss = 0.0
            target = 0.0

        return {
            "Stock": ticker.replace(".NS", ""),
            "Entry (Price)": round(entry, 2),
            "Target (Exit)": round(target, 2),
            "Stop Loss": round(stop_loss, 2),
            "RSI": round(float(latest['RSI']), 1),
            "Bias": bias
        }
    except Exception as e:
        return None

st.title("✨ Laby's Miracle: The Elite 5")
st.write("Ranked by highest momentum using **VWAP, EMA 50, and RSI**.")

st.sidebar.header("Controls")
auto_refresh = st.sidebar.checkbox("Auto-Scan Every 60s", value=True)

all_data = []
my_bar = st.progress(0, text="Laby's Miracle is hunting for setups... Please wait.")

for index, ticker in enumerate(STOCKS):
    result = get_data_and_analyze(ticker)
    if result:
        all_data.append(result)
    my_bar.progress((index + 1) / len(STOCKS), text=f"Analyzing {ticker.replace('.NS', '')}...")

my_bar.empty()
st.subheader(f"Last Market Scan: {datetime.now().strftime('%H:%M:%S')}")

if not all_data:
    st.error("⚠️ The Scanner is empty. Waiting for market data...")
else:
    df_all = pd.DataFrame(all_data)
    bullish_df = df_all[df_all['Bias'] == 'BULLISH'].sort_values(by='RSI', ascending=False).head(5)
    bearish_df = df_all[df_all['Bias'] == 'BEARISH'].sort_values(by='RSI', ascending=True).head(5)
    
    col1, col2 = st.columns(2)
    with col1:
        st.success("🟢 TOP 5 BUYS (Strongest Upward Momentum)")
        if not bullish_df.empty:
            st.dataframe(bullish_df[['Stock', 'Entry (Price)', 'Target (Exit)', 'Stop Loss']], hide_index=True, use_container_width=True)
        else:
            st.write("No strong bullish setups right now.")
            
    with col2:
        st.error("🔴 TOP 5 SHORTS (Strongest Downward Momentum)")
        if not bearish_df.empty:
            st.dataframe(bearish_df[['Stock', 'Entry (Price)', 'Target (Exit)', 'Stop Loss']], hide_index=True, use_container_width=True)
        else:
            st.write("No strong bearish setups right now.")

if auto_refresh:
    time.sleep(60)
    st.rerun()
