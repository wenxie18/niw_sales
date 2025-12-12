# Code Review and Fix Plan

## Issues Identified

### 1. Status Not Persisting After Navigation
**Problem**: When user navigates away and comes back, status shows "No sending in progress" even when thread is running.

**Root Cause**: 
- Status endpoint relies on `sending_thread` global variable
- Thread object might be lost or not properly tracked
- Frontend polling might not be active when page loads

**Fix**:
- Add thread ID tracking to persist across page loads
- Check for running threads by process/thread ID, not just object reference
- Ensure frontend starts polling immediately on page load
- Add thread registry to track all active sending threads

### 2. app_password Accounts Not Sending
**Problem**: `sanqiacademia@gmail.com` with `app_password` is enabled but not sending.

**Root Cause**:
- Code prefers Gmail API if available
- If Gmail API initializes successfully, SMTP accounts are never used
- Logic should use BOTH Gmail API AND SMTP accounts in parallel

**Fix**:
- Modify sender initialization to use BOTH Gmail API and SMTP if both available
- Create unified sender that can handle both types
- OR: Initialize both senders and use them together

### 3. Thread Cleanup Logic
**Problem**: Threads might not be properly cleaned up, causing stale state.

**Fix**:
- Ensure thread cleanup happens in finally block
- Add thread registry to track all threads
- Clean up dead threads on status check

## Implementation Steps

1. **Fix Status Persistence**
   - Add thread ID to progress state
   - Check thread by ID, not just object reference
   - Start polling immediately on page load

2. **Fix Account Usage**
   - Modify sender logic to use both Gmail API and SMTP
   - Ensure all enabled accounts are included

3. **Add Thread Registry**
   - Track threads by ID
   - Clean up dead threads automatically

4. **Test All Scenarios**
   - Start sending, navigate away, come back
   - Enable/disable accounts
   - Mix of Gmail API and SMTP accounts

