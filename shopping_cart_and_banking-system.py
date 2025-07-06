import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
import os
import csv
import json
from datetime import date, datetime
from collections import Counter
import hashlib
import secrets
import re
import threading
import time
import logging

# File paths
FILES = {
    'PRODUCTS': 'products.json',
    'CATEGORIES': 'categories.json',
    'HISTORY': 'history.json',
    'FEEDBACK': 'feedback.txt',
    'SHOP': 'shop.json',
    'ACCOUNTS': 'accounts.json',
    'TRANSACTIONS': 'transactions.json',
    'SETTINGS': 'settings.json',
    'USERS': 'users.json',
    'ANALYTICS': 'analytics.json',
    'LOGS': 'app.log'
}

# Configure logging
logging.basicConfig(
    filename=FILES['LOGS'],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create console handler for development
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

# Default configurations
DEFAULT_CATEGORIES = [
    "Fresh Produce", "Dairy, Bread & Eggs", "Meat & Seafood", "Packaged & Breakfast Foods",
    "Snacks & Munchies", "Beverages", "Zepto Cafe", "Personal Care", "Beauty & Makeup",
    "Health & Wellness", "Home & Cleaning Supplies", "Home Decor & Essentials",
    "Apparel and Accessories", "Electronics & Gadgets", "Family Care", "Pet Supplies"
]

DEFAULT_SHOP = {
    "shop_name": "Ashish's online banking and shopping",
    "address": "334 F-block alpha 2, Gr. Noida UP 201310, India",
    "contact": "+91-1234567890",
    "email": "0241cys143@niet.co.in",
    "about": "Ashish's online banking and shopping is your comprehensive banking and shopping solution.",
    "owner": "Ashish"
}

DEFAULT_SETTINGS = {
    "dark_mode": False,
    "notifications_enabled": True,
    "language": "English"
}

ADMIN_PASSWORD = "admin123"

# Utility functions
def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def append_feedback(feedback):
    with open(FILES['FEEDBACK'], "a", encoding="utf-8") as f:
        f.write(feedback + "\n---\n")

# Security functions
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

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password: str) -> dict:
    """Validate password strength and return feedback"""
    result = {"valid": True, "issues": []}
    
    if len(password) < 8:
        result["issues"].append("At least 8 characters")
        result["valid"] = False
    
    if not re.search(r'[A-Z]', password):
        result["issues"].append("At least one uppercase letter")
        result["valid"] = False
    
    if not re.search(r'[a-z]', password):
        result["issues"].append("At least one lowercase letter")
        result["valid"] = False
    
    if not re.search(r'\d', password):
        result["issues"].append("At least one number")
        result["valid"] = False
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result["issues"].append("At least one special character")
        result["valid"] = False
    
    return result

class SecureSession:
    """Secure session management"""
    def __init__(self):
        self.session_token = None
        self.user_id = None
        self.login_time = None
        self.last_activity = None
        self.failed_attempts = {}
    
    def create_session(self, user_id):
        self.session_token = secrets.token_urlsafe(32)
        self.user_id = user_id
        self.login_time = datetime.now()
        self.last_activity = datetime.now()
        # Reset failed attempts on successful login
        if user_id in self.failed_attempts:
            del self.failed_attempts[user_id]
    
    def is_valid(self, timeout_minutes=30):
        if not self.session_token:
            return False
        
        time_since_activity = datetime.now() - self.last_activity
        return time_since_activity.total_seconds() < (timeout_minutes * 60)
    
    def update_activity(self):
        self.last_activity = datetime.now()
    
    def is_account_locked(self, user_id, max_attempts=5, lockout_minutes=15):
        """Check if account is locked due to failed login attempts"""
        if user_id not in self.failed_attempts:
            return False
        
        attempts_data = self.failed_attempts[user_id]
        if attempts_data['count'] >= max_attempts:
            time_since_last = datetime.now() - attempts_data['last_attempt']
            return time_since_last.total_seconds() < (lockout_minutes * 60)
        
        return False
    
    def record_failed_attempt(self, user_id):
        """Record a failed login attempt"""
        if user_id not in self.failed_attempts:
            self.failed_attempts[user_id] = {'count': 0, 'last_attempt': datetime.now()}
        
        self.failed_attempts[user_id]['count'] += 1
        self.failed_attempts[user_id]['last_attempt'] = datetime.now()

# Rate limiting for API calls
class RateLimiter:
    """Simple rate limiter for preventing abuse"""
    def __init__(self, max_requests=10, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, identifier):
        """Check if request is allowed for given identifier"""
        now = time.time()
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove old requests outside the window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if now - req_time < self.window_seconds
        ]
        
        # Check if under limit
        if len(self.requests[identifier]) < self.max_requests:
            self.requests[identifier].append(now)
            return True
        
        return False

def add_hover_effect(widget, bg_normal, fg_normal, bg_hover, fg_hover, tooltip_text=None):
    def on_enter(e):
        widget['background'] = bg_hover
        widget['foreground'] = fg_hover
        if tooltip_text:
            widget.tooltip = tk.Toplevel(widget)
            widget.tooltip.wm_overrideredirect(True)
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + 20
            widget.tooltip.wm_geometry(f"+{x}+{y}")
            tk.Label(widget.tooltip, text=tooltip_text, bg="#222", fg="white", font=("Segoe UI", 9)).pack()
    def on_leave(e):
        widget['background'] = bg_normal
        widget['foreground'] = fg_normal
        if hasattr(widget, 'tooltip'):
            widget.tooltip.destroy()
            del widget.tooltip
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)

class NotificationManager:
    """Modern notification system"""
    def __init__(self, parent):
        self.parent = parent
        self.notifications = []
    
    def show_notification(self, message, notification_type="info", duration=3000):
        """Show a notification banner"""
        # Create notification frame
        notification = tk.Frame(self.parent, height=50)
        notification.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(5, 0))
        
        # Style based on type
        colors = {
            "info": {"bg": "#d1ecf1", "fg": "#0c5460", "border": "#bee5eb"},
            "success": {"bg": "#d4edda", "fg": "#155724", "border": "#c3e6cb"},
            "warning": {"bg": "#fff3cd", "fg": "#856404", "border": "#ffeaa7"},
            "error": {"bg": "#f8d7da", "fg": "#721c24", "border": "#f5c6cb"}
        }
        
        color = colors.get(notification_type, colors["info"])
        notification.configure(bg=color["bg"], relief="solid", bd=1)
        
        # Add message
        label = tk.Label(
            notification, 
            text=message, 
            bg=color["bg"], 
            fg=color["fg"],
            font=("Segoe UI", 10, "bold"),
            pady=10
        )
        label.pack(side=tk.LEFT, padx=15)
        
        # Add close button
        close_btn = tk.Button(
            notification,
            text="×",
            bg=color["bg"],
            fg=color["fg"],
            border=0,
            font=("Segoe UI", 12, "bold"),
            command=lambda: self._close_notification(notification)
        )
        close_btn.pack(side=tk.RIGHT, padx=10)
        
        # Auto-close after duration
        self.parent.after(duration, lambda: self._close_notification(notification))
        
        self.notifications.append(notification)
    
    def _close_notification(self, notification):
        """Close and remove notification"""
        if notification in self.notifications:
            notification.destroy()
            self.notifications.remove(notification)

class ModernUI:
    """Modern UI components and styling"""
    
    @staticmethod
    def create_card_frame(parent, **kwargs):
        """Create a modern card-style frame"""
        frame = tk.Frame(
            parent,
            bg=kwargs.get('bg', '#ffffff'),
            relief='solid',
            bd=1,
            padx=kwargs.get('padx', 20),
            pady=kwargs.get('pady', 15)
        )
        
        # Add subtle shadow effect
        shadow = tk.Frame(parent, bg='#e0e0e0', height=2)
        return frame, shadow
    
    @staticmethod
    def create_gradient_button(parent, text, command, **kwargs):
        """Create a modern gradient-style button"""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=kwargs.get('bg', '#007bff'),
            fg=kwargs.get('fg', 'white'),
            font=kwargs.get('font', ('Segoe UI', 11, 'bold')),
            relief='flat',
            bd=0,
            padx=kwargs.get('padx', 20),
            pady=kwargs.get('pady', 10),
            cursor='hand2'
        )
        
        # Add hover effects
        normal_bg = kwargs.get('bg', '#007bff')
        hover_bg = kwargs.get('hover_bg', '#0056b3')
        
        def on_enter(e):
            btn.configure(bg=hover_bg)
        def on_leave(e):
            btn.configure(bg=normal_bg)
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        return btn
    
    @staticmethod
    def create_modern_entry(parent, placeholder="", **kwargs):
        """Create a modern entry widget with placeholder"""
        entry = tk.Entry(
            parent,
            font=kwargs.get('font', ('Segoe UI', 11)),
            relief='solid',
            bd=1,
            **kwargs
        )
        
        # Add placeholder functionality
        if placeholder:
            entry.placeholder = placeholder
            entry.placeholder_color = '#999999'
            entry.default_color = entry.cget('fg')
            
            def on_focus_in(event):
                if entry.get() == entry.placeholder:
                    entry.delete(0, tk.END)
                    entry.configure(fg=entry.default_color)
            
            def on_focus_out(event):
                if not entry.get():
                    entry.insert(0, entry.placeholder)
                    entry.configure(fg=entry.placeholder_color)
            
            entry.bind('<FocusIn>', on_focus_in)
            entry.bind('<FocusOut>', on_focus_out)
            
            # Set initial placeholder
            entry.insert(0, placeholder)
            entry.configure(fg=entry.placeholder_color)
        
        return entry

class AnalyticsTracker:
    """Track user behavior and app performance"""
    def __init__(self):
        self.analytics_file = FILES['ANALYTICS']
        self.session_data = {
            'session_id': secrets.token_hex(8),
            'start_time': datetime.now().isoformat(),
            'events': [],
            'performance_metrics': {}
        }
    
    def track_event(self, event_type, event_data=None):
        """Track user events for analytics"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': event_data or {}
        }
        self.session_data['events'].append(event)
        
        # Log important events
        if event_type in ['login', 'logout', 'purchase', 'error']:
            logging.info(f"Analytics: {event_type} - {event_data}")
    
    def track_performance(self, operation, duration):
        """Track performance metrics"""
        if operation not in self.session_data['performance_metrics']:
            self.session_data['performance_metrics'][operation] = []
        
        self.session_data['performance_metrics'][operation].append({
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        })
    
    def save_session(self):
        """Save session analytics to file"""
        try:
            # Load existing analytics
            analytics_data = load_json(self.analytics_file, {'sessions': []})
            
            # Add current session
            self.session_data['end_time'] = datetime.now().isoformat()
            analytics_data['sessions'].append(self.session_data)
            
            # Keep only last 1000 sessions to prevent file bloat
            analytics_data['sessions'] = analytics_data['sessions'][-1000:]
            
            # Save analytics
            save_json(self.analytics_file, analytics_data)
            
        except Exception as e:
            logging.error(f"Failed to save analytics: {e}")

# GST utilities and validation
class GSTUtils:
    """Utility class for GST calculations and validations"""
    
    # Standard GST rates in India
    STANDARD_GST_RATES = [0, 3, 5, 12, 18, 28]
    
    @staticmethod
    def validate_gst_number(gst_number):
        """
        Validate GST number format (15 characters: 2 state code + 10 PAN + 1 entity + 1 check digit + 1 default)
        Example: 07AABCU9603R1ZM
        """
        if not gst_number or len(gst_number) != 15:
            return False
        
        # Check if first 2 characters are digits (state code)
        if not gst_number[:2].isdigit():
            return False
        
        # Check if characters 3-12 are alphanumeric (PAN format)
        pan_part = gst_number[2:12]
        if not pan_part.isalnum():
            return False
        
        # Check if remaining characters are alphanumeric
        if not gst_number[12:].isalnum():
            return False
        
        return True
    
    @staticmethod
    def validate_gst_rate(gst_rate):
        """Validate if GST rate is a standard rate"""
        return gst_rate in GSTUtils.STANDARD_GST_RATES
    
    @staticmethod
    def get_gst_rate_category(gst_rate):
        """Get the category based on GST rate"""
        if gst_rate == 0:
            return "Exempt"
        elif gst_rate == 3:
            return "Essential Goods"
        elif gst_rate == 5:
            return "Necessities"
        elif gst_rate == 12:
            return "Standard Goods"
        elif gst_rate == 18:
            return "Standard Services"
        elif gst_rate == 28:
            return "Luxury Items"
        else:
            return "Custom Rate"
    
    @staticmethod
    def format_gst_invoice_number(order_id, financial_year=None):
        """Generate GST invoice number format"""
        if not financial_year:
            current_date = datetime.now()
            if current_date.month >= 4:  # Financial year starts from April
                fy_start = current_date.year
                fy_end = current_date.year + 1
            else:
                fy_start = current_date.year - 1
                fy_end = current_date.year
            financial_year = f"{fy_start}-{str(fy_end)[2:]}"
        
        return f"GST/{financial_year}/{order_id}"
    
    @staticmethod
    def calculate_reverse_charge(amount, is_reverse_charge=False):
        """Calculate reverse charge applicability"""
        if is_reverse_charge:
            return {
                'applicable': True,
                'amount': amount,
                'note': 'Reverse charge applicable as per Section 9(3) of CGST Act'
            }
        return {'applicable': False, 'amount': 0, 'note': ''}

def validate_product_gst_data(product):
    """Validate GST-related data in product"""
    errors = []
    
    # Check GST rate
    gst_rate = product.get('gst_rate', 0)
    if not isinstance(gst_rate, (int, float)) or gst_rate < 0 or gst_rate > 28:
        errors.append(f"Invalid GST rate: {gst_rate}. Must be between 0 and 28.")
    
    if not GSTUtils.validate_gst_rate(gst_rate):
        errors.append(f"Non-standard GST rate: {gst_rate}. Standard rates are: {GSTUtils.STANDARD_GST_RATES}")
    
    # Check price structure
    if 'price_inclusive_gst' not in product:
        product['price_inclusive_gst'] = True  # Default to inclusive
    
    return errors
class CacheManager:
    """Simple caching system for improved performance"""
    def __init__(self, default_timeout=300):  # 5 minutes default
        self.cache = {}
        self.default_timeout = default_timeout
    
    def get(self, key):
        """Get cached value if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.default_timeout:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key, value, timeout=None):
        """Set cache value with timestamp"""
        timeout = timeout or self.default_timeout
        self.cache[key] = (value, time.time())
    
    def invalidate(self, key):
        """Remove item from cache"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()

# --- Add per-user cashback system ---

# 1. Store user cashback in accounts (admin can set/remove it)
# Example: self.accounts[acc_num]['cashback_percent'] = 5.0

# 2. Update ShoppingCart.get_details to use user cashback if present

class ShoppingCart:
    def __init__(self):
        self.items = Counter()
        self.user_cashback = 0.0  # Default, set by MainApp on login or guest

    def add(self, product_id, qty):
        self.items[product_id] += qty

    def remove(self, product_id):
        if product_id in self.items:
            del self.items[product_id]

    def clear(self):
        self.items.clear()

    @staticmethod
    def calculate_gst_breakdown(base_amount, gst_rate, is_interstate=False):
        """
        Calculate GST breakdown for CGST, SGST, and IGST
        
        Args:
            base_amount (float): Base amount before GST
            gst_rate (float): GST rate as percentage (e.g., 18 for 18%)
            is_interstate (bool): True for interstate transaction (IGST), False for intrastate (CGST+SGST)
        
        Returns:
            dict: GST breakdown with cgst, sgst, igst amounts
        """
        total_gst = base_amount * (gst_rate / 100)
        
        if is_interstate:
            return {
                'cgst': 0,
                'sgst': 0,
                'igst': total_gst,
                'total': total_gst
            }
        else:
            # For intrastate: CGST = SGST = Total GST / 2
            half_gst = total_gst / 2
            return {
                'cgst': half_gst,
                'sgst': half_gst,
                'igst': 0,
                'total': total_gst
            }

    @staticmethod
    def extract_gst_from_inclusive_price(inclusive_price, gst_rate):
        """
        Extract base price and GST amount from GST-inclusive price
        
        Args:
            inclusive_price (float): Price including GST
            gst_rate (float): GST rate as percentage
        
        Returns:
            tuple: (base_price, gst_amount)
        """
        base_price = inclusive_price / (1 + (gst_rate / 100))
        gst_amount = inclusive_price - base_price
        return base_price, gst_amount

    @staticmethod
    def add_gst_to_exclusive_price(exclusive_price, gst_rate):
        """
        Add GST to GST-exclusive price
        
        Args:
            exclusive_price (float): Price excluding GST
            gst_rate (float): GST rate as percentage
        
        Returns:
            tuple: (base_price, gst_amount, total_price)
        """
        gst_amount = exclusive_price * (gst_rate / 100)
        total_price = exclusive_price + gst_amount
        return exclusive_price, gst_amount, total_price

    def get_details(self, products):
        catalog = {p['product_id']: p for p in products}
        items = []
        subtotal_pre_gst = 0
        total_gst = 0
        total_cgst = 0
        total_sgst = 0
        total_igst = 0
        total_cashback = 0

        for pid, qty in self.items.items():
            if pid in catalog:
                product = catalog[pid]
                price = float(product.get('price', 0))
                gst_rate = float(product.get('gst_rate', 0))  # Expected as percentage (e.g., 18 for 18%)
                discount = float(product.get('discount_percent', 0))
                # Use user cashback if set, else product cashback
                cashback = self.user_cashback if self.user_cashback > 0 else float(product.get('cashback_percent', 0))
                
                # Check if price is inclusive or exclusive of GST
                price_inclusive_gst = product.get('price_inclusive_gst', True)  # Default to inclusive
                
                # Calculate base price and GST amounts
                if price_inclusive_gst:
                    # Price includes GST - extract GST from the price
                    base_price = price / (1 + (gst_rate / 100))
                    gst_per_unit = price - base_price
                else:
                    # Price excludes GST - add GST to the price
                    base_price = price
                    gst_per_unit = price * (gst_rate / 100)

                # Apply discount to base price
                discounted_base_price = base_price * (1 - discount / 100)
                
                # Calculate line totals
                line_subtotal = discounted_base_price * qty
                line_gst_amount = gst_per_unit * (1 - discount / 100) * qty
                line_total = line_subtotal + line_gst_amount
                
                # Calculate GST breakdown (CGST + SGST for intra-state, IGST for inter-state)
                # For simplicity, assuming intra-state transactions (CGST + SGST)
                # In real applications, this would be determined by buyer/seller state
                is_interstate = product.get('is_interstate', False)
                
                if is_interstate:
                    igst_amount = line_gst_amount
                    cgst_amount = 0
                    sgst_amount = 0
                else:
                    igst_amount = 0
                    cgst_amount = line_gst_amount / 2
                    sgst_amount = line_gst_amount / 2

                # Calculate cashback based on discounted base price
                cashback_amount = discounted_base_price * (cashback / 100) * qty

                items.append({
                    'product': product,
                    'quantity': qty,
                    'original_price': price,
                    'base_price': base_price,
                    'discounted_base_price': discounted_base_price,
                    'gst_rate': gst_rate,
                    'gst_per_unit': gst_per_unit,
                    'line_subtotal': line_subtotal,
                    'line_gst_amount': line_gst_amount,
                    'cgst_amount': cgst_amount,
                    'sgst_amount': sgst_amount,
                    'igst_amount': igst_amount,
                    'line_total': line_total,
                    'cashback_amount': cashback_amount,
                    'cashback_percent': cashback,
                    'price_inclusive_gst': price_inclusive_gst
                })

                subtotal_pre_gst += line_subtotal
                total_gst += line_gst_amount
                total_cgst += cgst_amount
                total_sgst += sgst_amount
                total_igst += igst_amount
                total_cashback += cashback_amount

        delivery_charge = 0 if subtotal_pre_gst > 50 else 5
        delivery_gst_rate = 18.0  # 18% GST on delivery
        delivery_gst = delivery_charge * (delivery_gst_rate / 100) if delivery_charge > 0 else 0
        
        # Add delivery GST to totals
        total_gst += delivery_gst
        if delivery_charge > 0:
            # Assuming intra-state delivery
            total_cgst += delivery_gst / 2
            total_sgst += delivery_gst / 2

        grand_total = subtotal_pre_gst + total_gst + delivery_charge

        return {
            'items': items,
            'subtotal_pre_gst': subtotal_pre_gst,
            'total_gst': total_gst,
            'total_cgst': total_cgst,
            'total_sgst': total_sgst,
            'total_igst': total_igst,
            'delivery_charge': delivery_charge,
            'delivery_gst': delivery_gst,
            'delivery_gst_rate': delivery_gst_rate,
            'grand_total': grand_total,
            'total_cashback': total_cashback
        }

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ashish's Online Banking & Shopping")
        self.geometry("1280x900")
        self.configure(bg="#f7f9fa")
        self.minsize(1100, 700)

        # Initialize security and UI components
        self.session = SecureSession()
        self.rate_limiter = RateLimiter()
        self.notification_manager = NotificationManager(self)
        self.cache_manager = CacheManager()
        self.analytics = AnalyticsTracker()

        # Initialize data
        self.cart = ShoppingCart()
        self.products = load_json(FILES['PRODUCTS'], [])
        self.categories = load_json(FILES['CATEGORIES'], DEFAULT_CATEGORIES)
        self.shop_info = load_json(FILES['SHOP'], DEFAULT_SHOP)
        self.accounts = load_json(FILES['ACCOUNTS'], {})
        self.transactions = load_json(FILES['TRANSACTIONS'], [])
        self.settings = load_json(FILES['SETTINGS'], DEFAULT_SETTINGS.copy())
        self.dark_mode = self.settings.get("dark_mode", False)
        self.notifications_enabled = self.settings.get("notifications_enabled", True)
        self.language = self.settings.get("language", "English")
        
        # User session management
        self.current_user = None  # Will store logged-in user info
        self.is_logged_in = False
        self.users = load_json(FILES['USERS'], {})  # Separate file for user credentials
        
        # Auto-logout timer
        self.auto_logout_timer = None
        self.start_auto_logout_timer()

        # --- Improved Style ---
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure('TNotebook.Tab', font=('Segoe UI', 12, 'bold'), padding=[16, 8])
        self.style.configure('TButton', font=('Segoe UI', 11, 'bold'), padding=6)
        self.style.configure('Treeview.Heading', font=('Segoe UI', 11, 'bold'))

        # --- Main Layout ---
        self.tab_control = ttk.Notebook(self)
        self.tab_control.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # Create tabs
        self.home_tab = tk.Frame(self.tab_control, bg="#f7f9fa")
        self.banking_tab = tk.Frame(self.tab_control, bg="#f7f9fa")
        self.products_tab = tk.Frame(self.tab_control, bg="#f7f9fa")
        self.cart_tab = tk.Frame(self.tab_control, bg="#f7f9fa")
        self.orders_tab = tk.Frame(self.tab_control, bg="#f7f9fa")
        self.profile_tab = tk.Frame(self.tab_control, bg="#f7f9fa")
        self.feedback_tab = tk.Frame(self.tab_control, bg="#f7f9fa")
        self.help_tab = tk.Frame(self.tab_control, bg="#f7f9fa")  # Help tab

        # Add tabs to notebook
        self.tab_control.add(self.home_tab, text="🏠 Home")
        self.tab_control.add(self.banking_tab, text="🏦 Banking")
        self.tab_control.add(self.products_tab, text="🛒 Products")
        self.tab_control.add(self.cart_tab, text="🛍️ Cart")
        self.tab_control.add(self.orders_tab, text="📦 Orders")
        self.tab_control.add(self.profile_tab, text="👤 Profile")
        self.tab_control.add(self.feedback_tab, text="💬 Feedback")
        self.tab_control.add(self.help_tab, text="❓ Help")  # Help tab

        # --- Navigation Bar (Sticky) ---
        nav_bar = tk.Frame(self, bg="#0d6efd", height=48)
        nav_bar.pack(side=tk.TOP, fill=tk.X)
        nav_btns = [
            ("🏠 Home", self.home_tab),
            ("🏦 Banking", self.banking_tab),
            ("🛒 Products", self.products_tab),
            ("🛍️ Cart", self.cart_tab),
            ("📦 Orders", self.orders_tab),
            ("👤 Profile", self.profile_tab),
            ("💬 Feedback", self.feedback_tab),
            ("❓ Help", self.help_tab),  # Help tab
        ]
        for text, tab in nav_btns:
            btn = tk.Button(nav_bar, text=text, font=("Segoe UI", 11, "bold"), bg="#0d6efd", fg="white",
                            bd=0, relief=tk.FLAT, activebackground="#198754", activeforeground="white",
                            command=lambda t=tab: self.tab_control.select(t), cursor="hand2")
            btn.pack(side=tk.LEFT, padx=2, pady=4, ipadx=8)
            add_hover_effect(btn, "#0d6efd", "white", "#198754", "white")

        # --- Top-right controls ---
        btn_settings = tk.Button(nav_bar, text="⚙️ Settings", font=("Segoe UI", 11, "bold"),
                                 bg="#6c757d", fg="white", bd=0, relief=tk.FLAT, cursor="hand2",
                                 command=self.open_settings_window)
        btn_settings.pack(side=tk.RIGHT, padx=8)
        add_hover_effect(btn_settings, "#6c757d", "white", "#495057", "white", tooltip_text="Settings")

        btn_admin = tk.Button(nav_bar, text="🛠️ Admin", font=("Segoe UI", 11, "bold"),
                              bg="#0d6efd", fg="white", bd=0, relief=tk.FLAT, cursor="hand2",
                              command=self.open_admin_window)
        btn_admin.pack(side=tk.RIGHT, padx=8)
        add_hover_effect(btn_admin, "#0d6efd", "white", "#198754", "white", tooltip_text="Admin Panel")

        btn_dark = tk.Button(nav_bar, text="🌙", font=("Segoe UI", 11), bg="#222", fg="white", bd=0, relief=tk.FLAT,
                             command=self.toggle_dark_mode, cursor="hand2")
        btn_dark.pack(side=tk.RIGHT, padx=8)
        add_hover_effect(btn_dark, "#222", "white", "#444", "white", tooltip_text="Toggle Dark Mode")

        # --- Menu Bar ---
        menubar = tk.Menu(self)
        nav_menu = tk.Menu(menubar, tearoff=0)
        for text, tab in nav_btns:
            nav_menu.add_command(label=text, command=lambda t=tab: self.tab_control.select(t))
        menubar.add_cascade(label="Go to", menu=nav_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="How to use", command=lambda: messagebox.showinfo(
            "Help",
            "Use the navigation bar or 'Go to' menu to quickly switch between pages.\n"
            "Tabs are also clickable at the top of the window.\n"
            "For further help, contact: 0241cys143@niet.co.in"
        ))
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

        # --- Footer ---
        self._footer = tk.Frame(self, bg="#0d6efd", height=30)
        self._footer.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(
            self._footer, text="© 2025 Ashish's online banking and shopping", font=("Segoe UI", 10),
            bg="#0d6efd", fg="white"
        ).pack(pady=4)

        # Build tabs
        self.build_home_tab()
        self.build_banking_tab()
        self.build_products_tab()
        self.build_cart_tab()
        self.build_orders_tab()
        self.build_profile_tab()
        self.build_feedback_tab()
        self.build_help_tab()  # Help tab

        # Setup navigation bar and menus
        self.setup_navigation_and_menus()
        
        # Bind activity tracking events
        self.bind_all('<Button-1>', lambda e: self.reset_activity_timer())
        self.bind_all('<Key>', lambda e: self.reset_activity_timer())
        self.bind_all('<Motion>', lambda e: self.reset_activity_timer())
        
        # Bind window close event for proper cleanup
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Track app start
        self.analytics.track_event('app_start')

    def start_auto_logout_timer(self):
        """Start or restart the auto-logout timer"""
        if self.auto_logout_timer:
            self.after_cancel(self.auto_logout_timer)
        
        # Auto logout after 30 minutes of inactivity
        self.auto_logout_timer = self.after(30 * 60 * 1000, self.auto_logout)

    def auto_logout(self):
        """Automatically logout user after inactivity"""
        if self.is_logged_in:
            self.logout_user()
            self.notification_manager.show_notification(
                "You have been automatically logged out due to inactivity.", 
                "warning"
            )

    def reset_activity_timer(self):
        """Reset the activity timer on user interaction"""
        if self.is_logged_in:
            self.session.update_activity()
            self.start_auto_logout_timer()

    def login_user(self, email, password):
        """Secure user login with rate limiting and account lockout"""
        # Rate limiting check
        if not self.rate_limiter.is_allowed(email):
            self.notification_manager.show_notification(
                "Too many login attempts. Please try again later.", 
                "error"
            )
            return False

        # Account lockout check
        if self.session.is_account_locked(email):
            self.notification_manager.show_notification(
                "Account temporarily locked due to failed login attempts.", 
                "error"
            )
            return False

        # Validate credentials
        if email in self.users:
            user_data = self.users[email]
            stored_password = user_data.get('password', '')
            
            # Check if password is hashed (new format) or plain text (old format)
            if ':' in stored_password and len(stored_password) > 50:
                # Hashed password
                if verify_password(password, stored_password):
                    self._complete_login(email, user_data)
                    return True
            else:
                # Plain text password (legacy) - upgrade to hashed
                if password == stored_password:
                    # Upgrade to hashed password
                    self.users[email]['password'] = hash_password(password)
                    save_json(FILES['USERS'], self.users)
                    self._complete_login(email, user_data)
                    return True

        # Failed login attempt
        self.session.record_failed_attempt(email)
        self.notification_manager.show_notification(
            "Invalid email or password.", 
            "error"
        )
        return False

    def _complete_login(self, email, user_data):
        """Complete the login process"""
        self.current_user = {
            'email': email,
            'name': user_data.get('name', 'User'),
            'role': user_data.get('role', 'customer'),
            'cashback_percent': user_data.get('cashback_percent', 0)
        }
        self.is_logged_in = True
        self.session.create_session(email)
        
        # Set user cashback in cart
        self.cart.user_cashback = self.current_user.get('cashback_percent', 0)
        
        # Track login event
        self.analytics.track_event('login', {
            'user_email': email,
            'user_role': user_data.get('role', 'customer')
        })
        
        # Update profile tab
        self.update_profile_display()
        
        # Show welcome notification
        self.notification_manager.show_notification(
            f"Welcome back, {self.current_user['name']}!", 
            "success"
        )
        
        # Start activity timer
        self.start_auto_logout_timer()
        
        logging.info(f"User logged in: {email}")

    def register_user(self, email, password, name, phone=""):
        """Register new user with secure password storage"""
        # Validate email
        if not validate_email(email):
            self.notification_manager.show_notification(
                "Please enter a valid email address.", 
                "error"
            )
            return False

        # Check if user already exists
        if email in self.users:
            self.notification_manager.show_notification(
                "User with this email already exists.", 
                "error"
            )
            return False

        # Validate password strength
        password_check = validate_password_strength(password)
        if not password_check["valid"]:
            issues = ", ".join(password_check["issues"])
            self.notification_manager.show_notification(
                f"Password requirements: {issues}", 
                "error"
            )
            return False

        # Create new user
        self.users[email] = {
            'name': name,
            'password': hash_password(password),
            'phone': phone,
            'role': 'customer',
            'cashback_percent': 0,
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        
        save_json(FILES['USERS'], self.users)
        
        # Track registration event
        self.analytics.track_event('registration', {
            'user_email': email,
            'user_name': name
        })
        
        logging.info(f"New user registered: {email}")
        
        self.notification_manager.show_notification(
            "Account created successfully! You can now log in.", 
            "success"
        )
        return True

    def logout_user(self):
        """Logout current user"""
        if self.is_logged_in:
            # Track logout event
            self.analytics.track_event('logout', {
                'user_email': self.current_user.get('email') if self.current_user else None
            })
            
            # Update last login time
            if self.current_user and self.current_user['email'] in self.users:
                self.users[self.current_user['email']]['last_login'] = datetime.now().isoformat()
                save_json(FILES['USERS'], self.users)
            
            logging.info(f"User logged out: {self.current_user.get('email') if self.current_user else 'Unknown'}")
            
            self.current_user = None
            self.is_logged_in = False
            self.session = SecureSession()  # Reset session
            self.cart.user_cashback = 0  # Reset cart cashback
            
            # Cancel auto-logout timer
            if self.auto_logout_timer:
                self.after_cancel(self.auto_logout_timer)
                self.auto_logout_timer = None
            
            # Update profile display
            self.update_profile_display()
            
            self.notification_manager.show_notification(
                "You have been logged out successfully.", 
                "info"
            )

    def update_profile_display(self):
        """Update the profile tab display based on login status"""
        # Rebuild the entire profile tab to reflect login state
        self.build_profile_tab()

    def on_closing(self):
        """Handle application closing with proper cleanup"""
        try:
            # Track app close
            self.analytics.track_event('app_close')
            
            # Save analytics session
            self.analytics.save_session()
            
            # Save any pending data
            save_json(FILES['SETTINGS'], self.settings)
            
            logging.info("Application closed gracefully")
            
        except Exception as e:
            logging.error(f"Error during application shutdown: {e}")
        
        finally:
            self.destroy()

    def show_progress_dialog(self, title, operation_func, *args, **kwargs):
        """Show a progress dialog for long-running operations"""
        progress_window = tk.Toplevel(self)
        progress_window.title(title)
        progress_window.geometry("400x150")
        progress_window.transient(self)
        progress_window.grab_set()
        
        # Center the window
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (progress_window.winfo_screenheight() // 2) - (150 // 2)
        progress_window.geometry(f"400x150+{x}+{y}")
        
        # Progress label
        progress_label = tk.Label(progress_window, text="Processing...", font=("Segoe UI", 12))
        progress_label.pack(pady=20)
        
        # Progress bar
        progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
        progress_bar.pack(pady=10, padx=50, fill=tk.X)
        progress_bar.start()
        
        # Cancel button
        cancelled = tk.BooleanVar()
        cancel_btn = tk.Button(
            progress_window, 
            text="Cancel", 
            command=lambda: cancelled.set(True),
            bg="#dc3545",
            fg="white"
        )
        cancel_btn.pack(pady=10)
        
        def run_operation():
            try:
                start_time = time.time()
                result = operation_func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Track performance
                operation_name = operation_func.__name__
                self.analytics.track_performance(operation_name, duration)
                
                progress_window.destroy()
                return result
                
            except Exception as e:
                logging.error(f"Operation failed: {e}")
                progress_window.destroy()
                self.notification_manager.show_notification(
                    f"Operation failed: {str(e)}", 
                    "error"
                )
                return None
        
        # Run operation in thread
        def start_operation():
            if not cancelled.get():
                thread = threading.Thread(target=run_operation)
                thread.daemon = True
                thread.start()
        
        progress_window.after(100, start_operation)
        return progress_window

    def nav_button(self, parent, text, tab, side=tk.LEFT):
        btn = tk.Button(parent, text=text, font=("Segoe UI", 10, "bold"), bg="#0d6efd", fg="white",
                        command=lambda: self.tab_control.select(tab))
        btn.pack(side=side, padx=3, pady=2)
        add_hover_effect(btn, "#0d6efd", "white", "#198754", "white")
        return btn

    def nav_bar(self, parent):
        bar = tk.Frame(parent, bg="#e9ecef")
        bar.pack(fill=tk.X, pady=(0, 8))
        self.nav_button(bar, "Home", self.home_tab)
        self.nav_button(bar, "Banking", self.banking_tab)
        self.nav_button(bar, "Products", self.products_tab)
        self.nav_button(bar, "Cart", self.cart_tab)
        self.nav_button(bar, "Orders", self.orders_tab)
        self.nav_button(bar, "Profile", self.profile_tab)
        self.nav_button(bar, "Feedback", self.feedback_tab)
        self.nav_button(bar, "Help", self.help_tab)  # Help tab
        return bar

    def setup_navigation_and_menus(self):
        # Add nav_bar to each tab
        self._nav_bars = []
        for tab in [
            self.home_tab, self.banking_tab, self.products_tab, self.cart_tab,
            self.orders_tab, self.profile_tab, self.feedback_tab, self.help_tab
        ]:
            self._nav_bars.append(self.nav_bar(tab))

        # Dark mode toggle
        self.dark_mode = False
        btn_dark = tk.Button(self, text="🌙", font=("Segoe UI", 12), bg="#222", fg="white", command=self.toggle_dark_mode)
        btn_dark.place(relx=1.0, rely=0.0, anchor="ne", x=-250, y=20)
        add_hover_effect(btn_dark, "#222", "white", "#444", "white", tooltip_text="Toggle Dark Mode")

        # Settings button
        btn_settings = tk.Button(self, text="⚙️ Settings", font=("Segoe UI", 12, "bold"),
                                 bg="#6c757d", fg="white", command=self.open_settings_window)
        btn_settings.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=20)
        add_hover_effect(btn_settings, "#6c757d", "white", "#495057", "white", tooltip_text="Settings")

        # Admin button
        btn_admin = tk.Button(self, text="🛠️ Admin", font=("Segoe UI", 12, "bold"),
                              bg="#0d6efd", fg="white", command=self.open_admin_window)
        btn_admin.place(relx=1.0, rely=0.0, anchor="ne", x=-120, y=20)
        add_hover_effect(btn_admin, "#0d6efd", "white", "#198754", "white", tooltip_text="Admin Panel")

        # Notifications
        self.notifications_enabled = True

        # --- Add a menu bar for easy navigation ---
        menubar = tk.Menu(self)
        nav_menu = tk.Menu(menubar, tearoff=0)
        nav_menu.add_command(label="Home", command=lambda: self.tab_control.select(self.home_tab))
        nav_menu.add_command(label="Banking", command=lambda: self.tab_control.select(self.banking_tab))
        nav_menu.add_command(label="Products", command=lambda: self.tab_control.select(self.products_tab))
        nav_menu.add_command(label="Cart", command=lambda: self.tab_control.select(self.cart_tab))
        nav_menu.add_command(label="Orders", command=lambda: self.tab_control.select(self.orders_tab))
        nav_menu.add_command(label="Profile", command=lambda: self.tab_control.select(self.profile_tab))
        nav_menu.add_command(label="Feedback", command=lambda: self.tab_control.select(self.feedback_tab))
        nav_menu.add_command(label="Help", command=lambda: self.tab_control.select(self.help_tab))  # Help tab
        menubar.add_cascade(label="Go to", menu=nav_menu)

        # Add a Help menu for user guidance
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="How to use", command=lambda: messagebox.showinfo(
            "Help",
            "Use the navigation bar or 'Go to' menu to quickly switch between pages.\n"
            "Tabs are also clickable at the top of the window.\n"
            "For further help, contact: 0241cys143@niet.co.in"
        ))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

        # --- Footer ---
        self._footer = tk.Frame(self, bg="#0d6efd", height=30)
        self._footer.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(
            self._footer, text="© 2025 Ashish's online banking and shopping", font=("Segoe UI", 10),
            bg="#0d6efd", fg="white"
        ).pack(pady=4)

        # Build tabs
        self.build_home_tab()
        self.build_banking_tab()
        self.build_products_tab()
        self.build_cart_tab()
        self.build_orders_tab()
        self.build_profile_tab()
        self.build_feedback_tab()
        self.build_help_tab()  # Help tab

    def nav_button(self, parent, text, tab, side=tk.LEFT):
        btn = tk.Button(parent, text=text, font=("Segoe UI", 10, "bold"), bg="#0d6efd", fg="white",
                        command=lambda: self.tab_control.select(tab))
        btn.pack(side=side, padx=3, pady=2)
        add_hover_effect(btn, "#0d6efd", "white", "#198754", "white")
        return btn

    def nav_bar(self, parent):
        bar = tk.Frame(parent, bg="#e9ecef")
        bar.pack(fill=tk.X, pady=(0, 8))
        self.nav_button(bar, "Home", self.home_tab)
        self.nav_button(bar, "Banking", self.banking_tab)
        self.nav_button(bar, "Products", self.products_tab)
        self.nav_button(bar, "Cart", self.cart_tab)
        self.nav_button(bar, "Orders", self.orders_tab)
        self.nav_button(bar, "Profile", self.profile_tab)
        self.nav_button(bar, "Feedback", self.feedback_tab)
        self.nav_button(bar, "Help", self.help_tab)  # Help tab
        return bar

    def setup_navigation_and_menus(self):
        # Add nav_bar to each tab
        self._nav_bars = []
        for tab in [
            self.home_tab, self.banking_tab, self.products_tab, self.cart_tab,
            self.orders_tab, self.profile_tab, self.feedback_tab, self.help_tab
        ]:
            self._nav_bars.append(self.nav_bar(tab))

        # Dark mode toggle
        self.dark_mode = False
        btn_dark = tk.Button(self, text="🌙", font=("Segoe UI", 12), bg="#222", fg="white", command=self.toggle_dark_mode)
        btn_dark.place(relx=1.0, rely=0.0, anchor="ne", x=-250, y=20)
        add_hover_effect(btn_dark, "#222", "white", "#444", "white", tooltip_text="Toggle Dark Mode")

        # Settings button
        btn_settings = tk.Button(self, text="⚙️ Settings", font=("Segoe UI", 12, "bold"),
                                 bg="#6c757d", fg="white", command=self.open_settings_window)
        btn_settings.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=20)
        add_hover_effect(btn_settings, "#6c757d", "white", "#495057", "white", tooltip_text="Settings")

        # Admin button
        btn_admin = tk.Button(self, text="🛠️ Admin", font=("Segoe UI", 12, "bold"),
                              bg="#0d6efd", fg="white", command=self.open_admin_window)
        btn_admin.place(relx=1.0, rely=0.0, anchor="ne", x=-120, y=20)
        add_hover_effect(btn_admin, "#0d6efd", "white", "#198754", "white", tooltip_text="Admin Panel")

        # Notifications
        self.notifications_enabled = True

        # --- Add a menu bar for easy navigation ---
        menubar = tk.Menu(self)
        nav_menu = tk.Menu(menubar, tearoff=0)
        nav_menu.add_command(label="Home", command=lambda: self.tab_control.select(self.home_tab))
        nav_menu.add_command(label="Banking", command=lambda: self.tab_control.select(self.banking_tab))
        nav_menu.add_command(label="Products", command=lambda: self.tab_control.select(self.products_tab))
        nav_menu.add_command(label="Cart", command=lambda: self.tab_control.select(self.cart_tab))
        nav_menu.add_command(label="Orders", command=lambda: self.tab_control.select(self.orders_tab))
        nav_menu.add_command(label="Profile", command=lambda: self.tab_control.select(self.profile_tab))
        nav_menu.add_command(label="Feedback", command=lambda: self.tab_control.select(self.feedback_tab))
        nav_menu.add_command(label="Help", command=lambda: self.tab_control.select(self.help_tab))  # Help tab
        menubar.add_cascade(label="Go to", menu=nav_menu)

        # Add a Help menu for user guidance
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="How to use", command=lambda: messagebox.showinfo(
            "Help",
            "Use the navigation bar or 'Go to' menu to quickly switch between pages.\n"
            "Tabs are also clickable at the top of the window.\n"
            "For further help, contact: 0241cys143@niet.co.in"
        ))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

        # --- Footer ---
        self._footer = tk.Frame(self, bg="#0d6efd", height=30)
        self._footer.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(
            self._footer, text="© 2025 Ashish's online banking and shopping", font=("Segoe UI", 10),
            bg="#0d6efd", fg="white"
        ).pack(pady=4)

        # Build tabs
        self.build_home_tab()
        self.build_banking_tab()
        self.build_products_tab()
        self.build_cart_tab()
        self.build_orders_tab()
        self.build_profile_tab()
        self.build_feedback_tab()
        self.build_help_tab()  # Help tab

    def nav_button(self, parent, text, tab, side=tk.LEFT):
        btn = tk.Button(parent, text=text, font=("Segoe UI", 10, "bold"), bg="#0d6efd", fg="white",
                        command=lambda: self.tab_control.select(tab))
        btn.pack(side=side, padx=3, pady=2)
        add_hover_effect(btn, "#0d6efd", "white", "#198754", "white")
        return btn

    def nav_bar(self, parent):
        bar = tk.Frame(parent, bg="#e9ecef")
        bar.pack(fill=tk.X, pady=(0, 8))
        self.nav_button(bar, "Home", self.home_tab)
        self.nav_button(bar, "Banking", self.banking_tab)
        self.nav_button(bar, "Products", self.products_tab)
        self.nav_button(bar, "Cart", self.cart_tab)
        self.nav_button(bar, "Orders", self.orders_tab)
        self.nav_button(bar, "Profile", self.profile_tab)
        self.nav_button(bar, "Feedback", self.feedback_tab)
        self.nav_button(bar, "Help", self.help_tab)  # Help tab
        return bar

    def setup_navigation_and_menus(self):
        # Add nav_bar to each tab
        self._nav_bars = []
        for tab in [
            self.home_tab, self.banking_tab, self.products_tab, self.cart_tab,
            self.orders_tab, self.profile_tab, self.feedback_tab, self.help_tab
        ]:
            self._nav_bars.append(self.nav_bar(tab))

        # Dark mode toggle
        self.dark_mode = False
        btn_dark = tk.Button(self, text="🌙", font=("Segoe UI", 12), bg="#222", fg="white", command=self.toggle_dark_mode)
        btn_dark.place(relx=1.0, rely=0.0, anchor="ne", x=-250, y=20)
        add_hover_effect(btn_dark, "#222", "white", "#444", "white", tooltip_text="Toggle Dark Mode")

        # Settings button
        btn_settings = tk.Button(self, text="⚙️ Settings", font=("Segoe UI", 12, "bold"),
                                 bg="#6c757d", fg="white", command=self.open_settings_window)
        btn_settings.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=20)
        add_hover_effect(btn_settings, "#6c757d", "white", "#495057", "white", tooltip_text="Settings")

        # Admin button
        btn_admin = tk.Button(self, text="🛠️ Admin", font=("Segoe UI", 12, "bold"),
                              bg="#0d6efd", fg="white", command=self.open_admin_window)
        btn_admin.place(relx=1.0, rely=0.0, anchor="ne", x=-120, y=20)
        add_hover_effect(btn_admin, "#0d6efd", "white", "#198754", "white", tooltip_text="Admin Panel")

        # Notifications
        self.notifications_enabled = True

        # --- Add a menu bar for easy navigation ---
        menubar = tk.Menu(self)
        nav_menu = tk.Menu(menubar, tearoff=0)
        nav_menu.add_command(label="Home", command=lambda: self.tab_control.select(self.home_tab))
        nav_menu.add_command(label="Banking", command=lambda: self.tab_control.select(self.banking_tab))
        nav_menu.add_command(label="Products", command=lambda: self.tab_control.select(self.products_tab))
        nav_menu.add_command(label="Cart", command=lambda: self.tab_control.select(self.cart_tab))
        nav_menu.add_command(label="Orders", command=lambda: self.tab_control.select(self.orders_tab))
        nav_menu.add_command(label="Profile", command=lambda: self.tab_control.select(self.profile_tab))
        nav_menu.add_command(label="Feedback", command=lambda: self.tab_control.select(self.feedback_tab))
        nav_menu.add_command(label="Help", command=lambda: self.tab_control.select(self.help_tab))  # Help tab
        menubar.add_cascade(label="Go to", menu=nav_menu)

        # Add a Help menu for user guidance
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="How to use", command=lambda: messagebox.showinfo(
            "Help",
            "Use the navigation bar or 'Go to' menu to quickly switch between pages.\n"
            "Tabs are also clickable at the top of the window.\n"
            "For further help, contact: 0241cys143@niet.co.in"
        ))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

        # --- Footer ---
        self._footer = tk.Frame(self, bg="#0d6efd", height=30)
        self._footer.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(
            self._footer, text="© 2025 Ashish's online banking and shopping", font=("Segoe UI", 10),
            bg="#0d6efd", fg="white"
        ).pack(pady=4)

        # Build tabs
        self.build_home_tab()
        self.build_banking_tab()
        self.build_products_tab()
        self.build_cart_tab()
        self.build_orders_tab()
        self.build_profile_tab()
        self.build_feedback_tab()
        self.build_help_tab()  # Help tab

    def nav_button(self, parent, text, tab, side=tk.LEFT):
        btn = tk.Button(parent, text=text, font=("Segoe UI", 10, "bold"), bg="#0d6efd", fg="white",
                        command=lambda: self.tab_control.select(tab))
        btn.pack(side=side, padx=3, pady=2)
        add_hover_effect(btn, "#0d6efd", "white", "#198754", "white")
        return btn

    def nav_bar(self, parent):
        bar = tk.Frame(parent, bg="#e9ecef")
        bar.pack(fill=tk.X, pady=(0, 8))
        self.nav_button(bar, "Home", self.home_tab)
        self.nav_button(bar, "Banking", self.banking_tab)
        self.nav_button(bar, "Products", self.products_tab)
        self.nav_button(bar, "Cart", self.cart_tab)
        self.nav_button(bar, "Orders", self.orders_tab)
        self.nav_button(bar, "Profile", self.profile_tab)
        self.nav_button(bar, "Feedback", self.feedback_tab)
        self.nav_button(bar, "Help", self.help_tab)  # Help tab
        return bar

    def setup_navigation_and_menus(self):
        # Add nav_bar to each tab
        self._nav_bars = []
        for tab in [
            self.home_tab, self.banking_tab, self.products_tab, self.cart_tab,
            self.orders_tab, self.profile_tab, self.feedback_tab, self.help_tab
        ]:
            self._nav_bars.append(self.nav_bar(tab))

        # Dark mode toggle
        self.dark_mode = False
        btn_dark = tk.Button(self, text="🌙", font=("Segoe UI", 12), bg="#222", fg="white", command=self.toggle_dark_mode)
        btn_dark.place(relx=1.0, rely=0.0, anchor="ne", x=-250, y=20)
        add_hover_effect(btn_dark, "#222", "white", "#444", "white", tooltip_text="Toggle Dark Mode")

        # Settings button
        btn_settings = tk.Button(self, text="⚙️ Settings", font=("Segoe UI", 12, "bold"),
                                 bg="#6c757d", fg="white", command=self.open_settings_window)
        btn_settings.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=20)
        add_hover_effect(btn_settings, "#6c757d", "white", "#495057", "white", tooltip_text="Settings")

        # Admin button
        btn_admin = tk.Button(self, text="🛠️ Admin", font=("Segoe UI", 12, "bold"),
                              bg="#0d6efd", fg="white", command=self.open_admin_window)
        btn_admin.place(relx=1.0, rely=0.0, anchor="ne", x=-120, y=20)
        add_hover_effect(btn_admin, "#0d6efd", "white", "#198754", "white", tooltip_text="Admin Panel")

        # Notifications
        self.notifications_enabled = True

        # --- Add a menu bar for easy navigation ---
        menubar = tk.Menu(self)
        nav_menu = tk.Menu(menubar, tearoff=0)
        nav_menu.add_command(label="Home", command=lambda: self.tab_control.select(self.home_tab))
        nav_menu.add_command(label="Banking", command=lambda: self.tab_control.select(self.banking_tab))
        nav_menu.add_command(label="Products", command=lambda: self.tab_control.select(self.products_tab))
        nav_menu.add_command(label="Cart", command=lambda: self.tab_control.select(self.cart_tab))
        nav_menu.add_command(label="Orders", command=lambda: self.tab_control.select(self.orders_tab))
        nav_menu.add_command(label="Profile", command=lambda: self.tab_control.select(self.profile_tab))
        nav_menu.add_command(label="Feedback", command=lambda: self.tab_control.select(self.feedback_tab))
        nav_menu.add_command(label="Help", command=lambda: self.tab_control.select(self.help_tab))  # Help tab
        menubar.add_cascade(label="Go to", menu=nav_menu)

        # Add a Help menu for user guidance
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="How to use", command=lambda: messagebox.showinfo(
            "Help",
            "Use the navigation bar or 'Go to' menu to quickly switch between pages.\n"
            "Tabs are also clickable at the top of the window.\n"
            "For further help, contact: 0241cys143@niet.co.in"
        ))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

        # --- Footer ---
        self._footer = tk.Frame(self, bg="#0d6efd", height=30)
        self._footer.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(
            self._footer, text="© 2025 Ashish's online banking and shopping", font=("Segoe UI", 10),
            bg="#0d6efd", fg="white"
        ).pack(pady=4)

        # Build tabs
        self.build_home_tab()
        self.build_banking_tab()
        self.build_products_tab()
        self.build_cart_tab()
        self.build_orders_tab()
        self.build_profile_tab()
        self.build_feedback_tab()
        self.build_help_tab()  # Help tab

    def nav_button(self, parent, text, tab, side=tk.LEFT):
        btn = tk.Button(parent, text=text, font=("Segoe UI", 10, "bold"), bg="#0d6efd", fg="white",
                        command=lambda: self.tab_control.select(tab))
        btn.pack(side=side, padx=3, pady=2)
        add_hover_effect(btn, "#0d6efd", "white", "#198754", "white")
        return btn

    def nav_bar(self, parent):
        bar = tk.Frame(parent, bg="#e9ecef")
        bar.pack(fill=tk.X, pady=(0, 8))
        self.nav_button(bar, "Home", self.home_tab)
        self.nav_button(bar, "Banking", self.banking_tab)
        self.nav_button(bar, "Products", self.products_tab)
        self.nav_button(bar, "Cart", self.cart_tab)
        self.nav_button(bar, "Orders", self.orders_tab)
        self.nav_button(bar, "Profile", self.profile_tab)
        self.nav_button(bar, "Feedback", self.feedback_tab)
        self.nav_button(bar, "Help", self.help_tab)  # Help tab
        return bar

    def setup_navigation_and_menus(self):
        # Add nav_bar to each tab
        self._nav_bars = []
        for tab in [
            self.home_tab, self.banking_tab, self.products_tab, self.cart_tab,
            self.orders_tab, self.profile_tab, self.feedback_tab, self.help_tab
        ]:
            self._nav_bars.append(self.nav_bar(tab))

        # Dark mode toggle
        self.dark_mode = False
        btn_dark = tk.Button(self, text="🌙", font=("Segoe UI", 12), bg="#222", fg="white", command=self.toggle_dark_mode)
        btn_dark.place(relx=1.0, rely=0.0, anchor="ne", x=-250, y=20)
        add_hover_effect(btn_dark, "#222", "white", "#444", "white", tooltip_text="Toggle Dark Mode")

        # Settings button
        btn_settings = tk.Button(self, text="⚙️ Settings", font=("Segoe UI", 12, "bold"),
                                 bg="#6c757d", fg="white", command=self.open_settings_window)
        btn_settings.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=20)
        add_hover_effect(btn_settings, "#6c757d", "white", "#495057", "white", tooltip_text="Settings")

        # Admin button
        btn_admin = tk.Button(self, text="🛠️ Admin", font=("Segoe UI", 12, "bold"),
                              bg="#0d6efd", fg="white", command=self.open_admin_window)
        btn_admin.place(relx=1.0, rely=0.0, anchor="ne", x=-120, y=20)
        add_hover_effect(btn_admin, "#0d6efd", "white", "#198754", "white", tooltip_text="Admin Panel")

        # Notifications
        self.notifications_enabled = True

        # --- Add a menu bar for easy navigation ---
        menubar = tk.Menu(self)
        nav_menu = tk.Menu(menubar, tearoff=0)
        nav_menu.add_command(label="Home", command=lambda: self.tab_control.select(self.home_tab))
        nav_menu.add_command(label="Banking", command=lambda: self.tab_control.select(self.banking_tab))
        nav_menu.add_command(label="Products", command=lambda: self.tab_control.select(self.products_tab))
        nav_menu.add_command(label="Cart", command=lambda: self.tab_control.select(self.cart_tab))
        nav_menu.add_command(label="Orders", command=lambda: self.tab_control.select(self.orders_tab))
        nav_menu.add_command(label="Profile", command=lambda: self.tab_control.select(self.profile_tab))
        nav_menu.add_command(label="Feedback", command=lambda: self.tab_control.select(self.feedback_tab))
        nav_menu.add_command(label="Help", command=lambda: self.tab_control.select(self.help_tab))  # Help tab
        menubar.add_cascade(label="Go to", menu=nav_menu)

        # Add a Help menu for user guidance
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="How to use", command=lambda: messagebox.showinfo(
            "Help",
            "Use the navigation bar or 'Go to' menu to quickly switch between pages.\n"
            "Tabs are also clickable at the top of the window.\n"
            "For further help, contact: 0241cys143@niet.co.in"
        ))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

        # --- Footer ---
        self._footer = tk.Frame(self, bg="#0d6efd", height=30)
        self._footer.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(
            self._footer, text="© 2025 Ashish's online banking and shopping", font=("Segoe UI", 10),
            bg="#0d6efd", fg="white"
        ).pack(pady=4)

        # Build tabs
        self.build_home_tab()
        self.build_banking_tab()
        self.build_products_tab()
        self.build_cart_tab()
        self.build_orders_tab()
        self.build_profile_tab()
        self.build_feedback_tab()
        self.build_help_tab()  # Help tab

    def nav_button(self, parent, text, tab, side=tk.LEFT):
        btn = tk.Button(parent, text=text, font=("Segoe UI", 10, "bold"), bg="#0d6efd", fg="white",
                        command=lambda: self.tab_control.select(tab))
        btn.pack(side=side, padx=3, pady=2)
        add_hover_effect(btn, "#0d6efd", "white", "#198754", "white")
        return btn

    def nav_bar(self, parent):
        bar = tk.Frame(parent, bg="#e9ecef")
        bar.pack(fill=tk.X, pady=(0, 8))
        self.nav_button(bar, "Home", self.home_tab)
        self.nav_button(bar, "Banking", self.banking_tab)
        self.nav_button(bar, "Products", self.products_tab)
        self.nav_button(bar, "Cart", self.cart_tab)
        self.nav_button(bar, "Orders", self.orders_tab)
        self.nav_button(bar, "Profile", self.profile_tab)
        self.nav_button(bar, "Feedback", self.feedback_tab)
        self.nav_button(bar, "Help", self.help_tab)  # Help tab
        return bar

    def setup_navigation_and_menus(self):
        # Add nav_bar to each tab
        self._nav_bars = []
        for tab in [
            self.home_tab, self.banking_tab, self.products_tab, self.cart_tab,
            self.orders_tab, self.profile_tab, self.feedback_tab, self.help_tab
        ]:
            self._nav_bars.append(self.nav_bar(tab))

        # Dark mode toggle
        self.dark_mode = False
        btn_dark = tk.Button(self, text="🌙", font=("Segoe UI", 12), bg="#222", fg="white", command=self.toggle_dark_mode)
        btn_dark.place(relx=1.0, rely=0.0, anchor="ne", x=-250, y=20)
        add_hover_effect(btn_dark, "#222", "white", "#444", "white", tooltip_text="Toggle Dark Mode")

        # Settings button
        btn_settings = tk.Button(self, text="⚙️ Settings", font=("Segoe UI", 12, "bold"),
                                 bg="#6c757d", fg="white", command=self.open_settings_window)
        btn_settings.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=20)
        add_hover_effect(btn_settings, "#6c757d", "white", "#495057", "white", tooltip_text="Settings")

        # Admin button
        btn_admin = tk.Button(self, text="🛠️ Admin", font=("Segoe UI", 12, "bold"),
                              bg="#0d6efd", fg="white", command=self.open_admin_window)
        btn_admin.place(relx=1.0, rely=0.0, anchor="ne", x=-120, y=20)
        add_hover_effect(btn_admin, "#0d6efd", "white", "#198754", "white", tooltip_text="Admin Panel")

        # Notifications
        self.notifications_enabled = True

        # --- Add a menu bar for easy navigation ---
        menubar = tk.Menu(self)
        nav_menu = tk.Menu(menubar, tearoff=0)
        nav_menu.add_command(label="Home", command=lambda: self.tab_control.select(self.home_tab))
        nav_menu.add_command(label="Banking", command=lambda: self.tab_control.select(self.banking_tab))
        nav_menu.add_command(label="Products", command=lambda: self.tab_control.select(self.products_tab))
        nav_menu.add_command(label="Cart", command=lambda: self.tab_control.select(self.cart_tab))
        nav_menu.add_command(label="Orders", command=lambda: self.tab_control.select(self.orders_tab))
        nav_menu.add_command(label="Profile", command=lambda: self.tab_control.select(self.profile_tab))
        nav_menu.add_command(label="Feedback", command=lambda: self.tab_control.select(self.feedback_tab))
        nav_menu.add_command(label="Help", command=lambda: self.tab_control.select(self.help_tab))  # Help tab
        menubar.add_cascade(label="Go to", menu=nav_menu)

        # Add a Help menu for user guidance
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="How to use", command=lambda: messagebox.showinfo(
            "Help",
            "Use the navigation bar or 'Go to' menu to quickly switch between pages.\n"
            "Tabs are also clickable at the top of the window.\n"
            "For further help, contact: 0241cys143@niet.co.in"
        ))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

        # --- Footer ---
        self._footer = tk.Frame(self, bg="#0d6efd", height=30)
        self._footer.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(
            self._footer, text="© 2025 Ashish's online banking and shopping", font=("Segoe UI", 10),
            bg="#0d6efd", fg="white"
        ).pack(pady=4)

        # Build tabs
        self.build_home_tab()
        self.build_banking_tab()
        self.build_products_tab()
        self.build_cart_tab()
        self.build_orders_tab()
        self.build_profile_tab()
        self.build_feedback_tab()
        self.build_help_tab()  # Help tab

    def nav_button(self, parent, text, tab, side=tk.LEFT):
        btn = tk.Button(parent, text=text, font=("Segoe UI", 10, "bold"), bg="#0d6efd", fg="white",
                        command=lambda: self.tab_control.select(tab))
        btn.pack(side=side, padx=3, pady=2)
        add_hover_effect(btn, "#0d6efd", "white", "#198754", "white")
        return btn

    def nav_bar(self, parent):
        bar = tk.Frame(parent, bg="#e9ecef")
        bar.pack(fill=tk.X, pady=(0, 8))
        self.nav_button(bar, "Home", self.home_tab)
        self.nav_button(bar, "Banking", self.banking_tab)
        self.nav_button(bar, "Products", self.products_tab)
        self.nav_button(bar, "Cart", self.cart_tab)
        self.nav_button(bar, "Orders", self.orders_tab)
        self.nav_button(bar, "Profile", self.profile_tab)
        self.nav_button(bar, "Feedback", self.feedback_tab)
        self.nav_button(bar, "Help", self.help_tab)  # Help tab
        return bar

    def setup_navigation_and_menus(self):
        # Add nav_bar to each tab
        self._nav_bars = []
        for tab in [
            self.home_tab, self.banking_tab, self.products_tab, self.cart_tab,
            self.orders_tab, self.profile_tab, self.feedback_tab, self.help_tab
        ]:
            self._nav_bars.append(self.nav_bar(tab))

        # Dark mode toggle
        self.dark_mode = False
        btn_dark = tk.Button(self, text="🌙", font=("Segoe UI", 12), bg="#222", fg="white", command=self.toggle_dark_mode)
        btn_dark.place(relx=1.0, rely=0.0, anchor="ne", x=-250, y=20)
        add_hover_effect(btn_dark, "#222", "white", "#444", "white", tooltip_text="Toggle Dark Mode")

        # Settings button
        btn_settings = tk.Button(self, text="⚙️ Settings", font=("Segoe UI", 12, "bold"),
                                 bg="#6c757d", fg="white", command=self.open_settings_window)
        btn_settings.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=20)
        add_hover_effect(btn_settings, "#6c757d", "white", "#495057", "white", tooltip_text="Settings")

        # Admin button
        btn_admin = tk.Button(self, text="🛠️ Admin", font=("Segoe UI", 12, "bold"),
                              bg="#0d6efd", fg="white", command=self.open_admin_window)
        btn_admin.place(relx=1.0, rely=0.0, anchor="ne", x=-120, y=20)
        add_hover_effect(btn_admin, "#0d6efd", "white", "#198754", "white", tooltip_text="Admin Panel")

        # Notifications
        self.notifications_enabled = True

        # --- Add a menu bar for easy navigation ---
        menubar = tk.Menu(self)
        nav_menu = tk.Menu(menubar, tearoff=0)
        nav_menu.add_command(label="Home", command=lambda: self.tab_control.select(self.home_tab))
        nav_menu.add_command(label="Banking", command=lambda: self.tab_control.select(self.banking_tab))
        nav_menu.add_command(label="Products", command=lambda: self.tab_control.select(self.products_tab))
        nav_menu.add_command(label="Cart", command=lambda: self.tab_control.select(self.cart_tab))
        nav_menu.add_command(label="Orders", command=lambda: self.tab_control.select(self.orders_tab))
        nav_menu.add_command(label="Profile", command=lambda: self.tab_control.select(self.profile_tab))
        nav_menu.add_command(label="Feedback", command=lambda: self.tab_control.select(self.feedback_tab))
        nav_menu.add_command(label="Help", command=lambda: self.tab_control.select(self.help_tab))  # Help tab
        menubar.add_cascade(label="Go to", menu=nav_menu)

        # Add a Help menu for user guidance
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="How to use", command=lambda: messagebox.showinfo(
            "Help",
            "Use the navigation bar or 'Go to' menu to quickly switch between pages.\n"
            "Tabs are also clickable at the top of the window.\n"
            "For further help, contact: 0241cys143@niet.co.in"
        ))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

        # --- Footer ---
        self._footer = tk.Frame(self, bg="#0d6efd", height=30)
        self._footer.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(
            self._footer, text="© 2025 Ashish's online banking and shopping", font=("Segoe UI", 10),
            bg="#0d6efd", fg="white"
        ).pack(pady=4)

        # Build tabs
        self.build_home_tab()
        self.build_banking_tab()
        self.build_products_tab()
        self.build_cart_tab()
        self.build_orders_tab()
        self.build_profile_tab()
        self.build_feedback_tab()
        self.build_help_tab()  # Help tab

    def build_home_tab(self):
        for widget in self.home_tab.winfo_children():
            widget.destroy()

        # Hero Banner
        banner = tk.Frame(self.home_tab, bg="#0d6efd", height=160)
        banner.pack(fill=tk.X, pady=(0, 24))
        tk.Label(
            banner, text="ASHISH's Online Banking & Shopping",
            font=("Segoe UI", 38, "bold"), bg="#0d6efd", fg="white"
        ).pack(pady=(32, 8))
        tk.Label(
            banner, text="Your one-stop solution for banking and shopping needs.",
            font=("Segoe UI", 18, "italic"), bg="#0d6efd", fg="#e9ecef"
        ).pack()

        # Services section (cards)
        cards_frame = tk.Frame(self.home_tab, bg="#f7f9fa")
        cards_frame.pack(pady=40)
        def make_card(parent, emoji, title, desc, color):
            card = tk.Frame(parent, bg="white", relief=tk.RAISED, bd=2, padx=40, pady=30)
            card.pack(side=tk.LEFT, padx=40)
            tk.Label(card, text=emoji, font=("Segoe UI", 96), bg="white").pack()
            tk.Label(card, text=title, font=("Segoe UI", 20, "bold"), bg="white", fg=color).pack(pady=(12, 4))
            tk.Label(card, text=desc, font=("Segoe UI", 14), bg="white", fg="#666").pack()
        make_card(cards_frame, "🏦", "Banking", "Account management, transfers, and more", "#0d6efd")
        make_card(cards_frame, "🛒", "Shopping", "Wide range of products at best prices", "#198754")

        # Refresh button
        btn_refresh = tk.Button(self.home_tab, text="🔄 Refresh", font=("Segoe UI", 16, "bold"),
                                bg="#198754", fg="white", command=self.refresh_all, bd=0, relief=tk.FLAT, cursor="hand2")
        btn_refresh.pack(pady=16)
        add_hover_effect(btn_refresh, "#198754", "white", "#0d6efd", "white", tooltip_text="Refresh this section")

        # Banner
        banner = tk.Frame(self.home_tab, bg="#0d6efd", height=100)
        banner.pack(fill=tk.X)
        tk.Label(
            banner, text="Welcome to ASHISH's online banking and shopping",
            font=("Segoe UI", 34, "bold"), bg="#0d6efd", fg="white"
        ).pack(pady=24)

    def build_banking_tab(self):
        for widget in self.banking_tab.winfo_children():
            widget.destroy()
            
        # Title
        title_frame = tk.Frame(self.banking_tab, bg="#f0f6ff", pady=8)
        title_frame.pack(fill=tk.X)
        tk.Label(title_frame, text="Banking Services", font=("Segoe UI", 22, "bold"),
                bg="#f0f6ff", fg="#0d6efd").pack(pady=10)
        
        # Refresh button
        btn_refresh = tk.Button(title_frame, text="🔄", font=("Segoe UI", 15, "bold"),
                                bg="#198754", fg="white", command=self.refresh_all)
        btn_refresh.pack(side=tk.RIGHT, padx=10)
        add_hover_effect(btn_refresh, "#198754", "white", "#0d6efd", "white", tooltip_text="Refresh")
        
        # Main content
        main_frame = tk.Frame(self.banking_tab, bg="#f7f9fa")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Account operations
        operations_frame = tk.LabelFrame(main_frame, text="Account Operations", 
                                       font=("Segoe UI", 14, "bold"), bg="#f7f9fa", fg="#0d6efd")
        operations_frame.pack(fill=tk.X, pady=10)
        
        btn_frame = tk.Frame(operations_frame, bg="#f7f9fa")
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame, text="Create Account", font=("Segoe UI", 13, "bold"),
            bg="#198754", fg="white", padx=18, pady=8, bd=0, relief=tk.FLAT, cursor="hand2",
            command=self.create_account
        ).pack(side=tk.LEFT, padx=8)
        tk.Button(
            btn_frame, text="View Balance", font=("Segoe UI", 13, "bold"),
            bg="#0d6efd", fg="white", padx=18, pady=8, bd=0, relief=tk.FLAT, cursor="hand2",
            command=self.view_balance
        ).pack(side=tk.LEFT, padx=8)
        tk.Button(
            btn_frame, text="Transfer Money", font=("Segoe UI", 13, "bold"),
            bg="#fd7e14", fg="white", padx=18, pady=8, bd=0, relief=tk.FLAT, cursor="hand2",
            command=self.transfer_money
        ).pack(side=tk.LEFT, padx=8)
        tk.Button(
            btn_frame, text="Transaction History", font=("Segoe UI", 13, "bold"),
            bg="#6f42c1", fg="white", padx=18, pady=8, bd=0, relief=tk.FLAT, cursor="hand2",
            command=self.view_transactions
        ).pack(side=tk.LEFT, padx=8)

        # --- Cash Withdraw and Deposit Section ---
        cash_frame = tk.LabelFrame(main_frame, text="Cash Withdraw & Deposit", font=("Segoe UI", 13, "bold"), bg="#f7f9fa", fg="#198754")
        cash_frame.pack(fill=tk.X, pady=10, padx=5)

        btn_cash = tk.Frame(cash_frame, bg="#f7f9fa")
        btn_cash.pack(pady=8)

        def withdraw_cash():
            win = tk.Toplevel(self)
            win.title("Withdraw Cash")
            win.geometry("350x220")
            win.configure(bg="#f7f9fa")
            tk.Label(win, text="Withdraw Cash", font=("Segoe UI", 15, "bold"), bg="#f7f9fa", fg="#fd7e14").pack(pady=12)
            tk.Label(win, text="Account Number:", font=("Segoe UI", 11), bg="#f7f9fa").pack()
            acc_var = tk.StringVar()
            tk.Entry(win, textvariable=acc_var, font=("Segoe UI", 11)).pack()
            tk.Label(win, text="Amount:", font=("Segoe UI", 11), bg="#f7f9fa").pack(pady=(10,0))
            amt_var = tk.StringVar()
            tk.Entry(win, textvariable=amt_var, font=("Segoe UI", 11)).pack()
            def do_withdraw():
                acc = acc_var.get()
                try:
                    amt = float(amt_var.get())
                except:
                    messagebox.showerror("Error", "Invalid amount!", parent=win)
                    return
                if acc not in self.accounts:
                    messagebox.showerror("Error", "Account not found!", parent=win)
                    return
                if amt <= 0:
                    messagebox.showerror("Error", "Amount must be positive!", parent=win)
                    return
                if self.accounts[acc]["balance"] < amt:
                    messagebox.showerror("Error", "Insufficient balance!", parent=win)
                    return
                self.accounts[acc]["balance"] -= amt
                # Record transaction
                transaction = {
                    "date": str(datetime.now()),
                    "from_account": acc,
                    "to_account": "Cash Withdraw",
                    "amount": amt,
                    "type": "withdraw"
                }
                self.transactions.append(transaction)
                save_json(FILES['ACCOUNTS'], self.accounts)
                save_json(FILES['TRANSACTIONS'], self.transactions)
                messagebox.showinfo("Success", f"₹{amt:.2f} withdrawn from account {acc}.", parent=win)
                win.destroy()
            tk.Button(win, text="Withdraw", font=("Segoe UI", 12, "bold"), bg="#fd7e14", fg="white", command=do_withdraw).pack(pady=16)

        def deposit_cash():
            win = tk.Toplevel(self)
            win.title("Deposit Cash")
            win.geometry("350x220")
            win.configure(bg="#f7f9fa")
            tk.Label(win, text="Deposit Cash", font=("Segoe UI", 15, "bold"), bg="#f7f9fa", fg="#198754").pack(pady=12)
            tk.Label(win, text="Account Number:", font=("Segoe UI", 11), bg="#f7f9fa").pack()
            acc_var = tk.StringVar()
            tk.Entry(win, textvariable=acc_var, font=("Segoe UI", 11)).pack()
            tk.Label(win, text="Amount:", font=("Segoe UI", 11), bg="#f7f9fa").pack(pady=(10,0))
            amt_var = tk.StringVar()
            tk.Entry(win, textvariable=amt_var, font=("Segoe UI", 11)).pack()
            def do_deposit():
                acc = acc_var.get()
                try:
                    amt = float(amt_var.get())
                except:
                    messagebox.showerror("Error", "Invalid amount!", parent=win)
                    return
                if acc not in self.accounts:
                    messagebox.showerror("Error", "Account not found!", parent=win)
                    return
                if amt <= 0:
                    messagebox.showerror("Error", "Amount must be positive!", parent=win)
                    return
                self.accounts[acc]["balance"] += amt
                # Record transaction
                transaction = {
                    "date": str(datetime.now()),
                    "from_account": "Cash Deposit",
                    "to_account": acc,
                    "amount": amt,
                    "type": "deposit"
                }
                self.transactions.append(transaction)
                save_json(FILES['ACCOUNTS'], self.accounts)
                save_json(FILES['TRANSACTIONS'], self.transactions)
                messagebox.showinfo("Success", f"₹{amt:.2f} deposited to account {acc}.", parent=win)
                win.destroy()
            tk.Button(win, text="Deposit", font=("Segoe UI", 12, "bold"), bg="#198754", fg="white", command=do_deposit).pack(pady=16)

        tk.Button(btn_cash, text="Withdraw Cash", font=("Segoe UI", 11, "bold"), bg="#fd7e14", fg="white", command=withdraw_cash).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_cash, text="Deposit Cash", font=("Segoe UI", 11, "bold"), bg="#198754", fg="white", command=deposit_cash).pack(side=tk.LEFT, padx=10)

        btn_refresh = tk.Button(self.banking_tab, text="🔄 Refresh", font=("Segoe UI", 11, "bold"),
                               bg="#198754", fg="white", command=self.refresh_all)
        btn_refresh.pack(pady=10)
        add_hover_effect(btn_refresh, "#198754", "white", "#0d6efd", "white", tooltip_text="Refresh this section")

    def build_products_tab(self):
        for widget in self.products_tab.winfo_children():
            widget.destroy()
            
        # Title
        title_frame = tk.Frame(self.products_tab, bg="#f0f6ff", pady=8)
        title_frame.pack(fill=tk.X)
        tk.Label(title_frame, text="Product Catalog", font=("Segoe UI", 22, "bold"),
                bg="#f0f6ff", fg="#0d6efd").pack(pady=10)
        
        # Refresh button
        btn_refresh = tk.Button(title_frame, text="🔄", font=("Segoe UI", 13, "bold"),
                                bg="#198754", fg="white", command=self.refresh_all)
        btn_refresh.pack(side=tk.RIGHT, padx=10)
        add_hover_effect(btn_refresh, "#198754", "white", "#0d6efd", "white", tooltip_text="Refresh this section")
        
        # Search and filter
        filter_frame = tk.Frame(self.products_tab, bg="#f9f9fa")
        filter_frame.pack(fill=tk.X, pady=5, padx=15)
        
        search_frame = tk.Frame(filter_frame, bg="#f9f9fa")
        search_frame.pack(side=tk.LEFT)
        tk.Label(search_frame, text="Search:", font=("Segoe UI", 12), bg="#f9f9fa").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=search_var, font=("Segoe UI", 12), width=20).pack(side=tk.LEFT, padx=5)
        
        # Products display
        canvas = tk.Canvas(self.products_tab, bg="#f7f9fa")
        scrollbar = ttk.Scrollbar(self.products_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f7f9fa")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pagination
        self.product_page = getattr(self, "product_page", 0)
        products_per_page = 12
        start = self.product_page * products_per_page
        end = start + products_per_page
        
        # Display products
        row, col = 0, 0
        for product in self.products[start:end]:  # Paginated products
            product_frame = tk.Frame(scrollable_frame, bg="white", relief=tk.RAISED, bd=1)
            product_frame.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
            
            tk.Label(product_frame, text=product.get('name', 'Unknown'), 
                    font=("Segoe UI", 12, "bold"), bg="white").pack(pady=5)
            tk.Label(product_frame, text=f"₹{product.get('price', 0)}", 
                    font=("Segoe UI", 11), bg="white", fg="#198754").pack()
            btn = tk.Button(product_frame, text="Add to Cart", bg="#0d6efd", fg="white",
                     command=lambda p=product: self.add_to_cart(p['product_id']))
            btn.pack(pady=5)
            add_hover_effect(btn, "#0d6efd", "white", "#198754", "white")
            
            # Product image - support multiple photos, use first available
            photos = product.get('photos', [])
            # Handle backward compatibility - if 'photo' exists, use it
            if not photos and product.get('photo'):
                photos = [product.get('photo')]
            
            image_displayed = False
            for img_path in photos:
                if img_path and os.path.exists(img_path):
                    try:
                        img = Image.open(img_path).resize((64, 64))
                        photo = ImageTk.PhotoImage(img)
                        img_label = tk.Label(product_frame, image=photo, bg="white")
                        img_label.image = photo
                        img_label.pack()
                        image_displayed = True
                        break
                    except Exception:
                        continue
            
            if not image_displayed:
                tk.Label(product_frame, text="🖼️", font=("Segoe UI", 24), bg="white").pack()
            
            col += 1
            if col > 3:
                col = 0
                row += 1
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Pagination controls
        def next_page():
            self.product_page += 1
            self.build_products_tab()
        def prev_page():
            self.product_page = max(0, self.product_page - 1)
            self.build_products_tab()
        tk.Button(self.products_tab, text="Prev", command=prev_page).pack(side=tk.LEFT)
        tk.Button(self.products_tab, text="Next", command=next_page).pack(side=tk.RIGHT)
        
        btn_refresh = tk.Button(self.products_tab, text="🔄 Refresh", font=("Segoe UI", 11, "bold"),
                               bg="#198754", fg="white", command=self.build_products_tab)
        btn_refresh.pack(pady=10)
        add_hover_effect(btn_refresh, "#198754", "white", "#0d6efd", "white", tooltip_text="Refresh this section")
        
        # Add hover to product "Add to Cart" buttons:
        for child in self.products_tab.winfo_children():
            if isinstance(child, tk.Button):
                add_hover_effect(child, "#2a3340", "white", "#198754", "white")

    def build_cart_tab(self):
        for widget in self.cart_tab.winfo_children():
            widget.destroy()
            
        # Title
        tk.Label(self.cart_tab, text="Shopping Cart", font=("Segoe UI", 22, "bold"),
                bg="#f7f9fa", fg="#0d6efd").pack(pady=10)
        
        # Cart content
        cart_frame = tk.Frame(self.cart_tab, bg="#f7f9fa")
        cart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        if not self.cart.items:
            tk.Label(cart_frame, text="Your cart is empty", font=("Segoe UI", 16),
                    bg="#f7f9fa", fg="#666").pack(pady=50)
        else:
            details = self.cart.get_details(self.products)
            
            # Items list
            for item in details['items']:
                item_frame = tk.Frame(cart_frame, bg="white", relief=tk.RAISED, bd=1)
                item_frame.pack(fill=tk.X, pady=5)
                
                # Product image on the left
                product = item['product']
                photos = product.get('photos', [])
                # Handle backward compatibility
                if not photos and product.get('photo'):
                    photos = [product.get('photo')]
                
                image_displayed = False
                for img_path in photos:
                    if img_path and os.path.exists(img_path):
                        try:
                            img = Image.open(img_path).resize((48, 48))
                            photo = ImageTk.PhotoImage(img)
                            img_label = tk.Label(item_frame, image=photo, bg="white")
                            img_label.image = photo
                            img_label.pack(side=tk.LEFT, padx=10)
                            image_displayed = True
                            break
                        except Exception:
                            continue
                
                if not image_displayed:
                    tk.Label(item_frame, text="🖼️", font=("Segoe UI", 20), bg="white").pack(side=tk.LEFT, padx=10)
                
                # Product details
                info_frame = tk.Frame(item_frame, bg="white")
                info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
                
                tk.Label(info_frame, text=item['product']['name'], 
                        font=("Segoe UI", 12, "bold"), bg="white").pack(anchor="w")
                tk.Label(info_frame, text=f"Qty: {item['quantity']}", 
                        font=("Segoe UI", 11), bg="white").pack(anchor="w")
                
                # Show per-item discount, GST, cashback
                details_text = []
                if item['product'].get('discount_percent', 0) > 0:
                    details_text.append(f"Discount: {item['product'].get('discount_percent', 0)}%")
                details_text.append(f"GST: {item.get('gst_rate', 0):.1f}%")
                if item.get('cashback_amount', 0) > 0:
                    details_text.append(f"Cashback: ₹{item['cashback_amount']:.2f}")
                
                # Show price breakdown
                base_price_text = f"Base: ₹{item['discounted_base_price']:.2f}"
                gst_text = f"GST: ₹{item['line_gst_amount']:.2f}"
                details_text.extend([base_price_text, gst_text])
                
                if details_text:
                    tk.Label(info_frame, text=" | ".join(details_text), 
                            font=("Segoe UI", 10), bg="white", fg="#666").pack(anchor="w")
                
                # Price and buttons on the right
                right_frame = tk.Frame(item_frame, bg="white")
                right_frame.pack(side=tk.RIGHT, padx=10)
                
                tk.Label(right_frame, text=f"₹{item['line_total']:.2f}", 
                        font=("Segoe UI", 11, "bold"), bg="white", fg="#198754").pack()
            
                # Quantity and remove buttons
                def update_qty(pid, delta):
                    self.cart.items[pid] = max(1, self.cart.items[pid] + delta)
                    self.build_cart_tab()
                def remove_item(pid):
                    self.cart.remove(pid)
                    self.build_cart_tab()

                btn_frame = tk.Frame(right_frame, bg="white")
                btn_frame.pack(pady=(5, 0))
                
                tk.Button(btn_frame, text="-", command=lambda pid=item['product']['product_id']: update_qty(pid, -1),
                          bg="#fd7e14", fg="white", width=2).pack(side=tk.LEFT, padx=1)
                tk.Button(btn_frame, text="+", command=lambda pid=item['product']['product_id']: update_qty(pid, 1),
                          bg="#198754", fg="white", width=2).pack(side=tk.LEFT, padx=1)
                tk.Button(btn_frame, text="Remove", command=lambda pid=item['product']['product_id']: remove_item(pid),
                          bg="#dc3545", fg="white", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=1)
                
                # Add hover effects
                add_hover_effect(btn_frame.winfo_children()[-3], "#fd7e14", "white", "#c82333", "white")  # "-" button
                add_hover_effect(btn_frame.winfo_children()[-2], "#198754", "white", "#117a8b", "white")  # "+" button
                add_hover_effect(btn_frame.winfo_children()[-1], "#dc3545", "white", "#c82333", "white")  # "Remove" button
            
            # --- Bill Summary Section ---
            summary_frame = tk.Frame(cart_frame, bg="white", relief=tk.RAISED, bd=2)
            summary_frame.pack(fill=tk.X, pady=10)
            tk.Label(summary_frame, text="Bill Summary", font=("Segoe UI", 14, "bold"), bg="white", fg="#0d6efd").pack(anchor="w", padx=10, pady=(10, 2))
            
            # Subtotal
            tk.Label(summary_frame, text=f"Subtotal (before GST): ₹{details['subtotal_pre_gst']:.2f}", font=("Segoe UI", 11), bg="white").pack(anchor="w", padx=20)
            
            # GST Breakdown
            if details['total_gst'] > 0:
                gst_frame = tk.Frame(summary_frame, bg="white")
                gst_frame.pack(fill=tk.X, padx=20, pady=2)
                
                tk.Label(gst_frame, text="GST Breakdown:", font=("Segoe UI", 11, "bold"), bg="white", fg="#0d6efd").pack(anchor="w")
                
                # Show CGST, SGST, IGST breakdown
                if details['total_cgst'] > 0:
                    tk.Label(gst_frame, text=f"  CGST: ₹{details['total_cgst']:.2f}", font=("Segoe UI", 10), bg="white", fg="#666").pack(anchor="w", padx=20)
                if details['total_sgst'] > 0:
                    tk.Label(gst_frame, text=f"  SGST: ₹{details['total_sgst']:.2f}", font=("Segoe UI", 10), bg="white", fg="#666").pack(anchor="w", padx=20)
                if details['total_igst'] > 0:
                    tk.Label(gst_frame, text=f"  IGST: ₹{details['total_igst']:.2f}", font=("Segoe UI", 10), bg="white", fg="#666").pack(anchor="w", padx=20)
                
                tk.Label(gst_frame, text=f"Total GST: ₹{details['total_gst']:.2f}", font=("Segoe UI", 11, "bold"), bg="white", fg="#0d6efd").pack(anchor="w")
            
            # Delivery charges
            if details['delivery_charge'] > 0:
                delivery_frame = tk.Frame(summary_frame, bg="white")
                delivery_frame.pack(fill=tk.X, padx=20, pady=2)
                tk.Label(delivery_frame, text=f"Delivery Charge: ₹{details['delivery_charge']:.2f}", font=("Segoe UI", 11), bg="white").pack(anchor="w")
                if details.get('delivery_gst', 0) > 0:
                    tk.Label(delivery_frame, text=f"Delivery GST ({details.get('delivery_gst_rate', 18):.0f}%): ₹{details['delivery_gst']:.2f}", font=("Segoe UI", 10), bg="white", fg="#666").pack(anchor="w", padx=20)
            
            # Cashback
            if details['total_cashback'] > 0:
                tk.Label(summary_frame, text=f"Total Cashback: ₹{details['total_cashback']:.2f}", font=("Segoe UI", 11, "bold"), bg="white", fg="#fd7e14").pack(anchor="w", padx=20)
            
            # Grand total
            tk.Label(summary_frame, text=f"Grand Total: ₹{details['grand_total']:.2f}", font=("Segoe UI", 13, "bold"), bg="white", fg="#198754").pack(anchor="w", padx=20, pady=(5, 10))

            # --- GST Invoice Section ---
            invoice_frame = tk.Frame(cart_frame, bg="white", relief=tk.RIDGE, bd=2)
            invoice_frame.pack(fill=tk.X, pady=10)
            tk.Label(invoice_frame, text="GST Invoice (Eligible for Input Tax Credit up to 28%)", font=("Segoe UI", 13, "bold"), bg="white", fg="#6610f2").pack(anchor="w", padx=10, pady=(10, 2))
            tk.Label(invoice_frame, text="This invoice can be used to claim GST input credit as per government rules.", font=("Segoe UI", 10), bg="white", fg="#444").pack(anchor="w", padx=20)
            tk.Label(invoice_frame, text=f"GST Amount (claimable): ₹{details['total_gst']:.2f} (up to 28%)", font=("Segoe UI", 11, "bold"), bg="white", fg="#fd7e14").pack(anchor="w", padx=20, pady=(0, 10))
            tk.Label(invoice_frame, text="For official GST invoice, please contact: 0241cys143@niet.co.in", font=("Segoe UI", 10, "italic"), bg="white", fg="#666").pack(anchor="w", padx=20, pady=(0, 10))

            # --- GST Number Button ---
            def open_gst_details():
                gst_win = tk.Toplevel(self)
                gst_win.title("Enter GST Details")
                gst_win.geometry("420x400")
                gst_win.configure(bg="#f7f9fa")
                tk.Label(gst_win, text="Enter GST Details for Invoice", font=("Segoe UI", 15, "bold"), bg="#f7f9fa", fg="#0d6efd").pack(pady=12)

                # GST Number
                tk.Label(gst_win, text="GST Number:", font=("Segoe UI", 12), bg="#f7f9fa").pack(pady=(10, 2))
                gst_var = tk.StringVar()
                gst_entry = tk.Entry(gst_win, textvariable=gst_var, font=("Segoe UI", 12), width=32)
                gst_entry.pack(pady=2)

                # Business Name
                tk.Label(gst_win, text="Business Name:", font=("Segoe UI", 12), bg="#f7f9fa").pack(pady=(10, 2))
                name_var = tk.StringVar()
                name_entry = tk.Entry(gst_win, textvariable=name_var, font=("Segoe UI", 12), width=32)
                name_entry.pack(pady=2)
                def save_gst():
                    gst_no = gst_var.get().strip()
                    biz_name = name_var.get().strip()
                    if not gst_no or not biz_name:
                        messagebox.showwarning("Missing Info", "Please fill all GST details.", parent=gst_win)
                        return
                    messagebox.showinfo("GST Details Saved", f"GST No: {gst_no}\nBusiness: {biz_name}\nDetails will be used for your GST invoice.", parent=gst_win)
                    gst_win.destroy()

                tk.Button(gst_win, text="Save GST Details", font=("Segoe UI", 12, "bold"), bg="#198754", fg="white", command=save_gst).pack(pady=18)
                add_hover_effect(gst_win.winfo_children()[-1], "#198754", "white", "#0d6efd", "white")
            tk.Button(invoice_frame, text="Add GST No. for GST Invoice", font=("Segoe UI", 11, "bold"), bg="#0d6efd", fg="white", command=open_gst_details).pack(pady=8)
            add_hover_effect(invoice_frame.winfo_children()[-1], "#0d6efd", "white", "#198754", "white")

            # Checkout button
            tk.Button(cart_frame, text="Checkout", font=("Segoe UI", 14, "bold"),
                     bg="#198754", fg="white", padx=30, pady=10, command=self.checkout).pack(pady=10)
        
        btn_refresh = tk.Button(self.cart_tab, text="🔄 Refresh", font=("Segoe UI", 11, "bold"),
                               bg="#198754", fg="white", command=self.refresh_all)
        btn_refresh.pack(pady=10)
        add_hover_effect(btn_refresh, "#198754", "white", "#0d6efd", "white", tooltip_text="Refresh this section")
        
        # Add hover to checkout button:
        for child in self.cart_tab.winfo_children():
            if isinstance(child, tk.Button):
                add_hover_effect(child, "#198754", "white", "#0d6efd", "white")

    def build_orders_tab(self):
        for widget in self.orders_tab.winfo_children():
            widget.destroy()
            
        btn_refresh = tk.Button(self.orders_tab, text="🔄 Refresh", font=("Segoe UI", 11, "bold"),
                               bg="#198754", fg="white", command=self.refresh_all)
        btn_refresh.pack(pady=10)
        add_hover_effect(btn_refresh, "#198754", "white", "#0d6efd", "white", tooltip_text="Refresh this section")
        
        tk.Label(self.orders_tab, text="Order History", font=("Segoe UI", 22, "bold"),
                bg="#f7f9fa", fg="#0d6efd").pack(pady=20)
        tk.Label(self.orders_tab, text="No orders yet", font=("Segoe UI", 14),
                bg="#f7f9fa", fg="#666").pack(pady=50)

        orders = load_json(FILES['HISTORY'], [])
        if not orders:
            tk.Label(self.orders_tab, text="No orders yet", font=("Segoe UI", 14),
                     bg="#f7f9fa", fg="#666").pack(pady=50)
        else:
            columns = ("Order ID", "Date", "Total", "Status")
            tree = ttk.Treeview(self.orders_tab, columns=columns, show="headings", height=12)
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=120)
            for idx, order in enumerate(reversed(orders)):
                tree.insert("", tk.END, values=(
                    f"ORD{idx+1:04d}",
                    order.get("timestamp", ""),
                    f"₹{order.get('grand_total', 0):.2f}",
                    order.get("status", "Pending")
                ))
            tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    def build_profile_tab(self):
        for widget in self.profile_tab.winfo_children():
            widget.destroy()
            
        btn_refresh = tk.Button(self.profile_tab, text="🔄 Refresh", font=("Segoe UI", 11, "bold"),
                               bg="#198754", fg="white", command=self.refresh_all)
        btn_refresh.pack(pady=10)
        add_hover_effect(btn_refresh, "#198754", "white", "#0d6efd", "white", tooltip_text="Refresh this section")
        
        tk.Label(self.profile_tab, text="User Profile", font=("Segoe UI", 22, "bold"),
                bg="#f7f9fa", fg="#0d6efd").pack(pady=20)
        
        # Create a notebook widget for profile tabs
        profile_notebook = ttk.Notebook(self.profile_tab)
        profile_notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Tab 1: User Info
        user_info_tab = tk.Frame(profile_notebook, bg="white")
        profile_notebook.add(user_info_tab, text="👤 User Info")
        
        # Tab 2: Login/Register
        login_tab = tk.Frame(profile_notebook, bg="white")
        profile_notebook.add(login_tab, text="🔐 Login")
        
        # Build User Info Tab
        self.build_user_info_tab(user_info_tab)
        
        # Build Login Tab
        self.build_login_tab(login_tab)
    
    def build_user_info_tab(self, parent):
        # User avatar and info
        user_frame = tk.Frame(parent, bg="white", relief=tk.RAISED, bd=2)
        user_frame.pack(padx=20, pady=20, fill=tk.X)
        
        tk.Label(user_frame, text="👤", font=("Segoe UI", 50), bg="white").pack(pady=10)
        
        if self.is_logged_in and self.current_user:
            # Show logged-in user info
            tk.Label(user_frame, text=self.current_user['name'], font=("Segoe UI", 18, "bold"), bg="white").pack()
            tk.Label(user_frame, text=self.current_user['email'], font=("Segoe UI", 12), bg="white", fg="#666").pack(pady=5)
            tk.Label(user_frame, text=f"Member since: {self.current_user.get('join_date', 'N/A')}", 
                    font=("Segoe UI", 10), bg="white", fg="#888").pack(pady=2)
            
            # Logout button
            logout_btn = tk.Button(user_frame, text="🚪 Logout", font=("Segoe UI", 12, "bold"),
                                 bg="#dc3545", fg="white", command=self.logout_user)
            logout_btn.pack(pady=10)
            add_hover_effect(logout_btn, "#dc3545", "white", "#c82333", "white")
            
        else:
            # Show guest user info
            tk.Label(user_frame, text="Guest User", font=("Segoe UI", 18, "bold"), bg="white").pack()
            tk.Label(user_frame, text="guest@example.com", font=("Segoe UI", 12), bg="white", fg="#666").pack(pady=5)
            tk.Label(user_frame, text="Please login to access personalized features", 
                    font=("Segoe UI", 10), bg="white", fg="#888").pack(pady=2)
        
        # Account stats (if logged in)
        if self.is_logged_in and self.current_user:
            stats_frame = tk.Frame(parent, bg="white", relief=tk.RAISED, bd=2)
            stats_frame.pack(padx=20, pady=10, fill=tk.X)
            
            tk.Label(stats_frame, text="Account Statistics", font=("Segoe UI", 16, "bold"), 
                    bg="white", fg="#0d6efd").pack(pady=10)
            
            # Show user's banking accounts
            user_accounts = [acc for acc_num, acc in self.accounts.items() 
                           if acc.get('owner_email') == self.current_user['email']]
            
            tk.Label(stats_frame, text=f"Banking Accounts: {len(user_accounts)}", 
                    font=("Segoe UI", 12), bg="white").pack(pady=2)
            
            total_balance = sum(acc.get('balance', 0) for acc in user_accounts)
            tk.Label(stats_frame, text=f"Total Balance: ₹{total_balance:.2f}", 
                    font=("Segoe UI", 12, "bold"), bg="white", fg="#28a745").pack(pady=2)
    
    def build_login_tab(self, parent):
        # Create a notebook for Login and Register
        auth_notebook = ttk.Notebook(parent)
        auth_notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Login frame
        login_frame = tk.Frame(auth_notebook, bg="white")
        auth_notebook.add(login_frame, text="Login")
        
        # Register frame
        register_frame = tk.Frame(auth_notebook, bg="white")
        auth_notebook.add(register_frame, text="Register")
        
        # Build login form
        self.build_login_form(login_frame)
        
        # Build register form
        self.build_register_form(register_frame)
    
    def build_login_form(self, parent):
        tk.Label(parent, text="� User Login", font=("Segoe UI", 20, "bold"), 
                bg="white", fg="#0d6efd").pack(pady=20)
        
        # Login form
        form_frame = tk.Frame(parent, bg="white")
        form_frame.pack(pady=20)
        
        # Email field
        tk.Label(form_frame, text="Email:", font=("Segoe UI", 12, "bold"), bg="white").grid(row=0, column=0, sticky="w", pady=5)
        self.login_email_var = tk.StringVar()
        email_entry = tk.Entry(form_frame, textvariable=self.login_email_var, font=("Segoe UI", 12), width=25)
        email_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Password field
        tk.Label(form_frame, text="Password:", font=("Segoe UI", 12, "bold"), bg="white").grid(row=1, column=0, sticky="w", pady=5)
        self.login_password_var = tk.StringVar()
        password_entry = tk.Entry(form_frame, textvariable=self.login_password_var, font=("Segoe UI", 12), width=25, show="*")
        password_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # Login button
        login_btn = tk.Button(form_frame, text="🔑 Login", font=("Segoe UI", 12, "bold"),
                             bg="#28a745", fg="white", command=self.login_user_form, padx=20, pady=8)
        login_btn.grid(row=2, column=0, columnspan=2, pady=20)
        add_hover_effect(login_btn, "#28a745", "white", "#218838", "white")
        
        # Demo credentials info
        demo_frame = tk.Frame(parent, bg="#f8f9fa", relief=tk.RAISED, bd=1)
        demo_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(demo_frame, text="Demo Credentials", font=("Segoe UI", 12, "bold"), 
                bg="#f8f9fa", fg="#495057").pack(pady=5)
        tk.Label(demo_frame, text="Email: demo@example.com", font=("Segoe UI", 10), 
                bg="#f8f9fa", fg="#6c757d").pack()
        tk.Label(demo_frame, text="Password: demo123", font=("Segoe UI", 10), 
                bg="#f8f9fa", fg="#6c757d").pack(pady=(0, 5))
    
    def build_register_form(self, parent):
        tk.Label(parent, text="📝 Create Account", font=("Segoe UI", 20, "bold"), 
                bg="white", fg="#0d6efd").pack(pady=20)
        
        # Register form
        form_frame = tk.Frame(parent, bg="white")
        form_frame.pack(pady=20)
        
        # Name field
        tk.Label(form_frame, text="Full Name:", font=("Segoe UI", 12, "bold"), bg="white").grid(row=0, column=0, sticky="w", pady=5)
        self.register_name_var = tk.StringVar()
        name_entry = tk.Entry(form_frame, textvariable=self.register_name_var, font=("Segoe UI", 12), width=25)
        name_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Email field
        tk.Label(form_frame, text="Email:", font=("Segoe UI", 12, "bold"), bg="white").grid(row=1, column=0, sticky="w", pady=5)
        self.register_email_var = tk.StringVar()
        email_entry = tk.Entry(form_frame, textvariable=self.register_email_var, font=("Segoe UI", 12), width=25)
        email_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # Password field
        tk.Label(form_frame, text="Password:", font=("Segoe UI", 12, "bold"), bg="white").grid(row=2, column=0, sticky="w", pady=5)
        self.register_password_var = tk.StringVar()
        password_entry = tk.Entry(form_frame, textvariable=self.register_password_var, font=("Segoe UI", 12), width=25, show="*")
        password_entry.grid(row=2, column=1, padx=10, pady=5)
        
        # Confirm Password field
        tk.Label(form_frame, text="Confirm Password:", font=("Segoe UI", 12, "bold"), bg="white").grid(row=3, column=0, sticky="w", pady=5)
        self.register_confirm_var = tk.StringVar()
        confirm_entry = tk.Entry(form_frame, textvariable=self.register_confirm_var, font=("Segoe UI", 12), width=25, show="*")
        confirm_entry.grid(row=3, column=1, padx=10, pady=5)
        
        # Register button
        register_btn = tk.Button(form_frame, text="📝 Create Account", font=("Segoe UI", 12, "bold"),
                               bg="#007bff", fg="white", command=self.register_user_form, padx=20, pady=8)
        register_btn.grid(row=4, column=0, columnspan=2, pady=20)
        add_hover_effect(register_btn, "#007bff", "white", "#0056b3", "white")
    
    def login_user_form(self):
        """Handle login form submission"""
        email = self.login_email_var.get().strip()
        password = self.login_password_var.get().strip()
        
        if not email or not password:
            self.notification_manager.show_notification(
                "Please fill in all fields!", 
                "error"
            )
            return
        
        # Use the secure login method
        if self.login_user(email, password):
            # Clear form on successful login
            self.login_email_var.set("")
            self.login_password_var.set("")
            # Refresh the profile tab
            self.build_profile_tab()
    
    def register_user_form(self):
        """Handle registration form submission"""
        name = self.register_name_var.get().strip()
        email = self.register_email_var.get().strip()
        password = self.register_password_var.get().strip()
        confirm = self.register_confirm_var.get().strip()
        
        if not all([name, email, password, confirm]):
            self.notification_manager.show_notification(
                "Please fill in all fields!", 
                "error"
            )
            return
        
        if password != confirm:
            self.notification_manager.show_notification(
                "Passwords do not match!", 
                "error"
            )
            return
        
        # Use the secure registration method
        if self.register_user(email, password, name):
            # Clear form on successful registration
            self.register_name_var.set("")
            self.register_email_var.set("")
            self.register_password_var.set("")
            self.register_confirm_var.set("")
            return
        
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match!")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long!")
            return
        
        if email in self.users:
            messagebox.showerror("Error", "Email already registered!")
            return
        
        # Register new user
        self.users[email] = {
            'name': name,
            'email': email,
            'password': password,
            'join_date': str(date.today())
        }
        
        # Save users to file
        save_json(FILES['USERS'], self.users)
        
        messagebox.showinfo("Success", "Account created successfully! You can now login.")
        
        # Clear form fields
        self.register_name_var.set("")
        self.register_email_var.set("")
        self.register_password_var.set("")
        self.register_confirm_var.set("")
    
    def logout_user(self):
        self.current_user = None
        self.is_logged_in = False
        messagebox.showinfo("Logged Out", "You have been logged out successfully!")
        self.build_profile_tab()  # Refresh the profile tab

    def build_feedback_tab(self):
        for widget in self.feedback_tab.winfo_children():
            widget.destroy()
            
        btn_refresh = tk.Button(self.feedback_tab, text="🔄 Refresh", font=("Segoe UI", 11, "bold"),
                               bg="#198754", fg="white", command=self.refresh_all)
        btn_refresh.pack(pady=10)
        add_hover_effect(btn_refresh, "#198754", "white", "#0d6efd", "white", tooltip_text="Refresh this section")
        
        tk.Label(self.feedback_tab, text="Feedback", font=("Segoe UI", 22, "bold"),
                bg="#f7f9fa", fg="#0d6efd").pack(pady=20)
        
        feedback_frame = tk.Frame(self.feedback_tab, bg="#f9f9fa")
        feedback_frame.pack(padx=50, pady=20, fill=tk.BOTH, expand=True)
        
        tk.Label(feedback_frame, text="Your feedback is important to us:", 
                font=("Segoe UI", 14), bg="#f9f9fa").pack(pady=10)
        
        feedback_text = tk.Text(feedback_frame, height=10, font=("Segoe UI", 12))
        feedback_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        tk.Button(feedback_frame, text="Submit Feedback", font=("Segoe UI", 12, "bold"),
                 bg="#198754", fg="white", padx=20, pady=5,
                 command=lambda: self.submit_feedback(feedback_text.get("1.0", tk.END))).pack(pady=10)
        
        # Add hover to submit feedback button:
        for child in self.feedback_tab.winfo_children():
            if isinstance(child, tk.Button):
                add_hover_effect(child, "#198754", "white", "#0d6efd", "white")
        
        with open(FILES['FEEDBACK'], encoding="utf-8") as f:
            feedbacks = f.read().split("---\n")
        if feedbacks:
            tk.Label(feedback_frame, text="Previous Feedbacks:", font=("Segoe UI", 12, "bold"), bg="#f9f9fa").pack(pady=5)
            fb_box = tk.Text(feedback_frame, height=8, font=("Segoe UI", 10), state="normal")
            fb_box.pack(fill=tk.BOTH, expand=True)
            for fb in feedbacks:
                if fb.strip():
                    fb_box.insert(tk.END, fb.strip() + "\n\n")
            fb_box.config(state="disabled")

    def build_help_tab(self):
        for widget in self.help_tab.winfo_children():
            widget.destroy()
        
        tk.Label(self.help_tab, text="Help & AI Chat Assistant", font=("Segoe UI", 22, "bold"), bg="#f7f9fa", fg="#0d6efd").pack(pady=20)
        
        # Instructions section
        instructions = (
            "Welcome to the Help Center!\n\n"
            "- Use the navigation bar or menu to switch between pages.\n"
            "- For banking, go to the Banking tab.\n"
            "- For shopping, browse Products and add to Cart.\n"
            "- For admin features, use the Admin button.\n"
            "- For feedback, use the Feedback tab.\n\n"
            "If you need more help, ask the AI assistant below."
        )
        tk.Label(self.help_tab, text=instructions, font=("Segoe UI", 13), bg="#f7f9fa", fg="#222").pack(pady=8)
        
        # --- AI Chat Section ---
        chat_frame = tk.LabelFrame(self.help_tab, text="AI Chat Assistant", font=("Segoe UI", 13, "bold"), bg="#f9f9fa", fg="#198754")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=16)
        
        chat_log = tk.Text(chat_frame, state="disabled", wrap="word", font=("Segoe UI", 11), bg="white", height=12)
        chat_log.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        entry_frame = tk.Frame(chat_frame, bg="#f9f9fa")
        entry_frame.pack(fill=tk.X, padx=8, pady=(0,8))
        user_entry = tk.Entry(entry_frame, font=("Segoe UI", 12))
        user_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        # Session memory for multi-turn conversation
        self._ai_chat_history = []
        
        def ai_response(user_msg):
            self._ai_chat_history.append(("user", user_msg))
            user_msg_l = user_msg.lower()
            if any(x in user_msg_l for x in ["feature", "what can", "do", "functions"]):
                return ("I can help you with: \n- Account management (create, view, transfer)\n- Shopping (browse, add to cart, checkout)\n- Order history\n- Settings and dark mode\n- Admin panel\n- Feedback\nJust ask about any feature!")
            elif any(x in user_msg_l for x in ["navigation", "where", "find", "tab", "page"]):
                return ("Use the navigation bar at the top or the menu to switch between Home, Banking, Products, Cart, Orders, Profile, Feedback, and Help tabs.")
            elif any(x in user_msg_l for x in ["trouble", "error", "problem", "not working"]):
                return ("If you encounter issues, try refreshing the section or restarting the app. For persistent problems, contact support at 0241cys143@niet.co.in.")
            elif "contact" in user_msg_l or "support" in user_msg_l:
                return ("You can contact support at 0241cys143@niet.co.in or use the Feedback tab to submit your issue.")
            elif "clear chat" in user_msg_l:
                self._ai_chat_history.clear()
                return "Chat history cleared. How can I help you now?"
            elif "account" in user_msg_l:
                return ("To create or manage your account, go to the Banking tab and use the Account Operations section.")
            elif "order" in user_msg_l:
                return ("You can view your order history in the Orders tab.")
            elif "cart" in user_msg_l:
                return ("Add products to your cart from the Products tab, then review and checkout from the Cart tab.")
            elif "dark mode" in user_msg_l:
                return ("Click the 🌙 button in the top bar to toggle dark mode.")
            elif "admin" in user_msg_l:
                return ("The Admin panel is accessible via the 🛠️ Admin button in the top bar.")
            elif "feedback" in user_msg_l:
                return ("Submit your feedback in the Feedback tab.")
            elif "help" in user_msg_l or "how" in user_msg_l:
                return ("Use the navigation bar or menu to switch between pages. For more help, contact: 0241cys143@niet.co.in")
            else:
                return ("Sorry, I can only answer questions about using this app. For more help, contact: 0241cys143@niet.co.in")
        
        def send_message(event=None):
            msg = user_entry.get().strip()
            if not msg:
                return
            chat_log.config(state="normal")
            chat_log.insert(tk.END, f"You: {msg}\n", "user")
            chat_log.tag_config("user", foreground="#0d6efd")
            response = ai_response(msg)
            self._ai_chat_history.append(("ai", response))
            chat_log.insert(tk.END, f"AI: {response}\n", "ai")
            chat_log.tag_config("ai", foreground="#198754")
            chat_log.config(state="disabled")
            chat_log.see(tk.END)
            user_entry.delete(0, tk.END)
        
        user_entry.bind("<Return>", send_message)
        send_btn = tk.Button(entry_frame, text="Send", font=("Segoe UI", 11, "bold"), bg="#17a2b8", fg="white", command=send_message)
        send_btn.pack(side=tk.RIGHT)
        
        # Clear chat button
        def clear_chat():
            self._ai_chat_history.clear()
            chat_log.config(state="normal")
            chat_log.delete(1.0, tk.END)
            chat_log.insert(tk.END, "AI: Hi! I'm your assistant. Ask me anything about using this app.\n", "ai")
            chat_log.tag_config("ai", foreground="#198754")
            chat_log.config(state="disabled")
            chat_log.see(tk.END)
        clear_btn = tk.Button(entry_frame, text="Clear Chat", font=("Segoe UI", 10), bg="#6c757d", fg="white", command=clear_chat)
        clear_btn.pack(side=tk.RIGHT, padx=(0,8))
        
        # Greet the user
        chat_log.config(state="normal")
        chat_log.insert(tk.END, "AI: Hi! I'm your assistant. Ask me anything about using this app.\n", "ai")
        chat_log.tag_config("ai", foreground="#198754")
        chat_log.config(state="disabled")
        chat_log.see(tk.END)

    def build_admin_tab(self):
        for widget in self.admin_tab.winfo_children():
            widget.destroy()
        tk.Label(self.admin_tab, text="Admin Dashboard", font=("Segoe UI", 22, "bold"), bg="#f7f9fa", fg="#0d6efd").pack(pady=10)
        btn_frame = tk.Frame(self.admin_tab, bg="#f7f9fa")
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Manage Products", font=("Segoe UI", 12, "bold"),
                 bg="#198754", fg="white", command=self.open_admin_window).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Manage Categories", font=("Segoe UI", 12, "bold"),
                 bg="#0d6efd", fg="white", command=self.open_admin_window).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="View Orders", font=("Segoe UI", 12, "bold"),
                 bg="#fd7e14", fg="white", command=self.build_orders_tab).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Manage Accounts", font=("Segoe UI", 12, "bold"),
                 bg="#6f42c1", fg="white", command=self.open_admin_window).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="User Management", font=("Segoe UI", 12, "bold"),
                 bg="#dc3545", fg="white", command=self.open_admin_window).pack(side=tk.LEFT, padx=10)
        
        # Quick stats
        stats_frame = tk.Frame(self.admin_tab, bg="#f7f9fa")
        stats_frame.pack(pady=20)
        tk.Label(stats_frame, text="Quick Stats", font=("Segoe UI", 18, "bold"),
                bg="#f7f9fa", fg="#0d6efd").pack(pady=10)
        
        # Example stats (replace with real calculations)
        total_orders = len(load_json(FILES['HISTORY'], []))
        total_revenue = sum(o.get('grand_total', 0) for o in load_json(FILES['HISTORY'], []))
        tk.Label(stats_frame, text=f"Total Orders: {total_orders}", font=("Segoe UI", 14),
                bg="#f7f9fa").pack()
        tk.Label(stats_frame, text=f"Total Revenue: ₹{total_revenue:.2f}", font=("Segoe UI", 14),
                bg="#f7f9fa").pack()

    # Banking methods
    def create_account(self):
        account_window = tk.Toplevel(self)
        account_window.title("Create Account")
        account_window.geometry("400x300")
        account_window.configure(bg="#f7f9fa")
        
        tk.Label(account_window, text="Create New Account", font=("Segoe UI", 16, "bold"),
                bg="#f7f9fa", fg="#0d6efd").pack(pady=20)
        
        fields = {}
        field_names = ["Account Number", "Account Holder Name", "Initial Deposit", "Account Type"]
        
        for field in field_names:
            frame = tk.Frame(account_window, bg="#f7f9fa")
            frame.pack(fill=tk.X, padx=20, pady=5)
            tk.Label(frame, text=field + ":", font=("Segoe UI", 11), bg="#f7f9fa").pack(side=tk.LEFT)
            entry = tk.Entry(frame, font=("Segoe UI", 11), width=25)
            entry.pack(side=tk.RIGHT)
            fields[field] = entry
        
        def create():
            acc_num = fields["Account Number"].get()
            name = fields["Account Holder Name"].get()
            deposit = fields["Initial Deposit"].get()
            acc_type = fields["Account Type"].get()
            
            if acc_num and name and deposit and acc_type:
                try:
                    deposit = float(deposit)
                    if not acc_num.isdigit():
                        messagebox.showerror("Error", "Account number must be numeric!")
                        return
                    if acc_num in self.accounts:
                        messagebox.showerror("Error", "Account number already exists!")
                        return
                    self.accounts[acc_num] = {
                        "name": name,
                        "balance": deposit,
                        "type": acc_type,
                        "created_date": str(date.today()),
                        "owner_email": self.current_user['email'] if self.is_logged_in else "guest@example.com"
                    }
                    save_json(FILES['ACCOUNTS'], self.accounts)
                    messagebox.showinfo("Success", "Account created successfully!")
                    account_window.destroy()
                except ValueError:
                    messagebox.showerror("Error", "Invalid deposit amount!")
            else:
                messagebox.showerror("Error", "Please fill all fields!")
        
        tk.Button(account_window, text="Create Account", font=("Segoe UI", 12, "bold"),
                 bg="#198754", fg="white", command=create).pack(pady=20)

    def view_balance(self):
        acc_num = simpledialog.askstring("Account", "Enter account number:")
        if acc_num and acc_num in self.accounts:
            account = self.accounts[acc_num]
            messagebox.showinfo("Balance", 
                f"Account: {acc_num}\nHolder: {account['name']}\nBalance: ₹{account['balance']:.2f}")
        elif acc_num:
            messagebox.showerror("Error", "Account not found!")

    def transfer_money(self):
        transfer_window = tk.Toplevel(self)
        transfer_window.title("Transfer Money")
        transfer_window.geometry("400x300")
        transfer_window.configure(bg="#f7f9fa")
        
        tk.Label(transfer_window, text="Money Transfer", font=("Segoe UI", 16, "bold"),
                bg="#f7f9fa", fg="#0d6efd").pack(pady=20)
        
        fields = {}
        field_names = ["From Account", "To Account", "Amount"]
        
        for field in field_names:
            frame = tk.Frame(transfer_window, bg="#f7f9fa")
            frame.pack(fill=tk.X, padx=20, pady=10)
            tk.Label(frame, text=field + ":", font=("Segoe UI", 11), bg="#f7f9fa").pack(side=tk.LEFT)
            entry = tk.Entry(frame, font=("Segoe UI", 11), width=25)
            entry.pack(side=tk.RIGHT)
            fields[field] = entry
        
        def transfer():
            from_acc = fields["From Account"].get()
            to_acc = fields["To Account"].get()
            amount = fields["Amount"].get()
            
            if from_acc and to_acc and amount:
                try:
                    amount = float(amount)
                    if from_acc in self.accounts and to_acc in self.accounts:
                        if self.accounts[from_acc]["balance"] >= amount:
                            self.accounts[from_acc]["balance"] -= amount
                            self.accounts[to_acc]["balance"] += amount
                            
                            # Record transaction
                            transaction = {
                                "date": str(datetime.now()),
                                "from_account": from_acc,
                                "to_account": to_acc,
                                "amount": amount,
                                "type": "transfer"
                            }
                            self.transactions.append(transaction)
                            
                            save_json(FILES['ACCOUNTS'], self.accounts)
                            save_json(FILES['TRANSACTIONS'], self.transactions)
                            
                            messagebox.showinfo("Success", "Transfer completed successfully!")
                            transfer_window.destroy()
                        else:
                            messagebox.showerror("Error", "Insufficient balance!")
                    else:
                        messagebox.showerror("Error", "One or both accounts not found!")
                except ValueError:
                    messagebox.showerror("Error", "Invalid amount!")
            else:
                messagebox.showerror("Error", "Please fill all fields!")
        
        tk.Button(transfer_window, text="Transfer", font=("Segoe UI", 12, "bold"),
                 bg="#0d6efd", fg="white", command=transfer).pack(pady=20)

    def view_transactions(self):
        trans_window = tk.Toplevel(self)
        trans_window.title("Transaction History")
        trans_window.geometry("600x400")
        trans_window.configure(bg="#f7f9fa")
        
        tk.Label(trans_window, text="Transaction History", font=("Segoe UI", 16, "bold"),
                bg="#f7f9fa", fg="#0d6efd").pack(pady=10)
        
        # Create treeview for transactions
        columns = ("Date", "From", "To", "Amount", "Type")
        tree = ttk.Treeview(trans_window, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        # Add transactions
        for trans in self.transactions:
            tree.insert("", tk.END, values=(
                trans.get("date", ""),
                trans.get("from_account", ""),
                trans.get("to_account", ""),
                f"₹{trans.get('amount', 0):.2f}",
                trans.get("type", "")
            ))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    # Shopping methods
    def add_to_cart(self, product_id):
        self.cart.add(product_id, 1)
        messagebox.showinfo("Success", "Product added to cart!")
        self.build_cart_tab()

    def checkout(self):
        """Enhanced checkout process with analytics and notifications"""
        if not self.cart.items:
            self.notification_manager.show_notification(
                "Your cart is empty! Add some products first.", 
                "warning"
            )
            return
        
        details = self.cart.get_details(self.products)
        
        # Show modern checkout confirmation
        checkout_window = tk.Toplevel(self)
        checkout_window.title("Checkout Confirmation")
        checkout_window.geometry("500x400")
        checkout_window.transient(self)
        checkout_window.grab_set()
        
        # Center the window
        checkout_window.update_idletasks()
        x = (checkout_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (checkout_window.winfo_screenheight() // 2) - (400 // 2)
        checkout_window.geometry(f"500x400+{x}+{y}")
        
        # Header
        header = tk.Frame(checkout_window, bg="#007bff", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header, 
            text="🛒 Checkout Confirmation", 
            font=("Segoe UI", 16, "bold"),
            bg="#007bff", 
            fg="white"
        ).pack(expand=True)
        
        # Order summary
        summary_frame = tk.Frame(checkout_window, bg="white", padx=20, pady=20)
        summary_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            summary_frame, 
            text="Order Summary", 
            font=("Segoe UI", 14, "bold"),
            bg="white"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Items list
        items_frame = tk.Frame(summary_frame, bg="white")
        items_frame.pack(fill=tk.X, pady=(0, 10))
        
        for item in details['items']:
            item_line = tk.Frame(items_frame, bg="white")
            item_line.pack(fill=tk.X, pady=2)
            
            tk.Label(
                item_line,
                text=f"{item['product']['name']} x{item['quantity']}",
                font=("Segoe UI", 10),
                bg="white"
            ).pack(side=tk.LEFT)
            
            tk.Label(
                item_line,
                text=f"₹{item['line_total']:.2f}",
                font=("Segoe UI", 10, "bold"),
                bg="white"
            ).pack(side=tk.RIGHT)
        
        # Totals
        totals_frame = tk.Frame(summary_frame, bg="#f8f9fa", padx=10, pady=10)
        totals_frame.pack(fill=tk.X, pady=(10, 0))
        
        total_items = [
            ("Subtotal:", f"₹{details['subtotal_pre_gst']:.2f}"),
        ]
        
        # Add GST breakdown if applicable
        if details['total_cgst'] > 0:
            total_items.append(("CGST:", f"₹{details['total_cgst']:.2f}"))
        if details['total_sgst'] > 0:
            total_items.append(("SGST:", f"₹{details['total_sgst']:.2f}"))
        if details['total_igst'] > 0:
            total_items.append(("IGST:", f"₹{details['total_igst']:.2f}"))
        
        total_items.extend([
            ("Total GST:", f"₹{details['total_gst']:.2f}"),
            ("Delivery:", f"₹{details['delivery_charge']:.2f}")
        ])
        
        # Add delivery GST if applicable
        if details.get('delivery_gst', 0) > 0:
            total_items.append(("Delivery GST:", f"₹{details['delivery_gst']:.2f}"))
        
        if details['total_cashback'] > 0:
            total_items.append(("Cashback:", f"-₹{details['total_cashback']:.2f}"))
        
        for label, value in total_items:
            row = tk.Frame(totals_frame, bg="#f8f9fa")
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=label, bg="#f8f9fa", font=("Segoe UI", 10)).pack(side=tk.LEFT)
            tk.Label(row, text=value, bg="#f8f9fa", font=("Segoe UI", 10, "bold")).pack(side=tk.RIGHT)
        
        # Grand total
        grand_total_frame = tk.Frame(totals_frame, bg="#28a745", padx=5, pady=5)
        grand_total_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Label(
            grand_total_frame, 
            text="Total:", 
            bg="#28a745", 
            fg="white",
            font=("Segoe UI", 12, "bold")
        ).pack(side=tk.LEFT)
        
        tk.Label(
            grand_total_frame, 
            text=f"₹{details['grand_total']:.2f}", 
            bg="#28a745", 
            fg="white",
            font=("Segoe UI", 12, "bold")
        ).pack(side=tk.RIGHT)
        
        # Buttons
        button_frame = tk.Frame(checkout_window, bg="white", pady=20)
        button_frame.pack(fill=tk.X)
        
        def confirm_order():
            checkout_window.destroy()
            self._process_order(details)
        
        def cancel_order():
            checkout_window.destroy()
        
        # Confirm button
        confirm_btn = ModernUI.create_gradient_button(
            button_frame,
            "✅ Confirm Order",
            confirm_order,
            bg="#28a745",
            hover_bg="#218838"
        )
        confirm_btn.pack(side=tk.RIGHT, padx=(5, 20))
        
        # Cancel button
        cancel_btn = ModernUI.create_gradient_button(
            button_frame,
            "❌ Cancel",
            cancel_order,
            bg="#dc3545",
            hover_bg="#c82333"
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

    def _process_order(self, details):
        """Process the order with analytics tracking"""
        try:
            # Create order record
            order = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "customer": self.current_user['email'] if self.is_logged_in else "Guest",
                "customer_name": self.current_user['name'] if self.is_logged_in else "Guest User",
                "items": [
                    {
                        "product_id": item['product']['product_id'],
                        "name": item['product']['name'],
                        "quantity": item['quantity'],
                        "original_price": item['original_price'],
                        "base_price": item['base_price'],
                        "discounted_base_price": item['discounted_base_price'],
                        "gst_rate": item['gst_rate'],
                        "line_subtotal": item['line_subtotal'],
                        "line_gst_amount": item['line_gst_amount'],
                        "cgst_amount": item['cgst_amount'],
                        "sgst_amount": item['sgst_amount'],
                        "igst_amount": item['igst_amount'],
                        "line_total": item['line_total'],
                        "cashback_amount": item['cashback_amount'],
                        "price_inclusive_gst": item['price_inclusive_gst']
                    }
                    for item in details['items']
                ],
                "subtotal_pre_gst": details['subtotal_pre_gst'],
                "total_gst": details['total_gst'],
                "total_cgst": details['total_cgst'],
                "total_sgst": details['total_sgst'],
                "total_igst": details['total_igst'],
                "delivery_charge": details['delivery_charge'],
                "delivery_gst": details.get('delivery_gst', 0),
                "delivery_gst_rate": details.get('delivery_gst_rate', 18),
                "total_cashback": details['total_cashback'],
                "grand_total": details['grand_total'],
                "status": "Confirmed",
                "order_id": f"ORD{int(time.time())}"
            }
            
            # Save to history
            history = load_json(FILES['HISTORY'], [])
            history.append(order)
            save_json(FILES['HISTORY'], history)
            
            # Track purchase analytics
            self.analytics.track_event('purchase', {
                'order_id': order['order_id'],
                'total_amount': details['grand_total'],
                'item_count': len(details['items']),
                'customer': order['customer']
            })
            
            # Clear cart
            self.cart.clear()
            
            # Refresh UI
            self.build_cart_tab()
            self.build_orders_tab()
            
            # Show success notification
            self.notification_manager.show_notification(
                f"Order {order['order_id']} placed successfully! Total: ₹{details['grand_total']:.2f}", 
                "success"
            )
            
            logging.info(f"Order placed: {order['order_id']} - ₹{details['grand_total']:.2f}")
            
        except Exception as e:
            logging.error(f"Order processing failed: {e}")
            self.notification_manager.show_notification(
                "Failed to process order. Please try again.", 
                "error"
            )

    def submit_feedback(self, feedback):
        if feedback.strip():
            append_feedback(feedback.strip())
            messagebox.showinfo("Success", "Thank you for your feedback!")
        else:
            messagebox.showwarning("Warning", "Please enter your feedback!")

    def open_admin_window(self):
        password = simpledialog.askstring("Admin Login", "Enter admin password:", show="*")
        if password == ADMIN_PASSWORD:
            AdminWindow(self, self.products, self.categories, self.shop_info, self.refresh_all)
        elif password is not None:
            messagebox.showerror("Error", "Invalid password!")

    def refresh_all(self):
        self.products = load_json(FILES['PRODUCTS'], [])
        self.categories = load_json(FILES['CATEGORIES'], DEFAULT_CATEGORIES)
        self.shop_info = load_json(FILES['SHOP'], DEFAULT_SHOP)
        self.accounts = load_json(FILES['ACCOUNTS'], {})
        self.transactions = load_json(FILES['TRANSACTIONS'], [])
        self.settings = load_json(FILES['SETTINGS'], DEFAULT_SETTINGS.copy())
        self.build_home_tab()
        self.build_products_tab()
        self.build_cart_tab()
        self.build_orders_tab()
        self.build_profile_tab()
        self.build_feedback_tab()

    def update_widget_colors(self, widget, bg, fg):
        """Recursively update bg/fg for widget and all its children, skipping ttk widgets."""
        # Skip ttk widgets (they use styles)
        if widget.winfo_class().startswith('T'):  # e.g., TButton, TLabel, Treeview, etc.
            return
        # Optionally, skip specific widget types (like Canvas, if you want)
        # if isinstance(widget, tk.Canvas):
        #     return
        try:
            widget.configure(bg=bg)
        except Exception:
            pass
        try:
            widget.configure(fg=fg)
        except Exception:
            pass
        for child in widget.winfo_children():
            self.update_widget_colors(child, bg, fg)

    # --- Replace your toggle_dark_mode method with this improved version ---
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.settings["dark_mode"] = self.dark_mode
        save_json(FILES['SETTINGS'], self.settings)
        bg = "#222" if self.dark_mode else "#f7f9fa"
        fg = "white" if self.dark_mode else "#222"
        # Update all tabs
        for tab in [
            self.home_tab, self.banking_tab, self.products_tab, self.cart_tab,
            self.orders_tab, self.profile_tab, self.feedback_tab, self.admin_tab
        ]:
            self.update_widget_colors(tab, bg, fg)
        # Update main window
        self.update_widget_colors(self, bg, fg)
        # Update ttk styles for dark mode
        style = ttk.Style()
        if self.dark_mode:
            style.theme_use('clam')
            style.configure('.', background=bg, foreground=fg, fieldbackground=bg)
            style.configure('Treeview', background="#333", foreground="white", fieldbackground="#333")
            style.map('Treeview', background=[('selected', '#444')])
        else:
            style.theme_use('clam')
            style.configure('.', background="#f7f9fa", foreground="#222", fieldbackground="#f7f9fa")
            style.configure('Treeview', background="white", foreground="#222", fieldbackground="white")
            style.map('Treeview', background=[('selected', '#e0e0e0')])

        # --- UI improvement: Add or update a footer ---
        accent = "#0d6efd" if not self.dark_mode else "#222"
        if not hasattr(self, "_footer"):
            self._footer = tk.Frame(self, bg=accent, height=30)
            self._footer.pack(side=tk.BOTTOM, fill=tk.X)
            tk.Label(
                self._footer, text="© 2025 Ashish's online banking and shopping", font=("Segoe UI", 10),
                bg=accent, fg="white"
            ).pack(pady=4)
        else:
            self._footer.configure(bg=accent)
            for child in self._footer.winfo_children():
                child.configure(bg=accent, fg="white")

    def backup_data(self):
        import zipfile
        from datetime import datetime
        files = [FILES['PRODUCTS'], FILES['CATEGORIES'], FILES['HISTORY'], FILES['FEEDBACK'], FILES['SHOP'], FILES['ACCOUNTS'], FILES['TRANSACTIONS']]
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        with zipfile.ZipFile(backup_name, 'w') as zipf:
            for file in files:
                if os.path.exists(file):
                    zipf.write(file)
        messagebox.showinfo("Backup", f"Backup saved as {backup_name}")

    def open_settings_window(self):
        win = tk.Toplevel(self)
        win.title("Settings")
        win.geometry("420x420")
        win.configure(bg="#f7f9fa")
        tk.Label(win, text="Settings", font=("Segoe UI", 18, "bold"), bg="#f7f9fa", fg="#0d6efd").pack(pady=18)

        # Dark mode toggle
        frame = tk.Frame(win, bg="#f7f9fa")
        frame.pack(fill=tk.X, padx=30, pady=5)
        tk.Label(frame, text="Theme:", font=("Segoe UI", 12), bg="#f7f9fa").pack(side=tk.LEFT)
        theme_var = tk.StringVar(value="Dark" if self.dark_mode else "Light")
        def toggle_theme():
            self.toggle_dark_mode()
            theme_var.set("Dark" if self.dark_mode else "Light")
        btn_theme = tk.Button(frame, textvariable=theme_var, font=("Segoe UI", 11), bg="#198754", fg="white", command=toggle_theme)
        btn_theme.pack(side=tk.LEFT, padx=10)
        add_hover_effect(btn_theme, "#198754", "white", "#0d6efd", "white", tooltip_text="Toggle Dark/Light Mode")

        # Change password
        frame3 = tk.Frame(win, bg="#f7f9fa")
        frame3.pack(fill=tk.X, padx=30, pady=5)
        tk.Label(frame3, text="Change Admin Password:", font=("Segoe UI", 12), bg="#f7f9fa").pack(side=tk.LEFT)
        def change_password():
            global ADMIN_PASSWORD
            old = simpledialog.askstring("Old Password", "Enter current admin password:", show="*")
            if old != ADMIN_PASSWORD:
                messagebox.showerror("Error", "Incorrect current password!")
                return
            new = simpledialog.askstring("New Password", "Enter new password:", show="*")
            if new:
                ADMIN_PASSWORD = new
                messagebox.showinfo("Success", "Admin password changed for this session.\n(Persist manually if needed.)")
        btn_pw = tk.Button(frame3, text="Change", font=("Segoe UI", 11), bg="#fd7e14", fg="white", command=change_password)
        btn_pw.pack(side=tk.LEFT, padx=10)
        add_hover_effect(btn_pw, "#fd7e14", "white", "#c82333", "white", tooltip_text="Change admin password")

        # Notifications
        frame4 = tk.Frame(win, bg="#f7f9fa")
        frame4.pack(fill=tk.X, padx=30, pady=5)
        tk.Label(frame4, text="Notifications:", font=("Segoe UI", 12), bg="#f7f9fa").pack(side=tk.LEFT)
        notif_var = tk.StringVar(value="On" if self.notifications_enabled else "Off")
        def toggle_notif():
            self.notifications_enabled = not self.notifications_enabled
            notif_var.set("On" if self.notifications_enabled else "Off")
            self.settings["notifications_enabled"] = self.notifications_enabled
            save_json(FILES['SETTINGS'], self.settings)
        btn_notif = tk.Button(frame4, textvariable=notif_var, font=("Segoe UI", 11), bg="#6c757d", fg="white", command=toggle_notif)
        btn_notif.pack(side=tk.LEFT, padx=10)
        add_hover_effect(btn_notif, "#6c757d", "white", "#495057", "white", tooltip_text="Toggle notifications")

        # Language selection
        frame5 = tk.Frame(win, bg="#f7f9fa")
        frame5.pack(fill=tk.X, padx=30, pady=5)
        tk.Label(frame5, text="Language:", font=("Segoe UI", 12), bg="#f7f9fa").pack(side=tk.LEFT)
        lang_var = tk.StringVar(value="English")
        lang_menu = ttk.Combobox(frame5, textvariable=lang_var, values=["English", "Hindi", "Marathi"], state="readonly", width=12)
        lang_menu.pack(side=tk.LEFT, padx=10)

        def on_language_change(event=None):
            self.language = lang_var.get()
            self.settings["language"] = self.language
            save_json(FILES['SETTINGS'], self.settings)
        lang_menu.bind("<<ComboboxSelected>>", on_language_change)

        # Separator
        ttk.Separator(win, orient="horizontal").pack(fill=tk.X, padx=20, pady=10)
        
        # Backup and restore options
        backup_frame = tk.Frame(win, bg="#f7f9fa")
        backup_frame.pack(fill=tk.X, padx=30, pady=5)
        tk.Label(backup_frame, text="Data Management:", font=("Segoe UI", 12), bg="#f7f9fa").pack(side=tk.LEFT)
        tk.Button(backup_frame, text="Backup Data", font=("Segoe UI", 11), bg="#17a2b8", fg="white", command=self.backup_data).pack(side=tk.LEFT, padx=10)
        add_hover_effect(backup_frame.winfo_children()[-1], "#17a2b8", "white", "#138496", "white", tooltip_text="Create data backup")

    def build_notification_center(self, parent):
        notif_frame = tk.Frame(parent, bg="#fff", relief=tk.RAISED, bd=2)
        notif_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(notif_frame, text="Notifications", font=("Segoe UI", 13, "bold"), bg="#fff", fg="#dc3545").pack(side=tk.LEFT)
        # Example: show low stock, abandoned carts, support requests
        notifs = []
        for p in self.products:
            if p.get("quantity_available", 0) < 5:
                notifs.append(f"Low stock: {p['name']}")
        # Add more: abandoned carts, support, etc.
        for n in notifs:
            tk.Label(notif_frame, text=n, font=("Segoe UI", 11), bg="#fff", fg="#dc3545").pack(anchor="w")

# Usage: call self.build_notification_center(self.dashboard_tab) in build_dashboard_tab

class AdminWindow(tk.Toplevel):
    def __init__(self, master, products, categories, shop_info, refresh_callback):
        super().__init__(master)
        self.title("Ashish's online banking and shopping Admin Dashboard")
        self.geometry("1280x850")
        self.configure(bg="#f7f9fa")
        self.products = products
        self.categories = categories
        self.shop_info = shop_info
        self.refresh_callback = refresh_callback
        self.users = load_json(FILES['USERS'], {})  # Load users data
        self.accounts = load_json(FILES['ACCOUNTS'], {})  # Load accounts data

        notebook = ttk.Notebook(self)
        notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.dashboard_tab = tk.Frame(notebook, bg="#f7f9fa")
        self.product_tab = tk.Frame(notebook, bg="#f7f9fa")
        self.category_tab = tk.Frame(notebook, bg="#f7f9fa")
        self.order_tab = tk.Frame(notebook, bg="#f7f9fa")
        self.accounts_tab = tk.Frame(notebook, bg="#f7f9fa")
        self.users_tab = tk.Frame(notebook, bg="#f7f9fa")
        self.shop_tab = tk.Frame(notebook, bg="#f7f9fa")
        self.reporting_tab = tk.Frame(notebook, bg="#f7f9fa")
        notebook.add(self.dashboard_tab, text="Dashboard")
        notebook.add(self.product_tab, text="Products")
        notebook.add(self.category_tab, text="Categories")
        notebook.add(self.order_tab, text="Orders")
        notebook.add(self.accounts_tab, text="Accounts")
        notebook.add(self.users_tab, text="Users")
        notebook.add(self.shop_tab, text="Shop Info")
        notebook.add(self.reporting_tab, text="Reporting")

        self.build_dashboard_tab()
        self.build_product_tab()
        self.build_category_tab()
        self.build_order_tab()
        self.build_accounts_tab()
        self.build_users_tab()
        self.build_shop_tab()
        self.build_reporting_tab()

        self.bind_shortcuts()

        footer = tk.Frame(self, bg="#0d6efd", height=30)
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(
            footer, text="© 2025 Ashish's online banking and shopping", font=("Segoe UI", 10),
            bg="#0d6efd", fg="white"
        ).pack(pady=4)

    def bind_shortcuts(self):
        self.bind_all("<Control-s>", lambda e: self.refresh_callback() if self.refresh_callback else None)
        self.bind_all("<Control-f>", lambda e: self.focus_search_bar())
        # Add more as needed

    def focus_search_bar(self):
        # Example: focus the search entry in product tab
        for child in self.product_tab.winfo_children():
            if isinstance(child, tk.Frame):
                for sub in child.winfo_children():
                    if isinstance(sub, tk.Entry):
                        sub.focus_set()
                        return

    def build_dashboard_tab(self):
        for widget in self.dashboard_tab.winfo_children():
            widget.destroy()
        tk.Label(self.dashboard_tab, text="Admin Dashboard", font=("Segoe UI", 24, "bold"), bg="#f7f9fa", fg="#0d6efd").pack(pady=16)

        # Quick Stats
        stats_frame = tk.Frame(self.dashboard_tab, bg="#f7f9fa")
        stats_frame.pack(pady=10)
        products = self.products if hasattr(self, "products") else []
        categories = self.categories if hasattr(self, "categories") else []
        accounts = self.master.accounts if hasattr(self.master, "accounts") else {}
        orders = load_json(FILES['HISTORY'], [])
        total_orders = len(orders)
        total_products = len(products)
        total_categories = len(categories)
        total_users = len(accounts)
        total_revenue = sum(o.get('grand_total', 0) for o in orders)

        stats = [
            ("Products", total_products, "#0d6efd"),
            ("Categories", total_categories, "#6610f2"),
            ("Users", total_users, "#fd7e14"),
            ("Orders", total_orders, "#198754"),
            ("Revenue", f"₹{total_revenue:.2f}", "#dc3545"),
        ]
        for i, (label, value, color) in enumerate(stats):
            card = tk.Frame(stats_frame, bg="white", relief=tk.RAISED, bd=2)
            card.grid(row=0, column=i, padx=18, ipadx=18, ipady=8)
            tk.Label(card, text=str(value), font=("Segoe UI", 20, "bold"), bg="white", fg=color).pack()
            tk.Label(card, text=label, font=("Segoe UI", 11), bg="white").pack()

        # Top Products
        product_counter = {}
        for order in orders:
            for item in order.get("items", []):
                name = item.get("name", "Unknown")
                qty = item.get("quantity", 0)
                product_counter[name] = product_counter.get(name, 0) + qty
        top = sorted(product_counter.items(), key=lambda x: x[1], reverse=True)[:5]
        tk.Label(self.dashboard_tab, text="Top Products", font=("Segoe UI", 14, "bold"), bg="#f7f9fa").pack(pady=(20, 5))
        top_frame = tk.Frame(self.dashboard_tab, bg="#f7f9fa")
        top_frame.pack()
        for name, qty in top:
            tk.Label(top_frame, text=f"{name}: {qty} sold", font=("Segoe UI", 12), bg="#f7f9fa").pack(anchor="w")

        # Recent Orders
        tk.Label(self.dashboard_tab, text="Recent Orders", font=("Segoe UI", 14, "bold"), bg="#f7f9fa").pack(pady=(20, 5))
        columns = ("Order ID", "Date", "Customer", "Total", "Status")
        tree = ttk.Treeview(self.dashboard_tab, columns=columns, show="headings", height=5)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        for idx, order in enumerate(reversed(orders[-5:])):
            tree.insert("", tk.END, values=(
                f"ORD{total_orders-idx:04d}",
                order.get("timestamp", ""),
                order.get("customer", "Guest"),
                f"₹{order.get('grand_total', 0):.2f}",
                order.get("status", "Pending")
            ))
        tree.pack(fill=tk.X, padx=30)

        # Recent Users
        tk.Label(self.dashboard_tab, text="Recent Users", font=("Segoe UI", 14, "bold"), bg="#f7f9fa").pack(pady=(20, 5))
        columns = ("Account No", "Name", "Balance", "Type", "Created")
        tree2 = ttk.Treeview(self.dashboard_tab, columns=columns, show="headings", height=5)
        for col in columns:
            tree2.heading(col, text=col)
            tree2.column(col, width=120)
        for acc, info in list(accounts.items())[-5:]:
            tree2.insert("", tk.END, values=(acc, info['name'], f"₹{info['balance']:.2f}", info['type'], info['created_date']))
        tree2.pack(fill=tk.X, padx=30)

    def build_product_tab(self):
        for widget in self.product_tab.winfo_children():
            widget.destroy()
        tk.Label(self.product_tab, text="Manage Products", font=("Segoe UI", 18, "bold"), bg="#f7f9fa", fg="#0d6efd").pack(pady=10)
        columns = ("ID", "Name", "Price", "Stock", "Category", "GST", "Discount", "Cashback", "Photos")
        tree = ttk.Treeview(self.product_tab, columns=columns, show="headings", height=15)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=90)
        for p in self.products:
            # Count photos
            photos = p.get('photos', [])
            if not photos and p.get('photo'):  # Backward compatibility
                photos = [p.get('photo')]
            photo_count = len([photo for photo in photos if photo and os.path.exists(photo)])
            
            tree.insert("", tk.END, values=(
                p.get("product_id", ""),
                p.get("name", ""),
                p.get("price", ""),
                p.get("quantity_available", ""),
                p.get("category", ""),
                p.get("gst_rate", ""),
                p.get("discount_percent", ""),
                p.get("cashback_percent", 0.0),
                f"{photo_count} photo(s)"
            ))
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        btn_frame = tk.Frame(self.product_tab, bg="#f7f9fa")
        btn_frame.pack(pady=10)

        def add_or_edit_product(edit=False, product=None):
            dialog = tk.Toplevel(self)
            dialog.title("Edit Product" if edit else "Add Product")
            dialog.geometry("500x650")
            dialog.configure(bg="#f7f9fa")
            fields = {}
            
            # Get existing photos for editing
            existing_photos = product.get("photos", []) if edit and product else []
            # Handle backward compatibility - if 'photo' exists, migrate it
            if not existing_photos and product and product.get("photo"):
                existing_photos = [product.get("photo")]
            
            labels = [
                ("Product ID", product.get("product_id", "") if edit and product else ""),
                ("Name", product.get("name", "") if edit and product else ""),
                ("Price", product.get("price", "") if edit and product else ""),
                ("Stock", product.get("quantity_available", "") if edit and product else ""),
                ("Category", product.get("category", self.categories[0] if self.categories else "") if edit and product else (self.categories[0] if self.categories else "")),
                ("GST Rate", product.get("gst_rate", 0.0) if edit and product else "0.0"),
                ("Discount (%)", product.get("discount_percent", 0.0) if edit and product else "0.0"),
                ("Cashback (%)", product.get("cashback_percent", 0.0) if edit and product else "0.0")
            ]
            
            # Create fields for basic product info
            for i, (label, default) in enumerate(labels):
                tk.Label(dialog, text=label, bg="#f7f9fa", anchor="w").grid(row=i, column=0, sticky="w", padx=10, pady=7)
                if label == "Category":
                    var = tk.StringVar(value=default)
                    entry = ttk.Combobox(dialog, textvariable=var, values=self.categories, state="readonly")
                    entry.grid(row=i, column=1, padx=10, pady=7)
                    fields[label] = entry
                else:
                    entry = tk.Entry(dialog)
                    entry.grid(row=i, column=1, padx=10, pady=7)
                    entry.insert(0, default)
                    fields[label] = entry
            
            # Photo management section
            row_offset = len(labels)
            tk.Label(dialog, text="Product Photos", font=("Segoe UI", 12, "bold"), bg="#f7f9fa", fg="#0d6efd").grid(row=row_offset, column=0, columnspan=3, pady=(15, 5))
            
            # Frame for photo list
            photo_frame = tk.Frame(dialog, bg="#f7f9fa")
            photo_frame.grid(row=row_offset+1, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
            
            # List to store photo paths
            photo_list = existing_photos.copy()
            
            # Listbox to display photos
            photo_listbox = tk.Listbox(photo_frame, height=6, width=50)
            photo_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Scrollbar for listbox
            scrollbar = tk.Scrollbar(photo_frame, orient="vertical", command=photo_listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            photo_listbox.configure(yscrollcommand=scrollbar.set)
            
            def refresh_photo_list():
                photo_listbox.delete(0, tk.END)
                for i, photo_path in enumerate(photo_list):
                    display_name = os.path.basename(photo_path) if photo_path else f"Photo {i+1}"
                    status = " ✓" if photo_path and os.path.exists(photo_path) else " ✗"
                    photo_listbox.insert(tk.END, f"{i+1}. {display_name}{status}")
            
            refresh_photo_list()
            
            # Photo management buttons
            photo_btn_frame = tk.Frame(dialog, bg="#f7f9fa")
            photo_btn_frame.grid(row=row_offset+2, column=0, columnspan=3, pady=10)
            
            def add_photo():
                path = filedialog.askopenfilename(
                    title="Select Product Image", 
                    filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
                )
                if path:
                    photo_list.append(path)
                    refresh_photo_list()
            
            def remove_photo():
                selected = photo_listbox.curselection()
                if selected:
                    idx = selected[0]
                    if 0 <= idx < len(photo_list):
                        photo_list.pop(idx)
                        refresh_photo_list()
                else:
                    messagebox.showwarning("Select Photo", "Please select a photo to remove.", parent=dialog)
            
            def edit_photo():
                selected = photo_listbox.curselection()
                if selected:
                    idx = selected[0]
                    if 0 <= idx < len(photo_list):
                        path = filedialog.askopenfilename(
                            title="Replace Product Image", 
                            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
                        )
                        if path:
                            photo_list[idx] = path
                            refresh_photo_list()
                else:
                    messagebox.showwarning("Select Photo", "Please select a photo to edit.", parent=dialog)
            
            def move_photo_up():
                selected = photo_listbox.curselection()
                if selected:
                    idx = selected[0]
                    if idx > 0:
                        photo_list[idx], photo_list[idx-1] = photo_list[idx-1], photo_list[idx]
                        refresh_photo_list()
                        photo_listbox.selection_set(idx-1)
            
            def move_photo_down():
                selected = photo_listbox.curselection()
                if selected:
                    idx = selected[0]
                    if idx < len(photo_list) - 1:
                        photo_list[idx], photo_list[idx+1] = photo_list[idx+1], photo_list[idx]
                        refresh_photo_list()
                        photo_listbox.selection_set(idx+1)
            
            tk.Button(photo_btn_frame, text="Add Photo", bg="#198754", fg="white", command=add_photo).pack(side=tk.LEFT, padx=2)
            tk.Button(photo_btn_frame, text="Remove Photo", bg="#dc3545", fg="white", command=remove_photo).pack(side=tk.LEFT, padx=2)
            tk.Button(photo_btn_frame, text="Edit Photo", bg="#fd7e14", fg="white", command=edit_photo).pack(side=tk.LEFT, padx=2)
            tk.Button(photo_btn_frame, text="Move Up", bg="#6c757d", fg="white", command=move_photo_up).pack(side=tk.LEFT, padx=2)
            tk.Button(photo_btn_frame, text="Move Down", bg="#6c757d", fg="white", command=move_photo_down).pack(side=tk.LEFT, padx=2)
            
            # Save button
            def save():
                try:
                    pid = fields["Product ID"].get().strip()
                    name = fields["Name"].get().strip()
                    price = float(fields["Price"].get())
                    stock = int(fields["Stock"].get())
                    category = fields["Category"].get()
                    gst = float(fields["GST Rate"].get())
                    discount = float(fields["Discount (%)"].get())
                    cashback = float(fields["Cashback (%)"].get())
                    
                    if not pid or not name:
                        messagebox.showerror("Error", "Product ID and Name are required.", parent=dialog)
                        return
                    if not edit and any(p["product_id"] == pid for p in self.products):
                        messagebox.showerror("Error", "Product ID already exists.", parent=dialog)
                        return
                    
                    prod_data = {
                        "product_id": pid,
                        "name": name,
                        "price": price,
                        "quantity_available": stock,
                        "category": category,
                        "gst_rate": gst,
                        "discount_percent": discount,
                        "cashback_percent": cashback,
                        "photos": photo_list.copy()
                    }
                    
                    # Keep backward compatibility with single photo field
                    if photo_list:
                        prod_data["photo"] = photo_list[0]
                    
                    if edit:
                        product.update(prod_data)
                    else:
                        self.products.append(prod_data)
                    
                    save_json(FILES['PRODUCTS'], self.products)
                    self.build_product_tab()
                    dialog.destroy()
                    messagebox.showinfo("Success", "Product saved successfully!", parent=self)
                except ValueError:
                    messagebox.showerror("Error", "Invalid number in price, stock, GST, discount, or cashback.", parent=dialog)
                except Exception as e:
                    messagebox.showerror("Error", f"Unexpected error: {e}", parent=dialog)
            
            tk.Button(dialog, text="Save Product", font=("Segoe UI", 12, "bold"), bg="#198754", fg="white", command=save).grid(row=row_offset+3, column=0, columnspan=3, pady=(20, 10))

        def add_product():
            add_or_edit_product(edit=False)

        def edit_product():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Select", "Select a product to edit.", parent=self)
                return
            idx = tree.index(selected[0])
            product = self.products[idx]
            add_or_edit_product(edit=True, product=product)

        def delete_product():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Select", "Select a product to delete.", parent=self)
                return
            idx = tree.index(selected[0])
            prod = self.products[idx]
            if messagebox.askyesno("Delete", f"Delete product '{prod['name']}'?", parent=self):
                del self.products[idx]
                save_json(FILES['PRODUCTS'], self.products)
                self.build_product_tab()
                messagebox.showinfo("Deleted", "Product deleted.", parent=self)

        tk.Button(btn_frame, text="Add Product", bg="#198754", fg="white", command=add_product).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit Product", bg="#fd7e14", fg="white", command=edit_product).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete Product", bg="#dc3545", fg="white", command=delete_product).pack(side=tk.LEFT, padx=5)

        # Extra: Double-click to edit
        def on_double_click(event):
            selected = tree.selection()
            if selected:
                idx = tree.index(selected[0])
                product = self.products[idx]
                add_or_edit_product(edit=True, product=product)
        tree.bind("<Double-1>", on_double_click)

    def build_category_tab(self):
        for widget in self.category_tab.winfo_children():
            widget.destroy()
        tk.Label(self.category_tab, text="Manage Categories", font=("Segoe UI", 18, "bold"), bg="#f7f9fa", fg="#0d6efd").pack(pady=10)
        columns = ("Category Name",)
        tree = ttk.Treeview(self.category_tab, columns=columns, show="headings", height=15)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=200)
        for cat in self.categories:
            tree.insert("", tk.END, values=(cat,))
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        btn_frame = tk.Frame(self.category_tab, bg="#f7f9fa")
        btn_frame.pack(pady=10)

        def add_category():
            name = simpledialog.askstring("New Category", "Enter category name:")
            if name:
                self.categories.append(name)
                save_json(FILES['CATEGORIES'], self.categories)
                self.build_category_tab()
                messagebox.showinfo("Success", "Category added.")

        def delete_category():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Select", "Select a category to delete.")
                return
            cat = tree.item(selected[0])["values"][0]
            self.categories.remove(cat)
            save_json(FILES['CATEGORIES'], self.categories)
            self.build_category_tab()
            messagebox.showinfo("Deleted", "Category deleted.")

        tk.Button(btn_frame, text="Add Category", bg="#198754", fg="white", command=add_category).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete Category", bg="#dc3545", fg="white", command=delete_category).pack(side=tk.LEFT, padx=5)

    def build_order_tab(self):
        for widget in self.order_tab.winfo_children():
            widget.destroy()
        tk.Label(self.order_tab, text="Manage Orders", font=("Segoe UI", 18, "bold"), bg="#f7f9fa", fg="#0d6efd").pack(pady=10)
        btn_refresh = tk.Button(self.order_tab, text="🔄 Refresh", font=("Segoe UI", 11, "bold"), bg="#198754", fg="white", command=self.build_order_tab)
        btn_refresh.pack(pady=5)
        add_hover_effect(btn_refresh, "#198754", "white", "#0d6efd", "white", tooltip_text="Refresh order list")
        columns = ("Order ID", "Date", "Customer", "Total", "Status")
        tree = ttk.Treeview(self.order_tab, columns=columns, show="headings", height=18)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        orders = load_json(FILES['HISTORY'], [])
        for idx, order in enumerate(reversed(orders)):
            tree.insert("", tk.END, values=(
                f"ORD{len(orders)-idx:04d}",
                order.get("timestamp", ""),
                order.get("customer", "Guest"),
                f"₹{order.get('grand_total', 0):.2f}",
                order.get("status", "Pending")
            ))
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
        def show_order_details(event):
            selected = tree.selection()
            if not selected:
                return
            idx = tree.index(selected[0])
            order = orders[-(idx+1)]  # reversed order
            dialog = tk.Toplevel(self)
            dialog.title(f"Order Details - ORD{len(orders)-idx:04d}")
            dialog.geometry("500x500")
            dialog.configure(bg="#f7f9fa")
            tk.Label(dialog, text=f"Order ID: ORD{len(orders)-idx:04d}", font=("Segoe UI", 14, "bold"), bg="#f7f9fa").pack(pady=8)
            tk.Label(dialog, text=f"Date: {order.get('timestamp', '')}", font=("Segoe UI", 12), bg="#f7f9fa").pack()
            tk.Label(dialog, text=f"Customer: {order.get('customer', 'Guest')}", font=("Segoe UI", 12), bg="#f7f9fa").pack()
            tk.Label(dialog, text=f"Status: {order.get('status', 'Pending')}", font=("Segoe UI", 12), bg="#f7f9fa").pack()
            tk.Label(dialog, text=f"Grand Total: ₹{order.get('grand_total', 0):.2f}", font=("Segoe UI", 12, "bold"), bg="#f7f9fa", fg="#198754").pack(pady=5)
            tk.Label(dialog, text="Items:", font=("Segoe UI", 12, "bold"), bg="#f7f9fa").pack(pady=(10,2))
            items_frame = tk.Frame(dialog, bg="#f7f9fa")
            items_frame.pack(fill=tk.BOTH, expand=True, padx=10)
            for item in order.get("items", []):
                tk.Label(items_frame, text=f"- {item.get('name', '')} x{item.get('quantity', 1)} (₹{item.get('line_total', 0):.2f})", font=("Segoe UI", 11), bg="#f7f9fa").pack(anchor="w")
            tk.Button(dialog, text="Close", command=dialog.destroy, bg="#6c757d", fg="white").pack(pady=16)
        tree.bind("<Double-1>", show_order_details)

    def build_accounts_tab(self):
        for widget in self.accounts_tab.winfo_children():
            widget.destroy()
        tk.Label(self.accounts_tab, text="Manage Accounts", font=("Segoe UI", 18, "bold"), bg="#f7f9fa", fg="#0d6efd").pack(pady=10)
        btn_refresh = tk.Button(self.accounts_tab, text="🔄 Refresh", font=("Segoe UI", 11, "bold"), bg="#198754", fg="white", command=self.build_accounts_tab)
        btn_refresh.pack(pady=5)
        add_hover_effect(btn_refresh, "#198754", "white", "#0d6efd", "white", tooltip_text="Refresh account list")
        columns = ("Account No", "Holder Name", "Balance", "Type", "Created", "Cashback (%)")
        tree = ttk.Treeview(self.accounts_tab, columns=columns, show="headings", height=18)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        for acc, info in self.master.accounts.items():
            tree.insert("", tk.END, values=(
                acc,
                info['name'],
                f"₹{info['balance']:.2f}",
                info['type'],
                info['created_date'],
                info.get('cashback_percent', 0.0)
            ))
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
        def show_account_details(event):
            selected = tree.selection()
            if not selected:
                return
            idx = tree.index(selected[0])
            acc = list(self.master.accounts.keys())[idx]
            info = self.master.accounts[acc]
            dialog = tk.Toplevel(self)
            dialog.title(f"Account Details - {acc}")
            dialog.geometry("400x400")
            dialog.configure(bg="#f7f9fa")
            fields = {}
            labels = [
                ("Account No", acc),
                ("Holder Name", info['name']),
                ("Balance", info['balance']),
                ("Type", info['type']),
                ("Created", info['created_date']),
                ("Cashback (%)", info.get('cashback_percent', 0.0))
            ]
            for i, (label, value) in enumerate(labels):
                tk.Label(dialog, text=label+":", font=("Segoe UI", 11), bg="#f7f9fa").grid(row=i, column=0, sticky="w", padx=10, pady=8)
                entry = tk.Entry(dialog, font=("Segoe UI", 11), width=25)
                entry.insert(0, value)
                if label == "Account No" or label == "Created":
                    entry.config(state="readonly")
                entry.grid(row=i, column=1, padx=10, pady=8)
                fields[label] = entry
            def save():
                try:
                    info['name'] = fields['Holder Name'].get()
                    info['balance'] = float(fields['Balance'].get())
                    info['type'] = fields['Type'].get()
                    cashback = float(fields['Cashback (%)'].get())
                    if cashback == 0:
                        info.pop('cashback_percent', None)
                    else:
                        info['cashback_percent'] = cashback
                    save_json(FILES['ACCOUNTS'], self.master.accounts)
                    dialog.destroy()
                    self.build_accounts_tab()
                    messagebox.showinfo("Success", "Account updated.", parent=self)
                except Exception as e:
                    messagebox.showerror("Error", f"Invalid input: {e}", parent=dialog)
            tk.Button(dialog, text="Save", font=("Segoe UI", 12, "bold"), bg="#198754", fg="white", command=save).grid(row=len(labels), column=0, columnspan=2, pady=18)
        tree.bind("<Double-1>", show_account_details)
    
        btn_frame = tk.Frame(self.accounts_tab, bg="#f7f9fa")
        btn_frame.pack(pady=10)
        def set_cashback():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Select", "Select an account.", parent=self)
                return
            idx = tree.index(selected[0])
            acc = list(self.master.accounts.keys())[idx]
            percent = simpledialog.askfloat("Set Cashback", "Enter cashback percent (0 to remove):", minvalue=0, maxvalue=100, parent=self)
            if percent is not None:
                if percent == 0:
                    self.master.accounts[acc].pop('cashback_percent', None)
                else:
                    self.master.accounts[acc]['cashback_percent'] = percent
                save_json(FILES['ACCOUNTS'], self.master.accounts)
                self.build_accounts_tab()
                messagebox.showinfo("Success", "Cashback updated.", parent=self)
        tk.Button(btn_frame, text="Set/Remove Cashback", bg="#198754", fg="white", command=set_cashback).pack(side=tk.LEFT, padx=5)
 
    def build_users_tab(self):
        for widget in self.users_tab.winfo_children():
            widget.destroy()
        
        # Title
        tk.Label(self.users_tab, text="User Management", font=("Segoe UI", 18, "bold"), 
                bg="#f7f9fa", fg="#0d6efd").pack(pady=10)
        
        # Control buttons frame
        control_frame = tk.Frame(self.users_tab, bg="#f7f9fa")
        control_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Refresh button
        refresh_btn = tk.Button(control_frame, text="🔄 Refresh", font=("Segoe UI", 11, "bold"),
                               bg="#198754", fg="white", command=self.refresh_users_data)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        add_hover_effect(refresh_btn, "#198754", "white", "#0d6efd", "white")
        
        # Add user button
        add_user_btn = tk.Button(control_frame, text="➕ Add User", font=("Segoe UI", 11, "bold"),
                                bg="#007bff", fg="white", command=self.add_new_user)
        add_user_btn.pack(side=tk.LEFT, padx=5)
        add_hover_effect(add_user_btn, "#007bff", "white", "#0056b3", "white")
        
        # Export users button
        export_btn = tk.Button(control_frame, text="📄 Export Users", font=("Segoe UI", 11, "bold"),
                              bg="#6c757d", fg="white", command=self.export_users)
        export_btn.pack(side=tk.LEFT, padx=5)
        add_hover_effect(export_btn, "#6c757d", "white", "#495057", "white")
        
        # Statistics frame
        stats_frame = tk.LabelFrame(self.users_tab, text="User Statistics", 
                                   font=("Segoe UI", 12, "bold"), bg="#f7f9fa", fg="#0d6efd")
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        stats_inner = tk.Frame(stats_frame, bg="#f7f9fa")
        stats_inner.pack(fill=tk.X, padx=10, pady=5)
        
        total_users = len(self.users)
        today = str(date.today())
        new_users_today = len([u for u in self.users.values() if u.get('join_date') == today])
        
        # Count users with banking accounts
        users_with_accounts = 0
        for email in self.users.keys():
            if any(acc.get('owner_email') == email for acc in self.accounts.values()):
                users_with_accounts += 1
        
        tk.Label(stats_inner, text=f"Total Users: {total_users}", 
                font=("Segoe UI", 11), bg="#f7f9fa").pack(side=tk.LEFT, padx=20)
        tk.Label(stats_inner, text=f"New Today: {new_users_today}", 
                font=("Segoe UI", 11), bg="#f7f9fa").pack(side=tk.LEFT, padx=20)
        tk.Label(stats_inner, text=f"With Bank Accounts: {users_with_accounts}", 
                font=("Segoe UI", 11), bg="#f7f9fa").pack(side=tk.LEFT, padx=20)
        
        # Users table
        table_frame = tk.Frame(self.users_tab, bg="#f7f9fa")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        columns = ("Email", "Name", "Join Date", "Bank Accounts", "Total Balance", "Actions")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        tree.heading("Email", text="Email Address")
        tree.heading("Name", text="Full Name")
        tree.heading("Join Date", text="Registration Date")
        tree.heading("Bank Accounts", text="Bank Accounts")
        tree.heading("Total Balance", text="Total Balance (₹)")
        tree.heading("Actions", text="Actions")
        
        tree.column("Email", width=200)
        tree.column("Name", width=150)
        tree.column("Join Date", width=120)
        tree.column("Bank Accounts", width=100)
        tree.column("Total Balance", width=120)
        tree.column("Actions", width=100)
        
        # Populate user data
        for email, user_info in self.users.items():
            # Calculate user's banking information
            user_accounts = [acc for acc_num, acc in self.accounts.items() 
                           if acc.get('owner_email') == email]
            account_count = len(user_accounts)
            total_balance = sum(acc.get('balance', 0) for acc in user_accounts)
            
            tree.insert("", tk.END, values=(
                email,
                user_info.get('name', 'N/A'),
                user_info.get('join_date', 'N/A'),
                account_count,
                f"{total_balance:.2f}",
                "Manage"
            ))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to manage user
        tree.bind("<Double-1>", self.on_user_double_click)
        
        # Context menu for users
        def show_user_context_menu(event):
            try:
                item = tree.selection()[0]
                user_email = tree.item(item, "values")[0]
                
                context_menu = tk.Menu(self, tearoff=0)
                context_menu.add_command(label="View Details", 
                                       command=lambda: self.view_user_details(user_email))
                context_menu.add_command(label="Edit User", 
                                       command=lambda: self.edit_user(user_email))
                context_menu.add_command(label="Reset Password", 
                                       command=lambda: self.reset_user_password(user_email))
                context_menu.add_separator()
                context_menu.add_command(label="View Bank Accounts", 
                                       command=lambda: self.view_user_accounts(user_email))
                context_menu.add_separator()
                context_menu.add_command(label="Delete User", 
                                       command=lambda: self.delete_user(user_email))
                
                context_menu.post(event.x_root, event.y_root)
            except IndexError:
                pass
        
        tree.bind("<Button-3>", show_user_context_menu)  # Right-click
    
    def refresh_users_data(self):
        """Refresh users and accounts data"""
        self.users = load_json(FILES['USERS'], {})
        self.accounts = load_json(FILES['ACCOUNTS'], {})
        self.build_users_tab()
    
    def on_user_double_click(self, event):
        """Handle double-click on user row"""
        try:
            item = event.widget.selection()[0]
            user_email = event.widget.item(item, "values")[0]
            self.view_user_details(user_email)
        except IndexError:
            pass
    
    def add_new_user(self):
        """Add a new user dialog"""
        add_window = tk.Toplevel(self)
        add_window.title("Add New User")
        add_window.geometry("400x300")
        add_window.configure(bg="#f7f9fa")
        add_window.grab_set()  # Make modal
        
        tk.Label(add_window, text="Add New User", font=("Segoe UI", 16, "bold"),
                bg="#f7f9fa", fg="#0d6efd").pack(pady=20)
        
        # Form fields
        form_frame = tk.Frame(add_window, bg="#f7f9fa")
        form_frame.pack(pady=20)
        
        # Name field
        tk.Label(form_frame, text="Full Name:", font=("Segoe UI", 12, "bold"), 
                bg="#f7f9fa").grid(row=0, column=0, sticky="w", pady=5)
        name_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=name_var, font=("Segoe UI", 12), 
                width=25).grid(row=0, column=1, padx=10, pady=5)
        
        # Email field
        tk.Label(form_frame, text="Email:", font=("Segoe UI", 12, "bold"), 
                bg="#f7f9fa").grid(row=1, column=0, sticky="w", pady=5)
        email_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=email_var, font=("Segoe UI", 12), 
                width=25).grid(row=1, column=1, padx=10, pady=5)
        
        # Password field
        tk.Label(form_frame, text="Password:", font=("Segoe UI", 12, "bold"), 
                bg="#f7f9fa").grid(row=2, column=0, sticky="w", pady=5)
        password_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=password_var, font=("Segoe UI", 12), 
                width=25, show="*").grid(row=2, column=1, padx=10, pady=5)
        
        def save_user():
            name = name_var.get().strip()
            email = email_var.get().strip()
            password = password_var.get().strip()
            
            if not all([name, email, password]):
                messagebox.showerror("Error", "Please fill in all fields!")
                return
            
            if email in self.users:
                messagebox.showerror("Error", "Email already exists!")
                return
            
            if len(password) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters!")
                return
            
            # Add user
            self.users[email] = {
                'name': name,
                'email': email,
                'password': password,
                'join_date': str(date.today())
            }
            
            save_json(FILES['USERS'], self.users)
            messagebox.showinfo("Success", "User added successfully!")
            add_window.destroy()
            self.build_users_tab()
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg="#f7f9fa")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        save_btn = tk.Button(btn_frame, text="Add User", font=("Segoe UI", 12, "bold"),
                           bg="#28a745", fg="white", command=save_user)
        save_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", font=("Segoe UI", 12, "bold"),
                             bg="#6c757d", fg="white", command=add_window.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=10)
    
    def view_user_details(self, email):
        """View detailed user information"""
        if email not in self.users:
            messagebox.showerror("Error", "User not found!")
            return
        
        user = self.users[email]
        details_window = tk.Toplevel(self)
        details_window.title(f"User Details - {user['name']}")
        details_window.geometry("500x400")
        details_window.configure(bg="#f7f9fa")
        
        # User info
        info_frame = tk.LabelFrame(details_window, text="User Information", 
                                  font=("Segoe UI", 12, "bold"), bg="#f7f9fa", fg="#0d6efd")
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(info_frame, text=f"Name: {user['name']}", font=("Segoe UI", 11), 
                bg="#f7f9fa").pack(anchor="w", padx=10, pady=2)
        tk.Label(info_frame, text=f"Email: {user['email']}", font=("Segoe UI", 11), 
                bg="#f7f9fa").pack(anchor="w", padx=10, pady=2)
        tk.Label(info_frame, text=f"Join Date: {user.get('join_date', 'N/A')}", 
                font=("Segoe UI", 11), bg="#f7f9fa").pack(anchor="w", padx=10, pady=2)
        
        # Banking info
        bank_frame = tk.LabelFrame(details_window, text="Banking Information", 
                                  font=("Segoe UI", 12, "bold"), bg="#f7f9fa", fg="#0d6efd")
        bank_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        user_accounts = [(acc_num, acc) for acc_num, acc in self.accounts.items() 
                        if acc.get('owner_email') == email]
        
        if user_accounts:
            columns = ("Account #", "Type", "Balance")
            tree = ttk.Treeview(bank_frame, columns=columns, show="headings", height=8)
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=120)
            
            total_balance = 0
            for acc_num, acc in user_accounts:
                balance = acc.get('balance', 0)
                total_balance += balance
                tree.insert("", tk.END, values=(
                    acc_num,
                    acc.get('type', 'N/A'),
                    f"₹{balance:.2f}"
                ))
            
            tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            tk.Label(bank_frame, text=f"Total Balance: ₹{total_balance:.2f}", 
                    font=("Segoe UI", 12, "bold"), bg="#f7f9fa", fg="#28a745").pack(pady=5)
        else:
            tk.Label(bank_frame, text="No banking accounts found", 
                    font=("Segoe UI", 11), bg="#f7f9fa", fg="#666").pack(pady=20)
    
    def edit_user(self, email):
        """Edit user information"""
        if email not in self.users:
            messagebox.showerror("Error", "User not found!")
            return
        
        user = self.users[email]
        edit_window = tk.Toplevel(self)
        edit_window.title(f"Edit User - {user['name']}")
        edit_window.geometry("400x250")
        edit_window.configure(bg="#f7f9fa")
        edit_window.grab_set()
        
        tk.Label(edit_window, text="Edit User Information", font=("Segoe UI", 16, "bold"),
                bg="#f7f9fa", fg="#0d6efd").pack(pady=20)
        
        # Form fields
        form_frame = tk.Frame(edit_window, bg="#f7f9fa")
        form_frame.pack(pady=20)
        
        # Name field
        tk.Label(form_frame, text="Full Name:", font=("Segoe UI", 12, "bold"), 
                bg="#f7f9fa").grid(row=0, column=0, sticky="w", pady=5)
        name_var = tk.StringVar(value=user['name'])
        tk.Entry(form_frame, textvariable=name_var, font=("Segoe UI", 12), 
                width=25).grid(row=0, column=1, padx=10, pady=5)
        
        # Email field (readonly)
        tk.Label(form_frame, text="Email:", font=("Segoe UI", 12, "bold"), 
                bg="#f7f9fa").grid(row=1, column=0, sticky="w", pady=5)
        tk.Label(form_frame, text=email, font=("Segoe UI", 12), 
                bg="#f7f9fa", fg="#666").grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        def save_changes():
            new_name = name_var.get().strip()
            if not new_name:
                messagebox.showerror("Error", "Name cannot be empty!")
                return
            
            self.users[email]['name'] = new_name
            save_json(FILES['USERS'], self.users)
            messagebox.showinfo("Success", "User information updated!")
            edit_window.destroy()
            self.build_users_tab()
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg="#f7f9fa")
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        save_btn = tk.Button(btn_frame, text="Save Changes", font=("Segoe UI", 12, "bold"),
                           bg="#28a745", fg="white", command=save_changes)
        save_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", font=("Segoe UI", 12, "bold"),
                             bg="#6c757d", fg="white", command=edit_window.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=10)
    
    def reset_user_password(self, email):
        """Reset user password"""
        if email not in self.users:
            messagebox.showerror("Error", "User not found!")
            return
        
        new_password = simpledialog.askstring("Reset Password", 
                                            f"Enter new password for {email}:", show="*")
        if new_password and len(new_password) >= 6:
            self.users[email]['password'] = new_password
            save_json(FILES['USERS'], self.users)
            messagebox.showinfo("Success", "Password reset successfully!")
        elif new_password:
            messagebox.showerror("Error", "Password must be at least 6 characters!")
    
    def view_user_accounts(self, email):
        """View user's banking accounts in detail"""
        user_accounts = [(acc_num, acc) for acc_num, acc in self.accounts.items() 
                        if acc.get('owner_email') == email]
        
        if not user_accounts:
            messagebox.showinfo("Info", f"No banking accounts found for {email}")
            return
        
        accounts_window = tk.Toplevel(self)
        accounts_window.title(f"Banking Accounts - {email}")
        accounts_window.geometry("600x400")
        accounts_window.configure(bg="#f7f9fa")
        
        tk.Label(accounts_window, text=f"Banking Accounts for {email}", 
                font=("Segoe UI", 16, "bold"), bg="#f7f9fa", fg="#0d6efd").pack(pady=10)
        
        columns = ("Account Number", "Type", "Balance", "Created Date")
        tree = ttk.Treeview(accounts_window, columns=columns, show="headings", height=12)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=140)
        
        total_balance = 0
        for acc_num, acc in user_accounts:
            balance = acc.get('balance', 0)
            total_balance += balance
            tree.insert("", tk.END, values=(
                acc_num,
                acc.get('type', 'N/A'),
                f"₹{balance:.2f}",
                acc.get('created_date', 'N/A')
            ))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(accounts_window, text=f"Total Balance: ₹{total_balance:.2f}", 
                font=("Segoe UI", 14, "bold"), bg="#f7f9fa", fg="#28a745").pack(pady=10)
    
    def delete_user(self, email):
        """Delete a user account"""
        if email not in self.users:
            messagebox.showerror("Error", "User not found!")
            return
        
        # Check if user has banking accounts
        user_accounts = [acc_num for acc_num, acc in self.accounts.items() 
                        if acc.get('owner_email') == email]
        
        confirm_msg = f"Are you sure you want to delete user {email}?"
        if user_accounts:
            confirm_msg += f"\n\nWarning: This user has {len(user_accounts)} banking account(s). "
            confirm_msg += "These accounts will become orphaned!"
        
        if messagebox.askyesno("Confirm Delete", confirm_msg):
            del self.users[email]
            save_json(FILES['USERS'], self.users)
            messagebox.showinfo("Success", "User deleted successfully!")
            self.build_users_tab()
    
    def export_users(self):
        """Export users data to CSV"""
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Users Data"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Email", "Name", "Join Date", "Bank Accounts", "Total Balance"])
                    
                    for email, user in self.users.items():
                        user_accounts = [acc for acc in self.accounts.values() 
                                       if acc.get('owner_email') == email]
                        account_count = len(user_accounts)
                        total_balance = sum(acc.get('balance', 0) for acc in user_accounts)
                        
                        writer.writerow([
                            email,
                            user.get('name', 'N/A'),
                            user.get('join_date', 'N/A'),
                            account_count,
                            total_balance
                        ])
                
                messagebox.showinfo("Success", f"Users data exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def build_shop_tab(self):
        for widget in self.shop_tab.winfo_children():
            widget.destroy()
        tk.Label(self.shop_tab, text="Shop Information", font=("Segoe UI", 18, "bold"), bg="#f7f9fa", fg="#0d6efd").pack(pady=10)
        info_frame = tk.Frame(self.shop_tab, bg="#f7f9fa")
        info_frame.pack(padx=20, pady=10, fill=tk.X)
        
        for key, value in self.shop_info.items():
            tk.Label(info_frame, text=f"{key.replace('_', ' ').title()}:",
                     font=("Segoe UI", 12), bg="#f7f9fa").pack(anchor="w")
            tk.Label(info_frame, text=value, font=("Segoe UI", 11),
                     bg="#f7f9fa", fg="#333").pack(anchor="w", padx=10)
        
        btn_frame = tk.Frame(self.shop_tab, bg="#f7f9fa")
        btn_frame.pack(pady=10)
        
        def edit_shop_info():
            # Open a dialog to edit shop info (implement as needed)
            pass
            pass
        tk.Button(btn_frame, text="Edit Shop Info", font=("Segoe UI", 12, "bold"),
                 bg="#198754", fg="white", command=edit_shop_info).pack(pady=10)

    def build_reporting_tab(self):
        for widget in self.reporting_tab.winfo_children():
            widget.destroy()
        tk.Label(self.reporting_tab, text="Full Report & Analytics", font=("Segoe UI", 22, "bold"), bg="#f7f9fa", fg="#0d6efd").pack(pady=10)
        orders = load_json(FILES['HISTORY'], [])
        total_orders = len(orders)
        total_revenue = sum(o.get('grand_total', 0) for o in orders)
        tk.Label(self.reporting_tab, text=f"Total Orders: {total_orders}", font=("Segoe UI", 14), bg="#f7f9fa").pack()
        tk.Label(self.reporting_tab, text=f"Total Revenue: ₹{total_revenue:.2f}", font=("Segoe UI", 14), bg="#f7f9fa").pack()
        # Top products
        product_counter = {}
        for o in orders:
            for it in o.get("items", []):
                name = it.get("name", "")
                product_counter[name] = product_counter.get(name, 0) + it.get("quantity", 0)
        top = sorted(product_counter.items(), key=lambda x: x[1], reverse=True)[:10]
        tk.Label(self.reporting_tab, text="Top 10 Products:", font=("Segoe UI", 13, "bold"), bg="#f7f9fa").pack(pady=5)
        for name, qty in top:
            tk.Label(self.reporting_tab, text=f"{name}: {qty} sold", bg="#f7f9fa").pack()
        # All Orders Table
        tk.Label(self.reporting_tab, text="All Orders", font=("Segoe UI", 13, "bold"), bg="#f7f9fa").pack(pady=(15, 5))
        columns = ("Order ID", "Date", "Customer", "Total", "Status")
        tree = ttk.Treeview(self.reporting_tab, columns=columns, show="headings", height=10)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        for idx, order in enumerate(orders):
            tree.insert("", tk.END, values=(
                f"ORD{idx+1:04d}",
                order.get("timestamp", ""),
                order.get("customer", "Guest"),
                f"₹{order.get('grand_total', 0):.2f}",
                order.get("status", "Pending")
            ))
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # Export
        def export_report():
            path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if not path: return
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Order ID", "Date", "Customer", "Total", "Status"])
                for idx, o in enumerate(orders):
                    writer.writerow([f"ORD{idx+1:04d}", o.get("timestamp", ""), o.get("customer", ""), o.get("grand_total", ""), o.get("status", "")])
            messagebox.showinfo("Export", "Report exported.")
        tk.Button(self.reporting_tab, text="Export Orders CSV", bg="#0d6efd", fg="white", command=export_report).pack(pady=10)
        
        
if __name__ == '__main__':
    # Create default files if they don't exist
    if not os.path.exists(FILES['CATEGORIES']):
        save_json(FILES['CATEGORIES'], DEFAULT_CATEGORIES)

    if not os.path.exists(FILES['PRODUCTS']):
        save_json(FILES['PRODUCTS'], [])

    if not os.path.exists(FILES['SHOP']):
        save_json(FILES['SHOP'], DEFAULT_SHOP)

    if not os.path.exists(FILES['ACCOUNTS']):
        save_json(FILES['ACCOUNTS'], {})

    if not os.path.exists(FILES['TRANSACTIONS']):
        save_json(FILES['TRANSACTIONS'], [])

    if not os.path.exists(FILES['FEEDBACK']):
        with open(FILES['FEEDBACK'], 'w', encoding='utf-8') as f:
            f.write("")

    # --- Improvement: Ensure settings file exists and is loaded ---
    if not os.path.exists(FILES['SETTINGS']):
        save_json(FILES['SETTINGS'], DEFAULT_SETTINGS.copy())

    # --- Improvement: Handle missing history file gracefully ---
    if not os.path.exists(FILES['HISTORY']):
        save_json(FILES['HISTORY'], [])

    # --- Improvement: Add error handling for app startup ---
    try:
        app = MainApp()
        app.mainloop()
    except Exception as e:
        import traceback
        with open("app_crash.log", "w", encoding="utf-8") as log:
            log.write(traceback.format_exc())
        print("An error occurred. See app_crash.log for details.")

# ...existing code...

# --- Improvement: Add unit tests for ShoppingCart ---
import unittest

class TestShoppingCart(unittest.TestCase):
    def test_add_and_remove(self):
        cart = ShoppingCart()
        cart.add("p1", 2)
        self.assertEqual(cart.items["p1"], 2)
        cart.remove("p1")
        self.assertNotIn("p1", cart.items)

    def test_clear(self):
        cart = ShoppingCart()
        cart.add("p1", 1)
        cart.add("p2", 3)
        cart.clear()
        self.assertEqual(len(cart.items), 0)

    def test_get_details_empty(self):
        cart = ShoppingCart()
        details = cart.get_details([])
        self.assertEqual(details['grand_total'], 5)  # Only delivery charge
