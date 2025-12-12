# Code Review and Optimization Analysis

## Current Implementation Review

### How `process_csv()` Works Now

1. **CSV Reading & Filtering** (Lines 317-341):
   - Reads entire CSV file into memory
   - Filters recipients:
     - Skip invalid emails
     - Skip blacklisted emails
     - Skip already sent (checks `sent_history.json`)
   - Result: `to_send` list with all valid recipients

2. **Shared Queue Approach** (Lines 376-379):
   - Creates ONE `Queue()` with ALL filtered recipients
   - All accounts pull from this same queue
   - Each account thread competes for recipients

3. **Account Worker Logic** (Lines 403-497):
   - Each account thread:
     - Pulls recipient from shared queue
     - Checks daily limit → stop if reached
     - Checks target (if auto-send) → stop if reached
     - Double-checks not already sent (race condition protection)
     - Sends email
     - Repeats until queue empty or limit/target reached

### Issues with Current Approach

1. **Inefficiency for Auto-Send**:
   - Accounts with targets (e.g., 100 emails) may pull 200+ recipients from queue
   - Many recipients get skipped (already sent by other accounts)
   - Queue contention overhead
   - Unclear which account gets which recipients

2. **Race Conditions**:
   - Multiple accounts might pull same recipient (though we check before sending)
   - Extra history checks needed

3. **Wasted Work**:
   - Account pulls recipient → checks history → already sent → skip → pull next
   - This happens repeatedly

## Proposed Optimization

### For Auto-Send: Pre-Assignment Strategy

**Logic:**
1. Calculate targets per account (already done)
2. Pre-assign recipients to each account:
   - Account 1: Get first 100 recipients (or target + buffer)
   - Account 2: Get next 150 recipients
   - Account 3: Get next 200 recipients
   - etc.
3. Each account has its own queue/list
4. Still check history (double-check, but should be minimal)

**Benefits:**
- ✅ No queue contention
- ✅ Clear assignment (account knows exactly what to send)
- ✅ Less skipping (each account has unique recipients)
- ✅ More efficient (no wasted pulls)
- ✅ Better for fixed targets

**Implementation:**
- Add optional parameter `account_recipients_map` to `process_csv()`
- If provided, use pre-assigned recipients per account
- If not provided, use shared queue (current approach for manual send)

### For Manual Send: Keep Shared Queue

**Why:**
- More flexible (accounts can pick up slack if one finishes early)
- Simpler code (one queue)
- Works well when targets are dynamic

## Code Changes Needed

1. **Modify `process_csv()` to support both modes**:
   - Shared queue mode (default, for manual send)
   - Pre-assigned mode (for auto-send with targets)

2. **Update auto-send to pre-assign recipients**:
   - Calculate targets
   - Pre-assign recipients to accounts
   - Pass to `process_csv()` with `account_recipients_map`

3. **Keep backward compatibility**:
   - Manual send continues to use shared queue
   - Auto-send uses pre-assignment

