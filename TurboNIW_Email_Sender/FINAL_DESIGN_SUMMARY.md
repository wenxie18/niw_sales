# Final Design Summary: Manual Send vs Auto-Send

## Core Principle: **Same Logic, Different Triggers**

Both manual send and auto-send use **exactly the same code path** - the only difference is:
1. **Trigger**: User click vs. scheduler
2. **Targets**: Auto-send sets `account_targets` before calling `process_csv()`

---

## Unified Flow

### 1. **CSV Processing** (`process_csv()`)
```
1. Read CSV file
2. Filter recipients:
   - Skip invalid emails
   - Skip blacklisted emails
   - Skip already sent (checks sent_history.json)
3. Create shared Queue with all filtered recipients
4. Validate all enabled accounts
```

### 2. **Parallel Sending** (Same for both manual and auto-send)
```
1. Create shared Queue with all recipients
2. Create worker threads (one per account, up to max_parallel_accounts)
3. Each account thread:
   - Pulls recipient from shared queue
   - Checks daily limit → stop if reached
   - Checks target (if auto-send) → stop if reached
   - Double-checks not already sent (race condition protection)
   - Sends email
   - Records in sent_history.json (thread-safe)
   - Waits random delay
   - Repeats until queue empty or limit/target reached
4. All threads run in parallel
```

### 3. **Key Differences**

| Aspect | Manual Send | Auto-Send |
|--------|-------------|-----------|
| **Trigger** | User clicks "Start Sending" | Scheduler (10 AM ET) |
| **Entry Point** | `send_emails_worker_direct()` | `auto_send_emails()` |
| **Target Calculation** | None (sends until limit) | Pre-calculated per account |
| **account_targets** | Not set (empty dict) | Set before `process_csv()` |
| **process_csv()** | Same method | Same method |
| **Queue System** | Shared queue | Shared queue |
| **Parallel Logic** | Same | Same |

---

## Code Structure

### Manual Send Flow
```python
# web_app/app.py - send_emails_worker_direct()
1. Initialize sender (GmailAPISender or EmailSender)
2. Set stop_check callback
3. Set progress_callback
4. Call sender.process_csv(csv_path, max_emails=max_emails)
   → Uses shared queue
   → Accounts pull until daily_limit reached
```

### Auto-Send Flow
```python
# web_app/app.py - auto_send_emails()
1. Calculate targets per account (random within range, capped at daily_limit)
2. Initialize sender (GmailAPISender or EmailSender)
3. Set sender.account_targets = {account_id: target, ...}
4. Set progress_callback
5. Call sender.process_csv(csv_path, max_emails=None)
   → Uses shared queue (SAME as manual send)
   → Accounts pull until target OR daily_limit reached
```

---

## Account Worker Logic (Both Use Same Code)

```python
def account_worker(account):
    while True:
        # Check stop flag
        if stop_check(): break
        
        # Check daily limit
        if sent_today >= daily_limit: break
        
        # Check target (only for auto-send, when account_targets is set)
        if account_id in self.account_targets:
            if sent_today >= self.account_targets[account_id]: break
        
        # Get recipient from shared queue
        recipient = recipient_queue.get()
        
        # Double-check not already sent (race condition protection)
        if is_already_sent(email): continue
        
        # Send email
        send_email(...)
        
        # Record and delay
        record_sent_email(...)
        time.sleep(random_delay)
```

---

## Safety Mechanisms

1. **No Duplicates**: Both check `is_already_sent()` before sending
2. **Shared History**: Both use same `sent_history.json`
3. **Shared Limits**: Daily limits are shared (manual + auto combined)
4. **Mutual Exclusion**: Auto-send skips if manual send is active
5. **Thread Safety**: All history updates use locks

---

## Summary

✅ **Simple Design**: One code path for both manual and auto-send
✅ **No Complexity**: No pre-assignment, no separate queues
✅ **Same Logic**: Both use shared queue, parallel threads, same validation
✅ **Only Difference**: Auto-send sets `account_targets` before calling `process_csv()`

The design is clean, simple, and maintainable! 🚀

