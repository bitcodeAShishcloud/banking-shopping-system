# Ashish's Online Banking & Shopping System

A comprehensive Python/Tkinter-based application combining banking and e-commerce functionality with modern security features, user management, and analytics.

## 🚀 Features

### Core Functionality
- **Shopping Cart**: Advanced cart system with product management, discounts, GST calculations, and cashback
- **Banking System**: Account management, transactions, balance tracking
- **User Authentication**: Secure login/registration with password hashing and session management
- **Admin Panel**: Comprehensive user and system management
- **Order Management**: Complete order processing with history tracking
- **Product Catalog**: Category-based product organization
- **Feedback System**: Customer feedback collection and management

### Security Enhancements ✅
- **Password Hashing**: PBKDF2-based secure password storage
- **Session Management**: Automatic logout, session tokens, activity tracking
- **Rate Limiting**: Protection against brute force attacks
- **Account Lockout**: Temporary lockout after failed login attempts
- **Input Validation**: Email validation, password strength requirements
- **Audit Logging**: Comprehensive logging of user actions and system events

### Modern UI/UX ✅
- **Notification System**: In-app notifications for user feedback
- **Modern Components**: Gradient buttons, card layouts, modern entry fields
- **Progress Dialogs**: Loading indicators for long operations
- **Responsive Design**: Improved layout and styling
- **Hover Effects**: Interactive UI elements with visual feedback
- **Dark Mode Support**: Toggle between light and dark themes

### Analytics & Performance ✅
- **User Analytics**: Track user behavior, login patterns, purchase history
- **Performance Monitoring**: Operation timing and optimization
- **Caching System**: Improved application performance
- **Background Operations**: Threading for non-blocking operations
- **Memory Management**: Efficient data handling and cleanup

### Advanced Features
- **Multi-user Support**: Role-based access (customer, admin)
- **Cashback System**: Per-user and per-product cashback tracking
- **Export Functionality**: CSV export for reports and data
- **Backup & Recovery**: Automatic data backup and recovery
- **Error Handling**: Graceful error handling with user feedback

## 📋 Requirements

- Python 3.7 or higher
- Pillow (PIL) for image handling
- Tkinter (usually included with Python)

## 🛠️ Installation

### Automatic Installation (Windows)
1. Run `install_dependencies.bat` to install all required dependencies
2. Run `run_app.bat` to start the application

### Manual Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python shopping_cart_and_banking-system.py
```

## 🎯 Quick Start

### First Time Setup
1. Run the application
2. Default admin password: `admin123`
3. Demo user credentials:
   - Email: `demo@example.com`
   - Password: `demo123`

### Admin Access
- Click "Admin Panel" and enter the admin password
- Manage users, products, categories, and view analytics
- Access comprehensive reporting and export features

### Customer Features
- Register a new account or login with existing credentials
- Browse products by category
- Add items to cart with automatic calculations
- Complete checkout process with order tracking
- View banking accounts and transaction history

## 📁 File Structure

```
├── shopping_cart_and_banking-system.py    # Main application
├── requirements.txt                        # Python dependencies
├── install_dependencies.bat              # Windows installer
├── run_app.bat                           # Windows launcher
├── users.json                            # User credentials and data
├── products.json                         # Product catalog
├── categories.json                       # Product categories
├── accounts.json                         # Banking accounts
├── transactions.json                     # Transaction history
├── history.json                          # Order history
├── settings.json                         # Application settings
├── analytics.json                        # User analytics data
├── app.log                              # Application logs
├── feedback.txt                         # Customer feedback
├── shop.json                            # Shop information
├── test_user_management.py              # User management tests
├── test_app.py                          # Application tests
├── USER_LOGIN_DOCUMENTATION.md          # User login features
├── ADMIN_USER_MANAGEMENT_DOCS.md        # Admin documentation
└── improvement_templates/               # Enhancement templates
    ├── security_improvements.py
    ├── ui_improvements.py
    ├── analytics_improvements.py
    ├── performance_improvements.py
    ├── api_integrations.py
    └── mobile_web_improvements.py
```

## 🔐 Security Features

### Password Security
- PBKDF2 hashing with salt (100,000 iterations)
- Password strength validation
- Automatic upgrade from plain text passwords

### Session Security
- Session tokens for authenticated users
- Automatic logout after 30 minutes of inactivity
- Activity tracking and session validation

### Access Control
- Rate limiting for login attempts
- Account lockout after failed attempts
- Role-based permissions (customer/admin)

### Audit & Monitoring
- Comprehensive logging of all user actions
- Analytics tracking for behavior analysis
- Error logging and crash reporting

## 📊 Analytics Dashboard

The application tracks various metrics:
- User registration and login patterns
- Product view and purchase statistics
- Performance metrics for optimization
- Error rates and system health

## 🧪 Testing

Run the included test scripts:
```bash
python test_user_management.py
python test_app.py
```

## 🛡️ Data Privacy

- User passwords are securely hashed and never stored in plain text
- Session data is automatically cleaned up
- Analytics data is anonymized where possible
- All data files are stored locally

## 🔧 Configuration

### Settings File (settings.json)
```json
{
  "dark_mode": false,
  "notifications_enabled": true,
  "language": "English"
}
```

### Admin Settings
- Admin password can be changed in the source code (ADMIN_PASSWORD variable)
- User roles and permissions can be modified through the admin panel

## 📈 Future Enhancements

The application includes templates for future improvements:
- **API Integration**: REST API, payment gateways, SMS/Email notifications
- **Mobile Support**: Progressive Web App (PWA) capabilities
- **Advanced Analytics**: Data visualization and reporting dashboards
- **Performance Scaling**: Database migration, connection pooling
- **Security Hardening**: JWT tokens, encryption, advanced threat protection

## 🐛 Troubleshooting

### Common Issues
1. **Python not found**: Ensure Python is installed and added to PATH
2. **Pillow import error**: Run `pip install Pillow`
3. **Permission errors**: Run as administrator if needed
4. **Data corruption**: Delete `.json` files to reset to defaults

### Logs
Check `app.log` for detailed error information and system events.

## 📞 Support

For issues or questions:
- Check the application logs (`app.log`)
- Review the test scripts for usage examples
- Refer to the documentation files in the project directory

## 📝 License

This project is for educational and demonstration purposes. Please ensure proper licensing for commercial use.

## 🎯 Version History

### v2.0 (Current)
- ✅ Secure authentication system with password hashing
- ✅ Modern UI with notifications and progress indicators
- ✅ Analytics tracking and performance monitoring
- ✅ Enhanced admin panel with user management
- ✅ Comprehensive logging and error handling
- ✅ Improved checkout process with order tracking

### v1.0 (Previous)
- Basic shopping cart and banking functionality
- Simple user interface
- File-based data storage
- Basic admin panel

---

**Note**: This application demonstrates modern software development practices including security, user experience, analytics, and maintainable code architecture.
