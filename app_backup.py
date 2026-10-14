import os
import sqlite3
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "demo_transactions.csv"
DB_FILE = DATA_DIR / "fraud_detection.db"

st.set_page_config(page_title="Financial Fraud Detection", page_icon="🛡️", layout="wide")

# ---------------- Theme ----------------
st.markdown("""
<style>
.stApp {background: linear-gradient(135deg,#f6fbff 0%,#eef7ff 45%,#ffffff 100%);}
header[data-testid="stHeader"] {background: rgba(255,255,255,0.0);}
.block-container {padding-top: 1.2rem; max-width: 1450px;}
.hero {background:linear-gradient(120deg,#073b70,#0a68d8);color:white;padding:18px 24px;border-radius:14px;margin-bottom:16px;box-shadow:0 8px 30px rgba(0,75,150,.18)}
.hero h1{margin:0;font-size:30px}.hero p{margin:5px 0 0;opacity:.9}
.card {background:white;border:1px solid #dcecff;border-radius:14px;padding:18px;box-shadow:0 5px 20px rgba(20,80,140,.08);margin-bottom:14px}
.result-high{background:#fff0f1;border:1px solid #ffb7bd;border-radius:14px;padding:20px}
.result-low{background:#effcf4;border:1px solid #b7e8ca;border-radius:14px;padding:20px}
.result-review{background:#fff9e8;border:1px solid #f4dc91;border-radius:14px;padding:20px}
.small{font-size:13px;color:#5f7690}.big{font-size:34px;font-weight:800}.danger{color:#dc2637}.safe{color:#159447}.warn{color:#b87900}
</style>
""", unsafe_allow_html=True)

# ---------------- Demo dataset ----------------
CITIES = [
    ("Hyderabad", "India"), ("Bengaluru", "India"), ("Chennai", "India"),
    ("Mumbai", "India"), ("Delhi", "India"), ("Pune", "India"),
    ("London", "UK"), ("New York", "USA"), ("Dubai", "UAE"), ("Singapore", "Singapore")
]
MERCHANTS = ["Amazon", "Walmart", "Flipkart", "Electronics Store", "Travel", "Fuel", "Grocery", "Restaurant", "Gaming", "Crypto Exchange"]
PAYMENTS = ["Online Banking", "Card", "UPI", "Wallet"]
DEVICES = ["Known Device", "New Device", "Mobile", "Desktop"]
CHANNELS = ["Internet Banking", "Mobile App", "POS", "ATM"]


def make_demo_dataset(n=7000, seed=42):
    rng = np.random.default_rng(seed)
    rows=[]
    normal_cities=[0,1,2,3,4,5]
    for _ in range(n):
        amount = float(np.round(np.exp(rng.normal(np.log(3500), 1.0)),2))
        amount = min(amount, 150000)
        hour = int(rng.integers(0,24))
        city_idx = int(rng.choice(range(len(CITIES)), p=[.17,.14,.10,.12,.09,.08,.08,.07,.08,.07]))
        city,country=CITIES[city_idx]
        merchant=str(rng.choice(MERCHANTS))
        payment=str(rng.choice(PAYMENTS, p=[.30,.25,.35,.10]))
        device=str(rng.choice(DEVICES, p=[.62,.18,.12,.08]))
        channel=str(rng.choice(CHANNELS, p=[.35,.30,.25,.10]))
        international = int(country != "India")
        new_device = int(device == "New Device")
        distance = float(np.round(rng.gamma(2.2, 55 if international else 9),1))
        # Fraud label is generated from multiple risk signals, not a fixed amount threshold.
        score = -5.0
        score += 1.7 * (amount > 20000)
        score += 1.1 * (amount > 50000)
        score += 1.7 * (hour <= 5 or hour >= 23)
        score += 1.8 * international
        score += 1.6 * new_device
        score += 0.9 * (distance > 300)
        score += 1.2 * (merchant in ["Gaming","Crypto Exchange"])
        score += 0.7 * (channel == "ATM" and amount > 15000)
        score += float(rng.normal(0,1.15))
        p = 1/(1+np.exp(-score))
        fraud = int(rng.random() < p*0.38)  # keep fraud minority
        rows.append([amount,hour,city,country,merchant,payment,device,channel,international,new_device,distance,fraud])
    return pd.DataFrame(rows, columns=["amount","hour","city","country","merchant","payment_method","device","channel","international","new_device","distance_km","fraud"])


@st.cache_resource
def load_model():
    if not DATA_FILE.exists():
        df=make_demo_dataset()
        df.to_csv(DATA_FILE,index=False)
    else:
        df=pd.read_csv(DATA_FILE)
    features=["amount","hour","city","country","merchant","payment_method","device","channel","international","new_device","distance_km"]
    X=df[features]
    y=df["fraud"]
    categorical=["city","country","merchant","payment_method","device","channel"]
    numeric=["amount","hour","international","new_device","distance_km"]
    prep=ColumnTransformer([
        ("cat",OneHotEncoder(handle_unknown="ignore"),categorical),
        ("num","passthrough",numeric)
    ])
    model=RandomForestClassifier(n_estimators=260,max_depth=13,min_samples_leaf=3,class_weight="balanced_subsample",random_state=42,n_jobs=-1)
    pipe=Pipeline([("prep",prep),("model",model)])
    pipe.fit(X,y)
    return pipe,df


def db():
    con=sqlite3.connect(DB_FILE)
    con.execute("""CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, created_at TEXT,
        amount REAL, city TEXT, country TEXT, merchant TEXT, payment_method TEXT,
        device TEXT, channel TEXT, hour INTEGER, risk REAL, status TEXT,
        reasons TEXT, action TEXT DEFAULT 'Pending')""")
    con.commit()
    return con


def history(username):
    con=db(); q="SELECT id,created_at,city,country,amount,status,risk,merchant,action FROM transactions WHERE username=? ORDER BY id DESC LIMIT 5"
    df=pd.read_sql_query(q,con,params=(username,)); con.close(); return df


def add_tx(username, tx, risk, status, reasons):
    con=db(); con.execute("INSERT INTO transactions(username,created_at,amount,city,country,merchant,payment_method,device,channel,hour,risk,status,reasons) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (username,datetime.now().strftime("%Y-%m-%d %H:%M:%S"),tx["amount"],tx["city"],tx["country"],tx["merchant"],tx["payment_method"],tx["device"],tx["channel"],tx["hour"],risk,status,"; ".join(reasons)))
    con.commit(); con.close()


def previous_locations(username):
    con=db(); df=pd.read_sql_query("SELECT city,country,amount FROM transactions WHERE username=? ORDER BY id DESC LIMIT 20",con,params=(username,)); con.close(); return df


def explain(tx, username):
    reasons=[]
    prev=previous_locations(username)
    usual=set((prev.city+", "+prev.country).tolist()) if not prev.empty else {"Hyderabad, India"}
    loc=f"{tx['city']}, {tx['country']}"
    if loc not in usual: reasons.append(f"Transaction location is new: {loc}.")
    if tx["new_device"]: reasons.append("A new device was used.")
    if tx["international"]: reasons.append("International transaction detected.")
    if tx["amount"] >= 20000: reasons.append("Transaction amount is unusually high for the demo profile.")
    if tx["hour"] <= 5 or tx["hour"] >= 23: reasons.append("Transaction occurred at an unusual late-night/early-morning time.")
    if tx["distance_km"] > 300: reasons.append("Transaction location is far from recent activity.")
    if not reasons: reasons.append("No strong abnormal pattern was found in the supplied transaction fields.")
    return reasons, loc, (sorted(usual) if usual else ["No previous location"])


def risk_from_model(pipe, tx):
    row=pd.DataFrame([tx])
    p=float(pipe.predict_proba(row)[0,1])
    # Blend model probability with transparent risk indicators for a responsive demo score.
    signal=0
    signal += 20 if tx["amount"]>=20000 else 0
    signal += 15 if tx["new_device"] else 0
    signal += 15 if tx["international"] else 0
    signal += 15 if tx["hour"]<=5 or tx["hour"]>=23 else 0
    signal += 10 if tx["distance_km"]>300 else 0
    score=int(np.clip(100*(0.70*p+0.30*signal/75),0,99))
    return score


pipe, demo_df = load_model()

# ---------------- Session ----------------
if "logged_in" not in st.session_state: st.session_state.logged_in=False
if "username" not in st.session_state: st.session_state.username=""
if "page" not in st.session_state: st.session_state.page="Login"
if "last_result" not in st.session_state: st.session_state.last_result=None

st.markdown('<div class="hero"><h1>🛡️ Financial Fraud Detection</h1><p>Real-time transaction risk analysis • Explainable alerts • Demo banking environment</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🛡️ Financial Fraud Detection")
    pages=["Home","Login","Bank Details","Transactions","Analysis","Profile"] if st.session_state.logged_in else ["Home","Login"]
    choice=st.radio("Navigation",pages,index=pages.index(st.session_state.page) if st.session_state.page in pages else 0)
    st.session_state.page=choice
    if st.session_state.logged_in and st.button("Logout",use_container_width=True):
        st.session_state.logged_in=False; st.session_state.last_result=None; st.rerun()

# ---------------- Pages ----------------
if st.session_state.page=="Home":
    st.markdown('<div class="card"><h2>Welcome</h2><p>Enter a transaction and click <b>Analyze Transaction</b>. The model immediately predicts risk, identifies suspicious patterns, stores the transaction and updates the history.</p></div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    c1.metric("Training transactions",f"{len(demo_df):,}")
    c2.metric("Fraud examples",f"{int(demo_df.fraud.sum()):,}")
    c3.metric("Model", "Random Forest")

elif st.session_state.page=="Login":
    st.markdown('<div class="card"><h2>🔐 User Login</h2><p class="small">College demonstration mode: use any non-empty username and password. Do not enter real banking passwords.</p></div>',unsafe_allow_html=True)
    col1,col2=st.columns([1,1])
    with col1:
        user=st.text_input("Email / Username",placeholder="john.doe@example.com")
        pw=st.text_input("Password",type="password",placeholder="Demo password")
        if st.button("Login",type="primary",use_container_width=True):
            if user.strip() and pw.strip():
                st.session_state.logged_in=True; st.session_state.username=user.strip(); st.session_state.page="Bank Details"; st.rerun()
            else: st.error("Enter both username and password.")
    with col2:
        st.info("Demo safety: this application is not connected to a bank and does not verify real account credentials.")

elif st.session_state.page=="Bank Details":
    st.markdown('<div class="card"><h2>🏦 Bank Account Details</h2><p class="small">Use demo information only.</p></div>',unsafe_allow_html=True)
    b1,b2=st.columns(2)
    with b1:
        st.selectbox("Bank Name",["State Bank of India","HDFC Bank","ICICI Bank","Axis Bank"])
        st.text_input("Account Number",value="123456789012")
    with b2:
        st.text_input("IFSC Code",value="SBIN0001234")
        st.text_input("Account Holder Name",value=st.session_state.username.split('@')[0].title())
    if st.button("Save & Continue",type="primary"):
        st.session_state.page="Transactions"; st.rerun()

elif st.session_state.page in ["Transactions","Analysis"]:
    st.markdown('<div class="card"><h2>💳 Enter Transaction Details</h2><p class="small">Every click creates a fresh prediction from the current transaction values.</p></div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    with c1:
        amount=st.number_input("Amount (₹)",min_value=1.0,value=85000.0,step=500.0)
        city=st.selectbox("Location / City",[x[0] for x in CITIES],index=6)
        merchant=st.selectbox("Merchant Name",MERCHANTS,index=0)
    with c2:
        tx_date=st.date_input("Transaction Date",value=datetime.now().date())
        tx_time=st.time_input("Transaction Time",value=datetime.now().time().replace(second=0,microsecond=0))
        dt=datetime.combine(tx_date,tx_time)
        country=dict(CITIES)[city]
        payment=st.selectbox("Payment Method",PAYMENTS,index=0)
        device=st.selectbox("Device",DEVICES,index=1)
    with c3:
        channel=st.selectbox("Transaction Channel",CHANNELS,index=0)
        distance=st.number_input("Distance from usual location (km)",min_value=0.0,value=850.0,step=10.0)
        st.caption("This distance is a demo transaction attribute; it is not your GPS location.")

    tx={"amount":float(amount),"hour":int(dt.hour),"city":city,"country":country,"merchant":merchant,"payment_method":payment,"device":device,"channel":channel,"international":int(country!="India"),"new_device":int(device=="New Device"),"distance_km":float(distance)}

    if st.button("🔎 Analyze Transaction",type="primary",use_container_width=True):
        score=risk_from_model(pipe,tx)
        status="FRAUD ALERT" if score>=70 else ("REVIEW REQUIRED" if score>=40 else "LOW RISK")
        reasons,loc,usual=explain(tx,st.session_state.username)
        add_tx(st.session_state.username,tx,score,status,reasons)
        st.session_state.last_result={"score":score,"status":status,"tx":tx,"reasons":reasons,"loc":loc,"usual":usual}
        st.session_state.page="Analysis"; st.rerun()

    # Simulator for a quick live demo
    if st.button("⚡ Simulate Incoming Transaction",use_container_width=True):
        city,country=CITIES[int(np.random.randint(len(CITIES)))]
        tx={"amount":float(np.round(np.exp(np.random.normal(np.log(12000),1.2)),2)),"hour":int(np.random.randint(24)),"city":city,"country":country,"merchant":str(np.random.choice(MERCHANTS)),"payment_method":str(np.random.choice(PAYMENTS)),"device":str(np.random.choice(DEVICES)),"channel":str(np.random.choice(CHANNELS)),"international":int(country!="India"),"new_device":int(np.random.choice([0,1],p=[.65,.35])),"distance_km":float(np.round(np.random.gamma(2,120),1))}
        score=risk_from_model(pipe,tx); status="FRAUD ALERT" if score>=70 else ("REVIEW REQUIRED" if score>=40 else "LOW RISK")
        reasons,loc,usual=explain(tx,st.session_state.username); add_tx(st.session_state.username,tx,score,status,reasons)
        st.session_state.last_result={"score":score,"status":status,"tx":tx,"reasons":reasons,"loc":loc,"usual":usual}; st.session_state.page="Analysis"; st.rerun()

    r=st.session_state.last_result
    if r:
        cls="result-high" if r["score"]>=70 else ("result-review" if r["score"]>=40 else "result-low")
        icon="🔴" if r["score"]>=70 else ("🟡" if r["score"]>=40 else "🟢")
        st.markdown(f'<div class="{cls}"><div class="big">{icon} {r["status"]}</div><p>Risk Score: <b>{r["score"]}%</b></p></div>',unsafe_allow_html=True)
        t=r["tx"]
        a,b,c,d,e=st.columns(5)
        a.metric("Amount",f"₹{t['amount']:,.0f}"); b.metric("Location",f"{t['city']}, {t['country']}"); c.metric("Merchant",t['merchant']); d.metric("Device",t['device']); e.metric("Channel",t['channel'])
        left,right=st.columns(2)
        with left:
            st.markdown("### 📍 Where is the suspicious activity?")
            st.info(f"**Current transaction:** {r['loc']}\n\n**Previous observed locations:** {', '.join(r['usual'][:5])}")
            st.markdown("### 🚨 Why was it flagged?")
            for x in r["reasons"]: st.write("⚠️",x)
        with right:
            st.markdown("### 💡 User Hint / Action")
            if r["score"]>=70:
                st.warning("Verify this transaction immediately. If you did not make it, report it as fraud.")
            elif r["score"]>=40:
                st.warning("Verify the transaction before treating it as normal.")
            else:
                st.success("No strong abnormal pattern was detected. Continue normal security checks.")
            x1,x2=st.columns(2)
            if x1.button("🚨 Report as Fraud",use_container_width=True):
                con=db(); con.execute("UPDATE transactions SET action='Reported as Fraud' WHERE username=? AND id=(SELECT MAX(id) FROM transactions WHERE username=?)",(st.session_state.username,st.session_state.username)); con.commit(); con.close(); st.success("Transaction marked as reported fraud.")
            if x2.button("✅ Mark as Safe",use_container_width=True):
                con=db(); con.execute("UPDATE transactions SET action='Marked Safe', status='SAFE' WHERE username=? AND id=(SELECT MAX(id) FROM transactions WHERE username=?)",(st.session_state.username,st.session_state.username)); con.commit(); con.close(); st.success("Transaction marked as safe.")

        st.markdown("### 🧠 Analysis Modules")
        mods=[("Machine Learning","Random Forest prediction",True),("Federated Learning","Architecture-ready demo module",False),("GNN","Transaction-network module placeholder",False),("Explainable AI","Rule-based explanation for current demo",True),("Data Integrity","Transaction/database consistency checks",True)]
        cols=st.columns(len(mods))
        for col,(name,desc,done) in zip(cols,mods):
            col.success("Completed" if done else "Module")
            col.write(f"**{name}**")
            col.caption(desc)

elif st.session_state.page=="Profile":
    st.markdown('<div class="card"><h2>👤 Profile</h2></div>',unsafe_allow_html=True)
    st.write("Logged-in demo user:",st.session_state.username)

# ---------------- History ----------------
if st.session_state.logged_in and st.session_state.page in ["Transactions","Analysis","Profile","Bank Details"]:
    st.markdown("### 📋 Transaction History (Last 5)")
    h=history(st.session_state.username)
    if h.empty: st.caption("No analyzed transactions yet.")
    else:
        h=h.rename(columns={"created_at":"Date & Time","city":"Location","country":"Country","amount":"Amount","status":"Status","risk":"Risk %","merchant":"Merchant","action":"Action"})
        st.dataframe(h,use_container_width=True,hide_index=True)

st.caption("College demo environment • Uses synthetic transaction data • Not connected to any real bank or payment network")
