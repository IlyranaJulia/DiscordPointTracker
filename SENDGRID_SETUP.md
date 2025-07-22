# SendGrid API Key Setup Guide

## Step 1: Create SendGrid Account
1. Go to https://sendgrid.com/
2. Click "Sign Up" or "Get Started Free"
3. Choose the **Free Plan** (100 emails/day forever)
4. Complete account registration with your email

## Step 2: Verify Your Email
1. Check your email for verification link
2. Click the verification link
3. Complete your profile setup

## Step 3: Create API Key
1. Log into SendGrid dashboard
2. Go to **Settings** → **API Keys** (left sidebar)
3. Click **"Create API Key"**
4. Choose **"Restricted Access"** for security
5. Name it "Discord Bot Points System"
6. Under **Mail Send**, select **"Full Access"**
7. Click **"Create & View"**
8. **COPY THE API KEY IMMEDIATELY** (you won't see it again)

## Step 4: Add to Your Project
1. In Replit, go to **Tools** → **Secrets** (lock icon)
2. Add new secret:
   - Key: `SENDGRID_API_KEY`
   - Value: (paste your copied API key)
3. Click **"Add Secret"**

## Step 5: Verify Sender Domain (Optional but Recommended)
1. In SendGrid, go to **Settings** → **Sender Authentication**
2. Click **"Verify a Single Sender"**
3. Use an email you control (like admin@yourdomain.com)
4. Fill out the form and verify
5. Update `order_processor.py` with your verified email

## For Your CSV Format
Your CSV should look like this:
```csv
email,amount
customer1@example.com,29.99
customer2@example.com,49.99
customer3@example.com,19.99
```

## Alternative CSV Formats Supported
```csv
customer_email,order_total
user@domain.com,25.50
```

```csv
email_address,purchase_amount,order_date
buyer@example.com,75.00,2025-07-22
```

The system automatically detects columns containing:
- **Email**: "email", "mail", "customer_email", etc.
- **Amount**: "amount", "total", "price", "cost", etc.

## Points Calculation Options

### Option 1: Fixed Points Per Order
```python
# Everyone gets same points regardless of order amount
points_per_order = 100  # Fixed 100 points
```

### Option 2: Points Based on Amount
```python
# 1 point per dollar spent (minimum 10 points)
# $29.99 order = 30 points
# $5.00 order = 10 points (minimum)
```

The current system uses Option 2 with your minimum points setting.

## Free SendGrid Limits
- **100 emails per day** (perfect for small-medium Discord servers)
- **No monthly limit** (resets daily)
- **Professional email templates**
- **Delivery analytics**

## Security Tips
- Never share your API key
- Use "Restricted Access" not "Full Access"
- Only give "Mail Send" permissions
- Store in Replit Secrets, not in code

## Testing
Once set up, you can test with a small CSV file containing your own email to verify everything works before processing real customer orders.