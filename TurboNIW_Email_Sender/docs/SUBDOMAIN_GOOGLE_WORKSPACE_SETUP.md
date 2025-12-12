# Subdomain Setup: info@mail.turboniw.com with Google Workspace

## Overview

This guide shows you how to:
- **Keep** `contact@turboniw.com` in Zoho (no changes needed)
- **Create** `info@mail.turboniw.com` in Google Workspace for sending emails
- **Send** 2,000 emails/day via Gmail API from `info@mail.turboniw.com`

**Cost**: $6/month (1 Google Workspace account)

---

## How It Works

### Current Setup
- **Domain**: `turboniw.com` (registered at GoDaddy)
- **Email Hosting**: Zoho Mail
- **Current Email**: `contact@turboniw.com` (in Zoho)
- **MX Records**: Point to Zoho (for `turboniw.com`)

### After Setup
- **Main Domain** (`turboniw.com`): MX records still point to Zoho
  - `contact@turboniw.com` → receives emails in Zoho ✅
- **Subdomain** (`mail.turboniw.com`): MX records point to Google Workspace
  - `info@mail.turboniw.com` → receives emails in Google Workspace ✅
  - `info@mail.turboniw.com` → sends 2,000 emails/day via Gmail API ✅

---

## Step-by-Step Instructions

### Step 1: Sign Up for Google Workspace

1. **Go to Google Workspace**
   - Visit: https://workspace.google.com/
   - Click **"Get Started"**

2. **Enter Business Details**
   - Business name: (your business name)
   - Number of employees: (select appropriate)
   - Country/region: (select your country)

3. **Enter Domain**
   - **Important**: Enter `mail.turboniw.com` (the subdomain, not the main domain)
   - Click **"Next"**

4. **Choose Plan**
   - Select **"Business Starter"** ($6/user/month)
   - Click **"Next"**

5. **Create Admin Account**
   - First name, Last name
   - Username: `info` (this will create `info@mail.turboniw.com`)
   - Password: (create a strong password)
   - Click **"Next"**

6. **Verify Domain Ownership**
   - Google will provide a **verification code** (TXT record)
   - **Save this code** - you'll need it in Step 2

---

### Step 2: Verify Domain in GoDaddy

1. **Log into GoDaddy**
   - Go to: https://dcc.godaddy.com/
   - Sign in with your GoDaddy account

2. **Select Your Domain**
   - Click on **"My Products"**
   - Find `turboniw.com`
   - Click **"DNS"** (or **"Manage DNS"**)

3. **Add TXT Record for Verification**
   - Click **"Add"** or **"Add Record"**
   - Select **"TXT"** from the dropdown
   - **Name**: `mail` (this verifies the subdomain `mail.turboniw.com`)
   - **Value**: (paste the verification code from Google Workspace)
   - **TTL**: 600 (or default)
   - Click **"Save"**

4. **Wait for DNS Propagation**
   - Wait **5-10 minutes** for DNS to update
   - DNS changes can take up to 48 hours, but usually work within minutes

5. **Verify in Google Workspace**
   - Go back to Google Workspace setup page
   - Click **"Verify"** or **"Verify Domain"**
   - If successful, you'll see a confirmation message

---

### Step 3: Add MX Records for Subdomain in GoDaddy

1. **Get MX Records from Google Workspace**
   - After verification, Google Workspace will show you **MX records**
   - They will look like:
     ```
     ASPMX.L.GOOGLE.COM (Priority: 1)
     ALT1.ASPMX.L.GOOGLE.COM (Priority: 5)
     ALT2.ASPMX.L.GOOGLE.COM (Priority: 5)
     ALT3.ASPMX.L.GOOGLE.COM (Priority: 10)
     ALT4.ASPMX.L.GOOGLE.COM (Priority: 10)
     ```
   - **Copy these** - you'll need them

2. **Add MX Records in GoDaddy**
   - Still in GoDaddy DNS settings for `turboniw.com`
   - **Add each MX record** (you'll add 5 records total):

   **First MX Record:**
   - Click **"Add"** → Select **"MX"**
   - **Name**: `mail` (this is the subdomain)
   - **Priority**: `1`
   - **Value**: `ASPMX.L.GOOGLE.COM`
   - **TTL**: 3600 (or default)
   - Click **"Save"**

   **Second MX Record:**
   - Click **"Add"** → Select **"MX"**
   - **Name**: `mail`
   - **Priority**: `5`
   - **Value**: `ALT1.ASPMX.L.GOOGLE.COM`
   - **TTL**: 3600
   - Click **"Save"**

   **Third MX Record:**
   - Click **"Add"** → Select **"MX"**
   - **Name**: `mail`
   - **Priority**: `5`
   - **Value**: `ALT2.ASPMX.L.GOOGLE.COM`
   - **TTL**: 3600
   - Click **"Save"**

   **Fourth MX Record:**
   - Click **"Add"** → Select **"MX"**
   - **Name**: `mail`
   - **Priority**: `10`
   - **Value**: `ALT3.ASPMX.L.GOOGLE.COM`
   - **TTL**: 3600
   - Click **"Save"**

   **Fifth MX Record:**
   - Click **"Add"** → Select **"MX"**
   - **Name**: `mail`
   - **Priority**: `10`
   - **Value**: `ALT4.ASPMX.L.GOOGLE.COM`
   - **TTL**: 3600
   - Click **"Save"**

3. **Verify MX Records**
   - After adding all 5 MX records, your DNS should show:
     ```
     mail.turboniw.com MX records:
     - Priority 1: ASPMX.L.GOOGLE.COM
     - Priority 5: ALT1.ASPMX.L.GOOGLE.COM
     - Priority 5: ALT2.ASPMX.L.GOOGLE.COM
     - Priority 10: ALT3.ASPMX.L.GOOGLE.COM
     - Priority 10: ALT4.ASPMX.L.GOOGLE.COM
     ```

4. **Wait for DNS Propagation**
   - Wait **24-48 hours** for MX records to fully propagate
   - You can test by sending an email to `info@mail.turboniw.com`

---

### Step 4: Complete Google Workspace Setup

1. **Finish Account Setup**
   - Go back to Google Workspace admin console
   - Complete any remaining setup steps
   - Verify that `info@mail.turboniw.com` account is created

2. **Test Email Receiving**
   - Send a test email to `info@mail.turboniw.com`
   - Check if it arrives in Google Workspace inbox
   - This confirms MX records are working

---

### Step 5: Set Up Gmail API for Your System

1. **Create OAuth Credentials** (if not already done)
   - Go to: https://console.cloud.google.com/
   - Create a new project or use existing project
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - **Note**: Use the same OAuth credentials as your other Gmail accounts

2. **Add Account to `config.json`**
   ```json
   {
     "id": "info_mail_turboniw",
     "email": "info@mail.turboniw.com",
     "name": "Wen",
     "auth_method": "gmail_api",
     "credentials_file": ".secrets/gmail_credentials_info_mail_turboniw.json",
     "daily_limit": 2000,
     "enabled": true
   }
   ```

3. **Save Credentials File**
   - Download OAuth credentials JSON file
   - Save to: `TurboNIW_Email_Sender/.secrets/gmail_credentials_info_mail_turboniw.json`

4. **Authenticate Account**
   - Go to your website: http://127.0.0.1:5001/accounts
   - Click **"Authenticate"** for `info@mail.turboniw.com`
   - Complete OAuth flow
   - Account should show as "Ready"

---

## Important Notes

### Email Address Format
- **Sending from**: `info@mail.turboniw.com`
- **Receiving at**: `info@mail.turboniw.com`
- **Note**: Recipients will see `info@mail.turboniw.com` (not `info@turboniw.com`)

### DNS Records Summary
- **Main domain** (`turboniw.com`): MX records still point to Zoho
- **Subdomain** (`mail.turboniw.com`): MX records point to Google Workspace
- Both can coexist without conflicts

### Sending Limits
- **Daily Limit**: 2,000 emails/day from `info@mail.turboniw.com`
- **Via**: Gmail API (same as your other Gmail accounts)
- **Shared Limit**: This is separate from your other Gmail accounts

### Cost
- **Google Workspace**: $6/month (Business Starter plan)
- **Zoho**: Free (keep `contact@turboniw.com` there)
- **Total**: $6/month

---

## Troubleshooting

### Issue: Verification Failed
- **Solution**: Wait 10-15 minutes after adding TXT record, then try again
- **Check**: Make sure TXT record name is `mail` (not `@` or blank)

### Issue: MX Records Not Working
- **Solution**: Wait 24-48 hours for full DNS propagation
- **Check**: Use online MX record checker: https://mxtoolbox.com/
- **Verify**: Enter `mail.turboniw.com` and check if MX records show Google's servers

### Issue: Can't Receive Emails
- **Check**: Verify MX records are correct in GoDaddy
- **Check**: Make sure MX records have `mail` as the name (subdomain)
- **Wait**: DNS propagation can take up to 48 hours

### Issue: Authentication Fails
- **Check**: Make sure OAuth credentials are correct
- **Check**: Make sure `info@mail.turboniw.com` account exists in Google Workspace
- **Check**: Make sure you're using the correct credentials file path

---

## Testing

### Test 1: Receive Email
1. Send an email to `info@mail.turboniw.com` from an external email
2. Check Google Workspace inbox
3. Email should arrive within a few minutes

### Test 2: Send Email via Gmail API
1. Add account to `config.json`
2. Authenticate via website
3. Send a test email using your system
4. Check recipient's inbox

### Test 3: Verify MX Records
1. Go to: https://mxtoolbox.com/
2. Enter: `mail.turboniw.com`
3. Click **"MX Lookup"**
4. Should show Google's MX records

---

## Next Steps

After setup is complete:
1. ✅ Test receiving emails at `info@mail.turboniw.com`
2. ✅ Add account to `config.json`
3. ✅ Authenticate via website
4. ✅ Send test emails
5. ✅ Start using for bulk sending (2,000 emails/day capacity)

---

## Summary

**What You've Set Up:**
- ✅ `contact@turboniw.com` → Still in Zoho (no changes)
- ✅ `info@mail.turboniw.com` → In Google Workspace
- ✅ Can send 2,000 emails/day from `info@mail.turboniw.com`
- ✅ Cost: $6/month

**DNS Records:**
- Main domain (`turboniw.com`): MX → Zoho
- Subdomain (`mail.turboniw.com`): MX → Google Workspace

**Result:**
- Both email systems work independently
- No conflicts or migration needed
- Clean separation of receiving and sending

---

## Need Help?

If you encounter issues:
1. Check DNS propagation: https://mxtoolbox.com/
2. Verify MX records in GoDaddy
3. Check Google Workspace admin console
4. Review error messages in your system logs

Good luck with your setup! 🚀

