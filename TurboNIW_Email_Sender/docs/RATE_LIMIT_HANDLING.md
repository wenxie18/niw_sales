# Rate Limit Handling and Gmail Sending Limits

## Problem

Your Gmail account (`phd.help.phd@gmail.com`) hit a sending limit at 50 emails, receiving:
> "You have reached a limit for sending mail. Your message was not sent."

## Gmail Sending Limits

### Official Limits (2024-2025)
- **Free Gmail Accounts**: Up to 500 emails per day
- **Google Workspace Accounts**: Up to 2,000 emails per day

### Why You Hit Limit at 50?

**Possible reasons:**
1. **New Account**: New Gmail accounts may have lower initial limits (50-100/day) that increase over time
2. **Bulk Email Detection**: Google may temporarily restrict accounts that appear to be sending bulk emails
3. **Account Reputation**: Accounts with low sending history may have stricter limits
4. **Temporary Restrictions**: Google may impose temporary limits if they detect unusual patterns

### Gmail API vs SMTP

**Gmail API:**
- ✅ Higher limits (up to 2,000/day for Workspace)
- ✅ Better error handling (returns specific error codes)
- ✅ Can detect rate limits via HTTP status codes (429, 403)
- ✅ More reliable for bulk sending

**SMTP (App Passwords):**
- ❌ Lower limits (typically 100-500/day for free accounts)
- ❌ Less reliable error messages
- ❌ Harder to detect rate limits

**Recommendation**: Use Gmail API for primary sending (as you're doing).

---

## Solution: Enhanced Rate Limit Detection

### What We Added

1. **Gmail API Error Detection**:
   - Detects HTTP 429 (Too Many Requests)
   - Detects HTTP 403 with "limit" or "quota" messages
   - Detects error messages containing:
     - "reached a limit for sending mail"
     - "mail delivery subsystem"
     - "daily sending quota"
     - "rateLimitExceeded"

2. **SMTP Error Detection**:
   - Detects SMTP exceptions with rate limit messages
   - Checks for "mail delivery subsystem" errors
   - Detects quota/limit-related errors

3. **Automatic Account Stopping**:
   - When rate limit is detected, account is marked as `failed`
   - Account thread stops immediately
   - Other accounts continue sending
   - Recipient is NOT put back in queue (account is done for today)

### How It Works

```python
# In send_email() method
try:
    # Send email via Gmail API or SMTP
    ...
except HttpError as error:
    if is_rate_limit_error(error):
        # Mark account as failed
        self.failed_accounts.add(account_id)
        # Raise exception to stop this account
        raise Exception(f"Rate limit reached for {account_id}")
```

```python
# In account_worker() thread
try:
    send_email(...)
except Exception as e:
    if 'rate limit reached' in str(e).lower():
        # Don't put recipient back - account is done
        recipient_queue.task_done()
        break  # Stop this account thread
    else:
        # Other errors - put recipient back for other accounts
        recipient_queue.put(recipient)
```

---

## Best Practices

### 1. **Start Conservative**
- New accounts: Start with 20-50 emails/day
- Gradually increase over weeks
- Monitor for rate limit errors

### 2. **Use Gmail API**
- Higher limits
- Better error detection
- More reliable

### 3. **Distribute Across Accounts**
- Don't send all emails from one account
- Spread across multiple accounts
- Each account has its own limit

### 4. **Monitor Errors**
- Check logs for rate limit messages
- If account hits limit, it will automatically stop
- Other accounts continue sending

### 5. **Account Warm-up**
- For new accounts, start with 10-20 emails/day
- Increase by 10-20 per week
- Build account reputation

---

## Current Behavior

✅ **Automatic Detection**: Code now detects rate limit errors
✅ **Immediate Stop**: Account stops sending when limit is hit
✅ **Other Accounts Continue**: Other accounts keep sending
✅ **No Retries**: Recipient is not retried (account is done for today)
✅ **Clear Logging**: Error messages clearly indicate rate limit

---

## Recommendations for Your Account

1. **Reduce Daily Limit**: Set `phd.help.phd@gmail.com` to 40-45 emails/day (below the 50 limit you hit)
2. **Monitor**: Watch for rate limit errors in logs
3. **Gradual Increase**: If no errors for a week, increase by 5-10 emails/day
4. **Use Multiple Accounts**: Distribute sending across multiple Gmail API accounts
5. **Account Age**: Older accounts typically have higher limits

---

## Future Improvements

- Track rate limit occurrences per account
- Automatically reduce daily limit when rate limit is hit
- Alert/notification when account hits limit
- Account warm-up schedule for new accounts

