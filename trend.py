import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime, timedelta, timezone
import numpy as np

st.set_page_config(page_title="Laby's Miracle - Normal Equity Screener", layout="wide")

# --- NIFTY 200 & RETAIL FAVORITES (Normal Cash Market) ---
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

# Set up IST Timezone Rule
IST = timezone(timedelta(hours=5, minutes=30))

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
            "Price": round(entry, 2),
            "Target": round(target, 2),
            "Stop Loss": round(stop_loss, 2),
            "RSI": round(float(latest['RSI']), 1),
            "Bias": bias
        }
    except Exception as e:
        return None

st.title("✨ Laby's Miracle: Normal Equity Screener")
st.write("Scanning high-volume NSE cash stocks, ranked by momentum.")

st.sidebar.header("Controls")
auto_refresh = st.sidebar.checkbox("Auto-Scan Every 90s", value=True)

all_data = []
my_bar = st.progress(0, text="Laby's Miracle is downloading market data... Please wait.")

for index, ticker in enumerate(STOCKS):
    result = get_data_and_analyze(ticker)
    if result:
        all_data.append(result)
    my_bar.progress((index + 1) / len(STOCKS), text=f"Analyzing {ticker.replace('.NS', '')}...")

my_bar.empty()

# FORCE THE CLOCK TO DISPLAY IST
st.subheader(f"Last Market Scan: {datetime.now(IST).strftime('%I:%M:%S %p')} (IST)")

if not all_data:
    st.error("⚠️ The Scanner is empty. Waiting for market data...")
else:
    df_all = pd.DataFrame(all_data)
    
    bullish_all = df_all[df_all['Bias'] == 'BULLISH'].sort_values(by='RSI', ascending=False)
    bearish_all = df_all[df_all['Bias'] == 'BEARISH'].sort_values(by='RSI', ascending=True)
    
    bullish_600 = bullish_all[bullish_all['Price'] < 600]
    bearish_600 = bearish_all[bearish_all['Price'] < 600]

    st.markdown("---")
    st.markdown("### 🌐 SECTIONS 1 & 2: ALL NORMAL NSE STOCKS")
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("1. 🟢 BUY (All Stocks - Highest RSI)")
        if not bullish_all.empty:
            st.dataframe(bullish_all[['Stock', 'Price', 'Target', 'Stop Loss', 'RSI']].head(10), hide_index=True, use_container_width=True)
        else:
            st.write("No bullish setups.")
            
    with col2:
        st.error("2. 🔴 SELL/SHORT (All Stocks - Lowest RSI)")
        if not bearish_all.empty:
            st.dataframe(bearish_all[['Stock', 'Price', 'Target', 'Stop Loss', 'RSI']].head(10), hide_index=True, use_container_width=True)
        else:
            st.write("No bearish setups.")

    st.markdown("---")
    st.markdown("### 🪙 SECTIONS 3 & 4: STOCKS PRICED UNDER ₹600")
    col3, col4 = st.columns(2)
    
    with col3:
        st.success("3. 🟢 BUY (Under ₹600 - Highest RSI)")
        if not bullish_600.empty:
            st.dataframe(bullish_600[['Stock', 'Price', 'Target', 'Stop Loss', 'RSI']].head(10), hide_index=True, use_container_width=True)
        else:
            st.write("No cheap bullish setups.")
            
    with col4:
        st.error("4. 🔴 SELL/SHORT (Under ₹600 - Lowest RSI)")
        if not bearish_600.empty:
            st.dataframe(bearish_600[['Stock', 'Price', 'Target', 'Stop Loss', 'RSI']].head(10), hide_index=True, use_container_width=True)
        else:
            st.write("No cheap bearish setups.")

if auto_refresh:
    time.sleep(90)
    st.rerun()
