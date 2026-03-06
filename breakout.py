import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime, timedelta, timezone
import numpy as np

st.set_page_config(page_title="Laby's Miracle - Breakout", layout="wide")

# --- NORMAL EQUITY CASH MARKET ---
STOCKS = [
    "ADANIENT.NS", "ADANIPORTS.NS", "ADANIPOWER.NS", "AMBUJACEM.NS", "ANGELONE.NS", 
    "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", 
    "BANKBARODA.NS", "BEL.NS", "BHEL.NS", "BHARTIARTL.NS", "BSE.NS", "BPCL.NS", 
    "CDSL.NS", "CHOLAFIN.NS", "CIPLA.NS", "COALINDIA.NS", "COCHINSHIP.NS", 
    "CUMMINSIND.NS", "DABUR.NS", "DIXON.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", 
    "FACT.NS", "GAIL.NS", "GMRINFRA.NS", "GRASIM.NS", "HAL.NS", "HAVELLS.NS", 
    "HCLTECH.NS", "HDFCBANK.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDCOPPER.NS", 
    "HINDPETRO.NS", "HINDUNILVR.NS", "HUDCO.NS", "ICICIBANK.NS", "IDFCFIRSTB.NS", 
    "IEX.NS", "INDHOTEL.NS", "INDIGO.NS", "INDUSINDBK.NS", "INFY.NS", "IOC.NS", 
    "IREDA.NS", "IRFC.NS", "IRCTC.NS", "ITC.NS", "JINDALSTEL.NS", "JIOFIN.NS", 
    "JSWSTEEL.NS", "KALYANKJIL.NS", "KOTAKBANK.NS", "KPITTECH.NS", "LT.NS", 
    "LTIM.NS", "M&M.NS", "MARICO.NS", "MARUTI.NS", "MAZDOCK.NS", "MRF.NS", 
    "NATIONALUM.NS", "NAUKRI.NS", "NESTLEIND.NS", "NHPC.NS", "NMDC.NS", "NTPC.NS", 
    "NYKAA.NS", "ONGC.NS", "PAYTM.NS", "PFC.NS", "PNB.NS", "POLYCAB.NS", "POLICYBZR.NS", 
    "POWERGRID.NS", "PUNITCOMM.NS", "RAILTEL.NS", "RECLTD.NS", "RELIANCE.NS", "RVNL.NS", 
    "SAIL.NS", "SBIN.NS", "SJVN.NS", "SUZLON.NS", "SUNPHARMA.NS", "TATACHEM.NS", 
    "TATACOMM.NS", "TATACONSUM.NS", "TATAELXSI.NS", "TATAMOTORS.NS", "TATAPOWER.NS", 
    "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "TITAN.NS", "TRENT.NS", "TVSMOTOR.NS", 
    "UPL.NS", "VEDL.NS", "VOLTAS.NS", "WIPRO.NS", "YESBANK.NS", "ZOMATO.NS"
]
TIMEFRAME = "5m" 
IST = timezone(timedelta(hours=5, minutes=30))

def calculate_breakout_indicators(df):
    # 1. VWAP (Base Trend Filter)
    v = df['Volume']
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (tp * v).groupby(df.index.date).cumsum() / v.groupby(df.index.date).cumsum()
    
    # 2. Bollinger Bands (Volatility)
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['STD_20'] = df['Close'].rolling(window=20).std()
    df['Upper_BB'] = df['SMA_20'] + (df['STD_20'] * 2)
    df['Lower_BB'] = df['SMA_20'] - (df['STD_20'] * 2)
    
    # 3. Relative Volume (RVOL) - Institutional Footprint
    df['Avg_Vol_20'] = df['Volume'].rolling(window=20).mean()
    df['RVOL'] = df['Volume'] / df['Avg_Vol_20'] 
    
    # 4. ATR (Stop Loss)
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = true_range.rolling(14).mean()
    
    return df

def analyze_breakout(ticker):
    try:
        df = yf.download(ticker, period="5d", interval=TIMEFRAME, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if df.empty or len(df) < 50: return None
            
        df = calculate_breakout_indicators(df)
        latest = df.iloc[-1]
        
        signal = "WAIT"
        
        # BUY BREAKOUT LOGIC: Price breaks top band + Massive Volume (> 1.5x average) + Above VWAP
        if (latest['Close'] > latest['Upper_BB'] and 
            latest['RVOL'] > 1.5 and 
            latest['Close'] > latest['VWAP']):
            signal = "BULLISH BREAKOUT"
            
        # SELL BREAKOUT LOGIC: Price breaks bottom band + Massive Volume (> 1.5x average) + Below VWAP
        elif (latest['Close'] < latest['Lower_BB'] and 
              latest['RVOL'] > 1.5 and 
              latest['Close'] < latest['VWAP']):
            signal = "BEARISH BREAKDOWN"
            
        entry = float(latest['Close'])
        atr = float(latest['ATR'])
        
        if signal == "BULLISH BREAKOUT":
            stop_loss = entry - (1.5 * atr)
            target = entry + ((entry - stop_loss) * 2)
        elif signal == "BEARISH BREAKDOWN":
            stop_loss = entry + (1.5 * atr)
            target = entry - ((stop_loss - entry) * 2)
        else:
            stop_loss = 0.0
            target = 0.0

        return {
            "Stock": ticker.replace(".NS", ""),
            "Price": round(entry, 2),
            "Target": round(target, 2),
            "Stop Loss": round(stop_loss, 2),
            "Vol Spike (RVOL)": f"{round(float(latest['RVOL']), 1)}x",
            "Signal": signal
        }
    except Exception as e:
        return None

st.title("🌋 Laby's Miracle: Volatility Breakout")
st.write("Scanning for explosive moves using **Bollinger Bands & Relative Volume (RVOL)**.")

st.sidebar.header("Controls")
auto_refresh = st.sidebar.checkbox("Auto-Scan Every 90s", value=True)

all_data = []
my_bar = st.progress(0, text="Hunting for explosive breakouts... Please wait.")

for index, ticker in enumerate(STOCKS):
    result = analyze_breakout(ticker)
    if result and result['Signal'] != "WAIT":
        all_data.append(result)
    my_bar.progress((index + 1) / len(STOCKS), text=f"Analyzing {ticker.replace('.NS', '')}...")

my_bar.empty()
st.subheader(f"Last Market Scan: {datetime.now(IST).strftime('%I:%M:%S %p')} (IST)")

if not all_data:
    st.info("No high-volume breakouts happening right now. The market is consolidating...")
else:
    df_all = pd.DataFrame(all_data)
    
    buys = df_all[df_all['Signal'] == 'BULLISH BREAKOUT'].sort_values(by='Vol Spike (RVOL)', ascending=False)
    shorts = df_all[df_all['Signal'] == 'BEARISH BREAKDOWN'].sort_values(by='Vol Spike (RVOL)', ascending=False)
    
    col1, col2 = st.columns(2)
    with col1:
        st.success("🚀 🟢 LONG BREAKOUTS (High Volume Surge)")
        if not buys.empty:
            st.dataframe(buys[['Stock', 'Price', 'Target', 'Stop Loss', 'Vol Spike (RVOL)']], hide_index=True, use_container_width=True)
        else:
            st.write("No bullish breakouts currently.")
            
    with col2:
        st.error("🩸 🔴 SHORT BREAKDOWNS (High Volume Dump)")
        if not shorts.empty:
            st.dataframe(shorts[['Stock', 'Price', 'Target', 'Stop Loss', 'Vol Spike (RVOL)']], hide_index=True, use_container_width=True)
        else:
            st.write("No bearish breakdowns currently.")

if auto_refresh:
    time.sleep(90)
    st.rerun()
