import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, filedialog
import openai
import os
import json
import hashlib
import secrets
import re
import time
import logging
import uuid
from functools import lru_cache
import threading
from datetime import datetime, date
from collections import Counter
import sys
import random
import queue
import traceback

# For actual image loading in product details, install and uncomment:
from PIL import Image, ImageTk
import requests
from io import BytesIO

# Thread utilities for safe GUI operations
THREAD_UTILS_AVAILABLE = False
try:
    import importlib
    thread_utils = importlib.import_module('thread_utils')
    ThreadSafeDecorator = thread_utils.ThreadSafeDecorator
    ImageLoadingManager = thread_utils.ImageLoadingManager
    SafeUpdater = thread_utils.SafeUpdater
    thread_safe_call = thread_utils.thread_safe_call
    make_thread_safe = thread_utils.make_thread_safe
    THREAD_UTILS_AVAILABLE = True
except ImportError:
    pass  # Fallback: thread_utils not available, continue without it

# File operations with error handling
def load_json(filename, default_value=None):
    """Load JSON data from file with error handling"""
    try:
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
                logging.error(f"Error loading {filename}: {e}")
                return default_value if default_value is not None else {}
        return default_value if default_value is not None else {}
    except Exception as e:
        logging.error(f"Unexpected error loading {filename}: {e}")
        return default_value if default_value is not None else {}

def save_json(filename, data):
    """Save JSON data to file with error handling"""
    try:
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except (PermissionError, OSError) as e:
            logging.error(f"File write error for {filename}: {e}")
            return False
    except Exception as e:
        logging.error(f"Unexpected error saving {filename}: {e}")
        return False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# File paths for data persistence
FILES = {
    'PRODUCTS': 'products.json',
    'CATEGORIES': 'categories.json',
    'ACCOUNTS': 'accounts.json',
    'TRANSACTIONS': 'transactions.json',
    'USERS': 'users.json',
    'SETTINGS': 'settings.json',
    'SHOP': 'shop.json',
    'FEEDBACK': 'feedback.txt'
}

# Default configurations
DEFAULT_CATEGORIES = [
    "Electronics", "Clothing", "Books", "Home & Garden", "Sports", 
    "Beauty", "Automotive", "Food & Beverages", "Health", "Toys"
]

DEFAULT_SHOP = {
    "shop_name": "Advanced Banking & Shopping System",
    "address": "123 Tech Street, Digital City, India",
    "contact": "+91-9876543210",
    "email": "support@advancedbanking.com",
    "established_year": "2025",
    "license_number": "ABSS-2025-001",
    "website": "https://advancedbanking.com",
    "business_hours": "Monday-Friday: 9:00 AM - 6:00 PM",
    "support_email": "support@advancedbanking.com",
    "version": "2.0"
}

DEFAULT_SETTINGS = {
    "dark_mode": False,
    "notifications_enabled": True,
    "language": "English",
    "auto_logout_minutes": 30,
    "theme": "modern",
    "currency_symbol": "₹",
    "date_format": "%Y-%m-%d",
    "show_animations": True,
    "sound_enabled": False,
    "backup_enabled": True,
    "security_level": "high",
    "biometric_enabled": False,
    "two_factor_auth": False,
    "max_login_attempts": 3,
    "password_expiry_days": 90,
    "session_timeout_minutes": 60,
    "encryption_enabled": True,
    "audit_logging": True,
    "data_retention_days": 365,
    "backup_frequency": "daily"
}

# Enhanced Theme Configurations
THEMES = {
    "modern": {
        "primary": "#007bff",
        "secondary": "#6c757d", 
        "success": "#28a745",
        "danger": "#dc3545",
        "warning": "#ffc107",
        "info": "#17a2b8",
        "light": "#f8f9fa",
        "dark": "#343a40",
        "white": "#ffffff",
        "background": "#f8f9fa",
        "card": "#ffffff",
        "text": "#495057"
    },
    "dark": {
        "primary": "#0d6efd",
        "secondary": "#6c757d",
        "success": "#198754", 
        "danger": "#dc3545",
        "warning": "#fd7e14",
        "info": "#0dcaf0",
        "light": "#212529",
        "dark": "#adb5bd",
        "white": "#2d3338",
        "background": "#121212",
        "card": "#1e1e1e", 
        "text": "#ffffff"
    }
}

# Initialize OpenAI client with enhanced configuration
client = None
# Enhanced Multi-Provider AI Configuration
class AIProviderManager:
    """Manages multiple AI providers with automatic fallback"""
    
    def __init__(self):
        self.providers = {}
        self.available_models = []
        self.current_provider = None
        self.current_model = None
        self.initialize_providers()
    
    def initialize_providers(self):
        """Initialize all available AI providers"""
        
        # Google Gemini Setup
        try:
            import google.generativeai as genai
            
            # Try to get API key from environment first, then fallback to default
            google_api_key = os.environ.get('GOOGLE_API_KEY', "AIzaSyAfxm_bMfOeL1k90HA9beA5yX0WwmNAgOc")
            
            if google_api_key and google_api_key != "your_google_api_key_here":
                genai.configure(api_key=google_api_key)
                
                # Test different Gemini models
                gemini_models = {
                    "gemini-pro": genai.GenerativeModel('gemini-pro'),
                    "gemini-pro-vision": genai.GenerativeModel('gemini-pro-vision')
                }
                
                # Test connection with a simple prompt
                try:
                    test_response = gemini_models["gemini-pro"].generate_content("Hello")
                    if test_response and test_response.text:
                        self.providers["gemini"] = {
                            "client": gemini_models,
                            "models": ["gemini-pro", "gemini-pro-vision"],
                            "active": True,
                            "priority": 1,
                            "name": "Google Gemini"
                        }
                        self.current_provider = "gemini"
                        self.current_model = "gemini-pro"
                        self.available_models.extend(["gemini-pro", "gemini-pro-vision"])
                        logging.info("✅ Google Gemini initialized successfully")
                    else:
                        logging.warning("🔴 Gemini test response was empty")
                except Exception as test_error:
                    logging.warning(f"🔴 Gemini connection test failed: {test_error}")
            else:
                logging.warning("🔑 Google API key not provided - Gemini disabled")
                    
        except ImportError:
            logging.warning("📦 Google Generative AI library not found. Install: pip install google-generativeai")
        except Exception as e:
            logging.warning(f"🔴 Gemini initialization failed: {e}")
        
        # OpenAI Setup
        try:
            openai_key = os.environ.get('OPENAI_API_KEY')
            if openai_key:
                openai_client = openai.OpenAI(api_key=openai_key)
                
                # Test connection and get models
                try:
                    models_response = openai_client.models.list()
                    model_ids = [model.id for model in models_response.data]
                    openai_models = [m for m in ["gpt-4", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"] if m in model_ids]
                    
                    if openai_models:
                        self.providers["openai"] = {
                            "client": openai_client,
                            "models": openai_models,
                            "active": True,
                            "priority": 2,
                            "name": "OpenAI"
                        }
                        
                        # Set as current if no Gemini
                        if not self.current_provider:
                            self.current_provider = "openai"
                            self.current_model = openai_models[0]
                        
                        self.available_models.extend(openai_models)
                        logging.info(f"✅ OpenAI initialized with models: {openai_models}")
                        
                except Exception as e:
                    logging.warning(f"🔴 OpenAI model fetch failed: {e}")
                    
        except Exception as e:
            logging.warning(f"🔴 OpenAI initialization failed: {e}")
        
        # Anthropic Claude Setup (Future enhancement)
        try:
            claude_key = os.environ.get('ANTHROPIC_API_KEY')
            if claude_key:
                # Placeholder for future Anthropic integration
                logging.info("🔮 Anthropic API key found (integration coming soon)")
        except:
            pass
        
        # Local AI Models Setup (Future enhancement)
        try:
            # Check for local models like Ollama, Llama, etc.
            # This would allow completely offline AI operation
            logging.info("🏠 Checking for local AI models...")
        except:
            pass
        
        # Enhanced Offline Mode (Always available)
        self.providers["offline"] = {
            "client": None,
            "models": ["enhanced-offline"],
            "active": True,
            "priority": 99,
            "name": "Enhanced Offline"
        }
        
        if "enhanced-offline" not in self.available_models:
            self.available_models.append("enhanced-offline")
        
        # Set fallback if no other provider
        if not self.current_provider:
            self.current_provider = "offline"
            self.current_model = "enhanced-offline"
            
        logging.info(f"🤖 AI System initialized: {len(self.providers)} providers, Current: {self.current_provider}")
    
    def get_active_providers(self):
        """Get list of active providers"""
        return {name: info for name, info in self.providers.items() if info["active"]}
    
    def switch_provider(self, provider_name, model_name=None):
        """Switch to a different AI provider"""
        if provider_name in self.providers and self.providers[provider_name]["active"]:
            self.current_provider = provider_name
            
            if model_name and model_name in self.providers[provider_name]["models"]:
                self.current_model = model_name
            else:
                self.current_model = self.providers[provider_name]["models"][0]
            
            logging.info(f"🔄 Switched to {provider_name}: {self.current_model}")
            return True
        return False
    
    def generate_response(self, prompt, max_tokens=500, temperature=0.7):
        """Generate response using current provider with automatic fallback"""
        
        # Try current provider first
        providers_to_try = [self.current_provider]
        
        # Add other providers as fallback (by priority)
        other_providers = sorted(
            [name for name, info in self.providers.items() 
             if name != self.current_provider and info["active"]],
            key=lambda x: self.providers[x]["priority"]
        )
        providers_to_try.extend(other_providers)
        
        for provider_name in providers_to_try:
            try:
                provider = self.providers[provider_name]
                
                if provider_name == "gemini":
                    model = provider["client"][self.current_model if self.current_provider == "gemini" else "gemini-pro"]
                    response = model.generate_content(prompt)
                    
                    # Check if response is valid
                    if response and hasattr(response, 'text') and response.text:
                        return response.text, provider_name
                    else:
                        raise Exception("Empty response from Gemini")
                        
                elif provider_name == "openai":
                    client = provider["client"]
                    model = self.current_model if self.current_provider == "openai" else provider["models"][0]
                    
                    response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    
                    # Check if response is valid
                    if response and response.choices and response.choices[0].message.content:
                        return response.choices[0].message.content, provider_name
                    else:
                        raise Exception("Empty response from OpenAI")
                        
                elif provider_name == "offline":
                    # Enhanced offline response
                    offline_response = self.generate_offline_response(prompt)
                    return offline_response, provider_name
                    
            except ImportError as e:
                logging.warning(f"🔴 {provider_name} library not available: {e}")
                continue
            except Exception as e:
                logging.warning(f"🔴 {provider_name} failed: {e}")
                continue
        
        # Ultimate fallback
        return "I apologize, but I'm having trouble connecting to AI services. Please try again later.", "error"
    
    def generate_offline_response(self, prompt):
        """Enhanced offline response generation"""
        prompt_lower = prompt.lower()
        
        # Banking responses
        if any(word in prompt_lower for word in ['account', 'bank', 'deposit', 'withdraw', 'balance']):
            return """🏦 **Banking Help Available**

I can help you with:
• **Account Management**: Create, view, and manage your accounts
• **Transactions**: Deposits, withdrawals, and transfers
• **Balance Inquiries**: Check your current balances
• **Transaction History**: View and filter your transaction records

To get started, navigate to the Banking section using the tabs above. Would you like specific guidance on any of these features?"""

        elif any(word in prompt_lower for word in ['shop', 'product', 'cart', 'buy', 'checkout']):
            return """🛒 **Shopping Features Available**

I can guide you through:
• **Product Browsing**: Search and filter products by category, price, or name
• **Shopping Cart**: Add items, manage quantities, and review selections
• **Checkout Process**: Complete purchases using your banking accounts
• **Order History**: Track your past purchases and orders

The shopping section offers real-time search and advanced filtering. What specific shopping feature would you like to explore?"""

        elif any(word in prompt_lower for word in ['search', 'filter', 'find']):
            return """🔍 **Advanced Search Features**

Our system includes powerful search capabilities:
• **Global Search**: Search across all sections simultaneously
• **Real-time Filtering**: Instant results as you type
• **Advanced Operators**: Use >, <, ranges, and exact matches
• **Smart Suggestions**: Context-aware search recommendations

Try using operators like:
- `amount > 100` for transactions over $100
- `electronics` for electronics products
- `date:2024` for items from 2024

What would you like to search for?"""

        else:
            return """👋 **Welcome to the Banking & Shopping System!**

I'm here to help you navigate our comprehensive platform:

🏦 **Banking**: Account management, transactions, transfers
🛒 **Shopping**: Product browsing, cart management, checkout
🔍 **Search**: Advanced filtering across all sections
📊 **Analytics**: Transaction history and reporting
💬 **Support**: Step-by-step guidance for all features

What specific area would you like assistance with? I can provide detailed guidance for any feature or operation."""

# Initialize AI Provider Manager
ai_manager = AIProviderManager()

# Legacy variables for backward compatibility
available_models = ai_manager.available_models
current_model = ai_manager.current_model
client = ai_manager.providers.get("openai", {}).get("client")
gemini_client = ai_manager.providers.get("gemini", {}).get("client")

# Enhanced validation utilities
def validate_amount(amount_str):
    """Enhanced amount validation with better error handling"""
    try:
        amount = float(amount_str)
        if amount <= 0:
            return False, "Amount must be positive"
        if amount > 10000000:  # 1 crore limit
            return False, "Amount too large (max: ₹1,00,00,000)"
        if len(str(amount).split('.')[-1]) > 2:
            return False, "Amount can have maximum 2 decimal places"
        return True, amount
    except ValueError:
        return False, "Please enter a valid number"

def validate_account_id(account_id):
    """Validate account ID format"""
    if not account_id:
        return False, "Account ID cannot be empty"
    if not account_id.isdigit():
        return False, "Account ID must contain only numbers"
    if len(account_id) > 10:
        return False, "Account ID too long"
    return True, account_id

def validate_user_input(text, min_length=2, max_length=100, allow_special=True):
    """Enhanced user input validation"""
    if not text or not text.strip():
        return False, "Field cannot be empty"
    
    text = text.strip()
    if len(text) < min_length:
        return False, f"Minimum {min_length} characters required"
    if len(text) > max_length:
        return False, f"Maximum {max_length} characters allowed"
    
    if not allow_special:
        if not text.replace(' ', '').isalnum():
            return False, "Only letters, numbers and spaces allowed"
    
    return True, text

def validate_password(password):
    """Enhanced password validation"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"

def format_currency(amount, symbol="₹"):
    """Enhanced currency formatting"""
    try:
        return f"{symbol}{float(amount):,.2f}"
    except (ValueError, TypeError):
        return f"{symbol}0.00"

def generate_transaction_id():
    """Generate unique transaction ID"""
    import uuid
    return str(uuid.uuid4())[:8].upper()

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

# Additional UI classes
class AccountDialog:
    """Enhanced dialog for account creation with better UX"""
    def __init__(self, parent, title):
        self.parent = parent
        self.result = None
        self.create_dialog(title)
    
    def create_dialog(self, title):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(title)
        self.dialog.geometry("450x400")
        self.dialog.configure(bg='#f8f9fa')
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.center_dialog()
        
        # Header with icon
        header_frame = tk.Frame(self.dialog, bg='#007bff', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, text="🏦 " + title, 
                               font=('Segoe UI', 16, 'bold'),
                               bg='#007bff', fg='white')
        header_label.pack(pady=15)
        
        # Main form
        form_frame = tk.Frame(self.dialog, bg='white', padx=30, pady=30)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Account name field with validation
        tk.Label(form_frame, text="👤 Account Holder Name:", 
                font=('Segoe UI', 11, 'bold'), bg='white', fg='#495057').pack(anchor='w', pady=(0,5))
        self.name_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=30, 
                                  relief='solid', bd=1, highlightthickness=2,
                                  highlightcolor='#007bff')
        self.name_entry.pack(pady=(0,15), ipady=8)
        
        # Initial balance
        tk.Label(form_frame, text="💰 Initial Balance (₹):", 
                font=('Segoe UI', 11, 'bold'), bg='white', fg='#495057').pack(anchor='w', pady=(0,5))
        self.balance_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=30,
                                     relief='solid', bd=1, highlightthickness=2,
                                     highlightcolor='#007bff')
        self.balance_entry.pack(pady=(0,15), ipady=8)
        self.balance_entry.insert(0, "500")  # Default minimum
        
        # Account type
        tk.Label(form_frame, text="🏛️ Account Type:", 
                font=('Segoe UI', 11, 'bold'), bg='white', fg='#495057').pack(anchor='w', pady=(0,5))
        self.type_var = tk.StringVar(value="Savings")
        type_combo = ttk.Combobox(form_frame, textvariable=self.type_var,
                                 values=["Savings", "Current", "Fixed Deposit"], 
                                 state="readonly", font=('Segoe UI', 11), width=27)
        type_combo.pack(pady=(0,15), ipady=5)
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg='white')
        btn_frame.pack(pady=20)
        
        ok_btn = tk.Button(btn_frame, text="✅ Create Account", command=self.ok_clicked,
                          bg='#28a745', fg='white', font=('Segoe UI', 11, 'bold'),
                          relief='flat', cursor='hand2', padx=20, pady=10)
        ok_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(btn_frame, text="❌ Cancel", command=self.cancel_clicked,
                              bg='#dc3545', fg='white', font=('Segoe UI', 11, 'bold'),
                              relief='flat', cursor='hand2', padx=20, pady=10)
        cancel_btn.pack(side=tk.LEFT, padx=10)
        
        # Focus on first field
        self.name_entry.focus_set()
    
    def center_dialog(self):
        """Center the dialog on parent window"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (450 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (400 // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def ok_clicked(self):
        try:
            name = self.name_entry.get().strip()
            balance = float(self.balance_entry.get() or 0)
            account_type = self.type_var.get()
            
            if not name:
                messagebox.showerror("Error", "Please enter account holder name", parent=self.dialog)
                return
            
            if balance < 500:
                messagebox.showerror("Error", "Minimum balance of ₹500 required", parent=self.dialog)
                return
            
            self.result = (name, balance, account_type)
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid balance amount", parent=self.dialog)
    
    def cancel_clicked(self):
        self.dialog.destroy()

class TransactionDialog:
    """Enhanced transaction dialog"""
    def __init__(self, parent, title, transaction_type):
        self.parent = parent
        self.transaction_type = transaction_type
        self.result = None
        self.create_dialog(title)
    
    def create_dialog(self, title):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.configure(bg='white')
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.center_dialog()
        
        # Header
        header_frame = tk.Frame(self.dialog, bg='#007bff', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, text=f"💳 {title}", 
                               font=('Segoe UI', 16, 'bold'),
                               bg='#007bff', fg='white')
        header_label.pack(pady=15)
        
        # Main form
        form_frame = tk.Frame(self.dialog, bg='white', padx=30, pady=30)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Account ID field
        tk.Label(form_frame, text="🏦 Account ID:", 
                font=('Segoe UI', 11, 'bold'), bg='white', fg='#495057').pack(anchor='w', pady=(0,5))
        self.account_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=30)
        self.account_entry.pack(pady=(0,15), ipady=8)
        
        # For transfer, add destination account
        if self.transaction_type == "transfer":
            tk.Label(form_frame, text="📤 Destination Account ID:", 
                    font=('Segoe UI', 11, 'bold'), bg='white', fg='#495057').pack(anchor='w', pady=(0,5))
            self.dest_account_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=30)
            self.dest_account_entry.pack(pady=(0,15), ipady=8)
        
        # Amount field
        tk.Label(form_frame, text="💰 Amount (₹):", 
                font=('Segoe UI', 11, 'bold'), bg='white', fg='#495057').pack(anchor='w', pady=(0,5))
        self.amount_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=30)
        self.amount_entry.pack(pady=(0,15), ipady=8)
        
        # Description field
        tk.Label(form_frame, text="📝 Description (Optional):", 
                font=('Segoe UI', 11, 'bold'), bg='white', fg='#495057').pack(anchor='w', pady=(0,5))
        self.desc_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=30)
        self.desc_entry.pack(pady=(0,15), ipady=8)
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg='white')
        btn_frame.pack(pady=20)
        
        ok_btn = tk.Button(btn_frame, text="✅ Confirm", command=self.ok_clicked,
                          bg='#28a745', fg='white', font=('Segoe UI', 11, 'bold'),
                          relief='flat', cursor='hand2', padx=20, pady=10)
        ok_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(btn_frame, text="❌ Cancel", command=self.cancel_clicked,
                              bg='#dc3545', fg='white', font=('Segoe UI', 11, 'bold'),
                              relief='flat', cursor='hand2', padx=20, pady=10)
        cancel_btn.pack(side=tk.LEFT, padx=10)
        
        # Focus on first field
        self.account_entry.focus_set()
    
    def center_dialog(self):
        """Center the dialog on parent window"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (500 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (400 // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def ok_clicked(self):
        try:
            account_id = self.account_entry.get().strip()
            amount = float(self.amount_entry.get() or 0)
            description = self.desc_entry.get().strip()
            
            if not account_id:
                messagebox.showerror("Error", "Please enter account ID", parent=self.dialog)
                return
            
            if amount <= 0:
                messagebox.showerror("Error", "Please enter valid amount", parent=self.dialog)
                return
            
            if self.transaction_type == "transfer":
                dest_account = self.dest_account_entry.get().strip()
                if not dest_account:
                    messagebox.showerror("Error", "Please enter destination account ID", parent=self.dialog)
                    return
                self.result = (account_id, dest_account, amount, description)
            else:
                self.result = (account_id, amount, description)
            
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid amount", parent=self.dialog)
    
    def cancel_clicked(self):
        self.dialog.destroy()

class AdminWindow:
    """Admin management window with system controls"""
    def __init__(self, parent, bank, users, products, categories, shop_info):
        self.parent = parent
        self.bank = bank
        self.users = users
        self.products = products
        self.categories = categories
        self.shop_info = shop_info
        self.create_admin_window()
    
    def create_admin_window(self):
        """Create the main admin window"""
        self.admin_window = tk.Toplevel(self.parent)
        self.admin_window.title("🔐 Admin Control Panel")
        self.admin_window.geometry("1000x700")
        self.admin_window.configure(bg='#f8f9fa')
        self.admin_window.transient(self.parent)
        self.admin_window.grab_set()
        
        # Center the window
        self.center_window()
        
        # Header
        header_frame = tk.Frame(self.admin_window, bg='#dc3545', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, text="🔐 Admin Control Panel", 
                               font=('Segoe UI', 18, 'bold'),
                               bg='#dc3545', fg='white')
        header_label.pack(expand=True)
        
        # Create admin tabs
        self.create_admin_tabs()
    
    def center_window(self):
        """Center the admin window"""
        self.admin_window.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (1000 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (700 // 2)
        self.admin_window.geometry(f"+{x}+{y}")
    
    def create_admin_tabs(self):
        """Create all admin tabs"""
        # Notebook for admin tabs
        self.admin_notebook = ttk.Notebook(self.admin_window)
        self.admin_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Overview tab
        overview_frame = tk.Frame(self.admin_notebook, bg='white')
        self.admin_notebook.add(overview_frame, text="📊 Overview")
        
        # Users tab
        self.users_frame = tk.Frame(self.admin_notebook, bg='white')
        self.admin_notebook.add(self.users_frame, text="👥 Users")
        
        # Products tab
        self.products_frame = tk.Frame(self.admin_notebook, bg='white')
        self.admin_notebook.add(self.products_frame, text="📦 Products")
        
        # Transactions tab
        self.transactions_frame = tk.Frame(self.admin_notebook, bg='white')
        self.admin_notebook.add(self.transactions_frame, text="💰 Transactions")
        
        # Settings tab
        self.settings_frame = tk.Frame(self.admin_notebook, bg='white')
        self.admin_notebook.add(self.settings_frame, text="⚙️ Settings")
        
        # Initialize each tab
        self.create_overview_tab(overview_frame)
        self.create_users_tab(self.users_frame)
        self.create_products_tab(self.products_frame)
        self.create_transactions_tab(self.transactions_frame)
        self.create_settings_tab(self.settings_frame)
    
    def create_overview_tab(self, frame):
        """Create overview tab with system statistics"""
        # Header
        header_frame = tk.Frame(frame, bg='white')
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(header_frame, text="📊 System Overview", 
                font=('Segoe UI', 18, 'bold'),
                bg='white', fg='#2c3e50').pack(anchor='w')
        
        # Statistics cards
        stats_frame = tk.Frame(frame, bg='white')
        stats_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Create stat cards
        self.create_stat_card(stats_frame, "👥 Total Users", str(len(self.users)), "#3498db", 0, 0)
        self.create_stat_card(stats_frame, "🏦 Total Accounts", str(len(self.bank.accounts)), "#2ecc71", 0, 1)
        self.create_stat_card(stats_frame, "📦 Total Products", str(len(self.products)), "#e74c3c", 1, 0)
        self.create_stat_card(stats_frame, "💰 Total Transactions", str(len(self.bank.transactions)), "#f39c12", 1, 1)
    
    def create_stat_card(self, parent, title, value, color, row, col):
        """Create a statistics card"""
        card_frame = tk.Frame(parent, bg=color, relief='raised', bd=2)
        card_frame.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
        
        parent.grid_columnconfigure(col, weight=1)
        parent.grid_rowconfigure(row, weight=1)
        
        tk.Label(card_frame, text=title, font=('Segoe UI', 12, 'bold'),
                bg=color, fg='white').pack(pady=(10, 5))
        
        tk.Label(card_frame, text=value, font=('Segoe UI', 20, 'bold'),
                bg=color, fg='white').pack(pady=(0, 10))
        
        # Set minimum size
        card_frame.config(width=200, height=100)
        card_frame.pack_propagate(False)
    
    def create_users_tab(self, frame):
        """Create users management tab with full CRUD operations"""
        # Header
        header_frame = tk.Frame(frame, bg='white')
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(header_frame, text="👥 User Management", 
                font=('Segoe UI', 18, 'bold'),
                bg='white', fg='#2c3e50').pack(side=tk.LEFT)
        
        # Action buttons
        btn_frame = tk.Frame(header_frame, bg='white')
        btn_frame.pack(side=tk.RIGHT)
        
        tk.Button(btn_frame, text="➕ Add User", command=self.add_user_dialog,
                 bg='#28a745', fg='white', font=('Segoe UI', 10, 'bold'),
                 relief='flat', cursor='hand2', padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_users_list,
                 bg='#6c757d', fg='white', font=('Segoe UI', 10, 'bold'),
                 relief='flat', cursor='hand2', padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        # Search frame
        search_frame = tk.Frame(frame, bg='white')
        search_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(search_frame, text="🔍 Search Users:", 
                font=('Segoe UI', 12, 'bold'),
                bg='white').pack(side=tk.LEFT)
        
        self.user_search_var = tk.StringVar()
        self.user_search_var.trace('w', self.filter_users_admin)
        
        search_entry = tk.Entry(search_frame, textvariable=self.user_search_var,
                               font=('Segoe UI', 12), width=30)
        search_entry.pack(side=tk.LEFT, padx=10)
        search_entry.insert(0, "Search by name, email, or role...")
        search_entry.config(fg='gray')
        
        # Clear search button
        clear_btn = tk.Button(search_frame, text="❌", command=self.clear_user_search,
                             bg='#f8f9fa', fg='#6c757d', font=('Segoe UI', 10),
                             relief='flat', cursor='hand2', padx=5, pady=2)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Search status label
        self.user_search_status = tk.Label(search_frame, text="", 
                                          font=('Segoe UI', 10), bg='white', fg='#6c757d')
        self.user_search_status.pack(side=tk.LEFT, padx=10)
        
        # Bind focus events for placeholder
        def on_focus_in(event):
            if search_entry.get() == "Search by name, email, or role...":
                search_entry.delete(0, tk.END)
                search_entry.config(fg='black')
        
        def on_focus_out(event):
            if search_entry.get() == "":
                search_entry.insert(0, "Search by name, email, or role...")
                search_entry.config(fg='gray')
        
        search_entry.bind('<FocusIn>', on_focus_in)
        search_entry.bind('<FocusOut>', on_focus_out)
        
        # Keyboard shortcut for search
        def focus_user_search(event):
            search_entry.focus_set()
            if search_entry.get() == "Search by name, email, or role...":
                search_entry.delete(0, tk.END)
                search_entry.config(fg='black')
        
        frame.bind('<Control-f>', focus_user_search)
        frame.focus_set()  # Allow frame to receive key events
        
        # Users table
        table_frame = tk.Frame(frame, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create treeview for users
        columns = ('Email', 'Name', 'Role', 'Status')
        self.users_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Define headings
        for col in columns:
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to edit
        self.users_tree.bind('<Double-1>', self.edit_user_dialog)
        
        # Context menu for users
        self.create_users_context_menu()
        
        # Load users
        self.refresh_users_list()
    
    def create_products_tab(self, frame):
        """Create products management tab with full CRUD operations"""
        # Header
        header_frame = tk.Frame(frame, bg='white')
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(header_frame, text="📦 Product Management", 
                font=('Segoe UI', 18, 'bold'),
                bg='white', fg='#2c3e50').pack(side=tk.LEFT)
        
        # Action buttons
        btn_frame = tk.Frame(header_frame, bg='white')
        btn_frame.pack(side=tk.RIGHT)
        
        tk.Button(btn_frame, text="➕ Add Product", command=self.add_product_dialog,
                 bg='#28a745', fg='white', font=('Segoe UI', 10, 'bold'),
                 relief='flat', cursor='hand2', padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="� Fix Images", command=self.fix_product_images,
                 bg='#fd7e14', fg='white', font=('Segoe UI', 10, 'bold'),
                 relief='flat', cursor='hand2', padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="�🔄 Refresh", command=self.refresh_products_list,
                 bg='#6c757d', fg='white', font=('Segoe UI', 10, 'bold'),
                 relief='flat', cursor='hand2', padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        # Search frame
        search_frame = tk.Frame(frame, bg='white')
        search_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(search_frame, text="🔍 Search Products:", 
                font=('Segoe UI', 12, 'bold'),
                bg='white').pack(side=tk.LEFT)
        
        self.product_search_var = tk.StringVar()
        self.product_search_var.trace('w', self.filter_products_admin)
        
        product_search_entry = tk.Entry(search_frame, textvariable=self.product_search_var,
                                       font=('Segoe UI', 12), width=30)
        product_search_entry.pack(side=tk.LEFT, padx=10)
        product_search_entry.insert(0, "Search by name, ID, or category...")
        product_search_entry.config(fg='gray')
        
        # Clear search button
        clear_product_btn = tk.Button(search_frame, text="❌", command=self.clear_product_search,
                                     bg='#f8f9fa', fg='#6c757d', font=('Segoe UI', 10),
                                     relief='flat', cursor='hand2', padx=5, pady=2)
        clear_product_btn.pack(side=tk.LEFT, padx=5)
        
        # Search status label
        self.product_search_status = tk.Label(search_frame, text="", 
                                             font=('Segoe UI', 10), bg='white', fg='#6c757d')
        self.product_search_status.pack(side=tk.LEFT, padx=10)
        
        # Bind focus events for placeholder
        def on_product_focus_in(event):
            if product_search_entry.get() == "Search by name, ID, or category...":
                product_search_entry.delete(0, tk.END)
                product_search_entry.config(fg='black')
        
        def on_product_focus_out(event):
            if product_search_entry.get() == "":
                product_search_entry.insert(0, "Search by name, ID, or category...")
                product_search_entry.config(fg='gray')
        
        product_search_entry.bind('<FocusIn>', on_product_focus_in)
        product_search_entry.bind('<FocusOut>', on_product_focus_out)
        
        # Keyboard shortcut for search
        def focus_product_search(event):
            product_search_entry.focus_set()
            if product_search_entry.get() == "Search by name, ID, or category...":
                product_search_entry.delete(0, tk.END)
                product_search_entry.config(fg='black')
        
        frame.bind('<Control-f>', focus_product_search)
        frame.focus_set()  # Allow frame to receive key events
        
        # Products table
        table_frame = tk.Frame(frame, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create treeview for products
        columns = ('ID', 'Name', 'Category', 'Price', 'Stock')
        self.products_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Define headings
        for col in columns:
            self.products_tree.heading(col, text=col)
            self.products_tree.column(col, width=120)
        
        # Add scrollbar
        scrollbar2 = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=scrollbar2.set)
        
        # Pack treeview and scrollbar
        self.products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to edit
        self.products_tree.bind('<Double-1>', self.edit_product_dialog)
        
        # Context menu for products
        self.create_products_context_menu()
        
        # Load products
        self.refresh_products_list()
    
    def create_transactions_tab(self, frame):
        """Create transactions management tab"""
        # Header
        header_frame = tk.Frame(frame, bg='white')
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(header_frame, text="💰 Transaction Management", 
                font=('Segoe UI', 18, 'bold'),
                bg='white', fg='#2c3e50').pack(side=tk.LEFT)
        
        # Transactions table
        table_frame = tk.Frame(frame, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create treeview for transactions
        columns = ('ID', 'Type', 'Amount', 'From', 'To', 'Date')
        self.transactions_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Define headings
        for col in columns:
            self.transactions_tree.heading(col, text=col)
            self.transactions_tree.column(col, width=120)
        
        # Add scrollbar
        scrollbar3 = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.transactions_tree.yview)
        self.transactions_tree.configure(yscrollcommand=scrollbar3.set)
        
        # Pack treeview and scrollbar
        self.transactions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar3.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load transactions
        self.refresh_transactions_list()
    
    def create_settings_tab(self, frame):
        """Create settings management tab"""
        # Header
        header_frame = tk.Frame(frame, bg='white')
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(header_frame, text="⚙️ System Settings", 
                font=('Segoe UI', 18, 'bold'),
                bg='white', fg='#2c3e50').pack(anchor='w')
        
        # Settings form
        settings_frame = tk.Frame(frame, bg='white')
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Shop info section
        shop_frame = tk.LabelFrame(settings_frame, text="🏪 Shop Information", 
                                  font=('Segoe UI', 12, 'bold'), bg='white', padx=10, pady=10)
        shop_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(shop_frame, text="Shop Name:", font=('Segoe UI', 11), bg='white').grid(row=0, column=0, sticky='w', pady=5)
        self.shop_name_entry = tk.Entry(shop_frame, font=('Segoe UI', 11), width=30)
        self.shop_name_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(shop_frame, text="Contact:", font=('Segoe UI', 11), bg='white').grid(row=1, column=0, sticky='w', pady=5)
        self.shop_contact_entry = tk.Entry(shop_frame, font=('Segoe UI', 11), width=30)
        self.shop_contact_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # Load current settings
        self.load_shop_settings()
        
        # Save button
        tk.Button(settings_frame, text="💾 Save Settings", command=self.save_shop_settings,
                 bg='#28a745', fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2', padx=20, pady=8).pack(pady=20)
    
    def add_user_dialog(self):
        """Dialog to add new user"""
        dialog = tk.Toplevel(self.admin_window)
        dialog.title("➕ Add New User")
        dialog.geometry("500x450")
        dialog.configure(bg='white')
        dialog.transient(self.admin_window)
        dialog.grab_set()
        
        # Center dialog
        x = self.admin_window.winfo_x() + (self.admin_window.winfo_width() // 2) - 250
        y = self.admin_window.winfo_y() + (self.admin_window.winfo_height() // 2) - 225
        dialog.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(dialog, bg='#28a745', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="➕ Add New User", 
                font=('Segoe UI', 16, 'bold'),
                bg='#28a745', fg='white').pack(pady=15)
        
        # Form
        form_frame = tk.Frame(dialog, bg='white')
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Name
        tk.Label(form_frame, text="👤 Full Name:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        name_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=40)
        name_entry.pack(pady=(0,15), ipady=5)
        
        # Email
        tk.Label(form_frame, text="📧 Email:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        email_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=40)
        email_entry.pack(pady=(0,15), ipady=5)
        
        # Password
        tk.Label(form_frame, text="🔒 Password:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        password_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=40, show='*')
        password_entry.pack(pady=(0,15), ipady=5)
        
        # Role
        tk.Label(form_frame, text="🔐 Role:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        role_var = tk.StringVar(value="user")
        role_combo = ttk.Combobox(form_frame, textvariable=role_var,
                                 values=["user", "admin"], state="readonly", width=37)
        role_combo.pack(pady=(0,15), ipady=5)
        
        # Status
        status_var = tk.BooleanVar(value=True)
        tk.Checkbutton(form_frame, text="🟢 Active User", variable=status_var,
                      font=('Segoe UI', 11), bg='white').pack(anchor='w', pady=10)
        
        def save_user():
            try:
                name = name_entry.get().strip()
                email = email_entry.get().strip().lower()
                password = password_entry.get()
                role = role_var.get()
                is_active = status_var.get()
                
                if not all([name, email, password]):
                    messagebox.showerror("Error", "Please fill all required fields", parent=dialog)
                    return
                
                if not validate_email(email):
                    messagebox.showerror("Error", "Please enter a valid email", parent=dialog)
                    return
                
                if len(password) < 6:
                    messagebox.showerror("Error", "Password must be at least 6 characters", parent=dialog)
                    return
                
                if email in self.users:
                    messagebox.showerror("Error", "Email already exists", parent=dialog)
                    return
                
                # Create user
                self.users[email] = {
                    'name': name,
                    'email': email,
                    'password': hash_password(password),
                    'role': role,
                    'is_active': is_active,
                    'created_date': datetime.now().isoformat()
                }
                
                # Save to file
                save_json(FILES['USERS'], self.users)
                
                dialog.destroy()
                self.refresh_users_list()
                messagebox.showinfo("Success", f"User '{name}' added successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add user: {str(e)}", parent=dialog)
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg='white')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="✅ Save User", command=save_user,
                 bg='#28a745', fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2', padx=20, pady=8).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy,
                 bg='#dc3545', fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2', padx=20, pady=8).pack(side=tk.LEFT, padx=10)
        
        # Focus on name field
        name_entry.focus_set()
    
    def edit_user_dialog(self, event=None):
        """Dialog to edit existing user"""
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user to edit")
            return
        
        user_email = self.users_tree.item(selected[0])['values'][0]
        user_data = self.users.get(user_email)
        
        if not user_data:
            messagebox.showerror("Error", "User not found")
            return
        
        dialog = tk.Toplevel(self.admin_window)
        dialog.title("✏️ Edit User")
        dialog.geometry("500x500")
        dialog.configure(bg='white')
        dialog.transient(self.admin_window)
        dialog.grab_set()
        
        # Center dialog
        x = self.admin_window.winfo_x() + (self.admin_window.winfo_width() // 2) - 250
        y = self.admin_window.winfo_y() + (self.admin_window.winfo_height() // 2) - 225
        dialog.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(dialog, bg='#007bff', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="✏️ Edit User", 
                font=('Segoe UI', 16, 'bold'),
                bg='#007bff', fg='white').pack(pady=15)
        
        # Form
        form_frame = tk.Frame(dialog, bg='white')
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Name
        tk.Label(form_frame, text="👤 Full Name:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        name_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=40)
        name_entry.pack(pady=(0,15), ipady=5)
        name_entry.insert(0, user_data.get('name', ''))
        
        # Email (read-only)
        tk.Label(form_frame, text="📧 Email:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        email_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=40, state='readonly')
        email_entry.pack(pady=(0,15), ipady=5)
        email_entry.config(state='normal')
        email_entry.insert(0, user_data.get('email', ''))
        email_entry.config(state='readonly')
        
        # Role
        tk.Label(form_frame, text="🔐 Role:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        role_var = tk.StringVar(value=user_data.get('role', 'user'))
        role_combo = ttk.Combobox(form_frame, textvariable=role_var,
                                 values=["user", "admin"], state="readonly", width=37)
        role_combo.pack(pady=(0,15), ipady=5)
        
        # Status
        status_var = tk.BooleanVar(value=user_data.get('is_active', True))
        tk.Checkbutton(form_frame, text="🟢 Active User", variable=status_var,
                      font=('Segoe UI', 11), bg='white').pack(anchor='w', pady=10)
        
        def update_user():
            try:
                name = name_entry.get().strip()
                role = role_var.get()
                is_active = status_var.get()
                
                if not name:
                    messagebox.showerror("Error", "Please enter user name", parent=dialog)
                    return
                
                # Update user data
                self.users[user_email].update({
                    'name': name,
                    'role': role,
                    'is_active': is_active,
                    'updated_date': datetime.now().isoformat()
                })
                
                # Save to file
                save_json(FILES['USERS'], self.users)
                
                dialog.destroy()
                self.refresh_users_list()
                messagebox.showinfo("Success", f"User '{name}' updated successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update user: {str(e)}", parent=dialog)
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg='white')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="✅ Update User", command=update_user,
                 bg='#007bff', fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2', padx=20, pady=8).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy,
                 bg='#dc3545', fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2', padx=20, pady=8).pack(side=tk.LEFT, padx=10)
        
        # Focus on name field
        name_entry.focus_set()
    
    def create_users_context_menu(self):
        """Create context menu for users table"""
        self.users_context_menu = tk.Menu(self.admin_window, tearoff=0)
        self.users_context_menu.add_command(label="✏️ Edit User", command=self.edit_user_dialog)
        self.users_context_menu.add_command(label="🔒 Toggle Status", command=self.toggle_user_status)
        self.users_context_menu.add_command(label="🔑 Reset Password", command=self.reset_user_password)
        self.users_context_menu.add_separator()
        self.users_context_menu.add_command(label="🗑️ Delete User", command=self.delete_user)
        
        def show_context_menu(event):
            try:
                self.users_context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.users_context_menu.grab_release()
        
        self.users_tree.bind('<Button-3>', show_context_menu)

    def delete_user(self):
        """Delete selected user"""
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user to delete")
            return
        
        user_email = self.users_tree.item(selected[0])['values'][0]
        user_data = self.users.get(user_email)
        
        if not user_data:
            messagebox.showerror("Error", "User not found")
            return
        
        # Prevent deleting current admin user
        if user_email == "admin@banking.com":
            messagebox.showerror("Error", "Cannot delete the default admin user")
            return
        
        # Confirm deletion
        result = messagebox.askyesno("Confirm Delete", 
                                   f"Are you sure you want to delete user '{user_data['name']}'?\n\n"
                                   f"This action cannot be undone!",
                                   icon='warning')
        
        if result:
            try:
                # Remove user
                del self.users[user_email]
                
                # Save to file
                save_json(FILES['USERS'], self.users)
                
                self.refresh_users_list()
                messagebox.showinfo("Success", f"User '{user_data['name']}' deleted successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete user: {str(e)}")

    def toggle_user_status(self):
        """Toggle user active/inactive status"""
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user")
            return
        
        user_email = self.users_tree.item(selected[0])['values'][0]
        user_data = self.users.get(user_email)
        
        if not user_data:
            messagebox.showerror("Error", "User not found")
            return
        
        # Prevent deactivating current admin user
        if user_email == "admin@banking.com":
            messagebox.showerror("Error", "Cannot deactivate the default admin user")
            return
        
        try:
            # Toggle status
            current_status = user_data.get('is_active', True)
            new_status = not current_status
            
            self.users[user_email]['is_active'] = new_status
            self.users[user_email]['updated_date'] = datetime.now().isoformat()
            
            # Save to file
            save_json(FILES['USERS'], self.users)
            
            self.refresh_users_list()
            
            status_text = "activated" if new_status else "deactivated"
            messagebox.showinfo("Success", f"User '{user_data['name']}' {status_text} successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle user status: {str(e)}")

    def reset_user_password(self):
        """Reset user password"""
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user")
            return
        
        user_email = self.users_tree.item(selected[0])['values'][0]
        user_data = self.users.get(user_email)
        
        if not user_data:
            messagebox.showerror("Error", "User not found")
            return
        
        # Simple password reset
        new_password = simpledialog.askstring("Reset Password", 
                                             f"Enter new password for {user_data['name']}:", 
                                             show='*')
        
        if new_password and len(new_password) >= 6:
            try:
                self.users[user_email]['password'] = hash_password(new_password)
                self.users[user_email]['updated_date'] = datetime.now().isoformat()
                save_json(FILES['USERS'], self.users)
                messagebox.showinfo("Success", f"Password reset successfully for '{user_data['name']}'!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset password: {str(e)}")
        elif new_password:
            messagebox.showerror("Error", "Password must be at least 6 characters")

    def filter_users_admin(self, *args):
        """Filter users based on search text in admin panel"""
        search_text = self.user_search_var.get().lower()
        
        # Skip filtering if placeholder text
        if search_text == "search by name, email, or role...":
            return
        
        # Clear existing items
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        # Add filtered users
        count = 0
        for email, user_data in self.users.items():
            if (not search_text or 
                search_text in email.lower() or 
                search_text in user_data.get('name', '').lower() or
                search_text in user_data.get('role', '').lower()):
                
                status = "🟢 Active" if user_data.get('is_active', True) else "🔴 Inactive"
                self.users_tree.insert('', 'end', values=(
                    email,
                    user_data.get('name', ''),
                    user_data.get('role', 'user').title(),
                    status
                ))
                count += 1
        
        # Update search status
        if hasattr(self, 'user_search_status'):
            if search_text:
                self.user_search_status.config(text=f"Found {count} user(s)")
            else:
                self.user_search_status.config(text="")

    def clear_user_search(self):
        """Clear user search"""
        self.user_search_var.set("")
        if hasattr(self, 'user_search_status'):
            self.user_search_status.config(text="")
        self.refresh_users_list()
    
    def fix_product_images(self):
        """Fix broken product images by replacing them with working placeholders"""
        try:
            # Count products with images
            total_products = len(self.products)
            products_with_issues = 0
            fixed_products = 0
            
            # Working placeholder images
            working_images = [
                "https://picsum.photos/400/300?random=1",
                "https://picsum.photos/400/300?random=2", 
                "https://picsum.photos/400/300?random=3",
                "https://via.placeholder.com/400x300/4CAF50/ffffff?text=Product+Image+1",
                "https://via.placeholder.com/400x300/2196F3/ffffff?text=Product+Image+2",
                "https://via.placeholder.com/400x300/FF9800/ffffff?text=Product+Image+3",
                "https://dummyimage.com/400x300/ff6b6b/ffffff&text=Sample+1",
                "https://dummyimage.com/400x300/4ecdc4/ffffff&text=Sample+2"
            ]
            
            response = messagebox.askyesno(
                "Fix Product Images",
                f"This will check all {total_products} products and fix broken image URLs.\n\n"
                "Would you like to proceed?",
                parent=self.admin_window
            )
            
            if not response:
                return
            
            # Create progress dialog
            progress_window = tk.Toplevel(self.admin_window)
            progress_window.title("Fixing Product Images")
            progress_window.geometry("500x200")
            progress_window.configure(bg='white')
            progress_window.transient(self.admin_window)
            progress_window.grab_set()
            
            # Center the window
            x = self.admin_window.winfo_x() + (self.admin_window.winfo_width() // 2) - 250
            y = self.admin_window.winfo_y() + (self.admin_window.winfo_height() // 2) - 100
            progress_window.geometry(f"+{x}+{y}")
            
            # Progress label
            progress_label = tk.Label(progress_window, text="Starting image fix process...",
                                    font=('Segoe UI', 12), bg='white')
            progress_label.pack(pady=20)
            
            # Progress bar
            from tkinter import ttk
            progress_bar = ttk.Progressbar(progress_window, length=400, mode='determinate')
            progress_bar.pack(pady=10)
            progress_bar['maximum'] = total_products
            
            # Details label
            details_label = tk.Label(progress_window, text="",
                                   font=('Segoe UI', 10), bg='white', fg='#666')
            details_label.pack(pady=10)
            
            def fix_images():
                nonlocal products_with_issues, fixed_products
                
                for i, product in enumerate(self.products):
                    # Update progress
                    progress_bar['value'] = i + 1
                    progress_label.config(text=f"Checking product {i+1}/{total_products}: {product.get('name', 'Unknown')}")
                    details_label.config(text=f"Found {products_with_issues} issues, fixed {fixed_products}")
                    progress_window.update()
                    
                    # Check if product has image issues
                    needs_fix = False
                    current_images = product.get('images', [])
                    
                    if not current_images:
                        needs_fix = True
                        products_with_issues += 1
                    else:
                        # Check for broken URLs or missing files
                        for img_url in current_images:
                            if not img_url or img_url.strip() == "":
                                needs_fix = True
                                break
                            elif img_url.startswith('C:') and not os.path.exists(img_url):
                                needs_fix = True  # Local file doesn't exist
                                break
                            elif 'placeholder.com' in img_url and 'No+Image' in img_url:
                                needs_fix = True  # Has placeholder indicating no image
                                break
                    
                    if needs_fix:
                        products_with_issues += 1
                        # Fix the product
                        import random
                        # Assign 2-3 random working images
                        num_images = random.randint(2, 3)
                        new_images = random.sample(working_images, num_images)
                        product['images'] = new_images
                        fixed_products += 1
                        print(f"✅ Fixed images for product: {product.get('name', 'Unknown')}")
                
                # Save the updated products
                if fixed_products > 0:
                    save_json(FILES['PRODUCTS'], self.products)
                    progress_label.config(text="✅ Image fix completed!")
                else:
                    progress_label.config(text="✅ No issues found!")
                
                details_label.config(text=f"Processed {total_products} products - Fixed {fixed_products} issues")
                
                # Close button
                close_btn = tk.Button(progress_window, text="Close", 
                                    command=progress_window.destroy,
                                    bg='#28a745', fg='white', font=('Segoe UI', 10, 'bold'),
                                    relief='flat', cursor='hand2', padx=20, pady=5)
                close_btn.pack(pady=20)
                
                # Refresh the products display
                if fixed_products > 0:
                    self.refresh_products_list()
                    messagebox.showinfo(
                        "Success", 
                        f"✅ Fixed {fixed_products} products with image issues!\n\n"
                        f"• Total products checked: {total_products}\n"
                        f"• Products with issues: {products_with_issues}\n"
                        f"• Products fixed: {fixed_products}",
                        parent=self.admin_window
                    )
            
            # Start fixing images after a short delay
            progress_window.after(500, fix_images)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fix product images:\n{str(e)}", parent=self.admin_window)
    
    def create_products_context_menu(self):
        """Create context menu for products table"""
        self.products_context_menu = tk.Menu(self.admin_window, tearoff=0)
        self.products_context_menu.add_command(label="✏️ Edit Product", command=self.edit_product_dialog)
        self.products_context_menu.add_command(label="📦 Update Stock", command=self.update_product_stock)
        self.products_context_menu.add_separator()
        self.products_context_menu.add_command(label="🗑️ Delete Product", command=self.delete_product)
        
        def show_context_menu(event):
            try:
                self.products_context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.products_context_menu.grab_release()
        
        self.products_tree.bind('<Button-3>', show_context_menu)

    def add_product_dialog(self):
        """Dialog to add new product with image management"""
        dialog = tk.Toplevel(self.admin_window)
        dialog.title("➕ Add New Product")
        dialog.geometry("800x750")
        dialog.configure(bg='white')
        dialog.transient(self.admin_window)
        dialog.grab_set()
        
        # Center dialog
        x = self.admin_window.winfo_x() + (self.admin_window.winfo_width() // 2) - 400
        y = self.admin_window.winfo_y() + (self.admin_window.winfo_height() // 2) - 375
        dialog.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(dialog, bg='#28a745', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="➕ Add New Product", 
                font=('Segoe UI', 16, 'bold'),
                bg='#28a745', fg='white').pack(pady=15)
        
        # Create scrollable form
        canvas = tk.Canvas(dialog, bg='white')
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Form
        form_frame = tk.Frame(scrollable_frame, bg='white')
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Product Name
        tk.Label(form_frame, text="📦 Product Name:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        name_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=50)
        name_entry.pack(pady=(0,15), ipady=5)
        
        # Category
        tk.Label(form_frame, text="🏷️ Category:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        category_var = tk.StringVar(value="Electronics")
        categories = ["Electronics", "Clothing", "Books", "Home & Garden", "Sports", "Food & Beverages", "Other"]
        category_combo = ttk.Combobox(form_frame, textvariable=category_var,
                                     values=categories, width=47)
        category_combo.pack(pady=(0,15), ipady=5)
        
        # Price
        tk.Label(form_frame, text="💰 Price (₹):", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        price_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=50)
        price_entry.pack(pady=(0,15), ipady=5)
        
        # Stock
        tk.Label(form_frame, text="📊 Stock Quantity:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        stock_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=50)
        stock_entry.pack(pady=(0,15), ipady=5)
        stock_entry.insert(0, "10")  # Default stock
        
        # Description
        tk.Label(form_frame, text="📝 Description:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        desc_text = tk.Text(form_frame, font=('Segoe UI', 11), width=50, height=4)
        desc_text.pack(pady=(0,15))
        
        # Image Management Section
        images_frame = tk.LabelFrame(form_frame, text="🖼️ Product Images", 
                                    font=('Segoe UI', 11, 'bold'), bg='white', 
                                    padx=10, pady=10)
        images_frame.pack(fill=tk.X, pady=(0,15))
        
        # List to store image URLs
        self.temp_images = []
        
        # Image URLs listbox with scrollbar
        images_container = tk.Frame(images_frame, bg='white')
        images_container.pack(fill=tk.X, pady=(0,10))
        
        tk.Label(images_container, text="Image URLs:", 
                font=('Segoe UI', 10, 'bold'), bg='white').pack(anchor='w')
        
        listbox_frame = tk.Frame(images_container, bg='white')
        listbox_frame.pack(fill=tk.X, pady=(5,0))
        
        self.images_listbox = tk.Listbox(listbox_frame, height=4, font=('Segoe UI', 9))
        images_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.images_listbox.yview)
        self.images_listbox.configure(yscrollcommand=images_scrollbar.set)
        
        self.images_listbox.pack(side="left", fill="both", expand=True)
        images_scrollbar.pack(side="right", fill="y")
        
        # Image URL input
        url_frame = tk.Frame(images_frame, bg='white')
        url_frame.pack(fill=tk.X, pady=(10,0))
        
        tk.Label(url_frame, text="Add Image URL or Local File:", 
                font=('Segoe UI', 10, 'bold'), bg='white').pack(anchor='w')
        
        # Help text
        help_text = tk.Label(url_frame, 
                           text="💡 Tip: Use 📁 Browse for local files or enter image URLs (jpg, png, gif, webp)",
                           font=('Segoe UI', 8), bg='white', fg='#666')
        help_text.pack(anchor='w', pady=(2,5))
        
        url_input_frame = tk.Frame(url_frame, bg='white')
        url_input_frame.pack(fill=tk.X, pady=(5,0))
        
        self.image_url_entry = tk.Entry(url_input_frame, font=('Segoe UI', 10), width=40)
        self.image_url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        
        def add_image_url():
            url = self.image_url_entry.get().strip()
            if url:
                if url in self.temp_images:
                    messagebox.showwarning("Warning", "This image URL is already added", parent=dialog)
                    return
                
                # Basic URL validation
                if url.startswith(('http://', 'https://')):
                    # Check if URL seems to be an image
                    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff')
                    if not any(url.lower().endswith(ext) for ext in image_extensions) and '?' not in url:
                        response = messagebox.askyesno(
                            "Confirm", 
                            "This URL doesn't appear to be a direct image link.\nAdd it anyway?",
                            parent=dialog
                        )
                        if not response:
                            return
                elif os.path.exists(url):
                    # Local file path
                    pass
                else:
                    # Neither valid URL nor existing file
                    messagebox.showerror(
                        "Invalid Input", 
                        "Please enter a valid image URL (http/https) or use Browse for local files",
                        parent=dialog
                    )
                    return
                    
                self.temp_images.append(url)
                self.images_listbox.insert(tk.END, f"{len(self.temp_images)}. {url}")
                self.image_url_entry.delete(0, tk.END)
                update_image_buttons()
        
        def remove_selected_image():
            selection = self.images_listbox.curselection()
            if selection:
                index = selection[0]
                self.temp_images.pop(index)
                refresh_images_listbox()
                update_image_buttons()
        
        def refresh_images_listbox():
            self.images_listbox.delete(0, tk.END)
            for i, url in enumerate(self.temp_images):
                self.images_listbox.insert(tk.END, f"{i+1}. {url}")
        
        def update_image_buttons():
            remove_btn.config(state='normal' if self.temp_images else 'disabled')
            clear_btn.config(state='normal' if self.temp_images else 'disabled')
        
        # Image management buttons
        img_btn_frame = tk.Frame(url_input_frame, bg='white')
        img_btn_frame.pack(side=tk.RIGHT)
        
        tk.Button(img_btn_frame, text="➕ Add", command=add_image_url,
                 bg='#28a745', fg='white', font=('Segoe UI', 9, 'bold'),
                 relief='flat', cursor='hand2', padx=10, pady=2).pack(side=tk.LEFT, padx=2)
        
        # Browse for local image file
        def browse_image_file():
            file_path = filedialog.askopenfilename(
                parent=dialog,
                title="Select Image File",
                filetypes=[
                    ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp"),
                    ("JPEG files", "*.jpg *.jpeg"),
                    ("PNG files", "*.png"),
                    ("GIF files", "*.gif"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                # Convert to absolute path and add to list
                abs_path = os.path.abspath(file_path)
                if abs_path not in self.temp_images:
                    self.temp_images.append(abs_path)
                    self.images_listbox.insert(tk.END, f"{len(self.temp_images)}. {abs_path}")
                    update_image_buttons()
                else:
                    messagebox.showwarning("Warning", "This image file is already added", parent=dialog)
        
        tk.Button(img_btn_frame, text="📁 Browse", command=browse_image_file,
                 bg='#007bff', fg='white', font=('Segoe UI', 9, 'bold'),
                 relief='flat', cursor='hand2', padx=10, pady=2).pack(side=tk.LEFT, padx=2)
        
        remove_btn = tk.Button(img_btn_frame, text="➖ Remove", command=remove_selected_image,
                              bg='#dc3545', fg='white', font=('Segoe UI', 9, 'bold'),
                              relief='flat', cursor='hand2', padx=10, pady=2, state='disabled')
        remove_btn.pack(side=tk.LEFT, padx=2)
        
        clear_btn = tk.Button(img_btn_frame, text="🗑️ Clear All", 
                             command=lambda: [self.temp_images.clear(), refresh_images_listbox(), update_image_buttons()],
                             bg='#6c757d', fg='white', font=('Segoe UI', 9, 'bold'),
                             relief='flat', cursor='hand2', padx=10, pady=2, state='disabled')
        clear_btn.pack(side=tk.LEFT, padx=2)
        
        # Bind Enter key to add image
        self.image_url_entry.bind('<Return>', lambda e: add_image_url())
        
        # Quick sample images button
        def add_sample_images():
            # More reliable sample image services
            sample_urls = [
                "https://picsum.photos/400/300?random=1",
                "https://picsum.photos/400/300?random=2", 
                "https://picsum.photos/400/300?random=3",
                "https://via.placeholder.com/400x300/4CAF50/ffffff?text=Sample+Product+1",
                "https://via.placeholder.com/400x300/2196F3/ffffff?text=Sample+Product+2",
                "https://via.placeholder.com/400x300/FF9800/ffffff?text=Sample+Product+3",
                "https://dummyimage.com/400x300/ff6b6b/ffffff&text=Test+Image+1",
                "https://dummyimage.com/400x300/4ecdc4/ffffff&text=Test+Image+2"
            ]
            added_count = 0
            for url in sample_urls:
                if url not in self.temp_images:
                    self.temp_images.append(url)
                    added_count += 1
            
            if added_count > 0:
                refresh_images_listbox()
                update_image_buttons()
                messagebox.showinfo("Success", f"Added {added_count} reliable sample images", parent=dialog)
            else:
                messagebox.showinfo("Info", "All sample images are already added", parent=dialog)
        
        # Test image button
        def test_image_loading():
            """Test if image loading is working with thread-safe implementation"""
            test_url = "https://httpbin.org/image/jpeg"
            
            def test_load():
                """Background thread function for testing image loading"""
                try:
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    response = requests.get(test_url, timeout=10, headers=headers)
                    response.raise_for_status()
                    image = Image.open(BytesIO(response.content))
                    
                    # Schedule success message in main thread
                    def show_success():
                        try:
                            messagebox.showinfo("Success", "✅ Image loading is working correctly!", parent=dialog)
                        except:
                            pass  # Dialog may have been closed
                    
                    self.after_idle(show_success)
                    
                except Exception as e:
                    # Schedule error message in main thread
                    def show_error():
                        try:
                            messagebox.showerror("Error", f"❌ Image loading failed:\n{str(e)}", parent=dialog)
                        except:
                            pass  # Dialog may have been closed
                    
                    self.after_idle(show_error)
            
            try:
                # Show testing message immediately
                messagebox.showinfo("Testing", "🔄 Testing image loading... Please wait", parent=dialog)
                
                # Start background thread
                test_thread = threading.Thread(target=test_load, daemon=True)
                test_thread.start()
                
            except Exception as e:
                messagebox.showerror("Error", f"❌ Test failed:\n{str(e)}", parent=dialog)
        
        # Button frame for sample images and test
        sample_btn_frame = tk.Frame(images_frame, bg='white')
        sample_btn_frame.pack(pady=(10,0))
        
        tk.Button(sample_btn_frame, text="🎨 Add Sample Images", command=add_sample_images,
                 bg='#17a2b8', fg='white', font=('Segoe UI', 10, 'bold'),
                 relief='flat', cursor='hand2', padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(sample_btn_frame, text="🧪 Test Image Loading", command=test_image_loading,
                 bg='#6f42c1', fg='white', font=('Segoe UI', 10, 'bold'),
                 relief='flat', cursor='hand2', padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        def save_product():
            try:
                name = name_entry.get().strip()
                category = category_var.get()
                price = float(price_entry.get() or 0)
                stock = int(stock_entry.get() or 0)
                description = desc_text.get("1.0", tk.END).strip()
                
                if not name:
                    messagebox.showerror("Error", "Please enter product name", parent=dialog)
                    return
                
                if price <= 0:
                    messagebox.showerror("Error", "Please enter valid price", parent=dialog)
                    return
                
                if stock < 0:
                    messagebox.showerror("Error", "Stock quantity cannot be negative", parent=dialog)
                    return
                
                # Generate product ID
                product_id = f"PRD{len(self.products) + 1:04d}"
                
                # Use provided images or default placeholder
                images = self.temp_images.copy() if self.temp_images else [
                    "https://via.placeholder.com/400x300?text=No+Image+1",
                    "https://via.placeholder.com/400x300?text=No+Image+2"
                ]
                
                # Create product
                new_product = {
                    'id': product_id,
                    'name': name,
                    'category': category,
                    'price': price,
                    'stock': stock,
                    'description': description,
                    'images': images,
                    'rating': 0.0,
                    'reviews': 0,
                    'created_date': datetime.now().isoformat(),
                    'created_by': 'admin'
                }
                
                # Add to products list
                self.products.append(new_product)
                
                # Save to file
                save_json(FILES['PRODUCTS'], self.products)
                
                dialog.destroy()
                self.refresh_products_list()
                messagebox.showinfo("Success", f"Product '{name}' added successfully with {len(images)} images!")
                
            except ValueError as e:
                messagebox.showerror("Error", "Please enter valid numeric values for price and stock", parent=dialog)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add product: {str(e)}", parent=dialog)
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg='white')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="✅ Add Product", command=save_product,
                 bg='#28a745', fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2', padx=20, pady=8).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy,
                 bg='#dc3545', fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2', padx=20, pady=8).pack(side=tk.LEFT, padx=10)
        
        # Focus on name field
        name_entry.focus_set()

    def edit_product_dialog(self, event=None):
        """Dialog to edit existing product with image management"""
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a product to edit")
            return
        
        product_id = self.products_tree.item(selected[0])['values'][0]
        product_data = None
        
        # Find product by ID
        for product in self.products:
            if product.get('id') == product_id:
                product_data = product
                break
        
        if not product_data:
            messagebox.showerror("Error", "Product not found")
            return
        
        dialog = tk.Toplevel(self.admin_window)
        dialog.title("✏️ Edit Product")
        dialog.geometry("800x950")
        dialog.configure(bg='white')
        dialog.transient(self.admin_window)
        dialog.grab_set()
        
        # Center dialog
        x = self.admin_window.winfo_x() + (self.admin_window.winfo_width() // 2) - 400
        y = self.admin_window.winfo_y() + (self.admin_window.winfo_height() // 2) - 425
        dialog.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(dialog, bg='#007bff', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="✏️ Edit Product", 
                font=('Segoe UI', 16, 'bold'),
                bg='#007bff', fg='white').pack(pady=15)
        
        # Create scrollable form
        canvas = tk.Canvas(dialog, bg='white')
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Form
        form_frame = tk.Frame(scrollable_frame, bg='white')
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Product ID (read-only)
        tk.Label(form_frame, text="🆔 Product ID:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        id_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=50, state='readonly')
        id_entry.pack(pady=(0,15), ipady=5)
        id_entry.config(state='normal')
        id_entry.insert(0, product_data.get('id', ''))
        id_entry.config(state='readonly')
        
        # Product Name
        tk.Label(form_frame, text="📦 Product Name:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        name_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=50)
        name_entry.pack(pady=(0,15), ipady=5)
        name_entry.insert(0, product_data.get('name', ''))
        
        # Category
        tk.Label(form_frame, text="🏷️ Category:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        category_var = tk.StringVar(value=product_data.get('category', 'Electronics'))
        categories = ["Electronics", "Clothing", "Books", "Home & Garden", "Sports", "Food & Beverages", "Other"]
        category_combo = ttk.Combobox(form_frame, textvariable=category_var,
                                     values=categories, width=47)
        category_combo.pack(pady=(0,15), ipady=5)
        
        # Price
        tk.Label(form_frame, text="💰 Price (₹):", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        price_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=50)
        price_entry.pack(pady=(0,15), ipady=5)
        price_entry.insert(0, str(product_data.get('price', 0)))
        
        # Stock
        tk.Label(form_frame, text="📊 Stock Quantity:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        stock_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=50)
        stock_entry.pack(pady=(0,15), ipady=5)
        stock_entry.insert(0, str(product_data.get('stock', 0)))
        
        # Description
        tk.Label(form_frame, text="📝 Description:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        desc_text = tk.Text(form_frame, font=('Segoe UI', 11), width=50, height=4)
        desc_text.pack(pady=(0,15))
        desc_text.insert("1.0", product_data.get('description', ''))
        
        # Image Management Section
        images_frame = tk.LabelFrame(form_frame, text="🖼️ Product Images", 
                                    font=('Segoe UI', 11, 'bold'), bg='white', 
                                    padx=10, pady=10)
        images_frame.pack(fill=tk.X, pady=(0,15))
        
        # Load existing images
        existing_images = product_data.get('images', [])
        if isinstance(existing_images, str):
            # Handle old single image format
            existing_images = [existing_images] if existing_images else []
        elif not existing_images and product_data.get('image'):
            # Handle old image field
            existing_images = [product_data.get('image')]
        
        self.temp_images = existing_images.copy()
        
        # Image URLs listbox with scrollbar
        images_container = tk.Frame(images_frame, bg='white')
        images_container.pack(fill=tk.X, pady=(0,10))
        
        tk.Label(images_container, text="Current Images:", 
                font=('Segoe UI', 10, 'bold'), bg='white').pack(anchor='w')
        
        listbox_frame = tk.Frame(images_container, bg='white')
        listbox_frame.pack(fill=tk.X, pady=(5,0))
        
        self.images_listbox = tk.Listbox(listbox_frame, height=4, font=('Segoe UI', 9))
        images_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.images_listbox.yview)
        self.images_listbox.configure(yscrollcommand=images_scrollbar.set)
        
        self.images_listbox.pack(side="left", fill="both", expand=True)
        images_scrollbar.pack(side="right", fill="y")
        
        # Populate existing images
        def refresh_images_listbox():
            self.images_listbox.delete(0, tk.END)
            for i, url in enumerate(self.temp_images):
                self.images_listbox.insert(tk.END, f"{i+1}. {url}")
        
        refresh_images_listbox()
        
        # Image URL input
        url_frame = tk.Frame(images_frame, bg='white')
        url_frame.pack(fill=tk.X, pady=(10,0))
        
        tk.Label(url_frame, text="Add/Update Image URL:", 
                font=('Segoe UI', 10), bg='white').pack(anchor='w')
        
        url_input_frame = tk.Frame(url_frame, bg='white')
        url_input_frame.pack(fill=tk.X, pady=(5,0))
        
        self.image_url_entry = tk.Entry(url_input_frame, font=('Segoe UI', 10), width=40)
        self.image_url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        
        def add_image_url():
            url = self.image_url_entry.get().strip()
            if url:
                if url in self.temp_images:
                    messagebox.showwarning("Warning", "This image URL is already added", parent=dialog)
                    return
                    
                self.temp_images.append(url)
                refresh_images_listbox()
                self.image_url_entry.delete(0, tk.END)
                update_image_buttons()
        
        def remove_selected_image():
            selection = self.images_listbox.curselection()
            if selection:
                index = selection[0]
                self.temp_images.pop(index)
                refresh_images_listbox()
                update_image_buttons()
        
        def update_image_buttons():
            remove_btn.config(state='normal' if self.temp_images else 'disabled')
            clear_btn.config(state='normal' if self.temp_images else 'disabled')
        
        # Image management buttons
        img_btn_frame = tk.Frame(url_input_frame, bg='white')
        img_btn_frame.pack(side=tk.RIGHT)
        
        tk.Button(img_btn_frame, text="➕ Add", command=add_image_url,
                 bg='#28a745', fg='white', font=('Segoe UI', 9, 'bold'),
                 relief='flat', cursor='hand2', padx=10, pady=2).pack(side=tk.LEFT, padx=2)
        
        remove_btn = tk.Button(img_btn_frame, text="➖ Remove", command=remove_selected_image,
                              bg='#dc3545', fg='white', font=('Segoe UI', 9, 'bold'),
                              relief='flat', cursor='hand2', padx=10, pady=2)
        remove_btn.pack(side=tk.LEFT, padx=2)
        
        clear_btn = tk.Button(img_btn_frame, text="🗑️ Clear All", 
                             command=lambda: [self.temp_images.clear(), refresh_images_listbox(), update_image_buttons()],
                             bg='#6c757d', fg='white', font=('Segoe UI', 9, 'bold'),
                             relief='flat', cursor='hand2', padx=10, pady=2)
        clear_btn.pack(side=tk.LEFT, padx=2)
        
        # Initial button states
        update_image_buttons()
        
        # Bind Enter key to add image
        self.image_url_entry.bind('<Return>', lambda e: add_image_url())
        
        def update_product():
            try:
                name = name_entry.get().strip()
                category = category_var.get()
                price = float(price_entry.get() or 0)
                stock = int(stock_entry.get() or 0)
                description = desc_text.get("1.0", tk.END).strip()
                
                if not name:
                    messagebox.showerror("Error", "Please enter product name", parent=dialog)
                    return
                
                if price <= 0:
                    messagebox.showerror("Error", "Please enter valid price", parent=dialog)
                    return
                
                if stock < 0:
                    messagebox.showerror("Error", "Stock quantity cannot be negative", parent=dialog)
                    return
                
                # Update product data
                product_data.update({
                    'name': name,
                    'category': category,
                    'price': price,
                    'stock': stock,
                    'description': description,
                    'images': self.temp_images.copy() if self.temp_images else ["https://via.placeholder.com/400x300?text=No+Image"],
                    'updated_date': datetime.now().isoformat(),
                    'updated_by': 'admin'
                })
                
                # Remove old single image field if it exists
                if 'image' in product_data:
                    del product_data['image']
                
                # Save to file
                save_json(FILES['PRODUCTS'], self.products)
                
                dialog.destroy()
                self.refresh_products_list()
                messagebox.showinfo("Success", f"Product '{name}' updated successfully with {len(self.temp_images)} images!")
                
            except ValueError as e:
                messagebox.showerror("Error", "Please enter valid numeric values for price and stock", parent=dialog)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update product: {str(e)}", parent=dialog)
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg='white')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="✅ Update Product", command=update_product,
                 bg='#007bff', fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2', padx=20, pady=8).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy,
                 bg='#6c757d', fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2', padx=20, pady=8).pack(side=tk.LEFT, padx=10)
        
        # Focus on name field
        name_entry.focus_set()
        
        tk.Button(btn_frame, text="✅ Update Product", command=update_product,
                 bg='#007bff', fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2', padx=20, pady=8).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy,
                 bg='#dc3545', fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2', padx=20, pady=8).pack(side=tk.LEFT, padx=10)
        
        # Focus on name field
        name_entry.focus_set()

    def delete_product(self):
        """Delete selected product"""
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a product to delete")
            return
        
        product_id = self.products_tree.item(selected[0])['values'][0]
        product_data = None
        
        # Find product by ID
        for product in self.products:
            if product.get('id') == product_id:
                product_data = product
                break
        
        if not product_data:
            messagebox.showerror("Error", "Product not found")
            return
        
        # Confirm deletion
        result = messagebox.askyesno("Confirm Delete", 
                                   f"Are you sure you want to delete product '{product_data['name']}'?\n\n"
                                   f"This action cannot be undone!",
                                   icon='warning')
        
        if result:
            try:
                # Remove product from list
                self.products.remove(product_data)
                
                # Save to file
                save_json(FILES['PRODUCTS'], self.products)
                
                self.refresh_products_list()
                messagebox.showinfo("Success", f"Product '{product_data['name']}' deleted successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete product: {str(e)}")

    def update_product_stock(self):
        """Update product stock quantity"""
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a product to update stock")
            return
        
        product_id = self.products_tree.item(selected[0])['values'][0]
        product_data = None
        
        # Find product by ID
        for product in self.products:
            if product.get('id') == product_id:
                product_data = product
                break
        
        if not product_data:
            messagebox.showerror("Error", "Product not found")
            return
        
        # Stock update dialog
        dialog = tk.Toplevel(self.admin_window)
        dialog.title("📦 Update Stock")
        dialog.geometry("400x300")
        dialog.configure(bg='white')
        dialog.transient(self.admin_window)
        dialog.grab_set()
        
        # Center dialog
        x = self.admin_window.winfo_x() + (self.admin_window.winfo_width() // 2) - 200
        y = self.admin_window.winfo_y() + (self.admin_window.winfo_height() // 2) - 150
        dialog.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(dialog, bg='#17a2b8', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="📦 Update Stock", 
                font=('Segoe UI', 16, 'bold'),
                bg='#17a2b8', fg='white').pack(pady=15)
        
        # Form
        form_frame = tk.Frame(dialog, bg='white')
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        tk.Label(form_frame, text=f"Product: {product_data['name']}", 
                font=('Segoe UI', 12, 'bold'), bg='white').pack(pady=10)
        
        tk.Label(form_frame, text=f"Current Stock: {product_data['stock']}", 
                font=('Segoe UI', 11), bg='white').pack(pady=5)
        
        # New stock
        tk.Label(form_frame, text="📊 New Stock Quantity:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(10,5))
        stock_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=20)
        stock_entry.pack(pady=(0,15), ipady=5)
        stock_entry.insert(0, str(product_data['stock']))
        
        def update_stock():
            try:
                new_stock = int(stock_entry.get() or 0)
                
                if new_stock < 0:
                    messagebox.showerror("Error", "Stock quantity cannot be negative", parent=dialog)
                    return
                
                # Update stock
                product_data['stock'] = new_stock
                product_data['updated_date'] = datetime.now().isoformat()
                
                # Save to file
                save_json(FILES['PRODUCTS'], self.products)
                
                dialog.destroy()
                self.refresh_products_list()
                messagebox.showinfo("Success", f"Stock updated to {new_stock} for '{product_data['name']}'!")
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid stock quantity", parent=dialog)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update stock: {str(e)}", parent=dialog)
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg='white')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="✅ Update Stock", command=update_stock,
                 bg='#17a2b8', fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2', padx=20, pady=8).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy,
                 bg='#dc3545', fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2', padx=20, pady=8).pack(side=tk.LEFT, padx=10)
        
        # Focus on stock field
        stock_entry.focus_set()
        stock_entry.select_range(0, tk.END)

    def filter_products_admin(self, *args):
        """Filter products based on search text in admin panel"""
        search_text = self.product_search_var.get().lower()
        
        # Skip filtering if placeholder text
        if search_text == "search by name, id, or category...":
            return
        
        # Clear existing items
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # Add filtered products
        count = 0
        for product in self.products:
            if (not search_text or 
                search_text in product.get('name', '').lower() or 
                search_text in product.get('category', '').lower() or
                search_text in product.get('id', '').lower()):
                
                self.products_tree.insert('', 'end', values=(
                    product.get('id', ''),
                    product.get('name', ''),
                    product.get('category', ''),
                    f"₹{product.get('price', 0):.2f}",
                    product.get('stock', 0)
                ))
                count += 1
        
        # Update search status
        if hasattr(self, 'product_search_status'):
            if search_text:
                self.product_search_status.config(text=f"Found {count} product(s)")
            else:
                self.product_search_status.config(text="")

    def clear_product_search(self):
        """Clear product search"""
        self.product_search_var.set("")
        if hasattr(self, 'product_search_status'):
            self.product_search_status.config(text="")
        self.refresh_products_list()
    
    def refresh_users_list(self):
        """Refresh users list"""
        try:
            # Clear search if exists
            if hasattr(self, 'user_search_var'):
                self.user_search_var.set("")
            
            # Clear search status
            if hasattr(self, 'user_search_status'):
                self.user_search_status.config(text="")
            
            # Clear existing items
            for item in self.users_tree.get_children():
                self.users_tree.delete(item)
            
            # Add users to tree
            for email, user_data in self.users.items():
                status = "🟢 Active" if user_data.get('is_active', True) else "🔴 Inactive"
                self.users_tree.insert('', 'end', values=(
                    email,
                    user_data.get('name', ''),
                    user_data.get('role', 'user').title(),
                    status
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh users: {str(e)}")
    
    def refresh_products_list(self):
        """Refresh products list"""
        try:
            # Clear search if exists
            if hasattr(self, 'product_search_var'):
                self.product_search_var.set("")
            
            # Clear search status
            if hasattr(self, 'product_search_status'):
                self.product_search_status.config(text="")
            
            # Clear existing items
            for item in self.products_tree.get_children():
                self.products_tree.delete(item)
            
            # Add products to tree
            for product in self.products:
                self.products_tree.insert('', 'end', values=(
                    product.get('id', ''),
                    product.get('name', ''),
                    product.get('category', ''),
                    f"₹{product.get('price', 0):.2f}",
                    product.get('stock', 0)
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh products: {str(e)}")
    
    def refresh_transactions_list(self):
        """Refresh transactions list"""
        try:
            # Clear existing items
            for item in self.transactions_tree.get_children():
                self.transactions_tree.delete(item)
            
            # Add transactions to tree
            for transaction in self.bank.transactions:
                self.transactions_tree.insert('', 'end', values=(
                    transaction.get('id', ''),
                    transaction.get('type', ''),
                    f"₹{transaction.get('amount', 0):.2f}",
                    transaction.get('from_account', ''),
                    transaction.get('to_account', ''),
                    transaction.get('date', '')
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh transactions: {str(e)}")
    
    def load_shop_settings(self):
        """Load shop settings"""
        try:
            self.shop_name_entry.insert(0, self.shop_info.get('name', 'Banking & Shopping System'))
            self.shop_contact_entry.insert(0, self.shop_info.get('contact', '+91-9876543210'))
        except Exception as e:
            print(f"Error loading shop settings: {e}")
    
    def save_shop_settings(self):
        """Save shop settings"""
        try:
            self.shop_info['name'] = self.shop_name_entry.get()
            self.shop_info['contact'] = self.shop_contact_entry.get()
            
            # Save to file (assuming shop_info is saved somewhere)
            messagebox.showinfo("Success", "Shop settings saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

class AIAssistant:
    """Enhanced AI Assistant with context awareness and advanced features"""
    
    def __init__(self, banking_system):
        self.system = banking_system
        self.conversation_context = []
        self.user_preferences = {}
        self.knowledge_base = self._build_knowledge_base()
        self.intent_patterns = self._build_intent_patterns()
        self.response_templates = self._build_response_templates()
        
    def _build_knowledge_base(self):
        """Build comprehensive knowledge base about the system"""
        return {
            'banking_operations': {
                'create_account': {
                    'description': 'Create a new banking account',
                    'steps': ['Go to Banking tab', 'Click Create Account', 'Choose account type', 'Enter details', 'Confirm creation'],
                    'requirements': ['Valid name', 'Initial deposit (optional)', 'Account type selection'],
                    'account_types': ['Savings', 'Current', 'Fixed Deposit']
                },
                'deposit_money': {
                    'description': 'Add money to an existing account',
                    'steps': ['Go to Banking tab', 'Click Deposit Money', 'Enter account ID', 'Enter amount', 'Confirm transaction'],
                    'requirements': ['Valid account ID', 'Positive amount'],
                    'limits': 'No maximum limit'
                },
                'withdraw_money': {
                    'description': 'Withdraw money from an account',
                    'steps': ['Go to Banking tab', 'Click Withdraw Money', 'Enter account ID', 'Enter amount', 'Confirm transaction'],
                    'requirements': ['Valid account ID', 'Sufficient balance', 'Positive amount'],
                    'limits': 'Limited by account balance'
                },
                'transfer_money': {
                    'description': 'Transfer money between accounts',
                    'steps': ['Go to Banking tab', 'Click Transfer Money', 'Enter source account', 'Enter destination account', 'Enter amount', 'Confirm transfer'],
                    'requirements': ['Valid source and destination accounts', 'Sufficient balance in source', 'Positive amount'],
                    'fees': 'No transfer fees between internal accounts'
                },
                'view_transactions': {
                    'description': 'View transaction history with advanced filtering',
                    'steps': ['Go to Banking tab', 'Click Transaction History', 'Enter account ID', 'Use filters to refine results'],
                    'features': ['Date range filtering', 'Transaction type filtering', 'Amount range filtering', 'Export to CSV']
                }
            },
            'shopping_features': {
                'browse_products': {
                    'description': 'Browse and search products',
                    'features': ['Real-time search', 'Category filtering', 'Price range filtering', 'Stock status filtering'],
                    'search_tips': ['Use keywords for product names', 'Try price ranges like "100-500"', 'Filter by availability']
                },
                'cart_management': {
                    'description': 'Manage shopping cart items',
                    'features': ['Add/remove items', 'Quantity adjustment', 'Real-time price calculation', 'Stock validation'],
                    'filtering': ['Search cart items', 'Sort by price/quantity', 'Filter by category']
                },
                'checkout_process': {
                    'description': 'Complete purchase of cart items',
                    'steps': ['Review cart items', 'Verify total amount', 'Choose payment method', 'Confirm purchase'],
                    'requirements': ['Items in cart', 'Sufficient account balance', 'User login']
                }
            },
            'system_features': {
                'search_functionality': {
                    'description': 'Global search across all sections',
                    'features': ['Product search', 'Banking feature search', 'Help content search', 'Smart suggestions'],
                    'tips': ['Use the search bar in navigation', 'Try specific keywords', 'Use filters for better results']
                },
                'filtering_options': {
                    'description': 'Advanced filtering in all sections',
                    'locations': ['Product browsing', 'Transaction history', 'User management (admin)', 'Help content', 'Chat history'],
                    'operators': ['Price ranges (100-500)', 'Comparison operators (>100, <50)', 'Date ranges', 'Text matching']
                }
            }
        }
    
    def _build_intent_patterns(self):
        """Build patterns for intent recognition"""
        return {
            'greeting': [
                r'hello|hi|hey|good\s+(morning|afternoon|evening)',
                r'how\s+are\s+you',
                r'what\'s\s+up'
            ],
            'banking_help': [
                r'how\s+to\s+(create|make|open)\s+account',
                r'(deposit|withdraw|transfer)\s+money',
                r'check\s+balance',
                r'transaction\s+history',
                r'banking\s+(operations|features)'
            ],
            'shopping_help': [
                r'how\s+to\s+(shop|buy|purchase)',
                r'add\s+to\s+cart',
                r'checkout\s+process',
                r'(browse|search)\s+products',
                r'shopping\s+(features|guide)'
            ],
            'technical_help': [
                r'how\s+to\s+(use|navigate)',
                r'search\s+(function|feature)',
                r'filter\s+(options|results)',
                r'export\s+data',
                r'system\s+(features|guide)'
            ],
            'troubleshooting': [
                r'(problem|issue|error)\s+with',
                r'not\s+working',
                r'can\'t\s+(find|access|use)',
                r'(fix|solve|resolve)',
                r'troubleshoot'
            ],
            'account_specific': [
                r'my\s+(account|balance|transactions)',
                r'(show|display)\s+my',
                r'account\s+(details|information)'
            ]
        }
    
    def _build_response_templates(self):
        """Build response templates for different scenarios"""
        return {
            'greeting': [
                "👋 Hello! I'm your AI banking and shopping assistant. How can I help you today?",
                "🤖 Hi there! I'm here to help with banking operations, shopping, and general questions about the system.",
                "✨ Welcome! I can assist you with account management, product browsing, and much more. What would you like to know?"
            ],
            'banking_guidance': {
                'create_account': "🏦 **Creating an Account:**\n\n1. Navigate to the **Banking** tab\n2. Click **Create Account**\n3. Choose your account type (Savings, Current, or Fixed Deposit)\n4. Enter your details\n5. Set an initial deposit (optional)\n6. Confirm to create your account\n\n💡 **Tip:** Savings accounts are great for regular use, while Fixed Deposits offer better interest rates for long-term savings.",
                
                'deposit_withdraw': "💳 **Deposit/Withdraw Process:**\n\n**To Deposit:**\n• Go to Banking → Deposit Money\n• Enter your account ID\n• Enter the amount\n• Confirm the transaction\n\n**To Withdraw:**\n• Go to Banking → Withdraw Money\n• Enter your account ID\n• Enter the amount (must not exceed balance)\n• Confirm the transaction\n\n🔒 **Security:** All transactions are encrypted and logged for your security.",
                
                'transfer_money': "💸 **Money Transfer:**\n\n1. Banking tab → Transfer Money\n2. Enter source account ID\n3. Enter destination account ID\n4. Enter transfer amount\n5. Review and confirm\n\n✅ **Features:** Instant transfers, no fees between internal accounts, automatic balance validation.",
                
                'transaction_history': "📊 **Transaction History:**\n\nAccess your complete transaction history with powerful filtering options:\n\n• **Date Range:** Today, This Week, This Month, Custom\n• **Transaction Type:** Deposits, Withdrawals, Transfers\n• **Amount Range:** <₹100, ₹100-₹1,000, >₹10,000, Custom\n• **Search:** By description or transaction ID\n• **Export:** Download as CSV for record-keeping\n\n🔍 **Pro Tip:** Use multiple filters together for precise results!"
            },
            'shopping_guidance': {
                'product_browsing': "🛍️ **Product Browsing:**\n\n**Search Features:**\n• Real-time search as you type\n• Category filtering (Electronics, Clothing, Books, etc.)\n• Price range search (e.g., \"100-500\", \">100\", \"<50\")\n• Stock availability filtering\n\n**Smart Search Tips:**\n• Use specific product names\n• Try partial words (\"lapt\" for laptops)\n• Combine filters for better results\n• Check different categories",
                
                'cart_management': "🛒 **Cart Management:**\n\n**Adding Items:**\n• Click 'Add to Cart' on any product\n• Adjust quantities using +/- buttons\n• Real-time price calculation\n• Stock validation prevents overselling\n\n**Cart Features:**\n• Search cart items\n• Sort by name, price, or quantity\n• Remove unwanted items\n• See total with tax breakdown",
                
                'checkout_process': "✅ **Checkout Process:**\n\n1. **Review Cart:** Check all items and quantities\n2. **Verify Total:** Review subtotal, taxes, and delivery charges\n3. **Payment:** Choose from available account balances\n4. **Confirm:** Final confirmation and order placement\n\n💰 **Payment:** Uses your banking account balance for secure transactions."
            },
            'system_help': {
                'navigation': "🧭 **System Navigation:**\n\n**Main Tabs:**\n• **Home:** Dashboard and overview\n• **Banking:** All financial operations\n• **Products:** Shopping and browsing\n• **Cart:** Review and checkout\n• **Profile:** Account management\n• **AI:** This assistant (me!)\n• **Help:** Detailed documentation\n\n**Global Search:** Use the search bar in the top navigation for quick access to anything!",
                
                'filtering': "🔍 **Advanced Filtering:**\n\nAvailable across all sections:\n\n**Text Search:** Real-time filtering as you type\n**Range Filters:** Price ranges (100-500), Date ranges\n**Category Filters:** Product categories, Transaction types\n**Status Filters:** Stock availability, Account status\n**Operators:** > (greater than), < (less than), = (equals)\n\n💡 **Example:** Search \"Electronics >100 <500\" to find electronics between ₹100-₹500"
            }
        }
    
    def analyze_intent(self, message):
        """Analyze user message to determine intent"""
        import re
        message_lower = message.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        
        return 'general'
    
    def get_context_aware_response(self, message):
        """Generate context-aware response based on user message and system state"""
        intent = self.analyze_intent(message)
        
        # Add message to conversation context
        self.conversation_context.append({
            'message': message,
            'intent': intent,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 10 messages for context
        if len(self.conversation_context) > 10:
            self.conversation_context = self.conversation_context[-10:]
        
        # Generate response based on intent and context
        response = self._generate_response(message, intent)
        
        # Add personalization if user is logged in
        if hasattr(self.system, 'is_logged_in') and self.system.is_logged_in:
            response = self._personalize_response(response)
        
        return response
    
    def _generate_response(self, message, intent):
        """Generate appropriate response based on intent"""
        message_lower = message.lower()
        
        if intent == 'greeting':
            return random.choice(self.response_templates['greeting'])
        
        elif intent == 'banking_help':
            if any(word in message_lower for word in ['create', 'open', 'new', 'account']):
                return self.response_templates['banking_guidance']['create_account']
            elif any(word in message_lower for word in ['deposit', 'withdraw', 'cash']):
                return self.response_templates['banking_guidance']['deposit_withdraw']
            elif any(word in message_lower for word in ['transfer', 'send', 'move']):
                return self.response_templates['banking_guidance']['transfer_money']
            elif any(word in message_lower for word in ['history', 'transactions', 'statement']):
                return self.response_templates['banking_guidance']['transaction_history']
            else:
                return "🏦 **Banking Operations Available:**\n\n• **Account Management:** Create accounts, check balances\n• **Transactions:** Deposit, withdraw, transfer money\n• **History:** View detailed transaction records\n• **Security:** Encrypted and secure operations\n\nWhat specific banking operation would you like help with?"
        
        elif intent == 'shopping_help':
            if any(word in message_lower for word in ['browse', 'search', 'find', 'product']):
                return self.response_templates['shopping_guidance']['product_browsing']
            elif any(word in message_lower for word in ['cart', 'add', 'remove']):
                return self.response_templates['shopping_guidance']['cart_management']
            elif any(word in message_lower for word in ['checkout', 'buy', 'purchase', 'pay']):
                return self.response_templates['shopping_guidance']['checkout_process']
            else:
                return "🛍️ **Shopping Features:**\n\n• **Product Browsing:** Advanced search and filtering\n• **Cart Management:** Add, modify, and organize items\n• **Secure Checkout:** Integrated with your banking accounts\n• **Real-time Updates:** Live stock and pricing information\n\nWhat aspect of shopping would you like to explore?"
        
        elif intent == 'technical_help':
            if any(word in message_lower for word in ['navigate', 'use', 'how']):
                return self.response_templates['system_help']['navigation']
            elif any(word in message_lower for word in ['search', 'filter', 'find']):
                return self.response_templates['system_help']['filtering']
            else:
                return "⚙️ **System Features:**\n\n• **Global Search:** Find anything across all sections\n• **Advanced Filtering:** Powerful search operators\n• **Real-time Updates:** Instant feedback and notifications\n• **Export Options:** Download data in various formats\n• **Responsive Design:** Works great on different screen sizes\n\nWhich feature would you like to learn more about?"
        
        elif intent == 'account_specific':
            return self._get_account_specific_info(message_lower)
        
        elif intent == 'troubleshooting':
            return "🔧 **Troubleshooting Help:**\n\n**Common Solutions:**\n• **Refresh the page** if something isn't loading\n• **Check your internet connection** for real-time features\n• **Clear browser cache** if experiencing display issues\n• **Ensure you're logged in** for account-specific features\n\n**Still having issues?**\n• Describe the specific problem you're experiencing\n• Let me know what you were trying to do\n• I'll provide targeted assistance\n\n**Error Codes:** If you see any error messages, please share them for specific help."
        
        else:
            return self._get_general_help(message)
    
    def _get_account_specific_info(self, message):
        """Get user-specific account information"""
        if not hasattr(self.system, 'is_logged_in') or not self.system.is_logged_in:
            return "🔐 **Login Required**\n\nTo access your account information, please log in first:\n\n1. Go to the **Profile** tab\n2. Enter your email and password\n3. Click **Login**\n\nOnce logged in, I can help you with:\n• Your account balances\n• Recent transactions\n• Shopping cart contents\n• Order history"
        
        user_info = ""
        if hasattr(self.system, 'current_user') and self.system.current_user:
            user_info += f"👤 **Welcome, {self.system.current_user.get('name', 'User')}!**\n\n"
        
        # Get account information
        if hasattr(self.system, 'bank') and self.system.bank.accounts:
            user_info += "💳 **Your Accounts:**\n"
            for acc_id, acc_data in self.system.bank.accounts.items():
                if acc_data.get('is_active', True):
                    user_info += f"• Account {acc_id}: ₹{acc_data['balance']:,.2f} ({acc_data['type']})\n"
        
        # Get cart information
        if hasattr(self.system, 'cart') and self.system.cart.items:
            cart_details = self.system.cart.get_details(self.system.products)
            user_info += f"\n🛒 **Your Cart:** {len(cart_details['items'])} items, Total: ₹{cart_details['total']:,.2f}\n"
        
        return user_info if user_info else "📊 **Account Overview:**\n\nNo account information available. You may need to:\n• Create a banking account\n• Add items to your cart\n• Complete your profile setup"
    
    def _get_general_help(self, message):
        """Generate general help response"""
        return f"🤖 **AI Assistant Help**\n\nI can help you with:\n\n🏦 **Banking:** Account creation, transactions, balance checks\n🛍️ **Shopping:** Product browsing, cart management, checkout\n⚙️ **System:** Navigation, search, filtering, troubleshooting\n📊 **Data:** Export options, transaction history, reporting\n\n**Your question:** \"{message}\"\n\n💡 **Tip:** Try being more specific, like:\n• \"How do I create a savings account?\"\n• \"Show me electronics under ₹500\"\n• \"How to transfer money between accounts?\"\n\nWhat specific area would you like help with?"
    
    def _personalize_response(self, response):
        """Add personalization to response based on user context"""
        if hasattr(self.system, 'current_user') and self.system.current_user:
            name = self.system.current_user.get('name', 'there')
            if not response.startswith(f"👤 **Welcome, {name}"):
                response = f"Hi {name}! " + response
        
        return response

    def get_response(self, message, context=None):
        """
        Main method for getting AI responses with fallback to multiple providers
        This method integrates with the AIProviderManager for advanced responses
        """
        try:
            # First try to get AI response from AIProviderManager
            ai_response, provider_used = ai_manager.generate_response(message)
            
            if provider_used != "error":
                # Add context if available
                if context:
                    context_info = f"\n\n**Context:** {context}"
                    ai_response += context_info
                
                # Log successful AI response
                logging.info(f"AI response generated using {provider_used}")
                return ai_response
            else:
                # AI providers failed, use context-aware response
                logging.warning("AI providers failed, using context-aware response")
                return self.get_context_aware_response(message)
                
        except Exception as e:
            logging.error(f"Error in get_response: {e}")
            # Ultimate fallback to context-aware response
            return self.get_context_aware_response(message)
    
    def get_user_context(self):
        """Get current user context for better AI responses"""
        context = []
        
        # Add user information if logged in
        if hasattr(self.system, 'current_user') and self.system.current_user:
            context.append(f"User: {self.system.current_user.get('name', 'Unknown')}")
        
        # Add account information
        if hasattr(self.system, 'bank') and self.system.bank.accounts:
            active_accounts = [acc_id for acc_id, acc in self.system.bank.accounts.items() 
                             if acc.get('is_active', True)]
            if active_accounts:
                context.append(f"Active accounts: {len(active_accounts)}")
        
        # Add cart information
        if hasattr(self.system, 'cart') and self.system.cart.items:
            context.append(f"Cart items: {len(self.system.cart.items)}")
        
        # Add current tab/section
        if hasattr(self.system, 'current_tab'):
            context.append(f"Current section: {self.system.current_tab}")
        
        return "; ".join(context) if context else "No specific context"

@lru_cache(maxsize=128)
def get_offline_response(user_message):
    """Cached offline responses for better performance"""
    message = user_message.lower()
    
    # Banking queries
    if any(word in message for word in ['account', 'bank', 'balance', 'deposit', 'withdraw', 'transfer']):
        if 'create' in message:
            return "🏦 To create account: Banking → Create Account → Enter details"
        elif 'balance' in message:
            return "💰 To check balance: Banking → View Balance → Enter account number"
        elif 'deposit' in message:
            return "💳 To deposit: Banking → Deposit → Enter account & amount"
        elif 'withdraw' in message:
            return "🏧 To withdraw: Banking → Withdraw → Enter account & amount"
        elif 'transfer' in message:
            return "💸 To transfer: Banking → Transfer → Enter source, destination & amount"
        else:
            return "🏦 Banking features: Create Account, Deposit, Withdraw, Check Balance, Transfer Money"
    
    # Shopping queries
    elif any(word in message for word in ['shop', 'cart', 'buy', 'product', 'purchase']):
        if 'add' in message:
            return "🛒 To add items: Products → Browse → Add to Cart"
        elif 'checkout' in message:
            return "✅ To checkout: Cart → Review Items → Checkout"
        elif 'product' in message:
            return "📦 Browse products in the Products tab with categories and search"
        else:
            return "🛍️ Shopping features: Browse Products, Add to Cart, Checkout, Order History"
    
    # Help queries
    elif 'help' in message:
        return "📚 Use the navigation tabs: Home, Banking, Products, Cart, Profile, Help"
    elif any(word in message for word in ['hello', 'hi', 'hey']):
        return "👋 Hello! I'm your AI assistant. Ask me about banking or shopping!"
    else:
        return "🤖 I can help with banking operations and shopping. What would you like to know?"

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
        if user_id in self.failed_attempts:
            del self.failed_attempts[user_id]
    
    def is_valid(self, timeout_minutes=30):
        if not self.session_token:
            return False
        time_since_activity = datetime.now() - self.last_activity
        return time_since_activity.total_seconds() < (timeout_minutes * 60)
    
    def update_activity(self):
        self.last_activity = datetime.now()

class NotificationManager:
    """Enhanced notification system with animations and better UX"""
    def __init__(self, parent):
        self.parent = parent
        self.notifications = []
        self.notification_container = None
        self.setup_container()
    
    def setup_container(self):
        """Setup notification container"""
        self.notification_container = tk.Frame(self.parent, bg='#f8f9fa')
        self.notification_container.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(5, 0))
    
    def show_notification(self, message, notification_type="info", duration=4000):
        """Show an enhanced notification with animations"""
        # Icons for different notification types
        icons = {
            "info": "ℹ️",
            "success": "✅", 
            "warning": "⚠️",
            "error": "❌"
        }
        
        # Create notification frame
        notification = tk.Frame(self.notification_container, height=60)
        notification.pack(fill=tk.X, pady=2)
        notification.pack_propagate(False)
        
        colors = {
            "info": {"bg": "#cce7ff", "fg": "#004085", "border": "#007bff"},
            "success": {"bg": "#d4edda", "fg": "#155724", "border": "#28a745"},
            "warning": {"bg": "#fff3cd", "fg": "#856404", "border": "#ffc107"},
            "error": {"bg": "#f8d7da", "fg": "#721c24", "border": "#dc3545"}
        }
        
        color = colors.get(notification_type, colors["info"])
        notification.configure(bg=color["bg"], relief="solid", bd=2,
                              highlightbackground=color["border"], highlightthickness=1)
        
        # Content frame
        content_frame = tk.Frame(notification, bg=color["bg"])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Icon and message
        icon_label = tk.Label(content_frame, text=icons.get(notification_type, "📢"),
                             font=("Segoe UI", 14), bg=color["bg"])
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        message_label = tk.Label(content_frame, text=message, 
                                bg=color["bg"], fg=color["fg"],
                                font=("Segoe UI", 11, "bold"), 
                                wraplength=800, justify=tk.LEFT)
        message_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Close button with hover effect
        close_btn = tk.Button(content_frame, text="✕", 
                             bg=color["bg"], fg=color["fg"],
                             border=0, font=("Segoe UI", 14, "bold"),
                             cursor='hand2', padx=10,
                             command=lambda: self._close_notification(notification))
        close_btn.pack(side=tk.RIGHT)
        
        # Hover effects for close button
        def on_enter(e):
            close_btn.config(bg=color["border"], fg='white')
        def on_leave(e):
            close_btn.config(bg=color["bg"], fg=color["fg"])
        
        close_btn.bind('<Enter>', on_enter)
        close_btn.bind('<Leave>', on_leave)
        
        # Add to notifications list
        self.notifications.append(notification)
        
        # Auto-close after duration
        self.parent.after(duration, lambda: self._close_notification(notification))
        
        # Slide-in animation
        self._animate_slide_in(notification)
        
        # Limit number of notifications
        if len(self.notifications) > 3:
            self._close_notification(self.notifications[0])
    
    def _animate_slide_in(self, notification):
        """Simple slide-in animation"""
        notification.pack_forget()
        notification.pack(fill=tk.X, pady=2)
        self.parent.update()
    
    def _close_notification(self, notification):
        """Close notification with fade effect"""
        if notification in self.notifications:
            try:
                # Simple fade effect
                notification.configure(bg='#f8f9fa')
                self.parent.update()
                notification.destroy()
                self.notifications.remove(notification)
            except:
                pass  # Handle case where notification is already destroyed
    
    def show_success_toast(self, message, duration=3000):
        """Shortcut for success notifications"""
        self.show_notification(message, "success", duration)
    
    def show_error_toast(self, message, duration=5000):
        """Shortcut for error notifications"""
        self.show_notification(message, "error", duration)
    
    def show_info_toast(self, message, duration=4000):
        """Shortcut for info notifications"""
        self.show_notification(message, "info", duration)
    
    def clear_all(self):
        """Clear all notifications"""
        for notification in self.notifications[:]:
            self._close_notification(notification)

class Bank:
    def __init__(self):
        self.accounts = load_json(FILES['ACCOUNTS'], {})
        self.transactions = load_json(FILES['TRANSACTIONS'], [])
        # Safe calculation of next account ID
        try:
            account_ids = []
            for k in self.accounts.keys():
                try:
                    account_ids.append(int(k))
                except ValueError:
                    continue
            self.next_account_id = max(account_ids + [0]) + 1
        except (ValueError, TypeError):
            self.next_account_id = 1

    def create_account(self, name, initial_balance=0, account_type="Savings", user_email=None):
        account_id = str(self.next_account_id)
        self.accounts[account_id] = {
            "name": name,
            "balance": initial_balance,
            "type": account_type,
            "created_date": datetime.now().isoformat(),
            "user_email": user_email,
            "is_active": True
        }
        self.next_account_id += 1
        
        # Record transaction
        self.add_transaction(account_id, "Account Created", initial_balance, "credit")
        
        self.save_data()
        return True, f"Account created successfully. Account ID: {account_id}"

    def get_balance(self, account_id):
        if account_id not in self.accounts:
            return False, "Account not found."
        if not self.accounts[account_id]["is_active"]:
            return False, "Account is inactive."
        balance = self.accounts[account_id]["balance"]
        return True, f"Account balance: ₹{balance:,.2f}"

    def deposit(self, account_id, amount, description="Deposit"):
        if account_id not in self.accounts:
            return False, "Account not found."
        if amount <= 0:
            return False, "Amount must be positive."
        if not self.accounts[account_id]["is_active"]:
            return False, "Account is inactive."
        
        self.accounts[account_id]["balance"] += amount
        self.add_transaction(account_id, description, amount, "credit")
        self.save_data()
        
        new_balance = self.accounts[account_id]["balance"]
        return True, f"Deposited ₹{amount:,.2f}. New balance: ₹{new_balance:,.2f}"

    def withdraw(self, account_id, amount, description="Withdrawal"):
        if account_id not in self.accounts:
            return False, "Account not found."
        if amount <= 0:
            return False, "Amount must be positive."
        if not self.accounts[account_id]["is_active"]:
            return False, "Account is inactive."
        if self.accounts[account_id]["balance"] < amount:
            return False, "Insufficient funds."
        
        self.accounts[account_id]["balance"] -= amount
        self.add_transaction(account_id, description, amount, "debit")
        self.save_data()
        
        new_balance = self.accounts[account_id]["balance"]
        return True, f"Withdrew ₹{amount:,.2f}. New balance: ₹{new_balance:,.2f}"

    def transfer(self, from_account, to_account, amount, description="Transfer"):
        if from_account not in self.accounts:
            return False, "Source account not found."
        if to_account not in self.accounts:
            return False, "Destination account not found."
        if amount <= 0:
            return False, "Amount must be positive."
        if not self.accounts[from_account]["is_active"]:
            return False, "Source account is inactive."
        if not self.accounts[to_account]["is_active"]:
            return False, "Destination account is inactive."
        if self.accounts[from_account]["balance"] < amount:
            return False, "Insufficient funds in source account."
        
        # Perform transfer
        self.accounts[from_account]["balance"] -= amount
        self.accounts[to_account]["balance"] += amount
        
        # Record transactions
        self.add_transaction(from_account, f"Transfer to {to_account}", amount, "debit")
        self.add_transaction(to_account, f"Transfer from {from_account}", amount, "credit")
        
        self.save_data()
        return True, f"Transferred ₹{amount:,.2f} from {from_account} to {to_account}"

    def add_transaction(self, account_id, description, amount, transaction_type, category="General"):
        """Enhanced transaction recording with analytics data"""
        transaction = {
            "id": generate_transaction_id(),
            "account_id": account_id,
            "description": description,
            "amount": amount,
            "type": transaction_type,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "balance_after": self.accounts[account_id]["balance"] if account_id in self.accounts else 0,
            "location": "ATM" if "ATM" in description else "Online",
            "merchant": self.extract_merchant_name(description),
            "tags": self.generate_transaction_tags(description, category)
        }
        self.transactions.append(transaction)
        logging.info(f"Transaction recorded: {transaction['id']} - {description}")
    
    def extract_merchant_name(self, description):
        """Extract merchant name from transaction description"""
        common_merchants = ["Amazon", "Flipkart", "Zomato", "Swiggy", "PayTM", "GPay"]
        for merchant in common_merchants:
            if merchant.lower() in description.lower():
                return merchant
        return "Unknown"
    
    def generate_transaction_tags(self, description, category):
        """Generate relevant tags for transactions"""
        tags = [category.lower()]
        desc_lower = description.lower()
        if "grocery" in desc_lower or "supermarket" in desc_lower:
            tags.append("grocery")
        if "fuel" in desc_lower or "petrol" in desc_lower:
            tags.append("fuel")
        if "medical" in desc_lower or "hospital" in desc_lower:
            tags.append("healthcare")
        if "restaurant" in desc_lower or "food" in desc_lower:
            tags.append("dining")
        return list(set(tags))

    def get_transactions(self, account_id, limit=10):
        account_transactions = [t for t in self.transactions if t["account_id"] == account_id]
        return account_transactions[-limit:] if limit else account_transactions

    def save_data(self):
        save_json(FILES['ACCOUNTS'], self.accounts)
        save_json(FILES['TRANSACTIONS'], self.transactions)

class ShoppingCart:
    def __init__(self):
        self.items = Counter()
        self.user_cashback = 0.0

    def add(self, product_id, quantity=1):
        self.items[product_id] += quantity

    def remove(self, product_id, quantity=1):
        if product_id in self.items:
            self.items[product_id] -= quantity
            if self.items[product_id] <= 0:
                del self.items[product_id]

    def clear(self):
        self.items.clear()

    def get_details(self, products):
        catalog = {p['id']: p for p in products}
        items = []
        subtotal = 0
        
        for product_id, quantity in self.items.items():
            if product_id in catalog:
                product = catalog[product_id]
                price = product['price']
                total_price = price * quantity
                subtotal += total_price
                
                items.append({
                    'id': product_id,
                    'name': product['name'],
                    'price': price,
                    'quantity': quantity,
                    'total': total_price
                })
        
        # Calculate additional charges
        delivery_charge = 0 if subtotal > 500 else 50
        tax_rate = 0.18  # 18% GST
        tax_amount = subtotal * tax_rate
        
        # Calculate cashback
        cashback_amount = subtotal * (self.user_cashback / 100)
        
        grand_total = subtotal + delivery_charge + tax_amount
        
        return {
            'items': items,
            'subtotal': subtotal,
            'delivery_charge': delivery_charge,
            'tax_amount': tax_amount,
            'cashback_amount': cashback_amount,
            'grand_total': grand_total
        }

class SplashScreen:
    """Modern loading splash screen"""
    def __init__(self):
        self.splash = tk.Toplevel()
        self.splash.title("Loading...")
        self.splash.geometry("400x300")
        self.splash.configure(bg='#ffffff')
        self.splash.overrideredirect(True)  # Remove window decorations
        
        # Center the splash screen
        self.center_splash()
        
        # Main content
        main_frame = tk.Frame(self.splash, bg='#ffffff', padx=40, pady=40)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Logo/Icon
        logo_label = tk.Label(main_frame, text="💰🏦", font=('Segoe UI', 48),
                             bg='#ffffff', fg='#007bff')
        logo_label.pack(pady=20)
        
        # App name
        title_label = tk.Label(main_frame, text="Advanced Banking & Shopping System",
                              font=('Segoe UI', 16, 'bold'),
                              bg='#ffffff', fg='#343a40')
        title_label.pack(pady=10)
        
        # Subtitle
        subtitle_label = tk.Label(main_frame, text="Your Modern Financial Companion",
                                 font=('Segoe UI', 11),
                                 bg='#ffffff', fg='#6c757d')
        subtitle_label.pack(pady=5)
        
        # Progress bar
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(main_frame, 
                                           variable=self.progress_var,
                                           maximum=100,
                                           length=300,
                                           mode='determinate')
        self.progress_bar.pack(pady=30)
        
        # Status label
        self.status_label = tk.Label(main_frame, text="Initializing application...",
                                    font=('Segoe UI', 10),
                                    bg='#ffffff', fg='#007bff')
        self.status_label.pack(pady=10)
        
        # Version info
        version_label = tk.Label(main_frame, text="Version 2.0 | Powered by AI",
                                font=('Segoe UI', 9),
                                bg='#ffffff', fg='#adb5bd')
        version_label.pack(side=tk.BOTTOM, pady=10)
        
    def center_splash(self):
        """Center splash screen on screen"""
        self.splash.update_idletasks()
        width = 400
        height = 300
        x = (self.splash.winfo_screenwidth() // 2) - (width // 2)
        y = (self.splash.winfo_screenheight() // 2) - (height // 2)
        self.splash.geometry(f"{width}x{height}+{x}+{y}")
    
    def update_progress(self, value, status):
        """Update progress bar and status"""
        self.progress_var.set(value)
        self.status_label.config(text=status)
        self.splash.update()
        time.sleep(0.1)  # Small delay for visual effect
    
    def close(self):
        """Close splash screen"""
        self.splash.destroy()

class EnhancedBankingShoppingSystem(tk.Tk):
    def __init__(self):
        # Show splash screen
        splash = SplashScreen()
        
        super().__init__()
        self.withdraw()  # Hide main window initially
        
        # Update splash progress
        splash.update_progress(10, "Loading configurations...")
        
        # Window configuration with modern styling
        self.title("💰 Advanced Banking & Shopping System v2.0")
        self.geometry("1400x900")
        self.minsize(1200, 800)
        self.configure(bg="#f8f9fa")
        
        # Set window icon (if available)
        try:
            self.iconbitmap(default='icon.ico')  # Add your icon file
        except:
            pass
        
        splash.update_progress(25, "Initializing secure components...")
        
        # Initialize thread-safe components first
        self.setup_thread_safety()
        
        # Initialize components
        self.session = SecureSession()
        self.notification_manager = NotificationManager(self)
        self.bank = Bank()
        self.cart = ShoppingCart()
        self.ai_assistant = AIAssistant(self)  # Initialize enhanced AI assistant
        
        splash.update_progress(40, "Loading user data...")
        
        # Load data
        self.products = load_json(FILES['PRODUCTS'], self.get_default_products())
        self.categories = load_json(FILES['CATEGORIES'], DEFAULT_CATEGORIES)
        self.users = load_json(FILES['USERS'], {})
        self.settings = load_json(FILES['SETTINGS'], DEFAULT_SETTINGS.copy())
        self.shop_info = load_json(FILES['SHOP'], DEFAULT_SHOP)
        
        # Migrate old product format to new image structure
        self.migrate_product_images()
        
        # Create default admin user if not exists
        self.create_default_admin()
        
        splash.update_progress(60, "Configuring interface...")
        
        # User session
        self.current_user = None
        self.is_logged_in = False
        
        # Style configuration
        self.configure_styles()
        
        splash.update_progress(80, "Creating user interface...")
        
        # Create UI
        self.create_main_interface()
        
        # Welcome tour for first-time users
        self.setup_welcome_tour()
        
        splash.update_progress(90, "Setting up security...")
        
        # Auto-logout timer
        self.auto_logout_timer = None
        self.start_auto_logout_timer()
        
        # Bind activity tracking
        self.bind_all('<Button-1>', lambda e: self.reset_activity_timer())
        self.bind_all('<Key>', lambda e: self.reset_activity_timer())
        
        # Window close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        splash.update_progress(100, "Ready!")
        
        # Center main window
        self.center_window()
        
        # Close splash and show main window
        splash.close()
        self.deiconify()
        
        # Show welcome message for new users
        self.show_welcome_message()
    
    def setup_thread_safety(self):
        """Initialize thread-safe components and error handling"""
        try:
            if THREAD_UTILS_AVAILABLE:
                # Use advanced thread utilities
                self.thread_utils = make_thread_safe(self)
                self.image_manager = self.thread_utils['image_manager']
                self.safe_updater = self.thread_utils['updater']
                self.thread_decorator = self.thread_utils['decorator']
                print("✅ Advanced thread utilities initialized")
            else:
                # Fallback to basic thread safety
                self.image_manager = None
                self.safe_updater = None
                print("⚠️ Using basic thread safety measures")
            
            # Thread pool for image loading (basic fallback)
            import concurrent.futures
            self.image_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            
            # Thread-safe image cache
            self.image_cache = {}
            self.image_cache_lock = threading.Lock()
            
            # Queue for pending GUI updates from background threads
            self.gui_update_queue = queue.Queue()
            
            # Active image loading threads tracking
            self.active_image_threads = set()
            self.thread_lock = threading.Lock()
            
            # Error tracking
            self.thread_errors = []
            self.max_thread_errors = 10  # Keep last 10 errors
            
            # Start GUI update processor
            self.process_gui_updates()
            
            print("✅ Thread safety components initialized")
            
        except Exception as e:
            print(f"❌ Error setting up thread safety: {e}")
            traceback.print_exc()
            # Continue with minimal setup
            self.image_manager = None
            self.safe_updater = None
    
    def process_gui_updates(self):
        """Process pending GUI updates from background threads with error handling"""
        try:
            updates_processed = 0
            max_updates_per_cycle = 5  # Limit updates per cycle to prevent blocking
            
            # Process pending updates
            while updates_processed < max_updates_per_cycle:
                try:
                    update_func = self.gui_update_queue.get_nowait()
                    if callable(update_func):
                        try:
                            update_func()
                            updates_processed += 1
                        except tk.TclError as e:
                            # Widget was destroyed - this is normal during cleanup
                            if "invalid command name" not in str(e):
                                print(f"⚠️ Widget destroyed during update: {e}")
                        except Exception as e:
                            self.log_thread_error(f"GUI update error: {e}")
                            print(f"❌ Error processing GUI update: {e}")
                except queue.Empty:
                    break  # No more updates to process
                except Exception as e:
                    self.log_thread_error(f"Queue processing error: {e}")
                    break
                    
        except Exception as e:
            self.log_thread_error(f"GUI update processor error: {e}")
            print(f"❌ Error in GUI update processor: {e}")
        
        # Schedule next check (increased to 100ms to reduce CPU usage)
        try:
            if hasattr(self, 'winfo_exists') and self.winfo_exists():
                self.after(100, self.process_gui_updates)
        except:
            # Application is shutting down
            pass
    
    def log_thread_error(self, error_msg: str):
        """Log thread-related errors with rotation"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            error_entry = f"[{timestamp}] {error_msg}"
            
            if hasattr(self, 'thread_errors'):
                self.thread_errors.append(error_entry)
                # Keep only recent errors
                if len(self.thread_errors) > self.max_thread_errors:
                    self.thread_errors = self.thread_errors[-self.max_thread_errors:]
        except:
            pass  # Don't let error logging cause more errors
    
    def cleanup_threading(self):
        """Clean up all threading components properly"""
        try:
            print("🧹 Cleaning up threading components...")
            
            # Shutdown thread pool if it exists
            if hasattr(self, 'image_thread_pool'):
                print("🔄 Shutting down thread pool...")
                self.image_thread_pool.shutdown(wait=False)
            
            # Clear image cache
            if hasattr(self, 'image_cache'):
                with self.image_cache_lock:
                    self.image_cache.clear()
            
            # Clear GUI update queue
            if hasattr(self, 'gui_update_queue'):
                while not self.gui_update_queue.empty():
                    try:
                        self.gui_update_queue.get_nowait()
                    except:
                        break
            
            # Clear active thread tracking
            if hasattr(self, 'active_image_threads'):
                with self.thread_lock:
                    self.active_image_threads.clear()
            
            print("✅ Threading cleanup completed")
            
        except Exception as e:
            print(f"❌ Error during threading cleanup: {e}")
    
    def center_window(self):
        """Center the main window on screen"""
        self.update_idletasks()
        width = 1400
        height = 900
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def thread_safe_call(self, func, *args, **kwargs):
        """Execute a function in the main thread safely from any thread"""
        try:
            if threading.current_thread() == threading.main_thread():
                # Already in main thread, execute directly
                return func(*args, **kwargs)
            else:
                # Schedule execution in main thread using thread-safe queue
                result_container = {'result': None, 'exception': None, 'completed': False}
                
                def wrapper():
                    try:
                        result_container['result'] = func(*args, **kwargs)
                    except Exception as e:
                        result_container['exception'] = e
                    finally:
                        result_container['completed'] = True
                
                # Use after_idle for better thread safety
                self.after_idle(wrapper)
                return None  # Can't return result from async call
        except Exception as e:
            print(f"❌ Thread-safe call error: {e}")
            return None
    
    def thread_safe_update(self, widget, **config_options):
        """Safely update a widget from any thread with improved error handling"""
        def update_widget():
            try:
                if widget and hasattr(widget, 'winfo_exists') and widget.winfo_exists():
                    widget.config(**config_options)
                else:
                    # Widget doesn't exist, this is normal during cleanup
                    pass
            except tk.TclError as e:
                if "invalid command name" not in str(e):
                    # Only log if it's not a normal cleanup error
                    self.log_thread_error(f"Widget update TclError: {e}")
            except Exception as e:
                self.log_thread_error(f"Widget update error: {e}")
                print(f"❌ Widget update error: {e}")
        
        if threading.current_thread() == threading.main_thread():
            update_widget()
        else:
            # Use queue instead of after_idle for better reliability
            try:
                self.gui_update_queue.put(update_widget)
            except:
                # Fallback to after_idle if queue fails
                try:
                    self.after_idle(update_widget)
                except:
                    pass  # Complete fallback - just skip the update
    
    def show_thread_errors(self):
        """Show recent thread errors in a dialog"""
        if not hasattr(self, 'thread_errors') or not self.thread_errors:
            messagebox.showinfo("Thread Status", "✅ No recent threading errors detected!")
            return
        
        error_window = tk.Toplevel(self)
        error_window.title("🧵 Threading Error Log")
        error_window.geometry("700x500")
        error_window.configure(bg='white')
        
        # Header
        header = tk.Label(error_window, text="🧵 Recent Threading Errors", 
                         font=('Segoe UI', 14, 'bold'), bg='white')
        header.pack(pady=10)
        
        # Error display
        text_frame = tk.Frame(error_window, bg='white')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        text_widget = tk.Text(text_frame, font=('Consolas', 10), wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add errors to display
        for error in self.thread_errors:
            text_widget.insert(tk.END, error + "\n")
        
        text_widget.config(state=tk.DISABLED)
        
        # Clear button
        def clear_errors():
            if hasattr(self, 'thread_errors'):
                self.thread_errors.clear()
            error_window.destroy()
            messagebox.showinfo("Cleared", "✅ Thread error log cleared!")
        
        clear_btn = tk.Button(error_window, text="🗑️ Clear Errors", command=clear_errors,
                             bg='#dc3545', fg='white', font=('Segoe UI', 10, 'bold'))
        clear_btn.pack(pady=10)
    
    def show_thread_status(self):
        """Show current threading status and diagnostics"""
        status_window = tk.Toplevel(self)
        status_window.title("🧵 Thread Status & Diagnostics")
        status_window.geometry("600x600")
        status_window.configure(bg='white')
        
        # Header
        header = tk.Label(status_window, text="🧵 Threading Status & Diagnostics", 
                         font=('Segoe UI', 14, 'bold'), bg='white')
        header.pack(pady=10)
        
        # Create scrollable text widget
        text_frame = tk.Frame(status_window, bg='white')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        text_widget = tk.Text(text_frame, font=('Consolas', 10), wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Gather thread status information
        status_info = []
        status_info.append("=== THREAD STATUS REPORT ===\n")
        status_info.append(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Current thread info
        current_thread = threading.current_thread()
        main_thread = threading.main_thread()
        status_info.append("🧵 CURRENT THREAD INFO:")
        status_info.append(f"   Name: {current_thread.name}")
        status_info.append(f"   Is Main Thread: {current_thread == main_thread}")
        status_info.append(f"   Is Alive: {current_thread.is_alive()}\n")
        
        # Active threads
        active_threads = threading.enumerate()
        status_info.append(f"🔄 ACTIVE THREADS ({len(active_threads)}):")
        for i, thread in enumerate(active_threads, 1):
            status_info.append(f"   {i}. {thread.name} (Daemon: {thread.daemon}, Alive: {thread.is_alive()})")
        status_info.append("")
        
        # Threading components status
        status_info.append("⚙️ THREADING COMPONENTS:")
        status_info.append(f"   Thread Utils Available: {THREAD_UTILS_AVAILABLE}")
        status_info.append(f"   Image Manager: {'✅ Active' if hasattr(self, 'image_manager') and self.image_manager else '❌ Not Available'}")
        status_info.append(f"   Safe Updater: {'✅ Active' if hasattr(self, 'safe_updater') and self.safe_updater else '❌ Not Available'}")
        status_info.append(f"   Thread Pool: {'✅ Active' if hasattr(self, 'image_thread_pool') else '❌ Not Available'}")
        status_info.append(f"   GUI Update Queue: {'✅ Active' if hasattr(self, 'gui_update_queue') else '❌ Not Available'}")
        
        # Queue status
        if hasattr(self, 'gui_update_queue'):
            try:
                queue_size = self.gui_update_queue.qsize()
                status_info.append(f"   Queue Size: {queue_size} pending updates")
            except:
                status_info.append("   Queue Size: Unable to determine")
        status_info.append("")
        
        # Error statistics
        if hasattr(self, 'thread_errors'):
            status_info.append(f"❌ RECENT ERRORS ({len(self.thread_errors)}):")
            if self.thread_errors:
                for error in self.thread_errors[-5:]:  # Show last 5 errors
                    status_info.append(f"   • {error}")
            else:
                status_info.append("   ✅ No recent errors!")
        status_info.append("")
        
        # Image loading status
        status_info.append("🖼️ IMAGE LOADING STATUS:")
        if hasattr(self, 'image_cache'):
            with self.image_cache_lock:
                cache_size = len(self.image_cache)
            status_info.append(f"   Image Cache: {cache_size} cached images")
        
        if hasattr(self, 'active_image_threads'):
            with self.thread_lock:
                active_loads = len(self.active_image_threads)
            status_info.append(f"   Active Loads: {active_loads} in progress")
        status_info.append("")
        
        # Recommendations
        status_info.append("💡 RECOMMENDATIONS:")
        if not THREAD_UTILS_AVAILABLE:
            status_info.append("   ⚠️ Consider installing thread_utils for enhanced safety")
        
        error_count = len(self.thread_errors) if hasattr(self, 'thread_errors') else 0
        if error_count > 5:
            status_info.append("   ⚠️ High error count detected - check application logs")
        elif error_count == 0:
            status_info.append("   ✅ Threading system operating normally")
        
        # Insert all status info
        text_widget.insert(tk.END, "\n".join(status_info))
        text_widget.config(state=tk.DISABLED)
        
        # Refresh button
        def refresh_status():
            text_widget.config(state=tk.NORMAL)
            text_widget.delete(1.0, tk.END)
            # Re-run the status gathering (recursive call)
            status_window.destroy()
            self.show_thread_status()
        
        refresh_btn = tk.Button(status_window, text="🔄 Refresh", command=refresh_status,
                               bg='#28a745', fg='white', font=('Segoe UI', 10, 'bold'))
        refresh_btn.pack(pady=10)
    
    def safe_image_loader(self, image_url, success_callback, error_callback=None, progress_callback=None):
        """Generic thread-safe image loader with callbacks"""
        def load_image_safe():
            try:
                if progress_callback:
                    self.after_idle(lambda: progress_callback("Starting download..."))
                
                # Load image
                if os.path.exists(image_url):
                    image = Image.open(image_url)
                else:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    if progress_callback:
                        self.after_idle(lambda: progress_callback("Downloading image..."))
                    
                    response = requests.get(image_url, timeout=15, headers=headers)
                    response.raise_for_status()
                    image = Image.open(BytesIO(response.content))
                
                if progress_callback:
                    self.after_idle(lambda: progress_callback("Processing image..."))
                
                # Convert to RGB if needed
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Call success callback in main thread
                self.after_idle(lambda: success_callback(image))
                
            except Exception as e:
                # Call error callback in main thread
                if error_callback:
                    self.after_idle(lambda: error_callback(e))
                else:
                    print(f"❌ Image loading error: {e}")
        
        # Start background thread
        try:
            thread = threading.Thread(target=load_image_safe, daemon=True)
            thread.start()
            return thread
        except Exception as e:
            if error_callback:
                error_callback(e)
            else:
                print(f"❌ Failed to start image loading thread: {e}")
            return None
    
    def load_image_with_fallback(self, image_url, success_callback, error_callback=None, 
                                progress_callback=None, size=None):
        """Enhanced image loading with multiple fallback strategies"""
        try:
            # Use advanced image manager if available
            if hasattr(self, 'image_manager') and self.image_manager:
                return self.image_manager.load_image_async(
                    image_url, success_callback, error_callback, progress_callback
                )
            
            # Fallback to basic thread-safe loading
            def load_with_progress():
                try:
                    if progress_callback:
                        self.gui_update_queue.put(lambda: progress_callback("Loading..."))
                    
                    # Load image
                    if os.path.exists(image_url):
                        image = Image.open(image_url)
                    else:
                        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                        response = requests.get(image_url, timeout=15, headers=headers)
                        response.raise_for_status()
                        image = Image.open(BytesIO(response.content))
                    
                    # Process image
                    if image.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', image.size, (255, 255, 255))
                        if image.mode == 'P':
                            image = image.convert('RGBA')
                        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                        image = background
                    elif image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    # Resize if size specified
                    if size:
                        image.thumbnail(size, Image.Resampling.LANCZOS)
                    
                    # Schedule success callback
                    self.gui_update_queue.put(lambda: success_callback(image))
                    
                except Exception as e:
                    # Schedule error callback
                    if error_callback:
                        self.gui_update_queue.put(lambda: error_callback(e))
                    else:
                        self.log_thread_error(f"Image loading error: {e}")
            
            # Start thread
            thread = threading.Thread(target=load_with_progress, daemon=True)
            thread.start()
            return thread
            
        except Exception as e:
            self.log_thread_error(f"Image loading setup error: {e}")
            if error_callback:
                error_callback(e)
            return None
    
    def setup_welcome_tour(self):
        """Setup welcome tour for new users"""
        self.tour_step = 0
        self.tour_active = False
    
    def show_welcome_message(self):
        """Show enhanced welcome message"""
        if not self.settings.get('first_time_user_seen', False):
            self.show_first_time_dialog()
            self.settings['first_time_user_seen'] = True
            self.after(1000, self.show_first_time_dialog)  # Delay for better UX
    
    def show_first_time_dialog(self):
        """Show first-time user dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Welcome! 🎉")
        dialog.geometry("500x400")
        dialog.configure(bg='white')
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        x = self.winfo_x() + (self.winfo_width() // 2) - 250
        y = self.winfo_y() + (self.winfo_height() // 2) - 200
        dialog.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(dialog, bg='#007bff', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, text="🎉 Welcome to Advanced Banking!",
                               font=('Segoe UI', 18, 'bold'),
                               bg='#007bff', fg='white')
        header_label.pack(expand=True)
        
        # Content
        content_frame = tk.Frame(dialog, bg='white', padx=30, pady=30)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        welcome_text = """Welcome to your new financial companion!

🏦 Secure banking with real-time transactions
🛍️ Smart shopping with AI recommendations
🤖 Intelligent assistant for all your needs
📱 Modern, user-friendly interface

Ready to get started?"""
        
        text_label = tk.Label(content_frame, text=welcome_text,
                             font=('Segoe UI', 11), bg='white', fg='#495057',
                             justify=tk.LEFT)
        text_label.pack(padx=20, pady=15)
        
        # Buttons
        btn_frame = tk.Frame(content_frame, bg='white')
        btn_frame.pack(pady=20)
        
        def start_tour():
            self.settings['first_time_user_seen'] = True
            save_json(FILES['SETTINGS'], self.settings)
            dialog.destroy()
            self.start_welcome_tour()
        
        def skip_tour():
            self.settings['first_time_user_seen'] = True
            save_json(FILES['SETTINGS'], self.settings)
            dialog.destroy()
        
        tour_btn = tk.Button(btn_frame, text="🚀 Take Quick Tour",
                            command=start_tour,
                            bg='#28a745', fg='white', font=('Segoe UI', 11, 'bold'),
                            relief='flat', cursor='hand2', padx=20, pady=10)
        tour_btn.pack(side=tk.LEFT, padx=10)
        
        skip_btn = tk.Button(btn_frame, text="Skip for Now",
                            command=skip_tour,
                            bg='#6c757d', fg='white', font=('Segoe UI', 11, 'bold'),
                            relief='flat', cursor='hand2', padx=20, pady=10)
        skip_btn.pack(side=tk.LEFT, padx=10)
    
    def start_welcome_tour(self):
        """Start interactive welcome tour"""
        # This could be enhanced with step-by-step highlighting
        self.notification_manager.show_notification(
            "🎯 Tour: Start by exploring the Banking tab to create your first account!", 
            "info", 5000
        )

    def configure_styles(self):
        """Configure modern styling with theme support"""
        current_theme = self.settings.get('theme', 'modern')
        self.colors = THEMES.get(current_theme, THEMES['modern']).copy()
        
        # Apply theme to window
        self.configure(bg=self.colors['background'])
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure ttk styles with current theme
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 16, 'bold'),
                       background=self.colors['background'],
                       foreground=self.colors['text'])
        style.configure('Heading.TLabel', 
                       font=('Segoe UI', 12, 'bold'),
                       background=self.colors['background'],
                       foreground=self.colors['text'])
        style.configure('Modern.TButton', 
                       font=('Segoe UI', 10, 'bold'))
        
        # Configure notebook tabs
        style.configure('TNotebook', 
                       background=self.colors['background'])
        style.configure('TNotebook.Tab',
                       background=self.colors['card'],
                       foreground=self.colors['text'],
                       padding=[20, 10])
        style.map('TNotebook.Tab',
                 background=[('selected', self.colors['primary'])],
                 foreground=[('selected', 'white')])
    
    def apply_theme(self, theme_name):
        """Apply a new theme to the application"""
        if theme_name in THEMES:
            self.colors = THEMES[theme_name].copy()
            self.configure_styles()
            self.settings['theme'] = theme_name
            save_json(FILES['SETTINGS'], self.settings)
            
            # Show restart notification
            self.notification_manager.show_notification(
                "🎨 Theme changed! Please restart the application to see changes.",
                "info", 5000
            )

    def create_main_interface(self):
        """Create the main interface with navigation"""
        # Create top navigation bar
        self.create_navigation_bar()
        
        # Create main content area with notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Create tabs
        self.create_tabs()
        
        # Create status bar
        self.create_status_bar()

    def create_navigation_bar(self):
        """Create top navigation bar"""
        nav_frame = tk.Frame(self, bg=self.colors['primary'], height=60)
        nav_frame.pack(fill=tk.X)
        nav_frame.pack_propagate(False)
        
        # Logo/Title
        title_label = tk.Label(nav_frame, text="💰 Advanced Banking & Shopping", 
                              font=('Segoe UI', 14, 'bold'),
                              bg=self.colors['primary'], fg='white')
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Admin quick access (only shown for admin users)
        self.admin_quick_frame = tk.Frame(nav_frame, bg=self.colors['primary'])
        self.admin_quick_frame.pack(side=tk.LEFT, padx=20, pady=10)
        
        # User info
        self.user_info_frame = tk.Frame(nav_frame, bg=self.colors['primary'])
        self.user_info_frame.pack(side=tk.RIGHT, padx=20, pady=10)
        
        self.update_user_info_display()
        
        # Settings button
        settings_btn = tk.Button(nav_frame, text="⚙️ Settings", 
                               font=('Segoe UI', 10), bg=self.colors['secondary'], 
                               fg='white', border=0, cursor='hand2',
                               command=self.open_settings)
        settings_btn.pack(side=tk.RIGHT, padx=10, pady=15)

    def create_tabs(self):
        """Create all application tabs"""
        # Home tab
        self.home_frame = tk.Frame(self.notebook, bg=self.colors['light'])
        self.notebook.add(self.home_frame, text="🏠 Home")
        self.build_home_tab()
        
        # Banking tab
        self.banking_frame = tk.Frame(self.notebook, bg=self.colors['light'])
        self.notebook.add(self.banking_frame, text="🏦 Banking")
        self.build_banking_tab()
        
        # Products tab
        self.products_frame = tk.Frame(self.notebook, bg=self.colors['light'])
        self.notebook.add(self.products_frame, text="🛒 Products")
        self.build_products_tab()
        
        # Cart tab
        self.cart_frame = tk.Frame(self.notebook, bg=self.colors['light'])
        self.notebook.add(self.cart_frame, text="🛍️ Cart")
        self.build_cart_tab()
        
        # Profile tab
        self.profile_frame = tk.Frame(self.notebook, bg=self.colors['light'])
        self.notebook.add(self.profile_frame, text="👤 Profile")
        self.build_profile_tab()
        
        # AI Assistant tab
        self.ai_frame = tk.Frame(self.notebook, bg=self.colors['light'])
        self.notebook.add(self.ai_frame, text="🤖 AI Assistant")
        self.build_ai_tab()
        
        # Help tab
        self.help_frame = tk.Frame(self.notebook, bg=self.colors['light'])
        self.notebook.add(self.help_frame, text="❓ Help")
        self.build_help_tab()

    def create_status_bar(self):
        """Create bottom status bar with enhanced AI provider info"""
        status_frame = tk.Frame(self, bg=self.colors['dark'], height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        # Left side - AI system status
        status_left = tk.Frame(status_frame, bg=self.colors['dark'])
        status_left.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Enhanced AI status display
        active_providers = ai_manager.get_active_providers()
        if ai_manager.current_provider and ai_manager.current_provider != "offline":
            provider_name = ai_manager.providers[ai_manager.current_provider]["name"]
            ai_status = f"🟢 AI: {provider_name} ({ai_manager.current_model})"
        elif len(active_providers) > 1:  # Has offline + others
            ai_status = f"🟡 AI: {len(active_providers)-1} providers available"
        else:
            ai_status = "🟡 AI: Offline mode"
            
        self.ai_status_label = tk.Label(status_left, text=ai_status, 
                                       bg=self.colors['dark'], fg='white',
                                       font=('Segoe UI', 9))
        self.ai_status_label.pack(side=tk.LEFT)
        
        # Provider count indicator
        if len(active_providers) > 1:
            provider_count = tk.Label(status_left, text=f"({len(active_providers)} providers)", 
                                     bg=self.colors['dark'], fg=self.colors['warning'],
                                     font=('Segoe UI', 8))
            provider_count.pack(side=tk.LEFT, padx=(5, 0))
        
        # Right side - current time
        status_right = tk.Frame(status_frame, bg=self.colors['dark'])
        status_right.pack(side=tk.RIGHT, padx=10, pady=5)
        
        self.time_label = tk.Label(status_right, text="", 
                                  bg=self.colors['dark'], fg='white',
                                  font=('Segoe UI', 9))
        self.time_label.pack(side=tk.RIGHT)
        self.update_time()

    def build_home_tab(self):
        """Build the home dashboard"""
        # Create scrollable frame
        canvas = tk.Canvas(self.home_frame, bg=self.colors['light'])
        scrollbar = ttk.Scrollbar(self.home_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['light'])
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Welcome section
        welcome_frame = self.create_card_frame(scrollable_frame, "🎉 Welcome to Advanced Banking & Shopping")
        welcome_frame.pack(fill=tk.X, padx=20, pady=20)
        
        welcome_text = tk.Label(welcome_frame, 
                               text="Your comprehensive financial and shopping platform\n\n"
                                    "✨ Secure banking with real-time transactions\n"
                                    "🛍️ Smart shopping with AI recommendations\n"
                                    "🤖 Intelligent assistant for all your needs\n"
                                    "📱 Modern, user-friendly interface",
                               font=('Segoe UI', 11), bg='white', fg='#495057',
                               justify=tk.LEFT)
        welcome_text.pack(padx=20, pady=15)
        
        # Quick stats
        stats_frame = self.create_card_frame(scrollable_frame, "📊 Quick Overview")
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.create_stats_display(stats_frame)
        
        # Quick actions
        actions_frame = self.create_card_frame(scrollable_frame, "🚀 Quick Actions")
        actions_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.create_quick_actions(actions_frame)

    def build_banking_tab(self):
        """Build the banking interface"""
        # Banking header
        header_frame = self.create_card_frame(self.banking_frame, "🏦 Banking Services")
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Banking operations
        operations_frame = tk.Frame(self.banking_frame, bg=self.colors['light'])
        operations_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left panel - operations
        left_panel = self.create_card_frame(operations_frame, "💳 Account Operations")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        operations = [
            ("Create Account", self.create_account, self.colors['success']),
            ("View Balance", self.view_balance, self.colors['primary']),
            ("Deposit Money", self.deposit_money, self.colors['success']),
            ("Withdraw Money", self.withdraw_money, self.colors['warning']),
            ("Transfer Money", self.transfer_money, self.colors['primary']),
            ("Transaction History", self.view_transactions, self.colors['secondary'])
        ]
        
        for text, command, color in operations:
            btn = tk.Button(left_panel, text=text, command=command,
                           bg=color, fg='white', font=('Segoe UI', 10, 'bold'),
                           relief='flat', cursor='hand2', pady=8)
            btn.pack(fill=tk.X, padx=15, pady=5)
        
        # Right panel - account info
        right_panel = self.create_card_frame(operations_frame, "📋 Account Information")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        self.account_info_text = tk.Text(right_panel, height=15, font=('Consolas', 10),
                                        wrap=tk.WORD, state=tk.DISABLED)
        self.account_info_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.refresh_account_info()

    def build_products_tab(self):
        """Build the products browsing interface"""
        # Search and filter frame
        search_frame = tk.Frame(self.products_frame, bg=self.colors['light'])
        search_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(search_frame, text="🔍 Search Products:", 
                font=('Segoe UI', 12, 'bold'), bg=self.colors['light']).pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                               font=('Segoe UI', 11), width=30)
        search_entry.pack(side=tk.LEFT, padx=10)
        search_entry.bind('<KeyRelease>', self.filter_products)
        
        # Category filter
        tk.Label(search_frame, text="📂 Category:", 
                font=('Segoe UI', 12, 'bold'), bg=self.colors['light']).pack(side=tk.LEFT, padx=(20, 5))
        
        self.category_var = tk.StringVar(value="All")
        category_combo = ttk.Combobox(search_frame, textvariable=self.category_var,
                                     values=["All"] + self.categories, state="readonly")
        category_combo.pack(side=tk.LEFT, padx=5)
        category_combo.bind('<<ComboboxSelected>>', self.filter_products)
        
        # Products display frame
        products_container = tk.Frame(self.products_frame, bg=self.colors['light'])
        products_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create canvas for scrollable products
        self.products_canvas = tk.Canvas(products_container, bg='white')
        products_scrollbar = ttk.Scrollbar(products_container, orient="vertical", 
                                          command=self.products_canvas.yview)
        self.products_inner_frame = tk.Frame(self.products_canvas, bg='white')
        
        self.products_canvas.configure(yscrollcommand=products_scrollbar.set)
        self.products_canvas.bind('<Configure>', 
                                 lambda e: self.products_canvas.configure(scrollregion=self.products_canvas.bbox("all")))
        self.products_canvas.create_window((0, 0), window=self.products_inner_frame, anchor="nw")
        
        self.products_canvas.pack(side="left", fill="both", expand=True)
        products_scrollbar.pack(side="right", fill="y")
        
        self.display_products()

    def build_cart_tab(self):
        """Build the shopping cart interface"""
        # Cart header
        header_frame = self.create_card_frame(self.cart_frame, "🛍️ Shopping Cart")
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Cart content
        content_frame = tk.Frame(self.cart_frame, bg=self.colors['light'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left panel - cart items
        left_panel = self.create_card_frame(content_frame, "📦 Cart Items")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.cart_items_frame = tk.Frame(left_panel, bg='white')
        self.cart_items_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Right panel - order summary
        right_panel = self.create_card_frame(content_frame, "💰 Order Summary")
        right_panel.config(width=300)  # Set width on the widget itself
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        self.order_summary_frame = tk.Frame(right_panel, bg='white')
        self.order_summary_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Checkout button
        checkout_btn = tk.Button(right_panel, text="🛒 Proceed to Checkout",
                               command=self.checkout, bg=self.colors['success'], 
                               fg='white', font=('Segoe UI', 12, 'bold'),
                               relief='flat', cursor='hand2', pady=10)
        checkout_btn.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.refresh_cart_display()

    def build_profile_tab(self):
        """Build the user profile interface"""
        if not self.is_logged_in:
            self.build_login_interface()
        else:
            self.build_user_profile_interface()

    def build_ai_tab(self):
        """Build the enhanced AI assistant interface with advanced features"""
        # AI header with model selection
        header_frame = self.create_card_frame(self.ai_frame, "🤖 Advanced AI Assistant")
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Status and model selection
        status_frame = tk.Frame(header_frame, bg='white')
        status_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Enhanced AI provider status
        active_providers = ai_manager.get_active_providers()
        current_provider_info = ai_manager.providers.get(ai_manager.current_provider, {})
        
        if ai_manager.current_provider and ai_manager.current_provider != "offline":
            provider_name = current_provider_info.get("name", ai_manager.current_provider)
            status_text = f"🟢 Online - {provider_name}: {ai_manager.current_model}"
            status_color = self.colors['success']
        else:
            status_text = "🟡 Offline Mode - Enhanced Responses"
            status_color = self.colors['warning']
        
        # Main status display
        status_label = tk.Label(status_frame, text=status_text, 
                               font=('Segoe UI', 11, 'bold'), bg='white', fg=status_color)
        status_label.pack(side=tk.LEFT)
        
        # Provider count and fallback info
        if len(active_providers) > 1:
            fallback_info = tk.Label(status_frame, 
                                   text=f"({len(active_providers)} providers available)", 
                                   font=('Segoe UI', 9), bg='white', fg=self.colors['secondary'])
            fallback_info.pack(side=tk.LEFT, padx=(10, 0))
        
        # Model/Provider selection
        if len(active_providers) > 0:
            # Provider selection dropdown
            tk.Label(status_frame, text="Provider:", 
                    font=('Segoe UI', 10), bg='white').pack(side=tk.RIGHT, padx=(20, 5))
            
            self.provider_var = tk.StringVar(value=ai_manager.current_provider)
            provider_options = [name for name in active_providers.keys()]
            provider_combo = ttk.Combobox(status_frame, textvariable=self.provider_var,
                                        values=provider_options, state="readonly", width=12)
            provider_combo.pack(side=tk.RIGHT, padx=5)
            provider_combo.bind('<<ComboboxSelected>>', self.change_ai_provider)
            
            # Model selection for current provider
            if ai_manager.current_provider in active_providers:
                available_models_current = active_providers[ai_manager.current_provider]["models"]
                if len(available_models_current) > 1:
                    tk.Label(status_frame, text="Model:", 
                            font=('Segoe UI', 10), bg='white').pack(side=tk.RIGHT, padx=(20, 5))
                    
                    self.model_var = tk.StringVar(value=ai_manager.current_model)
                    model_combo = ttk.Combobox(status_frame, textvariable=self.model_var,
                                              values=available_models_current, state="readonly", width=15)
                    model_combo.pack(side=tk.RIGHT, padx=5)
                    model_combo.bind('<<ComboboxSelected>>', self.change_ai_model)
        
        # AI capabilities info
        capabilities_frame = tk.Frame(header_frame, bg='white')
        capabilities_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        capabilities_text = "💡 I can help with: Banking operations • Product shopping • System navigation • Troubleshooting • Data analysis"
        tk.Label(capabilities_frame, text=capabilities_text, 
                font=('Segoe UI', 9), bg='white', fg=self.colors['text'], wraplength=800).pack()
        
        # Enhanced AI Provider Management Panel
        if len(active_providers) > 1:
            provider_panel = tk.Frame(header_frame, bg='white')
            provider_panel.pack(fill=tk.X, padx=20, pady=(5, 10))
            
            # Provider status overview
            tk.Label(provider_panel, text="🔌 Available AI Providers:", 
                    font=('Segoe UI', 10, 'bold'), bg='white').pack(anchor='w')
            
            providers_info_frame = tk.Frame(provider_panel, bg='white')
            providers_info_frame.pack(fill=tk.X, pady=5)
            
            for provider_name, provider_info in active_providers.items():
                if provider_name == "offline":
                    continue  # Skip offline in detailed view
                    
                # Provider status indicator
                is_current = provider_name == ai_manager.current_provider
                status_color = self.colors['success'] if is_current else self.colors['secondary']
                status_icon = "🟢" if is_current else "⚪"
                
                provider_status = tk.Frame(providers_info_frame, bg='white')
                provider_status.pack(side=tk.LEFT, padx=(0, 20))
                
                tk.Label(provider_status, text=f"{status_icon} {provider_info['name']}", 
                        font=('Segoe UI', 9, 'bold' if is_current else 'normal'), 
                        bg='white', fg=status_color).pack(anchor='w')
                
                models_text = f"Models: {', '.join(provider_info['models'])}"
                tk.Label(provider_status, text=models_text, 
                        font=('Segoe UI', 8), bg='white', fg=self.colors['text']).pack(anchor='w')
        
        # Chat controls frame with enhanced features
        controls_frame = tk.Frame(self.ai_frame, bg=self.colors['light'])
        controls_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Chat history search
        search_frame = tk.Frame(controls_frame, bg=self.colors['light'])
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="🔍 Search Chat:", 
                font=('Segoe UI', 10), bg=self.colors['light']).pack(side=tk.LEFT)
        
        self.chat_search_var = tk.StringVar()
        chat_search_entry = tk.Entry(search_frame, textvariable=self.chat_search_var, 
                                    font=('Segoe UI', 10), width=25)
        chat_search_entry.pack(side=tk.LEFT, padx=10)
        chat_search_entry.bind('<KeyRelease>', lambda e: self.filter_chat_history())
        
        # Chat filter options
        tk.Label(search_frame, text="Filter:", 
                font=('Segoe UI', 10), bg=self.colors['light']).pack(side=tk.LEFT, padx=(20, 5))
        
        self.chat_filter_var = tk.StringVar(value="All Messages")
        chat_filter_combo = ttk.Combobox(search_frame, textvariable=self.chat_filter_var,
                                        values=["All Messages", "My Messages", "AI Responses", 
                                               "Banking Questions", "Shopping Questions", "Recent (Today)"], 
                                        state="readonly", width=15)
        chat_filter_combo.pack(side=tk.LEFT, padx=5)
        chat_filter_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_chat_history())
        
        # Quick actions with enhanced suggestions
        actions_frame = tk.Frame(controls_frame, bg=self.colors['light'])
        actions_frame.pack(fill=tk.X, padx=10, pady=5)
        
        quick_actions = [
            ("💳 Banking Help", "How do I manage my bank accounts and perform transactions?"),
            ("🛒 Shopping Guide", "Help me understand the shopping features and checkout process."),
            ("🔍 Search Features", "Explain the advanced search and filtering capabilities."),
            ("🔒 Security Info", "What security features protect my data and transactions?"),
            ("📊 My Account", "Show me my account summary and current status."),
            ("⚡ Quick Start", "I'm new here. Give me a quick overview of key features.")
        ]
        
        for i, (label, message) in enumerate(quick_actions):
            if i < 3:  # First row
                row_frame = actions_frame if i == 0 else actions_frame
            else:  # Second row
                if i == 3:
                    row_frame = tk.Frame(actions_frame, bg=self.colors['light'])
                    row_frame.pack(fill=tk.X, pady=2)
            
            btn = tk.Button(row_frame, text=label, 
                           command=lambda msg=message: self.send_quick_message(msg),
                           bg=self.colors['secondary'], fg='white', 
                           font=('Segoe UI', 8), relief='flat', cursor='hand2')
            btn.pack(side=tk.LEFT, padx=2)
        
        # Chat management buttons
        management_frame = tk.Frame(controls_frame, bg=self.colors['light'])
        management_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Left side - analysis buttons
        analysis_frame = tk.Frame(management_frame, bg=self.colors['light'])
        analysis_frame.pack(side=tk.LEFT)
        
        tk.Button(analysis_frame, text="📈 Chat Analytics", 
                 command=self.show_chat_analytics,
                 bg=self.colors['primary'], fg='white', 
                 font=('Segoe UI', 8), relief='flat', cursor='hand2').pack(side=tk.LEFT, padx=2)
        
        tk.Button(analysis_frame, text="💾 Save Session", 
                 command=self.save_chat_session,
                 bg=self.colors['success'], fg='white', 
                 font=('Segoe UI', 8), relief='flat', cursor='hand2').pack(side=tk.LEFT, padx=2)
        
        # Right side - management buttons
        management_buttons = tk.Frame(management_frame, bg=self.colors['light'])
        management_buttons.pack(side=tk.RIGHT)
        
        tk.Button(management_buttons, text="📄 Export Chat", 
                 command=self.export_chat_history,
                 bg=self.colors['primary'], fg='white', 
                 font=('Segoe UI', 8), relief='flat', cursor='hand2').pack(side=tk.LEFT, padx=2)
        
        tk.Button(management_buttons, text="🗑️ Clear Chat", 
                 command=self.clear_chat_history,
                 bg=self.colors['warning'], fg='white', 
                 font=('Segoe UI', 8), relief='flat', cursor='hand2').pack(side=tk.LEFT, padx=2)
        
        # Enhanced chat interface
        chat_frame = tk.Frame(self.ai_frame, bg=self.colors['light'])
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Chat display with scrollbar and enhanced styling
        chat_container = tk.Frame(chat_frame, bg='white', relief='solid', bd=1)
        chat_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create scrollable text widget
        self.chat_display = tk.Text(chat_container, height=20, font=('Segoe UI', 10),
                                   wrap=tk.WORD, state=tk.DISABLED, bg='white',
                                   selectbackground=self.colors['primary'], selectforeground='white')
        
        chat_scrollbar = ttk.Scrollbar(chat_container, orient="vertical", command=self.chat_display.yview)
        self.chat_display.configure(yscrollcommand=chat_scrollbar.set)
        
        self.chat_display.pack(side="left", fill=tk.BOTH, expand=True)
        chat_scrollbar.pack(side="right", fill="y")
        
        # Configure enhanced text tags for styling
        self.chat_display.tag_configure("user", foreground=self.colors['primary'], font=('Segoe UI', 10, 'bold'))
        self.chat_display.tag_configure("assistant", foreground=self.colors['success'], font=('Segoe UI', 10))
        self.chat_display.tag_configure("timestamp", foreground=self.colors['text'], font=('Segoe UI', 8))
        self.chat_display.tag_configure("highlight", background=self.colors['warning'], foreground='white')
        self.chat_display.tag_configure("system", foreground=self.colors['secondary'], font=('Segoe UI', 9, 'italic'))
        self.chat_display.tag_configure("error", foreground=self.colors['danger'], font=('Segoe UI', 9))
        
        # Enhanced input frame with features
        input_container = tk.Frame(chat_frame, bg=self.colors['light'])
        input_container.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Input suggestions
        suggestions_frame = tk.Frame(input_container, bg=self.colors['light'])
        suggestions_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.suggestions_label = tk.Label(suggestions_frame, text="💭 Suggestions: Try asking about specific features, operations, or troubleshooting help",
                                         font=('Segoe UI', 9), bg=self.colors['light'], fg=self.colors['text'])
        self.suggestions_label.pack(side=tk.LEFT)
        
        # Message input with placeholder and enhanced features
        input_frame = tk.Frame(input_container, bg='white', relief='solid', bd=1)
        input_frame.pack(fill=tk.X, pady=5)
        
        # Input area with support for multiline
        self.chat_input = tk.Text(input_frame, height=3, font=('Segoe UI', 11), 
                                 wrap=tk.WORD, bg='white', border=0)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=5)
        self.chat_input.bind('<Return>', self.send_ai_message)
        self.chat_input.bind('<Control-Return>', lambda e: self.chat_input.insert(tk.INSERT, '\n'))
        self.chat_input.bind('<KeyRelease>', self.update_input_suggestions)
        
        # Insert placeholder text
        self.chat_input.insert(1.0, "Ask me anything about banking, shopping, or system features... (Press Enter to send, Ctrl+Enter for new line)")
        self.chat_input.bind('<FocusIn>', self.clear_placeholder)
        self.chat_input.bind('<FocusOut>', self.restore_placeholder)
        
        # Enhanced send button with icons
        button_frame = tk.Frame(input_frame, bg='white')
        button_frame.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Voice input button (placeholder for future feature)
        voice_btn = tk.Button(button_frame, text="🎤", 
                             command=self.voice_input_placeholder,
                             bg=self.colors['light'], fg=self.colors['text'], 
                             font=('Segoe UI', 10), cursor='hand2', relief='flat', width=3)
        voice_btn.pack(side=tk.TOP, pady=1)
        
        # Send button
        send_btn = tk.Button(button_frame, text="Send", command=self.send_ai_message,
                           bg=self.colors['primary'], fg='white', 
                           font=('Segoe UI', 10, 'bold'), cursor='hand2', relief='flat')
        send_btn.pack(side=tk.BOTTOM, pady=1)
        
        # Chat history storage and initialization
        if not hasattr(self, 'chat_history'):
            self.chat_history = []
        
        # Add enhanced welcome message
        self.add_chat_message("AI Assistant", 
                             "🌟 Welcome to the Advanced AI Assistant! I'm here to help you with banking operations, shopping, system navigation, and much more.\n\n💡 **Quick Start Tips:**\n• Ask specific questions for detailed guidance\n• Use the quick action buttons above\n• Try commands like 'show my account status' or 'help with checkout'\n• I can provide step-by-step instructions for any feature\n\nWhat would you like to explore today?",
                             "assistant")
    
    def change_ai_model(self, event=None):
        """Change the AI model being used"""
        global current_model
        if hasattr(self, 'model_var'):
            new_model = self.model_var.get()
            current_provider_models = ai_manager.providers[ai_manager.current_provider]["models"]
            if new_model != ai_manager.current_model and new_model in current_provider_models:
                ai_manager.current_model = new_model
                current_model = new_model  # Update legacy variable
                self.add_chat_message("System", 
                                     f"🔄 Switched to model: {new_model}",
                                     "system")
                # Update status bar
                self.update_ai_status()
    
    def change_ai_provider(self, event=None):
        """Change the AI provider being used"""
        if hasattr(self, 'provider_var'):
            new_provider = self.provider_var.get()
            if new_provider != ai_manager.current_provider:
                # Switch provider using AI manager
                success = ai_manager.switch_provider(new_provider)
                if success:
                    provider_name = ai_manager.providers[new_provider]["name"]
                    self.add_chat_message("System", 
                                         f"🔄 Switched to AI provider: {provider_name} ({ai_manager.current_model})",
                                         "system")
                    # Update status bar and rebuild AI tab for new model options
                    self.update_ai_status()
                    self.notification_manager.show_notification(f"Switched to {provider_name}", "success")
                else:
                    self.notification_manager.show_notification("Failed to switch provider", "error")
                    # Reset combo box to current provider
                    self.provider_var.set(ai_manager.current_provider)
    
    def update_ai_status(self):
        """Update AI status in status bar and AI tab"""
        if hasattr(self, 'ai_status_label'):
            active_providers = ai_manager.get_active_providers()
            if ai_manager.current_provider and ai_manager.current_provider != "offline":
                provider_name = ai_manager.providers[ai_manager.current_provider]["name"]
                status_text = f"🟢 AI: {provider_name} ({ai_manager.current_model})"
            elif len(active_providers) > 1:
                status_text = f"🟡 AI: {len(active_providers)-1} providers available"
            else:
                status_text = "🟡 AI: Offline mode"
            
            self.ai_status_label.config(text=status_text)
    
    def voice_input_placeholder(self):
        """Placeholder for voice input feature"""
        self.notification_manager.show_notification("🎤 Voice input feature coming soon!", "info")
    
    def clear_placeholder(self, event):
        """Clear placeholder text when input is focused"""
        current_text = self.chat_input.get(1.0, tk.END).strip()
        if "Ask me anything about banking" in current_text:
            self.chat_input.delete(1.0, tk.END)
    
    def restore_placeholder(self, event):
        """Restore placeholder text if input is empty"""
        current_text = self.chat_input.get(1.0, tk.END).strip()
        if not current_text:
            self.chat_input.insert(1.0, "Ask me anything about banking, shopping, or system features... (Press Enter to send, Ctrl+Enter for new line)")
    
    def update_input_suggestions(self, event):
        """Update input suggestions based on current text"""
        current_text = self.chat_input.get(1.0, tk.END).strip().lower()
        
        if len(current_text) < 3 or "ask me anything" in current_text:
            suggestion = "💭 Suggestions: Try asking about specific features, operations, or troubleshooting help"
        elif any(word in current_text for word in ['bank', 'account', 'money', 'balance']):
            suggestion = "💳 Banking: Try 'create account', 'check balance', 'transfer money', or 'transaction history'"
        elif any(word in current_text for word in ['shop', 'buy', 'cart', 'product']):
            suggestion = "🛒 Shopping: Try 'browse products', 'add to cart', 'checkout process', or 'order status'"
        elif any(word in current_text for word in ['search', 'find', 'filter']):
            suggestion = "🔍 Search: Try 'search features', 'filter options', or 'advanced search'"
        elif any(word in current_text for word in ['help', 'how', 'guide']):
            suggestion = "📚 Help: Try 'getting started', 'navigation guide', or 'feature overview'"
        else:
            suggestion = "✨ I can help with banking, shopping, navigation, troubleshooting, and more!"
        
        if hasattr(self, 'suggestions_label'):
            self.suggestions_label.config(text=suggestion)
    
    def show_chat_analytics(self):
        """Show chat analytics and statistics"""
        if not hasattr(self, 'chat_history') or not self.chat_history:
            self.notification_manager.show_notification("No chat history to analyze", "info")
            return
        
        analytics_window = tk.Toplevel(self)
        analytics_window.title("Chat Analytics")
        analytics_window.geometry("600x500")
        analytics_window.configure(bg='white')
        
        # Analytics content
        analytics_frame = tk.Frame(analytics_window, bg='white')
        analytics_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(analytics_frame, text="📈 Chat Analytics", 
                font=('Segoe UI', 16, 'bold'), bg='white').pack(pady=10)
        
        # Calculate statistics
        total_messages = len(self.chat_history)
        user_messages = len([m for m in self.chat_history if m['type'] == 'user'])
        ai_messages = len([m for m in self.chat_history if m['type'] == 'assistant'])
        
        # Create statistics display
        stats_text = f"""
📊 **Message Statistics:**
• Total Messages: {total_messages}
• Your Messages: {user_messages}
• AI Responses: {ai_messages}

🕒 **Session Info:**
• First Message: {self.chat_history[0]['timestamp'][:19] if self.chat_history else 'N/A'}
• Latest Message: {self.chat_history[-1]['timestamp'][:19] if self.chat_history else 'N/A'}

📝 **Topics Discussed:**
"""
        
        # Analyze topics
        all_messages = ' '.join([m['message'].lower() for m in self.chat_history if m['type'] == 'user'])
        topics = {
            'Banking': len([w for w in ['bank', 'account', 'money', 'deposit', 'withdraw', 'transfer'] if w in all_messages]),
            'Shopping': len([w for w in ['shop', 'cart', 'buy', 'product', 'checkout'] if w in all_messages]),
            'Technical': len([w for w in ['search', 'filter', 'help', 'guide', 'feature'] if w in all_messages]),
        }
        
        for topic, count in topics.items():
            if count > 0:
                stats_text += f"• {topic}: {count} mentions\n"
        
        text_widget = tk.Text(analytics_frame, font=('Segoe UI', 10), wrap=tk.WORD, height=15)
        text_widget.pack(fill=tk.BOTH, expand=True, pady=10)
        text_widget.insert(1.0, stats_text)
        text_widget.config(state=tk.DISABLED)
        
        tk.Button(analytics_frame, text="Close", command=analytics_window.destroy,
                 bg=self.colors['secondary'], fg='white', 
                 font=('Segoe UI', 10, 'bold')).pack(pady=10)
    
    def save_chat_session(self):
        """Save current chat session"""
        try:
            if not hasattr(self, 'chat_history') or not self.chat_history:
                self.notification_manager.show_notification("No chat session to save", "info")
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_session_{timestamp}.json"
            
            session_data = {
                'timestamp': datetime.now().isoformat(),
                'user': self.current_user.get('name', 'Guest') if self.is_logged_in else 'Guest',
                'total_messages': len(self.chat_history),
                'chat_history': self.chat_history
            }
            
            if save_json(filename, session_data):
                self.notification_manager.show_notification(f"Chat session saved as {filename}", "success")
            else:
                self.notification_manager.show_notification("Failed to save chat session", "error")
                
        except Exception as e:
            self.notification_manager.show_notification(f"Save failed: {str(e)}", "error")

    def build_help_tab(self):
        """Build the help interface"""
        # Create scrollable help content
        canvas = tk.Canvas(self.help_frame, bg=self.colors['light'])
        scrollbar = ttk.Scrollbar(self.help_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['light'])
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Help sections
        sections = [
            ("🏠 Getting Started", "Learn how to navigate and use the application"),
            ("🏦 Banking Guide", "How to manage accounts, transfer money, and view transactions"),
            ("🛒 Shopping Guide", "Browse products, add to cart, and checkout"),
            ("🤖 AI Assistant", "Get help from our intelligent assistant"),
            ("⚙️ Settings", "Customize your experience"),
            ("🔒 Security", "Keep your account safe and secure")
        ]
        
        for title, description in sections:
            section_frame = self.create_card_frame(scrollable_frame, title)
            section_frame.pack(fill=tk.X, padx=20, pady=10)
            
            desc_label = tk.Label(section_frame, text=description,
                                 font=('Segoe UI', 11), bg='white', 
                                 fg=self.colors['dark'])
            desc_label.pack(padx=20, pady=15)

    # Utility methods
    def create_card_frame(self, parent, title=""):
        """Create a card-style frame"""
        card = tk.Frame(parent, bg='white', relief='solid', bd=1)
        
        if title:
            title_frame = tk.Frame(card, bg=self.colors['light'])
            title_frame.pack(fill=tk.X)
            
            title_label = tk.Label(title_frame, text=title, 
                                  font=('Segoe UI', 12, 'bold'),
                                  bg=self.colors['light'], fg=self.colors['dark'])
            title_label.pack(pady=10)
        
        return card

    def create_modern_button(self, parent, text, command, style='primary'):
        """Create a modern styled button"""
        color = self.colors.get(style, self.colors['primary'])
        btn = tk.Button(parent, text=text, command=command,
                       bg=color, fg='white', font=('Segoe UI', 10, 'bold'),
                       relief='flat', cursor='hand2', pady=8)
        return btn

    def update_user_info_display(self):
        """Update user info in navigation bar"""
        # Clear existing content
        for widget in self.user_info_frame.winfo_children():
            widget.destroy()
        
        # Clear admin quick access
        if hasattr(self, 'admin_quick_frame'):
            for widget in self.admin_quick_frame.winfo_children():
                widget.destroy()
        
        if self.is_logged_in and self.current_user:
            # Show role for admin users
            if self.current_user.get('role') == 'admin':
                user_text = f"🔐 {self.current_user['name']} (Admin)"
                
                # Add admin quick access buttons
                if hasattr(self, 'admin_quick_frame'):
                    # Quick Add Product button
                    quick_add_btn = tk.Button(self.admin_quick_frame, text="➕ Quick Add Product",
                                            command=self.quick_add_product_dialog,
                                            bg='#28a745', fg='white', font=('Segoe UI', 9, 'bold'),
                                            border=0, cursor='hand2', padx=10, pady=2)
                    quick_add_btn.pack(side=tk.LEFT, padx=5)
                    
                    # Admin Panel button
                    admin_panel_btn = tk.Button(self.admin_quick_frame, text="🔐 Admin Panel",
                                               command=self.open_admin_window,
                                               bg='#dc3545', fg='white', font=('Segoe UI', 9, 'bold'),
                                               border=0, cursor='hand2', padx=10, pady=2)
                    admin_panel_btn.pack(side=tk.LEFT, padx=5)
            else:
                user_text = f"👤 {self.current_user['name']}"
            
            user_label = tk.Label(self.user_info_frame, 
                                 text=user_text, 
                                 bg=self.colors['primary'], fg='white',
                                 font=('Segoe UI', 10))
            user_label.pack(side=tk.LEFT, padx=10)
            
            logout_btn = tk.Button(self.user_info_frame, text="Logout",
                                  command=self.logout_user, bg=self.colors['danger'],
                                  fg='white', font=('Segoe UI', 9), border=0, cursor='hand2')
            logout_btn.pack(side=tk.LEFT)
        else:
            login_btn = tk.Button(self.user_info_frame, text="Login",
                                 command=self.show_login_dialog, bg=self.colors['success'],
                                 fg='white', font=('Segoe UI', 10), border=0, cursor='hand2')
            login_btn.pack(side=tk.LEFT, padx=5)
    
    def quick_add_product_dialog(self):
        """Quick dialog to add new product (simplified version for admin)"""
        if not self.is_logged_in or not self.current_user or self.current_user.get('role') != 'admin':
            messagebox.showerror("Access Denied", "Admin privileges required")
            return
        
        dialog = tk.Toplevel(self)
        dialog.title("➕ Quick Add Product")
        dialog.geometry("600x700")
        dialog.configure(bg='white')
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        x = self.winfo_x() + (self.winfo_width() // 2) - 300
        y = self.winfo_y() + (self.winfo_height() // 2) - 250
        dialog.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(dialog, bg='#28a745', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="➕ Quick Add Product", 
                font=('Segoe UI', 16, 'bold'),
                bg='#28a745', fg='white').pack(pady=15)
        
        # Form
        form_frame = tk.Frame(dialog, bg='white')
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Product Name
        tk.Label(form_frame, text="📦 Product Name:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        name_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=50)
        name_entry.pack(pady=(0,15), ipady=5)
        
        # Category
        tk.Label(form_frame, text="🏷️ Category:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        category_var = tk.StringVar(value="Electronics")
        categories = ["Electronics", "Clothing", "Books", "Home & Garden", "Sports", "Food & Beverages", "Other"]
        category_combo = ttk.Combobox(form_frame, textvariable=category_var,
                                     values=categories, width=47)
        category_combo.pack(pady=(0,15), ipady=5)
        
        # Price
        tk.Label(form_frame, text="💰 Price (₹):", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        price_entry = tk.Entry(form_frame, font=('Segoe UI', 12), width=50)
        price_entry.pack(pady=(0,15), ipady=5)
        
        # Description
        tk.Label(form_frame, text="📝 Description:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,5))
        desc_text = tk.Text(form_frame, font=('Segoe UI', 11), width=50, height=4)
        desc_text.pack(pady=(0,15))
        
        # Quick action to add default images
        def add_sample_images():
            return [
                "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=400",
                "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400"
            ]
        
        def save_quick_product():
            try:
                name = name_entry.get().strip()
                category = category_var.get()
                price = float(price_entry.get() or 0)
                description = desc_text.get("1.0", tk.END).strip()
                
                if not name:
                    messagebox.showerror("Error", "Please enter product name", parent=dialog)
                    return
                
                if price <= 0:
                    messagebox.showerror("Error", "Please enter valid price", parent=dialog)
                    return
                
                # Generate product ID
                product_id = f"PRD{len(self.products) + 1:04d}"
                
                # Create product with default values
                new_product = {
                    'id': product_id,
                    'name': name,
                    'category': category,
                    'price': price,
                    'stock': 10,  # Default stock
                    'description': description,
                    'images': add_sample_images(),
                    'rating': 0.0,
                    'reviews': 0,
                    'created_date': datetime.now().isoformat(),
                    'created_by': 'admin'
                }
                
                # Add to products list
                self.products.append(new_product)
                
                # Save to file
                save_json(FILES['PRODUCTS'], self.products)
                
                dialog.destroy()
                self.display_products()  # Refresh products display
                messagebox.showinfo("Success", f"Product '{name}' added successfully!\n\nID: {product_id}\nStock: 10 (default)\nImages: 2 sample images added")
                
            except ValueError as e:
                messagebox.showerror("Error", "Please enter valid price", parent=dialog)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add product: {str(e)}", parent=dialog)
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg='white')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="✅ Add Product", command=save_quick_product,
                 bg='#28a745', fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2', padx=20, pady=8).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="🔧 Advanced Add", 
                 command=lambda: [dialog.destroy(), self.open_admin_window()],
                 bg='#007bff', fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2', padx=20, pady=8).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy,
                 bg='#dc3545', fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2', padx=20, pady=8).pack(side=tk.LEFT, padx=10)
        
        # Focus on name field
        name_entry.focus_set()

    def update_time(self):
        """Update the time display"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.after(1000, self.update_time)

    # Continue with more methods...
    def create_default_admin(self):
        """Create default admin user if not exists"""
        admin_email = "admin@banking.com"
        if admin_email not in self.users:
            # Create default admin user
            admin_user = {
                "name": "System Admin",
                "email": admin_email,
                "password": hash_password("admin123"),  # Default password
                "role": "admin",
                "is_active": True,
                "created_date": datetime.now().isoformat()
            }
            self.users[admin_email] = admin_user
            save_json(FILES['USERS'], self.users)
            
            # Show admin credentials in console
            print("🔐 Default admin user created:")
            print(f"   Email: {admin_email}")
            print(f"   Password: admin123")
            print("   Please change the default password after first login!")
    
    def get_default_products(self):
        """Get default product catalog"""
        return [
            {
                "id": "p001", 
                "name": "Laptop", 
                "price": 45000, 
                "category": "Electronics", 
                "description": "High-performance laptop with latest processor and graphics",
                "images": [
                    "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400",
                    "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=400",
                    "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=400"
                ]
            },
            {
                "id": "p002", 
                "name": "Smartphone", 
                "price": 25000, 
                "category": "Electronics", 
                "description": "Latest smartphone with advanced camera and features",
                "images": [
                    "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400",
                    "https://images.unsplash.com/photo-1520923642038-b4259acccb15?w=400",
                    "https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=400"
                ]
            },
            {
                "id": "p003", 
                "name": "T-Shirt", 
                "price": 500, 
                "category": "Clothing", 
                "description": "Premium cotton t-shirt with comfortable fit",
                "images": [
                    "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400",
                    "https://images.unsplash.com/photo-1571945153237-4929e783af4a?w=400",
                    "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=400"
                ]
            },
            {
                "id": "p004", 
                "name": "Book", 
                "price": 300, 
                "category": "Books", 
                "description": "Comprehensive programming book for beginners and experts",
                "images": [
                    "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400",
                    "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400",
                    "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400"
                ]
            },
            {
                "id": "p005", 
                "name": "Headphones", 
                "price": 2000, 
                "category": "Electronics", 
                "description": "Wireless headphones with noise cancellation",
                "images": [
                    "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400",
                    "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=400",
                    "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=400"
                ]
            }
        ]

    def migrate_product_images(self):
        """Migrate old product format to new image structure"""
        try:
            updated = False
            for product in self.products:
                # Check if product has old 'image' field instead of 'images' array
                if 'image' in product and 'images' not in product:
                    # Convert single image to images array
                    old_image = product.get('image', '')
                    if old_image:
                        product['images'] = [old_image]
                    else:
                        product['images'] = ["https://via.placeholder.com/400x300?text=No+Image"]
                    
                    # Remove old image field
                    del product['image']
                    updated = True
                    
                # Ensure images field exists and is a list
                elif 'images' not in product:
                    product['images'] = ["https://via.placeholder.com/400x300?text=No+Image"]
                    updated = True
                    
                # Ensure images is a list (not a string)
                elif isinstance(product.get('images'), str):
                    product['images'] = [product['images']]
                    updated = True
            
            # Save updated products if migration occurred
            if updated:
                save_json(FILES['PRODUCTS'], self.products)
                print("✅ Product image format migrated successfully")
                
        except Exception as e:
            print(f"⚠️ Error during product migration: {str(e)}")

    # Session management
    def start_auto_logout_timer(self):
        if self.auto_logout_timer:
            self.after_cancel(self.auto_logout_timer)
        timeout = self.settings.get('auto_logout_minutes', 30) * 60 * 1000
        self.auto_logout_timer = self.after(timeout, self.auto_logout)

    def reset_activity_timer(self):
        if self.is_logged_in:
            self.session.update_activity()
            self.start_auto_logout_timer()

    def auto_logout(self):
        if self.is_logged_in:
            self.notification_manager.show_notification(
                "Automatically logged out due to inactivity", "warning"
            )
            self.logout_user()

    # Banking methods (implement these based on your needs)
    def create_account(self):
        """Create a new bank account"""
        if not self.is_logged_in:
            self.show_login_required_message()
            return
        
        dialog = AccountDialog(self, "Create Account")
        if dialog.result:
            name, initial_balance, account_type = dialog.result
            success, message = self.bank.create_account(
                name, initial_balance, account_type, 
                self.current_user['email']
            )
            
            if success:
                self.notification_manager.show_notification(message, "success")
                self.refresh_account_info()
            else:
                self.notification_manager.show_notification(message, "error")

    def view_balance(self):
        """View account balance"""
        if not self.is_logged_in:
            self.show_login_required_message()
            return
        
        account_id = simpledialog.askstring("Account Balance", "Enter Account ID:")
        if account_id:
            success, message = self.bank.get_balance(account_id)
            if success:
                self.notification_manager.show_notification(message, "success")
            else:
                self.notification_manager.show_notification(message, "error")

    def deposit_money(self):
        """Deposit money to account"""
        if not self.is_logged_in:
            self.show_login_required_message()
            return
        
        dialog = TransactionDialog(self, "Deposit Money", "deposit")
        if dialog.result:
            account_id, amount, description = dialog.result
            if not description:
                description = "Deposit"
            
            success, message = self.bank.deposit(account_id, amount, description)
            if success:
                self.notification_manager.show_notification(message, "success")
                self.refresh_account_info()
            else:
                self.notification_manager.show_notification(message, "error")

    def withdraw_money(self):
        """Withdraw money from account"""
        if not self.is_logged_in:
            self.show_login_required_message()
            return
        
        dialog = TransactionDialog(self, "Withdraw Money", "withdraw")
        if dialog.result:
            account_id, amount, description = dialog.result
            if not description:
                description = "Withdrawal"
            
            success, message = self.bank.withdraw(account_id, amount, description)
            if success:
                self.notification_manager.show_notification(message, "success")
                self.refresh_account_info()
            else:
                self.notification_manager.show_notification(message, "error")

    def transfer_money(self):
        """Transfer money between accounts"""
        if not self.is_logged_in:
            self.show_login_required_message()
            return
        
        dialog = TransactionDialog(self, "Transfer Money", "transfer")
        if dialog.result:
            from_account, to_account, amount, description = dialog.result
            if not description:
                description = "Transfer"
            
            success, message = self.bank.transfer(from_account, to_account, amount, description)
            if success:
                self.notification_manager.show_notification(message, "success")
                self.refresh_account_info()
            else:
                self.notification_manager.show_notification(message, "error")

    def view_transactions(self):
        """View transaction history"""
        if not self.is_logged_in:
            self.show_login_required_message()
            return
        
        account_id = simpledialog.askstring("Transaction History", "Enter Account ID:")
        if account_id:
            transactions = self.bank.get_transactions(account_id, limit=20)
            if transactions:
                self.show_transaction_history(transactions)
            else:
                self.notification_manager.show_notification("No transactions found", "info")

    def show_transaction_history(self, transactions):
        """Display transaction history in a new window"""
        history_window = tk.Toplevel(self)
        history_window.title("Transaction History")
        history_window.geometry("800x600")
        history_window.configure(bg='white')
        
        # Create treeview for transactions
        columns = ("ID", "Date", "Description", "Type", "Amount", "Balance")
        tree = ttk.Treeview(history_window, columns=columns, show="headings", height=20)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        # Add transactions to tree
        for transaction in transactions:
            date_str = transaction['timestamp'][:19]  # Remove microseconds
            amount_str = f"₹{transaction['amount']:,.2f}"
            balance_str = f"₹{transaction['balance_after']:,.2f}"
            
            tree.insert("", "end", values=(
                transaction['id'],
                date_str,
                transaction['description'],
                transaction['type'].title(),
                amount_str,
                balance_str
            ))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Close button
        tk.Button(history_window, text="Close", command=history_window.destroy,
                 bg=self.colors['secondary'], fg='white', 
                 font=('Segoe UI', 10, 'bold')).pack(pady=10)

    def refresh_account_info(self):
        """Refresh account information display"""
        self.account_info_text.config(state=tk.NORMAL)
        self.account_info_text.delete(1.0, tk.END)
        
        if self.bank.accounts:
            info = "📋 Account Summary\n" + "="*50 + "\n\n"
            for account_id, account in self.bank.accounts.items():
                if account.get('is_active', True):
                    info += f"Account ID: {account_id}\n"
                    info += f"Name: {account['name']}\n"
                    info += f"Type: {account['type']}\n"
                    info += f"Balance: ₹{account['balance']:,.2f}\n"
                    # Safe date formatting
                    created_date = account.get('created_date', 'N/A')
                    if created_date and len(created_date) >= 10:
                        info += f"Created: {created_date[:10]}\n"
                    else:
                        info += f"Created: {created_date}\n"
                    info += "-" * 30 + "\n\n"
        else:
            info = "No accounts found.\nCreate an account to get started!"
        
        self.account_info_text.insert(1.0, info)
        self.account_info_text.config(state=tk.DISABLED)

    def create_stats_display(self, parent):
        """Create statistics display for home tab"""
        stats_frame = tk.Frame(parent, bg='white')
        stats_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # Banking stats
        total_accounts = len([acc for acc in self.bank.accounts.values() if acc.get('is_active', True)])
        total_balance = sum(acc['balance'] for acc in self.bank.accounts.values() if acc.get('is_active', True))
        
        # Shopping stats
        total_products = len(self.products)
        cart_items = sum(self.cart.items.values())
        
        stats = [
            ("🏦 Active Accounts", str(total_accounts)),
            ("💰 Total Balance", f"₹{total_balance:,.2f}"),
            ("📦 Available Products", str(total_products)),
            ("🛒 Items in Cart", str(cart_items))
        ]
        
        for i, (label, value) in enumerate(stats):
            stat_frame = tk.Frame(stats_frame, bg=self.colors['light'], relief='solid', bd=1)
            stat_frame.grid(row=0, column=i, padx=10, pady=10, sticky='ew')
            stats_frame.grid_columnconfigure(i, weight=1)
            
            tk.Label(stat_frame, text=label, font=('Segoe UI', 10),
                    bg=self.colors['light'], fg=self.colors['dark']).pack(pady=5)
            tk.Label(stat_frame, text=value, font=('Segoe UI', 14, 'bold'),
                    bg=self.colors['light'], fg=self.colors['primary']).pack(pady=5)

    def create_quick_actions(self, parent):
        """Create quick actions for home tab"""
        actions_frame = tk.Frame(parent, bg='white')
        actions_frame.pack(fill=tk.X, padx=20, pady=15)
        
        actions = [
            ("🏦 Create Account", self.create_account, self.colors['success']),
            ("💰 Check Balance", self.view_balance, self.colors['primary']),
            ("🛒 Browse Products", lambda: self.notebook.select(2), self.colors['warning']),
            ("🤖 Ask AI Assistant", lambda: self.notebook.select(5), self.colors['secondary'])
        ]
        
        for i, (text, command, color) in enumerate(actions):
            btn = tk.Button(actions_frame, text=text, command=command,
                           bg=color, fg='white', font=('Segoe UI', 10, 'bold'),
                           relief='flat', cursor='hand2', pady=8, width=15)
            btn.grid(row=0, column=i, padx=10, pady=10, sticky='ew')
            actions_frame.grid_columnconfigure(i, weight=1)

    def display_products(self):
        """Display products in the products tab"""
        # Direct display without recursion
        self._display_simple_products()
    
    def _display_simple_products(self):
        """Simple fallback product display"""
        if not hasattr(self, 'products_inner_frame'):
            return
        
        # Clear existing products
        for widget in self.products_inner_frame.winfo_children():
            widget.destroy()
        
        # Display products in grid
        row, col = 0, 0
        for product in self.products:
            product_frame = self.create_product_card(self.products_inner_frame, product)
            product_frame.grid(row=row, column=col, padx=10, pady=10, sticky='ew')
            
            col += 1
            if col >= 3:  # 3 products per row
                col = 0
                row += 1
        
        # Configure grid weights
        for i in range(3):
            self.products_inner_frame.grid_columnconfigure(i, weight=1)

    def create_product_card(self, parent, product):
        """Create an enhanced product card with modern styling and image preview"""
        card_container = tk.Frame(parent, bg=self.colors['light'])
        
        # Main card with shadow effect
        card = tk.Frame(card_container, bg='white', relief='solid', bd=1)
        card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Image section at the top
        image_frame = tk.Frame(card, bg=self.colors['light'], height=120)
        image_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        image_frame.pack_propagate(False)
        
        # Image preview
        image_label = tk.Label(image_frame, text="🖼️\nProduct Image", 
                              font=('Segoe UI', 10), bg=self.colors['light'], 
                              fg=self.colors['secondary'], justify=tk.CENTER)
        image_label.pack(expand=True)
        
        # Try to load actual product image
        self.load_product_card_image(image_label, product)
        
        # Info frame
        info_frame = tk.Frame(card, bg='white')
        info_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Product name with truncation
        name_text = product['name']
        if len(name_text) > 20:
            name_text = name_text[:17] + "..."
        
        name_label = tk.Label(info_frame, text=name_text, font=('Segoe UI', 13, 'bold'),
                             bg='white', fg=self.colors['dark'])
        name_label.pack(anchor='w')
        
        # Product category badge
        category_frame = tk.Frame(info_frame, bg='white')
        category_frame.pack(fill=tk.X, pady=(5,0))
        
        category_badge = tk.Label(category_frame, text=product['category'], 
                                 font=('Segoe UI', 9), bg='#e7f3ff', fg='#0056b3',
                                 padx=8, pady=2)
        category_badge.pack(side=tk.LEFT)
        
        # Rating stars (placeholder - you can make this dynamic)
        rating_frame = tk.Frame(info_frame, bg='white')
        rating_frame.pack(fill=tk.X, pady=(5,0))
        
        stars_label = tk.Label(rating_frame, text="⭐⭐⭐⭐⭐", font=('Segoe UI', 10),
                              bg='white', fg='#ffc107')
        stars_label.pack(side=tk.LEFT)
        
        rating_label = tk.Label(rating_frame, text="(4.5)", font=('Segoe UI', 9),
                               bg='white', fg=self.colors['secondary'])
        rating_label.pack(side=tk.LEFT, padx=(5,0))
        
        # Product price with discount
        price_frame = tk.Frame(info_frame, bg='white')
        price_frame.pack(fill=tk.X, pady=(10,0))
        
        # Current price
        price_label = tk.Label(price_frame, text=f"₹{product['price']:,.2f}", 
                              font=('Segoe UI', 16, 'bold'), bg='white', fg=self.colors['success'])
        price_label.pack(side=tk.LEFT)
        
        # Original price (crossed out) - simulate discount
        original_price = product['price'] * 1.2  # 20% discount
        original_label = tk.Label(price_frame, text=f"₹{original_price:,.0f}", 
                                 font=('Segoe UI', 11), bg='white', fg=self.colors['secondary'])
        original_label.pack(side=tk.LEFT, padx=(10,0))
        
        # Add strikethrough effect
        def add_strikethrough():
            original_label.config(font=('Segoe UI', 11, 'overstrike'))
        original_label.after(1, add_strikethrough)
        
        # Discount badge
        discount_label = tk.Label(price_frame, text="20% OFF", 
                                 font=('Segoe UI', 8, 'bold'), bg='#dc3545', fg='white',
                                 padx=5, pady=1)
        discount_label.pack(side=tk.LEFT, padx=(10,0))
        
        # Product description (truncated)
        desc_text = product['description']
        if len(desc_text) > 50:
            desc_text = desc_text[:47] + "..."
        
        desc_label = tk.Label(info_frame, text=desc_text, font=('Segoe UI', 10),
                             bg='white', fg=self.colors['secondary'], 
                             wraplength=250, justify=tk.LEFT)
        desc_label.pack(anchor='w', pady=(5,0))
        
        # Button frame
        btn_frame = tk.Frame(info_frame, bg='white')
        btn_frame.pack(fill=tk.X, pady=(15,0))
        
        # Add to cart button with enhanced styling
        add_btn = tk.Button(btn_frame, text="🛒 Add to Cart", 
                           command=lambda: self.add_to_cart_with_feedback(product),
                           bg=self.colors['primary'], fg='white', 
                           font=('Segoe UI', 11, 'bold'), cursor='hand2',
                           relief='flat', pady=8)
        add_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        
        # Quick view button
        view_btn = tk.Button(btn_frame, text="�️", 
                           command=lambda: self.show_product_details(product),
                           bg=self.colors['secondary'], fg='white', 
                           font=('Segoe UI', 11, 'bold'), cursor='hand2',
                           relief='flat', width=3, pady=8)
        view_btn.pack(side=tk.RIGHT)
        
        # Hover effects for buttons
        def btn_hover_in(e, btn, color):
            btn.config(bg=color)
        def btn_hover_out(e, btn, original_color):
            btn.config(bg=original_color)
        
        add_btn.bind('<Enter>', lambda e: btn_hover_in(e, add_btn, '#0056b3'))
        add_btn.bind('<Leave>', lambda e: btn_hover_out(e, add_btn, self.colors['primary']))
        
        view_btn.bind('<Enter>', lambda e: btn_hover_in(e, view_btn, '#5a6268'))
        view_btn.bind('<Leave>', lambda e: btn_hover_out(e, view_btn, self.colors['secondary']))
        
        return card_container
    
    def add_to_cart_with_feedback(self, product):
        """Add product to cart with visual feedback"""
        self.cart.add(product['id'])
        
        # Show success notification
        self.notification_manager.show_success_toast(
            f"✅ {product['name']} added to cart!"
        )
        
        # Update cart display
        self.refresh_cart_display()
        
        # Optional: Highlight cart tab briefly
        self.highlight_cart_tab()
    
    def highlight_cart_tab(self):
        """Briefly highlight the cart tab"""
        # This creates a visual cue that something was added to cart
        original_text = self.notebook.tab(3, "text")  # Cart tab index
        self.notebook.tab(3, text="🛍️ Cart (!)")
        self.after(2000, lambda: self.notebook.tab(3, text=original_text))
    
    def show_product_details(self, product):
        """Show detailed product information in a modal with image gallery"""
        details_window = tk.Toplevel(self)
        details_window.title(f"Product Details - {product['name']}")
        details_window.geometry("1000x700")
        details_window.configure(bg='white')
        details_window.transient(self)
        details_window.grab_set()
        
        # Center the window
        x = self.winfo_x() + (self.winfo_width() // 2) - 500
        y = self.winfo_y() + (self.winfo_height() // 2) - 350
        details_window.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(details_window, bg=self.colors['primary'], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, text=f"📦 {product['name']}", 
                               font=('Segoe UI', 18, 'bold'),
                               bg=self.colors['primary'], fg='white')
        header_label.pack(expand=True)
        
        # Main content container
        main_content = tk.Frame(details_window, bg='white')
        main_content.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Left side - Image Gallery
        left_frame = tk.Frame(main_content, bg='white', width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        left_frame.pack_propagate(False)
        
        # Image section title
        img_title = tk.Label(left_frame, text="📸 Product Images", 
                            font=('Segoe UI', 14, 'bold'),
                            bg='white', fg=self.colors['dark'])
        img_title.pack(pady=(0, 15))
        
        # Main image display
        main_image_frame = tk.Frame(left_frame, bg=self.colors['light'], 
                                   relief='solid', bd=1, width=350, height=300)
        main_image_frame.pack(pady=(0, 15))
        main_image_frame.pack_propagate(False)
        
        # Main image placeholder
        self.main_image_label = tk.Label(main_image_frame, 
                                        text="🖼️\nMain Product Image\n\nImage will load here",
                                        font=('Segoe UI', 12),
                                        bg=self.colors['light'], 
                                        fg=self.colors['secondary'],
                                        justify=tk.CENTER)
        self.main_image_label.pack(expand=True)
        
        # Image thumbnails
        if product.get('images'):
            thumb_frame = tk.Frame(left_frame, bg='white')
            thumb_frame.pack(fill=tk.X)
            
            tk.Label(thumb_frame, text="Click to view:", 
                    font=('Segoe UI', 10), bg='white', 
                    fg=self.colors['secondary']).pack(anchor='w', pady=(0, 5))
            
            thumb_container = tk.Frame(thumb_frame, bg='white')
            thumb_container.pack(fill=tk.X)
            
            for i, image_url in enumerate(product['images'][:3]):  # Show up to 3 thumbnails
                thumb_btn = tk.Button(thumb_container, 
                                     text=f"📷 Image {i+1}",
                                     command=lambda url=image_url, idx=i: self.load_product_image(url, idx+1),
                                     bg=self.colors['light'], 
                                     fg=self.colors['dark'],
                                     font=('Segoe UI', 9),
                                     relief='solid', bd=1,
                                     cursor='hand2',
                                     width=12, pady=8)
                thumb_btn.pack(side=tk.LEFT, padx=5)
                
                # Hover effects
                thumb_btn.bind('<Enter>', lambda e, btn=thumb_btn: btn.config(bg=self.colors['primary'], fg='white'))
                thumb_btn.bind('<Leave>', lambda e, btn=thumb_btn: btn.config(bg=self.colors['light'], fg=self.colors['dark']))
        
        # Load first image by default
        if product.get('images'):
            self.load_product_image(product['images'][0], 1)
        
        # Right side - Product Details
        right_frame = tk.Frame(main_content, bg='white')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Product details
        details_text = (
            f"Category: {product['category']}\n"
            f"Price: ₹{product['price']:,.2f}\n"
            f"Rating: ⭐⭐⭐⭐⭐ (4.5/5)\n\n"
            f"Description:\n{product['description']}\n\n"
            f"Features:\n"
            f"• High quality materials\n"
            f"• Fast shipping available\n"
            f"• 30-day return policy\n"
            f"• Customer support included\n\n"
            f"Specifications:\n"
            f"• Model: {product['id']}\n"
            f"• Warranty: 1 year\n"
            f"• Availability: In Stock"
        )
        
        details_label = tk.Label(right_frame, text=details_text.strip(),
                                font=('Segoe UI', 11), bg='white', fg=self.colors['dark'],
                                justify=tk.LEFT, anchor='nw')
        details_label.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        btn_frame = tk.Frame(right_frame, bg='white')
        btn_frame.pack(pady=20)
        
        add_btn = tk.Button(btn_frame, text="🛒 Add to Cart",
                           command=lambda: [self.add_to_cart_with_feedback(product), details_window.destroy()],
                           bg=self.colors['success'], fg='white', 
                           font=('Segoe UI', 12, 'bold'),
                           relief='flat', cursor='hand2', padx=20, pady=10)
        add_btn.pack(side=tk.LEFT, padx=10)
        
        close_btn = tk.Button(btn_frame, text="Close",
                             command=details_window.destroy,
                             bg=self.colors['secondary'], fg='white', 
                             font=('Segoe UI', 12, 'bold'),
                             relief='flat', cursor='hand2', padx=20, pady=10)
        close_btn.pack(side=tk.LEFT, padx=10)
    
    def load_product_image(self, image_url, image_number):
        """Load and display product image with enhanced thread-safe implementation"""
        print(f"🔄 Loading image {image_number}: {image_url}")
        
        # Show loading message immediately (this is called from main thread)
        if hasattr(self, 'main_image_label') and self.main_image_label.winfo_exists():
            self.main_image_label.config(
                text=f"🔄 Loading Image {image_number}...\n\nPlease wait",
                font=('Segoe UI', 12),
                wraplength=300,
                fg='blue',
                image=''  # Clear any existing image
            )
        
        # Define success callback
        def on_success(image):
            try:
                # Resize image for display
                display_width, display_height = 350, 250
                original_size = image.size
                image.thumbnail((display_width, display_height), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(image)
                
                # Update GUI
                if hasattr(self, 'main_image_label') and self.main_image_label.winfo_exists():
                    self.main_image_label.config(
                        image=photo,
                        text=f"✅ Image {image_number} loaded successfully",
                        compound=tk.CENTER,
                        font=('Segoe UI', 10),
                        fg=self.colors.get('success', 'green')
                    )
                    # Keep reference to prevent garbage collection
                    self.main_image_label.image = photo
                    
                    # Hide text after 2 seconds
                    self.after(2000, lambda: self.thread_safe_update(self.main_image_label, text=""))
                    print(f"🎉 Image {image_number} displayed successfully!")
                    
            except Exception as e:
                self.log_thread_error(f"Image success callback error: {e}")
                self.show_image_placeholder(image_url, image_number, f"Display Error: {str(e)}")
        
        # Define error callback
        def on_error(error):
            error_type = type(error).__name__
            if "Network" in str(error) or "requests" in error_type:
                error_msg = "Network Error"
            elif "FileNotFound" in error_type:
                error_msg = "File not found"
            else:
                error_msg = f"Image Error: {str(error)}"
            
            print(f"❌ Image loading error: {error_msg}")
            self.show_image_placeholder(image_url, image_number, error_msg)
        
        # Define progress callback
        def on_progress(message):
            if hasattr(self, 'main_image_label') and self.main_image_label.winfo_exists():
                self.thread_safe_update(self.main_image_label,
                    text=f"🔄 {message}\nImage {image_number}",
                    font=('Segoe UI', 10), fg='blue')
        
        # Start enhanced image loading
        try:
            self.load_image_with_fallback(
                image_url, on_success, on_error, on_progress, (350, 250)
            )
        except Exception as e:
            self.log_thread_error(f"Failed to start image loading: {e}")
            self.show_image_placeholder(image_url, image_number, f"Load Error: {str(e)}")
    
    def show_image_placeholder(self, image_url, image_number, error_reason=""):
        """Show a styled placeholder when image cannot be loaded"""
        if hasattr(self, 'main_image_label'):
            placeholder_text = f"🖼️ Image {image_number}\n\n"
            
            # Show different messages based on error type
            if "Network Error" in error_reason:
                placeholder_text += "🌐 Check your internet connection\n"
            elif "File not found" in error_reason:
                placeholder_text += "📁 Image file not found\n"
            elif "Image Error" in error_reason:
                placeholder_text += "⚠️ Invalid image format\n"
            else:
                placeholder_text += "📱 Tap thumbnail to switch\n"
            
            # Show truncated URL
            if len(image_url) > 40:
                placeholder_text += f"🔗 {image_url[:37]}..."
            else:
                placeholder_text += f"🔗 {image_url}"
            
            if error_reason and error_reason not in placeholder_text:
                placeholder_text += f"\n\n⚠️ {error_reason}"
            
            self.main_image_label.config(
                text=placeholder_text,
                font=('Segoe UI', 10),
                wraplength=300,
                image="",  # Clear any existing image
                compound=tk.CENTER,
                fg=self.colors['danger'] if error_reason else self.colors['secondary'],
                bg=self.colors['light'],
                justify=tk.CENTER
            )
    
    def load_product_card_image(self, image_label, product):
        """Load a small thumbnail image for product cards with enhanced thread-safe implementation"""
        try:
            # Get first available image
            image_url = None
            if product.get('images') and len(product['images']) > 0:
                image_url = product['images'][0]
            elif product.get('image'):  # Fallback to old single image field
                image_url = product['image']
            
            print(f"🔄 Loading card image for {product.get('name', 'Unknown')}: {image_url}")
            
            if image_url:
                # Show loading state immediately (in main thread)
                if image_label.winfo_exists():
                    image_label.config(
                        text="🔄\nLoading...", 
                        font=('Segoe UI', 8),
                        fg='blue',
                        image=''  # Clear any existing image
                    )
                
                # Define success callback
                def on_card_success(image):
                    try:
                        # Resize to card size
                        image.thumbnail((120, 100), Image.Resampling.LANCZOS)
                        
                        # Convert to PhotoImage
                        photo = ImageTk.PhotoImage(image)
                        
                        # Update GUI
                        if image_label.winfo_exists():
                            image_label.config(
                                image=photo,
                                text="✅ Loaded",
                                compound=tk.CENTER,
                                font=('Segoe UI', 8),
                                fg='green'
                            )
                            image_label.image = photo  # Keep reference
                            
                            # Hide text after 1 second
                            self.after(1000, lambda: self.thread_safe_update(image_label, text=""))
                            print(f"🎉 Card image displayed successfully!")
                            
                    except Exception as e:
                        self.log_thread_error(f"Card image success callback error: {e}")
                        self.thread_safe_update(image_label,
                            text="🖼️❌\nDisplay\nError", font=('Segoe UI', 8), fg='red')
                
                # Define error callback
                def on_card_error(error):
                    error_type = type(error).__name__
                    if "Network" in str(error) or "requests" in error_type:
                        self.thread_safe_update(image_label,
                            text="🌐❌\nNetwork\nError", font=('Segoe UI', 8), fg='red')
                    elif "FileNotFound" in error_type:
                        self.thread_safe_update(image_label,
                            text="📁❌\nFile Not\nFound", font=('Segoe UI', 8), fg='red')
                    else:
                        self.thread_safe_update(image_label,
                            text="🖼️❌\nImage\nError", font=('Segoe UI', 8), fg='red')
                    
                    print(f"❌ Card image error: {error}")
                
                # Start enhanced image loading
                try:
                    self.load_image_with_fallback(
                        image_url, on_card_success, on_card_error, size=(120, 100)
                    )
                except Exception as e:
                    self.log_thread_error(f"Card image loading setup error: {e}")
                    self.thread_safe_update(image_label,
                        text="🖼️\nLoad Error", font=('Segoe UI', 9), fg='red')
            else:
                print(f"⚠️ No image URL available for product: {product.get('name', 'Unknown')}")
                # No image URL available
                if image_label.winfo_exists():
                    image_label.config(
                        text="🖼️\nNo Image\nAvailable", 
                        font=('Segoe UI', 8),
                        fg='gray'
                    )
                    
        except Exception as e:
            self.log_thread_error(f"Card image loading error: {e}")
            print(f"❌ Card image loading error: {e}")
            # General error handling
            if image_label.winfo_exists():
                image_label.config(
                    text="🖼️\nLoad Failed", 
                    font=('Segoe UI', 9),
                    fg='red'
                )

    def show_login_required_message(self):
        """Show user-friendly login prompt"""
        result = messagebox.askyesno(
            "Login Required", 
            "You need to login to access banking features.\n\nWould you like to login now?",
            icon='question'
        )
        if result:
            self.show_login_dialog()

    def filter_products(self, event=None):
        """Filter products based on search and category"""
        self.display_products()

    def filter_products(self, event=None):
        """Filter products based on search and category"""
        if not hasattr(self, 'products_inner_frame'):
            return
        
        # Clear existing products
        for widget in self.products_inner_frame.winfo_children():
            widget.destroy()
        
        search_text = self.search_var.get().lower()
        selected_category = self.category_var.get()
        
        # Filter products
        filtered_products = []
        for product in self.products:
            # Category filter
            if selected_category != "All" and product['category'] != selected_category:
                continue
            
            # Search filter
            if search_text and search_text not in product['name'].lower() and search_text not in product['category'].lower():
                continue
            
            filtered_products.append(product)
        
        # Display filtered products
        row, col = 0, 0
        for product in filtered_products:
            product_frame = self.create_product_card(self.products_inner_frame, product)
            product_frame.grid(row=row, column=col, padx=10, pady=10, sticky='ew')
            
            col += 1
            if col >= 3:  # 3 products per row
                col = 0
                row += 1
        
        # Configure grid weights
        for i in range(3):
            self.products_inner_frame.grid_columnconfigure(i, weight=1)

    def add_to_cart(self, product_id):
        """Add product to cart with enhanced feedback"""
        self.cart.add(product_id)
        
        # Find product name for notification
        product = next((p for p in self.products if p['id'] == product_id), None)
        if product:
            self.notification_manager.show_success_toast(
                f"✅ {product['name']} added to cart!"
            )
        
        self.refresh_cart_display()

    def show_login_dialog(self):
        """Show login dialog"""
        self.notebook.select(4)  # Switch to profile tab
        if hasattr(self, 'login_email_entry'):
            self.login_email_entry.focus()

    def show_register_dialog(self):
        """Show registration dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Register New User")
        dialog.geometry("500x450")
        dialog.configure(bg='white')
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 50,
            self.winfo_rooty() + 50
        ))
        
        # Registration form
        tk.Label(dialog, text="Full Name:", font=('Segoe UI', 11), bg='white').pack(pady=10)
        name_entry = tk.Entry(dialog, font=('Segoe UI', 11), width=30)
        name_entry.pack(pady=5)
        
        tk.Label(dialog, text="Email:", font=('Segoe UI', 11), bg='white').pack(pady=10)
        email_entry = tk.Entry(dialog, font=('Segoe UI', 11), width=30)
        email_entry.pack(pady=5)
        
        tk.Label(dialog, text="Password:", font=('Segoe UI', 11), bg='white').pack(pady=10)
        password_entry = tk.Entry(dialog, font=('Segoe UI', 11), width=30, show="*")
        password_entry.pack(pady=5)
        
        tk.Label(dialog, text="Confirm Password:", font=('Segoe UI', 11), bg='white').pack(pady=10)
        confirm_entry = tk.Entry(dialog, font=('Segoe UI', 11), width=30, show="*")
        confirm_entry.pack(pady=5)
        
        def register_user():
            name = name_entry.get().strip()
            email = email_entry.get().strip()
            password = password_entry.get()
            confirm = confirm_entry.get()
            
            if not all([name, email, password, confirm]):
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            if not validate_email(email):
                messagebox.showerror("Error", "Please enter a valid email")
                return
            
            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match")
                return
            
            if email in self.users:
                messagebox.showerror("Error", "Email already registered")
                return
            
            # Create user
            self.users[email] = {
                'name': name,
                'email': email,
                'password': hash_password(password),
                'created_date': datetime.now().isoformat(),
                'account_type': 'Standard'
            }
            
            save_json(FILES['USERS'], self.users)
            dialog.destroy()
            self.notification_manager.show_notification("Registration successful! Please login.", "success")
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg='white')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Register", command=register_user,
                 bg=self.colors['success'], fg='white', font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 bg=self.colors['secondary'], fg='white', font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=10)

    def login_user(self):
        """Login user"""
        email = self.login_email_entry.get().strip()
        password = self.login_password_entry.get()
        
        if not email or not password:
            self.notification_manager.show_notification("Please enter email and password", "warning")
            return
        
        if email == "demo@example.com":
            # Demo user login
            if password == "demo123":
                self.current_user = {
                    "name": "Demo User",
                    "email": email,
                    "role": "user",
                    "is_active": True
                }
                self.is_logged_in = True
                self.update_user_info_display()
                self.build_user_profile_interface()
                self.refresh_account_info()
                
                self.notification_manager.show_notification("Welcome to the demo account! 🎉", "success")
            else:
                self.notification_manager.show_notification("Invalid demo password", "error")
            return
        
        if email not in self.users:
            self.notification_manager.show_notification("Invalid email or password", "error")
            return
        
        user = self.users[email]
        if not verify_password(password, user['password']):
            self.notification_manager.show_notification("Invalid email or password", "error")
            return
        
        # Login successful
        self.current_user = user
        self.is_logged_in = True
        self.session.create_session(email)
        
        self.notification_manager.show_notification(f"Welcome back, {user['name']}!", "success")
        self.update_user_info_display()
        self.build_user_profile_interface()
        self.refresh_account_info()

    def logout_user(self):
        """Logout user"""
        self.current_user = None
        self.is_logged_in = False
        self.session = SecureSession()
        
        self.notification_manager.show_notification("Logged out successfully", "info")
        self.update_user_info_display()
        self.build_login_interface()
        self.refresh_account_info()

    def send_ai_message(self, event=None):
        """Send message to AI assistant with enhanced multi-provider support"""
        try:
            # Get message from text widget instead of entry
            message = self.chat_input.get(1.0, tk.END).strip()
            
            # Skip if empty or placeholder text
            if not message or "Ask me anything about banking" in message:
                return
                
            # Clear input
            self.chat_input.delete(1.0, tk.END)
            
            # Add user message to display and history
            self.add_chat_message("You", message, "user")
            
            # Use enhanced AI assistant first
            if hasattr(self, 'ai_assistant') and self.ai_assistant:
                ai_response = self.ai_assistant.get_response(message, self.get_user_context())
                provider_used = "Enhanced AI Assistant"
            else:
                # Use AI Provider Manager for multi-provider support
                context_prompt = self.create_context_prompt(message)
                ai_response, provider_used = ai_manager.generate_response(context_prompt)
            
            # Add provider info to response
            if provider_used != "Enhanced AI Assistant":
                provider_name = ai_manager.providers.get(provider_used, {}).get("name", provider_used)
                response_with_info = f"{ai_response}\n\n_Powered by {provider_name}_"
                ai_response = response_with_info
            
            # Add AI response to display and history
            self.add_chat_message("AI Assistant", ai_response, "assistant")
            
            # Update suggestions based on response
            self.update_suggestions_after_response(message, ai_response)
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            self.add_chat_message("System", error_msg, "error")
            self.notification_manager.show_notification(error_msg, "error")
    
    def send_quick_message(self, message):
        """Send a pre-defined quick message"""
        # Clear any placeholder text
        self.chat_input.delete(1.0, tk.END)
        # Insert the quick message
        self.chat_input.insert(1.0, message)
        # Send the message
        self.send_ai_message()
    
    def create_context_prompt(self, message):
        """Create a context-aware prompt for the AI"""
        user_context = self.get_user_context()
        
        context_info = f"""
System Context:
- User: {user_context.get('user_name', 'Guest')}
- Status: {'Logged in' if self.is_logged_in else 'Not logged in'}
- Current Section: {user_context.get('current_section', 'Unknown')}
- Account Balance: ${user_context.get('balance', 0):,.2f}
- Cart Items: {user_context.get('cart_items', 0)}
- Recent Activity: {user_context.get('recent_activity', 'None')}

Banking System Features Available:
- Account Management (Create, View, Delete accounts)
- Money Transfers (Between accounts, to external)
- Shopping Cart (Add products, checkout, order history)
- Transaction History (Search, filter, export)
- Real-time Search and Filtering across all sections
- Advanced Product Browsing and Shopping

User Question: {message}

Please provide a helpful, accurate response based on the system context and available features. If the user asks about specific operations, provide step-by-step guidance. Be conversational but informative.
"""
        return context_info
    
    def get_user_context(self):
        """Get current user context for AI assistant"""
        context = {
            'user_name': self.current_user.get('name', 'Guest') if self.is_logged_in else 'Guest',
            'current_section': getattr(self, 'current_tab', 'Unknown'),
            'balance': sum(acc.get('balance', 0) for acc in self.current_user.get('accounts', [])) if self.is_logged_in else 0,
            'cart_items': len(self.cart.items),
            'recent_activity': 'Logged in' if self.is_logged_in else 'Browsing',
            'accounts_count': len(self.current_user.get('accounts', [])) if self.is_logged_in else 0,
            'recent_transactions': len(self.current_user.get('transactions', [])) if self.is_logged_in else 0
        }
        return context
    
    def generate_enhanced_offline_response(self, message):
        """Generate enhanced offline responses using the AI assistant"""
        if hasattr(self, 'ai_assistant') and self.ai_assistant:
            return self.ai_assistant.get_response(message, self.get_user_context())
        else:
            return self.generate_offline_response(message)
    
    def update_suggestions_after_response(self, user_message, ai_response):
        """Update input suggestions based on the conversation"""
        # Analyze the conversation to provide relevant follow-up suggestions
        follow_ups = []
        
        if any(word in user_message.lower() for word in ['account', 'balance', 'money']):
            follow_ups.extend(["💳 Check recent transactions", "💰 Transfer money", "📊 Account summary"])
        elif any(word in user_message.lower() for word in ['shop', 'buy', 'product']):
            follow_ups.extend(["🛒 Browse more products", "📦 Check cart", "💳 Proceed to checkout"])
        elif any(word in user_message.lower() for word in ['search', 'find']):
            follow_ups.extend(["🔍 Advanced search tips", "⚡ Filter options", "📋 Search history"])
        else:
            follow_ups.extend(["❓ Ask another question", "📚 Explore features", "🔄 Try different topic"])
        
        if hasattr(self, 'suggestions_label') and follow_ups:
            suggestion_text = "💡 Follow-up: " + " • ".join(follow_ups[:3])
            self.suggestions_label.config(text=suggestion_text)
    
    def filter_chat_history(self):
        """Filter chat history based on search and filter criteria"""
        if not hasattr(self, 'chat_history') or not self.chat_history:
            return
        
        search_term = self.chat_search_var.get().lower()
        filter_type = self.chat_filter_var.get()
        
        # Clear current display
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        
        # Filter messages
        filtered_messages = []
        for msg in self.chat_history:
            # Apply filter type
            if filter_type == "My Messages" and msg['type'] != 'user':
                continue
            elif filter_type == "AI Responses" and msg['type'] != 'assistant':
                continue
            elif filter_type == "Recent (Today)":
                msg_date = datetime.fromisoformat(msg['timestamp']).date()
                if msg_date != datetime.now().date():
                    continue
            elif filter_type == "Banking Questions" and not any(word in msg['message'].lower() 
                for word in ['bank', 'account', 'money', 'balance', 'transfer', 'deposit', 'withdraw']):
                continue
            elif filter_type == "Shopping Questions" and not any(word in msg['message'].lower() 
                for word in ['shop', 'cart', 'buy', 'product', 'checkout', 'order']):
                continue
            
            # Apply search term
            if search_term and search_term not in msg['message'].lower():
                continue
            
            filtered_messages.append(msg)
        
        # Display filtered messages
        for msg in filtered_messages:
            self.display_chat_message(msg['sender'], msg['message'], msg['type'], msg['timestamp'])
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def export_chat_history(self):
        """Export chat history to a file"""
        if not hasattr(self, 'chat_history') or not self.chat_history:
            self.notification_manager.show_notification("No chat history to export", "info")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_export_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Chat History Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                
                for msg in self.chat_history:
                    timestamp = datetime.fromisoformat(msg['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"[{timestamp}] {msg['sender']}: {msg['message']}\n\n")
            
            self.notification_manager.show_notification(f"Chat exported to {filename}", "success")
            
        except Exception as e:
            self.notification_manager.show_notification(f"Export failed: {str(e)}", "error")
    
    def clear_chat_history(self):
        """Clear chat history with confirmation"""
        if not hasattr(self, 'chat_history') or not self.chat_history:
            self.notification_manager.show_notification("No chat history to clear", "info")
            return
        
        # Create confirmation dialog
        result = messagebox.askyesno("Clear Chat History", 
                                   "Are you sure you want to clear all chat history?\n\nThis action cannot be undone.",
                                   icon='warning')
        
        if result:
            self.chat_history = []
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.config(state=tk.DISABLED)
            
            # Add welcome message
            self.add_chat_message("AI Assistant", 
                                 "🆕 Chat history cleared. How can I help you today?",
                                 "assistant")
            
            self.notification_manager.show_notification("Chat history cleared", "success")
    
    def display_chat_message(self, sender, message, message_type, timestamp):
        """Display a single chat message with proper formatting"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add timestamp
        display_time = timestamp[:19] if len(timestamp) > 19 else timestamp
        self.chat_display.insert(tk.END, f"[{display_time}] ", "timestamp")
        
        # Add sender with appropriate styling
        if message_type == "user":
            self.chat_display.insert(tk.END, f"{sender}: ", "user")
        elif message_type == "assistant":
            self.chat_display.insert(tk.END, f"{sender}: ", "assistant")
        elif message_type == "system":
            self.chat_display.insert(tk.END, f"{sender}: ", "system")
        elif message_type == "error":
            self.chat_display.insert(tk.END, f"{sender}: ", "error")
        else:
            self.chat_display.insert(tk.END, f"{sender}: ")
        
        # Add message content
        self.chat_display.insert(tk.END, f"{message}\n\n")
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def add_chat_message(self, sender, message, message_type="assistant"):
        """Add message to chat display and history"""
        timestamp = datetime.now().isoformat()
        
        # Add to chat history
        if not hasattr(self, 'chat_history'):
            self.chat_history = []
        
        self.chat_history.append({
            'sender': sender,
            'message': message,
            'type': message_type,
            'timestamp': timestamp
        })
        
        # Update display if not filtered
        if not hasattr(self, 'chat_search_var') or not self.chat_search_var.get():
            self.chat_display.config(state=tk.NORMAL)
            
            # Add timestamp
            display_time = timestamp[:19] if len(timestamp) > 19 else timestamp
            self.chat_display.insert(tk.END, f"[{display_time}] ", "timestamp")
            
            # Add sender with styling
            sender_tag = "user" if message_type == 'user' else "assistant"
            self.chat_display.insert(tk.END, f"{sender}: ", sender_tag)
            
            # Add message
            self.chat_display.insert(tk.END, f"{message}\n\n")
            
            self.chat_display.config(state=tk.DISABLED)
            self.chat_display.see(tk.END)
        else:
            # Refresh filtered view
            self.filter_chat_history()

    def get_ai_response(self, message):
        """Get enhanced AI response with context awareness"""
        try:
            # Use enhanced AI assistant for better responses
            if hasattr(self, 'ai_assistant'):
                ai_message = self.ai_assistant.get_context_aware_response(message)
            elif gemini_client:
                # Enhanced Google Gemini integration
                system_context = self._build_system_context()
                full_prompt = f"{system_context}\n\nUser Question: {message}\n\nPlease provide a helpful response:"
                
                try:
                    response = gemini_client.generate_content(full_prompt)
                    ai_message = response.text
                except Exception as e:
                    logging.error(f"Gemini API error: {e}")
                    ai_message = f"🔴 Gemini AI temporarily unavailable: {str(e)}\n\nSwitching to enhanced offline mode..."
                    ai_message += "\n\n" + get_offline_response(message)
            elif client:
                # Enhanced OpenAI integration with better prompts
                system_context = self._build_system_context()
                
                response = client.chat.completions.create(
                    model=current_model,
                    messages=[
                        {"role": "system", "content": system_context},
                        {"role": "user", "content": message}
                    ],
                    max_tokens=500,  # Increased for more detailed responses
                    temperature=0.7,
                    presence_penalty=0.1,
                    frequency_penalty=0.1
                )
                ai_message = response.choices[0].message.content
            else:
                ai_message = get_offline_response(message)
        except Exception as e:
            logging.error(f"AI response error: {e}")
            ai_message = get_offline_response(message)
        
        # Add AI response to chat (run in main thread)
        self.after(0, lambda: self.add_chat_message("AI Assistant", ai_message))
    
    def _build_system_context(self):
        """Build comprehensive system context for AI"""
        context = """You are an advanced AI assistant for a comprehensive Banking & Shopping System. 

SYSTEM CAPABILITIES:
🏦 Banking: Account creation (Savings/Current/Fixed Deposit), deposits, withdrawals, transfers, transaction history with advanced filtering
🛍️ Shopping: Product browsing with real-time search, cart management, secure checkout integrated with banking
🔍 Search: Global search across all sections, advanced filtering with operators (>, <, ranges)
📊 Data: Export capabilities, detailed reporting, real-time updates
🔐 Security: Encrypted transactions, secure sessions, user authentication

CURRENT USER STATUS:"""
        
        if hasattr(self, 'is_logged_in') and self.is_logged_in:
            context += f"\n✅ Logged in as: {self.current_user.get('name', 'User')}"
            if hasattr(self, 'bank') and self.bank.accounts:
                context += f"\n💳 Has {len(self.bank.accounts)} bank account(s)"
            if hasattr(self, 'cart') and self.cart.items:
                context += f"\n🛒 Cart has {len(self.cart.items)} item(s)"
        else:
            context += "\n❌ Not logged in - limited access to features"
        
        context += """

RESPONSE GUIDELINES:
- Provide detailed, step-by-step instructions
- Use emojis for visual clarity
- Include specific navigation paths (Tab → Button → Action)
- Mention relevant features and tips
- Be helpful and encouraging
- For technical issues, provide troubleshooting steps
- Always maintain a professional yet friendly tone

Answer user questions comprehensively and guide them through the system effectively."""
        
        return context

    def open_admin_window(self):
        """Open admin window (only for admin users)"""
        if not self.is_logged_in or not self.current_user or self.current_user.get('role') != 'admin':
            messagebox.showerror("Access Denied", "You don't have admin privileges.")
            return
        
        try:
            AdminWindow(self, self.bank, self.users, self.products, self.categories, self.shop_info)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open admin window: {str(e)}")

    def open_settings(self):
        """Open settings dialog"""
        settings_window = tk.Toplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("500x500")
        settings_window.configure(bg='white')
        settings_window.transient(self)
        settings_window.grab_set()
        
        # Settings form
        tk.Label(settings_window, text="⚙️ Application Settings", 
                font=('Segoe UI', 14, 'bold'), bg='white').pack(pady=20)
        
        # Auto logout setting
        tk.Label(settings_window, text="Auto Logout (minutes):", 
                font=('Segoe UI', 11), bg='white').pack(pady=5)
        
        timeout_var = tk.StringVar(value=str(self.settings.get('auto_logout_minutes', 30)))
        timeout_entry = tk.Entry(settings_window, textvariable=timeout_var, 
                               font=('Segoe UI', 11), width=10)
        timeout_entry.pack(pady=5)
        
        # Notifications setting
        notifications_var = tk.BooleanVar(value=self.settings.get('notifications_enabled', True))
        notifications_check = tk.Checkbutton(settings_window, text="Enable Notifications",
                                           variable=notifications_var, font=('Segoe UI', 11),
                                           bg='white')
        notifications_check.pack(pady=10)
        
        # Security level
        tk.Label(settings_window, text="Security Level:", font=('Segoe UI', 11), bg='white').pack(pady=5)
        
        security_level_var = tk.StringVar(value=self.settings.get('security_level', 'high'))
        security_level_combo = ttk.Combobox(settings_window, textvariable=security_level_var,
                                           values=["low", "medium", "high"], state="readonly")
        security_level_combo.pack(pady=5)
        
        # Biometric authentication
        biometric_var = tk.BooleanVar(value=self.settings.get('biometric_enabled', False))
        biometric_check = tk.Checkbutton(settings_window, text="Enable Biometric Authentication",
                                        variable=biometric_var, font=('Segoe UI', 11),
                                        bg='white')
        biometric_check.pack(pady=10)
        
        # Two-factor authentication
        two_factor_var = tk.BooleanVar(value=self.settings.get('two_factor_auth', False))
        two_factor_check = tk.Checkbutton(settings_window, text="Enable Two-Factor Authentication",
                                         variable=two_factor_var, font=('Segoe UI', 11),
                                         bg='white')
        two_factor_check.pack(pady=10)
        
        # Threading diagnostics section
        tk.Label(settings_window, text="🧵 Threading Diagnostics:", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(pady=(20, 5))
        
        diag_frame = tk.Frame(settings_window, bg='white')
        diag_frame.pack(pady=5)
        
        tk.Button(diag_frame, text="🔍 Show Thread Errors", 
                 command=self.show_thread_errors,
                 bg='#17a2b8', fg='white', font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(diag_frame, text="📊 Thread Status", 
                 command=self.show_thread_status,
                 bg='#6f42c1', fg='white', font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=5)
        
        def save_settings():
            try:
                timeout = int(timeout_var.get())
                if timeout < 1:
                    timeout = 30
                
                self.settings['auto_logout_minutes'] = timeout
                self.settings['notifications_enabled'] = notifications_var.get()
                self.settings['security_level'] = security_level_var.get()
                self.settings['biometric_enabled'] = biometric_var.get()
                self.settings['two_factor_auth'] = two_factor_var.get()
                
                save_json(FILES['SETTINGS'], self.settings)
                settings_window.destroy()
                self.notification_manager.show_notification("Settings saved successfully!", "success")
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid timeout value")
        
        # Buttons
        btn_frame = tk.Frame(settings_window, bg='white')
        btn_frame.pack(pady=30)
        
        tk.Button(btn_frame, text="Save", command=save_settings,
                 bg=self.colors['success'], fg='white', 
                 font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Cancel", command=settings_window.destroy,
                 bg=self.colors['secondary'], fg='white', 
                 font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=10)
    
    def on_closing(self):
        """Handle application closing with proper cleanup"""
        try:
            print("🔄 Shutting down application...")
            
            # Cancel any pending timers
            if hasattr(self, 'auto_logout_timer') and self.auto_logout_timer:
                self.after_cancel(self.auto_logout_timer)
            
            # Logout user if logged in
            if self.is_logged_in:
                print("👤 Logging out user...")
                self.logout_user()
            
            # Save any pending data
            if hasattr(self, 'bank'):
                print("💾 Saving banking data...")
                self.bank.save_data()
            
            # Clean up threading components
            self.cleanup_threading()
            
            # Give background threads a moment to finish
            print("⏳ Waiting for background threads...")
            self.update()  # Process any pending GUI updates
            
            print("✅ Cleanup completed successfully")
                
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            logging.error(f"Error during cleanup: {e}")
        finally:
            print("🚪 Destroying window...")
            self.destroy()

    # Missing methods implementation
    def refresh_cart_display(self):
        """Refresh cart display"""
        # Clear existing cart items
        for widget in self.cart_items_frame.winfo_children():
            widget.destroy()
        
        if not self.cart.items:
            # Show empty cart message
            empty_label = tk.Label(self.cart_items_frame, text="🛒 Your cart is empty\nAdd some products to get started!", 
                                  font=('Segoe UI', 12), bg='white', fg='#6c757d',
                                  justify=tk.CENTER)
            empty_label.pack(expand=True, fill=tk.BOTH)
        else:
            # Show cart items
            cart_details = self.cart.get_details(self.products)
            
            for item in cart_details['items']:
                item_frame = tk.Frame(self.cart_items_frame, bg='white', relief='solid', bd=1)
                item_frame.pack(fill=tk.X, padx=5, pady=5)
                
                # Product info
                info_frame = tk.Frame(item_frame, bg='white')
                info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
                
                tk.Label(info_frame, text=item['name'], font=('Segoe UI', 11, 'bold'),
                        bg='white').pack(anchor='w')
                tk.Label(info_frame, text=f"₹{item['price']:,.2f} × {item['quantity']} = ₹{item['total']:,.2f}",
                        font=('Segoe UI', 10), bg='white', fg='#6c757d').pack(anchor='w')
                
                # Remove button
                remove_btn = tk.Button(item_frame, text="🗑️", 
                                     command=lambda pid=item['id']: self.remove_from_cart(pid),
                                     bg='#dc3545', fg='white', font=('Segoe UI', 9),
                                     relief='flat', cursor='hand2', width=3)
                remove_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Update order summary
        self.update_order_summary()
    
    def remove_from_cart(self, product_id):
        """Remove product from cart"""
        self.cart.remove(product_id)
        self.refresh_cart_display()
        self.notification_manager.show_notification("Item removed from cart", "info")
    
    def update_order_summary(self):
        """Update order summary display"""
        # Clear existing summary
        for widget in self.order_summary_frame.winfo_children():
            widget.destroy()
        
        if not self.cart.items:
            tk.Label(self.order_summary_frame, text="No items in cart", 
                    font=('Segoe UI', 11), bg='white', fg='#6c757d').pack(pady=20)
            return
        
        cart_details = self.cart.get_details(self.products)
        
        # Subtotal
        tk.Label(self.order_summary_frame, text="Subtotal:", 
                font=('Segoe UI', 11), bg='white').pack(anchor='w')
        tk.Label(self.order_summary_frame, text=f"₹{cart_details['subtotal']:,.2f}", 
                font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='e')
        
        # Delivery charge
        tk.Label(self.order_summary_frame, text="Delivery:", 
                font=('Segoe UI', 11), bg='white').pack(anchor='w', pady=(10,0))
        tk.Label(self.order_summary_frame, text=f"₹{cart_details['delivery_charge']:,.2f}", 
                font=('Segoe UI', 11), bg='white').pack(anchor='e')
        
        # Tax
        tk.Label(self.order_summary_frame, text="Tax (18%):", 
                font=('Segoe UI', 11), bg='white').pack(anchor='w', pady=(10,0))
        tk.Label(self.order_summary_frame, text=f"₹{cart_details['tax_amount']:,.2f}", 
                font=('Segoe UI', 11), bg='white').pack(anchor='e')
        
        # Separator
        tk.Frame(self.order_summary_frame, height=1, bg='#dee2e6').pack(fill=tk.X, pady=10)
        
        # Total
        tk.Label(self.order_summary_frame, text="Total:", 
                font=('Segoe UI', 12, 'bold'), bg='white').pack(anchor='w')
        tk.Label(self.order_summary_frame, text=f"₹{cart_details['grand_total']:,.2f}", 
                font=('Segoe UI', 12, 'bold'), bg='white', fg='#28a745').pack(anchor='e')
    
    def build_login_interface(self):
        """Build login interface in profile tab"""
        # Clear existing content
        for widget in self.profile_frame.winfo_children():
            widget.destroy()
        
        # Login form
        login_frame = self.create_card_frame(self.profile_frame, "🔐 Login to Your Account")
        login_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        form_frame = tk.Frame(login_frame, bg='white')
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Email field
        tk.Label(form_frame, text="Email:", font=('Segoe UI', 11, 'bold'),
                bg='white').pack(anchor='w', pady=(0,5))
        self.login_email_entry = tk.Entry(form_frame, font=('Segoe UI', 11), width=40)
        self.login_email_entry.pack(fill=tk.X, pady=(0,15))
        
        # Password field
        tk.Label(form_frame, text="Password:", font=('Segoe UI', 11, 'bold'),
                bg='white').pack(anchor='w', pady=(0,5))
        self.login_password_entry = tk.Entry(form_frame, font=('Segoe UI', 11), width=40, show="*")
        self.login_password_entry.pack(fill=tk.X, pady=(0,15))
        
        # Login button
        login_btn = tk.Button(form_frame, text="🔐 Login", command=self.login_user,
                             bg=self.colors['primary'], fg='white', 
                             font=('Segoe UI', 11, 'bold'),
                             relief='flat', cursor='hand2', pady=10)
        login_btn.pack(fill=tk.X, pady=10)
        
        # Register button
        register_btn = tk.Button(form_frame, text="📝 Register New Account", 
                               command=self.show_register_dialog,
                               bg=self.colors['success'], fg='white', 
                               font=('Segoe UI', 11, 'bold'),
                               relief='flat', cursor='hand2', pady=10)
        register_btn.pack(fill=tk.X, pady=5)
        
        # Demo account info
        demo_frame = tk.Frame(form_frame, bg='#e7f3ff', relief='solid', bd=1)
        demo_frame.pack(fill=tk.X, pady=20)
        
        tk.Label(demo_frame, text="🎯 Demo Account", font=('Segoe UI', 11, 'bold'),
                bg='#e7f3ff', fg='#0056b3').pack(pady=5)
        tk.Label(demo_frame, text="Email: demo@example.com", font=('Segoe UI', 10),
                bg='#e7f3ff', fg='#0056b3').pack()
        tk.Label(demo_frame, text="Password: demo123", font=('Segoe UI', 10),
                bg='#e7f3ff', fg='#0056b3').pack(pady=(0,5))
        
        # Bind Enter key
        self.login_password_entry.bind('<Return>', lambda e: self.login_user())
    
    def build_user_profile_interface(self):
        """Build user profile interface when logged in"""
        # Clear existing content
        for widget in self.profile_frame.winfo_children():
            widget.destroy()
        
        # Profile header
        profile_frame = self.create_card_frame(self.profile_frame, "👤 User Profile")
        profile_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        content_frame = tk.Frame(profile_frame, bg='white')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        if self.current_user:
            # User info
            tk.Label(content_frame, text=f"Name: {self.current_user.get('name', 'N/A')}", 
                    font=('Segoe UI', 12), bg='white').pack(anchor='w', pady=5)
            tk.Label(content_frame, text=f"Email: {self.current_user.get('email', 'N/A')}", 
                    font=('Segoe UI', 12), bg='white').pack(anchor='w', pady=5)
            tk.Label(content_frame, text=f"Role: {self.current_user.get('role', 'user').title()}", 
                    font=('Segoe UI', 12), bg='white').pack(anchor='w', pady=5)
            
            # Admin button (only for admin users)
            if self.current_user.get('role') == 'admin':
                admin_btn = tk.Button(content_frame, text="🔐 Open Admin Panel", 
                                    command=self.open_admin_window,
                                    bg=self.colors['danger'], fg='white', 
                                    font=('Segoe UI', 11, 'bold'),
                                    relief='flat', cursor='hand2', pady=10)
                admin_btn.pack(fill=tk.X, pady=20)
            
            # Logout button
            logout_btn = tk.Button(content_frame, text="🚪 Logout", command=self.logout_user,
                                 bg=self.colors['secondary'], fg='white', 
                                 font=('Segoe UI', 11, 'bold'),
                                 relief='flat', cursor='hand2', pady=10)
            logout_btn.pack(fill=tk.X, pady=10)
    
    def checkout(self):
        """Process checkout"""
        if not self.cart.items:
            self.notification_manager.show_notification("Cart is empty!", "warning")
            return
        
        if not self.is_logged_in:
            self.show_login_required_message()
            return
        
        cart_details = self.cart.get_details(self.products)
        total_amount = cart_details['grand_total']
        
        # Simple checkout - in real app, integrate payment gateway
        result = messagebox.askyesno("Checkout", 
                                   f"Total Amount: ₹{total_amount:,.2f}\n\nProceed with payment?")
        
        if result:
            # Clear cart
            self.cart.clear()
            self.refresh_cart_display()
            self.notification_manager.show_notification("Order placed successfully! 🎉", "success")
    
    def show_register_dialog(self):
        """Show registration dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Register New User")
        dialog.geometry("500x450")
        dialog.configure(bg='white')
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 50,
            self.winfo_rooty() + 50
        ))
        
        # Registration form
        tk.Label(dialog, text="Full Name:", font=('Segoe UI', 11), bg='white').pack(pady=10)
        name_entry = tk.Entry(dialog, font=('Segoe UI', 11), width=30)
        name_entry.pack(pady=5)
        
        tk.Label(dialog, text="Email:", font=('Segoe UI', 11), bg='white').pack(pady=10)
        email_entry = tk.Entry(dialog, font=('Segoe UI', 11), width=30)
        email_entry.pack(pady=5)
        
        tk.Label(dialog, text="Password:", font=('Segoe UI', 11), bg='white').pack(pady=10)
        password_entry = tk.Entry(dialog, font=('Segoe UI', 11), width=30, show="*")
        password_entry.pack(pady=5)
        
        tk.Label(dialog, text="Confirm Password:", font=('Segoe UI', 11), bg='white').pack(pady=10)
        confirm_entry = tk.Entry(dialog, font=('Segoe UI', 11), width=30, show="*")
        confirm_entry.pack(pady=5)
        
        def register_user():
            name = name_entry.get().strip()
            email = email_entry.get().strip()
            password = password_entry.get()
            confirm = confirm_entry.get()
            
            if not all([name, email, password, confirm]):
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            if not validate_email(email):
                messagebox.showerror("Error", "Please enter a valid email")
                return
            
            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match")
                return
            
            if email in self.users:
                messagebox.showerror("Error", "Email already registered")
                return
            
            # Create user
            self.users[email] = {
                'name': name,
                'email': email,
                'password': hash_password(password),
                'created_date': datetime.now().isoformat(),
                'role': 'user'
            }
            
            save_json(FILES['USERS'], self.users)
            dialog.destroy()
            self.notification_manager.show_notification("Registration successful! Please login.", "success")
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg='white')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Register", command=register_user,
                 bg=self.colors['success'], fg='white', 
                 font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 bg=self.colors['secondary'], fg='white', 
                 font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=10)


def test_ai_system():
    """Test the AI system functionality"""
    print("🧪 Testing AI System...")
    
    try:
        # Test AI Provider Manager
        print(f"✅ Active providers: {list(ai_manager.get_active_providers().keys())}")
        print(f"✅ Current provider: {ai_manager.current_provider}")
        print(f"✅ Available models: {ai_manager.available_models}")
        
        # Test basic response generation
        test_prompts = [
            "Hello, how are you?",
            "How do I create a bank account?",
            "Show me electronics products"
        ]
        
        for prompt in test_prompts:
            response, provider = ai_manager.generate_response(prompt)
            print(f"✅ Prompt: '{prompt}' -> Provider: {provider}")
            print(f"   Response preview: {response[:100]}...")
        
        print("🎉 AI System test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ AI System test failed: {e}")
        return False


if __name__ == "__main__":
    try:
        # Ensure we're running in the main thread
        if threading.current_thread() != threading.main_thread():
            print("❌ Application must be started from the main thread!")
            sys.exit(1)
        
        # Test AI system first (optional)
        # Uncomment the line below to test AI system on startup
        # test_ai_system()
        
        print("🚀 Starting Enhanced Banking & Shopping System...")
        print("📱 Initializing user interface...")
        
        # Start the application
        app = EnhancedBankingShoppingSystem()
        
        print("✅ Application loaded successfully!")
        print("🎯 Starting main event loop...")
        
        # Start the main event loop
        app.mainloop()
        
    except KeyboardInterrupt:
        print("\n⚠️ Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Application startup error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("👋 Application shutdown complete")