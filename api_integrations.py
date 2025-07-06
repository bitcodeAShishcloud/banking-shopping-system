# API and External Integration Improvements

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
from datetime import datetime
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import qrcode
import io
import base64

## 1. REST API Server
class BankingShoppingAPI:
    def __init__(self, db_manager):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for web frontend
        self.db = db_manager
        self.setup_routes()
    
    def setup_routes(self):
        """Setup all API routes"""
        
        # Authentication endpoints
        @self.app.route('/api/auth/login', methods=['POST'])
        def login():
            data = request.json
            email = data.get('email')
            password = data.get('password')
            
            # Verify credentials (implement proper password hashing)
            user = self.verify_user(email, password)
            if user:
                token = self.generate_token(user)
                return jsonify({
                    'success': True,
                    'token': token,
                    'user': {
                        'email': user['email'],
                        'name': user['name']
                    }
                })
            else:
                return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
        @self.app.route('/api/auth/register', methods=['POST'])
        def register():
            data = request.json
            try:
                user_id = self.create_user(data)
                return jsonify({'success': True, 'user_id': user_id})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 400
        
        # Banking endpoints
        @self.app.route('/api/banking/accounts', methods=['GET'])
        def get_accounts():
            user_email = self.get_user_from_token(request.headers.get('Authorization'))
            if not user_email:
                return jsonify({'error': 'Unauthorized'}), 401
            
            accounts = self.get_user_accounts(user_email)
            return jsonify({'accounts': accounts})
        
        @self.app.route('/api/banking/transfer', methods=['POST'])
        def transfer_money():
            user_email = self.get_user_from_token(request.headers.get('Authorization'))
            if not user_email:
                return jsonify({'error': 'Unauthorized'}), 401
            
            data = request.json
            try:
                transaction_id = self.process_transfer(
                    data['from_account'],
                    data['to_account'],
                    data['amount'],
                    user_email
                )
                return jsonify({'success': True, 'transaction_id': transaction_id})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 400
        
        @self.app.route('/api/banking/balance/<account_number>', methods=['GET'])
        def get_balance(account_number):
            user_email = self.get_user_from_token(request.headers.get('Authorization'))
            if not user_email:
                return jsonify({'error': 'Unauthorized'}), 401
            
            balance = self.get_account_balance(account_number, user_email)
            if balance is not None:
                return jsonify({'balance': balance})
            else:
                return jsonify({'error': 'Account not found or access denied'}), 404
        
        # Shopping endpoints
        @self.app.route('/api/products', methods=['GET'])
        def get_products():
            category = request.args.get('category')
            page = int(request.args.get('page', 1))
            limit = int(request.args.get('limit', 20))
            
            products = self.get_products_paginated(category, page, limit)
            return jsonify(products)
        
        @self.app.route('/api/cart', methods=['POST'])
        def add_to_cart():
            user_email = self.get_user_from_token(request.headers.get('Authorization'))
            if not user_email:
                return jsonify({'error': 'Unauthorized'}), 401
            
            data = request.json
            try:
                self.add_item_to_cart(user_email, data['product_id'], data['quantity'])
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 400
        
        @self.app.route('/api/orders', methods=['POST'])
        def create_order():
            user_email = self.get_user_from_token(request.headers.get('Authorization'))
            if not user_email:
                return jsonify({'error': 'Unauthorized'}), 401
            
            data = request.json
            try:
                order_id = self.process_order(user_email, data)
                return jsonify({'success': True, 'order_id': order_id})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 400
        
        # Analytics endpoints (admin only)
        @self.app.route('/api/admin/analytics', methods=['GET'])
        def get_analytics():
            # Check admin privileges
            user_email = self.get_user_from_token(request.headers.get('Authorization'))
            if not self.is_admin(user_email):
                return jsonify({'error': 'Admin access required'}), 403
            
            analytics_data = self.get_analytics_data()
            return jsonify(analytics_data)
    
    def verify_user(self, email, password):
        """Verify user credentials"""
        # Implement with proper password hashing
        pass
    
    def generate_token(self, user):
        """Generate JWT token for user"""
        # Implement JWT token generation
        pass
    
    def get_user_from_token(self, auth_header):
        """Extract user from authorization token"""
        # Implement JWT token verification
        pass
    
    def run(self, host='localhost', port=5000, debug=False):
        """Run the API server"""
        self.app.run(host=host, port=port, debug=debug)

## 2. Payment Gateway Integration
class PaymentGateway:
    def __init__(self, gateway_type='razorpay'):
        self.gateway_type = gateway_type
        self.api_key = None
        self.api_secret = None
    
    def configure(self, api_key, api_secret):
        """Configure payment gateway credentials"""
        self.api_key = api_key
        self.api_secret = api_secret
    
    def create_payment_order(self, amount, currency='INR', receipt=None):
        """Create a payment order"""
        if self.gateway_type == 'razorpay':
            return self._create_razorpay_order(amount, currency, receipt)
        elif self.gateway_type == 'stripe':
            return self._create_stripe_payment_intent(amount, currency)
        else:
            raise ValueError(f"Unsupported gateway: {self.gateway_type}")
    
    def _create_razorpay_order(self, amount, currency, receipt):
        """Create Razorpay order"""
        import razorpay
        
        client = razorpay.Client(auth=(self.api_key, self.api_secret))
        
        order_data = {
            'amount': int(amount * 100),  # Amount in paise
            'currency': currency,
            'receipt': receipt or f"order_{int(datetime.now().timestamp())}"
        }
        
        order = client.order.create(data=order_data)
        return order
    
    def _create_stripe_payment_intent(self, amount, currency):
        """Create Stripe payment intent"""
        import stripe
        
        stripe.api_key = self.api_secret
        
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Amount in cents
            currency=currency.lower()
        )
        
        return intent
    
    def verify_payment(self, payment_id, order_id, signature=None):
        """Verify payment status"""
        if self.gateway_type == 'razorpay':
            return self._verify_razorpay_payment(payment_id, order_id, signature)
        elif self.gateway_type == 'stripe':
            return self._verify_stripe_payment(payment_id)
    
    def _verify_razorpay_payment(self, payment_id, order_id, signature):
        """Verify Razorpay payment"""
        import razorpay
        
        client = razorpay.Client(auth=(self.api_key, self.api_secret))
        
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })
            return True
        except:
            return False

## 3. Email Integration
class EmailService:
    def __init__(self, smtp_server='smtp.gmail.com', smtp_port=587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = None
        self.password = None
    
    def configure(self, email, password):
        """Configure email credentials"""
        self.email = email
        self.password = password
    
    def send_email(self, to_email, subject, body, is_html=False):
        """Send email"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'html' if is_html else 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def send_welcome_email(self, user_email, user_name):
        """Send welcome email to new user"""
        subject = "Welcome to Ashish's Banking & Shopping!"
        body = f"""
        <html>
        <body>
            <h2>Welcome, {user_name}!</h2>
            <p>Thank you for joining Ashish's Online Banking & Shopping platform.</p>
            <p>You can now:</p>
            <ul>
                <li>Create banking accounts</li>
                <li>Transfer money securely</li>
                <li>Shop from our wide range of products</li>
                <li>Track your orders and transactions</li>
            </ul>
            <p>Get started by logging into your account!</p>
            <br>
            <p>Best regards,<br>Ashish's Banking & Shopping Team</p>
        </body>
        </html>
        """
        return self.send_email(user_email, subject, body, is_html=True)
    
    def send_transaction_alert(self, user_email, transaction_details):
        """Send transaction alert email"""
        subject = f"Transaction Alert - ₹{transaction_details['amount']}"
        body = f"""
        <html>
        <body>
            <h2>Transaction Alert</h2>
            <p>A transaction has been processed on your account:</p>
            <table border="1" style="border-collapse: collapse;">
                <tr><td><b>Transaction ID:</b></td><td>{transaction_details['id']}</td></tr>
                <tr><td><b>Amount:</b></td><td>₹{transaction_details['amount']}</td></tr>
                <tr><td><b>Type:</b></td><td>{transaction_details['type']}</td></tr>
                <tr><td><b>Date:</b></td><td>{transaction_details['date']}</td></tr>
                <tr><td><b>Balance:</b></td><td>₹{transaction_details['balance']}</td></tr>
            </table>
            <p>If you did not authorize this transaction, please contact us immediately.</p>
        </body>
        </html>
        """
        return self.send_email(user_email, subject, body, is_html=True)

## 4. SMS Integration
class SMSService:
    def __init__(self, provider='twilio'):
        self.provider = provider
        self.account_sid = None
        self.auth_token = None
        self.from_number = None
    
    def configure(self, account_sid, auth_token, from_number):
        """Configure SMS service"""
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
    
    def send_sms(self, to_number, message):
        """Send SMS"""
        if self.provider == 'twilio':
            return self._send_twilio_sms(to_number, message)
        else:
            raise ValueError(f"Unsupported SMS provider: {self.provider}")
    
    def _send_twilio_sms(self, to_number, message):
        """Send SMS via Twilio"""
        try:
            from twilio.rest import Client
            
            client = Client(self.account_sid, self.auth_token)
            
            message = client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            return True
        except Exception as e:
            print(f"Failed to send SMS: {e}")
            return False
    
    def send_otp(self, phone_number, otp):
        """Send OTP via SMS"""
        message = f"Your OTP for Ashish's Banking & Shopping is: {otp}. Valid for 5 minutes. Do not share with anyone."
        return self.send_sms(phone_number, message)

## 5. QR Code Generation
class QRCodeGenerator:
    @staticmethod
    def generate_payment_qr(account_number, amount=None, name=None):
        """Generate QR code for UPI payments"""
        # UPI payment URL format
        upi_id = f"ashish@banking"  # Your UPI ID
        
        upi_url = f"upi://pay?pa={upi_id}&pn={name or 'Ashish Banking'}"
        if amount:
            upi_url += f"&am={amount}"
        upi_url += f"&cu=INR&tn=Payment to {account_number}"
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(upi_url)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for web display
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'qr_code': qr_base64,
            'upi_url': upi_url
        }
    
    @staticmethod
    def generate_account_qr(account_details):
        """Generate QR code for account information"""
        account_data = json.dumps(account_details)
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(account_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()

## 6. External Data Integration
class ExternalDataService:
    @staticmethod
    def get_exchange_rates(base_currency='INR'):
        """Get current exchange rates"""
        try:
            response = requests.get(f"https://api.exchangerate-api.com/v4/latest/{base_currency}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Failed to get exchange rates: {e}")
        
        return None
    
    @staticmethod
    def verify_bank_account(account_number, ifsc_code):
        """Verify bank account details (mock implementation)"""
        # In real implementation, integrate with bank verification API
        try:
            # Mock verification logic
            if len(account_number) >= 8 and len(ifsc_code) == 11:
                return {
                    'valid': True,
                    'bank_name': 'Sample Bank',
                    'branch': 'Sample Branch'
                }
            else:
                return {'valid': False, 'message': 'Invalid account details'}
        except Exception as e:
            return {'valid': False, 'message': str(e)}
    
    @staticmethod
    def get_product_recommendations(user_id, category=None):
        """Get product recommendations from external ML service"""
        try:
            # Mock recommendation service
            recommendations = [
                {'product_id': 'prod_001', 'score': 0.95},
                {'product_id': 'prod_002', 'score': 0.87},
                {'product_id': 'prod_003', 'score': 0.82}
            ]
            return recommendations
        except Exception as e:
            print(f"Failed to get recommendations: {e}")
            return []

## 7. Webhook Handler
class WebhookHandler:
    def __init__(self):
        self.handlers = {}
    
    def register_handler(self, event_type, handler_func):
        """Register a webhook handler"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler_func)
    
    def handle_webhook(self, event_type, payload):
        """Handle incoming webhook"""
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                try:
                    handler(payload)
                except Exception as e:
                    print(f"Webhook handler error: {e}")
    
    def payment_success_handler(self, payload):
        """Handle payment success webhook"""
        print(f"Payment successful: {payload}")
        # Update order status, send confirmation email, etc.
    
    def payment_failed_handler(self, payload):
        """Handle payment failure webhook"""
        print(f"Payment failed: {payload}")
        # Notify user, update order status, etc.

# Initialize services
def initialize_integrations():
    """Initialize all external integrations"""
    
    # Payment gateway
    payment_gateway = PaymentGateway('razorpay')
    # payment_gateway.configure('your_key', 'your_secret')
    
    # Email service
    email_service = EmailService()
    # email_service.configure('your_email@gmail.com', 'your_password')
    
    # SMS service
    sms_service = SMSService('twilio')
    # sms_service.configure('account_sid', 'auth_token', '+1234567890')
    
    # Webhook handler
    webhook_handler = WebhookHandler()
    webhook_handler.register_handler('payment.success', webhook_handler.payment_success_handler)
    webhook_handler.register_handler('payment.failed', webhook_handler.payment_failed_handler)
    
    return {
        'payment_gateway': payment_gateway,
        'email_service': email_service,
        'sms_service': sms_service,
        'webhook_handler': webhook_handler
    }

if __name__ == "__main__":
    # Example usage
    services = initialize_integrations()
    
    # Generate QR code example
    qr_data = QRCodeGenerator.generate_payment_qr("1234567890", 100, "John Doe")
    print(f"QR code generated: {len(qr_data['qr_code'])} characters")
    
    # External data example
    exchange_rates = ExternalDataService.get_exchange_rates()
    if exchange_rates:
        print(f"USD rate: {exchange_rates['rates'].get('USD', 'N/A')}")
    
    print("API integrations ready!")
