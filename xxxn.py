import streamlit as st
import streamlit.components.v1 as components
import json
import os
import time
import requests
from datetime import datetime

# 1. ตั้งค่าหน้าจอ
st.set_page_config(page_title="MT5 Professional Terminal", layout="wide", initial_sidebar_state="collapsed")

# ================= ระบบฐานข้อมูลผู้ใช้ =================
USER_FILE = "trading_users.json"


def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {"admin": "1234"}


def save_users(users_dict):
    with open(USER_FILE, "w") as f:
        json.dump(users_dict, f, indent=4)


# ================= ฟังก์ชันดึงราคา =================
def get_live_price(symbol):
    try:
        mapping = {
            "OANDA:XAUUSD": "PAXGUSDT",
            "BINANCE:BTCUSDT": "BTCUSDT",
            "BINANCE:ETHUSDT": "ETHUSDT",
            "BINANCE:SOLUSDT": "SOLUSDT",
            "FX:EURUSD": "EURUSDT",
            "FX:GBPUSD": "GBPUSDT",
            "FX:USDJPY": "JPYUSDT"
        }
        api_sym = mapping.get(symbol, "BTCUSDT")
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={api_sym}"
        res = requests.get(url)
        return float(res.json()['price'])
    except:
        return 0.0


# ================= CSS: รวมธีม Gold Login + Dark Terminal =================
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background-color: #050505 !important;
        background-image: radial-gradient(circle at 50% 40%, #2b2000 0%, #050505 60%);
    }
    button[kind="primary"] {
        background: linear-gradient(135deg, #BF953F, #FCF6BA, #B38728, #FBF5B7, #AA771C) !important;
        color: black !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 30px !important;
    }
    .gold-text { color: #f5c542 !important; font-weight: bold; font-size: 18px; }
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
        background-color: #1a1a1a !important;
        color: white !important;
        border: 1px solid #333 !important;
    }
    .buy-btn button { background-color: #00c853 !important; color: white !important; }
    .sell-btn button { background-color: #ff1744 !important; color: white !important; }
    .close-btn button { background-color: #333 !important; color: #ff4d4d !important; border: 1px solid #ff4d4d !important; }
    .terminal-box {
        background-color: #000;
        border: 1px solid #222;
        padding: 15px;
        font-family: 'Consolas', monospace;
        color: #00ff00;
        border-radius: 5px;
    }
    .history-table {
        width: 100%;
        border-collapse: collapse;
        color: #ddd;
        font-size: 14px;
        margin-bottom: 20px;
    }
    .history-table th { color: #f5c542; border-bottom: 1px solid #333; padding: 10px; text-align: left; }
    .history-table td { padding: 8px; border-bottom: 1px solid #222; }
</style>
""", unsafe_allow_html=True)

# เริ่มต้น Session State
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "show_register" not in st.session_state: st.session_state["show_register"] = False
if "balance" not in st.session_state: st.session_state["balance"] = 10000.0
if "position" not in st.session_state: st.session_state["position"] = "None"
if "current_pnl" not in st.session_state: st.session_state["current_pnl"] = 0.0
if "tp_price" not in st.session_state: st.session_state["tp_price"] = 0.0
if "sl_price" not in st.session_state: st.session_state["sl_price"] = 0.0
if "trade_history" not in st.session_state: st.session_state["trade_history"] = []
if "transactions" not in st.session_state: st.session_state["transactions"] = []


# ฟังก์ชันบันทึกประวัติการเทรด
def add_to_history(symbol, side, entry, exit_p, lot, pnl):
    record = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset": symbol,
        "side": side,
        "entry": entry,
        "exit": exit_p,
        "lot": lot,
        "pnl": pnl
    }
    st.session_state["trade_history"].insert(0, record)


# ฟังก์ชันบันทึกประวัติเงินฝาก-ถอน
def add_transaction(type, amount):
    tx = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": type,
        "amount": amount,
        "balance": st.session_state["balance"]
    }
    st.session_state["transactions"].insert(0, tx)


# ================= 🛡️ ระบบ AUTHENTICATION =================
if not st.session_state["logged_in"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        if not st.session_state["show_register"]:
            st.markdown("<h1 style='text-align: center; color: #FFDF00;'>✨ XAUUSD EXCLUSIVE</h1>",
                        unsafe_allow_html=True)
            user_in = st.text_input("Username", placeholder="👤")
            pass_in = st.text_input("Password", type="password", placeholder="🔑")
            if st.button("AUTHORIZE ACCESS", type="primary", use_container_width=True):
                users = load_users()
                if user_in in users and users[user_in] == pass_in:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = user_in
                    st.rerun()
                else:
                    st.error("❌ Invalid Credentials")
            if st.button("CREATE NEW ACCOUNT", use_container_width=True):
                st.session_state["show_register"] = True
                st.rerun()
        else:
            st.markdown("<h2 style='text-align: center; color: #FFDF00;'>📝 REGISTER</h2>", unsafe_allow_html=True)
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            if st.button("REGISTER NOW", type="primary", use_container_width=True):
                if new_pass == confirm_pass and new_user:
                    users = load_users()
                    users[new_user] = new_pass
                    save_users(users)
                    st.success("✅ Account Created!")
                    st.session_state["show_register"] = False
                    time.sleep(1);
                    st.rerun()
            if st.button("⬅️ BACK TO LOGIN", use_container_width=True):
                st.session_state["show_register"] = False
                st.rerun()

# ================= 📈 หน้า TERMINAL =================
else:
    h_col1, h_col2 = st.columns([8, 2])
    with h_col1:
        st.markdown(
            f"<h3 style='color:#FFDF00;'>⚜️ Terminal | <span style='color:white; font-size:16px;'>User: {st.session_state['username'].upper()}</span></h3>",
            unsafe_allow_html=True)
    with h_col2:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    assets = {"🥇 GOLD (XAUUSD)": "OANDA:XAUUSD", "₿ Bitcoin (BTC)": "BINANCE:BTCUSDT",
              "💎 Ethereum (ETH)": "BINANCE:ETHUSDT", "☀️ Solana (SOL)": "BINANCE:SOLUSDT", "🇪🇺 EUR/USD": "FX:EURUSD",
              "🇬🇧 GBP/USD": "FX:GBPUSD", "🇯🇵 USD/JPY": "FX:USDJPY"}
    if "selected_asset" not in st.session_state: st.session_state["selected_asset"] = "🥇 GOLD (XAUUSD)"
    selected_sym = assets[st.session_state["selected_asset"]]

    components.html(
        f"""<div id="tv_chart_container" style="height: 480px;"></div><script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script><script type="text/javascript">new TradingView.widget({{"autosize": true, "symbol": "{selected_sym}", "interval": "1", "theme": "dark", "style": "1", "container_id": "tv_chart_container", "hide_side_toolbar": false, "allow_symbol_change": true}});</script>""",
        height=480)

    st.write("---")
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([2, 1.5, 2.5, 4])

    with ctrl_col1:
        st.markdown("<div class='gold-text'>📋 Market Watch</div>", unsafe_allow_html=True)
        st.session_state["selected_asset"] = st.selectbox("Asset", list(assets.keys()), label_visibility="collapsed")

    with ctrl_col2:
        st.markdown("<div class='gold-text'>⚡ Volume & TP/SL</div>", unsafe_allow_html=True)
        lot = st.number_input("Lots", value=1.00, step=0.1)
        tp_input = st.number_input("TP Price", value=0.0, step=0.1)
        sl_input = st.number_input("SL Price", value=0.0, step=0.1)

    with ctrl_col3:
        st.markdown("<div class='gold-text'>🚀 Execution</div>", unsafe_allow_html=True)
        b_col, s_col = st.columns(2)
        with b_col:
            if st.button("BUY", key="buy_btn", use_container_width=True):
                st.session_state["position"], st.session_state["active_asset"] = "BUY", selected_sym
                st.session_state["entry_price"] = get_live_price(selected_sym)
                st.session_state["tp_price"], st.session_state["sl_price"], st.session_state[
                    "active_lot"] = tp_input, sl_input, lot
        with s_col:
            if st.button("SELL", key="sell_btn", use_container_width=True):
                st.session_state["position"], st.session_state["active_asset"] = "SELL", selected_sym
                st.session_state["entry_price"] = get_live_price(selected_sym)
                st.session_state["tp_price"], st.session_state["sl_price"], st.session_state[
                    "active_lot"] = tp_input, sl_input, lot
        if st.button("❌ CLOSE ALL", use_container_width=True):
            if st.session_state["position"] != "None":
                pnl = st.session_state.get("current_pnl", 0)
                add_to_history(st.session_state["active_asset"], st.session_state["position"],
                               st.session_state["entry_price"], get_live_price(st.session_state["active_asset"]),
                               st.session_state["active_lot"], pnl)
                st.session_state["balance"] += pnl
                st.session_state["position"] = "None"

    with ctrl_col4:
        st.markdown("<div class='gold-text'>💻 Terminal & Wallet</div>", unsafe_allow_html=True)
        if st.session_state["position"] != "None":
            price_now = get_live_price(st.session_state["active_asset"])
            entry, lot_active = st.session_state["entry_price"], st.session_state["active_lot"]
            pnl = (price_now - entry) * lot_active * 100 if st.session_state["position"] == "BUY" else (
                                                                                                                   entry - price_now) * lot_active * 100
            st.session_state["current_pnl"] = pnl
            # Logic TP/SL
            tp, sl = st.session_state["tp_price"], st.session_state["sl_price"]
            if (st.session_state["position"] == "BUY" and (
                    (tp > 0 and price_now >= tp) or (sl > 0 and price_now <= sl))) or \
                    (st.session_state["position"] == "SELL" and (
                            (tp > 0 and price_now <= tp) or (sl > 0 and price_now >= sl))):
                add_to_history(st.session_state["active_asset"], st.session_state["position"], entry, price_now,
                               lot_active, pnl)
                st.session_state["balance"] += pnl;
                st.session_state["position"] = "None";
                st.rerun()

            st.markdown(
                f'<div class="terminal-box"><b>POS:</b> {st.session_state["position"]} | <b>PnL:</b> <span style="color:{"#00ff88" if pnl >= 0 else "#ff4d4d"}">${pnl:,.2f}</span><br><b>Balance:</b> ${st.session_state["balance"]:,.2f}</div>',
                unsafe_allow_html=True)
            time.sleep(1);
            st.rerun()
        else:
            # ระบบฝากถอนแบบกำหนดเอง
            st.markdown(f"<div class='terminal-box'>Balance: ${st.session_state['balance']:,.2f}</div>",
                        unsafe_allow_html=True)
            amt = st.number_input("Amount to Transfer", min_value=0.0, value=100.0, step=10.0,
                                  label_visibility="collapsed")
            d_col, w_col = st.columns(2)
            with d_col:
                if st.button("➕ DEPOSIT", use_container_width=True):
                    if amt > 0:
                        st.session_state["balance"] += amt
                        add_transaction("DEPOSIT", amt)
                        st.toast(f"Deposited ${amt:,.2f}")
                        st.rerun()
            with w_col:
                if st.button("➖ WITHDRAW", use_container_width=True):
                    if 0 < amt <= st.session_state["balance"]:
                        st.session_state["balance"] -= amt
                        add_transaction("WITHDRAW", amt)
                        st.toast(f"Withdrawn ${amt:,.2f}")
                        st.rerun()
                    else:
                        st.error("Invalid amount or insufficient balance")

    # ================= 📜 SECTION: HISTORIES =================
    hist_col1, hist_col2 = st.columns(2)
    with hist_col1:
        st.markdown("<div class='gold-text'>📜 Trade History</div>", unsafe_allow_html=True)
        if st.session_state["trade_history"]:
            html = "<table class='history-table'><tr><th>Time</th><th>Asset</th><th>Side</th><th>PnL</th></tr>"
            for t in st.session_state["trade_history"][:10]:
                html += f"<tr><td>{t['time'][-8:]}</td><td>{t['asset']}</td><td style='color: {'#00ff88' if t['side'] == 'BUY' else '#ff4d4d'}'>{t['side']}</td><td style='color: {'#00ff88' if t['pnl'] >= 0 else '#ff4d4d'}'>${t['pnl']:,.2f}</td></tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)

    with hist_col2:
        st.markdown("<div class='gold-text'>💳 Transaction History</div>", unsafe_allow_html=True)
        if st.session_state["transactions"]:
            html = "<table class='history-table'><tr><th>Time</th><th>Type</th><th>Amount</th><th>Balance</th></tr>"
            for tx in st.session_state["transactions"][:10]:
                color = "#00ff88" if tx['type'] == "DEPOSIT" else "#ff4d4d"
                html += f"<tr><td>{tx['time'][-8:]}</td><td style='color:{color}'>{tx['type']}</td><td style='color:{color}'>${tx['amount']:,.2f}</td><td>${tx['balance']:,.2f}</td></tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)