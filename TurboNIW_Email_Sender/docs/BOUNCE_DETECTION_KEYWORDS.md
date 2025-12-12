# Bounce Detection Keywords - Where They Are

## Summary

**Keywords are NOT in `config.json`** - they are **hardcoded in the Python file**.

---

## Location of Keywords

### File: `send_emails_gmail_api.py`

### Location 1: Bounce Message Detection (Inbox Checking)
**Function**: `check_rate_limit_bounce()`  
**Lines**: 451-461

```python
# Check for rate limit indicators
rate_limit_phrases = [
    'reached a limit for sending mail',
    'daily sending quota',
    'quota exceeded',
    'you have reached a limit'
]

# Check for message blocked/rejected indicators
blocked_phrases = [
    'message rejected',
]
```

### Location 2: API Error Detection (When Sending Fails)
**Function**: `send_email()` (error handling)  
**Lines**: 561-569

```python
# Check for rate limit or sending limit errors
is_rate_limit = (
    error_status == 429 or  # Too Many Requests
    (error_status == 403 and 'limit' in error_message.lower()) or
    (error_status == 403 and 'quota' in error_message.lower()) or
    (error_status == 403 and 'rateLimitExceeded' in error_reason) or
    'reached a limit for sending mail' in error_message.lower() or
    'mail delivery subsystem' in error_message.lower() or
    'daily sending quota' in error_message.lower()
)
```

---

## How to Modify Keywords

1. **Open**: `TurboNIW_Email_Sender/send_emails_gmail_api.py`
2. **Find**: Lines 451-461 (for bounce message detection)
3. **Edit**: Add or remove phrases from the lists
4. **Save**: The file

**Note**: You need to restart the website/server for changes to take effect.

---

## How Accounts Get Disabled

When bounce/block is detected:
1. The code calls `disable_account_for_24h(account_id)`
2. This adds `"disabled_until": "2025-12-13T16:43:40.637926"` to the account in `config.json`
3. The account is automatically skipped during sending

---

## How to Re-enable Accounts

### Option 1: Wait 24 Hours
- Accounts are automatically re-enabled after 24 hours
- The `disabled_until` timestamp is checked and removed when expired

### Option 2: Manually Re-enable (Immediate)
1. **Open**: `config.json`
2. **Find**: Accounts with `"disabled_until"` field
3. **Remove**: The `"disabled_until"` line
4. **Set**: `"enabled": true`
5. **Save**: The file

### Option 3: Use Website (If Available)
- Some versions may have a "Re-enable" button on the accounts page

---

## Current Keywords (After Your Edits)

You've already removed some keywords to reduce false positives. Current keywords are:

**Rate Limit Phrases:**
- `'reached a limit for sending mail'`
- `'daily sending quota'`
- `'quota exceeded'`
- `'you have reached a limit'`

**Blocked Phrases:**
- `'message rejected'`

**Removed Keywords (to reduce false positives):**
- ~~`'limit for sending mail'`~~ (removed)
- ~~`'sending limit'`~~ (removed)
- ~~`'message blocked'`~~ (removed)
- ~~`'message was blocked'`~~ (removed)
- ~~`'blocked. see technical details'`~~ (removed)
- ~~`'delivery status notification (failure)'`~~ (removed)

---

## To Add Keywords Back

If you want to add keywords back, edit `send_emails_gmail_api.py`:

```python
rate_limit_phrases = [
    'reached a limit for sending mail',
    'limit for sending mail',  # Add this back
    'sending limit',           # Add this back
    'daily sending quota',
    'quota exceeded',
    'you have reached a limit'
]

blocked_phrases = [
    'message blocked',                    # Add this back
    'message was blocked',                # Add this back
    'blocked. see technical details',    # Add this back
    'message rejected',
    'delivery status notification (failure)'  # Add this back
]
```

---

## Important Notes

1. **Keywords are case-insensitive** - they're converted to lowercase before matching
2. **Keywords match anywhere in the text** - subject, snippet, or body
3. **First match wins** - if any phrase matches, the account is disabled
4. **False positives** - Some bounce messages might match keywords but not be actual rate limits
5. **Restart required** - Changes to keywords require restarting the server/website

---

## Testing Keywords

To test if keywords work:
1. Send a test email that triggers a bounce
2. Check the logs for: `🚨 RATE LIMIT BOUNCE DETECTED` or `🚨 MESSAGE BLOCKED/REJECTED DETECTED`
3. Check `config.json` for `disabled_until` field

---

## All Accounts Re-enabled

✅ All 10 accounts have been re-enabled:
- Removed `disabled_until` fields
- Set `enabled: true`

You can now start sending emails again!

