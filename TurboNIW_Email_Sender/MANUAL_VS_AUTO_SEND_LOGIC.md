# Manual Send vs Auto-Send Logic Review

## Overview

Both manual and auto-send use the **same underlying sender classes** (`EmailSender` for SMTP, `GmailAPISender` for Gmail API) and share the **same history file** (`sent_history.json`). This ensures:
- ✅ **No duplicate sends** - Both check the same history
- ✅ **Shared daily limits** - Manual + auto-send combined cannot exceed account limits
- ✅ **Consistent behavior** - Same validation, blacklist, whitelist rules

---

## 🔵 MANUAL SEND Logic

### Entry Point
- **Web UI**: `/api/send/start` endpoint
- **Command Line**: `send_emails_smtp.py` or `send_emails_gmail_api.py`

### Flow

#### 1. **Initialization** (`send_emails_worker_direct`)
```
1. Load sent_history.json to get today's sent counts per account
2. Calculate total capacity = sum of all enabled accounts' daily_limit
3. Initialize progress tracking (in-memory state)
4. Set sending_active = True
```

#### 2. **Sender Selection**
- Prefers Gmail API if available, falls back to SMTP
- Initializes appropriate sender class (`GmailAPISender` or `EmailSender`)

#### 3. **CSV Processing** (`sender.process_csv()`)
```
1. Read CSV file
2. Filter recipients:
   - Skip invalid emails
   - Skip blacklisted emails
   - Skip already sent (checks sent_history.json)
3. Apply max_emails limit if specified (truncate list)
4. Validate all enabled accounts (check credentials)
```

#### 4. **Parallel Sending** (Both sender classes use same pattern)
```
1. Create shared Queue with all recipients
2. Create worker threads (one per account, up to max_parallel_accounts)
3. Each account thread:
   - Pulls recipient from shared queue
   - Checks daily limit: if sent_today >= daily_limit, stop
   - Double-checks not already sent (race condition protection)
   - Sends email via send_email()
   - Records in sent_history.json (thread-safe)
   - Waits random delay (delay_min to delay_max seconds)
   - Repeats until queue empty or limit reached
4. All threads run in parallel
```

#### 5. **Key Features**
- **Dynamic account rotation**: Accounts pull from shared queue until their limit
- **Thread-safe history**: Uses locks to prevent race conditions
- **Progress tracking**: Real-time updates via callback
- **Stop functionality**: Can be stopped mid-process
- **Error handling**: Failed accounts stop, others continue

---

## 🤖 AUTO-SEND Logic

### Entry Point
- **Scheduler**: APScheduler triggers `auto_send_emails()` at configured time (default: 10 AM ET)

### Flow

#### 1. **Pre-Checks**
```
1. Check if manual sending is active → Skip if yes
2. Check if auto-send is enabled → Skip if no
3. Load auto-send config (min_emails_per_account, max_emails_per_account)
```

#### 2. **Calculate Per-Account Targets**
```
For each enabled account:
1. Load sent_history.json to get sent_today count
2. Calculate remaining = daily_limit - sent_today
3. If remaining > 0:
   - Cap range at daily_limit:
     effective_min = min(min_emails, daily_limit)
     effective_max = min(max_emails, daily_limit)
   - Further cap at remaining:
     effective_max = min(effective_max, remaining)
   - Randomly select target: random.randint(effective_min, effective_max)
   - Store target for this account
```

**Example:**
- Account daily_limit: 200
- Already sent manually: 50
- Remaining: 150
- Auto-send range: 50-300
- Effective range: 50-150 (capped at remaining)
- Random target: 87 emails

#### 3. **CSV Processing**
```
1. Load default CSV file
2. Filter recipients (same as manual):
   - Skip invalid emails
   - Skip blacklisted emails
   - Skip already sent (checks sent_history.json)
3. Store filtered list
```

#### 4. **Sequential Per-Account Sending**
```
For each account with a target:
1. Select appropriate sender (Gmail API or SMTP)
2. Loop through recipients sequentially:
   - Check if already sent (double-check)
   - Check account daily limit again (may have changed)
   - Send email via send_email()
   - Record in sent_history.json
   - Wait random delay
   - Increment account_sent counter
   - Stop when account_sent >= target OR daily_limit reached
3. Move to next account
```

#### 5. **Key Differences from Manual Send**
- **Sequential per account**: Each account sends its target number, then moves to next
- **Pre-calculated targets**: Each account knows exactly how many to send
- **No shared queue**: Each account processes recipients in order
- **No parallel threads**: Accounts send one after another (but emails within an account are sequential)

---

## 🔄 Shared Components

### 1. **History File** (`sent_history.json`)
```json
{
  "recipients": {
    "email@example.com": {
      "send_count": 1,
      "last_sent": "2025-11-28",
      "accounts_used": ["account1@gmail.com"],
      "sent_dates": ["2025-11-28"]
    }
  },
  "daily_stats": {
    "2025-11-28": {
      "account1": 50,
      "account2": 100,
      "total": 150
    }
  }
}
```

### 2. **Daily Limit Enforcement**
Both manual and auto-send check:
```python
sent_today = daily_stats.get(account_id, 0)
if sent_today >= daily_limit:
    # Stop sending from this account
```

### 3. **Duplicate Prevention**
Both check before sending:
```python
if sender.is_already_sent(email):
    # Skip this recipient
```

### 4. **Validation Rules**
Both apply:
- Email format validation
- Blacklist check
- Whitelist check (for test emails)
- History check (already sent)

---

## 📊 Comparison Table

| Feature | Manual Send | Auto-Send |
|---------|-------------|-----------|
| **Trigger** | User clicks "Start Sending" | Scheduled (10 AM ET default) |
| **CSV Source** | User uploads or default | Always default CSV |
| **Account Distribution** | Parallel threads, shared queue | Sequential per account |
| **Target Calculation** | Send until limit or queue empty | Pre-calculated random target per account |
| **Max Emails** | User-specified (optional) | Calculated from range × accounts |
| **Stop Functionality** | Yes (user can stop) | No (runs to completion) |
| **Progress Tracking** | Real-time UI updates | Console logs only |
| **Daily Limit** | Shared (manual + auto) | Shared (manual + auto) |
| **Duplicate Prevention** | ✅ Same history file | ✅ Same history file |

---

## 🛡️ Safety Mechanisms

### 1. **No Duplicate Sends**
- Both check `is_already_sent()` before sending
- Uses same `sent_history.json` file
- Thread-safe locks prevent race conditions

### 2. **Daily Limit Protection**
- Manual send: Checks limit before each email
- Auto-send: Pre-calculates targets capped at remaining limit
- Both respect: `sent_today + new_sends <= daily_limit`

### 3. **Mutual Exclusion**
- Auto-send checks `sending_active` flag
- If manual send is running, auto-send skips
- Prevents conflicts and double-sending

### 4. **Range Capping**
- Auto-send range is automatically capped:
  - At daily_limit (if range exceeds it)
  - At remaining limit (if manual sends happened)
- Example: Range 50-300, limit 200 → Uses 50-200

---

## 🔍 Example Scenario

**Setup:**
- Account 1: daily_limit = 200
- Account 2: daily_limit = 250
- Auto-send range: 50-150

**Day 1 - Morning (Manual Send):**
- User manually sends 50 emails from Account 1
- Account 1: sent_today = 50, remaining = 150

**Day 1 - 10 AM (Auto-Send):**
- Account 1: remaining = 150, effective range = 50-150, target = 87
- Account 2: remaining = 250, effective range = 50-150, target = 142
- Auto-send sends 87 from Account 1, 142 from Account 2
- Total today: Account 1 = 137, Account 2 = 142

**Day 1 - Afternoon (Manual Send Again):**
- User tries to send 100 more
- Account 1: Can only send 63 more (200 - 137 = 63)
- Account 2: Can send 108 more (250 - 142 = 108)
- System automatically stops Account 1 at limit, continues Account 2

---

## ✅ Summary

**Both systems are safe and work together:**
1. ✅ Share the same history file (no duplicates)
2. ✅ Share the same daily limits (manual + auto combined)
3. ✅ Use the same validation rules
4. ✅ Auto-send respects manual sends (caps at remaining)
5. ✅ Manual send respects auto-send (checks history)
6. ✅ Mutual exclusion (auto-send skips if manual is active)

**The key difference:**
- **Manual**: Parallel threads, send until limit or queue empty
- **Auto**: Sequential per account, send exact pre-calculated target

Both are production-ready and safe to use together! 🚀

