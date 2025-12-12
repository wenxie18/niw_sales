#!/usr/bin/env python3
"""
Test script to read Gmail inbox and detect bounce/block messages.

This script tests:
1. Can we read the inbox?
2. Can we find "Message blocked" messages?
3. Can we find "You have reached a limit for sending mail" messages?
4. Can we filter by time window (e.g., last 24 hours)?

Usage:
    python3.9 test_read_inbox_bounces.py --account-id 16api
    python3.9 test_read_inbox_bounces.py --account-id 16api --hours 24
"""

import json
import argparse
import base64
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Gmail API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_API_AVAILABLE = True
except ImportError:
    print("❌ Gmail API libraries not installed!")
    print("   Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']


def load_config(config_file='config.json'):
    """Load configuration."""
    with open(config_file, 'r') as f:
        return json.load(f)


def authenticate_account(account_id, config):
    """Authenticate and get Gmail API service for an account."""
    account = next((acc for acc in config['accounts'] if acc['id'] == account_id), None)
    if not account:
        raise Exception(f"Account {account_id} not found in config")
    
    account_email = account.get('email', 'Unknown')
    print(f"\n{'='*80}")
    print(f"🔐 AUTHENTICATING ACCOUNT")
    print(f"   Account ID: {account_id}")
    print(f"   Email: {account_email}")
    print(f"{'='*80}")
    sys.stdout.flush()
    
    credentials_file = account.get('credentials_file')
    if not credentials_file:
        raise Exception(f"No credentials file for account {account_id}")
    
    # Resolve to absolute path if relative
    BASE_DIR = Path(__file__).parent
    if not Path(credentials_file).is_absolute():
        credentials_file = str(BASE_DIR / credentials_file)
    
    # Token file path
    token_file = str(BASE_DIR / '.secrets' / f"{account_id}_token.json")
    
    creds = None
    
    # Load existing token
    if Path(token_file).exists():
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            if creds and creds.valid:
                print(f"   ✓ Using existing token")
                sys.stdout.flush()
        except Exception as e:
            print(f"   ⚠️  Error loading token: {e}")
            sys.stdout.flush()
            creds = None
    
    # If no valid credentials, authenticate
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
            print(f"   Please grant both gmail.send and gmail.readonly permissions")
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
    body_text = ''
    payload = message.get('payload', {})
    
    # Check if message has parts
    parts = payload.get('parts', [])
    if parts:
        for part in parts:
            mime_type = part.get('mimeType', '')
            if mime_type == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    try:
                        body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
                    except:
                        pass
            elif mime_type == 'text/html':
                # Fallback to HTML if plain text not available
                data = part.get('body', {}).get('data', '')
                if data and not body_text:
                    try:
                        body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    except:
                        pass
    else:
        # Single part message
        mime_type = payload.get('mimeType', '')
        if mime_type == 'text/plain':
            data = payload.get('body', {}).get('data', '')
            if data:
                try:
                    body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                except:
                    pass
    
    return body_text


def search_bounce_messages(service, hours=24):
    """Search for bounce/block messages in inbox."""
    print(f"\n{'='*80}")
    print(f"🔍 SEARCHING FOR BOUNCE/BLOCK MESSAGES")
    print(f"{'='*80}")
    print(f"   Time window: Last {hours} hours")
    print(f"{'='*80}\n")
    sys.stdout.flush()
    
    # Build search query
    # Search for messages from mailer-daemon or Google Mail
    queries = [
        'from:mailer-daemon@googlemail.com',
        'from:noreply@google.com',
        'from:mail-noreply@google.com',
        'subject:"Message blocked"',
        'subject:"Delivery Status Notification"',
        'subject:"Mail Delivery Subsystem"',
    ]
    
    # Add time filter
    if hours <= 24:
        time_query = f'newer_than:{hours}h'
    else:
        days = hours // 24
        time_query = f'newer_than:{days}d'
    
    all_messages = []
    
    for query in queries:
        full_query = f'{query} {time_query}'
        print(f"   Searching: {full_query}")
        sys.stdout.flush()
        
        try:
            results = service.users().messages().list(
                userId='me',
                q=full_query,
                maxResults=50
            ).execute()
            
            messages = results.get('messages', [])
            print(f"      Found: {len(messages)} messages")
            sys.stdout.flush()
            
            for msg in messages:
                if msg['id'] not in [m['id'] for m in all_messages]:
                    all_messages.append(msg)
        except Exception as e:
            print(f"      ⚠️  Error: {e}")
            sys.stdout.flush()
    
    print(f"\n   Total unique messages found: {len(all_messages)}\n")
    sys.stdout.flush()
    
    return all_messages


def analyze_message(service, msg_id):
    """Get full message details and analyze for bounce/block indicators."""
    try:
        message = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()
        
        # Get headers
        headers = message['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        from_addr = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
        date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
        
        # Get body
        body_text = get_message_body(message)
        snippet = message.get('snippet', '')
        
        # Combine all text for pattern matching
        combined_text = f"{subject} {snippet} {body_text}".lower()
        
        # Check for bounce/block indicators
        indicators = {
            'message_blocked': any(phrase in combined_text for phrase in [
                'message blocked',
                'message was blocked',
                'blocked. see technical details',
            ]),
            'rate_limit': any(phrase in combined_text for phrase in [
                'reached a limit for sending mail',
                'limit for sending mail',
                'you have reached a limit',
                'sending limit',
                'daily sending quota',
                'quota exceeded',
            ]),
            'delivery_failed': any(phrase in combined_text for phrase in [
                'delivery status notification',
                'mail delivery subsystem',
                'message was not sent',
                'delivery failed',
            ]),
        }
        
        return {
            'id': msg_id,
            'subject': subject,
            'from': from_addr,
            'date': date_str,
            'snippet': snippet[:200],
            'body_preview': body_text[:500] if body_text else '',
            'indicators': indicators,
            'is_bounce': any(indicators.values())
        }
    except Exception as e:
        print(f"      ⚠️  Error reading message {msg_id}: {e}")
        sys.stdout.flush()
        return None


def main():
    parser = argparse.ArgumentParser(description='Test Gmail inbox reading for bounce/block messages')
    parser.add_argument('--account-id', type=str, required=True,
                       help='Account ID from config.json (e.g., 16api)')
    parser.add_argument('--hours', type=int, default=24,
                       help='Time window in hours to search (default: 24)')
    parser.add_argument('--config', type=str, default='config.json',
                       help='Config file path (default: config.json)')
    
    args = parser.parse_args()
    
    try:
        # Load config
        print(f"📋 Loading config from {args.config}...")
        sys.stdout.flush()
        config = load_config(args.config)
        
        # Authenticate
        service, account_email = authenticate_account(args.account_id, config)
        
        # Search for bounce messages
        messages = search_bounce_messages(service, args.hours)
        
        if not messages:
            print(f"\n{'='*80}")
            print(f"✅ NO BOUNCE MESSAGES FOUND")
            print(f"{'='*80}")
            print(f"   Searched last {args.hours} hours")
            print(f"   Account: {account_email}")
            print(f"{'='*80}\n")
            return
        
        # Analyze each message
        print(f"\n{'='*80}")
        print(f"📧 ANALYZING MESSAGES")
        print(f"{'='*80}\n")
        sys.stdout.flush()
        
        bounce_messages = []
        for i, msg in enumerate(messages, 1):
            print(f"   [{i}/{len(messages)}] Analyzing message {msg['id'][:20]}...")
            sys.stdout.flush()
            analysis = analyze_message(service, msg['id'])
            if analysis and analysis['is_bounce']:
                bounce_messages.append(analysis)
        
        # Print results
        print(f"\n{'='*80}")
        print(f"📊 RESULTS")
        print(f"{'='*80}")
        print(f"   Total messages found: {len(messages)}")
        print(f"   Bounce/block messages: {len(bounce_messages)}")
        print(f"{'='*80}\n")
        
        if bounce_messages:
            print(f"\n{'='*80}")
            print(f"🚨 BOUNCE/BLOCK MESSAGES DETECTED")
            print(f"{'='*80}\n")
            
            for i, msg in enumerate(bounce_messages, 1):
                print(f"   [{i}] Message ID: {msg['id']}")
                print(f"       Subject: {msg['subject']}")
                print(f"       From: {msg['from']}")
                print(f"       Date: {msg['date']}")
                print(f"       Indicators:")
                for indicator, found in msg['indicators'].items():
                    status = "✅" if found else "❌"
                    print(f"         {status} {indicator}: {found}")
                print(f"       Snippet: {msg['snippet']}")
                if msg['body_preview']:
                    print(f"       Body preview: {msg['body_preview'][:200]}...")
                print()
        else:
            print(f"\n✅ No bounce/block messages detected in the analyzed messages.")
            print(f"   (Messages found but don't match bounce/block patterns)")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

