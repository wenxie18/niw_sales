# arXiv Paper Collection & Email Extraction Workflow

This document describes the complete workflow for collecting papers from arXiv and extracting email addresses.

## Workflow Overview

```
1. Collect Papers → 2. Extract Emails → 3. Post-Process → 4. Ready for Campaigns
```

## Step 1: Collect Papers from arXiv

**Script:** `2.1-collect_arxiv_papers.py`

This script collects papers from arXiv by category and year using monthly queries (to bypass the 10,000 offset limit).

### Usage

```bash
# Uses configuration from arxiv_collection_config.json
python3.9 2.1-collect_arxiv_papers.py
```

### What it does:
- Queries arXiv API month-by-month for each category/year
- Collects paper metadata (title, authors, PDF URL, etc.)
- Saves to CSV files in `data/arxiv/round{N}/`
- Output format: `{category}_{year}.csv` (e.g., `cs_cv_2024.csv`)

### Configuration:
Edit `arxiv_collection_config.json` to change:
- Round number
- Categories (e.g., `cs.LG`, `cs.CV`)
- Years (e.g., `2024`, `2025`)
- Output directory
- Batch size and rate limit delays

## Step 2: Extract Emails from Papers

After collecting papers, extract email addresses from PDFs.

### Option A: Single File Processing

**Script:** `2.2-extract_emails_from_papers.py`

Process a single CSV file to extract emails.

```bash
python3.9 2.2-extract_emails_from_papers.py \
    --input data/arxiv/round2/cs_cv_2024.csv \
    --output data/arxiv/round2/cs_cv_2024_email.csv
```

### Option B: Batch Processing (Multiple Files)

**Script:** `2.3-batch_extract_emails.py` (Universal - works for any round)

Process all CSV files in a directory.

```bash
# Auto-detect round from config file (recommended)
python3.9 2.3-batch_extract_emails.py

# Manually specify round (overrides config)
python3.9 2.3-batch_extract_emails.py --round 2

# Custom directory (overrides round)
python3.9 2.3-batch_extract_emails.py --input-dir data/arxiv/round2
```

### What it does:
- Downloads PDFs from arXiv
- Extracts email addresses from first page
- Matches emails to authors using name matching
- Saves results to `*_email.csv` files
- Handles rate limits and CAPTCHAs

### Requirements:
- `arxiv.org_cookies.txt` file (for bypassing rate limits)
- Internet connection for PDF downloads

## Step 3: Post-Process Email Data

**Script:** `2.4-process_arxiv_round.py`

This universal script processes any round of collected emails.

### Usage

```bash
# Auto-detect round and settings from config file (recommended)
python3.9 2.4-process_arxiv_round.py

# Manually specify round (overrides config)
python3.9 2.4-process_arxiv_round.py --round 2

# Override confidence threshold (overrides config)
python3.9 2.4-process_arxiv_round.py --round 3 --min-confidence 0.80
```

### What it does:
1. Combines all `*_email.csv` files in the round folder
2. Deduplicates by email (keeps most recent year)
3. Filters by confidence threshold (default ≥75%)
4. Removes Chinese email domains
5. Excludes emails from ACL collection
6. Excludes emails from all prior rounds
7. Creates final output ready for email campaigns

### Output Files:
- `arxiv_high_confidence_non_chinese.csv` - Intermediate (before exclusions)
- `arxiv_high_confidence_non_chinese_no_acl_no_prior_rounds.csv` - **FINAL** (ready for campaigns)
- `ROUND{N}_EMAIL_SUMMARY.txt` - Statistics summary

## Complete Example Workflow

### Round 2 Collection

```bash
# Step 1: Update config file (arxiv_collection_config.json) with round=2, categories, years
# Step 2: Collect papers (uses config automatically)
python3.9 2.1-collect_arxiv_papers.py
# Output: data/arxiv/round2/cs_cv_2024.csv, cs_cv_2025.csv, etc.

# Step 3: Extract emails (auto-detects round from config)
python3.9 2.3-batch_extract_emails.py
# Output: data/arxiv/round2/cs_cv_2024_email.csv, cs_cv_2025_email.csv, etc.

# Step 4: Post-process (auto-detects round and settings from config)
python3.9 2.4-process_arxiv_round.py
# Output: data/arxiv/round2/arxiv_high_confidence_non_chinese_no_acl_no_prior_rounds.csv
```

### Round 3 Collection (Future)

```bash
# Step 1: Update config file: set round=3, update categories/years as needed
# Step 2: Collect papers
python3.9 2.1-collect_arxiv_papers.py

# Step 3: Extract emails (auto-detects round=3 from config)
python3.9 2.3-batch_extract_emails.py

# Step 4: Post-process (auto-detects round=3, automatically excludes Round 1 & 2)
python3.9 2.4-process_arxiv_round.py
```

## Script Summary

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `2.1-collect_arxiv_papers.py` | Collect papers from arXiv | Config file | `{category}_{year}.csv` |
| `2.2-extract_emails_from_papers.py` | Extract emails from single CSV | `{category}_{year}.csv` | `{category}_{year}_email.csv` |
| `2.3-batch_extract_emails.py` | Batch extract (Universal - any round) | Multiple CSVs | Multiple `*_email.csv` |
| `2.4-process_arxiv_round.py` | Post-process emails | All `*_email.csv` in round | Final campaign-ready CSV |

## Configuration File

All scripts use `arxiv_collection_config.json` for settings. Edit this file to change:
- **Collection**: Round number, categories, years, output directory, batch size
- **Email Extraction**: Cookie file path, temp directory, retries, rate limits
- **Post Processing**: Min confidence, remove Chinese emails, deduplicate

Scripts will auto-detect round number and settings from config, but you can override with command-line arguments.

## Notes

- **Rate Limits**: arXiv allows 1 request per 3 seconds. Scripts include delays.
- **CAPTCHAs**: If you hit CAPTCHA, refresh cookies in `arxiv.org_cookies.txt`
- **Resume**: Email extraction scripts can resume from where they stopped
- **Confidence Threshold**: Default is 75% (configurable in config file). Higher = more accurate but fewer emails
- **Chinese Emails**: Automatically filtered out in post-processing (configurable)

## Troubleshooting

### CAPTCHA Detected
1. Open browser, go to arxiv.org
2. Export cookies as `arxiv.org_cookies.txt` (Netscape format)
3. Place in project root
4. Re-run extraction script

### Script Not Found
Make sure you're in the project root directory:
```bash
cd /Users/wenxie/Documents/GitHub/niw_sales
```

### No Papers Collected
- Check internet connection
- Verify category names are correct (e.g., `cs.LG` not `cs_lg`)
- Check arXiv API status

