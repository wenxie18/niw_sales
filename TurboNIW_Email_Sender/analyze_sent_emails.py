#!/usr/bin/env python3
"""
Analyze Sent Emails - Categorize recipients into 3 groups:
1. Replied - They responded to our email
2. No Reply - We sent, but no response
3. Failed - Bounce/invalid address messages

This script analyzes emails sent from a specific account and checks the inbox
for replies and bounce messages to categorize each recipient.
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import base64
from collections import defaultdict

# Gmail API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False
    print("❌ Gmail API libraries not installed!")
    print("Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def load_config(config_file='config.json'):
    """Load configuration file."""
    with open(config_file, 'r') as f:
        return json.load(f)


def load_history(history_file='sent_history.json'):
    """Load sent email history."""
    if not Path(history_file).exists():
        return {"recipients": {}}
    
    with open(history_file, 'r') as f:
        return json.load(f)


def authenticate_account(account_id, config, config_file_path='config.json'):
    """Authenticate and get Gmail API service for an account."""
    print(f"\n{'='*80}")
    print(f"🔐 AUTHENTICATING ACCOUNT")
    print(f"   Account ID: {account_id}")
    print(f"{'='*80}")
    sys.stdout.flush()
    
    # Find account in config
    account = None
    for acc in config.get('accounts', []):
        if acc['id'] == account_id:
            account = acc
            break
    
    if not account:
        raise Exception(f"Account {account_id} not found in config.json")
    
    account_email = account.get('email', 'Unknown')
    print(f"   Email: {account_email}")
    sys.stdout.flush()
    
    credentials_file = account.get('credentials_file')
    if not credentials_file:
        raise Exception(f"No credentials file for account {account_id}")
    
    # Resolve paths
    config_dir = Path(config_file_path).parent if config_file_path else Path.cwd()
    if not Path(credentials_file).is_absolute():
        credentials_file = str(config_dir / credentials_file)
    
    token_file = str(config_dir / '.secrets' / f"{account_id}_token.json")
    
    creds = None
    
    # Load existing token
    if Path(token_file).exists():
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            print(f"   ✓ Loaded existing token")
            sys.stdout.flush()
        except Exception as e:
            print(f"   ⚠️  Could not load token: {e}")
            sys.stdout.flush()
            creds = None
    
    # Refresh or authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print(f"   ⟳ Refreshing token...")
            sys.stdout.flush()
            try:
                creds.refresh(Request())
                print(f"   ✓ Token refreshed")
                sys.stdout.flush()
            except Exception as e:
                print(f"   ⚠️  Token refresh failed: {e}")
                sys.stdout.flush()
                creds = None
        
        if not creds:
            print(f"\n   🌐 Opening browser for authentication...")
            print(f"   Please grant gmail.readonly permission")
            sys.stdout.flush()
            try:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
                print(f"\n   ✓ Authentication successful")
                sys.stdout.flush()
            except Exception as auth_error:
                error_msg = str(auth_error)
                print(f"\n   ❌ Authentication failed: {error_msg}")
                sys.stdout.flush()
                raise
    
    # Save token
    Path(token_file).parent.mkdir(exist_ok=True)
    with open(token_file, 'w') as token:
        token.write(creds.to_json())
    
    # Build service
    service = build('gmail', 'v1', credentials=creds)
    print(f"   ✓ Gmail API service ready")
    print(f"{'='*80}\n")
    sys.stdout.flush()
    
    return service, account_email


def get_message_body(message):
    """Extract text body from Gmail message."""
    try:
        payload = message.get('payload', {})
        body_text = ''
        
        # Check if message has parts
        parts = payload.get('parts', [])
        if parts:
            for part in parts:
                mime_type = part.get('mimeType', '')
                if mime_type == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
                elif mime_type == 'text/html':
                    # Fallback to HTML if no plain text
                    if not body_text:
                        data = part.get('body', {}).get('data', '')
                        if data:
                            body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            # Single part message
            data = payload.get('body', {}).get('data', '')
            if data:
                body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body_text
    except Exception as e:
        return ''


def classify_reply(reply):
    """Classify a reply message into: 'real_reply', 'auto_reply_ooo', 'auto_reply_invalid', or 'unknown'.
    
    Returns:
        tuple: (classification, is_valid_address)
        - 'real_reply': Actual human reply (Category 1)
        - 'auto_reply_ooo': Out-of-office auto-reply (Category 2 - valid address)
        - 'auto_reply_invalid': Mailbox deactivated/invalid (Category 3 - failed)
        - 'unknown': Can't determine
    """
    subject = reply.get('subject', '').lower()
    snippet = reply.get('snippet', '').lower()
    body = reply.get('body_preview', '').lower()
    combined = f"{subject} {snippet} {body}".lower()
    
    # Check for invalid/deactivated mailbox indicators
    invalid_indicators = [
        'mailbox is no longer active',
        'mailbox no longer active',
        'will soon be deactivated',
        'will be deactivated',
        'no longer be checking',
        'could not be delivered',
        'mailbox not found',
        'address not found',
        'unable to receive mail',
        'mailbox does not exist',
        'account has been disabled',
        'account disabled',
        'deactivated',
        'no longer active'
    ]
    
    # Check for out-of-office indicators
    ooo_indicators = [
        'out of office',
        'out of the office',
        'away from office',
        'will be traveling',
        'will respond when i return',
        'will respond as soon as i return',
        'currently away',
        'on vacation',
        'on leave',
        'automatic reply',
        'auto-reply',
        'auto reply'
    ]
    
    # Check for auto-reply subject patterns
    auto_reply_subjects = [
        'automatic reply',
        'auto-reply',
        'auto reply',
        'out of office',
        'away from office'
    ]
    
    # Check if it's an invalid mailbox
    if any(indicator in combined for indicator in invalid_indicators):
        return ('auto_reply_invalid', False)
    
    # Check if it's out-of-office (but valid address)
    if any(indicator in combined for indicator in ooo_indicators) or any(pattern in subject for pattern in auto_reply_subjects):
        return ('auto_reply_ooo', True)
    
    # If it has "Re:" and doesn't match auto-reply patterns, it's likely a real reply
    if subject.startswith('re:') or 're:' in subject:
        return ('real_reply', True)
    
    # Default: assume it's a real reply if we found it
    return ('real_reply', True)


def search_inbox_for_replies(service, recipient_email, sent_date, days_back=90):
    """Search inbox for replies from a specific recipient after sent_date."""
    # Search for messages from this recipient
    # Use sent_date to only look for replies after we sent
    sent_datetime = datetime.strptime(sent_date, '%Y-%m-%d')
    search_date = sent_datetime.strftime('%Y/%m/%d')
    
    query = f'from:{recipient_email} after:{search_date}'
    
    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=100
        ).execute()
        
        messages = results.get('messages', [])
        
        replies = []
        for msg in messages:
            try:
                message = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                
                headers = message['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
                date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
                from_addr = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
                
                # Check if subject contains "Re:" or "RE:" (reply indicator)
                is_reply = subject.lower().startswith('re:') or 're:' in subject.lower()
                
                # Get snippet and body
                snippet = message.get('snippet', '')
                body_text = get_message_body(message)
                
                # Classify the reply
                reply_data = {
                    'id': msg['id'],
                    'subject': subject,
                    'from': from_addr,
                    'date': date_str,
                    'snippet': snippet,
                    'body_preview': body_text[:500] if body_text else '',
                    'is_reply': is_reply
                }
                
                # Classify the reply type
                classification, is_valid = classify_reply(reply_data)
                reply_data['classification'] = classification
                reply_data['is_valid_address'] = is_valid
                
                replies.append(reply_data)
            except Exception as e:
                continue
        
        return replies
    except Exception as e:
        print(f"      ⚠️  Error searching for replies from {recipient_email}: {e}")
        return []


def search_inbox_for_bounces(service, recipient_email, sent_date, days_back=90):
    """Search inbox for bounce messages mentioning a specific recipient."""
    # Search for bounce messages from mailer-daemon
    sent_datetime = datetime.strptime(sent_date, '%Y-%m-%d')
    search_date = sent_datetime.strftime('%Y/%m/%d')
    
    # Search for bounce messages that might mention this recipient
    queries = [
        f'from:mailer-daemon@googlemail.com after:{search_date} "{recipient_email}"',
        f'from:mail-noreply@google.com after:{search_date} "{recipient_email}"',
        f'from:noreply@google.com after:{search_date} "{recipient_email}"',
        f'subject:"Delivery Status Notification" after:{search_date} "{recipient_email}"',
        f'subject:"Mail Delivery Subsystem" after:{search_date} "{recipient_email}"',
    ]
    
    all_bounces = []
    seen_ids = set()
    
    for query in queries:
        try:
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=50
            ).execute()
            
            messages = results.get('messages', [])
            
            for msg in messages:
                if msg['id'] in seen_ids:
                    continue
                seen_ids.add(msg['id'])
                
                try:
                    message = service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    headers = message['payload'].get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
                    date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
                    from_addr = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
                    
                    # Get body
                    body_text = get_message_body(message)
                    snippet = message.get('snippet', '')
                    
                    # Check if this bounce mentions our recipient
                    combined_text = f"{subject} {snippet} {body_text}".lower()
                    if recipient_email.lower() in combined_text:
                        all_bounces.append({
                            'id': msg['id'],
                            'subject': subject,
                            'from': from_addr,
                            'date': date_str,
                            'snippet': snippet,
                            'body_preview': body_text[:500] if body_text else '',
                            'recipient_mentioned': recipient_email
                        })
                except Exception as e:
                    continue
        except Exception as e:
            continue
    
    return all_bounces


def analyze_sent_emails(account_id, account_email, history, service, output_file, limit=None, json_output_dir=None):
    """Analyze all sent emails and categorize recipients."""
    print(f"\n{'='*80}")
    print(f"📊 ANALYZING SENT EMAILS")
    print(f"   Account: {account_email}")
    if limit:
        print(f"   ⚠️  TEST MODE: Limiting to {limit} recipients")
    print(f"{'='*80}\n")
    sys.stdout.flush()
    
    # Filter recipients sent from this account
    sent_recipients = []
    for email, data in history.get('recipients', {}).items():
        accounts_used = data.get('accounts_used', [])
        if account_email in accounts_used:
            sent_recipients.append({
                'email': email,
                'name': data.get('name', 'Unknown'),
                'paper_title': data.get('paper_title', ''),
                'first_sent': data.get('first_sent', ''),
                'last_sent': data.get('last_sent', ''),
                'send_count': data.get('send_count', 0)
            })
    
    # Apply limit if specified (for testing)
    original_count = len(sent_recipients)
    if limit and limit > 0:
        sent_recipients = sent_recipients[:limit]
        print(f"📧 Found {original_count} total recipients, analyzing {len(sent_recipients)} (limited for testing)\n")
    else:
        print(f"📧 Found {len(sent_recipients)} recipients sent from {account_email}\n")
    sys.stdout.flush()
    
    total = len(sent_recipients)  # Store for later use
    
    # Categorize recipients
    category_1_replied = []  # Replied
    category_2_no_reply = []  # No reply
    category_3_failed = []  # Failed/bounce
    
    processed = 0
    
    for recipient in sent_recipients:
        processed += 1
        email = recipient['email']
        name = recipient['name']
        sent_date = recipient['last_sent']
        
        print(f"[{processed}/{total}] Analyzing: {name} <{email}>")
        print(f"   Sent on: {sent_date}")
        sys.stdout.flush()
        
        # Check for replies
        replies = search_inbox_for_replies(service, email, sent_date)
        print(f"   Found {len(replies)} potential reply message(s)")
        sys.stdout.flush()
        
        # Check for bounces
        bounces = search_inbox_for_bounces(service, email, sent_date)
        print(f"   Found {len(bounces)} bounce message(s)")
        sys.stdout.flush()
        
        # Classify replies
        real_replies = []
        invalid_mailbox_replies = []
        ooo_replies = []
        
        for reply in replies:
            classification = reply.get('classification', 'unknown')
            if classification == 'real_reply':
                real_replies.append(reply)
            elif classification == 'auto_reply_invalid':
                invalid_mailbox_replies.append(reply)
            elif classification == 'auto_reply_ooo':
                ooo_replies.append(reply)
        
        # Categorize
        if bounces or invalid_mailbox_replies:
            # Category 3: Failed (has bounce message OR invalid mailbox auto-reply)
            category_3_failed.append({
                **recipient,
                'bounces': bounces,
                'invalid_mailbox_replies': invalid_mailbox_replies,
                'real_replies': real_replies  # Might have replied before mailbox was deactivated
            })
            print(f"   → Category 3: FAILED (bounce or invalid mailbox detected)")
        elif real_replies:
            # Category 1: Replied (has real human replies, no bounces)
            category_1_replied.append({
                **recipient,
                'replies': real_replies,
                'ooo_replies': ooo_replies  # Also track OOO if any
            })
            print(f"   → Category 1: REPLIED ({len(real_replies)} real reply/replies)")
        elif ooo_replies:
            # Category 2: No reply yet (has OOO auto-reply, but valid address)
            category_2_no_reply.append({
                **recipient,
                'ooo_replies': ooo_replies
            })
            print(f"   → Category 2: NO REPLY (out-of-office auto-reply found)")
        else:
            # Category 2: No reply (no replies, no bounces)
            category_2_no_reply.append(recipient)
            print(f"   → Category 2: NO REPLY")
        
        print()
        sys.stdout.flush()
    
    # Write analysis to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("SENT EMAIL ANALYSIS REPORT\n")
        f.write("="*80 + "\n\n")
        f.write(f"Account: {account_email}\n")
        f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Recipients Analyzed: {total}\n\n")
        
        f.write("="*80 + "\n")
        f.write("CATEGORY 1: REPLIED (They responded)\n")
        f.write("="*80 + "\n")
        f.write(f"Total: {len(category_1_replied)}\n\n")
        
        for recipient in category_1_replied:
            f.write(f"\n{'─'*80}\n")
            f.write(f"Name: {recipient['name']}\n")
            f.write(f"Email: {recipient['email']}\n")
            f.write(f"Paper Title: {recipient['paper_title']}\n")
            f.write(f"First Sent: {recipient['first_sent']}\n")
            f.write(f"Last Sent: {recipient['last_sent']}\n")
            f.write(f"Send Count: {recipient['send_count']}\n")
            f.write(f"\nReplies Found: {len(recipient['replies'])}\n")
            for i, reply in enumerate(recipient['replies'], 1):
                f.write(f"\n  Reply {i}:\n")
                f.write(f"    Subject: {reply['subject']}\n")
                f.write(f"    From: {reply['from']}\n")
                f.write(f"    Date: {reply['date']}\n")
                f.write(f"    Snippet: {reply['snippet'][:200]}...\n")
                if reply['body_preview']:
                    f.write(f"    Body Preview: {reply['body_preview'][:300]}...\n")
        
        f.write("\n\n" + "="*80 + "\n")
        f.write("CATEGORY 2: NO REPLY (No response yet)\n")
        f.write("="*80 + "\n")
        f.write(f"Total: {len(category_2_no_reply)}\n\n")
        
        for recipient in category_2_no_reply:
            f.write(f"\n{'─'*80}\n")
            f.write(f"Name: {recipient['name']}\n")
            f.write(f"Email: {recipient['email']}\n")
            f.write(f"Paper Title: {recipient['paper_title']}\n")
            f.write(f"First Sent: {recipient['first_sent']}\n")
            f.write(f"Last Sent: {recipient['last_sent']}\n")
            f.write(f"Send Count: {recipient['send_count']}\n")
        
        f.write("\n\n" + "="*80 + "\n")
        f.write("CATEGORY 3: FAILED (Bounce/Invalid address)\n")
        f.write("="*80 + "\n")
        f.write(f"Total: {len(category_3_failed)}\n\n")
        
        for recipient in category_3_failed:
            f.write(f"\n{'─'*80}\n")
            f.write(f"Name: {recipient['name']}\n")
            f.write(f"Email: {recipient['email']}\n")
            f.write(f"Paper Title: {recipient['paper_title']}\n")
            f.write(f"First Sent: {recipient['first_sent']}\n")
            f.write(f"Last Sent: {recipient['last_sent']}\n")
            f.write(f"Send Count: {recipient['send_count']}\n")
            f.write(f"\nBounce Messages Found: {len(recipient['bounces'])}\n")
            for i, bounce in enumerate(recipient['bounces'], 1):
                f.write(f"\n  Bounce {i}:\n")
                f.write(f"    Subject: {bounce['subject']}\n")
                f.write(f"    From: {bounce['from']}\n")
                f.write(f"    Date: {bounce['date']}\n")
                f.write(f"    Snippet: {bounce['snippet'][:200]}...\n")
                if bounce['body_preview']:
                    f.write(f"    Body Preview: {bounce['body_preview'][:500]}...\n")
    
    # Print summary
    # Save JSON files if output directory specified
    if json_output_dir:
        json_output_dir = Path(json_output_dir)
        json_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare JSON structures
        json_category_1 = {
            'account_id': account_id,
            'account_email': account_email,
            'analysis_date': datetime.now().isoformat(),
            'category': 'replied',
            'description': 'Recipients who replied to our emails',
            'total': len(category_1_replied),
            'recipients': []
        }
        
        json_category_2 = {
            'account_id': account_id,
            'account_email': account_email,
            'analysis_date': datetime.now().isoformat(),
            'category': 'no_reply',
            'description': 'Recipients who received emails but haven\'t replied yet',
            'total': len(category_2_no_reply),
            'recipients': []
        }
        
        json_category_3 = {
            'account_id': account_id,
            'account_email': account_email,
            'analysis_date': datetime.now().isoformat(),
            'category': 'failed',
            'description': 'Emails that bounced or failed due to invalid addresses',
            'total': len(category_3_failed),
            'recipients': []
        }
        
        # Populate Category 1 (Replied)
        for recipient in category_1_replied:
            json_category_1['recipients'].append({
                'email': recipient['email'],
                'name': recipient['name'],
                'paper_title': recipient['paper_title'],
                'first_sent': recipient['first_sent'],
                'last_sent': recipient['last_sent'],
                'send_count': recipient['send_count'],
                'reply_count': len(recipient.get('replies', [])),
                'replies': [
                    {
                        'subject': reply['subject'],
                        'from': reply['from'],
                        'date': reply['date'],
                        'snippet': reply['snippet'],
                        'body_preview': reply['body_preview'][:500] if reply['body_preview'] else '',
                        'classification': reply.get('classification', 'real_reply')
                    }
                    for reply in recipient.get('replies', [])
                ],
                'ooo_replies': [
                    {
                        'subject': reply['subject'],
                        'from': reply['from'],
                        'date': reply['date'],
                        'snippet': reply['snippet'],
                        'body_preview': reply['body_preview'][:500] if reply['body_preview'] else ''
                    }
                    for reply in recipient.get('ooo_replies', [])
                ]
            })
        
        # Populate Category 2 (No Reply)
        for recipient in category_2_no_reply:
            json_category_2['recipients'].append({
                'email': recipient['email'],
                'name': recipient['name'],
                'paper_title': recipient['paper_title'],
                'first_sent': recipient['first_sent'],
                'last_sent': recipient['last_sent'],
                'send_count': recipient['send_count'],
                'ooo_replies': [
                    {
                        'subject': reply['subject'],
                        'from': reply['from'],
                        'date': reply['date'],
                        'snippet': reply['snippet'],
                        'body_preview': reply['body_preview'][:500] if reply['body_preview'] else ''
                    }
                    for reply in recipient.get('ooo_replies', [])
                ] if 'ooo_replies' in recipient else []
            })
        
        # Populate Category 3 (Failed)
        for recipient in category_3_failed:
            json_category_3['recipients'].append({
                'email': recipient['email'],
                'name': recipient['name'],
                'paper_title': recipient['paper_title'],
                'first_sent': recipient['first_sent'],
                'last_sent': recipient['last_sent'],
                'send_count': recipient['send_count'],
                'bounce_count': len(recipient.get('bounces', [])),
                'bounces': [
                    {
                        'subject': bounce['subject'],
                        'from': bounce['from'],
                        'date': bounce['date'],
                        'snippet': bounce['snippet'],
                        'body_preview': bounce['body_preview'][:500] if bounce['body_preview'] else ''
                    }
                    for bounce in recipient.get('bounces', [])
                ],
                'invalid_mailbox_replies': [
                    {
                        'subject': reply['subject'],
                        'from': reply['from'],
                        'date': reply['date'],
                        'snippet': reply['snippet'],
                        'body_preview': reply['body_preview'][:500] if reply['body_preview'] else ''
                    }
                    for reply in recipient.get('invalid_mailbox_replies', [])
                ],
                'real_replies': [
                    {
                        'subject': reply['subject'],
                        'from': reply['from'],
                        'date': reply['date'],
                        'snippet': reply['snippet'],
                        'body_preview': reply['body_preview'][:500] if reply['body_preview'] else ''
                    }
                    for reply in recipient.get('real_replies', [])
                ]
            })
        
        # Save JSON files
        json_file_1 = json_output_dir / f'category_1_replied_{account_id}.json'
        json_file_2 = json_output_dir / f'category_2_no_reply_{account_id}.json'
        json_file_3 = json_output_dir / f'category_3_failed_{account_id}.json'
        
        with open(json_file_1, 'w', encoding='utf-8') as f:
            json.dump(json_category_1, f, indent=2, ensure_ascii=False)
        
        with open(json_file_2, 'w', encoding='utf-8') as f:
            json.dump(json_category_2, f, indent=2, ensure_ascii=False)
        
        with open(json_file_3, 'w', encoding='utf-8') as f:
            json.dump(json_category_3, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 JSON files saved:")
        print(f"   {json_file_1}")
        print(f"   {json_file_2}")
        print(f"   {json_file_3}")
        sys.stdout.flush()
    
    print(f"\n{'='*80}")
    print(f"📊 ANALYSIS COMPLETE")
    print(f"{'='*80}")
    print(f"Category 1 (Replied): {len(category_1_replied)}")
    print(f"Category 2 (No Reply): {len(category_2_no_reply)}")
    print(f"Category 3 (Failed): {len(category_3_failed)}")
    print(f"Total Analyzed: {total}")
    if limit:
        print(f"Total Available: {original_count} (limited to {limit} for testing)")
    print(f"\n📄 Detailed report saved to: {output_file}")
    print(f"{'='*80}\n")
    sys.stdout.flush()
    
    return {
        'category_1_replied': category_1_replied,
        'category_2_no_reply': category_2_no_reply,
        'category_3_failed': category_3_failed,
        'total_analyzed': total,
        'total_available': original_count if limit else total
    }


def main():
    parser = argparse.ArgumentParser(
        description='Analyze sent emails and categorize recipients into 3 groups'
    )
    parser.add_argument(
        '--account-id',
        type=str,
        default=None,
        help='Account ID from config.json (e.g., account3_gmail_api). Use --all-accounts to analyze all accounts.'
    )
    parser.add_argument(
        '--all-accounts',
        action='store_true',
        help='Analyze all Gmail API accounts and combine results into single JSON files'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.json',
        help='Config file path (default: config.json)'
    )
    parser.add_argument(
        '--history',
        type=str,
        default='sent_history.json',
        help='Sent history file path (default: sent_history.json)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='email_analysis_report.txt',
        help='Output analysis file (default: email_analysis_report.txt)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of recipients to analyze (for testing, e.g., --limit 100)'
    )
    parser.add_argument(
        '--json-dir',
        type=str,
        default='email_categories',
        help='Directory to save JSON category files (default: email_categories)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.all_accounts and not args.account_id:
        parser.error("Either --account-id or --all-accounts must be specified")
    
    # Load config and history
    print("📋 Loading configuration and history...")
    sys.stdout.flush()
    config = load_config(args.config)
    history = load_history(args.history)
    
    if args.all_accounts:
        # Analyze all Gmail API accounts
        print(f"\n{'='*80}")
        print(f"🔄 ANALYZING ALL GMAIL API ACCOUNTS")
        print(f"{'='*80}\n")
        sys.stdout.flush()
        
        # Find all Gmail API accounts (ignore enabled flag - analyze all)
        gmail_api_accounts = [
            acc for acc in config.get('accounts', [])
            if acc.get('auth_method') == 'gmail_api'
        ]
        
        if not gmail_api_accounts:
            print("❌ No Gmail API accounts found in config.json")
            sys.exit(1)
        
        print(f"Found {len(gmail_api_accounts)} Gmail API account(s) to analyze:\n")
        for acc in gmail_api_accounts:
            print(f"  - {acc['id']} ({acc.get('email', 'Unknown')})")
        print()
        sys.stdout.flush()
        
        # Accumulate results from all accounts
        all_category_1 = []
        all_category_2 = []
        all_category_3 = []
        total_analyzed = 0
        total_available = 0
        skipped_accounts = []  # Track accounts that failed
        
        # Create combined output file
        combined_output_file = args.output or 'email_analysis_all_accounts.txt'
        
        for i, account in enumerate(gmail_api_accounts, 1):
            account_id = account['id']
            account_email = account.get('email', 'Unknown')
            is_enabled = account.get('enabled', True)
            
            print(f"\n{'='*80}")
            print(f"📧 ACCOUNT {i}/{len(gmail_api_accounts)}: {account_id} ({account_email})")
            if not is_enabled:
                print(f"   ⚠️  Note: Account is disabled in config, but analyzing anyway")
            print(f"{'='*80}\n")
            sys.stdout.flush()
            
            try:
                # Authenticate
                service, _ = authenticate_account(account_id, config, args.config)
                
                # Analyze (no limit, use account-specific output)
                account_output = f"{combined_output_file}.{account_id}.txt"
                results = analyze_sent_emails(
                    account_id,
                    account_email,
                    history,
                    service,
                    account_output,
                    limit=args.limit,
                    json_output_dir=None  # Don't save individual account JSONs
                )
                
                # Accumulate results
                for recipient in results['category_1_replied']:
                    recipient['account_id'] = account_id
                    recipient['account_email'] = account_email
                    all_category_1.append(recipient)
                
                for recipient in results['category_2_no_reply']:
                    recipient['account_id'] = account_id
                    recipient['account_email'] = account_email
                    all_category_2.append(recipient)
                
                for recipient in results['category_3_failed']:
                    recipient['account_id'] = account_id
                    recipient['account_email'] = account_email
                    all_category_3.append(recipient)
                
                total_analyzed += results['total_analyzed']
                total_available += results['total_available']
                
                print(f"✅ Successfully analyzed account {account_id}")
                sys.stdout.flush()
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Error analyzing account {account_id} ({account_email}): {error_msg}")
                sys.stdout.flush()
                skipped_accounts.append({
                    'account_id': account_id,
                    'account_email': account_email,
                    'error': error_msg
                })
                continue
        
        # Save combined JSON files
        if args.json_dir:
            json_output_dir = Path(args.json_dir)
            json_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Prepare combined JSON structures
            json_category_1 = {
                'analysis_date': datetime.now().isoformat(),
                'category': 'replied',
                'description': 'Recipients who replied to our emails (from all accounts)',
                'total': len(all_category_1),
                'accounts_analyzed': len(gmail_api_accounts),
                'recipients': []
            }
            
            json_category_2 = {
                'analysis_date': datetime.now().isoformat(),
                'category': 'no_reply',
                'description': 'Recipients who received emails but haven\'t replied yet (from all accounts)',
                'total': len(all_category_2),
                'accounts_analyzed': len(gmail_api_accounts),
                'recipients': []
            }
            
            json_category_3 = {
                'analysis_date': datetime.now().isoformat(),
                'category': 'failed',
                'description': 'Emails that bounced or failed due to invalid addresses (from all accounts)',
                'total': len(all_category_3),
                'accounts_analyzed': len(gmail_api_accounts),
                'recipients': []
            }
            
            # Populate Category 1
            for recipient in all_category_1:
                json_category_1['recipients'].append({
                    'account_id': recipient.get('account_id'),
                    'account_email': recipient.get('account_email'),
                    'email': recipient['email'],
                    'name': recipient['name'],
                    'paper_title': recipient['paper_title'],
                    'first_sent': recipient['first_sent'],
                    'last_sent': recipient['last_sent'],
                    'send_count': recipient['send_count'],
                    'reply_count': len(recipient.get('replies', [])),
                    'replies': [
                        {
                            'subject': reply['subject'],
                            'from': reply['from'],
                            'date': reply['date'],
                            'snippet': reply['snippet'],
                            'body_preview': reply['body_preview'][:500] if reply['body_preview'] else '',
                            'classification': reply.get('classification', 'real_reply')
                        }
                        for reply in recipient.get('replies', [])
                    ],
                    'ooo_replies': [
                        {
                            'subject': reply['subject'],
                            'from': reply['from'],
                            'date': reply['date'],
                            'snippet': reply['snippet'],
                            'body_preview': reply['body_preview'][:500] if reply['body_preview'] else ''
                        }
                        for reply in recipient.get('ooo_replies', [])
                    ]
                })
            
            # Populate Category 2
            for recipient in all_category_2:
                json_category_2['recipients'].append({
                    'account_id': recipient.get('account_id'),
                    'account_email': recipient.get('account_email'),
                    'email': recipient['email'],
                    'name': recipient['name'],
                    'paper_title': recipient['paper_title'],
                    'first_sent': recipient['first_sent'],
                    'last_sent': recipient['last_sent'],
                    'send_count': recipient['send_count'],
                    'ooo_replies': [
                        {
                            'subject': reply['subject'],
                            'from': reply['from'],
                            'date': reply['date'],
                            'snippet': reply['snippet'],
                            'body_preview': reply['body_preview'][:500] if reply['body_preview'] else ''
                        }
                        for reply in recipient.get('ooo_replies', [])
                    ] if 'ooo_replies' in recipient else []
                })
            
            # Populate Category 3
            for recipient in all_category_3:
                json_category_3['recipients'].append({
                    'account_id': recipient.get('account_id'),
                    'account_email': recipient.get('account_email'),
                    'email': recipient['email'],
                    'name': recipient['name'],
                    'paper_title': recipient['paper_title'],
                    'first_sent': recipient['first_sent'],
                    'last_sent': recipient['last_sent'],
                    'send_count': recipient['send_count'],
                    'bounce_count': len(recipient.get('bounces', [])),
                    'bounces': [
                        {
                            'subject': bounce['subject'],
                            'from': bounce['from'],
                            'date': bounce['date'],
                            'snippet': bounce['snippet'],
                            'body_preview': bounce['body_preview'][:500] if bounce['body_preview'] else ''
                        }
                        for bounce in recipient.get('bounces', [])
                    ],
                    'invalid_mailbox_replies': [
                        {
                            'subject': reply['subject'],
                            'from': reply['from'],
                            'date': reply['date'],
                            'snippet': reply['snippet'],
                            'body_preview': reply['body_preview'][:500] if reply['body_preview'] else ''
                        }
                        for reply in recipient.get('invalid_mailbox_replies', [])
                    ],
                    'real_replies': [
                        {
                            'subject': reply['subject'],
                            'from': reply['from'],
                            'date': reply['date'],
                            'snippet': reply['snippet'],
                            'body_preview': reply['body_preview'][:500] if reply['body_preview'] else ''
                        }
                        for reply in recipient.get('real_replies', [])
                    ]
                })
            
            # Save combined JSON files
            json_file_1 = json_output_dir / 'category_1_replied_all_accounts.json'
            json_file_2 = json_output_dir / 'category_2_no_reply_all_accounts.json'
            json_file_3 = json_output_dir / 'category_3_failed_all_accounts.json'
            
            with open(json_file_1, 'w', encoding='utf-8') as f:
                json.dump(json_category_1, f, indent=2, ensure_ascii=False)
            
            with open(json_file_2, 'w', encoding='utf-8') as f:
                json.dump(json_category_2, f, indent=2, ensure_ascii=False)
            
            with open(json_file_3, 'w', encoding='utf-8') as f:
                json.dump(json_category_3, f, indent=2, ensure_ascii=False)
            
            print(f"\n{'='*80}")
            print(f"📊 COMBINED ANALYSIS COMPLETE")
            print(f"{'='*80}")
            print(f"Category 1 (Replied): {len(all_category_1)}")
            print(f"Category 2 (No Reply): {len(all_category_2)}")
            print(f"Category 3 (Failed): {len(all_category_3)}")
            print(f"Total Analyzed: {total_analyzed}")
            print(f"Total Available: {total_available}")
            print(f"Accounts Successfully Analyzed: {len(gmail_api_accounts) - len(skipped_accounts)}/{len(gmail_api_accounts)}")
            
            if skipped_accounts:
                print(f"\n⚠️  SKIPPED ACCOUNTS ({len(skipped_accounts)}):")
                for skipped in skipped_accounts:
                    print(f"   - {skipped['account_id']} ({skipped['account_email']})")
                    print(f"     Error: {skipped['error']}")
            
            print(f"\n📁 Combined JSON files saved:")
            print(f"   {json_file_1}")
            print(f"   {json_file_2}")
            print(f"   {json_file_3}")
            print(f"{'='*80}\n")
            sys.stdout.flush()
        
        print("✅ Analysis of all accounts complete!")
        sys.stdout.flush()
    
    else:
        # Single account analysis (original behavior)
        # Authenticate
        service, account_email = authenticate_account(args.account_id, config, args.config)
        
        # Analyze
        results = analyze_sent_emails(
            args.account_id,
            account_email,
            history,
            service,
            args.output,
            limit=args.limit,
            json_output_dir=args.json_dir
        )
        
        print("✅ Analysis complete!")
        sys.stdout.flush()


if __name__ == '__main__':
    main()

