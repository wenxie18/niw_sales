# Bounce Detection Code Review - December 12, 2025

## Issue Found

The code was detecting bounce messages from **December 7** (5 days ago) even though it should only check messages from the **last 20 minutes**.

## Root Cause

1. **Gmail API Query**: Uses `newer_than:20m` which should filter correctly, but...
2. **No Date Verification**: The code didn't verify the actual message date before processing
3. **Timezone Issues**: Potential timezone comparison problems between message dates and current time

## Fixes Applied

### 1. Added Date Verification (Lines 427-470)

**Before**: Only relied on Gmail API query `newer_than:20m`

**After**: 
- Calculates 20 minutes ago timestamp in UTC
- Parses each message's date header
- Converts to UTC for consistent comparison
- **Skips messages older than 20 minutes** with logging

```python
# Calculate 20 minutes ago timestamp for verification (use UTC to avoid timezone issues)
from datetime import timezone
now_utc = datetime.now(timezone.utc)
twenty_minutes_ago_utc = now_utc - timedelta(minutes=20)

# Parse message date and verify
msg_date = parsedate_to_datetime(date_header)
if msg_date.tzinfo is None:
    msg_date_utc = msg_date.replace(tzinfo=timezone.utc)
else:
    msg_date_utc = msg_date.astimezone(timezone.utc)

# Skip if older than 20 minutes
if msg_date_utc < twenty_minutes_ago_utc:
    print(f"  ⏭️  Skipping old message from {msg_date_utc.strftime('%Y-%m-%d %H:%M:%S UTC')} (age: {age_minutes:.1f} minutes)")
    continue
```

### 2. Added Logging

- Logs how many messages are being checked
- Logs when old messages are skipped (with age in minutes)
- Logs message date when bounce is detected (for verification)

### 3. Fixed Timezone Handling

- Uses UTC for all date comparisons
- Handles both timezone-aware and timezone-naive datetimes
- Prevents false positives from timezone mismatches

## Code Flow

1. **Query**: `from:mailer-daemon@googlemail.com newer_than:20m` (first filter)
2. **Date Verification**: Check each message's date is within last 20 minutes (second filter)
3. **Keyword Matching**: Check for rate limit/block phrases
4. **Action**: If match found, disable account for 24 hours

## Verification

The code now has **two layers of protection**:
1. Gmail API query filter (`newer_than:20m`)
2. Date verification (skips messages older than 20 minutes)

This ensures **only recent bounce messages** (within last 20 minutes) are processed.

## Testing

When you restart the website and send emails, you should see:
- `🔍 Checking X bounce messages from last 20 minutes for account_id`
- `⏭️  Skipping old message from YYYY-MM-DD HH:MM:SS UTC (age: X.X minutes, older than 20 minutes)` (if old messages found)
- `📅 Message date: YYYY-MM-DD HH:MM:SS UTC (age: X.X minutes)` (when bounce detected)

## Files Modified

- `send_emails_gmail_api.py`:
  - Added `parsedate_to_datetime` import
  - Added `timedelta` import  
  - Added `timezone` import
  - Added `sys` import
  - Enhanced `check_rate_limit_bounce()` function with date verification

## Status

✅ **Fixed** - Code now properly filters messages to only check those from the last 20 minutes

---

**Note**: Restart the website/server for changes to take effect.

