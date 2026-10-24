import os
import sqlite3
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from fraudguard_ai import show_fraudguard_ai
from incoming_money import show_incoming_money
from gnn_model import FraudGNN, create_sample_transactions
from bank_complaint import show_bank_complaint
from investigation_system import (
    show_report_suspicious_transaction,
    show_track_my_case,
    show_manager_dashboard
)
from auth_system import (
    create_users_table,
    validate_email,
    validate_password,
    create_user,
    authenticate_user,
    show_password_requirements
)

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# ============================================================
# PROJECT PATHS
# ============================================================

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(exist_ok=True)

DATA_FILE = DATA_DIR / "demo_transactions.csv"
DB_FILE = DATA_DIR / "fraud_detection.db"


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Financial Fraud Detection",
    page_icon="🛡️",
    layout="wide"
)


# ============================================================
# THEME
# ============================================================

st.markdown(
    """
    <style>

    /* Main application */
    .stApp {
        background: linear-gradient(
            135deg,
            #f6fbff 0%,
            #eef7ff 45%,
            #ffffff 100%
        );
    }

    header[data-testid="stHeader"] {
        background: rgba(255,255,255,0);
    }

    .block-container {
        padding-top: 1.2rem;
        max-width: 1450px;
    }

    /* Normal page hero */
    .hero {
        background: linear-gradient(
            120deg,
            #073b70,
            #0a68d8
        );
        color: white;
        padding: 18px 24px;
        border-radius: 14px;
        margin-bottom: 16px;
        box-shadow: 0 8px 30px rgba(0,75,150,.18);
    }

    .hero h1 {
        margin: 0;
        font-size: 30px;
    }

    .hero p {
        margin: 5px 0 0;
        opacity: .9;
    }

    /* Cards */
    .card {
        background: white;
        border: 1px solid #dcecff;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 5px 20px rgba(20,80,140,.08);
        margin-bottom: 14px;
    }

    /* Analysis result cards */
    .result-high {
        background: #fff0f1;
        border: 1px solid #ffb7bd;
        border-radius: 14px;
        padding: 20px;
    }

    .result-low {
        background: #effcf4;
        border: 1px solid #b7e8ca;
        border-radius: 14px;
        padding: 20px;
    }

    .result-review {
        background: #fff9e8;
        border: 1px solid #f4dc91;
        border-radius: 14px;
        padding: 20px;
    }

    .small {
        font-size: 13px;
        color: #5f7690;
    }

    .big {
        font-size: 34px;
        font-weight: 800;
    }

    .danger {
        color: #dc2637;
    }

    .safe {
        color: #159447;
    }

    .warn {
        color: #b87900;
    }


    /* ========================================================
       LOGIN PAGE
       ======================================================== */

    .login-page {
        background:
            radial-gradient(
                circle at 15% 20%,
                rgba(0,190,255,.35),
                transparent 30%
            ),
            radial-gradient(
                circle at 85% 75%,
                rgba(0,120,255,.30),
                transparent 30%
            ),
            linear-gradient(
                135deg,
                #02163d 0%,
                #063b7d 45%,
                #078dd0 100%
            );

        min-height: 82vh;
        border-radius: 24px;
        padding: 50px 30px;
        box-shadow:
            0 20px 60px rgba(0,50,120,.30);
    }

    .login-bank-symbol {
        text-align: center;
        font-size: 70px;
        margin-bottom: 5px;
    }

    .login-title {
        text-align: center;
        color: #073b78;
        font-size: 30px;
        font-weight: 800;
        margin-bottom: 25px;
    }

    .login-box {
        background: rgba(255,255,255,.97);
        border-radius: 24px;
        padding: 35px;
        box-shadow:
            0 20px 55px rgba(0,0,0,.25);
        max-width: 440px;
        margin: auto;
    }

    /* Login inputs */
    div[data-testid="stTextInput"] input {
        background: white !important;
        color: #12345b !important;
        border: 2px solid #cfe4f5 !important;
        border-radius: 12px !important;
        height: 48px !important;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #078be0 !important;
        box-shadow: 0 0 0 2px rgba(7,139,224,.15) !important;
    }

    div[data-testid="stTextInput"] label {
        color: #12345b !important;
        font-weight: 700 !important;
    }

    /* Login button */
    div.stButton > button {
        width: 100%;
        height: 50px;
        border-radius: 12px;
        border: none;
        background: linear-gradient(
            90deg,
            #0878ed,
            #08b8ed
        );
        color: white;
        font-size: 16px;
        font-weight: 800;
        box-shadow: 0 8px 22px rgba(0,120,255,.35);
    }

    div.stButton > button:hover {
        background: linear-gradient(
            90deg,
            #0565d8,
            #00a8df
        );
        color: white;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# DEMO DATA
# ============================================================

CITIES = [
    ("Hyderabad", "India"),
    ("Bengaluru", "India"),
    ("Chennai", "India"),
    ("Mumbai", "India"),
    ("Delhi", "India"),
    ("Pune", "India"),
    ("London", "UK"),
    ("New York", "USA"),
    ("Dubai", "UAE"),
    ("Singapore", "Singapore")
]

MERCHANTS = [
    "Amazon",
    "Walmart",
    "Flipkart",
    "Electronics Store",
    "Travel",
    "Fuel",
    "Grocery",
    "Restaurant",
    "Gaming",
    "Crypto Exchange"
]

PAYMENTS = [
    "Online Banking",
    "Card",
    "UPI",
    "Wallet"
]

DEVICES = [
    "Known Device",
    "New Device",
    "Mobile",
    "Desktop"
]

CHANNELS = [
    "Internet Banking",
    "Mobile App",
    "POS",
    "ATM"
]


# ============================================================
# DEMO DATASET GENERATION
# ============================================================

def make_demo_dataset(n=7000, seed=42):

    rng = np.random.default_rng(seed)

    rows = []

    for _ in range(n):

        amount = float(
            np.round(
                np.exp(
                    rng.normal(
                        np.log(500),
                        0.8
                    )
                ),
                2
            )
        )

        amount = min(amount, 10000)

        hour = int(rng.integers(0, 24))

        city_idx = int(
            rng.choice(
                range(len(CITIES)),
                p=[
                    .17,
                    .14,
                    .10,
                    .12,
                    .09,
                    .08,
                    .08,
                    .07,
                    .08,
                    .07
                ]
            )
        )

        city, country = CITIES[city_idx]

        merchant = str(
            rng.choice(MERCHANTS)
        )

        payment = str(
            rng.choice(
                PAYMENTS,
                p=[.30, .25, .35, .10]
            )
        )

        device = str(
            rng.choice(
                DEVICES,
                p=[.62, .18, .12, .08]
            )
        )

        channel = str(
            rng.choice(
                CHANNELS,
                p=[.35, .30, .25, .10]
            )
        )

        international = int(
            country != "India"
        )

        new_device = int(
            device == "New Device"
        )

        distance = float(
            np.round(
                rng.gamma(
                    2.2,
                    55 if international else 9
                ),
                1
            )
        )

        # Fraud label generated from multiple risk signals

        score = -5.0

        score += 1.7 * (amount > 1000)
        score += 1.1 * (amount > 3000)
        score += 1.7 * (
            hour <= 5 or hour >= 23
        )
        score += 1.8 * international
        score += 1.6 * new_device
        score += 0.9 * (distance > 50)
        score += 1.2 * (
            merchant in [
                "Gaming",
                "Crypto Exchange"
            ]
        )
        score += 0.7 * (
            channel == "ATM" and amount > 500
        )

        score += float(
            rng.normal(0, 1.15)
        )

        p = 1 / (
            1 + np.exp(-score)
        )

        fraud = int(
            rng.random() < p * 0.38
        )

        rows.append(
            [
                amount,
                hour,
                city,
                country,
                merchant,
                payment,
                device,
                channel,
                international,
                new_device,
                distance,
                fraud
            ]
        )

    return pd.DataFrame(
        rows,
        columns=[
            "amount",
            "hour",
            "city",
            "country",
            "merchant",
            "payment_method",
            "device",
            "channel",
            "international",
            "new_device",
            "distance_km",
            "fraud"
        ]
    )


# ============================================================
# MACHINE LEARNING MODEL
# ============================================================

@st.cache_resource
def load_model():

    if not DATA_FILE.exists():

        df = make_demo_dataset()

        df.to_csv(
            DATA_FILE,
            index=False
        )

    else:

        df = pd.read_csv(
            DATA_FILE
        )

    features = [
        "amount",
        "hour",
        "city",
        "country",
        "merchant",
        "payment_method",
        "device",
        "channel",
        "international",
        "new_device",
        "distance_km"
    ]

    X = df[features]

    y = df["fraud"]

    categorical = [
        "city",
        "country",
        "merchant",
        "payment_method",
        "device",
        "channel"
    ]

    numeric = [
        "amount",
        "hour",
        "international",
        "new_device",
        "distance_km"
    ]

    prep = ColumnTransformer(
        [
            (
                "cat",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                categorical
            ),
            (
                "num",
                "passthrough",
                numeric
            )
        ]
    )

    model = RandomForestClassifier(
        n_estimators=260,
        max_depth=13,
        min_samples_leaf=3,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1
    )

    pipe = Pipeline(
        [
            ("prep", prep),
            ("model", model)
        ]
    )

    pipe.fit(X, y)

    return pipe, df


# ============================================================
# DATABASE
# ============================================================

def db():

    con = sqlite3.connect(
        DB_FILE
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            created_at TEXT,
            amount REAL,
            city TEXT,
            country TEXT,
            merchant TEXT,
            payment_method TEXT,
            device TEXT,
            channel TEXT,
            hour INTEGER,
            risk REAL,
            status TEXT,
            reasons TEXT,
            action TEXT DEFAULT 'Pending'
        )
        """
    )

    con.commit()

    return con


def history(username):

    con = db()

    query = """
        SELECT
            id,
            created_at,
            city,
            country,
            amount,
            status,
            risk,
            merchant,
            action
        FROM transactions
        WHERE username=?
        ORDER BY id DESC
        LIMIT 5
    """

    df = pd.read_sql_query(
        query,
        con,
        params=(username,)
    )

    con.close()

    return df


def add_tx(
    username,
    tx,
    risk,
    status,
    reasons
):

    con = db()

    con.execute(
        """
        INSERT INTO transactions(
            username,
            created_at,
            amount,
            city,
            country,
            merchant,
            payment_method,
            device,
            channel,
            hour,
            risk,
            status,
            reasons
        )
        VALUES(
            ?,?,?,?,?,?,?,?,?,?,?,?,?
        )
        """,
        (
            username,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            tx["amount"],
            tx["city"],
            tx["country"],
            tx["merchant"],
            tx["payment_method"],
            tx["device"],
            tx["channel"],
            tx["hour"],
            risk,
            status,
            "; ".join(reasons)
        )
    )

    con.commit()

    con.close()


def previous_locations(username):

    con = db()

    df = pd.read_sql_query(
        """
        SELECT city,country,amount
        FROM transactions
        WHERE username=?
        ORDER BY id DESC
        LIMIT 20
        """,
        con,
        params=(username,)
    )

    con.close()

    return df


# ============================================================
# EXPLAINABLE RISK REASONS
# ============================================================

def explain(tx, username):

    reasons = []

    prev = previous_locations(
        username
    )

    if not prev.empty:

        usual = set(
            (
                prev.city
                + ", "
                + prev.country
            ).tolist()
        )

    else:

        usual = {
            "Hyderabad, India"
        }

    loc = (
        f"{tx['city']}, "
        f"{tx['country']}"
    )

    if loc not in usual:

        reasons.append(
            f"Transaction location is new: {loc}."
        )

    if tx["new_device"]:

        reasons.append(
            "A new device was used."
        )

    if tx["international"]:

        reasons.append(
            "International transaction detected."
        )

    if tx["amount"] >= 1000:

        reasons.append(
            "Transaction amount is unusually high for the demo profile."
        )

    if (
        tx["hour"] <= 5
        or tx["hour"] >= 23
    ):

        reasons.append(
            "Transaction occurred at an unusual late-night/early-morning time."
        )

    if tx["distance_km"] > 50:

        reasons.append(
            "Transaction location is far from recent activity."
        )

    if not reasons:

        reasons.append(
            "No strong abnormal pattern was found in the supplied transaction fields."
        )

    return (
        reasons,
        loc,
        sorted(usual)
        if usual
        else ["No previous location"]
    )


# ============================================================
# RISK SCORE
# ============================================================

def risk_from_model(pipe, tx):

    row = pd.DataFrame(
        [tx]
    )

    p = float(
        pipe.predict_proba(row)[0, 1]
    )

    signal = 0

    signal += (
        20
        if tx["amount"] >= 1000
        else 0
    )

    signal += (
        15
        if tx["new_device"]
        else 0
    )

    signal += (
        15
        if tx["international"]
        else 0
    )

    signal += (
        15
        if (
            tx["hour"] <= 5
            or tx["hour"] >= 23
        )
        else 0
    )

    signal += (
        10
        if tx["distance_km"] > 50
        else 0
    )

    score = int(
        np.clip(
            100 * (
                0.70 * p
                + 0.30 * signal / 75
            ),
            0,
            99
        )
    )

    return score


# ============================================================
# LOAD MODEL
# ============================================================

pipe, demo_df = load_model()


# ============================================================
# SESSION
# ============================================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False

if "username" not in st.session_state:

    st.session_state.username = ""

if "page" not in st.session_state:

    st.session_state.page = "Login"

if "last_result" not in st.session_state:

    st.session_state.last_result = None

if "account_balance" not in st.session_state:

    st.session_state.account_balance = 10000.0


# ============================================================
# SIDEBAR
# ============================================================

if st.session_state.page != "Login":

    st.markdown(
        """
        <div class="hero">
            <h1>🛡️ Financial Fraud Detection</h1>
            <p>
                Real-time transaction risk analysis
                • Explainable alerts
                • Demo banking environment
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


with st.sidebar:

    st.markdown(
        "### 🛡️ Financial Fraud Detection"
    )

    pages = (
        [
            "Home",
            "Login",
            "Bank Details",
            "Transactions",
            "Incoming Money",
            "Analysis",
            "GNN Analysis",
            "Bank Fraud Complaint",
            "Report Suspicious Transaction",
            "Track My Fraud Case",
            "Manager Dashboard",
            "Profile"
        ]
        if st.session_state.logged_in
        else [
            "Home",
            "Login"
        ]
    )

    choice = st.radio(
        "Navigation",
        pages,
        index=(
            pages.index(
                st.session_state.page
            )
            if st.session_state.page in pages
            else 0
        )
    )

    st.session_state.page = choice

    if (
        st.session_state.logged_in
        and st.button(
            "Logout",

        )
    ):

        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.last_result = None
        st.session_state.page = "Login"

        st.rerun()


# ============================================================
# HOME
# ============================================================

if st.session_state.page == "Home":

    st.markdown(
        """
        <div class="card">
            <h2>Welcome</h2>
            <p>
                Enter a transaction and click
                <b>Analyze Transaction</b>.
                The model immediately predicts risk,
                identifies suspicious patterns,
                stores the transaction and updates
                the history.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Training transactions",
        f"{len(demo_df):,}"
    )

    c2.metric(
        "Fraud examples",
        f"{int(demo_df.fraud.sum()):,}"
    )

    c3.metric(
        "Model",
        "Random Forest"
    )

    if st.session_state.logged_in:
        st.markdown(
            f"""
            <div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                <h3 style="margin: 0; color: white;">💰 Account Balance</h3>
                <p style="margin: 5px 0 0; font-size: 28px; font-weight: bold; color: white;">
                    ₹{st.session_state.account_balance:,.2f}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# LOGIN
# ============================================================

elif st.session_state.page == "Login":

    # Initialize users table
    create_users_table()

    # Toggle between Login and Create Account
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {
            display:none !important;
        }

        .login-container {
            max-width: 450px;
            margin: 100px auto;
            padding: 40px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }

        .login-title {
            text-align: center;
            margin-bottom: 30px;
        }

        .login-title h1 {
            color: #073b78;
            font-size: 32px;
            margin: 0;
        }

        .login-title p {
            color: #666;
            margin: 10px 0 0;
        }

        div[data-testid="stTextInput"] input {
            background: #f8f9fa !important;
            border: 2px solid #e9ecef !important;
            border-radius: 10px !important;
            padding: 12px 16px !important;
            font-size: 16px !important;
        }

        div[data-testid="stTextInput"] input:focus {
            border-color: #087be0 !important;
            box-shadow: 0 0 0 3px rgba(8,123,224,0.1) !important;
        }

        div[data-testid="stTextInput"] label {
            color: #073b78 !important;
            font-weight: 600 !important;
            font-size: 14px !important;
        }

        div.stButton > button {
            width: 100% !important;
            height: 50px !important;
            border-radius: 10px !important;
            border: none !important;
            background: linear-gradient(90deg, #0878ed, #08b8ed) !important;
            color: white !important;
            font-size: 16px !important;
            font-weight: 700 !important;
            margin-top: 20px !important;
        }

        div.stButton > button:hover {
            background: linear-gradient(90deg, #0565d8, #00a8df) !important;
        }

        .auth-toggle {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }

        .auth-toggle button {
            flex: 1;
            padding: 10px;
            border-radius: 8px;
            border: 2px solid #e9ecef;
            background: white;
            color: #666;
            font-weight: 600;
        }

        .auth-toggle button.active {
            background: linear-gradient(90deg, #0878ed, #08b8ed);
            color: white;
            border-color: #0878ed;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="login-container">
            <div class="login-title">
                <h1>🛡️ Financial Fraud Detection</h1>
                <p>Secure Login System</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Toggle buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", type="primary" if st.session_state.auth_mode == "login" else "secondary", key="toggle_login"):
            st.session_state.auth_mode = "login"
            st.rerun()
    with col2:
        if st.button("Create Account", type="primary" if st.session_state.auth_mode == "register" else "secondary", key="toggle_register"):
            st.session_state.auth_mode = "register"
            st.rerun()

    st.markdown("---")

    if st.session_state.auth_mode == "login":
        # Login Form
        st.markdown("### 🔐 Login")
        
        user = st.text_input("Username", placeholder="Enter your username", key="login_username")
        pw = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")

        if st.button("Login", type="primary", key="login_button"):
            if user.strip() and pw.strip():
                success, user_data, message = authenticate_user(user.strip(), pw.strip())
                
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = user_data['username']
                    st.session_state.full_name = user_data['full_name']
                    st.session_state.email = user_data['email']
                    st.session_state.page = "Bank Details"
                    st.success(f"✅ Welcome back, {user_data['full_name']}!")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("Please enter both username and password.")
        
        st.info("💡 Don't have an account? Click 'Create Account' above to register.")

    else:
        # Create Account Form
        st.markdown("### 📝 Create Account")
        
        full_name = st.text_input("Full Name *", placeholder="Enter your full name", key="register_fullname")
        email = st.text_input("Email Address *", placeholder="Enter your email", key="register_email")
        username = st.text_input("Username *", placeholder="Choose a username", key="register_username")
        password = st.text_input("Password *", type="password", placeholder="Create a strong password", key="register_password")
        confirm_password = st.text_input("Confirm Password *", type="password", placeholder="Confirm your password", key="register_confirm")

        # Show password requirements
        show_password_requirements()

        if st.button("Create Account", type="primary", key="register_button"):
            # Validate all fields
            errors = []
            
            if not full_name.strip():
                errors.append("Full name is required")
            
            # Validate email
            email_valid, email_msg = validate_email(email.strip())
            if not email_valid:
                errors.append(email_msg)
            
            if not username.strip():
                errors.append("Username is required")
            
            if not password:
                errors.append("Password is required")
            
            if not confirm_password:
                errors.append("Please confirm your password")
            
            # Validate password strength
            if password:
                password_valid, password_errors = validate_password(password)
                if not password_valid:
                    errors.extend(password_errors)
            
            # Check password match
            if password and confirm_password and password != confirm_password:
                errors.append("Passwords do not match")
            
            # Display errors
            if errors:
                st.error("❌ Please fix the following issues:")
                for error in errors:
                    st.write(f"• {error}")
            else:
                # Check if email or username already exists
                if check_email_exists(email.strip()):
                    st.error("❌ Email already registered. Please use a different email or login.")
                elif check_username_exists(username.strip()):
                    st.error("❌ Username already taken. Please choose a different username.")
                else:
                    # Create user
                    success, message = create_user(
                        username.strip(),
                        email.strip(),
                        full_name.strip(),
                        password
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.info("👉 Your account has been created! Click 'Login' above to sign in with your new credentials.")
                    else:
                        st.error(f"❌ {message}")
        
        st.info("💡 Already have an account? Click 'Login' above to sign in.")

# ============================================================
# BANK DETAILS
# ============================================================

elif st.session_state.page == "Bank Details":

    st.markdown(
        """
        <div class="card">
            <h2>🏦 Bank Account Details</h2>
            <p class="small">
                Use demo information only.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    b1, b2 = st.columns(2)

    with b1:

        st.selectbox(
            "Bank Name",
            [
                "State Bank of India",
                "HDFC Bank",
                "ICICI Bank",
                "Axis Bank"
            ]
        )

        st.text_input(
            "Account Number",
            value="123456789012"
        )

    with b2:

        st.text_input(
            "IFSC Code",
            value="SBIN0001234"
        )

        st.text_input(
            "Account Holder Name",
            value=(
                st.session_state.username
                .split("@")[0]
                .title()
            )
        )

    balance = st.number_input(
        "Account Balance (₹)",
        min_value=0.0,
        value=10000.0,
        step=500.0
    )

    if st.button(
        "Save & Continue",
        type="primary"
    ):

        st.session_state.account_balance = balance
        st.session_state.page = "Transactions"

        st.rerun()


# ============================================================
# TRANSACTIONS / ANALYSIS
# ============================================================

elif st.session_state.page in [
    "Transactions",
    "Analysis"
]:

    st.markdown(
        """
        <div class="card">
            <h2>💳 Enter Transaction Details</h2>
            <p class="small">
                Every click creates a fresh prediction
                from the current transaction values.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Display account balance
    st.markdown(
        f"""
        <div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
            <h3 style="margin: 0; color: white;">💰 Account Balance</h3>
            <p style="margin: 5px 0 0; font-size: 28px; font-weight: bold; color: white;">
                ₹{st.session_state.account_balance:,.2f}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    c1, c2, c3 = st.columns(3)

    with c1:

        amount = st.number_input(
            "Amount (₹)",
            min_value=1.0,
            value=500.0,
            step=50.0
        )

        city = st.selectbox(
            "Location / City",
            [x[0] for x in CITIES],
            index=0,
            key="city"
        )

        merchant = st.selectbox(
            "Merchant Name",
            MERCHANTS,
            index=0,
            key="merchant"
        )

    with c2:

        tx_date = st.date_input(
            "Transaction Date",
            value=datetime.now().date()
        )

        tx_time = st.time_input(
            "Transaction Time",
            value=datetime.now()
            .time()
            .replace(
                second=0,
                microsecond=0
            )
        )

        dt = datetime.combine(
            tx_date,
            tx_time
        )

        country = dict(
            CITIES
        )[city]

        payment = st.selectbox(
            "Payment Method",
            PAYMENTS,
            index=0,
            key="payment"
        )

        device = st.selectbox(
            "Device",
            DEVICES,
            index=1,
            key="device"
        )

    with c3:

        channel = st.selectbox(
            "Transaction Channel",
            CHANNELS,
            index=0
        )

        distance = st.number_input(
            "Distance from usual location (km)",
            min_value=0.0,
            value=20.0,
            step=5.0
        )

        st.caption(
            "This distance is a demo transaction attribute; "
            "it is not your GPS location."
        )

    tx = {
        "amount": float(amount),
        "hour": int(dt.hour),
        "city": city,
        "country": country,
        "merchant": merchant,
        "payment_method": payment,
        "device": device,
        "channel": channel,
        "international": int(
            country != "India"
        ),
        "new_device": int(
            device == "New Device"
        ),
        "distance_km": float(distance)
    }

    if st.button(
        "🔎 Analyze Transaction",
        type="primary"
    ):

        score = risk_from_model(
            pipe,
            tx
        )

        status = (
            "FRAUD ALERT"
            if score >= 70
            else (
                "REVIEW REQUIRED"
                if score >= 40
                else "LOW RISK"
            )
        )

        reasons, loc, usual = explain(
            tx,
            st.session_state.username
        )

        add_tx(
            st.session_state.username,
            tx,
            score,
            status,
            reasons
        )

        # Update account balance (deduct transaction amount)
        st.session_state.account_balance -= amount

        st.session_state.last_result = {
            "score": score,
            "status": status,
            "tx": tx,
            "reasons": reasons,
            "loc": loc,
            "usual": usual
        }

        st.session_state.page = "Analysis"

        st.rerun()

    # ========================================================
    # SIMULATOR
    # ========================================================

    if st.button(
        "⚡ Simulate Incoming Transaction"
    ):

        city, country = CITIES[
            int(
                np.random.randint(
                    len(CITIES)
                )
            )
        ]

        tx = {
            "amount": float(
                np.round(
                    np.exp(
                        np.random.normal(
                            np.log(500),
                            0.5
                        )
                    ),
                    2
                )
            ),
            "hour": int(
                np.random.randint(24)
            ),
            "city": city,
            "country": country,
            "merchant": str(
                np.random.choice(
                    MERCHANTS
                )
            ),
            "payment_method": str(
                np.random.choice(
                    PAYMENTS
                )
            ),
            "device": str(
                np.random.choice(
                    DEVICES
                )
            ),
            "channel": str(
                np.random.choice(
                    CHANNELS
                )
            ),
            "international": int(
                country != "India"
            ),
            "new_device": int(
                np.random.choice(
                    [0, 1],
                    p=[.65, .35]
                )
            ),
            "distance_km": float(
                np.round(
                    np.random.gamma(
                        2,
                        15
                    ),
                    1
                )
            )
        }

        score = risk_from_model(
            pipe,
            tx
        )

        status = (
            "FRAUD ALERT"
            if score >= 70
            else (
                "REVIEW REQUIRED"
                if score >= 40
                else "LOW RISK"
            )
        )

        reasons, loc, usual = explain(
            tx,
            st.session_state.username
        )

        add_tx(
            st.session_state.username,
            tx,
            score,
            status,
            reasons
        )

        # Update account balance (deduct transaction amount)
        st.session_state.account_balance -= tx["amount"]

        st.session_state.last_result = {
            "score": score,
            "status": status,
            "tx": tx,
            "reasons": reasons,
            "loc": loc,
            "usual": usual
        }

        st.session_state.page = "Analysis"

        st.rerun()

    # ========================================================
    # ANALYSIS RESULT
    # ========================================================

    r = st.session_state.last_result

    if r:

        cls = (
            "result-high"
            if r["score"] >= 70
            else (
                "result-review"
                if r["score"] >= 40
                else "result-low"
            )
        )

        icon = (
            "🔴"
            if r["score"] >= 70
            else (
                "🟡"
                if r["score"] >= 40
                else "🟢"
            )
        )

        st.markdown(
            f"""
            <div class="{cls}">
                <div class="big">
                    {icon} {r["status"]}
                </div>
                <p>
                    Risk Score:
                    <b>{r["score"]}%</b>
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Display updated account balance
        st.markdown(
            f"""
            <div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                <h3 style="margin: 0; color: white;">💰 Updated Account Balance</h3>
                <p style="margin: 5px 0 0; font-size: 28px; font-weight: bold; color: white;">
                    ₹{st.session_state.account_balance:,.2f}
                </p>
                <p style="margin: 5px 0 0; font-size: 14px; color: white;">
                    Transaction amount: ₹{r['tx']['amount']:,.2f} deducted
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        t = r["tx"]

        a, b, c, d, e = st.columns(5)

        a.metric(
            "Amount",
            f"₹{t['amount']:,.0f}"
        )

        b.metric(
            "Location",
            f"{t['city']}, {t['country']}"
        )

        c.metric(
            "Merchant",
            t["merchant"]
        )

        d.metric(
            "Device",
            t["device"]
        )

        e.metric(
            "Channel",
            t["channel"]
        )

        left, right = st.columns(2)

        with left:

            st.markdown(
                "### 📍 Where is the suspicious activity?"
            )

            st.info(
                f"""
                **Current transaction:** {r['loc']}

                **Previous observed locations:**
                {', '.join(r['usual'][:5])}
                """
            )

            st.markdown(
                "### 🚨 Why was it flagged?"
            )

            for x in r["reasons"]:

                st.write(
                    "⚠️",
                    x
                )

        with right:

            st.markdown(
                "### 💡 User Hint / Action"
            )

            if r["score"] >= 70:

                st.warning(
                    """
                    Verify this transaction immediately.
                    If you did not make it, report it as fraud.
                    """
                )

            elif r["score"] >= 40:

                st.warning(
                    """
                    Verify the transaction before
                    treating it as normal.
                    """
                )

            else:

                st.success(
                    """
                    No strong abnormal pattern was detected.
                    Continue normal security checks.
                    """
                )

            x1, x2 = st.columns(2)

            if x1.button(
                "🚨 Report as Fraud",
    
            ):

                con = db()

                con.execute(
                    """
                    UPDATE transactions
                    SET action='Reported as Fraud'
                    WHERE username=?
                    AND id=(
                        SELECT MAX(id)
                        FROM transactions
                        WHERE username=?
                    )
                    """,
                    (
                        st.session_state.username,
                        st.session_state.username
                    )
                )

                con.commit()
                con.close()

                st.success(
                    "Transaction marked as reported fraud."
                )

            if x2.button(
                "✅ Mark as Safe",
    
            ):

                con = db()

                con.execute(
                    """
                    UPDATE transactions
                    SET
                        action='Marked Safe',
                        status='SAFE'
                    WHERE username=?
                    AND id=(
                        SELECT MAX(id)
                        FROM transactions
                        WHERE username=?
                    )
                    """,
                    (
                        st.session_state.username,
                        st.session_state.username
                    )
                )

                con.commit()
                con.close()

                st.success(
                    "Transaction marked as safe."
                )

        # ====================================================
        # ANALYSIS MODULES
        # ====================================================

        st.markdown(
            "### 🧠 Analysis Modules"
        )

        mods = [
            (
                "Machine Learning",
                "Random Forest prediction",
                True
            ),
            (
                "Federated Learning",
                "Architecture-ready demo module",
                False
            ),
            (
                "GNN",
                "Transaction-network module placeholder",
                False
            ),
            (
                "Explainable AI",
                "Rule-based explanation for current demo",
                True
            ),
            (
                "Data Integrity",
                "Transaction/database consistency checks",
                True
            )
        ]

        cols = st.columns(
            len(mods)
        )

        for col, (
            name,
            desc,
            done
        ) in zip(cols, mods):

            col.success(
                "Completed"
                if done
                else "Module"
            )

            col.write(
                f"**{name}**"
            )

            col.caption(
                desc
            )


# ============================================================
# INCOMING MONEY
# ============================================================

elif st.session_state.page == "Incoming Money":

    show_incoming_money()


# ============================================================
# BANK FRAUD COMPLAINT
# ============================================================

elif st.session_state.page == "Bank Fraud Complaint":

    show_bank_complaint()


# ============================================================
# REPORT SUSPICIOUS TRANSACTION
# ============================================================

elif st.session_state.page == "Report Suspicious Transaction":

    show_report_suspicious_transaction()


# ============================================================
# TRACK MY FRAUD CASE
# ============================================================

elif st.session_state.page == "Track My Fraud Case":

    show_track_my_case()


# ============================================================
# MANAGER DASHBOARD
# ============================================================

elif st.session_state.page == "Manager Dashboard":

    show_manager_dashboard()


# ============================================================
# PROFILE
# ============================================================

elif st.session_state.page == "Profile":

    st.markdown(
        """
        <div class="card">
            <h2>👤 Profile</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write(
        "Logged-in demo user:",
        st.session_state.username
    )

    st.markdown(
        f"""
        <div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
            <h3 style="margin: 0; color: white;">💰 Account Balance</h3>
            <p style="margin: 5px 0 0; font-size: 28px; font-weight: bold; color: white;">
                ₹{st.session_state.account_balance:,.2f}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# ============================================================
# GNN ANALYSIS - EXPERIMENTAL MODEL COMPARISON
# ============================================================

elif st.session_state.page == "GNN Analysis":

    st.markdown("## 🧠 Graph Neural Network Analysis")
    st.info(
        "Experimental offline evaluation on synthetic transaction data. "
        "These metrics do not represent live transaction predictions."
    )

    st.markdown("### 📊 Model Performance Comparison")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Random Forest")
        st.metric("Test Precision", "15.22%")
        st.metric("Test Recall", "19.44%")
        st.metric("Average Precision", "0.1001")
        st.metric("Fraud Detected", "7 / 36")

    with col2:
        st.markdown("#### Experimental GNN")
        st.metric("Test Precision", "18.57%")
        st.metric("Test Recall", "36.11%")
        st.metric("Average Precision", "0.1392")
        st.metric("Fraud Detected", "13 / 36")

    st.markdown("### 🔎 Confusion Matrix")
    st.caption(
        "Rows are actual classes; columns are predicted classes. "
        "Class 0 = non-fraud, class 1 = fraud."
    )

    cm_col1, cm_col2 = st.columns(2)

    with cm_col1:
        st.markdown("**Random Forest**")
        st.dataframe(
            pd.DataFrame(
                [[975, 39], [29, 7]],
                index=["Actual non-fraud", "Actual fraud"],
                columns=["Predicted non-fraud", "Predicted fraud"]
            )
        )

    with cm_col2:
        st.markdown("**Experimental GNN**")
        st.dataframe(
            pd.DataFrame(
                [[957, 57], [23, 13]],
                index=["Actual non-fraud", "Actual fraud"],
                columns=["Predicted non-fraud", "Predicted fraud"]
            )
        )

    st.markdown("### 📝 Interpretation")
    st.write(
        "The experimental GNN detected 13 of 36 fraud cases, "
        "while Random Forest detected 7 of 36. The GNN also "
        "generated 57 false alerts, compared with 39 for "
        "Random Forest. Further testing is required."
    )

    st.warning(
        "These are recorded experimental metrics, not live "
        "GNN predictions or production validation."
    )

# TRANSACTION HISTORY
# ============================================================

if (
    st.session_state.logged_in
    and st.session_state.page in [
        "Transactions",
        "Analysis",
        "Profile",
        "Bank Details"
    ]
):

    st.markdown(
        "### 📋 Transaction History (Last 5)"
    )

    h = history(
        st.session_state.username
    )

    if h.empty:

        st.caption(
            "No analyzed transactions yet."
        )

    else:

        h = h.rename(
            columns={
                "created_at": "Date & Time",
                "city": "Location",
                "country": "Country",
                "amount": "Amount",
                "status": "Status",
                "risk": "Risk %",
                "merchant": "Merchant",
                "action": "Action"
            }
        )

        st.dataframe(
            h,
            hide_index=True
        )


# ============================================================
# ============================================================
# FRAUDGUARD AI ASSISTANT PANEL
# ============================================================

if st.session_state.logged_in and st.session_state.page in ["Home", "Bank Details", "Transactions", "Incoming Money", "Analysis", "Profile"]:
    with st.expander("🤖 FraudGuard AI Assistant — Ask a question", expanded=False):
        show_fraudguard_ai()

# FOOTER
# ============================================================

st.caption(
    "College demo environment • Uses synthetic transaction data "
    "• Not connected to any real bank or payment network"
)








