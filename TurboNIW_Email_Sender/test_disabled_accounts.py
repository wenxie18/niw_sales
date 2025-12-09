#!/usr/bin/env python3
"""
Test script to check if disabled Gmail accounts can still send emails.
Tests both SMTP and Gmail API methods.
"""

import json
import smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

# Try Gmail API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False
    print("⚠️  Gmail API libraries not available - will only test SMTP")

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / 'config.json'
SECRETS_DIR = BASE_DIR / '.secrets'

def load_config():
    """Load configuration."""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def get_password(account):
    """Get app password from file."""
    password_file = BASE_DIR / account['app_password_file']
    if not password_file.exists():
        return None
    with open(password_file, 'r') as f:
        return f.read().strip()

def test_smtp_account(account):
    """Test SMTP authentication and sending."""
    print(f"\n{'='*60}")
    print(f"Testing SMTP: {account['id']} ({account['email']})")
    print(f"{'='*60}")
    
    password = get_password(account)
    if not password:
        print(f"❌ Password file not found: {account['app_password_file']}")
        return False
    
    try:
        # Test authentication
        print("1. Testing SMTP authentication...")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(account['email'], password)
            print("   ✅ Authentication successful!")
        
        # Test sending (to a test email)
        print("2. Testing email sending...")
        test_email = "vaneshieh@gmail.com"  # Your test email
        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr((account['name'], account['email']))
        msg['To'] = test_email
        msg['Subject'] = "Test Email - Account Status Check"
        
        body_text = "This is a test email to verify account status."
        body_html = "<p>This is a test email to verify account status.</p>"
        
        msg.attach(MIMEText(body_text, 'plain'))
        msg.attach(MIMEText(body_html, 'html'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(account['email'], password)
            server.send_message(msg)
        
        print(f"   ✅ Email sent successfully to {test_email}!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ Authentication failed: {e}")
        print(f"   ⚠️  Account may be disabled or password invalid")
        return False
    except smtplib.SMTPException as e:
        print(f"   ❌ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_gmail_api_account(account):
    """Test Gmail API authentication and sending."""
    if not GMAIL_API_AVAILABLE:
        print("⚠️  Gmail API libraries not available")
        return False
    
    print(f"\n{'='*60}")
    print(f"Testing Gmail API: {account['id']} ({account['email']})")
    print(f"{'='*60}")
    
    credentials_file = BASE_DIR / account['credentials_file']
    if not credentials_file.exists():
        print(f"❌ Credentials file not found: {account['credentials_file']}")
        return False
    
    token_file = SECRETS_DIR / f"{account['id']}_token.json"
    
    try:
        # Load credentials
        print("1. Loading credentials...")
        creds = None
        if token_file.exists():
            creds = Credentials.from_authorized_user_file(str(token_file), 
                ['https://www.googleapis.com/auth/gmail.send'])
        
        # If no valid credentials, try to refresh
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("2. Refreshing expired token...")
                creds.refresh(Request())
            else:
                print("   ❌ No valid token found - account needs re-authentication")
                return False
        
        # Build service
        print("3. Building Gmail service...")
        service = build('gmail', 'v1', credentials=creds)
        print("   ✅ Service built successfully!")
        
        # Test sending
        print("4. Testing email sending...")
        test_email = "vaneshieh@gmail.com"
        
        message = MIMEMultipart('alternative')
        message['From'] = formataddr((account['name'], account['email']))
        message['To'] = test_email
        message['Subject'] = "Test Email - Account Status Check"
        
        body_text = "This is a test email to verify account status."
        body_html = "<p>This is a test email to verify account status.</p>"
        
        message.attach(MIMEText(body_text, 'plain'))
        message.attach(MIMEText(body_html, 'html'))
        
        raw_message = message.as_string().encode('utf-8')
        raw_message_b64 = base64.urlsafe_b64encode(raw_message).decode('utf-8')
        
        send_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message_b64}
        ).execute()
        
        print(f"   ✅ Email sent successfully! Message ID: {send_message['id']}")
        return True
        
    except HttpError as e:
        error_details = e.error_details[0] if e.error_details else {}
        reason = error_details.get('reason', 'Unknown')
        message = error_details.get('message', str(e))
        
        print(f"   ❌ Gmail API error: {reason}")
        print(f"   Message: {message}")
        
        if reason == 'invalidGrant':
            print("   ⚠️  Token expired or revoked - account may be disabled")
        elif reason == 'insufficientPermissions':
            print("   ⚠️  Insufficient permissions - may need re-authentication")
        elif 'disabled' in message.lower() or 'suspended' in message.lower():
            print("   ⚠️  Account appears to be disabled or suspended")
        
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Test all disabled accounts."""
    print("="*60)
    print("TESTING DISABLED GMAIL ACCOUNTS")
    print("="*60)
    
    config = load_config()
    
    # Find accounts with spy.observer.wx or qqq.observer.wx
    test_accounts = []
    for account in config['accounts']:
        email = account.get('email', '')
        if 'spy.observer.wx@gmail.com' in email or 'qqq.observer.wx@gmail.com' in email:
            test_accounts.append(account)
    
    if not test_accounts:
        print("No accounts found with spy.observer.wx or qqq.observer.wx")
        return
    
    print(f"\nFound {len(test_accounts)} account(s) to test:")
    for acc in test_accounts:
        print(f"  - {acc['id']}: {acc['email']} ({acc['auth_method']})")
    
    results = {}
    
    for account in test_accounts:
        if account['auth_method'] == 'app_password':
            results[account['id']] = test_smtp_account(account)
        elif account['auth_method'] == 'gmail_api':
            results[account['id']] = test_gmail_api_account(account)
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    for account_id, success in results.items():
        status = "✅ WORKING" if success else "❌ FAILED/DISABLED"
        print(f"{account_id}: {status}")
    
    print("\n" + "="*60)
    print("RECOMMENDATION")
    print("="*60)
    
    all_failed = all(not result for result in results.values())
    if all_failed:
        print("⚠️  All accounts failed - they appear to be disabled by Google")
        print("   Recommendation: Keep them disabled in config.json")
        print("   Action: No code changes needed (already disabled)")
    else:
        working = [acc_id for acc_id, result in results.items() if result]
        print(f"✅ Some accounts are working: {', '.join(working)}")
        print("   You may be able to re-enable these accounts")

if __name__ == "__main__":
    import base64
    main()

