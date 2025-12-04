#!/usr/bin/env python3
"""
Flask Web App for TurboNIW Email Sender
Provides UI for managing accounts, authentication, and sending emails.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import json
import os
from pathlib import Path
from datetime import datetime, date
import threading
import time
import random
from werkzeug.utils import secure_filename

# Import existing email sender classes
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from send_emails_smtp import EmailSender
from send_emails_gmail_api import GmailAPISender

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Change this in production!

# Paths
BASE_DIR = Path(__file__).parent.parent
CONFIG_FILE = BASE_DIR / 'config.json'
HISTORY_FILE = BASE_DIR / 'sent_history.json'
SECRETS_DIR = BASE_DIR / '.secrets'

# Global state
sending_active = False
sending_thread = None
sending_progress = {
    "sent": 0,
    "failed": 0,
    "total": 0,
    "current_name": "",
    "current_email": ""
}


def load_config():
    """Load configuration from JSON."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        "accounts": [],
        "email": {"_note": "Subject lines are dynamically generated"},
        "sending": {
            "delay_min_seconds": 10,
            "delay_max_seconds": 60,
            "max_retries": 2
        },
        "paths": {"sent_history": "sent_history.json"},
        "test_whitelist": {"emails": []},
        "blacklist": {"emails": []}
    }


def save_config(config):
    """Save configuration to JSON."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


@app.route('/')
def dashboard():
    """Main dashboard."""
    config = load_config()
    history = load_history()
    today = str(date.today())
    
    # Calculate stats
    total_accounts = len(config.get('accounts', []))
    enabled_accounts = sum(1 for acc in config.get('accounts', []) if acc.get('enabled', True))
    
    # Today's stats
    daily_stats = history.get('daily_stats', {}).get(today, {})
    # Sum only account-specific values, exclude 'total' key to avoid double-counting
    total_sent_today = sum(v for k, v in daily_stats.items() if k != 'total')
    
    # Account breakdown
    account_stats = []
    for account in config.get('accounts', []):
        if account.get('enabled', True):
            account_id = account['id']
            sent_today = daily_stats.get(account_id, 0)
            daily_limit = account.get('daily_limit', 0)
            account_stats.append({
                'id': account_id,
                'email': account['email'],
                'method': account.get('auth_method', 'app_password'),
                'sent_today': sent_today,
                'daily_limit': daily_limit,
                'remaining': max(0, daily_limit - sent_today)
            })
    
    return render_template('dashboard.html',
                         total_accounts=total_accounts,
                         enabled_accounts=enabled_accounts,
                         total_sent_today=total_sent_today,
                         account_stats=account_stats,
                         sending_active=sending_active)


def load_history():
    """Load sent email history."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"recipients": {}, "daily_stats": {}}


@app.route('/accounts')
def accounts():
    """Account management page."""
    config = load_config()
    return render_template('accounts.html', accounts=config.get('accounts', []))


@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    """Get all accounts."""
    config = load_config()
    return jsonify(config.get('accounts', []))


@app.route('/api/accounts', methods=['POST'])
def add_account():
    """Add a new account."""
    # Check if this is a file upload (FormData) or JSON
    if request.content_type and 'multipart/form-data' in request.content_type:
        # Handle file upload
        account_id = request.form.get('id')
        email = request.form.get('email')
        name = request.form.get('name', 'Wen')
        auth_method = request.form.get('auth_method', 'app_password')
        daily_limit = int(request.form.get('daily_limit', 10))
        
        config = load_config()
        
        # Create new account
        account = {
            "id": account_id,
            "email": email,
            "name": name,
            "auth_method": auth_method,
            "daily_limit": daily_limit,
            "enabled": True
        }
        
        if auth_method == 'app_password':
            account['app_password_file'] = f".secrets/{account_id}_password.txt"
            # Create password file if provided
            password = request.form.get('password')
            if password:
                SECRETS_DIR.mkdir(exist_ok=True)
                password_file = SECRETS_DIR / f"{account_id}_password.txt"
                with open(password_file, 'w') as f:
                    f.write(password)
        elif auth_method == 'gmail_api':
            # Handle credentials file upload
            if 'credentials_file' not in request.files:
                return jsonify({"success": False, "error": "Credentials file is required for Gmail API"}), 400
            
            credentials_file = request.files['credentials_file']
            if credentials_file.filename == '':
                return jsonify({"success": False, "error": "No file selected"}), 400
            
            if not credentials_file.filename.endswith('.json'):
                return jsonify({"success": False, "error": "Credentials file must be a JSON file"}), 400
            
            # Save credentials file with standardized name
            SECRETS_DIR.mkdir(exist_ok=True)
            credentials_path = SECRETS_DIR / f"gmail_credentials_{account_id}.json"
            credentials_file.save(str(credentials_path))
            
            account['credentials_file'] = f".secrets/gmail_credentials_{account_id}.json"
        
        config['accounts'].append(account)
        save_config(config)
        
        return jsonify({"success": True, "account": account})
    else:
        # Handle JSON request (backward compatibility)
        data = request.json
        config = load_config()
        
        # Create new account
        account = {
            "id": data.get('id'),
            "email": data.get('email'),
            "name": data.get('name', 'Wen'),
            "auth_method": data.get('auth_method', 'app_password'),
            "daily_limit": int(data.get('daily_limit', 10)),
            "enabled": data.get('enabled', True)
        }
        
        if account['auth_method'] == 'app_password':
            account['app_password_file'] = f".secrets/{account['id']}_password.txt"
            # Create password file if provided
            if data.get('password'):
                SECRETS_DIR.mkdir(exist_ok=True)
                password_file = SECRETS_DIR / f"{account['id']}_password.txt"
                with open(password_file, 'w') as f:
                    f.write(data['password'])
        elif account['auth_method'] == 'gmail_api':
            account['credentials_file'] = f".secrets/gmail_credentials_{account['id']}.json"
            # Note: User needs to upload credentials file separately
        
        config['accounts'].append(account)
        save_config(config)
        
        return jsonify({"success": True, "account": account})


@app.route('/api/accounts/<account_id>', methods=['PUT'])
def update_account(account_id):
    """Update an account."""
    data = request.json
    config = load_config()
    
    for i, account in enumerate(config['accounts']):
        if account['id'] == account_id:
            # Update fields
            if 'email' in data:
                account['email'] = data['email']
            if 'name' in data:
                account['name'] = data['name']
            if 'daily_limit' in data:
                account['daily_limit'] = int(data['daily_limit'])
            if 'enabled' in data:
                account['enabled'] = data['enabled']
            if 'password' in data and account.get('auth_method') == 'app_password':
                # Update password file
                password_file = SECRETS_DIR / f"{account_id}_password.txt"
                SECRETS_DIR.mkdir(exist_ok=True)
                with open(password_file, 'w') as f:
                    f.write(data['password'])
            
            save_config(config)
            return jsonify({"success": True, "account": account})
    
    return jsonify({"success": False, "error": "Account not found"}), 404


@app.route('/api/accounts/<account_id>', methods=['DELETE'])
def delete_account(account_id):
    """Delete an account."""
    config = load_config()
    config['accounts'] = [acc for acc in config['accounts'] if acc['id'] != account_id]
    save_config(config)
    return jsonify({"success": True})


@app.route('/api/accounts/<account_id>/authenticate', methods=['POST'])
def authenticate_account(account_id):
    """Authenticate a Gmail API account."""
    config = load_config()
    account = next((acc for acc in config['accounts'] if acc['id'] == account_id), None)
    
    if not account:
        return jsonify({"success": False, "error": "Account not found"}), 404
    
    if account.get('auth_method') != 'gmail_api':
        return jsonify({"success": False, "error": "Only Gmail API accounts can be authenticated"}), 400
    
    # Import authentication function
    import sys
    sys.path.append(str(BASE_DIR))
    from test_gmail_auth import authenticate_account as auth_func
    
    credentials_file = BASE_DIR / account['credentials_file']
    if not credentials_file.exists():
        return jsonify({"success": False, "error": "Credentials file not found"}), 400
    
    try:
        # Run authentication (this will open browser)
        success = auth_func(account_id, str(credentials_file))
        if success:
            return jsonify({"success": True, "message": "Authentication successful"})
        else:
            return jsonify({"success": False, "error": "Authentication failed"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/settings')
def settings():
    """Settings page."""
    config = load_config()
    return render_template('settings.html', config=config)


@app.route('/api/settings', methods=['PUT'])
def update_settings():
    """Update settings."""
    data = request.json
    config = load_config()
    
    if 'sending' in data:
        config['sending'].update(data['sending'])
    if 'test_whitelist' in data:
        config['test_whitelist'] = data['test_whitelist']
    if 'blacklist' in data:
        config['blacklist'] = data['blacklist']
    
    save_config(config)
    return jsonify({"success": True})


@app.route('/send')
def send_page():
    """Email sending page."""
    # Get default CSV path from config or use standard path
    default_csv = None
    config = load_config()
    
    # Try to find default CSV in common locations
    possible_paths = [
        BASE_DIR.parent / 'data' / 'arxiv' / 'round1' / 'arxiv_high_confidence_non_chinese_no_acl.csv',
        BASE_DIR.parent / 'data' / 'arxiv' / 'round1' / 'arxiv_high_confidence_non_chinese.csv',
        BASE_DIR.parent / 'data' / 'arxiv' / 'round1' / 'arxiv_high_confidence.csv',
    ]
    
    for path in possible_paths:
        if path.exists():
            default_csv = str(path.relative_to(BASE_DIR.parent))
            break
    
    return render_template('send.html', default_csv=default_csv)


@app.route('/api/send/load-default-csv', methods=['GET'])
def load_default_csv():
    """Load default CSV file."""
    import csv
    
    csv_path = request.args.get('path')
    if not csv_path:
        return jsonify({"success": False, "error": "No path provided"}), 400
    
    # Resolve path relative to project root
    full_path = BASE_DIR.parent / csv_path
    
    if not full_path.exists():
        return jsonify({"success": False, "error": f"File not found: {csv_path}"}), 404
    
    try:
        data = []
        with open(full_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        
        return jsonify({"success": True, "data": data, "count": len(data)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# Removed queue system - now uses process_csv() directly like command-line


@app.route('/api/send/start', methods=['POST'])
def start_sending():
    """Start sending emails - processes CSV and sends directly like command-line."""
    global sending_active, sending_thread
    
    if sending_active:
        return jsonify({"success": False, "error": "Sending already in progress"}), 400
    
    # Get parameters
    data = request.json or {}
    csv_path = data.get('csv_path')
    max_emails = int(data.get('max_emails', 0))
    
    # If no CSV path provided, use default
    if not csv_path:
        # Try to find default CSV
        possible_paths = [
            BASE_DIR.parent / 'data' / 'arxiv' / 'round1' / 'arxiv_high_confidence_non_chinese_no_acl.csv',
            BASE_DIR.parent / 'data' / 'arxiv' / 'round1' / 'arxiv_high_confidence_non_chinese.csv',
        ]
        for path in possible_paths:
            if path.exists():
                csv_path = str(path.relative_to(BASE_DIR.parent))
                break
    
    if not csv_path:
        return jsonify({"success": False, "error": "No CSV file specified and no default file found"}), 400
    
    sending_active = True
    sending_thread = threading.Thread(target=send_emails_worker_direct, args=(csv_path, max_emails), daemon=True)
    sending_thread.start()
    
    return jsonify({"success": True, "message": "Sending started"})


@app.route('/api/send/stop', methods=['POST'])
def stop_sending():
    """Stop sending emails."""
    global sending_active, sending_progress
    sending_active = False
    sending_progress = {
        "sent": sending_progress.get("sent", 0),
        "failed": sending_progress.get("failed", 0),
        "total": sending_progress.get("total", 0),
        "current_name": "",
        "current_email": "",
        "stopped": True
    }
    return jsonify({"success": True})


@app.route('/api/send/status', methods=['GET'])
def send_status():
    """Get sending status and progress."""
    # Check if sending is active by checking if thread is alive
    thread_alive = sending_thread and sending_thread.is_alive() if sending_thread else False
    is_active = sending_active or thread_alive
    
    # Always read from history file (source of truth) - like command-line
    try:
        history = load_history()
        today = str(date.today())
        if today in history.get('daily_stats', {}):
            daily_stats = history['daily_stats'][today]
            # Sum up sent emails today (excluding 'total' key)
            total_sent_today = sum(
                count for key, count in daily_stats.items() 
                if key != 'total'
            )
            # Always update from history (source of truth)
            sending_progress["sent"] = total_sent_today
    except:
        pass
    
    return jsonify({
        "active": is_active,
        "progress": sending_progress.copy()
    })


def send_emails_worker_direct(csv_path, max_emails=0):
    """Background worker that processes CSV and sends directly (exactly like command-line)."""
    global sending_active, sending_progress
    
    # Initialize progress - start from current sent count in history (like command-line)
    initial_sent = 0
    try:
        history = load_history()
        today = str(date.today())
        if today in history.get('daily_stats', {}):
            daily_stats = history['daily_stats'][today]
            # Sum up sent emails today (excluding 'total' key)
            initial_sent = sum(
                count for key, count in daily_stats.items() 
                if key != 'total'
            )
    except:
        pass
    
    sending_progress = {
        "sent": initial_sent,  # Start from current count in history
        "failed": 0,
        "total": 0,
        "current_name": "",
        "current_email": ""
    }
    
    try:
        # Change to BASE_DIR to ensure relative paths work correctly
        original_cwd = os.getcwd()
        os.chdir(str(BASE_DIR))
        
        try:
            # Determine which sender to use based on available accounts
            # Prefer Gmail API if available, otherwise use SMTP
            config = load_config()
            has_gmail_api = any(acc.get('auth_method') == 'gmail_api' and acc.get('enabled', True) 
                               for acc in config.get('accounts', []))
            has_smtp = any(acc.get('auth_method') == 'app_password' and acc.get('enabled', True) 
                          for acc in config.get('accounts', []))
            
            # Use the same logic as command-line scripts
            sender = None
            if has_gmail_api:
                try:
                    sender = GmailAPISender(str(CONFIG_FILE))
                except Exception as e:
                    print(f"⚠️  Gmail API initialization failed: {e}")
                    if has_smtp:
                        print("   Falling back to SMTP...")
                        sender = EmailSender(str(CONFIG_FILE))
                    else:
                        raise Exception("No valid accounts available")
            elif has_smtp:
                sender = EmailSender(str(CONFIG_FILE))
            else:
                raise Exception("❌ No enabled accounts found")
            
            # Process CSV directly (same as command-line - no queue needed!)
            full_path = BASE_DIR.parent / csv_path
            if not full_path.exists():
                raise Exception(f"❌ CSV file not found: {csv_path}")
            
            # Calculate total daily limit from all enabled accounts (this is the real limit)
            total_daily_limit = 0
            for account in config.get('accounts', []):
                if account.get('enabled', True):
                    if account.get('auth_method') == 'gmail_api' or account.get('auth_method') == 'app_password':
                        daily_limit = account.get('daily_limit', 0)
                        total_daily_limit += daily_limit
            
            # Count total recipients in CSV (for reference)
            import csv as csv_module
            with open(full_path, 'r', encoding='utf-8') as f:
                reader = csv_module.DictReader(f)
                total_recipients = sum(1 for _ in reader)
            
            # Total progress is based on daily limit, not CSV rows
            # We can't send more than our daily limit anyway
            if max_emails > 0:
                # If max_emails is set, use the minimum of max_emails and daily limit
                sending_progress["total"] = min(max_emails, total_daily_limit)
            else:
                # Otherwise, use daily limit (we can't send more than this)
                sending_progress["total"] = total_daily_limit
            
            print(f"📊 Total daily limit: {total_daily_limit}")
            print(f"📊 CSV recipients: {total_recipients}")
            print(f"📊 Progress total (based on daily limit): {sending_progress['total']}")
            
            print(f"🚀 Starting email sending (same as command-line)...")
            print(f"📁 CSV: {csv_path}")
            print(f"📊 Total recipients: {total_recipients}")
            print(f"📊 Max emails: {max_emails if max_emails > 0 else 'No limit'}")
            
            # Add a stop check function to the sender if it supports it
            # For now, we'll check sending_active in the worker loop
            # Add stop check function to sender
            def should_stop():
                return not sending_active
            
            # Store stop check in sender if it supports it
            if hasattr(sender, 'set_stop_check'):
                sender.set_stop_check(should_stop)
            
            # This is the same method the command-line uses - processes CSV and sends directly
            sender.process_csv(str(full_path), test_mode=False, max_emails=max_emails if max_emails > 0 else None)
            
            print(f"✅ Email sending completed")
        except Exception as e:
            # Re-raise to be caught by outer handler
            raise
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
        
    except Exception as e:
        import traceback
        error_msg = f"❌ Error in send_emails_worker_direct: {e}"
        print(f"\n{error_msg}")
        print(traceback.format_exc())
        sending_progress["current_name"] = f"Error: {str(e)[:50]}"
        # The error will be visible in the terminal/logs
    finally:
        sending_active = False
        sending_progress["current_name"] = ""
        sending_progress["current_email"] = ""


@app.route('/stats')
def stats():
    """Statistics page."""
    history = load_history()
    config = load_config()
    
    # Calculate various stats
    total_recipients = len(history.get('recipients', {}))
    total_emails_sent = sum(recipient.get('send_count', 0) for recipient in history.get('recipients', {}).values())
    
    # Daily stats
    daily_stats = history.get('daily_stats', {})
    dates = sorted(daily_stats.keys(), reverse=True)[:30]  # Last 30 days
    
    return render_template('stats.html',
                         total_recipients=total_recipients,
                         total_emails_sent=total_emails_sent,
                         daily_stats=daily_stats,
                         dates=dates)


if __name__ == '__main__':
    # Ensure secrets directory exists
    SECRETS_DIR.mkdir(exist_ok=True)
    
    # Use port 5001 (5000 is often used by macOS AirPlay Receiver)
    port = int(os.environ.get('PORT', 5001))
    
    print(f"\n🚀 Starting TurboNIW Email Sender Web App...")
    print(f"📧 Open your browser at: http://localhost:{port}")
    print(f"🌐 Or access from network: http://0.0.0.0:{port}")
    print(f"\nPress Ctrl+C to stop the server\n")
    
    # Run app
    app.run(debug=True, host='0.0.0.0', port=port)

