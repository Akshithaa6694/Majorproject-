import streamlit as st
from datetime import datetime
import sqlite3
from pathlib import Path
import random
import string


def get_db_connection():
    """Get database connection."""
    BASE = Path(__file__).resolve().parent
    DB_FILE = BASE / "data" / "fraud_detection.db"
    return sqlite3.connect(DB_FILE)


def create_complaint_table():
    """Create complaints table if it doesn't exist."""
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_ref TEXT UNIQUE,
            username TEXT,
            account_holder_name TEXT,
            account_number TEXT,
            amount_deducted REAL,
            transaction_date TEXT,
            from_location TEXT,
            to_location TEXT,
            transaction_id TEXT,
            bank_manager TEXT,
            complaint_reason TEXT,
            complaint_text TEXT,
            submitted_at TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)
    conn.commit()
    conn.close()


def generate_complaint_ref():
    """Generate unique complaint reference number."""
    return "CMP" + ''.join(random.choices(string.digits, k=8))


def save_complaint(complaint_data):
    """Save complaint to database."""
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO complaints(
                complaint_ref,
                username,
                account_holder_name,
                account_number,
                amount_deducted,
                transaction_date,
                from_location,
                to_location,
                transaction_id,
                bank_manager,
                complaint_reason,
                complaint_text,
                submitted_at,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            complaint_data['complaint_ref'],
            complaint_data['username'],
            complaint_data['account_holder_name'],
            complaint_data['account_number'],
            complaint_data['amount_deducted'],
            complaint_data['transaction_date'],
            complaint_data['from_location'],
            complaint_data['to_location'],
            complaint_data['transaction_id'],
            complaint_data['bank_manager'],
            complaint_data['complaint_reason'],
            complaint_data['complaint_text'],
            complaint_data['submitted_at'],
            'Pending'
        ))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def get_user_complaints(username):
    """Get all complaints for a user."""
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT complaint_ref, account_holder_name, amount_deducted, 
               transaction_date, complaint_reason, submitted_at, status
        FROM complaints
        WHERE username = ?
        ORDER BY submitted_at DESC
    """, conn, params=(username,))
    conn.close()
    return df


def generate_complaint_letter(data):
    """Generate professional complaint letter."""
    letter = f"""To,
The Bank Manager,
{data['bank_manager']}

Subject: Complaint Regarding Suspected Financial Fraud / Unauthorized Transaction

Dear Sir/Madam,

I am writing to formally lodge a complaint regarding a suspicious financial transaction involving my bank account. The details of the fraudulent transaction are as follows:

**Account Holder Name:** {data['account_holder_name']}
**Bank Account Number:** {data['account_number']}
**Amount Deducted:** ₹{data['amount_deducted']:,.2f}
**Date of Transaction:** {data['transaction_date']}
**Transaction ID / Reference:** {data['transaction_id']}
**From Location:** {data['from_location']}
**To Location:** {data['to_location']}
**Complaint Reason:** {data['complaint_reason']}

I noticed this transaction on my account and I did not authorize this deduction. The transaction appears to be fraudulent, and I am concerned about the security of my account.

I request you to investigate this transaction immediately and take appropriate action to:
1. Verify the authenticity of this transaction
2. Reverse the unauthorized deduction if found to be fraudulent
3. Strengthen security measures on my account
4. Provide me with details about how this transaction was processed

I have attached all relevant transaction details for your reference. Please treat this matter with urgency as it involves my hard-earned money.

I trust that you will take prompt action to resolve this issue and protect my account from further unauthorized transactions.

Thank you for your attention to this matter.

Yours faithfully,

{data['account_holder_name']}
"""
    return letter


def show_bank_complaint():
    """Display the Bank Fraud Complaint page."""
    
    # Ensure complaint table exists
    create_complaint_table()
    
    st.markdown("""
    <style>
    .complaint-title {
        background: linear-gradient(120deg, #dc2637, #ef4444);
        color: white;
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 20px;
    }
    .complaint-title h2 {
        margin: 0;
        color: white;
    }
    .complaint-preview {
        background: #fef2f2;
        border: 2px solid #fecaca;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        white-space: pre-wrap;
        font-family: 'Times New Roman', serif;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="complaint-title">
        <h2>📋 Bank Fraud Complaint</h2>
        <p>Report suspicious transactions or unauthorized deductions</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("ℹ️ **Demo Mode:** This is a demo complaint system. Complaints are recorded locally in this application and are not actually sent to any bank.")
    
    # Form inputs
    col1, col2 = st.columns(2)
    
    with col1:
        account_holder = st.text_input("Account Holder Name *", 
                                        value=st.session_state.username.split("@")[0].title() if st.session_state.username else "")
        account_number = st.text_input("Bank Account Number *", 
                                        placeholder="Enter your account number")
        amount = st.number_input("Amount Deducted (₹) *", 
                                  min_value=0.0, 
                                  value=0.0, 
                                  step=100.0)
        transaction_date = st.date_input("Date of Fraudulent Transaction *",
                                        value=datetime.now().date())
    
    with col2:
        from_location = st.text_input("From Location *", 
                                      placeholder="Where transaction originated")
        to_location = st.text_input("To Location *", 
                                    placeholder="Where money was sent/received")
        transaction_id = st.text_input("Transaction ID / Reference Number *",
                                       placeholder="Enter transaction reference")
        bank_manager = st.text_input("Bank Manager / Branch Name *",
                                      placeholder="Enter bank manager or branch name")
    
    complaint_reason = st.selectbox(
        "Complaint Reason *",
        [
            "Unauthorized Money Deduction",
            "Unknown Sender",
            "Suspicious Transaction",
            "Online Payment Fraud",
            "ATM Fraud",
            "UPI Transaction Fraud",
            "Other"
        ]
    )
    
    # Generate complaint preview
    st.markdown("---")
    st.markdown("### 📝 Complaint Preview")
    
    complaint_data = {
        'account_holder_name': account_holder,
        'account_number': account_number,
        'amount_deducted': amount,
        'transaction_date': transaction_date.strftime("%d-%m-%Y"),
        'from_location': from_location,
        'to_location': to_location,
        'transaction_id': transaction_id,
        'bank_manager': bank_manager,
        'complaint_reason': complaint_reason
    }
    
    if all([account_holder, account_number, amount > 0, from_location, to_location, transaction_id, bank_manager]):
        complaint_letter = generate_complaint_letter(complaint_data)
        st.markdown(f"""
        <div class="complaint-preview">
{complaint_letter}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Please fill in all required fields to see the complaint preview.")
    
    # Submit button
    st.markdown("---")
    
    if st.button("📨 Submit Complaint to Bank Manager", type="primary", width='stretch'):
        # Validation
        if not all([account_holder, account_number, amount > 0, from_location, to_location, transaction_id, bank_manager]):
            st.error("❌ Please fill in all required fields marked with *")
            return
        
        # Generate complaint reference
        complaint_ref = generate_complaint_ref()
        
        # Prepare data for saving
        complaint_data['complaint_ref'] = complaint_ref
        complaint_data['username'] = st.session_state.username
        complaint_data['complaint_text'] = complaint_letter
        complaint_data['submitted_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save to database
        if save_complaint(complaint_data):
            st.success(f"""
            ✅ **Complaint Submitted Successfully!**
            
            **Complaint Reference Number:** {complaint_ref}
            
            Your complaint has been recorded in the demo system.
            Please note: This is a demo complaint and has not been sent to any real bank.
            Reference this number for any future inquiries.
            """)
            
            # Display confirmation details
            st.markdown("---")
            st.markdown("### 📋 Submitted Complaint Details")
            col1, col2, col3 = st.columns(3)
            col1.metric("Reference", complaint_ref)
            col2.metric("Amount", f"₹{amount:,.2f}")
            col3.metric("Status", "Pending")
        else:
            st.error("❌ Failed to submit complaint. Please try again.")
    
    # View previous complaints
    st.markdown("---")
    st.markdown("### 📁 Your Previous Complaints")
    
    try:
        import pandas as pd
        complaints_df = get_user_complaints(st.session_state.username)
        
        if complaints_df.empty:
            st.info("No complaints submitted yet.")
        else:
            # Mask account number for display
            if 'account_number' in complaints_df.columns:
                complaints_df['account_number'] = complaints_df['account_number'].apply(
                    lambda x: x[:4] + "XXXX" + x[-4:] if len(x) > 8 else "XXXX"
                )
            
            st.dataframe(complaints_df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.warning("Unable to load complaint history.")


# Import pandas at the module level
import pandas as pd
