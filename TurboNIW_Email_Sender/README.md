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
      "auth_method": "gmail_api",
      "credentials_file": ".secrets/gmail_credentials_account2.json",
      "daily_limit": 50,
      "enabled": true
    }
  ],
  "email": {
    "_note": "Subject lines are dynamically generated from email_templates_variants.py (5 variants)"
  },
  "sending": {
    "delay_min_seconds": 10,
    "delay_max_seconds": 60,
    "max_retries": 2
  },
  "paths": {
    "sent_history": "sent_history.json"
  },
  "test_whitelist": {
    "_note": "Emails in this list can always be sent to, even if already sent before (for testing)",
    "emails": [
      "test@example.com"
    ]
  },
  "blacklist": {
    "_note": "Emails in this list will NEVER receive emails, even if they appear in the CSV",
    "emails": [
      "advisor@university.edu"
    ]
  }
}
```

**Key features:**
- **Subject lines**: Automatically generated from 5 variants (no need to set manually)
- **Random delays**: Between `delay_min_seconds` and `delay_max_seconds` (mimics human behavior)
- **Whitelist**: Test emails that can always be sent (useful for testing)
- **Blacklist**: Emails that will never receive emails (e.g., advisors, colleagues)

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
1. "Greetings from Wen, a resource you might find helpful"
2. "Hi from Wen, sharing a helpful NIW resource"
3. "Hello from Wen, a resource for NIW applications"
4. "Quick hello and a resource to share"
5. "Hi, Wen here, wanted to share something helpful"

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

## 🔧 Customizing Email Templates

Edit `email_templates_variants.py` to customize email content:

- **Subject lines**: Modify `SUBJECT_VARIANTS` list
- **Email bodies**: Modify `EMAIL_BODY_VARIANT_1` through `EMAIL_BODY_VARIANT_5`
- **Signature**: Modify `EMAIL_SIGNATURE`

The system automatically:
- Randomly selects one subject line and one body variant per email
- Formats recipient name (uses first name)
- Inserts paper title (if provided in CSV)
- Adds signature to all emails

**Key features:**
- Empathetic tone emphasizing helping researchers
- Mentions attorney fees being high (without explicit pricing)
- Includes referral appreciation (subtle, no explicit amounts)
- Best wishes for research at the end
- No dashes (uses commas for natural flow)

---

## 📁 File Structure

```
TurboNIW_Email_Sender/
├── send_emails_smtp.py          # SMTP sender (app passwords)
├── send_emails_gmail_api.py     # Gmail API sender
├── email_templates_variants.py  # Multi-variant email templates (5×5 combinations)
├── email_template.py            # Legacy template (for reference)
├── test_gmail_auth.py           # Gmail API authentication helper
├── config.json                  # Your configuration (⚠️ NOT in git)
├── sent_history.json            # Tracking data (auto-created, ⚠️ NOT in git)
├── requirements.txt             # Python dependencies
├── .secrets/                    # ⚠️ NEVER COMMIT THIS!
│   ├── account*_password.txt    # App passwords for SMTP accounts
│   ├── gmail_credentials_account*.json  # OAuth credentials for Gmail API
│   └── account*_gmail_api_token.json   # OAuth tokens (auto-generated)
├── README.md                    # This file
├── EMAIL_VARIANTS_STRATEGY.md   # Anti-spam strategy documentation
├── ANTI_SPAM_IMPROVEMENTS.md    # Spam prevention improvements
└── EMAIL_REVISIONS_MARKETING.md # Marketing-focused revisions
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
