# Private Email Submission System

## How It Works

### For Users (Private & Secure)
1. **Private Messages Only**: Users must DM the bot (not public channels)
2. **Simple Command**: `!submitemail your-order@email.com`
3. **Privacy Protected**: Only admins can see submitted emails
4. **One Email Per User**: Can't spam multiple submissions

### For Admins (Dashboard View)
1. **Admin Dashboard**: View all email submissions at `/dashboard`
2. **User Information**: See Discord ID, username, and submitted email
3. **Status Management**: Mark emails as verified, processed, or rejected
4. **Admin Notes**: Add notes for each submission

## User Experience

### Step 1: User DMs Bot
```
User: !submitemail john.doe@gmail.com
Bot: ✅ Email Submitted Successfully
     Your order email john.doe@gmail.com has been submitted for point verification.
     
     What's Next?
     Server admins will verify your order and you'll receive your points automatically.
```

### Step 2: Admin Dashboard View
```
Email Submissions Dashboard:
┌─────────────────────────────────────────────────────────────┐
│ Discord User       │ Email Address      │ Status   │ Date   │
├─────────────────────────────────────────────────────────────┤
│ john_doe (ID: 123) │ john.doe@gmail.com │ Pending  │ Today  │
│ jane_user (ID: 456)│ jane@example.com   │ Verified │ Today  │
└─────────────────────────────────────────────────────────────┘
```

### Step 3: Admin Processing
- Admin sees email submission in dashboard
- Checks if email exists in order database
- Can mark as "verified" and add admin notes
- System can auto-generate verification codes for matched orders

## Privacy Features

### User Privacy
- ✅ Emails only visible to server admins
- ✅ Must use private messages (DM) with bot
- ✅ Cannot submit multiple pending emails
- ✅ Secure database storage

### Admin Capabilities
- View all email submissions
- Match emails to order database
- Track processing status
- Add private admin notes
- Update submission status

## Integration with Order Processing

### Manual Matching
1. User submits email via DM
2. Admin sees email in dashboard
3. Admin checks if email exists in order CSV
4. Admin manually generates/provides verification code

### Automatic Matching (Future Enhancement)
1. User submits email
2. System automatically checks against order database
3. If found, auto-generates verification code
4. Sends verification code to user via DM

## Commands Available

### Users (DM Only)
- `!submitemail your-email@example.com` - Submit order email
- `!claim ABCD1234` - Claim points with verification code

### Admins (Dashboard)
- View all email submissions
- Update submission status
- Add admin notes
- Process bulk verifications

## Database Schema

```sql
email_submissions:
- id (auto-increment)
- discord_user_id (Discord user ID)
- discord_username (Display name)
- email_address (Submitted email)
- submitted_at (Timestamp)
- status (pending/verified/rejected)
- processed_at (When admin processed)
- admin_notes (Admin comments)
```

This system provides a secure, private way for users to submit their order emails and for admins to efficiently process point distributions.