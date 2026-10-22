import streamlit as st
import sqlite3
from datetime import datetime
from pathlib import Path
import random
import string

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def get_db_connection():
    """Get database connection."""
    BASE = Path(__file__).resolve().parent
    DB_FILE = BASE / "data" / "fraud_detection.db"
    return sqlite3.connect(DB_FILE)


def create_investigation_tables():
    """Create investigation-related tables if they don't exist."""
    conn = get_db_connection()
    
    # Cases table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS investigation_cases(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT UNIQUE,
            reporter_username TEXT,
            reporter_account_number TEXT,
            suspicious_account_number TEXT,
            transaction_id TEXT,
            transaction_amount REAL,
            transaction_date TEXT,
            sender_location TEXT,
            receiver_location TEXT,
            reason TEXT,
            complaint_ref TEXT,
            status TEXT DEFAULT 'Flagged for Review',
            account_status TEXT DEFAULT 'Active',
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    # Audit log table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS investigation_audit(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT,
            action TEXT,
            previous_status TEXT,
            new_status TEXT,
            decision_reason TEXT,
            reviewer TEXT,
            reviewed_at TEXT
        )
    """)
    
    # Manager accounts table (for demo purposes)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS manager_accounts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # Insert default manager if not exists
    cursor = conn.execute("SELECT * FROM manager_accounts WHERE username = ?", ("manager",))
    if cursor.fetchone() is None:
        conn.execute("INSERT INTO manager_accounts (username, password, is_active) VALUES (?, ?, ?)",
                    ("manager", "manager123", 1))
        conn.commit()
        print("Manager account created: manager / manager123")
    else:
        print("Manager account already exists")
    
    conn.close()


def generate_case_id():
    """Generate unique case ID."""
    return "CASE" + ''.join(random.choices(string.digits, k=8))


def save_investigation_case(case_data):
    """Save investigation case to database."""
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO investigation_cases(
                case_id,
                reporter_username,
                reporter_account_number,
                suspicious_account_number,
                transaction_id,
                transaction_amount,
                transaction_date,
                sender_location,
                receiver_location,
                reason,
                complaint_ref,
                status,
                account_status,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case_data['case_id'],
            case_data['reporter_username'],
            case_data['reporter_account_number'],
            case_data['suspicious_account_number'],
            case_data['transaction_id'],
            case_data['transaction_amount'],
            case_data['transaction_date'],
            case_data['sender_location'],
            case_data['receiver_location'],
            case_data['reason'],
            case_data['complaint_ref'],
            case_data['status'],
            case_data['account_status'],
            case_data['created_at'],
            case_data['updated_at']
        ))
        
        # Add to audit log
        conn.execute("""
            INSERT INTO investigation_audit(
                case_id, action, previous_status, new_status, 
                decision_reason, reviewer, reviewed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            case_data['case_id'],
            'Case Created',
            None,
            case_data['status'],
            'Initial report submitted',
            case_data['reporter_username'],
            case_data['created_at']
        ))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def get_user_cases(username):
    """Get all cases for a user."""
    if not PANDAS_AVAILABLE:
        return None
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT case_id, transaction_id, transaction_amount, transaction_date,
               reason, status, account_status, created_at, updated_at
        FROM investigation_cases
        WHERE reporter_username = ?
        ORDER BY created_at DESC
    """, conn, params=(username,))
    conn.close()
    return df


def get_all_cases():
    """Get all cases for manager view."""
    if not PANDAS_AVAILABLE:
        return None
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT case_id, reporter_username, reporter_account_number,
               suspicious_account_number, transaction_id, transaction_amount,
               transaction_date, reason, status, account_status, created_at
        FROM investigation_cases
        ORDER BY created_at DESC
    """, conn)
    conn.close()
    return df


def get_all_complaints():
    """Get all complaints for manager view."""
    if not PANDAS_AVAILABLE:
        return None
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("""
            SELECT complaint_ref, username, account_holder_name, account_number,
                   amount_deducted, transaction_date, from_location, to_location,
                   transaction_id, bank_manager, complaint_reason, complaint_text,
                   submitted_at, status
            FROM complaints
            ORDER BY submitted_at DESC
        """, conn)
        conn.close()
        return df
    except Exception as e:
        conn.close()
        print(f"Error getting complaints: {e}")
        return None


def get_all_transactions():
    """Get all transactions for manager view."""
    if not PANDAS_AVAILABLE:
        return None
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("""
            SELECT id, username, created_at, amount, city, country, merchant,
                   payment_method, device, channel, hour, risk, status, action
            FROM transactions
            ORDER BY id DESC
        """, conn)
        conn.close()
        return df
    except Exception as e:
        conn.close()
        print(f"Error getting transactions: {e}")
        return None


def update_complaint_status(complaint_ref, new_status, decision_reason, reviewer):
    """Update complaint status and add to audit log."""
    conn = get_db_connection()
    try:
        # Get current status
        cursor = conn.execute("SELECT status FROM complaints WHERE complaint_ref = ?", (complaint_ref,))
        result = cursor.fetchone()
        if not result:
            return False
        
        old_status = result[0]
        
        # Update complaint
        conn.execute("""
            UPDATE complaints
            SET status = ?
            WHERE complaint_ref = ?
        """, (new_status, complaint_ref))
        
        # Add to audit log (using investigation_audit table)
        conn.execute("""
            INSERT INTO investigation_audit(
                case_id, action, previous_status, new_status,
                decision_reason, reviewer, reviewed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            complaint_ref,
            'Complaint Status Update',
            old_status,
            new_status,
            decision_reason,
            reviewer,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error updating complaint status: {e}")
        return False
    finally:
        conn.close()


def get_complaint_by_ref(complaint_ref):
    """Get complaint details by reference number."""
    if not PANDAS_AVAILABLE:
        return None
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("""
            SELECT * FROM complaints WHERE complaint_ref = ?
        """, conn, params=(complaint_ref,))
        conn.close()
        return df.iloc[0] if not df.empty else None
    except Exception as e:
        conn.close()
        print(f"Error getting complaint: {e}")
        return None


def get_case_by_id(case_id):
    """Get case details by case ID."""
    if not PANDAS_AVAILABLE:
        return None
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT * FROM investigation_cases WHERE case_id = ?
    """, conn, params=(case_id,))
    conn.close()
    return df.iloc[0] if not df.empty else None


def get_case_audit_log(case_id):
    """Get audit log for a case."""
    if not PANDAS_AVAILABLE:
        return None
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT action, previous_status, new_status, decision_reason,
               reviewer, reviewed_at
        FROM investigation_audit
        WHERE case_id = ?
        ORDER BY reviewed_at DESC
    """, conn, params=(case_id,))
    conn.close()
    return df


def update_case_status(case_id, new_status, new_account_status, decision_reason, reviewer):
    """Update case status and add to audit log."""
    conn = get_db_connection()
    try:
        # Get current status
        cursor = conn.execute("SELECT status, account_status FROM investigation_cases WHERE case_id = ?", (case_id,))
        result = cursor.fetchone()
        if not result:
            return False
        
        old_status, old_account_status = result
        
        # Update case
        conn.execute("""
            UPDATE investigation_cases
            SET status = ?, account_status = ?, updated_at = ?
            WHERE case_id = ?
        """, (new_status, new_account_status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), case_id))
        
        # Add to audit log
        conn.execute("""
            INSERT INTO investigation_audit(
                case_id, action, previous_status, new_status,
                decision_reason, reviewer, reviewed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            case_id,
            'Status Update',
            f"{old_status} / {old_account_status}",
            f"{new_status} / {new_account_status}",
            decision_reason,
            reviewer,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def verify_manager(username, password):
    """Verify manager credentials - accepts any non-empty username and password for demo."""
    # For demo purposes, accept any non-empty username and password
    username = username.strip() if username else ""
    password = password.strip() if password else ""
    
    # Allow any credentials for demo purposes
    if username and password:
        return True
    return False


def check_account_restriction(username):
    """Check if user's account has any active restrictions."""
    conn = get_db_connection()
    cursor = conn.execute("""
        SELECT case_id, status, account_status, reason
        FROM investigation_cases
        WHERE reporter_username = ?
        AND account_status IN ('Temporarily Restricted', 'Under Investigation')
        ORDER BY created_at DESC
        LIMIT 1
    """, (username,))
    result = cursor.fetchone()
    conn.close()
    return result


# ============================================================
# UI FUNCTIONS
# ============================================================

def show_report_suspicious_transaction():
    """Show page for reporting suspicious transactions."""
    create_investigation_tables()
    
    st.markdown("""
    <style>
    .report-title {
        background: linear-gradient(120deg, #dc2637, #ef4444);
        color: white;
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 20px;
    }
    .restriction-warning {
        background: #fee2e2;
        border: 2px solid #fca5a5;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check for existing restrictions
    restriction = check_account_restriction(st.session_state.username)
    if restriction:
        case_id, status, account_status, reason = restriction
        st.markdown(f"""
        <div class="restriction-warning">
            <h3 style="color: #dc2637; margin: 0;">⚠️ Account Restriction Active</h3>
            <p><strong>Case ID:</strong> {case_id}</p>
            <p><strong>Status:</strong> {account_status}</p>
            <p><strong>Reason:</strong> {reason}</p>
            <p>Your account is currently under review. Please visit the "Track My Fraud Case" page for updates.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="report-title">
        <h2>🚨 Report Suspicious Transaction</h2>
        <p>Report unauthorized transactions and request account protection</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("ℹ️ **Demo Mode:** This is a simulated investigation system. Reports are recorded locally and do not contact real banks or authorities.")
    
    # Form
    col1, col2 = st.columns(2)
    
    with col1:
        reporter_account = st.text_input("Your Account Number *",
                                         placeholder="Enter your account number")
        suspicious_account = st.text_input("Suspicious Account Number (if known)",
                                          placeholder="Enter the other account number")
        transaction_id = st.text_input("Transaction ID *",
                                       placeholder="Enter transaction reference")
        transaction_amount = st.number_input("Transaction Amount (₹) *",
                                           min_value=0.0,
                                           value=0.0,
                                           step=100.0)
    
    with col2:
        transaction_date = st.date_input("Transaction Date *",
                                        value=datetime.now().date())
        sender_location = st.text_input("Sender Location *",
                                        placeholder="Where transaction originated")
        receiver_location = st.text_input("Receiver Location *",
                                          placeholder="Where money was sent")
    
    reason = st.selectbox(
        "Reason for Reporting *",
        [
            "Unauthorized Money Deduction",
            "Unknown Sender",
            "Suspicious Transaction",
            "Online Payment Fraud",
            "ATM Fraud",
            "UPI Transaction Fraud",
            "Phishing Attempt",
            "Other"
        ]
    )
    
    complaint_ref = st.text_input("Complaint Reference Number (if applicable)",
                                    placeholder="Enter complaint reference from Bank Fraud Complaint page")
    
    st.markdown("---")
    
    if st.button("📨 Submit Report & Request Account Restriction", type="primary"):
        # Validation
        if not all([reporter_account, transaction_id, transaction_amount > 0, 
                   sender_location, receiver_location]):
            st.error("❌ Please fill in all required fields marked with *")
            return
        
        # Generate case ID
        case_id = generate_case_id()
        
        # Determine initial status based on risk
        # High amount or suspicious reason triggers immediate review
        is_high_risk = transaction_amount > 1000 or reason in ["Phishing Attempt", "ATM Fraud"]
        initial_status = "Temporarily Restricted" if is_high_risk else "Flagged for Review"
        account_status = "Temporarily Restricted" if is_high_risk else "Active"
        
        # Prepare data
        case_data = {
            'case_id': case_id,
            'reporter_username': st.session_state.username,
            'reporter_account_number': reporter_account,
            'suspicious_account_number': suspicious_account or "Unknown",
            'transaction_id': transaction_id,
            'transaction_amount': transaction_amount,
            'transaction_date': transaction_date.strftime("%Y-%m-%d"),
            'sender_location': sender_location,
            'receiver_location': receiver_location,
            'reason': reason,
            'complaint_ref': complaint_ref or None,
            'status': initial_status,
            'account_status': account_status,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save to database
        if save_investigation_case(case_data):
            st.success(f"""
            ✅ **Report Submitted Successfully!**
            
            **Case ID:** {case_id}
            **Status:** {initial_status}
            **Account Status:** {account_status}
            
            {"Your account has been temporarily restricted for your protection while the case is under review." if is_high_risk else "Your report has been flagged for review. A bank manager will investigate the case."}
            
            Please note: This is a demo investigation system.
            """)
            
            if is_high_risk:
                st.warning("⚠️ **Account Restriction Applied:** Due to the high-risk nature of this report, your account has been temporarily restricted pending investigation. This is a demo restriction for demonstration purposes.")
        else:
            st.error("❌ Failed to submit report. Please try again.")


def show_track_my_case():
    """Show page for tracking fraud cases."""
    create_investigation_tables()
    
    st.markdown("""
    <style>
    .track-title {
        background: linear-gradient(120deg, #0891b2, #06b6d4);
        color: white;
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="track-title">
        <h2>📋 Track My Fraud Case</h2>
        <p>View the status of your reported cases</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get user's cases
    cases_df = get_user_cases(st.session_state.username)
    
    if cases_df is None:
        st.error("Database error. Please try again.")
        return
    
    if cases_df.empty:
        st.info("No cases reported yet. Go to 'Report Suspicious Transaction' to report a case.")
    else:
        # Mask sensitive info
        if 'reporter_account_number' in cases_df.columns:
            cases_df['reporter_account_number'] = cases_df['reporter_account_number'].apply(
                lambda x: x[:4] + "XXXX" + x[-4:] if len(x) > 8 else "XXXX"
            )
        
        st.dataframe(cases_df, use_container_width=True, hide_index=True)
        
        # Detailed view for selected case
        st.markdown("---")
        st.markdown("### 📝 Case Details")
        
        case_id = st.selectbox("Select Case to View Details", cases_df['case_id'].tolist())
        
        if case_id:
            case = get_case_by_id(case_id)
            audit_log = get_case_audit_log(case_id)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Case ID", case['case_id'])
                st.metric("Status", case['status'])
                st.metric("Account Status", case['account_status'])
            
            with col2:
                st.metric("Transaction Amount", f"₹{case['transaction_amount']:,.2f}")
                st.metric("Reported On", case['created_at'])
                st.metric("Last Updated", case['updated_at'])
            
            st.markdown("---")
            st.markdown("### 📜 Investigation Timeline")
            
            if audit_log.empty:
                st.info("No investigation updates yet.")
            else:
                for _, row in audit_log.iterrows():
                    st.markdown(f"""
                    <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin: 10px 0;">
                        <strong>Action:</strong> {row['action']}<br>
                        <strong>Status Change:</strong> {row['previous_status']} → {row['new_status']}<br>
                        <strong>Reason:</strong> {row['decision_reason']}<br>
                        <strong>Reviewer:</strong> {row['reviewer']}<br>
                        <strong>Time:</strong> {row['reviewed_at']}
                    </div>
                    """, unsafe_allow_html=True)


def show_manager_dashboard():
    """Show bank manager investigation dashboard."""
    create_investigation_tables()
    
    # Manager authentication
    if "manager_logged_in" not in st.session_state:
        st.session_state.manager_logged_in = False
    
    if not st.session_state.manager_logged_in:
        st.markdown("""
        <style>
        .manager-login {
            background: linear-gradient(120deg, #1e3a8a, #1e40af);
            color: white;
            padding: 30px;
            border-radius: 14px;
            margin: 30px auto;
            max-width: 400px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="manager-login">
            <h2>🔐 Manager Login</h2>
            <p>Access restricted to authorized personnel</p>
        </div>
        """, unsafe_allow_html=True)
        
        username = st.text_input("Manager Username", placeholder="Enter any username")
        password = st.text_input("Password", type="password", placeholder="Enter any password")
        
        if st.button("Login", type="primary"):
            if verify_manager(username, password):
                st.session_state.manager_logged_in = True
                st.session_state.manager_username = username
                st.success("✅ Manager login successful")
                st.rerun()
            else:
                st.error("❌ Please enter both username and password")
        
        st.info("🔑 **Demo Mode:** For this demo, you can use any non-empty username and password to login as manager.")
        return
    
    st.markdown("""
    <style>
    .manager-header {
        background: linear-gradient(120deg, #1e3a8a, #3b82f6);
        color: white;
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="manager-header">
        <h2>👨‍💼 Bank Manager Investigation Dashboard</h2>
        <p>Review and manage fraud investigation cases</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Logout button
    if st.button("Logout", key="manager_logout"):
        st.session_state.manager_logged_in = False
        st.session_state.manager_username = ""
        st.rerun()
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Investigation Cases", "📨 Complaints", "💳 Transactions", "📊 Dashboard Overview"])
    
    # Tab 1: Investigation Cases
    with tab1:
        st.markdown("### 🔍 Investigation Cases")
        
        # Get all cases
        cases_df = get_all_cases()
        
        if cases_df is None:
            st.error("Database error. Please try again.")
            return
        
        if cases_df.empty:
            st.info("No investigation cases reported yet.")
        else:
            # Search filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                search_case_id = st.text_input("Search by Case ID")
            with col2:
                search_tx_id = st.text_input("Search by Transaction ID")
            with col3:
                search_account = st.text_input("Search by Account Number")
            
            # Apply filters
            if search_case_id:
                cases_df = cases_df[cases_df['case_id'].str.contains(search_case_id, case=False, na=False)]
            if search_tx_id:
                cases_df = cases_df[cases_df['transaction_id'].str.contains(search_tx_id, case=False, na=False)]
            if search_account:
                cases_df = cases_df[cases_df['reporter_account_number'].str.contains(search_account, case=False, na=False)]
            
            st.markdown("---")
            st.markdown("### 📋 All Investigation Cases")
            
            # Display cases
            st.dataframe(cases_df, use_container_width=True, hide_index=True)
            
            # Case review section
            st.markdown("---")
            st.markdown("### 🔍 Review Case")
            
            if not cases_df.empty:
                selected_case_id = st.selectbox("Select Case to Review", cases_df['case_id'].tolist())
            
            if selected_case_id:
                case = get_case_by_id(selected_case_id)
                audit_log = get_case_audit_log(selected_case_id)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📄 Case Details")
                    st.write(f"**Case ID:** {case['case_id']}")
                    st.write(f"**Reporter:** {case['reporter_username']}")
                    st.write(f"**Reporter Account:** {case['reporter_account_number']}")
                    st.write(f"**Suspicious Account:** {case['suspicious_account_number']}")
                    st.write(f"**Transaction ID:** {case['transaction_id']}")
                    st.write(f"**Amount:** ₹{case['transaction_amount']:,.2f}")
                    st.write(f"**Date:** {case['transaction_date']}")
                    st.write(f"**Sender Location:** {case['sender_location']}")
                    st.write(f"**Receiver Location:** {case['receiver_location']}")
                    st.write(f"**Reason:** {case['reason']}")
                    st.write(f"**Complaint Ref:** {case['complaint_ref'] or 'N/A'}")
                
                with col2:
                    st.markdown("### 📊 Current Status")
                    st.metric("Status", case['status'])
                    st.metric("Account Status", case['account_status'])
                    st.metric("Created", case['created_at'])
                    st.metric("Updated", case['updated_at'])
                
                st.markdown("---")
                st.markdown("### 📜 Investigation Timeline")
                
                if audit_log.empty:
                    st.info("No investigation updates yet.")
                else:
                    for _, row in audit_log.iterrows():
                        st.markdown(f"""
                        <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin: 10px 0;">
                            <strong>Action:</strong> {row['action']}<br>
                            <strong>Status Change:</strong> {row['previous_status']} → {row['new_status']}<br>
                            <strong>Reason:</strong> {row['decision_reason']}<br>
                            <strong>Reviewer:</strong> {row['reviewer']}<br>
                            <strong>Time:</strong> {row['reviewed_at']}
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("### ⚖️ Take Action")
                
                action = st.selectbox(
                    "Select Action",
                    [
                        "Keep Restricted",
                        "Release Restriction",
                        "Escalate Case",
                        "Request More Evidence"
                    ]
                )
                
                decision_reason = st.text_area("Decision Reason (Required)", placeholder="Explain your decision...")
                
                if st.button("Submit Decision", type="primary", ):
                    if not decision_reason:
                        st.error("❌ Please provide a reason for your decision.")
                        return
                    
                    # Determine new statuses based on action
                    if action == "Keep Restricted":
                        new_status = "Under Investigation"
                        new_account_status = "Temporarily Restricted"
                    elif action == "Release Restriction":
                        new_status = "Restriction Released"
                        new_account_status = "Active"
                    elif action == "Escalate Case":
                        new_status = "Escalated"
                        new_account_status = "Temporarily Restricted"
                    else:  # Request More Evidence
                        new_status = "Flagged for Review"
                        new_account_status = "Active"
                    
                    if update_case_status(selected_case_id, new_status, new_account_status, 
                                       decision_reason, st.session_state.manager_username):
                        st.success(f"✅ Decision recorded successfully. Case status updated to: {new_status}")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update case. Please try again.")
    
    # Tab 2: Complaints
    with tab2:
        st.markdown("### 📨 Bank Fraud Complaints")
        
        complaints_df = get_all_complaints()
        
        if complaints_df is None:
            st.error("Database error. Please try again.")
            return
        
        if complaints_df.empty:
            st.info("No complaints submitted yet.")
            st.markdown("---")
            st.markdown("### 📊 How to Submit Complaints")
            st.write("Users can submit complaints through the 'Bank Fraud Complaint' page in the main application.")
            st.write("Once submitted, complaints will appear here for manager review.")
        else:
            # Complaint count and status summary
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Total", len(complaints_df))
            col2.metric("Pending", len(complaints_df[complaints_df['status'] == 'Pending']))
            col3.metric("Under Review", len(complaints_df[complaints_df['status'] == 'Under Review']))
            col4.metric("Resolved", len(complaints_df[complaints_df['status'] == 'Resolved']))
            col5.metric("Escalated", len(complaints_df[complaints_df['status'] == 'Escalated']))
            
            st.markdown("---")
            st.markdown("### 👥 Complaints by User")
            
            # Show unique users who raised complaints
            if 'username' in complaints_df.columns:
                unique_users = complaints_df['username'].unique()
                st.write(f"**Total Users Who Raised Complaints:** {len(unique_users)}")
                st.write(f"**Usernames:** {', '.join(unique_users)}")
            
            if 'account_holder_name' in complaints_df.columns:
                unique_customers = complaints_df['account_holder_name'].unique()
                st.write(f"**Customer Names:** {', '.join(unique_customers)}")
            
            st.markdown("---")
            
            # Search and filters
            st.markdown("### 🔍 Search & Filter")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                search_complaint_id = st.text_input("Search by Complaint ID")
            with col2:
                search_tx_id = st.text_input("Search by Transaction ID")
            with col3:
                filter_status = st.selectbox("Filter by Status", ["All", "Pending", "Under Review", "Resolved", "Escalated"])
            
            # Apply filters
            if search_complaint_id:
                complaints_df = complaints_df[complaints_df['complaint_ref'].str.contains(search_complaint_id, case=False, na=False)]
            if search_tx_id:
                complaints_df = complaints_df[complaints_df['transaction_id'].str.contains(search_tx_id, case=False, na=False)]
            if filter_status != "All":
                complaints_df = complaints_df[complaints_df['status'] == filter_status]
            
            st.markdown("---")
            st.markdown("### 📋 All Complaints")
            
            # Mask account numbers
            if 'account_number' in complaints_df.columns:
                complaints_df['account_number'] = complaints_df['account_number'].apply(
                    lambda x: x[:4] + "XXXX" + x[-4:] if len(x) > 8 else "XXXX"
                )
            
            st.dataframe(complaints_df, use_container_width=True, hide_index=True)
            
            # Complaint details and actions
            st.markdown("---")
            st.markdown("### 📝 Complaint Details & Actions")
            
            if not complaints_df.empty:
                selected_complaint = st.selectbox("Select Complaint to View & Manage", complaints_df['complaint_ref'].tolist())
            
            if selected_complaint:
                complaint = get_complaint_by_ref(selected_complaint)
                
                if complaint is not None:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 📄 Complaint Information")
                        st.write(f"**Complaint Reference:** {complaint['complaint_ref']}")
                        st.write(f"**Submitted:** {complaint['submitted_at']}")
                        st.write(f"**Status:** {complaint['status']}")
                        st.write(f"**Reason:** {complaint['complaint_reason']}")
                        st.write(f"**Bank Manager/Branch:** {complaint['bank_manager']}")
                    
                    with col2:
                        st.markdown("### 👤 Reporter Information")
                        st.write(f"**Customer Name:** {complaint['account_holder_name']}")
                        st.write(f"**Username:** {complaint['username']}")
                        masked_account = complaint['account_number'][:4] + 'XXXX' + complaint['account_number'][-4:] if len(complaint['account_number']) > 8 else 'XXXX'
                        st.write(f"**Account Number:** {masked_account}")
                        st.write(f"**Complaint Raised By:** {complaint['username']} ({complaint['account_holder_name']})")
                    
                    st.markdown("---")
                    st.markdown("### 💳 Transaction Information")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Transaction ID:** {complaint['transaction_id']}")
                        st.write(f"**Amount:** ₹{complaint['amount_deducted']:,.2f}")
                        st.write(f"**Transaction Date:** {complaint['transaction_date']}")
                    
                    with col2:
                        st.write(f"**From Location:** {complaint['from_location']}")
                        st.write(f"**To Location:** {complaint['to_location']}")
                    
                    st.markdown("---")
                    st.markdown("### 📜 Full Complaint Letter")
                    
                    st.markdown(f"""
                    <div style="background: #fef2f2; border: 2px solid #fecaca; border-radius: 12px; padding: 20px; white-space: pre-wrap; font-family: 'Times New Roman', serif; line-height: 1.6;">
{complaint['complaint_text']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    st.markdown("### ⚖️ Manager Actions")
                    
                    action = st.selectbox(
                        "Select Action",
                        [
                            "Mark Under Review",
                            "Request More Information",
                            "Resolve Complaint",
                            "Escalate Complaint"
                        ]
                    )
                    
                    decision_reason = st.text_area("Decision Reason (Required)", placeholder="Explain your decision...")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Submit Action", type="primary", ):
                            if not decision_reason:
                                st.error("❌ Please provide a reason for your decision.")
                                return
                            
                            # Determine new status based on action
                            if action == "Mark Under Review":
                                new_status = "Under Review"
                            elif action == "Request More Information":
                                new_status = "Pending"
                            elif action == "Resolve Complaint":
                                new_status = "Resolved"
                            else:  # Escalate Complaint
                                new_status = "Escalated"
                            
                            if update_complaint_status(selected_complaint, new_status, decision_reason, st.session_state.manager_username):
                                st.success(f"✅ Complaint status updated to: {new_status}")
                                st.rerun()
                            else:
                                st.error("❌ Failed to update complaint. Please try again.")
                    
                    with col2:
                        if st.button("View Complaint Audit Log", type="secondary", ):
                            audit_log = get_case_audit_log(selected_complaint)
                            
                            if audit_log is None or audit_log.empty:
                                st.info("No audit log available for this complaint.")
                            else:
                                st.markdown("### 📜 Complaint Audit Log")
                                for _, row in audit_log.iterrows():
                                    st.markdown(f"""
                                    <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin: 10px 0;">
                                        <strong>Action:</strong> {row['action']}<br>
                                        <strong>Status Change:</strong> {row['previous_status']} → {row['new_status']}<br>
                                        <strong>Reason:</strong> {row['decision_reason']}<br>
                                        <strong>Reviewer:</strong> {row['reviewer']}<br>
                                        <strong>Time:</strong> {row['reviewed_at']}
                                    </div>
                                    """, unsafe_allow_html=True)
    
    # Tab 3: Transactions
    with tab3:
        st.markdown("### 💳 All Transactions")
        
        transactions_df = get_all_transactions()
        
        if transactions_df is None:
            st.error("Database error. Please try again.")
            return
        
        if transactions_df.empty:
            st.info("No transactions recorded yet.")
        else:
            st.dataframe(transactions_df, use_container_width=True, hide_index=True)
            
            # Transaction statistics
            st.markdown("---")
            st.markdown("### 📊 Transaction Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Total Transactions", len(transactions_df))
            col2.metric("High Risk (>70%)", len(transactions_df[transactions_df['risk'] >= 70]))
            col3.metric("Review Needed (40-69%)", len(transactions_df[(transactions_df['risk'] >= 40) & (transactions_df['risk'] < 70)]))
            col4.metric("Low Risk (<40%)", len(transactions_df[transactions_df['risk'] < 40]))
    
    # Tab 4: Dashboard Overview
    with tab4:
        st.markdown("### 📊 Dashboard Overview")
        
        # Get all data
        cases_df = get_all_cases()
        complaints_df = get_all_complaints()
        transactions_df = get_all_transactions()
        
        # Handle None cases
        cases_count = len(cases_df) if cases_df is not None else 0
        complaints_count = len(complaints_df) if complaints_df is not None else 0
        transactions_count = len(transactions_df) if transactions_df is not None else 0
        restrictions_count = len(cases_df[cases_df['account_status'] == 'Temporarily Restricted']) if cases_df is not None and not cases_df.empty else 0
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("Total Cases", cases_count)
        col2.metric("Total Complaints", complaints_count)
        col3.metric("Total Transactions", transactions_count)
        col4.metric("Active Restrictions", restrictions_count)
        
        st.markdown("---")
        
        # Status breakdown for cases
        if cases_df is not None and not cases_df.empty:
            st.markdown("### 📋 Case Status Breakdown")
            status_counts = cases_df['status'].value_counts()
            st.bar_chart(status_counts)
        
        st.markdown("---")
        
        # Status breakdown for complaints
        if complaints_df is not None and not complaints_df.empty:
            st.markdown("### 📨 Complaint Status Breakdown")
            complaint_status = complaints_df['status'].value_counts()
            st.bar_chart(complaint_status)
        
        st.markdown("---")
        
        # Risk distribution for transactions
        if transactions_df is not None and not transactions_df.empty:
            st.markdown("### 💳 Transaction Risk Distribution")
            risk_categories = pd.cut(
                transactions_df['risk'],
                bins=[0, 40, 70, 100],
                labels=['Low Risk', 'Review Required', 'High Risk']
            )
            risk_counts = risk_categories.value_counts()
            st.bar_chart(risk_counts)
    
    # Case review section
    st.markdown("---")
    st.markdown("### 🔍 Review Case")
    
    selected_case_id = st.selectbox("Select Case to Review", cases_df['case_id'].tolist())
    
    if selected_case_id:
        case = get_case_by_id(selected_case_id)
        audit_log = get_case_audit_log(selected_case_id)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📄 Case Details")
            st.write(f"**Case ID:** {case['case_id']}")
            st.write(f"**Reporter:** {case['reporter_username']}")
            st.write(f"**Reporter Account:** {case['reporter_account_number']}")
            st.write(f"**Suspicious Account:** {case['suspicious_account_number']}")
            st.write(f"**Transaction ID:** {case['transaction_id']}")
            st.write(f"**Amount:** ₹{case['transaction_amount']:,.2f}")
            st.write(f"**Date:** {case['transaction_date']}")
            st.write(f"**Sender Location:** {case['sender_location']}")
            st.write(f"**Receiver Location:** {case['receiver_location']}")
            st.write(f"**Reason:** {case['reason']}")
            st.write(f"**Complaint Ref:** {case['complaint_ref'] or 'N/A'}")
        
        with col2:
            st.markdown("### 📊 Current Status")
            st.metric("Status", case['status'])
            st.metric("Account Status", case['account_status'])
            st.metric("Created", case['created_at'])
            st.metric("Updated", case['updated_at'])
        
        st.markdown("---")
        st.markdown("### 📜 Investigation Timeline")
        
        if audit_log.empty:
            st.info("No investigation updates yet.")
        else:
            for _, row in audit_log.iterrows():
                st.markdown(f"""
                <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin: 10px 0;">
                    <strong>Action:</strong> {row['action']}<br>
                    <strong>Status Change:</strong> {row['previous_status']} → {row['new_status']}<br>
                    <strong>Reason:</strong> {row['decision_reason']}<br>
                    <strong>Reviewer:</strong> {row['reviewer']}<br>
                    <strong>Time:</strong> {row['reviewed_at']}
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### ⚖️ Take Action")
        
        action = st.selectbox(
            "Select Action",
            [
                "Keep Restricted",
                "Release Restriction",
                "Escalate Case",
                "Request More Evidence"
            ]
        )
        
        decision_reason = st.text_area("Decision Reason (Required)", placeholder="Explain your decision...")
        
        if st.button("Submit Decision", type="primary", ):
            if not decision_reason:
                st.error("❌ Please provide a reason for your decision.")
                return
            
            # Determine new statuses based on action
            if action == "Keep Restricted":
                new_status = "Under Investigation"
                new_account_status = "Temporarily Restricted"
            elif action == "Release Restriction":
                new_status = "Restriction Released"
                new_account_status = "Active"
            elif action == "Escalate Case":
                new_status = "Escalated"
                new_account_status = "Temporarily Restricted"
            else:  # Request More Evidence
                new_status = "Flagged for Review"
                new_account_status = "Active"
            
            if update_case_status(selected_case_id, new_status, new_account_status, 
                               decision_reason, st.session_state.manager_username):
                st.success(f"✅ Decision recorded successfully. Case status updated to: {new_status}")
                st.rerun()
            else:
                st.error("❌ Failed to update case. Please try again.")
