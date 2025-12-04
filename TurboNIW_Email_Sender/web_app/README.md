# TurboNIW Email Sender - Web App

A simple web-based UI for managing email accounts, authentication, and sending emails at scale.

## 🚀 Features

- **Web UI**: No more command-line! Manage everything through a browser
- **Account Management**: Add, edit, delete email accounts through the UI
- **Gmail API Authentication**: One-click OAuth authentication flow
- **Settings Management**: Adjust delays, limits, whitelist/blacklist through UI
- **Email Sending**: Upload CSV and send emails with real-time status
- **Statistics Dashboard**: View sending stats and account status

## 📋 Quick Start

### 1. Install Dependencies

```bash
cd web_app
pip install -r requirements.txt
```

### 2. Run the App

```bash
python app.py
```

The app will start on `http://localhost:5001` (port 5000 is often used by macOS AirPlay Receiver)

### 3. Access the Web Interface

Open your browser and go to:
```
http://localhost:5001
```

**Note:** If you want to use a different port, set the `PORT` environment variable:
```bash
PORT=8080 python app.py
```

## 🎯 Usage

### Adding Accounts

1. Go to **Accounts** page
2. Click **+ Add Account**
3. Fill in:
   - Account ID (unique identifier)
   - Email address
   - Name
   - Authentication method (SMTP or Gmail API)
   - App password (for SMTP) or upload credentials file (for Gmail API)
   - Daily limit
4. Click **Add Account**

### Authenticating Gmail API Accounts

1. Go to **Accounts** page
2. Find your Gmail API account
3. Click **Authenticate** button
4. Browser will open for OAuth flow
5. Sign in and allow access
6. Token is saved automatically

### Adjusting Settings

1. Go to **Settings** page
2. Adjust:
   - **Minimum/Maximum Delay**: Random delay range between emails (in seconds)
   - **Max Retries**: Number of retry attempts
   - **Test Whitelist**: Emails that can always be sent to (for testing)
   - **Blacklist**: Emails that will never receive emails
3. Click **Save Settings**

### Sending Emails

1. Go to **Send Emails** page
2. Upload a CSV file with columns: `Email`, `Author` (or `Name`), `Title` (optional)
3. Set max emails (0 = no limit)
4. Click **Queue Emails**
5. Click **Start Sending** to begin
6. Monitor progress in real-time
7. Click **Stop Sending** to pause

## 📁 File Structure

```
web_app/
├── app.py                 # Flask application
├── templates/             # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── dashboard.html    # Main dashboard
│   ├── accounts.html    # Account management
│   ├── settings.html     # Settings page
│   ├── send.html         # Email sending interface
│   └── stats.html        # Statistics page
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🔧 Configuration

The web app uses the same `config.json` file as the command-line tools. All changes made through the web UI are saved to `config.json`.

## 🔒 Security Notes

- The app runs on `0.0.0.0:5000` by default (accessible from network)
- Change `app.secret_key` in production
- Use a reverse proxy (nginx) with HTTPS in production
- Never expose the `.secrets/` folder

## 🐛 Troubleshooting

### "Module not found" errors

Make sure you're running from the `web_app` directory and have installed requirements:
```bash
pip install -r requirements.txt
```

### Authentication not working

- Make sure credentials file exists in `.secrets/` folder
- Check that your email is added as a test user in Google Cloud Console
- Verify OAuth consent screen is configured

### CSV upload not working

- Ensure CSV has `Email` and `Author` (or `Name`) columns
- Check browser console for errors
- Verify CSV is valid (no special characters in headers)

## 🚀 Production Deployment

For production use:

1. **Use a production WSGI server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Set up HTTPS** with nginx or similar

3. **Change secret key:**
   ```python
   app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
   ```

4. **Use environment variables** for sensitive config

## 📝 Notes

- The web app integrates with existing `send_emails_smtp.py` and `send_emails_gmail_api.py`
- All email history is stored in `sent_history.json` (same as CLI)
- Account credentials are stored in `.secrets/` folder (same as CLI)

