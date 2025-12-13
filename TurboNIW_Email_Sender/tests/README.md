# Test Scripts

This folder contains test and utility scripts for the email sending system.

## Test Scripts

### `test_gmail_auth.py`
Tests Gmail API authentication for a specific account.
- **Usage**: `python3.9 test_gmail_auth.py --account-id <account_id>`
- **Purpose**: Verify that Gmail API credentials and tokens are working correctly

### `test_read_inbox_bounces.py`
Tests the bounce/block message detection functionality.
- **Usage**: `python3.9 test_read_inbox_bounces.py --account-id <account_id> [--hours 24]`
- **Purpose**: Verify that the system can correctly detect bounce messages and rate limit notifications in the inbox

### `test_disabled_accounts.py`
Tests account status and disabled account detection.
- **Usage**: `python3.9 test_disabled_accounts.py`
- **Purpose**: Check which accounts are disabled and why

## Test Data Files

### `test_email.csv`
Sample CSV file for testing email sending functionality.

### `test_gmail_api.csv`
Sample CSV file specifically for testing Gmail API sending.

## Running Tests

All test scripts should be run from the `TurboNIW_Email_Sender` directory:

```bash
cd TurboNIW_Email_Sender
python3.9 tests/test_gmail_auth.py --account-id account3_gmail_api
python3.9 tests/test_read_inbox_bounces.py --account-id account3_gmail_api
python3.9 tests/test_disabled_accounts.py
```

