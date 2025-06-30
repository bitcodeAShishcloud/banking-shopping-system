# Ashish's Online Banking & Shopping System

A comprehensive desktop application built with Python and Tkinter that combines banking services with an e-commerce shopping platform.

## 🚀 Features

### Banking Services
- **Account Management**: Create and manage bank accounts
- **Money Transfers**: Transfer funds between accounts
- **Transaction History**: View detailed transaction records
- **Cash Operations**: Deposit and withdraw cash
- **Balance Inquiry**: Check account balances

### Shopping Platform
- **Product Catalog**: Browse products with images and details
- **Shopping Cart**: Add/remove items with quantity management
- **Order Management**: Track order history and status
- **GST Calculations**: Automatic tax calculations with invoice generation
- **Cashback System**: Earn cashback on purchases
- **Multiple Payment Options**: Integrated with banking system

### Admin Panel
- **Product Management**: Add, edit, delete products with multiple photos
- **Category Management**: Organize products into categories
- **User Management**: Manage customer accounts
- **Order Tracking**: Monitor all orders and transactions
- **Reporting**: Generate sales and revenue reports
- **Data Backup**: Backup and restore system data

### Additional Features
- **Dark Mode**: Toggle between light and dark themes
- **Multi-language Support**: English, Hindi, Marathi
- **AI Chat Assistant**: Built-in help system
- **Responsive UI**: Modern and intuitive interface
- **Data Persistence**: JSON-based data storage

## 📋 Requirements

- Python 3.7 or higher
- Pillow (PIL) for image handling
- tkinter (usually comes with Python)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/banking-shopping-system.git
   cd banking-shopping-system
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python shopping_cart_and_banking-system.py
   ```

## 📁 Project Structure

```
banking-shopping-system/
├── shopping_cart_and_banking-system.py  # Main application file
├── requirements.txt                     # Python dependencies
├── README.md                           # Project documentation
├── LICENSE                             # License file
├── .gitignore                          # Git ignore rules
├── data/                               # Data storage directory
│   ├── products.json                   # Product catalog
│   ├── accounts.json                   # User accounts
│   ├── transactions.json               # Transaction history
│   ├── categories.json                 # Product categories
│   ├── history.json                    # Order history
│   ├── settings.json                   # Application settings
│   └── feedback.txt                    # User feedback
├── images/                             # Product images
│   └── (product image files)
└── docs/                              # Documentation
    └── user_guide.md                  # User guide
```

## 🚀 Quick Start

1. **First Run**: The application will create default configuration files
2. **Admin Access**: Use password `admin123` to access admin panel
3. **Create Account**: Start by creating a bank account
4. **Add Products**: Use admin panel to add products with images
5. **Start Shopping**: Browse products and add to cart
6. **Make Payment**: Complete purchases using your bank account

## 💡 Usage

### For Customers
1. **Banking**: Create account → Deposit money → Transfer funds
2. **Shopping**: Browse products → Add to cart → Checkout → Pay

### For Administrators
1. **Access Admin Panel**: Click "Admin" button and enter password
2. **Manage Products**: Add products with multiple photos
3. **Monitor Orders**: Track all customer orders
4. **Generate Reports**: View sales and revenue analytics

## 🔧 Configuration

### Default Settings
- **Admin Password**: `admin123` (can be changed in settings)
- **Default Categories**: Pre-loaded with common product categories
- **GST Rates**: Configurable per product
- **Delivery Charges**: ₹5 for orders under ₹50

### Customization
- Modify `DEFAULT_SETTINGS` in the main file
- Update product categories in admin panel
- Adjust GST rates and delivery charges
- Customize UI colors and themes

## 📊 Data Storage

The application uses JSON files for data persistence:
- **products.json**: Product catalog with photos and details
- **accounts.json**: Bank account information
- **transactions.json**: All financial transactions
- **history.json**: Order history and status

## 🛡️ Security Features

- Password-protected admin panel
- Transaction logging and audit trail
- Data backup and restore functionality
- Input validation and error handling

## 🎨 Screenshots

*Add screenshots of your application here*

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Ashish**
- Email: 0241cys143@niet.co.in
- Project: Banking & Shopping System

## 🙏 Acknowledgments

- Built with Python and Tkinter
- Icons and UI inspiration from modern web applications
- JSON for lightweight data storage

## 📞 Support

For support and questions:
- Email: 0241cys143@niet.co.in
- Create an issue in this repository

## 🔄 Version History

- **v1.0.0** - Initial release with basic banking and shopping features
- **v1.1.0** - Added multi-photo support for products
- **v1.2.0** - Enhanced admin panel and reporting features

---

⭐ Star this repository if you find it helpful!
"# banking-shopping-system" 
