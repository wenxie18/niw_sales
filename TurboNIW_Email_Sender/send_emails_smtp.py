#!/usr/bin/env python3
"""
Multi-Account Gmail SMTP Email Sender
Sends personalized emails using app passwords with smart account rotation.
Limits: 10 emails per account per day.
"""

import csv
import smtplib
import json
import re
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime, date
from pathlib import Path
import time
import random
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed

from email_templates_variants import format_email


class EmailSender:
    def __init__(self, config_file='config.json'):
        """Initialize email sender with configuration."""
        # Store config file path for resolving relative paths
        self.config_file = str(Path(config_file).resolve())
        self.config = self.load_config(config_file)
        self.history = self.load_history()
        self.today = str(date.today())
        self.failed_accounts = set()  # Track accounts that fail authentication
        self.stop_check = None  # Function to check if should stop
        self.progress_callback = None  # Callback for real-time progress updates
        self.history_lock = threading.Lock()  # Thread-safe history updates
        self.account_targets = {}  # Optional: per-account target counts (for auto-send)
        
    def load_config(self, config_file):
        """Load configuration from JSON."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception(f"Config file '{config_file}' not found!")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in config: {e}")
    
    def load_history(self):
        """Load sent email history."""
        history_file = self.config['paths']['sent_history']
        if Path(history_file).exists():
            try:
                with open(history_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "recipients": {},
            "daily_stats": {}
        }
    
    def save_history(self):
        """Save email history (thread-safe)."""
        with self.history_lock:
            history_file = self.config['paths']['sent_history']
            with open(history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
    
    def get_account_password(self, account):
        """Load account password from secure file."""
        password_file = account.get('app_password_file')
        if not password_file:
            raise Exception(f"No password file specified for account {account['id']}")
        
        # Resolve to absolute path if relative
        if not Path(password_file).is_absolute():
            # Assume relative to config file directory
            config_dir = Path(self.config_file).parent if hasattr(self, 'config_file') else Path.cwd()
            password_file = str(config_dir / password_file)
        
        try:
            with open(password_file, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise Exception(f"Password file not found: {password_file}")
    
    def set_stop_check(self, stop_check_func):
        """Set a function to check if sending should stop."""
        self.stop_check = stop_check_func
    
    def get_available_account(self):
        """Get an account that hasn't hit its daily limit. Skips accounts that have failed authentication."""
        if self.today not in self.history['daily_stats']:
            self.history['daily_stats'][self.today] = {}
        
        daily_stats = self.history['daily_stats'][self.today]
        
        for account in self.config['accounts']:
            if not account.get('enabled', True):
                continue
            
            if account.get('auth_method') != 'app_password':
                continue
            
            account_id = account['id']
            
            # Skip accounts that have failed authentication
            if account_id in self.failed_accounts:
                continue
            
            sent_today = daily_stats.get(account_id, 0)
            daily_limit = account.get('daily_limit', 10)
            
            if sent_today < daily_limit:
                return account, sent_today
        
        return None, None
    
    def validate_email(self, email):
        """Validate email format."""
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
        """Check if email was already sent. Returns False for whitelisted test emails."""
        email_lower = email.lower()
        
        # Check whitelist first - test emails can always be sent
        whitelist = self.config.get('test_whitelist', {}).get('emails', [])
        if email_lower in [e.lower() for e in whitelist]:
            return False  # Whitelisted emails can always be sent
        
        # Otherwise check normal history
        return email_lower in self.history['recipients']
    
    def send_email(self, account, recipient_email, recipient_name, paper_title="", publication_venue="arXiv"):
        """Send a single email using the specified account."""
        account_id = account['id']
        
        try:
            # Get password
            password = self.get_account_password(account)
            
            # Format email content (randomly select variant)
            subject, body = format_email(recipient_name, paper_title, publication_venue)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr((account['name'], account['email']))
            msg['To'] = recipient_email
            msg['Subject'] = subject  # Use dynamic subject from variant
            
            # Convert plain text to HTML (preserve line breaks and formatting)
            html_body = body.replace('\n', '<br>\n')
            # Wrap in simple HTML structure - natural full-width like normal emails
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
            
            # Send via SMTP
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(account['email'], password)
                server.send_message(msg)
            
            # Update history
            self.record_sent_email(recipient_email, recipient_name, paper_title, account)
            
            return True
            
        except FileNotFoundError as e:
            # Password file not found - mark account as failed and stop
            error_msg = f"Password file not found for account {account_id}: {e}"
            print(f"  ✗ {error_msg}")
            self.failed_accounts.add(account_id)
            raise Exception(error_msg)  # Raise to stop processing
        except smtplib.SMTPException as e:
            error_msg = str(e)
            
            # Check for rate limit or sending limit errors
            is_rate_limit = (
                'reached a limit for sending mail' in error_msg.lower() or
                'mail delivery subsystem' in error_msg.lower() or
                'daily sending quota' in error_msg.lower() or
                'quota exceeded' in error_msg.lower() or
                'rate limit' in error_msg.lower() or
                'too many requests' in error_msg.lower() or
                'sending limit' in error_msg.lower()
            )
            
            if is_rate_limit:
                error_msg_full = f"🚨 RATE LIMIT HIT for account {account_id}: {error_msg}"
                print(f"  ✗ {error_msg_full}")
                print(f"  ⚠️  Account {account_id} has reached its sending limit. Stopping this account immediately.")
                self.failed_accounts.add(account_id)
                # Raise to stop processing from this account
                raise Exception(f"Rate limit reached for {account_id}: {error_msg}")
            
            error_msg_full = f"SMTP error for account {account_id}: {error_msg}"
            print(f"  ✗ {error_msg_full}")
            return False
        except Exception as e:
            error_msg = str(e)
            
            # Check for rate limit errors in generic exceptions too
            is_rate_limit = (
                'reached a limit for sending mail' in error_msg.lower() or
                'mail delivery subsystem' in error_msg.lower() or
                'daily sending quota' in error_msg.lower() or
                'quota exceeded' in error_msg.lower() or
                'rate limit' in error_msg.lower() or
                'sending limit' in error_msg.lower()
            )
            
            if is_rate_limit:
                error_msg_full = f"🚨 RATE LIMIT HIT for account {account_id}: {error_msg}"
                print(f"  ✗ {error_msg_full}")
                print(f"  ⚠️  Account {account_id} has reached its sending limit. Stopping this account immediately.")
                self.failed_accounts.add(account_id)
                raise Exception(f"Rate limit reached for {account_id}: {error_msg}")
            
            error_msg_full = f"Error sending email for account {account_id}: {error_msg}"
            print(f"  ✗ {error_msg_full}")
            # If it's a path/credentials issue, mark as failed
            if "password" in error_msg.lower() or "file" in error_msg.lower() or "credentials" in error_msg.lower():
                self.failed_accounts.add(account_id)
                raise Exception(error_msg_full)  # Raise to stop processing
            return False
    
    def set_progress_callback(self, callback):
        """Set callback function for real-time progress updates (industry standard)."""
        self.progress_callback = callback
    
    def record_sent_email(self, email, name, paper_title, account):
        """Record successful email send in history (thread-safe)."""
        email_lower = email.lower()
        timestamp = datetime.now().isoformat()
        account_id = account['id']
        account_email = account['email']
        account_limit = account.get('daily_limit', 10)
        
        with self.history_lock:
            # Update recipient record
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
            
            # Update daily stats
            if self.today not in self.history['daily_stats']:
                self.history['daily_stats'][self.today] = {}
            
            if account_id not in self.history['daily_stats'][self.today]:
                self.history['daily_stats'][self.today][account_id] = 0
            
            self.history['daily_stats'][self.today][account_id] += 1
            
            # Calculate total for today
            self.history['daily_stats'][self.today]['total'] = sum(
                count for key, count in self.history['daily_stats'][self.today].items()
                if key != 'total'
            )
        
        # Industry standard: Call progress callback immediately after updating history
        # This updates in-memory state for real-time UI updates (no file I/O in status endpoint)
        if self.progress_callback:
            try:
                self.progress_callback(account_id, account_email, account_limit)
            except Exception as e:
                # Don't let callback errors break email sending
                print(f"⚠️  Progress callback error: {e}")
    
    def process_csv(self, csv_file, test_mode=False, max_emails=None):
        """Process CSV file and send emails."""
        if not Path(csv_file).exists():
            raise Exception(f"CSV file not found: {csv_file}")
        
        print(f"\n{'='*80}")
        print(f"EMAIL SENDER - {'TEST MODE' if test_mode else 'LIVE MODE'}")
        print(f"{'='*80}")
        print(f"CSV File: {csv_file}")
        print(f"Today: {self.today}")
        print(f"{'='*80}\n")
        
        # Read CSV
        recipients = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                recipients.append(row)
        
        print(f"Total recipients in CSV: {len(recipients)}")
        
        # Filter: skip already sent
        to_send = []
        skipped = 0
        blacklisted = 0
        for recipient in recipients:
            email = recipient.get('Email', '').strip()
            if not self.validate_email(email):
                continue
            if self.is_blacklisted(email):
                blacklisted += 1
                continue
            if self.is_already_sent(email):
                skipped += 1
                continue
            to_send.append(recipient)
        
        print(f"Blacklisted (skipped): {blacklisted}")
        print(f"Already sent: {skipped}")
        print(f"Ready to send: {len(to_send)}")
        
        if max_emails:
            to_send = to_send[:max_emails]
            print(f"Limited to: {max_emails}")
        
        if test_mode:
            print(f"\n⚠️  TEST MODE: Will only send to first recipient")
            to_send = to_send[:1]
        
        # Validate accounts before starting
        print("\n🔍 Validating accounts...")
        valid_accounts = []
        for account in self.config['accounts']:
            if not account.get('enabled', True):
                continue
            if account.get('auth_method') != 'app_password':
                continue
            
            account_id = account['id']
            try:
                # Try to get password to validate the account
                password = self.get_account_password(account)
                valid_accounts.append(account_id)
                print(f"  ✓ {account_id}: Valid")
            except Exception as e:
                error_msg = str(e)
                print(f"  ✗ {account_id}: FAILED - {error_msg}")
                self.failed_accounts.add(account_id)
        
        if not valid_accounts:
            error_msg = "❌ No valid SMTP accounts available! Please check password files."
            print(f"\n{error_msg}")
            raise Exception(error_msg)
        
        print(f"✅ {len(valid_accounts)} account(s) ready\n")
        
        # Parallel sending: Create a thread for each account
        recipient_queue = Queue()
        for recipient in to_send:
            recipient_queue.put(recipient)
        
        # Track stats across threads
        stats = {
            'sent': threading.Lock(),
            'failed': threading.Lock(),
            'sent_count': 0,
            'failed_count': 0,
            'account_stats': {}  # Per-account stats
        }
        
        # Get active accounts
        active_accounts = [acc for acc in self.config['accounts'] 
                          if acc.get('enabled', True) and 
                          acc.get('auth_method') == 'app_password' and
                          acc['id'] in valid_accounts]
        
        # Get max parallel accounts limit (default: 10, or number of accounts if less)
        max_parallel = self.config.get('sending', {}).get('max_parallel_accounts', 10)
        max_parallel = min(max_parallel, len(active_accounts))  # Can't exceed available accounts
        
        print(f"📊 Total enabled accounts: {len(active_accounts)}")
        print(f"🚀 Starting {max_parallel} parallel sending threads (limit: {max_parallel})...\n")
        
        def account_worker(account):
            """Worker thread for a single account - sends emails until queue empty or limit reached."""
            account_id = account['id']
            account_stats = {'sent': 0, 'failed': 0}
            stats['account_stats'][account_id] = account_stats
            
            recipient = None  # Track if we have a recipient in hand
            while True:
                # Check if should stop globally
                if self.stop_check and self.stop_check():
                    print(f"  [{account_id}] ⏹️  Stop requested")
                    if recipient:
                        recipient_queue.put(recipient)  # Put back recipient we were holding
                    break
                
                # Check account limit
                with self.history_lock:
                    daily_stats = self.history['daily_stats'].get(self.today, {})
                    sent_today = daily_stats.get(account_id, 0)
                    daily_limit = account.get('daily_limit', 10)
                
                # Check if we've reached daily limit
                if sent_today >= daily_limit:
                    print(f"  [{account_id}] ⏸️  Reached daily limit ({sent_today}/{daily_limit})")
                    if recipient:
                        recipient_queue.put(recipient)  # Put back recipient we were holding
                    break
                
                # Check if we've reached account-specific target (for auto-send)
                if account_id in self.account_targets:
                    target = self.account_targets[account_id]
                    if sent_today >= target:
                        print(f"  [{account_id}] ⏸️  Reached target ({sent_today}/{target})")
                        if recipient:
                            recipient_queue.put(recipient)  # Put back recipient we were holding
                        break
                
                # Check if account failed
                if account_id in self.failed_accounts:
                    print(f"  [{account_id}] ❌ Account failed, stopping")
                    if recipient:
                        recipient_queue.put(recipient)  # Put back recipient we were holding
                    break
                
                # Get next recipient (non-blocking)
                try:
                    recipient = recipient_queue.get(timeout=1)
                except:
                    # Queue empty or timeout - check if queue is actually empty
                    if recipient_queue.empty():
                        break  # No more recipients, exit thread
                    continue
                
                email = recipient.get('Email', '').strip()
                name = recipient.get('Author', recipient.get('Name', 'Colleague'))
                paper_title = recipient.get('Title', '')
                
                # Double-check: Has this email already been sent? (thread-safe check)
                # This prevents race conditions where multiple accounts might send to the same email
                with self.history_lock:
                    if self.is_already_sent(email):
                        print(f"  [{account_id}] ⏭️  Skipping {name} <{email}> (already sent by another account)")
                        recipient_queue.task_done()
                        recipient = None  # Clear recipient after skipping
                        continue
                
                print(f"  [{account_id}] Sending to {name} <{email}> ({sent_today}/{daily_limit})")
                
                try:
                    if self.send_email(account, email, name, paper_title):
                        account_stats['sent'] += 1
                        with stats['sent']:
                            stats['sent_count'] += 1
                        print(f"  [{account_id}] ✓ Sent")
                        self.save_history()
                        
                        # Delay before next email (per account)
                        delay_min = self.config['sending'].get('delay_min_seconds', 3)
                        delay_max = self.config['sending'].get('delay_max_seconds', 30)
                        delay = random.randint(delay_min, delay_max)
                        time.sleep(delay)
                    else:
                        account_stats['failed'] += 1
                        with stats['failed']:
                            stats['failed_count'] += 1
                        print(f"  [{account_id}] ✗ Failed to send")
                except Exception as e:
                    # Account-specific error - mark as failed but continue other accounts
                    error_msg = str(e)
                    
                    # Check if this is a rate limit error
                    is_rate_limit = 'rate limit reached' in error_msg.lower()
                    
                    print(f"  [{account_id}] ❌ Error: {error_msg}")
                    self.failed_accounts.add(account_id)
                    account_stats['failed'] += 1
                    with stats['failed']:
                        stats['failed_count'] += 1
                    
                    # For rate limit errors, don't put recipient back (account is done for today)
                    # For other critical errors (password, file), don't retry
                    # For non-critical errors, put recipient back for other accounts to try
                    if is_rate_limit or "password" in error_msg.lower() or "file" in error_msg.lower():
                        # Critical/rate limit error - we're done with this recipient, mark task as done
                        recipient_queue.task_done()
                    else:
                        # Non-critical error - put back for other accounts to try
                        recipient_queue.put(recipient)
                        # Don't call task_done() since we're putting it back
                    break  # Stop this account thread
                
                recipient_queue.task_done()
                recipient = None  # Clear recipient after processing
            
            print(f"  [{account_id}] Thread finished (sent: {account_stats['sent']}, failed: {account_stats['failed']})")
        
        # Start account threads with ThreadPoolExecutor to limit concurrent threads
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            # Submit all account workers
            futures = {executor.submit(account_worker, account): account['id'] 
                      for account in active_accounts}
            
            # Wait for all threads to complete
            for future in as_completed(futures):
                account_id = futures[future]
                try:
                    future.result()  # This will raise any exceptions that occurred
                except Exception as e:
                    print(f"  [{account_id}] ❌ Thread error: {e}")
        
        # Wait for all queue tasks to be processed
        recipient_queue.join()  # Wait for all tasks to be processed
        
        # Give threads a moment to finish
        time.sleep(1)
        
        sent_count = stats['sent_count']
        failed_count = stats['failed_count']
        
        # Final summary
        print(f"\n{'='*80}")
        print("PARALLEL SENDING COMPLETE")
        print(f"{'='*80}")
        print(f"Total Sent: {sent_count} | Total Failed: {failed_count}")
        print(f"\nPer-Account Stats:")
        for account_id, account_stats in stats['account_stats'].items():
            print(f"  {account_id}: {account_stats['sent']} sent, {account_stats['failed']} failed")
        if self.failed_accounts:
            print(f"\n⚠️  Failed accounts (stopped): {', '.join(self.failed_accounts)}")
        
        # Show daily stats
        if self.today in self.history['daily_stats']:
            print(f"\nToday's sending stats ({self.today}):")
            for account_id, count in self.history['daily_stats'][self.today].items():
                if account_id != 'total':
                    account = next((a for a in self.config['accounts'] if a['id'] == account_id), None)
                    if account:
                        print(f"  {account_id}: {count}/{account['daily_limit']} emails")
            print(f"  Total: {self.history['daily_stats'][self.today].get('total', 0)}")
        
        print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Send personalized emails using Gmail SMTP (app passwords)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test mode (send to 1 recipient)
  python send_emails_smtp.py --csv recipients.csv --test
  
  # Send 10 emails (will distribute across accounts)
  python send_emails_smtp.py --csv recipients.csv --max 10
  
  # Send all (up to daily limits)
  python send_emails_smtp.py --csv recipients.csv
        """
    )
    
    parser.add_argument('--csv', required=True, help='Path to CSV file with recipients')
    parser.add_argument('--config', default='config.json', help='Config file (default: config.json)')
    parser.add_argument('--test', action='store_true', help='Test mode (send to 1 recipient only)')
    parser.add_argument('--max', type=int, help='Maximum number of emails to send')
    
    args = parser.parse_args()
    
    try:
        sender = EmailSender(args.config)
        sender.process_csv(args.csv, test_mode=args.test, max_emails=args.max)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

