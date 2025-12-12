# Bounce Email Detection for Rate Limits

## Problem

Gmail doesn't always return rate limit errors via API. Instead, it:
1. ✅ Accepts the email (API call succeeds)
2. ⏱️ Sends the email
3. 📧 Then sends a bounce message to your inbox: "You have reached a limit for sending mail. Your message was not sent."

This means we need to **check the inbox** for bounce messages to detect rate limits.

---

## Solution: Inbox Monitoring

### How It Works

1. **Before Sending**: Periodically check inbox (every 30 seconds) for bounce messages
2. **After Sending**: Wait 3 seconds, then check for new bounce messages
3. **Pattern Matching**: Look for messages from `mailer-daemon@googlemail.com` with rate limit phrases
4. **Auto-Stop**: If bounce detected, mark account as failed and stop immediately

### Implementation

```python
def check_rate_limit_bounce(self, account, service):
    """Check inbox for rate limit bounce messages."""
    # Search for: from:mailer-daemon@googlemail.com newer_than:10m
    # Check subject/body for:
    #   - "reached a limit for sending mail"
    #   - "limit for sending mail"
    #   - "sending limit"
    #   - "daily sending quota"
    #   - "quota exceeded"
    # If found → mark account as failed
```

### Gmail API Scopes Required

**Updated Scopes:**
- `gmail.send` - Send emails
- `gmail.readonly` - Read inbox to check for bounce messages

**Important**: Existing accounts need to re-authenticate to grant the new `gmail.readonly` scope.

---

## How to Re-Authenticate

Since we added `gmail.readonly` scope, existing accounts need to re-authenticate:

1. **Via Web UI**: Click "Authenticate" button for each Gmail API account
2. **Via Command Line**: Run `python3.9 test_gmail_auth.py`
3. **Grant Permissions**: When browser opens, grant both:
   - Send email on your behalf
   - Read your email (for bounce detection)

---

## Features

### ✅ Automatic Detection
- Checks inbox every 30 seconds (per account)
- Checks after each email send (waits 3 seconds for bounce to arrive)
- Pattern matches bounce messages

### ✅ Efficient
- Only checks every 30 seconds (not every email)
- Only searches last 10 minutes of emails
- Doesn't block sending if check fails

### ✅ Safe
- If bounce check fails (e.g., no permission), continues sending
- Non-blocking: doesn't slow down email sending significantly

### ✅ Immediate Stop
- When bounce detected, account stops immediately
- Other accounts continue sending
- Clear error messages in logs

---

## Example Flow

```
1. Account sends email #50
2. API call succeeds ✅
3. Wait 3 seconds...
4. Check inbox for bounce messages
5. Find: "You have reached a limit for sending mail"
6. 🚨 RATE LIMIT BOUNCE DETECTED
7. Mark account as failed
8. Stop this account immediately
9. Other accounts continue sending
```

---

## Configuration

The bounce checking is **enabled by default**. To disable:

```python
sender.check_bounce_emails = False
```

But we recommend keeping it enabled for automatic rate limit detection.

---

## Benefits

✅ **Catches Rate Limits**: Detects bounces that API doesn't report
✅ **Automatic**: No manual checking needed
✅ **Fast**: Detects within 3-30 seconds
✅ **Safe**: Doesn't break if permission not granted
✅ **Efficient**: Minimal API calls (every 30s per account)

---

## Next Steps

1. **Re-authenticate all Gmail API accounts** to grant `gmail.readonly` scope
2. **Test**: Send a few emails and verify bounce detection works
3. **Monitor**: Check logs for "RATE LIMIT BOUNCE DETECTED" messages

The system will now automatically detect and stop accounts when they hit rate limits! 🚀

