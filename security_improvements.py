# Security Improvements for Shopping Cart & Banking System

## 1. Password Hashing Implementation

import hashlib
import secrets

def hash_password(password: str) -> str:
    """Hash password with salt for secure storage"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{password_hash.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against stored hash"""
    try:
        salt, stored_hash = hashed.split(':')
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return stored_hash == password_hash.hex()
    except ValueError:
        return False

## 2. Session Security
class SecureSession:
    def __init__(self):
        self.session_token = None
        self.user_id = None
        self.login_time = None
        self.last_activity = None
    
    def create_session(self, user_id):
        self.session_token = secrets.token_urlsafe(32)
        self.user_id = user_id
        self.login_time = datetime.now()
        self.last_activity = datetime.now()
    
    def is_valid(self, timeout_minutes=30):
        if not self.session_token:
            return False
        
        time_since_activity = datetime.now() - self.last_activity
        return time_since_activity.total_seconds() < (timeout_minutes * 60)

## 3. Input Validation
import re

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

def sanitize_input(input_str: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
    for char in dangerous_chars:
        input_str = input_str.replace(char, '')
    return input_str.strip()

## 4. Banking Security
def validate_account_number(account_num: str) -> bool:
    """Validate account number format"""
    return account_num.isdigit() and 8 <= len(account_num) <= 16

def validate_transaction_amount(amount: str) -> tuple[bool, float]:
    """Validate transaction amount"""
    try:
        amt = float(amount)
        if amt <= 0:
            return False, 0
        if amt > 100000:  # Daily limit
            return False, 0
        return True, amt
    except ValueError:
        return False, 0

## 5. Rate Limiting
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    def __init__(self):
        self.attempts = defaultdict(list)
    
    def is_allowed(self, identifier: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """Check if operation is allowed based on rate limiting"""
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old attempts
        self.attempts[identifier] = [
            attempt_time for attempt_time in self.attempts[identifier]
            if attempt_time > window_start
        ]
        
        # Check if under limit
        if len(self.attempts[identifier]) >= max_attempts:
            return False
        
        # Record this attempt
        self.attempts[identifier].append(now)
        return True
