# Email Sender for Research Outreach

Professional email sending tool with multi-account support, smart tracking, and rate limit protection.

## ✨ Features

- 📧 **Two sending methods**: SMTP (app passwords) or Gmail API
- 🔄 **Multi-account rotation**: Distribute sending across multiple Gmail accounts
- 🎭 **Multi-variant emails**: 5 subjects × 5 body templates = 25 unique combinations to **avoid spam filters**
- 📊 **Smart tracking**: Records who was sent, when, and how many times
- 🛡️ **Rate limit protection**: Respects Gmail's 10 emails/day limit per account
- ✅ **Skip duplicates**: Never send twice to the same person
- 🎯 **Test mode**: Test with 1 recipient before going live
- 🔒 **Secure credentials**: Passwords stored in `.secrets/` folder (gitignored)

---

## 📋 Quick Start

### 1. Install Dependencies

   ```bash
cd TurboNIW_Email_Sender
   pip install -r requirements.txt
   ```

For Gmail API (optional, higher limits):
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 2. Setup Configuration

Copy the example config:
   ```bash
cp config.json.example config.json
```

Edit `config.json`:
```json
{
  "accounts": [
    {
      "id": "account1",
      "email": "your-email1@gmail.com",
      "name": "Your Name",
      "auth_method": "app_password",
      "app_password_file": ".secrets/account1_password.txt",
      "daily_limit": 10,
      "enabled": true
    },
    {
      "id": "account2",
      "email": "your-email2@gmail.com",
      "name": "Your Name",
      "auth_method": "app_password",
      "app_password_file": ".secrets/account2_password.txt",
      "daily_limit": 10,
      "enabled": true
    }
  ],
  "email": {
    "subject": "Your email subject here"
  },
  "sending": {
    "delay_between_emails_seconds": 3,
    "max_retries": 3
  },
  "paths": {
    "sent_history": "sent_history.json"
  }
}
```

### 3. Setup Gmail App Passwords

1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Security → 2-Step Verification (enable if not already)
3. App passwords → Create new app password
4. Copy the 16-character password

Create password files:
```bash
mkdir -p .secrets
echo "your-16-char-password-here" > .secrets/account1_password.txt
echo "another-16-char-password" > .secrets/account2_password.txt
```

⚠️ **Security**: Never commit `.secrets/` folder to git!

### 4. Authenticate Gmail API Accounts (If Using)

If you're using Gmail API accounts (not just SMTP), you need to authenticate them:

1. **Add credentials file** to `.secrets/` folder (e.g., `gmail_credentials_accountX.json`)
2. **Add account to config.json** with `auth_method: "gmail_api"`
3. **Add your email as test user** in Google Cloud Console:
   - Go to "APIs & Services" → "OAuth consent screen"
   - Scroll to "Test users" → Click "+ ADD USERS"
   - Add your Gmail address → Click "SAVE"
4. **Run authentication:**
   ```bash
   python test_gmail_auth.py
   ```
   - Browser will open for each Gmail API account
   - Sign in and allow access
   - Token files will be saved automatically

**Note:** You only need to authenticate once per account. Tokens are saved in `.secrets/accountX_gmail_api_token.json`.

### 5. Prepare Your CSV File

Your CSV must have these columns:
- `Email`: Recipient email address
- `Author` or `Name`: Recipient's name
- `Title` (optional): Paper title or other reference

Example:
```csv
Email,Author,Title
john@university.edu,John Doe,Paper Title Here
jane@research.org,Jane Smith,Another Paper
```

### 6. Send Emails

**Test mode (send to 1 person):**
```bash
python send_emails_smtp.py --csv recipients.csv --test
```

**Send 10 emails:**
```bash
python send_emails_smtp.py --csv recipients.csv --max 10
```

**Send all (up to daily limits):**
```bash
python send_emails_smtp.py --csv recipients.csv
```

---

## 🎯 Sending Methods

### Method 1: SMTP (App Passwords) - Recommended

**Pros:**
- ✅ Simple setup
- ✅ No OAuth flow
- ✅ Works immediately

**Cons:**
- ⚠️ Limited to ~10-100 emails/day per account
- ⚠️ Can trigger security alerts if overdone

**Usage:**
```bash
python send_emails_smtp.py --csv recipients.csv
```

### Method 2: Gmail API

**Pros:**
- ✅ Higher limits (up to 2000/day with Google Workspace)
- ✅ More reliable
- ✅ Better for bulk sending

**Cons:**
- ⚠️ More complex setup (OAuth credentials)
- ⚠️ Requires user authentication flow

**Setup:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials JSON file
6. Save to `.secrets/gmail_credentials_accountX.json` (where X is your account number)
7. Add account to `config.json`:
   ```json
   {
     "id": "accountX_gmail_api",
     "email": "your-email@gmail.com",
     "name": "Your Name",
     "auth_method": "gmail_api",
     "credentials_file": ".secrets/gmail_credentials_accountX.json",
     "daily_limit": 50,
     "enabled": true
   }
   ```

**Authenticate New Account:**
After adding credentials and updating config, authenticate the account:
```bash
python test_gmail_auth.py
```
This will:
- Open a browser window for each Gmail API account
- Ask you to sign in and allow access
- Save authentication tokens to `.secrets/accountX_gmail_api_token.json`
- You only need to do this once per account

**Important:** Make sure to add your email as a **test user** in Google Cloud Console:
- Go to "APIs & Services" → "OAuth consent screen"
- Scroll to "Test users"
- Click "+ ADD USERS" and add your Gmail address
- Click "SAVE"

**Usage:**
```bash
python send_emails_gmail_api.py --csv recipients.csv
```

---

## 📊 Tracking System

All sent emails are tracked in `sent_history.json`:

```json
{
  "recipients": {
    "email@example.com": {
      "name": "John Doe",
      "first_sent": "2025-12-02",
      "last_sent": "2025-12-02",
      "send_count": 1,
      "send_dates": ["2025-12-02"],
      "accounts_used": ["account1"],
      "paper_title": "Example Paper"
    }
  },
  "daily_stats": {
    "2025-12-02": {
      "account1": 10,
      "account2": 8,
      "total": 18
    }
  }
}
```

**Benefits:**
- ✅ Never send twice to same person
- ✅ Track sending history
- ✅ Monitor daily limits per account
- ✅ See which account was used

---

## 💡 Best Practices

### For Gmail App Passwords (10 emails/day limit)

**Recommended strategy:**
- Use 2 accounts = 20 emails/day
- Send in morning and evening batches
- Wait 24 hours between sends
- Monitor `sent_history.json` for daily counts

**Example daily schedule:**
```bash
# Morning (9 AM)
python send_emails_smtp.py --csv recipients.csv --max 10

# Evening (5 PM)  
python send_emails_smtp.py --csv recipients.csv --max 10
```

### For Gmail API (2000 emails/day limit)

**You can send much more aggressively:**
   ```bash
# Send 100 at a time
python send_emails_gmail_api.py --csv recipients.csv --max 100
   ```

### General Tips

1. **Always test first:**
   ```bash
   python send_emails_smtp.py --csv recipients.csv --test
   ```

2. **Start small:**
   - Day 1: Send 5 emails
   - Day 2: Send 10 emails
   - Day 3+: Full quota

3. **Monitor for blocks:**
   - If you get errors, stop immediately
   - Wait 24 hours before resuming
   - Consider switching to Gmail API

4. **Keep backups:**
   ```bash
   cp sent_history.json sent_history_backup_$(date +%Y%m%d).json
   ```

---

## 🎭 Email Variants — Avoiding Spam Filters

### Why Variants Matter

Sending **identical emails** repeatedly triggers spam filters. Gmail/Outlook detect:
- ❌ Same subject line = mass mailing fingerprint
- ❌ Same body text = automated campaign
- ❌ Same timing = bot behavior

### Our Solution: Multi-Variant System

**5 Subject Line Variants:**
1. "A resource for NIW green card applications (from a fellow researcher)"
2. "Quick NIW resource that might help your students/colleagues"
3. "Thought this might be useful — NIW DIY tool for researchers"
4. "Following up on your {venue} work — NIW resource to share"
5. "NIW green card resource (in case it's helpful)"

**5 Email Body Variants:**
- Each has the **same core message** (TurboNIW resource)
- Different wording, structure, and phrasing
- All maintain authentic, peer-to-peer tone
- No pushy sales language

**Result:**
- ✅ 5 × 5 = **25 unique email combinations**
- ✅ Each recipient gets a **randomly selected variant**
- ✅ Looks like **individual outreach**, not mass mailing
- ✅ **Lower spam risk** = higher deliverability

### How It Works

```python
# Automatic variant selection
from email_templates_variants import format_email

# Each call returns a random (subject, body) pair
subject, body = format_email(
    name="Jane Smith",
    publication_venue="ACL"
)
```

**See `EMAIL_VARIANTS_STRATEGY.md` for full details.**

---

## 🚨 Gmail Limits & Warnings

### Free Gmail Account

| Method | Daily Limit | Recommendation |
|--------|-------------|----------------|
| **SMTP** | ~100 emails | Use **10/day** to be safe |
| **Gmail API** | 500 emails | Can use 100-200/day safely |

### Google Workspace

| Method | Daily Limit | Recommendation |
|--------|-------------|----------------|
| **SMTP** | ~500 emails | Use 100/day to be safe |
| **Gmail API** | 2,000 emails | Can use 500-1000/day |

### What Happens If You Exceed Limits?

- ⚠️ **24-hour sending block** on that account
- ⚠️ Repeated violations may trigger manual review
- ⚠️ Account can still receive emails
- ✅ Block automatically lifts after 24 hours

---

## 🔧 Customizing Email Template

Edit `email_template.py` to customize your email content:

```python
def format_email(recipient_name):
    """
    Customize this function to change email content.
    
    Returns:
        tuple: (html_content, plain_text_content)
    """
    html = f"""
    <html>
    <body>
        <p>Hi {recipient_name},</p>
        <p>Your message here...</p>
    </body>
    </html>
    """
    
    plain_text = f"""
    Hi {recipient_name},
    
    Your message here...
    """
    
    return html, plain_text
```

---

## 📁 File Structure

```
TurboNIW_Email_Sender/
├── send_emails_smtp.py          # SMTP sender (app passwords)
├── send_emails_gmail_api.py     # Gmail API sender
├── email_template.py            # Email content template
├── config.json                  # Your configuration
├── config.json.example          # Example config
├── sent_history.json            # Tracking data (auto-created)
├── requirements.txt             # Python dependencies
├── .secrets/                    # ⚠️ NEVER COMMIT THIS!
│   ├── account1_password.txt    # App password for account 1
│   └── account2_password.txt    # App password for account 2
└── README.md                    # This file
```

---

## 🐛 Troubleshooting

### "Authentication failed"
- Check app password is correct (16 characters, no spaces)
- Verify 2-Step Verification is enabled
- Try generating a new app password

### "Daily limit reached"
- Check `sent_history.json` daily_stats
- Wait 24 hours before sending more
- Use additional accounts or switch to Gmail API

### "Connection refused"
- Check internet connection
- Verify Gmail SMTP is not blocked by firewall
- Try different network (disable VPN if using)

### "Recipients not found in CSV"
- Verify CSV has `Email` and `Author` columns
- Check CSV encoding (should be UTF-8)
- Ensure no extra spaces in column names

---

## 📞 Support & Tips

### Check Sending Status

```bash
# View today's stats
cat sent_history.json | grep "$(date +%Y-%m-%d)"

# Count total sent
cat sent_history.json | grep '"send_count"' | wc -l
```

### Reset History (if needed)

```bash
# Backup first!
cp sent_history.json sent_history_backup.json

# Reset
echo '{"recipients": {}, "daily_stats": {}}' > sent_history.json
```

---

## ⚖️ Legal & Ethics

- ✅ Only send to people who might be interested
- ✅ Include clear contact info and unsubscribe option
- ✅ Respect opt-outs immediately
- ❌ Never buy email lists
- ❌ Don't send spam

**Recommendation**: Add unsubscribe info to your template:
```
If you'd prefer not to receive these emails, please reply with "unsubscribe"
```

---

## 📝 License

For academic/research outreach use.

---

**Need help?** Check `sent_history.json` for tracking data or review error messages carefully.
