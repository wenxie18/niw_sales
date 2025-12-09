# Email Service Providers Documentation
## Alternatives to Gmail for Automated Email Sending

This document provides detailed information about email service providers suitable for automated email sending, including setup instructions, pricing, limits, and integration details.

---

## Table of Contents
1. [Outlook/Hotmail (Microsoft)](#outlookhotmail-microsoft)
2. [AWS SES (Amazon Simple Email Service)](#aws-ses-amazon-simple-email-service)
3. [SendGrid (Twilio)](#sendgrid-twilio)
4. [Mailgun](#mailgun)
5. [Brevo (formerly Sendinblue)](#brevo-formerly-sendinblue)
6. [Comparison Matrix](#comparison-matrix)

---

## Outlook/Hotmail (Microsoft)

### Overview
Personal email service from Microsoft that supports SMTP for automated sending. Good for small-scale operations with multiple accounts.

### Setup Instructions

#### 1. Create Account
- Visit https://outlook.com or https://hotmail.com
- Create account (phone verification not always required)
- Note: Can create multiple accounts easily

#### 2. Enable Two-Step Verification
1. Go to https://account.microsoft.com/security
2. Sign in with your Outlook/Hotmail account
3. Navigate to "Security" section
4. Enable "Two-step verification" (if not already enabled)

#### 3. Generate App Password
1. On the security page, find "App passwords" section
2. Click "Create a new app password"
3. Name it (e.g., "Email Sender App")
4. Copy the 16-character password (format: `abcd-efgh-ijkl-mnop`)
5. Save to `.secrets/outlook_account1_password.txt`

#### 4. SMTP Settings
- **SMTP Server:** `smtp-mail.outlook.com`
- **Port:** 587
- **Encryption:** STARTTLS
- **Username:** Your full email address (e.g., `yourname@outlook.com`)
- **Password:** The app password (16-character code)

#### 5. Code Integration (Future)
Update `send_emails_smtp.py` to detect Outlook accounts:

```python
# Detect email provider and use appropriate SMTP server
if '@outlook.com' in account['email'] or '@hotmail.com' in account['email']:
    smtp_server = 'smtp-mail.outlook.com'
else:
    smtp_server = 'smtp.gmail.com'

with smtplib.SMTP(smtp_server, 587) as server:
    server.starttls()
    server.login(account['email'], password)
    server.send_message(msg)
```

### Limits
- **Daily Limit:** 300 emails per day per account
- **Recipients per Email:** 100 recipients maximum
- **Rate Limit:** Not officially documented, but conservative sending recommended

### Pricing
- **Free:** Yes (personal accounts)
- **Paid:** Microsoft 365 Personal ($6.99/month) - same limits

### Pros
- ✅ Easy to create multiple accounts
- ✅ No phone verification required (sometimes)
- ✅ Works with existing SMTP code (with minor modification)
- ✅ Good deliverability
- ✅ Free for personal use

### Cons
- ❌ Lower daily limits than Gmail (300 vs 500-2000)
- ❌ Basic Auth will be disabled March 2026 (need OAuth 2.0)
- ❌ Account suspension risk if limits exceeded
- ❌ Multiple accounts needed for scale

### Important Notes
- **March 2026:** Microsoft will disable Basic Authentication (username/password) for SMTP
- **OAuth 2.0 Required:** After March 2026, must use OAuth 2.0 authentication
- **Account Security:** Enable two-step verification to generate app passwords

### Config.json Format
```json
{
  "id": "outlook_account1",
  "email": "yourname@outlook.com",
  "name": "Wen",
  "auth_method": "app_password",
  "app_password_file": ".secrets/outlook_account1_password.txt",
  "daily_limit": 300,
  "enabled": true
}
```

---

## AWS SES (Amazon Simple Email Service)

### Overview
Enterprise-grade email service from Amazon Web Services. Extremely cost-effective for high-volume sending with excellent deliverability.

### Setup Instructions

#### 1. Create AWS Account
1. Go to https://aws.amazon.com
2. Create account (requires credit card, but free tier available)
3. Complete account verification

#### 2. Access SES Console
1. Sign in to AWS Console
2. Navigate to "Simple Email Service" (SES)
3. Select region (e.g., `us-east-1`, `us-west-2`)

#### 3. Verify Email Address (Sandbox Mode)
1. In SES Console, go to "Verified identities"
2. Click "Create identity"
3. Select "Email address"
4. Enter your email and click "Create identity"
5. Check email and click verification link
6. **Note:** In sandbox mode, can only send to verified addresses

#### 4. Request Production Access
1. In SES Console, go to "Account dashboard"
2. Click "Request production access"
3. Fill out form:
   - Use case: "Transactional emails for business outreach"
   - Website URL: Your website
   - Describe your use case
4. Wait for approval (usually 24-48 hours)

#### 5. Create IAM User for API Access
1. Go to IAM Console → Users → Create user
2. Name: `ses-email-sender`
3. Attach policy: `AmazonSESFullAccess` (or create custom policy)
4. Create access key (Access key ID and Secret access key)
5. Save credentials securely

#### 6. Install Python Library
```bash
pip install boto3
```

#### 7. Code Integration (Future)
Create `send_emails_aws_ses.py`:

```python
import boto3
from botocore.exceptions import ClientError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AWSSESSender:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        self.ses_client = boto3.client(
            'ses',
            aws_access_key_id=self.config['aws']['access_key_id'],
            aws_secret_access_key=self.config['aws']['secret_access_key'],
            region_name=self.config['aws']['region']  # e.g., 'us-east-1'
        )
    
    def send_email(self, from_email, to_email, subject, body_html, body_text):
        """Send email via AWS SES."""
        try:
            response = self.ses_client.send_email(
                Source=from_email,
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Html': {'Data': body_html, 'Charset': 'UTF-8'},
                        'Text': {'Data': body_text, 'Charset': 'UTF-8'}
                    }
                }
            )
            return response['MessageId']
        except ClientError as e:
            print(f"Error sending email: {e.response['Error']['Message']}")
            return None
```

#### 8. Config.json Structure
```json
{
  "aws": {
    "access_key_id": "AKIAIOSFODNN7EXAMPLE",
    "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    "region": "us-east-1"
  },
  "sending": {
    "from_email": "noreply@yourdomain.com",
    "from_name": "Your Name"
  }
}
```

### Limits

#### Sandbox Mode (Default)
- **Sending:** Only to verified email addresses
- **Receiving:** Only from verified email addresses
- **Daily Limit:** 200 emails/day
- **Rate Limit:** 1 email/second

#### Production Mode (After Approval)
- **Daily Limit:** Starts at 50,000 emails/day (can request increase)
- **Rate Limit:** 14 emails/second (can request increase)
- **Sending:** To any email address
- **Bounce/Complaint Rate:** Must stay below 5% bounce, 0.1% complaint

### Pricing
- **First 62,000 emails/month:** FREE (if sent from EC2 instance)
- **After free tier:** $0.10 per 1,000 emails
- **Example:** 100,000 emails/month = $3.80
- **Data transfer:** Free (emails are small)

### Pros
- ✅ Extremely cost-effective ($0.10 per 1,000 emails)
- ✅ Excellent deliverability rates
- ✅ Highly scalable (millions of emails/day)
- ✅ Detailed analytics and bounce/complaint tracking
- ✅ No per-account limits (single sending identity)
- ✅ Production-ready infrastructure

### Cons
- ❌ Requires AWS account setup (more technical)
- ❌ Sandbox mode restrictions initially
- ❌ Must verify sending domain/email
- ❌ Need to monitor bounce/complaint rates
- ❌ More complex setup than SMTP

### Best For
- High-volume sending (10,000+ emails/month)
- Cost-sensitive operations
- Long-term scalability needs
- Businesses with technical resources

### Resources
- **Documentation:** https://docs.aws.amazon.com/ses/
- **Python SDK:** https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ses.html
- **Pricing Calculator:** https://aws.amazon.com/ses/pricing/

---

## SendGrid (Twilio)

### Overview
Cloud-based email service designed for transactional and marketing emails. User-friendly with good API and SMTP support.

### Setup Instructions

#### 1. Create Account
1. Go to https://sendgrid.com
2. Sign up for free account
3. Verify email address

#### 2. Create API Key
1. Go to Settings → API Keys
2. Click "Create API Key"
3. Name: "Email Sender API Key"
4. Permissions: "Full Access" or "Mail Send" only
5. Copy API key (shown only once - save securely!)

#### 3. Verify Sender Identity
1. Go to Settings → Sender Authentication
2. Click "Verify a Single Sender"
3. Enter your email address
4. Fill out form (name, address, etc.)
5. Check email and click verification link

#### 4. Install Python Library
```bash
pip install sendgrid
```

#### 5. Code Integration (Future)
Create `send_emails_sendgrid.py`:

```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class SendGridSender:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        self.sg = SendGridAPIClient(self.config['sendgrid']['api_key'])
    
    def send_email(self, from_email, from_name, to_email, subject, body_html, body_text):
        """Send email via SendGrid API."""
        message = Mail(
            from_email=(from_email, from_name),
            to_emails=to_email,
            subject=subject,
            html_content=body_html,
            plain_text_content=body_text
        )
        
        try:
            response = self.sg.send(message)
            return response.status_code == 202  # 202 = accepted
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
```

#### 6. SMTP Alternative (Simpler)
SendGrid also supports SMTP (easier integration):

**SMTP Settings:**
- **Server:** `smtp.sendgrid.net`
- **Port:** 587
- **Username:** `apikey`
- **Password:** Your SendGrid API key
- **Encryption:** STARTTLS

Can use existing `send_emails_smtp.py` with these settings!

### Limits

#### Free Tier
- **Daily Limit:** 100 emails/day
- **Monthly Limit:** 3,000 emails/month
- **Features:** Full API access, analytics

#### Paid Plans
- **Essentials:** $19.95/month - 50,000 emails
- **Pro:** $89.95/month - 100,000 emails
- **Premier:** Custom pricing

### Pricing
- **Free:** 100 emails/day (3,000/month)
- **Paid:** Starts at $19.95/month for 50,000 emails
- **Overage:** $0.0006 per email after limit

### Pros
- ✅ Easy setup and integration
- ✅ Good free tier for testing
- ✅ Both API and SMTP support
- ✅ Excellent documentation
- ✅ Good deliverability
- ✅ Real-time analytics

### Cons
- ❌ Free tier limited (100/day)
- ❌ More expensive than AWS SES at scale
- ❌ Must verify sender identity
- ❌ Paid plans required for production use

### Best For
- Small to medium volume (under 50k/month)
- Quick setup needs
- Users preferring SMTP over API
- Businesses wanting user-friendly interface

### Resources
- **Documentation:** https://docs.sendgrid.com/
- **Python Library:** https://github.com/sendgrid/sendgrid-python
- **SMTP Settings:** https://docs.sendgrid.com/for-developers/sending-email/getting-started-smtp

---

## Mailgun

### Overview
Developer-friendly email service with powerful APIs. Good for transactional emails and automation.

### Setup Instructions

#### 1. Create Account
1. Go to https://www.mailgun.com
2. Sign up for account
3. Verify email address

#### 2. Add and Verify Domain
1. Go to Sending → Domains
2. Click "Add New Domain"
3. Enter your domain (e.g., `mail.yourdomain.com`)
4. Add DNS records (SPF, DKIM, MX) to your domain
5. Wait for verification (usually minutes)

**Alternative:** Use Mailgun's sandbox domain for testing (can only send to authorized recipients)

#### 3. Get API Credentials
1. Go to Sending → API Keys
2. Copy your API key (Private API key)
3. Note your domain name

#### 4. Install Python Library
```bash
pip install mailgun2
```

#### 5. Code Integration (Future)
Create `send_emails_mailgun.py`:

```python
import requests

class MailgunSender:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        self.api_key = self.config['mailgun']['api_key']
        self.domain = self.config['mailgun']['domain']
        self.base_url = f"https://api.mailgun.net/v3/{self.domain}"
    
    def send_email(self, from_email, from_name, to_email, subject, body_html, body_text):
        """Send email via Mailgun API."""
        response = requests.post(
            f"{self.base_url}/messages",
            auth=("api", self.api_key),
            data={
                "from": f"{from_name} <{from_email}>",
                "to": to_email,
                "subject": subject,
                "text": body_text,
                "html": body_html
            }
        )
        return response.status_code == 200
```

#### 6. SMTP Alternative
Mailgun also supports SMTP:

**SMTP Settings:**
- **Server:** `smtp.mailgun.org`
- **Port:** 587
- **Username:** Your Mailgun domain (e.g., `postmaster@mg.yourdomain.com`)
- **Password:** Your Mailgun SMTP password (different from API key)
- **Encryption:** STARTTLS

### Limits

#### Free Tier (First 3 Months)
- **Monthly Limit:** 5,000 emails/month
- **Daily Limit:** Not specified (reasonable use)

#### Free Tier (After 3 Months)
- **Monthly Limit:** 1,000 emails/month
- **Daily Limit:** ~33 emails/day average

#### Paid Plans
- **Foundation:** $35/month - 50,000 emails
- **Growth:** $80/month - 100,000 emails
- **Scale:** Custom pricing

### Pricing
- **Free:** 1,000 emails/month (after trial)
- **Paid:** Starts at $35/month for 50,000 emails
- **Overage:** $0.80 per 1,000 emails

### Pros
- ✅ Developer-friendly API
- ✅ Good free tier initially (5k/month)
- ✅ Excellent documentation
- ✅ Both API and SMTP support
- ✅ Good deliverability
- ✅ Detailed analytics and webhooks

### Cons
- ❌ Free tier reduces after 3 months
- ❌ More expensive than AWS SES
- ❌ Domain verification required for production
- ❌ Paid plans needed for serious use

### Best For
- Developers who prefer API-first approach
- Transactional email needs
- Applications requiring webhooks
- Medium volume (10k-100k/month)

### Resources
- **Documentation:** https://documentation.mailgun.com/
- **Python Examples:** https://github.com/mailgun/mailgun-python
- **SMTP Settings:** https://documentation.mailgun.com/en/latest/user_manual.html#sending-via-smtp

---

## Brevo (formerly Sendinblue)

### Overview
European-based email service with generous free tier. Good for small to medium volume sending.

### Setup Instructions

#### 1. Create Account
1. Go to https://www.brevo.com
2. Sign up for free account
3. Verify email address

#### 2. Get API Key
1. Go to Settings → API Keys
2. Click "Generate a new API key"
3. Name: "Email Sender"
4. Copy API key (save securely)

#### 3. Verify Sender
1. Go to Senders & IP → Senders
2. Click "Add a sender"
3. Enter email address and details
4. Verify via email link

#### 4. Install Python Library
```bash
pip install sib-api-v3-sdk
```

#### 5. Code Integration (Future)
Create `send_emails_brevo.py`:

```python
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

class BrevoSender:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = self.config['brevo']['api_key']
        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
    
    def send_email(self, from_email, from_name, to_email, subject, body_html, body_text):
        """Send email via Brevo API."""
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            sender=sib_api_v3_sdk.SendSmtpEmailSender(
                email=from_email, name=from_name
            ),
            to=[sib_api_v3_sdk.SendSmtpEmailTo(email=to_email)],
            subject=subject,
            html_content=body_html,
            text_content=body_text
        )
        
        try:
            api_response = self.api_instance.send_transac_email(send_smtp_email)
            return api_response.message_id is not None
        except ApiException as e:
            print(f"Error: {e}")
            return False
```

#### 6. SMTP Alternative
Brevo supports SMTP:

**SMTP Settings:**
- **Server:** `smtp-relay.brevo.com`
- **Port:** 587
- **Username:** Your Brevo login email
- **Password:** Your Brevo SMTP key (different from API key)
- **Encryption:** STARTTLS

### Limits

#### Free Tier
- **Daily Limit:** 300 emails/day
- **Monthly Limit:** 9,000 emails/month
- **Features:** Full API, SMTP, basic analytics

#### Paid Plans
- **Starter:** €25/month - 20,000 emails
- **Business:** €65/month - 100,000 emails
- **Enterprise:** Custom pricing

### Pricing
- **Free:** 300 emails/day (9,000/month)
- **Paid:** Starts at €25/month (~$27) for 20,000 emails
- **Overage:** €0.0025 per email

### Pros
- ✅ Generous free tier (300/day)
- ✅ Good for small to medium volume
- ✅ Both API and SMTP support
- ✅ User-friendly interface
- ✅ Good deliverability

### Cons
- ❌ Lower limits than AWS SES
- ❌ More expensive at scale
- ❌ European-based (may affect some users)
- ❌ Paid plans needed for high volume

### Best For
- Small businesses
- Startups testing email sending
- Users wanting generous free tier
- Medium volume (under 50k/month)

### Resources
- **Documentation:** https://developers.brevo.com/
- **Python SDK:** https://github.com/getbrevo/brevo-python
- **SMTP Settings:** https://help.brevo.com/hc/en-us/articles/209467485

---

## Comparison Matrix

| Service | Free Tier | Paid (50k/month) | Setup Difficulty | Best For |
|---------|-----------|-------------------|------------------|----------|
| **Outlook/Hotmail** | 300/day | Free | Easy | Small scale, multiple accounts |
| **AWS SES** | 62k/month* | $5 | Medium | High volume, cost-sensitive |
| **SendGrid** | 100/day | $20/month | Easy | Quick setup, SMTP preference |
| **Mailgun** | 1k/month | $35/month | Medium | Developers, API-first |
| **Brevo** | 300/day | €25/month | Easy | Small businesses, free tier |

*Free if sent from EC2 instance

## Recommendations by Use Case

### Current Setup (Multiple Accounts, ~200/day each)
- **Best:** Outlook/Hotmail (easy transition, works with existing code)
- **Alternative:** Brevo (300/day free tier, good for testing)

### Scaling to 10,000+ emails/month
- **Best:** AWS SES (most cost-effective)
- **Alternative:** SendGrid (easier setup, more expensive)

### Long-term Production (100k+ emails/month)
- **Best:** AWS SES (scalable, cost-effective)
- **Alternative:** Mailgun (if prefer API-first approach)

## Migration Strategy

### Phase 1: Immediate (Outlook/Hotmail)
1. Create 5-10 Outlook accounts
2. Generate app passwords
3. Update code to support Outlook SMTP
4. Add accounts to config.json
5. Test with small batch

### Phase 2: Short-term (3-6 months)
- Monitor account health
- Evaluate costs vs. limits
- Consider AWS SES for higher volume

### Phase 3: Long-term (6+ months)
- Migrate to AWS SES for cost efficiency
- Keep Outlook accounts as backup
- Implement proper bounce/complaint handling

## Code Changes Required (Future)

### For Outlook Support
Update `send_emails_smtp.py` line 182:

```python
# Detect email provider
if '@outlook.com' in account['email'] or '@hotmail.com' in account['email']:
    smtp_server = 'smtp-mail.outlook.com'
elif '@gmail.com' in account['email']:
    smtp_server = 'smtp.gmail.com'
else:
    smtp_server = 'smtp.gmail.com'  # default

with smtplib.SMTP(smtp_server, 587) as server:
    server.starttls()
    server.login(account['email'], password)
    server.send_message(msg)
```

### For AWS SES
- Create new `send_emails_aws_ses.py` file
- Update `web_app/app.py` to support SES sender
- Add AWS credentials to config.json
- Test with verified email addresses first

---

## Security Best Practices

1. **Never commit credentials** - Use `.secrets/` folder (already in .gitignore)
2. **Rotate API keys** - Change passwords/keys periodically
3. **Monitor usage** - Watch for unusual activity
4. **Rate limiting** - Respect service limits
5. **Bounce handling** - Remove invalid emails from lists
6. **Complaint handling** - Honor unsubscribe requests

---

## Support and Resources

- **Outlook:** https://support.microsoft.com/outlook
- **AWS SES:** https://aws.amazon.com/ses/ (24/7 support on paid plans)
- **SendGrid:** https://support.sendgrid.com/ (email support)
- **Mailgun:** https://www.mailgun.com/support/ (email + chat)
- **Brevo:** https://help.brevo.com/ (email support)

---

*Last Updated: December 2024*

