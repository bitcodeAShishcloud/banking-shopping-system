# 🏦 Advanced Banking & Shopping System

A modern, secure, and feature-rich desktop application that combines personal banking and e-commerce in one platform. Built with Python and Tkinter, it offers robust account management, secure transactions, shopping cart functionality, and admin controls—all with a beautiful, user-friendly interface.

---

## ✨ Features

- **User Management:** Registration, login, password hashing, roles (user/admin), and account status.
- **Banking:** Create/manage accounts, deposit, withdraw, transfer, and view transaction history.
- **Shopping:** Browse products, add to cart, purchase, and manage orders.
- **Admin Panel:** Full CRUD for users/products, system stats, and settings.
- **Security:** Password hashing & salting, input validation, and error handling.
- **Persistence:** Data stored in JSON (easy to migrate to SQLite).
- **Modern UI:** Themed interface, dialogs, and color-coded feedback.
- **AI Integration:** Optional support for OpenAI/Gemini for smart help and suggestions.
- **Extensible:** Modular codebase for easy customization and future enhancements.

---

## 🚀 Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/pdf-editor-clone.git
   cd pdf-editor-clone/web
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application:**
   ```bash
   python enhanced_banking_shopping_system.py
   ```

---

## 📦 Requirements
- Python 3.8+
- Tkinter (usually included with Python)
- Pillow
- requests
- (Optional) openai, google-generativeai

Install all requirements with:
```bash
pip install -r requirements.txt
```

---

## 🛡️ Security & Best Practices
- Passwords are hashed and salted before storage.
- All user input is validated.
- File/database operations are wrapped in try-except blocks for safety.

---

## 🛠️ Customization
- Easily extend with new features or migrate to SQLite for more robust data storage.
- The codebase is modular: see `user.py`, `banking.py`, `shopping.py`, `utils.py`, and `database.py`.

---

## 📄 License
MIT License. See [LICENSE](LICENSE) for details.

---

## 🙏 Credits
Developed by Ashish Gupta and contributors.

---

## 📬 Contact
For support or questions, open an issue or email: support@advancedbanking.com
