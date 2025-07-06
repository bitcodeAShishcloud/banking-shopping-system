# Advanced Analytics and Reporting System

import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import defaultdict
import sqlite3

## 1. Database Migration (from JSON to SQLite)
class DatabaseManager:
    def __init__(self, db_path="banking_shopping.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with proper schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                join_date DATE NOT NULL,
                last_login DATETIME,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Banking accounts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS banking_accounts (
                account_number TEXT PRIMARY KEY,
                user_email TEXT NOT NULL,
                account_type TEXT NOT NULL,
                balance DECIMAL(15,2) NOT NULL DEFAULT 0,
                created_date DATE NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_email) REFERENCES users(email)
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_account TEXT,
                to_account TEXT,
                amount DECIMAL(15,2) NOT NULL,
                transaction_type TEXT NOT NULL,
                description TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'completed',
                FOREIGN KEY (from_account) REFERENCES banking_accounts(account_number),
                FOREIGN KEY (to_account) REFERENCES banking_accounts(account_number)
            )
        ''')
        
        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                category TEXT NOT NULL,
                stock_quantity INTEGER DEFAULT 0,
                description TEXT,
                discount_percent DECIMAL(5,2) DEFAULT 0,
                gst_rate DECIMAL(5,4) DEFAULT 0.18,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                user_email TEXT NOT NULL,
                total_amount DECIMAL(15,2) NOT NULL,
                status TEXT DEFAULT 'pending',
                order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                delivery_address TEXT,
                payment_method TEXT,
                FOREIGN KEY (user_email) REFERENCES users(email)
            )
        ''')
        
        # Order items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price_per_item DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def migrate_from_json(self, json_files_path="./"):
        """Migrate existing JSON data to SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Migrate users
            with open(f"{json_files_path}users.json", 'r') as f:
                users_data = json.load(f)
            
            for email, user_data in users_data.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO users (email, name, password_hash, join_date)
                    VALUES (?, ?, ?, ?)
                ''', (email, user_data['name'], user_data['password'], user_data['join_date']))
            
            # Migrate banking accounts
            with open(f"{json_files_path}accounts.json", 'r') as f:
                accounts_data = json.load(f)
            
            for acc_num, acc_data in accounts_data.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO banking_accounts 
                    (account_number, user_email, account_type, balance, created_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (acc_num, acc_data.get('owner_email', 'guest@example.com'), 
                     acc_data['type'], acc_data['balance'], acc_data['created_date']))
            
            conn.commit()
            print("Data migration completed successfully!")
            
        except FileNotFoundError as e:
            print(f"JSON file not found: {e}")
        except Exception as e:
            print(f"Migration error: {e}")
        finally:
            conn.close()

## 2. Advanced Analytics
class AnalyticsEngine:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_user_analytics(self, start_date=None, end_date=None):
        """Get comprehensive user analytics"""
        conn = sqlite3.connect(self.db.db_path)
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # User registration trends
        query = '''
            SELECT DATE(join_date) as date, COUNT(*) as new_users
            FROM users 
            WHERE join_date BETWEEN ? AND ?
            GROUP BY DATE(join_date)
            ORDER BY date
        '''
        registration_data = pd.read_sql_query(query, conn, params=(start_date, end_date))
        
        # Active users (users with recent transactions or orders)
        query = '''
            SELECT COUNT(DISTINCT u.email) as active_users
            FROM users u
            WHERE u.email IN (
                SELECT DISTINCT user_email FROM orders 
                WHERE order_date >= date('now', '-30 days')
                UNION
                SELECT DISTINCT user_email FROM banking_accounts ba
                JOIN transactions t ON (ba.account_number = t.from_account OR ba.account_number = t.to_account)
                WHERE t.timestamp >= datetime('now', '-30 days')
            )
        '''
        active_users = pd.read_sql_query(query, conn)
        
        conn.close()
        return {
            'registration_trends': registration_data,
            'active_users': active_users.iloc[0]['active_users']
        }
    
    def get_financial_analytics(self):
        """Get banking and financial analytics"""
        conn = sqlite3.connect(self.db.db_path)
        
        # Total deposits, withdrawals, transfers
        query = '''
            SELECT 
                transaction_type,
                COUNT(*) as count,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount
            FROM transactions
            WHERE timestamp >= date('now', '-30 days')
            GROUP BY transaction_type
        '''
        transaction_summary = pd.read_sql_query(query, conn)
        
        # Account balances distribution
        query = '''
            SELECT 
                account_type,
                COUNT(*) as account_count,
                SUM(balance) as total_balance,
                AVG(balance) as avg_balance,
                MIN(balance) as min_balance,
                MAX(balance) as max_balance
            FROM banking_accounts
            WHERE is_active = 1
            GROUP BY account_type
        '''
        balance_distribution = pd.read_sql_query(query, conn)
        
        # Daily transaction volume
        query = '''
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as transaction_count,
                SUM(amount) as daily_volume
            FROM transactions
            WHERE timestamp >= date('now', '-30 days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        '''
        daily_volume = pd.read_sql_query(query, conn)
        
        conn.close()
        return {
            'transaction_summary': transaction_summary,
            'balance_distribution': balance_distribution,
            'daily_volume': daily_volume
        }
    
    def get_sales_analytics(self):
        """Get e-commerce sales analytics"""
        conn = sqlite3.connect(self.db.db_path)
        
        # Sales by category
        query = '''
            SELECT 
                p.category,
                COUNT(oi.id) as items_sold,
                SUM(oi.quantity * oi.price_per_item) as revenue,
                AVG(oi.price_per_item) as avg_price
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.order_date >= date('now', '-30 days')
            GROUP BY p.category
            ORDER BY revenue DESC
        '''
        category_sales = pd.read_sql_query(query, conn)
        
        # Top selling products
        query = '''
            SELECT 
                p.name,
                p.category,
                SUM(oi.quantity) as total_sold,
                SUM(oi.quantity * oi.price_per_item) as revenue
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.order_date >= date('now', '-30 days')
            GROUP BY p.product_id, p.name, p.category
            ORDER BY total_sold DESC
            LIMIT 10
        '''
        top_products = pd.read_sql_query(query, conn)
        
        # Daily sales
        query = '''
            SELECT 
                DATE(o.order_date) as date,
                COUNT(DISTINCT o.order_id) as orders_count,
                SUM(o.total_amount) as daily_revenue,
                AVG(o.total_amount) as avg_order_value
            FROM orders o
            WHERE o.order_date >= date('now', '-30 days')
            GROUP BY DATE(o.order_date)
            ORDER BY date
        '''
        daily_sales = pd.read_sql_query(query, conn)
        
        conn.close()
        return {
            'category_sales': category_sales,
            'top_products': top_products,
            'daily_sales': daily_sales
        }

## 3. Report Generator
class ReportGenerator:
    def __init__(self, analytics_engine):
        self.analytics = analytics_engine
    
    def generate_dashboard_data(self):
        """Generate data for admin dashboard"""
        user_data = self.analytics.get_user_analytics()
        financial_data = self.analytics.get_financial_analytics()
        sales_data = self.analytics.get_sales_analytics()
        
        return {
            'users': user_data,
            'financial': financial_data,
            'sales': sales_data,
            'generated_at': datetime.now().isoformat()
        }
    
    def export_report(self, report_type='comprehensive', format='json', filepath=None):
        """Export various types of reports"""
        if not filepath:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"report_{report_type}_{timestamp}.{format}"
        
        if report_type == 'comprehensive':
            data = self.generate_dashboard_data()
        elif report_type == 'financial':
            data = self.analytics.get_financial_analytics()
        elif report_type == 'sales':
            data = self.analytics.get_sales_analytics()
        elif report_type == 'users':
            data = self.analytics.get_user_analytics()
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        if format == 'json':
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif format == 'csv':
            # Convert DataFrames to CSV
            for key, df in data.items():
                if isinstance(df, pd.DataFrame):
                    df.to_csv(f"{filepath}_{key}.csv", index=False)
        
        return filepath

## 4. Performance Monitoring
class PerformanceMonitor:
    def __init__(self):
        self.metrics = defaultdict(list)
    
    def log_response_time(self, operation, duration):
        """Log operation response time"""
        self.metrics[f"{operation}_response_time"].append({
            'timestamp': datetime.now(),
            'duration': duration
        })
    
    def log_error(self, operation, error_type, details):
        """Log application errors"""
        self.metrics[f"{operation}_errors"].append({
            'timestamp': datetime.now(),
            'error_type': error_type,
            'details': details
        })
    
    def get_performance_summary(self, hours=24):
        """Get performance summary for the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        summary = {}
        
        for metric_name, data in self.metrics.items():
            recent_data = [d for d in data if d['timestamp'] > cutoff]
            
            if 'response_time' in metric_name:
                durations = [d['duration'] for d in recent_data]
                if durations:
                    summary[metric_name] = {
                        'count': len(durations),
                        'avg': sum(durations) / len(durations),
                        'min': min(durations),
                        'max': max(durations)
                    }
            elif 'errors' in metric_name:
                summary[metric_name] = {
                    'count': len(recent_data),
                    'error_types': list(set(d['error_type'] for d in recent_data))
                }
        
        return summary

## 5. Data Visualization
def create_dashboard_charts(analytics_data, output_dir="./charts/"):
    """Create visualization charts for dashboard"""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # User registration trends
    if 'users' in analytics_data and not analytics_data['users']['registration_trends'].empty:
        plt.figure(figsize=(10, 6))
        reg_data = analytics_data['users']['registration_trends']
        plt.plot(pd.to_datetime(reg_data['date']), reg_data['new_users'], marker='o')
        plt.title('User Registration Trends (Last 30 Days)')
        plt.xlabel('Date')
        plt.ylabel('New Users')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{output_dir}user_registration_trends.png")
        plt.close()
    
    # Transaction volume
    if 'financial' in analytics_data and not analytics_data['financial']['daily_volume'].empty:
        plt.figure(figsize=(10, 6))
        vol_data = analytics_data['financial']['daily_volume']
        plt.bar(pd.to_datetime(vol_data['date']), vol_data['daily_volume'])
        plt.title('Daily Transaction Volume')
        plt.xlabel('Date')
        plt.ylabel('Volume (₹)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{output_dir}daily_transaction_volume.png")
        plt.close()
    
    # Sales by category
    if 'sales' in analytics_data and not analytics_data['sales']['category_sales'].empty:
        plt.figure(figsize=(10, 6))
        cat_data = analytics_data['sales']['category_sales']
        plt.pie(cat_data['revenue'], labels=cat_data['category'], autopct='%1.1f%%')
        plt.title('Revenue by Product Category')
        plt.tight_layout()
        plt.savefig(f"{output_dir}revenue_by_category.png")
        plt.close()
    
    print(f"Charts saved to {output_dir}")

# Example usage
if __name__ == "__main__":
    # Initialize system
    db_manager = DatabaseManager()
    db_manager.migrate_from_json()
    
    analytics = AnalyticsEngine(db_manager)
    report_gen = ReportGenerator(analytics)
    
    # Generate comprehensive report
    dashboard_data = report_gen.generate_dashboard_data()
    report_file = report_gen.export_report('comprehensive', 'json')
    
    # Create visualizations
    create_dashboard_charts(dashboard_data)
    
    print(f"Analytics report generated: {report_file}")
    print("Dashboard charts created in ./charts/ directory")
