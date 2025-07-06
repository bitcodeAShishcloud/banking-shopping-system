# Admin User Management Documentation

## Overview
A comprehensive user management system has been added to the Admin panel, allowing administrators to manage all registered users, view their details, and monitor their banking activities.

## Accessing User Management

### Step 1: Open Admin Panel
1. Launch the application
2. Click the "🛠️ Admin" button (top-right corner)
3. Enter admin password: `admin123`
4. Navigate to the "Users" tab

## Features

### 1. User Statistics Dashboard
- **Total Users**: Shows the total number of registered users
- **New Users Today**: Displays users who registered today
- **Users with Bank Accounts**: Count of users who have created banking accounts

### 2. User Data Table
The main table displays comprehensive user information:
- **Email Address**: User's login email
- **Full Name**: User's registered name
- **Registration Date**: When the user joined
- **Bank Accounts**: Number of banking accounts owned
- **Total Balance**: Sum of all account balances (₹)
- **Actions**: Management options

### 3. User Management Actions

#### Add New User (➕ Add User)
- Create new user accounts manually
- Required fields: Name, Email, Password
- Automatic validation (email uniqueness, password length)
- Sets registration date automatically

#### View User Details (Double-click or Context Menu)
- Complete user profile information
- List of all banking accounts
- Individual account balances
- Total balance calculation

#### Edit User Information
- Modify user's full name
- Email addresses cannot be changed (used as unique identifier)
- Changes are saved immediately

#### Reset Password
- Change user's login password
- Minimum 6 characters required
- Secure password entry (hidden characters)

#### View Banking Accounts
- Detailed view of user's bank accounts
- Account numbers, types, and balances
- Account creation dates
- Total balance summary

#### Delete User
- Remove user from the system
- Warning if user has banking accounts
- Confirmation dialog for safety
- Banking accounts become "orphaned" (not deleted)

#### Export Users (📄 Export Users)
- Export all user data to CSV format
- Includes banking statistics
- Useful for reporting and backup

### 4. Interactive Features

#### Double-Click Actions
- Double-click any user row to view detailed information
- Opens comprehensive user details window

#### Right-Click Context Menu
- Right-click on any user for quick actions:
  - View Details
  - Edit User
  - Reset Password
  - View Bank Accounts
  - Delete User

#### Real-Time Refresh (🔄 Refresh)
- Updates user data and statistics
- Reloads banking account information
- Refreshes the entire table

## Integration with Banking System

### Account Ownership Tracking
- Each banking account is linked to a user via email
- Users can see their total balance across all accounts
- Administrators can track which users have accounts

### Banking Statistics
- Real-time calculation of user balances
- Count of accounts per user
- Total system balances per user

### Orphaned Account Prevention
- Warnings when deleting users with bank accounts
- Banking accounts remain in system for data integrity
- Future accounts can be reassigned if needed

## Data Files

### users.json
Contains user login credentials and profile information:
```json
{
  "email@example.com": {
    "name": "User Name",
    "email": "email@example.com", 
    "password": "password123",
    "join_date": "2025-07-06"
  }
}
```

### accounts.json
Banking accounts with owner email linking:
```json
{
  "account_number": {
    "name": "Account Holder",
    "balance": 1000.00,
    "type": "Savings",
    "created_date": "2025-07-06",
    "owner_email": "email@example.com"
  }
}
```

## Security Features

### Input Validation
- Email format validation
- Password strength requirements (minimum 6 characters)
- Duplicate email prevention
- Required field validation

### Confirmation Dialogs
- Delete operations require confirmation
- Warning messages for destructive actions
- Modal dialogs prevent accidental operations

### Data Integrity
- Atomic operations for data consistency
- Backup-friendly JSON format
- Error handling for file operations

## Current Demo Users

The system comes with three demo users:
1. **demo@example.com** - Demo User (password: demo123)
2. **admin@example.com** - Admin User (password: admin123)  
3. **agupta38160@gmail.com** - Ashish (password: 123456)

## Admin Capabilities Summary

✅ **User Oversight**
- Monitor all registered users
- Track registration trends
- View user activity statistics

✅ **Account Management** 
- Add users manually
- Edit user information
- Reset forgotten passwords
- Remove inactive users

✅ **Banking Integration**
- View user banking relationships
- Monitor account balances
- Track financial activity
- Identify banking patterns

✅ **Data Management**
- Export user data for analysis
- Backup user information
- Generate user reports
- Maintain data integrity

✅ **Security Administration**
- Password management
- Account validation
- Access control
- Audit trail maintenance

## Future Enhancements

Potential improvements that could be added:
- User activity logs
- Email verification system
- Bulk user operations
- Advanced filtering and search
- User role management
- Account linking/unlinking tools
- Detailed audit trails
- User communication tools
