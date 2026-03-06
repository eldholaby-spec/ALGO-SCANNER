import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import numpy as np

st.set_page_config(page_title="Laby's Miracle - Scalper", layout="wide")

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

def calculate_scalp_indicators(df):
    v = df['Volume']
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (tp * v).groupby(df.index.date).cumsum() / v.groupby(df.index.date).cumsum()
    
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    low_14 = df['Low'].rolling(window=14).min()
    high_14 = df['High'].rolling(window=14).max()
    df['%K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
    
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = true_range.rolling(14).mean()
    
    return df

def analyze_scalp(ticker):
    try:
        df = yf.download(ticker, period="5d", interval=TIMEFRAME, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if df.empty or len(df) < 50: return None
            
        df = calculate_scalp_indicators(df)
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        signal = "WAIT"
        
        if (latest['MACD'] > latest['Signal'] and prev['MACD'] <= prev['Signal'] and 
            latest['%K'] < 25 and latest['Close'] > latest['VWAP']):
            signal = "BUY SCALP"
            
        elif (latest['MACD'] < latest['Signal'] and prev['MACD'] >= prev['Signal'] and 
              latest['%K'] > 75 and latest['Close'] < latest['VWAP']):
            signal = "SHORT SCALP"
            
        entry = float(latest['Close'])
        atr = float(latest['ATR'])
        
        if signal == "BUY SCALP":
            stop_loss = entry - (1.2 * atr)
            target = entry + ((entry - stop_loss) * 1.5)
        elif signal == "SHORT SCALP":
            stop_loss = entry + (1.2 * atr)
            target = entry - ((stop_loss - entry) * 1.5)
        else:
            stop_loss = 0.0
            target = 0.0

        return {
            "Stock": ticker.replace(".NS", ""),
            "Entry": round(entry, 2),
            "Target": round(target, 2),
            "Stop Loss": round(stop_loss, 2),
            "Stoch %K": round(float(latest['%K']), 1),
            "Signal": signal
        }
    except Exception as e:
        return None

st.title("⚡ Laby's Miracle: Momentum Scalper")
st.write("Aggressive day trading engine using **Stochastic Oversold + MACD Crossover**.")

st.sidebar.header("Controls")
auto_refresh = st.sidebar.checkbox("Auto-Scan Every 60s", value=True)

opportunities = []
my_bar = st.progress(0, text="Laby's Miracle is hunting for scalps... Please wait.")

for index, ticker in enumerate(STOCKS):
    result = analyze_scalp(ticker)
    if result and result['Signal'] != "WAIT":
        opportunities.append(result)
    my_bar.progress((index + 1) / len(STOCKS), text=f"Analyzing {ticker.replace('.NS', '')}...")

my_bar.empty()
st.subheader(f"Last Market Scan: {datetime.now().strftime('%H:%M:%S')}")

if opportunities:
    df_res = pd.DataFrame(opportunities)
    buys = df_res[df_res['Signal'] == 'BUY SCALP']
    shorts = df_res[df_res['Signal'] == 'SHORT SCALP']
    
    col1, col2 = st.columns(2)
    with col1:
        st.success("🟢 ACTIVE BUY SCALPS")
        if not buys.empty:
            st.dataframe(buys[['Stock', 'Entry', 'Target', 'Stop Loss', 'Stoch %K']], hide_index=True, use_container_width=True)
        else:
            st.write("No buy triggers right now.")
            
    with col2:
        st.error("🔴 ACTIVE SHORT SCALPS")
        if not shorts.empty:
            st.dataframe(shorts[['Stock', 'Entry', 'Target', 'Stop Loss', 'Stoch %K']], hide_index=True, use_container_width=True)
        else:
            st.write("No short triggers right now.")
else:
    st.info("No Double-Cross setups right now. Waiting for the indicators to align...")

if auto_refresh:
    time.sleep(60)
    st.rerun()
