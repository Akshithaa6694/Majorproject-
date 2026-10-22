import streamlit as st
import numpy as np
from datetime import datetime


def show_incoming_money():

    st.markdown(
        """
        <style>
        .main-title {
            background: linear-gradient(120deg, #7a0000, #d71920);
            color: white;
            padding: 22px;
            border-radius: 14px;
            margin-bottom: 20px;
        }

        .fraud-box {
            background-color: #fff0f1;
            border: 3px solid #dc2637;
            border-radius: 14px;
            padding: 25px;
            margin-bottom: 20px;
        }

        .danger-title {
            color: #dc2637;
            font-size: 28px;
            font-weight: 800;
        }

        .do-not-use {
            background-color: #dc2637;
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-size: 22px;
            font-weight: 800;
            margin: 15px 0;
        }

        .sender-card {
            background-color: #f4f8fc;
            border: 1px solid #d7e5f2;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
        }

        .reason-box {
            background-color: #fff0f1;
            border-left: 5px solid #dc2637;
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="main-title">
            <h1>💰 Incoming Money Security Check</h1>
            <p>Automatic checking of received money for suspicious activity</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Display current account balance
    st.markdown(
        f"""
        <div class="sender-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none;">
            <h3 style="margin: 0; color: white;">💰 Current Account Balance</h3>
            <p style="margin: 5px 0 0; font-size: 28px; font-weight: bold; color: white;">
                ₹{st.session_state.get('account_balance', 10000.0):,.2f}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    fraud_transactions = [
        {
            "amount": 200.00,
            "sender_name": "Arjun Reddy",
            "sender_account": "XXXX XXXX 4521",
            "sender_bank": "HDFC Bank",
            "transaction_id": "TXN784512",
            "sender_location": "Hyderabad, India"
        },
        {
            "amount": 350.00,
            "sender_name": "Sneha Sharma",
            "sender_account": "XXXX XXXX 6732",
            "sender_bank": "ICICI Bank",
            "transaction_id": "TXN639821",
            "sender_location": "Bengaluru, India"
        },
        {
            "amount": 500.00,
            "sender_name": "Rahul Verma",
            "sender_account": "XXXX XXXX 2845",
            "sender_bank": "SBI",
            "transaction_id": "TXN521467",
            "sender_location": "Chennai, India"
        },
        {
            "amount": 750.00,
            "sender_name": "Priya Nair",
            "sender_account": "XXXX XXXX 9156",
            "sender_bank": "Axis Bank",
            "transaction_id": "TXN847236",
            "sender_location": "Mumbai, India"
        },
        {
            "amount": 1000.00,
            "sender_name": "Kiran Kumar",
            "sender_account": "XXXX XXXX 3468",
            "sender_bank": "Kotak Bank",
            "transaction_id": "TXN315789",
            "sender_location": "Pune, India"
        }
    ]

    selected_transaction = fraud_transactions[
        np.random.randint(len(fraud_transactions))
    ]

    amount = selected_transaction["amount"]
    sender_name = selected_transaction["sender_name"]
    sender_account = selected_transaction["sender_account"]
    sender_bank = selected_transaction["sender_bank"]
    transaction_id = selected_transaction["transaction_id"]
    sender_location = selected_transaction["sender_location"]

    unknown_sender = True
    unusual_amount = True
    suspicious_pattern = True

    fraud_score = 92

    received_time = datetime.now().strftime("%d-%m-%Y %I:%M %p")

    if unknown_sender and unusual_amount and suspicious_pattern:

        st.markdown(
    f"""
    <div class="fraud-box">
        <div class="danger-title">🔴 FRAUD / SUSPICIOUS MONEY ALERT</div>
        <h1 style="color:#dc2637;">₹{amount:,.2f} RECEIVED</h1>
        <div class="do-not-use">🚫 DO NOT USE THIS MONEY</div>
        <p>This incoming transaction has been identified as <b>highly suspicious</b> by the fraud detection system.</p>
        <p><b>Risk Score:</b> {fraud_score}%</p>
    </div>
    """,
    unsafe_allow_html=True
)

        st.markdown("## 👤 Sender Details")

        c1, c2 = st.columns(2)

        with c1:
            st.markdown(
                f"""
                <div class="sender-card">
                    <b>👤 Sender Name</b><br>
                    {sender_name}
                </div>

                <div class="sender-card">
                    <b>💳 Sender Account</b><br>
                    {sender_account}
                </div>

                <div class="sender-card">
                    <b>🏦 Sender Bank</b><br>
                    {sender_bank}
                </div>
                """,
                unsafe_allow_html=True
            )

        with c2:
            st.markdown(
                f"""
                <div class="sender-card">
                    <b>🆔 Transaction ID</b><br>
                    {transaction_id}
                </div>

                <div class="sender-card">
                    <b>📍 Sender Location</b><br>
                    {sender_location}
                </div>

                <div class="sender-card">
                    <b>🕒 Received Time</b><br>
                    {received_time}
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("## 🚨 Why was this transaction flagged?")

        st.markdown(
            """
            <div class="reason-box">
                🔴 <b>Sender is unknown</b>
            </div>

            <div class="reason-box">
                🔴 <b>Suspicious transaction amount pattern detected</b>
            </div>

            <div class="reason-box">
                🔴 <b>Transaction pattern is suspicious</b>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("## ⚠️ Recommended Action")

        st.warning(
            """
            **DO NOT withdraw, transfer, spend or use this money.**

            Verify the transaction and sender details with your bank
            before taking any action.
            """
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Accept Money (Safe)", type="primary", width='stretch'):
                st.session_state.account_balance = st.session_state.get('account_balance', 500000.0) + amount
                st.success(f"₹{amount:,.2f} has been added to your account!")
                st.rerun()

        with col2:
            if st.button("🚫 Reject Money (Suspicious)", width='stretch'):
                st.warning(f"Transaction {transaction_id} has been rejected. Money was not added to your account.")
                st.rerun()

        st.markdown("## 📋 Transaction Information")

        info = {
            "Amount": f"₹{amount:,.2f}",
            "Sender": sender_name,
            "Sender Account": sender_account,
            "Bank": sender_bank,
            "Transaction ID": transaction_id,
            "Location": sender_location,
            "Received Time": received_time,
            "Risk Score": f"{fraud_score}%",
            "Status": "🔴 SUSPICIOUS"
        }

        for key, value in info.items():
            st.write(f"**{key}:** {value}")

    else:
        st.success("🟢 No suspicious incoming transaction detected.")

