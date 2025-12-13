# Email Categorization System

## Overview

This system categorizes sent emails into 3 groups by analyzing inbox messages:

1. **Category 1: Replied** - Recipients who responded to our emails
2. **Category 2: No Reply** - Recipients who received emails but haven't responded yet
3. **Category 3: Failed** - Emails that bounced or failed due to invalid addresses

## How It Works

### Step 1: Analysis Script (`analyze_sent_emails.py`)

The script:
1. Loads `sent_history.json` to get all emails sent from a specific account
2. For each recipient, searches the Gmail inbox for:
   - **Replies**: Messages from the recipient's email address
   - **Bounces**: Messages from `mailer-daemon@googlemail.com` mentioning the recipient
3. Categorizes each recipient based on findings
4. Saves detailed analysis to a text file

### Step 2: JSON Categorization File

After analysis, a JSON file will be created to store categories for easy access:
- `email_categories.json` - Maps each recipient email to their category

### Step 3: Website Integration

Category 2 (No Reply) recipients will be displayed on the website for team follow-up.

## Usage

### Run Analysis

```bash
cd TurboNIW_Email_Sender
python3.9 analyze_sent_emails.py --account-id account3_gmail_api
```

**Options:**
- `--account-id`: Account ID from config.json (required)
- `--config`: Config file path (default: `config.json`)
- `--history`: Sent history file path (default: `sent_history.json`)
- `--output`: Output analysis file (default: `email_analysis_report.txt`)

### Example

```bash
# Analyze emails sent from spy.observer.wx@gmail.com
python3.9 analyze_sent_emails.py --account-id account3_gmail_api --output spy_account_analysis.txt
```

## Output

The script generates:
1. **Analysis Report** (text file): Detailed breakdown of all recipients with their categories
2. **Console Summary**: Quick stats showing counts for each category

## Categories Explained

### Category 1: Replied ✅
- **Criteria**: Found reply messages from the recipient
- **Action**: Team will follow up with these recipients
- **Data**: Includes reply subject, date, and preview

### Category 2: No Reply ⏳
- **Criteria**: No replies found, no bounce messages
- **Action**: Future follow-up candidates
- **Data**: Basic recipient info (name, email, paper title, send dates)

### Category 3: Failed ❌
- **Criteria**: Found bounce messages mentioning the recipient
- **Action**: Drop from future campaigns (invalid address)
- **Data**: Includes bounce message details (subject, date, error type)

## Next Steps

After running the analysis:
1. Review the analysis report
2. Create JSON categorization file
3. Integrate Category 2 display on website
4. Set up team follow-up workflow

