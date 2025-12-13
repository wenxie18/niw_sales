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

# Gmail API scopes
# gmail.readonly: Read emails to check for bounce/rate limit messages
# gmail.send: Send emails
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']

def authenticate_account(account_id, credentials_file):
    """Authenticate a single Gmail account."""
    import sys
    sys.stdout.flush()
    
    print(f"\n{'='*80}")
    print(f"🔐 AUTHENTICATING ACCOUNT")
    print(f"{'='*80}")
    print(f"   Account ID: {account_id}")
    print(f"   Credentials file: {credentials_file}")
    print(f"{'='*80}\n")
    sys.stdout.flush()
    
    # Resolve paths to absolute
    credentials_path = Path(credentials_file).resolve()
    config_dir = credentials_path.parent
    
    # If credentials file is already in .secrets, use that directory
    # Otherwise, use .secrets in the parent directory
    if config_dir.name == '.secrets':
        # Already in .secrets folder, use it directly
        secrets_dir = config_dir
    else:
        # Not in .secrets, use .secrets in the same directory as credentials
        secrets_dir = config_dir / '.secrets'
    
    token_file = secrets_dir / f"{account_id}_token.json"
    
    # Ensure .secrets directory exists
    secrets_dir.mkdir(parents=True, exist_ok=True)
    
    creds = None
    needs_reauth = False
    
    # Load existing token
    if token_file.exists():
        print(f"✓ Found existing token: {token_file}")
        sys.stdout.flush()
        try:
            # Try loading with old scopes first (backward compatibility)
            old_scopes = ['https://www.googleapis.com/auth/gmail.send']
            creds = Credentials.from_authorized_user_file(str(token_file), old_scopes)
            
            # Check if token has all required scopes
            if creds and creds.valid:
                token_scopes = set(creds.scopes or [])
                required_scopes = set(SCOPES)
                if not required_scopes.issubset(token_scopes):
                    print(f"\n⚠️  Token missing required scopes (need gmail.readonly for bounce detection)")
                    print(f"   Token has: {token_scopes}")
                    print(f"   Required: {required_scopes}")
                    print(f"   Deleting old token to force re-authentication...")
                    sys.stdout.flush()
                    token_file.unlink()  # Delete old token
                    creds = None
                    needs_reauth = True
                else:
                    # Token has correct scopes, but need to reload with new scopes
                    creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
        except Exception as e:
            print(f"\n⚠️  Error loading token: {e}")
            print(f"   Will re-authenticate...")
            sys.stdout.flush()
            creds = None
            needs_reauth = True
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid or needs_reauth:
        if creds and creds.expired and creds.refresh_token and not needs_reauth:
            print(f"\n⟳ Refreshing expired token...")
            sys.stdout.flush()
            try:
                creds.refresh(Request())
                print(f"✓ Token refreshed successfully")
                sys.stdout.flush()
            except Exception as e:
                print(f"\n⚠️  Token refresh failed: {e}")
                print(f"   Will re-authenticate...")
                sys.stdout.flush()
                creds = None
        
        # If still no valid credentials, authenticate via browser
        if not creds or not creds.valid:
            print(f"\n{'='*80}")
            print(f"🌐 OPENING BROWSER FOR AUTHENTICATION")
            print(f"{'='*80}")
            print(f"   Please sign in and allow access.")
            print(f"   You will be asked to grant:")
            print(f"   - Send email on your behalf (gmail.send)")
            print(f"   - Read your email (gmail.readonly) - for bounce detection")
            print(f"\n   ⚠️  NOTE: If you see 'access_denied' or '403' error:")
            print(f"      The app needs to be verified by Google OR")
            print(f"      Your email needs to be added as a test user")
            print(f"      in Google Cloud Console > OAuth consent screen")
            print(f"{'='*80}\n")
            sys.stdout.flush()
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
                print(f"⏳ Waiting for browser authentication...")
                sys.stdout.flush()
                creds = flow.run_local_server(port=0)
                
                # Check if authentication was successful
                if not creds:
                    print(f"\n❌ Authentication was cancelled or failed")
                    sys.stdout.flush()
                    return False
                
                print(f"\n✓ Browser authentication completed")
                sys.stdout.flush()
            except Exception as e:
                error_msg = str(e)
                print(f"\n{'='*80}")
                print(f"❌ AUTHENTICATION ERROR")
                print(f"   Error: {error_msg}")
                if 'access_denied' in error_msg or '403' in error_msg:
                    print(f"\n   🔧 SOLUTION:")
                    print(f"   1. Go to Google Cloud Console")
                    print(f"   2. Select your project")
                    print(f"   3. Navigate to: APIs & Services > OAuth consent screen")
                    print(f"   4. Add your email as a TEST USER")
                    print(f"   5. Save and try again")
                    print(f"\n   See GMAIL_API_VERIFICATION.md for detailed instructions")
                print(f"{'='*80}\n")
                sys.stdout.flush()
                return False
        
        # Save token (only if we have valid credentials)
        if creds and creds.valid:
            print(f"\n💾 Saving token to: {token_file}")
            sys.stdout.flush()
            with open(str(token_file), 'w') as token:
                token.write(creds.to_json())
            print(f"✓ Token saved successfully")
            sys.stdout.flush()
        else:
            print("❌ No valid credentials to save")
            sys.stdout.flush()
            return False
    else:
        print(f"\n{'='*80}")
        print(f"✓ TOKEN ALREADY VALID")
        print(f"   Account: {account_id}")
        print(f"   Token file: {token_file}")
        print(f"   No re-authentication needed")
        print(f"{'='*80}\n")
        sys.stdout.flush()
        return True
    
    # Test the connection (we only have gmail.send scope, so we can't access profile)
    print(f"\n{'='*80}")
    print(f"🔍 VERIFYING CREDENTIALS")
    print(f"{'='*80}")
    sys.stdout.flush()
    
    if creds and creds.valid:
        print(f"\n{'='*80}")
        print(f"✅ AUTHENTICATION COMPLETED SUCCESSFULLY")
        print(f"{'='*80}")
        print(f"   Account: {account_id}")
        print(f"   Token saved to: {token_file}")
        print(f"   Scopes: gmail.send (send emails), gmail.readonly (check for bounce messages)")
        print(f"   Status: Ready to send emails")
        print(f"{'='*80}\n")
        sys.stdout.flush()
        return True
    else:
        print(f"\n{'='*80}")
        print(f"❌ CREDENTIALS ARE INVALID")
        print(f"   Account: {account_id}")
        print(f"{'='*80}\n")
        sys.stdout.flush()
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

