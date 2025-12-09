# Round 2 Processing Summary

## Processing Steps Completed

### Processing Command
**Universal Script:** `2.4-process_arxiv_round.py`

```bash
# Auto-detect round and settings from config (recommended)
python3.9 2.4-process_arxiv_round.py

# Or manually specify
python3.9 2.4-process_arxiv_round.py --round 2 --min-confidence 0.75
```

This universal script automatically:
1. Combines all `*_email.csv` files in the round folder
2. Deduplicates by email (keeps most recent year)
3. Filters by confidence threshold (>=75%)
4. Removes Chinese email domains
5. Excludes emails from ACL collection
6. Excludes emails from all prior rounds (Round 1, Round 2, etc.)

**Results:**
- Combined 7 email CSV files from round2
- Total records loaded: 537,964
- After deduplication: 124,139 unique emails
- After confidence filter (>=75%): 120,432 records
- After removing Chinese emails: **96,547 records**
- After excluding prior rounds: **65,599 unique emails**

**Exclusions:**
- ACL emails: 16,711 unique emails (from `acl_high_confidence.csv`)
- Round 1 emails: 75,015 unique emails (from `arxiv_high_confidence_non_chinese_no_acl.csv`)
- Combined prior emails: 91,726 unique emails
- Total duplicates in Round 2: 30,948 records
  - ACL duplicates: 3,825
  - Round 1 duplicates: 27,123

### Final Round 2 File
**Final File:** `arxiv_high_confidence_non_chinese_no_acl_no_prior_rounds.csv`

**Final Statistics:**
- Original Round 2 records: 96,547
- Removed (prior rounds): 30,948
- **Final unique emails: 65,599**

## File Structure

```
data/arxiv/round2/
├── arxiv_high_confidence_non_chinese.csv (96,547 records - before exclusions)
├── arxiv_high_confidence_non_chinese_no_acl_no_prior_rounds.csv (65,599 records - FINAL)
├── ROUND2_EMAIL_SUMMARY.txt
└── [individual category files...]
```

## Final Round 2 Characteristics

[OK] **Non-Chinese emails only** (removed 23,885 Chinese emails, 19.8%)
[OK] **High confidence only** (>=75% confidence threshold)
[OK] **No ACL duplicates** (excluded 3,825 ACL emails)
[OK] **No Round 1 duplicates** (excluded 27,123 Round 1 emails)
[OK] **Deduplicated** (one record per unique email)

## Usage

**For email sending campaigns, use:**
```
data/arxiv/round2/arxiv_high_confidence_non_chinese_no_acl_no_prior_rounds.csv
```

This file contains **65,599 unique, high-quality, non-Chinese emails** that are:
- Not in ACL collection
- Not in Round 1 collection
- Ready for email campaigns

## Universal Script for Future Rounds

The `2.4-process_arxiv_round.py` script works for any round:

```bash
# Auto-detect round from config (recommended)
python3.9 2.4-process_arxiv_round.py

# Or manually specify round
python3.9 2.4-process_arxiv_round.py --round 3

# Process Round 4 (will automatically exclude ACL, Round 1, Round 2, Round 3)
python3.9 2.4-process_arxiv_round.py --round 4

# Custom confidence threshold (overrides config)
python3.9 2.4-process_arxiv_round.py --round 3 --min-confidence 0.80
```

The script automatically:
- Finds all `*_email.csv` files in `data/arxiv/round{N}/`
- Processes and combines them
- Excludes emails from ACL and all prior rounds
- Creates final output: `arxiv_high_confidence_non_chinese_no_acl_no_prior_rounds.csv`

## Comparison with Round 1

| Metric | Round 1 | Round 2 (Final) |
|--------|---------|------------------|
| Total unique emails | 75,015 | 65,599 |
| Confidence threshold | >=75% | >=75% |
| Non-Chinese | Yes | Yes |
| Excludes ACL | Yes | Yes |
| Excludes prior rounds | N/A | Yes (Round 1) |

## Notes

- Round 2 started with 537,964 total records across 7 category files
- After all filtering and exclusions, we have 65,599 new unique emails
- These emails represent researchers who were not contacted in ACL or Round 1 campaigns
