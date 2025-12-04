#!/usr/bin/env python3
"""
Gmail API Email Sender
Sends emails using Gmail API (higher limits, more reliable).
No 100/day limit like SMTP - can send up to 2000/day with Google Workspace.
"""

import csv
import json
import re
import argparse
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime, date
from pathlib import Path
import time
import random

# Gmail API imports (install: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client)
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False

from email_templates_variants import format_email

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


class GmailAPISender:
    def __init__(self, config_file='config.json'):
        """Initialize Gmail API sender."""
        if not GMAIL_API_AVAILABLE:
            raise Exception(
                "Gmail API libraries not installed!\n"
                "Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
        
        # Store config file path for resolving relative paths
        self.config_file = str(Path(config_file).resolve())
        self.config = self.load_config(config_file)
        self.history = self.load_history()
        self.today = str(date.today())
        self.services = {}  # Cache for authenticated services
        self.failed_accounts = set()  # Track accounts that fail authentication
        self.stop_check = None  # Function to check if should stop
    
    def load_config(self, config_file):
        """Load configuration."""
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def load_history(self):
        """Load sent email history."""
        history_file = self.config['paths']['sent_history']
        if Path(history_file).exists():
            try:
                with open(history_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {"recipients": {}, "daily_stats": {}}
    
    def save_history(self):
        """Save history."""
        with open(self.config['paths']['sent_history'], 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def authenticate_account(self, account):
        """Authenticate and get Gmail API service for an account."""
        account_id = account['id']
        
        # Return cached service if available
        if account_id in self.services:
            return self.services[account_id]
        
        credentials_file = account.get('credentials_file')
        if not credentials_file:
            raise Exception(f"No credentials file for account {account_id}")
        
        # Resolve to absolute path if relative
        if not Path(credentials_file).is_absolute():
            # Assume relative to config file directory
            config_dir = Path(self.config_file).parent if hasattr(self, 'config_file') else Path.cwd()
            credentials_file = str(config_dir / credentials_file)
        
        # Resolve token file path similarly
        config_dir = Path(self.config_file).parent if hasattr(self, 'config_file') else Path.cwd()
        token_file = str(config_dir / '.secrets' / f"{account_id}_token.json")
        
        creds = None
        
        # Load existing token
        if Path(token_file).exists():
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save token
            Path(token_file).parent.mkdir(parents=True, exist_ok=True)
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        # Build service
        service = build('gmail', 'v1', credentials=creds)
        self.services[account_id] = service
        
        return service
    
    def create_message(self, account, to_email, to_name, subject, body):
        """Create email message with both plain text and HTML versions."""
        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr((account['name'], account['email']))
        msg['To'] = to_email
        msg['Subject'] = subject  # Use dynamic subject from variant
        
        # Convert plain text to HTML (preserve line breaks and formatting)
        html_body = body.replace('\n', '<br>\n')
        # Wrap in simple HTML structure - natural left-aligned like normal emails
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; line-height: 1.6; color: #000000;">
{html_body}
</body>
</html>"""
        
        # Attach both plain text and HTML versions
        msg.attach(MIMEText(body, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        return {'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode()}
    
    def send_email(self, account, recipient_email, recipient_name, paper_title="", publication_venue="arXiv"):
        """Send email using Gmail API."""
        account_id = account['id']
        
        try:
            # Authenticate
            service = self.authenticate_account(account)
            
            # Format content (randomly select variant)
            subject, body = format_email(recipient_name, paper_title, publication_venue)
            
            # Create message
            message = self.create_message(account, recipient_email, recipient_name, subject, body)
            
            # Send
            service.users().messages().send(userId='me', body=message).execute()
            
            # Record
            self.record_sent_email(recipient_email, recipient_name, paper_title, account)
            
            return True
            
        except FileNotFoundError as e:
            # Credentials file not found - mark account as failed and stop
            error_msg = f"Credentials file not found for account {account_id}: {e}"
            print(f"  ✗ {error_msg}")
            self.failed_accounts.add(account_id)
            raise Exception(error_msg)  # Raise to stop processing
        except HttpError as error:
            error_msg = f"Gmail API error for account {account_id}: {error}"
            print(f"  ✗ {error_msg}")
            # For API errors, mark as failed if it's an auth/permission issue
            if error.resp.status in [401, 403]:
                self.failed_accounts.add(account_id)
                raise Exception(error_msg)  # Raise to stop processing
            return False
        except Exception as e:
            error_msg = f"Error for account {account_id}: {e}"
            print(f"  ✗ {error_msg}")
            # If it's a path/credentials issue, mark as failed
            if "credentials" in str(e).lower() or "file" in str(e).lower():
                self.failed_accounts.add(account_id)
                raise Exception(error_msg)  # Raise to stop processing
            return False
    
    def set_stop_check(self, stop_check_func):
        """Set a function to check if sending should stop."""
        self.stop_check = stop_check_func
    
    def get_available_account(self):
        """Get account with capacity. Skips accounts that have failed authentication."""
        if self.today not in self.history['daily_stats']:
            self.history['daily_stats'][self.today] = {}
        
        daily_stats = self.history['daily_stats'][self.today]
        
        for account in self.config['accounts']:
            if not account.get('enabled', True):
                continue
            if account.get('auth_method') != 'gmail_api':
                continue
            
            account_id = account['id']
            
            # Skip accounts that have failed authentication
            if account_id in self.failed_accounts:
                continue
            
            sent_today = daily_stats.get(account_id, 0)
            daily_limit = account.get('daily_limit', 2000)
            
            if sent_today < daily_limit:
                return account, sent_today
        
        return None, None
    
    def validate_email(self, email):
        """Validate email."""
        if not email or not isinstance(email, str):
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))
    
    def is_blacklisted(self, email):
        """Check if email is in blacklist (should never receive emails)."""
        email_lower = email.lower()
        blacklist = self.config.get('blacklist', {}).get('emails', [])
        return email_lower in [e.lower() for e in blacklist]
    
    def is_already_sent(self, email):
        """Check if already sent. Returns False for whitelisted test emails."""
        email_lower = email.lower()
        
        # Check whitelist first - test emails can always be sent
        whitelist = self.config.get('test_whitelist', {}).get('emails', [])
        if email_lower in [e.lower() for e in whitelist]:
            return False  # Whitelisted emails can always be sent
        
        # Otherwise check normal history
        return email_lower in self.history['recipients']
    
    def record_sent_email(self, email, name, paper_title, account):
        """Record sent email."""
        email_lower = email.lower()
        timestamp = datetime.now().isoformat()
        account_id = account['id']
        account_email = account['email']
        
        if email_lower in self.history['recipients']:
            recipient = self.history['recipients'][email_lower]
            recipient['last_sent'] = self.today
            recipient['send_count'] += 1
            recipient['send_dates'].append(self.today)
            recipient['accounts_used'].append(account_email)
        else:
            self.history['recipients'][email_lower] = {
                'email': email,
                'name': name,
                'paper_title': paper_title,
                'first_sent': self.today,
                'last_sent': self.today,
                'send_count': 1,
                'send_dates': [self.today],
                'accounts_used': [account_email],
                'last_timestamp': timestamp
            }
        
        if self.today not in self.history['daily_stats']:
            self.history['daily_stats'][self.today] = {}
        
        self.history['daily_stats'][self.today][account_id] = \
            self.history['daily_stats'][self.today].get(account_id, 0) + 1
        
        self.history['daily_stats'][self.today]['total'] = sum(
            count for key, count in self.history['daily_stats'][self.today].items()
            if key != 'total'
        )
    
    def process_csv(self, csv_file, test_mode=False, max_emails=None):
        """Process CSV and send emails."""
        print(f"\n{'='*80}")
        print(f"GMAIL API SENDER - {'TEST MODE' if test_mode else 'LIVE MODE'}")
        print(f"{'='*80}\n")
        
        # Read CSV
        recipients = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                recipients.append(row)
        
        print(f"Total recipients: {len(recipients)}")
        
        # Filter
        to_send = []
        blacklisted = 0
        for recipient in recipients:
            email = recipient.get('Email', '').strip()
            if not self.validate_email(email):
                continue
            if self.is_blacklisted(email):
                blacklisted += 1
                continue
            if self.is_already_sent(email):
                continue
            to_send.append(recipient)
        
        print(f"Blacklisted (skipped): {blacklisted}")
        print(f"Ready to send: {len(to_send)}")
        
        if max_emails:
            to_send = to_send[:max_emails]
        
        if test_mode:
            to_send = to_send[:1]
        
        # Validate accounts before starting
        print("\n🔍 Validating accounts...")
        valid_accounts = []
        for account in self.config['accounts']:
            if not account.get('enabled', True):
                continue
            if account.get('auth_method') != 'gmail_api':
                continue
            
            account_id = account['id']
            try:
                # Try to authenticate to validate the account
                service = self.authenticate_account(account)
                valid_accounts.append(account_id)
                print(f"  ✓ {account_id}: Valid")
            except Exception as e:
                error_msg = str(e)
                print(f"  ✗ {account_id}: FAILED - {error_msg}")
                self.failed_accounts.add(account_id)
        
        if not valid_accounts:
            error_msg = "❌ No valid Gmail API accounts available! Please check credentials files."
            print(f"\n{error_msg}")
            raise Exception(error_msg)
        
        print(f"✅ {len(valid_accounts)} account(s) ready\n")
        
        # Send
        sent_count = 0
        failed_count = 0
        
        for i, recipient in enumerate(to_send, 1):
            # Check if should stop
            if self.stop_check and self.stop_check():
                print(f"\n⚠️  Stop requested - stopping email sending")
                break
            
            email = recipient.get('Email', '').strip()
            name = recipient.get('Author', recipient.get('Name', 'Colleague'))
            paper_title = recipient.get('Title', '')
            
            account, sent_today = self.get_available_account()
            
            if not account:
                print(f"\n⚠️  All accounts at limit or failed!")
                if self.failed_accounts:
                    print(f"   Failed accounts: {', '.join(self.failed_accounts)}")
                break
            
            print(f"[{i}/{len(to_send)}] {name} <{email}>")
            print(f"           Account: {account['id']} ({sent_today}/{account['daily_limit']})")
            
            try:
                if self.send_email(account, email, name, paper_title):
                    sent_count += 1
                    print(f"           ✓ Sent")
                    self.save_history()
                    if i < len(to_send):
                        delay_min = self.config['sending'].get('delay_min_seconds', 3)
                        delay_max = self.config['sending'].get('delay_max_seconds', 30)
                        delay = random.randint(delay_min, delay_max)
                        print(f"           ⏱️  Waiting {delay} seconds before next email...")
                        time.sleep(delay)
                else:
                    failed_count += 1
            except Exception as e:
                # Critical error (e.g., credentials not found) - stop processing
                error_msg = f"❌ Critical error: {e}"
                print(f"\n{error_msg}")
                print(f"   Stopping email sending. Please fix the account configuration.")
                raise  # Re-raise to stop the process
        
        # Summary
        print(f"\n{'='*80}")
        print(f"Sent: {sent_count} | Failed: {failed_count}")
        print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description='Send emails using Gmail API')
    parser.add_argument('--csv', required=True, help='CSV file with recipients')
    parser.add_argument('--config', default='config.json', help='Config file')
    parser.add_argument('--test', action='store_true', help='Test mode (1 email)')
    parser.add_argument('--max', type=int, help='Max emails to send')
    
    args = parser.parse_args()
    
    try:
        sender = GmailAPISender(args.config)
        sender.process_csv(args.csv, test_mode=args.test, max_emails=args.max)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

