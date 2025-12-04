# NIW Sales - Research Paper Collection & Email Outreach System

A comprehensive system for collecting research papers from ACL Anthology and arXiv, extracting author and email information, and conducting professional email outreach campaigns.

## 🎯 Overview

This repository contains tools for:
1. **Paper Collection**: Automated collection of papers from ACL Anthology and arXiv
2. **Data Extraction**: Extracting titles, authors, emails, and institutions from PDFs
3. **Email Matching**: Intelligent matching of authors with their email addresses
4. **Email Outreach**: Professional email sending system with multi-account support and spam protection

## 📁 Project Structure

```
niw_sales/
├── 1-acl_info.py                    # ACL paper extraction (single paper)
├── 1.1-collect_years_acl.py         # Batch ACL collection by year
├── 2.3-extract_emails.py            # arXiv email extraction (single paper)
├── 2.4-batch_extract_emails.py      # Batch arXiv email extraction
├── 2.7.2-collect_round2_monthly.py  # Monthly arXiv collection (bypasses API limits)
├── 2.12-batch_extract_round2_emails.py  # Round 2 email extraction
├── email_postprocess.py             # Universal post-processing (combine, filter, clean)
├── remove_acl_duplicates_from_arxiv.py  # Remove ACL duplicates from arXiv data
├── requirements_acl.txt            # Python dependencies for ACL/arXiv scripts
│
├── data/
│   ├── acl/                        # ACL paper data
│   │   ├── acl_YYYY_track.csv      # Collected papers by year/track
│   │   ├── acl_high_confidence.csv # High-confidence email matches
│   │   └── COLLECTION_STATUS.md     # Collection status tracking
│   │
│   └── arxiv/                      # arXiv paper data
│       ├── round1/                  # First collection round
│       │   ├── cs_XX_YYYY.csv      # Papers by category/year
│       │   ├── cs_XX_YYYY_email.csv # Extracted emails
│       │   └── arxiv_high_confidence.csv # Combined high-confidence results
│       ├── round2/                 # Second collection round (completing round1)
│       └── logs/                    # Processing logs
│
└── TurboNIW_Email_Sender/           # Email sending system
    ├── send_emails_smtp.py          # SMTP email sender
    ├── send_emails_gmail_api.py     # Gmail API sender
    ├── email_templates_variants.py  # Multi-variant email templates
    ├── config.json                  # Email account configuration
    └── README.md                    # Detailed email sender documentation
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_acl.txt
```

### 2. Collect Papers

#### ACL Anthology

**Single paper:**
```bash
python 1-acl_info.py "https://aclanthology.org/2024.acl-long.1.pdf"
```

**Collect by year:**
```bash
python 1.1-collect_years_acl.py
```
Edit the script to specify which years/tracks to collect.

#### arXiv

**Collect papers by category and year:**
```bash
python 2.7.2-collect_round2_monthly.py
```
This script collects papers from arXiv API, organized by category (e.g., `cs.RO`, `cs.LG`) and year.

**Extract emails from collected papers:**
```bash
python 2.4-batch_extract_emails.py
```
Processes all collected CSV files and extracts emails from PDFs.

### 3. Post-Process Data

Combine, filter, and clean the collected data:
```bash
python email_postprocess.py
```

This script:
- Combines multiple CSV files
- Filters by confidence score
- Removes duplicates
- Excludes Chinese emails (optional)
- Generates summary reports

### 4. Send Emails

#### Option A: Web Interface (Recommended for Scaling)

**Start the web app:**
```bash
cd TurboNIW_Email_Sender/web_app
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:5000` in your browser. The web interface allows you to:
- Add/manage email accounts through UI
- Authenticate Gmail API accounts with one click
- Adjust settings (delays, limits, whitelist/blacklist)
- Upload CSV and send emails with real-time status
- View statistics and account status

See `TurboNIW_Email_Sender/web_app/README.md` for detailed web app documentation.

#### Option B: Command Line

See `TurboNIW_Email_Sender/README.md` for detailed email sending instructions.

**Quick example:**
```bash
cd TurboNIW_Email_Sender
python send_emails_smtp.py --csv ../data/arxiv/round1/arxiv_high_confidence_non_chinese.csv --max 10
```

## 📊 Data Collection Workflow

### ACL Anthology

1. **Collect papers** using `1.1-collect_years_acl.py`
   - Supports years 2019-2025
   - Handles different URL formats by year
   - Auto-detects paper ranges

2. **Output**: CSV files with paper URLs, titles, authors, emails, confidence scores

### arXiv

1. **Collect paper metadata** using `2.7.2-collect_round2_monthly.py`
   - Queries arXiv API by category and year
   - Uses monthly queries to bypass 10,000 offset limit
   - Saves paper IDs, URLs, titles, authors

2. **Extract emails** using `2.4-batch_extract_emails.py`
   - Downloads PDFs from arXiv
   - Extracts emails from PDF text
   - Matches emails to authors using intelligent heuristics
   - Provides confidence scores

3. **Post-process** using `email_postprocess.py`
   - Combines all CSV files
   - Filters by confidence threshold
   - Removes duplicates
   - Generates final output

## 🔍 Key Features

### Email-to-Author Matching

The system uses sophisticated matching algorithms:
- Exact name matching
- Substring matching
- Hyphenated name variations
- Initial combinations
- Letter-level anagram matching
- Confidence scoring (0-100%)

### Multi-Variant Email System

The email sender includes:
- **5 subject line variants** (randomly selected)
- **5 email body variants** (randomly selected)
- **25 unique combinations** to avoid spam filters
- Empathetic, resource-sharing tone
- No explicit pricing (marketing-friendly)

### Rate Limiting & Safety

- **arXiv**: 3-second delay between requests (official policy)
- **Gmail**: Daily limits per account (10-50 emails/day for SMTP, 50-2000/day for Gmail API)
- **CAPTCHA detection**: Automatically stops on CAPTCHA blocks
- **Resume capability**: Can resume from where it stopped

## 📝 Scripts Overview

### Collection Scripts

- **`1-acl_info.py`**: Extract info from single ACL PDF
- **`1.1-collect_years_acl.py`**: Batch collect ACL papers by year/track
- **`2.7.2-collect_round2_monthly.py`**: Collect arXiv papers (monthly strategy to bypass limits)

### Extraction Scripts

- **`2.3-extract_emails.py`**: Extract emails from single arXiv PDF
- **`2.4-batch_extract_emails.py`**: Batch extract emails from multiple papers
- **`2.12-batch_extract_round2_emails.py`**: Extract emails for Round 2 papers

### Post-Processing Scripts

- **`email_postprocess.py`**: Universal post-processing (combine, filter, clean)
- **`remove_acl_duplicates_from_arxiv.py`**: Remove ACL papers from arXiv data

## 🔒 Security & Privacy

**Never commit:**
- `.secrets/` folder (passwords, tokens, credentials)
- `config.json` (account information)
- `sent_history.json` (email tracking)
- `arxiv.org_cookies.txt` (session cookies)
- Large CSV data files

All sensitive files are excluded via `.gitignore`.

## 📚 Documentation

- **`TurboNIW_Email_Sender/README.md`**: Complete email sending guide
- **`data/acl/COLLECTION_STATUS.md`**: ACL collection status
- **`data/arxiv/COLLECTION_TRACKER.md`**: arXiv collection tracking
- **`data/arxiv/ARXIV_CATEGORIES.md`**: List of all arXiv categories

## 🛠️ Troubleshooting

### arXiv API Limits

If collection stops at 10,000 papers:
- Use `2.7.2-collect_round2_monthly.py` (monthly query strategy)
- Breaks year into 12 monthly queries to bypass offset limit

### CAPTCHA Blocks

If you encounter CAPTCHA:
1. Export fresh cookies from browser
2. Save to `arxiv.org_cookies.txt`
3. Resume from last processed paper

### Email Extraction Issues

- Some PDFs have emails in footers (system handles this)
- LaTeX artifacts in emails are cleaned automatically
- Multi-name email formats (e.g., `{name1, name2}@domain.com`) are expanded

## 📄 License

For academic/research outreach use.

## 🤝 Contributing

This is a private project for research outreach. If you find issues or have suggestions, please open an issue.

---

**Note**: This system is designed for legitimate research outreach. Always respect email recipients and follow best practices for email communication.
