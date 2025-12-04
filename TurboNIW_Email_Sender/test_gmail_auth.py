#!/usr/bin/env python3
"""
Test Gmail API Authentication
This script will open a browser window to authenticate each Gmail account.
"""

import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def authenticate_account(account_id, credentials_file):
    """Authenticate a single Gmail account."""
    print(f"\n{'='*80}")
    print(f"Authenticating: {account_id}")
    print(f"Credentials file: {credentials_file}")
    print(f"{'='*80}")
    
    token_file = f".secrets/{account_id}_token.json"
    creds = None
    
    # Load existing token
    if Path(token_file).exists():
        print(f"✓ Found existing token: {token_file}")
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("⟳ Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("🌐 Opening browser for authentication...")
            print("   Please sign in and allow access.")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save token
        print(f"💾 Saving token to: {token_file}")
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
    else:
        print("✓ Token is valid, no re-authentication needed")
    
    # Test the connection (we only have gmail.send scope, so we can't access profile)
    print("🔍 Verifying credentials...")
    if creds and creds.valid:
        print("✅ SUCCESS! Credentials are valid and ready to send emails")
        print(f"   Token saved to: {token_file}")
        print(f"   Scope: gmail.send (can send emails)")
        return True
    else:
        print("❌ Credentials are invalid")
        return False

def main():
    print("\n" + "="*80)
    print("GMAIL API AUTHENTICATION TEST")
    print("="*80)
    
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Find Gmail API accounts
    gmail_accounts = [acc for acc in config['accounts'] 
                      if acc.get('auth_method') == 'gmail_api' 
                      and acc.get('enabled', False)]
    
    if not gmail_accounts:
        print("\n❌ No Gmail API accounts found in config.json")
        print("   Make sure auth_method='gmail_api' and enabled=true")
        return
    
    print(f"\nFound {len(gmail_accounts)} Gmail API account(s) to authenticate:\n")
    
    for account in gmail_accounts:
        account_id = account['id']
        email = account.get('email', 'Unknown')
        credentials_file = account.get('credentials_file')
        
        print(f"  • {account_id} - {email}")
        
        if not credentials_file:
            print(f"    ❌ No credentials_file specified!")
            continue
        
        if not Path(credentials_file).exists():
            print(f"    ❌ Credentials file not found: {credentials_file}")
            continue
    
    print("\n" + "-"*80)
    input("\nPress ENTER to start authentication process...")
    
    # Authenticate each account
    success_count = 0
    for account in gmail_accounts:
        account_id = account['id']
        credentials_file = account.get('credentials_file')
        
        if not credentials_file or not Path(credentials_file).exists():
            continue
        
        try:
            if authenticate_account(account_id, credentials_file):
                success_count += 1
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            continue
    
    # Summary
    print("\n" + "="*80)
    print("AUTHENTICATION COMPLETE")
    print("="*80)
    print(f"✅ Successfully authenticated: {success_count}/{len(gmail_accounts)} accounts")
    
    if success_count == len(gmail_accounts):
        print("\n🎉 All accounts ready to send emails!")
        print("\nNext step:")
        print("  python send_emails_gmail_api.py --csv YOUR_FILE.csv --max 10")
    else:
        print("\n⚠️  Some accounts failed to authenticate. Please check the errors above.")

if __name__ == "__main__":
    main()

