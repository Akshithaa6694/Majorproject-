import sqlite3
import bcrypt
import re
from datetime import datetime
from pathlib import Path
import streamlit as st


def get_db_connection():
    """Get database connection."""
    BASE = Path(__file__).resolve().parent
    DB_FILE = BASE / "data" / "fraud_detection.db"
    return sqlite3.connect(DB_FILE)


def create_users_table():
    """Create users table if it doesn't exist."""
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            full_name TEXT,
            password_hash TEXT,
            created_at TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()


def validate_email(email):
    """Validate email format."""
    if not email:
        return False, "Email is required"
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Invalid email format"
    
    return True, "Valid email"


def validate_password(password):
    """Validate password strength."""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    if not re.search(r'[@#$%!&*]', password):
        errors.append("Password must contain at least one special character (@, #, $, %, !, &, *)")
    
    if ' ' in password:
        errors.append("Password must not contain spaces")
    
    if errors:
        return False, errors
    
    return True, []


def hash_password(password):
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password, hashed_password):
    """Verify password against hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except:
        return False


def check_email_exists(email):
    """Check if email already exists."""
    conn = get_db_connection()
    cursor = conn.execute("SELECT id FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def check_username_exists(username):
    """Check if username already exists."""
    conn = get_db_connection()
    cursor = conn.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def create_user(username, email, full_name, password):
    """Create a new user account."""
    conn = get_db_connection()
    try:
        # Hash password
        password_hash = hash_password(password)
        
        # Insert user
        conn.execute("""
            INSERT INTO users (username, email, full_name, password_hash, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, email, full_name, password_hash, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1))
        
        conn.commit()
        return True, "Account created successfully"
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return False, "Username already exists"
        elif "email" in str(e):
            return False, "Email already registered"
        else:
            return False, "Registration failed"
    except Exception as e:
        conn.rollback()
        return False, f"Error: {str(e)}"
    finally:
        conn.close()


def authenticate_user(username, password):
    """Authenticate user with username and password."""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT id, username, email, full_name, password_hash, is_active FROM users WHERE username = ?",
            (username,)
        )
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return False, None, "User not found"
        
        user_id, username, email, full_name, password_hash, is_active = user
        
        if not is_active:
            return False, None, "Account is inactive"
        
        if verify_password(password, password_hash):
            return True, {
                'id': user_id,
                'username': username,
                'email': email,
                'full_name': full_name
            }, "Login successful"
        else:
            return False, None, "Incorrect password"
    except Exception as e:
        conn.close()
        return False, None, f"Error: {str(e)}"


def get_user_by_username(username):
    """Get user information by username."""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT id, username, email, full_name, created_at FROM users WHERE username = ?",
            (username,)
        )
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'full_name': user[3],
                'created_at': user[4]
            }
        return None
    except Exception as e:
        conn.close()
        return None


def show_password_requirements():
    """Display password requirements."""
    st.markdown("""
    <div style="background: #f0f9ff; padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6; margin: 10px 0;">
        <strong>Password Requirements:</strong>
        <ul style="margin: 5px 0; padding-left: 20px;">
            <li>Minimum 8 characters</li>
            <li>At least one uppercase letter (A-Z)</li>
            <li>At least one lowercase letter (a-z)</li>
            <li>At least one number (0-9)</li>
            <li>At least one special character (@, #, $, %, !, &, *)</li>
            <li>No spaces allowed</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
