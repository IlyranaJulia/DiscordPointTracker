# Automatic Order Point Distribution System

## Overview

This system allows you to automatically distribute Discord points to customers based on order data files (CSV). Customers receive email notifications with verification codes to claim their points directly in Discord.

## Requirements

### 1. SendGrid Email Service
- **Purpose**: Send verification emails to customers
- **Required**: SendGrid API key
- **Setup**: 
  1. Create account at sendgrid.com
  2. Get API key from Settings > API Keys
  3. Add to environment: `SENDGRID_API_KEY=your_key_here`

### 2. Order Data File Format (CSV)
- **Supported formats**: CSV files with email and order information
- **Required columns**: Any column containing "email" or "mail" (case insensitive)
- **Optional columns**: Order ID, amount, date, etc.
- **Examples**:
  ```csv
  email,order_id,amount
  customer@example.com,ORD-001,29.99
  user@domain.com,ORD-002,49.99
  ```

### 3. Verified Email Domain
- **Required**: Configure a verified sender domain in SendGrid
- **Update**: Change `from_email` in `order_processor.py` from "noreply@yourdomain.com" to your domain

## How It Works

### 1. Process Order File
```python
# Upload CSV file with customer orders
# System reads email addresses and creates point requests
# Generates unique verification codes for each order
```

### 2. Email Notifications
```
Subject: Discord Points Available - Order [ID]

Your order ORD-001 qualifies for 100 Discord points!

To claim: !claim ABC123XYZ

Verification Code: ABC123XYZ
```

### 3. Customer Claims Points
```
User types in Discord: !claim ABC123XYZ
Bot verifies code and adds points to user account
Code becomes invalid after use
```

## Implementation Components

### 1. OrderProcessor Class (`order_processor.py`)
- Processes CSV files
- Sends emails via SendGrid
- Manages verification codes
- Handles point claims

### 2. Database Tables
```sql
-- Stores pending point claims
CREATE TABLE point_requests (
    email TEXT,
    order_id TEXT,
    points_amount INTEGER,
    verification_code TEXT,
    status TEXT DEFAULT 'pending',
    discord_user_id INTEGER,
    created_at TIMESTAMP,
    processed_at TIMESTAMP
);
```

### 3. Discord Commands
- `!claim <code>` - Users claim points with verification codes

### 4. Dashboard Features
- Upload and process order files
- View pending claims
- Monitor email delivery status

## Setup Instructions

### 1. Get SendGrid API Key
```bash
# Sign up at sendgrid.com
# Create API key with Mail Send permissions
# Add to environment variables
```

### 2. Configure Sender Email
```python
# In order_processor.py, update:
from_email=Email("noreply@yourdomain.com")  # Your verified domain
```

### 3. Prepare Order Data
```csv
# Example CSV format:
customer_email,order_number,purchase_amount
john@example.com,12345,29.99
jane@example.com,12346,49.99
```

### 4. Process Orders
```python
# Via dashboard or API:
# 1. Upload CSV file
# 2. Set points per order (e.g., 100 points)
# 3. Set server name for emails
# 4. Process file - sends emails automatically
```

## Security Features

- **Unique codes**: Each verification code works only once
- **Email validation**: Only valid email formats accepted
- **Database tracking**: Complete audit trail of all claims
- **Expiration**: Codes can be set to expire after time period
- **Rate limiting**: Prevent abuse of claim system

## Benefits

1. **Automated**: No manual point distribution needed
2. **Verified**: Only customers with valid orders get points
3. **Trackable**: Complete audit trail of all distributions
4. **Scalable**: Handle hundreds of orders at once
5. **Professional**: Branded email notifications

## Usage Examples

### Example 1: Monthly Order Rewards
```
1. Export monthly orders from e-commerce system
2. Upload CSV to dashboard
3. Set 50 points per order
4. Process file - 500 customers get emails
5. Customers claim points in Discord over time
```

### Example 2: Special Promotion
```
1. Filter orders for specific product/date range
2. Set bonus points (200 per order)
3. Custom email with promotion details
4. Track redemption rates in dashboard
```

## Monitoring & Analytics

- **Email delivery rates**: Track successful/failed emails
- **Claim rates**: See how many customers claim points
- **Pending requests**: View unclaimed codes
- **User analytics**: Track point distribution impact

This system transforms your order data into an engaging Discord community reward system!