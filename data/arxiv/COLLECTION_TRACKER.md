# arXiv Data Collection Tracker

This file tracks all arXiv data collection rounds, including categories, years, and dates collected.

---

## Round 1 - Engineering Categories 2024-2025

**Collection Period:** November 27 - December 2, 2025  
**Status:** ✅ Complete

### Categories Collected:

| Category | Full Name | Years | Papers (Raw) | Papers (With Emails) |
|----------|-----------|-------|--------------|---------------------|
| **cs.RO** | Robotics | 2024, 2025 | 18,253 | ~13,700 |
| **cs.LG** | Machine Learning | 2024, 2025 | 20,002 | ~13,400 |
| **cs.CV** | Computer Vision | 2024, 2025 | 20,002 | ~16,000 |
| **eess.SY** | Systems and Control | 2024, 2025 | 12,598 | ~7,500 |
| **eess.SP** | Signal Processing | 2024, 2025 | 11,608 | ~7,800 |

### Summary:
- **Total Papers Queried:** 82,463
- **Total Records (Before Dedup):** 407,263
- **Unique Emails (After Dedup):** 100,271
- **High Confidence (≥75%):** 97,235

### Output Files:
- `round1/arxiv_all_combined.csv` - All data combined (328,379 rows)
- `round1/arxiv_high_confidence.csv` - Filtered ≥75% confidence (97,235 rows) **← USE THIS**
- Individual category files in `round1/` folder
- Processing logs in `logs/` folder

### Notes:
- Deduplication: Kept most recent year when same email appeared multiple times
- Confidence threshold: ≥75% for high confidence file
- Rate limiting: 3 seconds between requests (arXiv policy)
- Multiple cookie refresh sessions needed due to CAPTCHA

---

## Round 2 - [Future Collection]

**Status:** 🔜 Not Started

**Planned Categories:**
- TBD

**Years:**
- TBD

**Notes:**
- Add details when starting Round 2

---

## Round 3 - [Future Collection]

**Status:** 🔜 Not Started

---

## Collection Guidelines for Future Rounds:

### Before Starting:
1. Choose categories from `ARXIV_CATEGORIES.md`
2. Decide on years to collect
3. Create `roundN/` folder in `data/arxiv/`
4. Update this tracker

### During Collection:
1. Run `2.1-query_arxiv_papers.py` for each category/year
2. Run `2.2-collect_arxiv_batch.py` to collect all
3. Run `2.3-extract_emails.py` to process PDFs
4. Run `2.4-batch_extract_emails.py` for batch processing
5. Refresh cookies when CAPTCHA appears

### After Collection:
1. Run `2.5-combine_arxiv_csv.py` to combine all files
2. Run `2.6-filter_arxiv_by_confidence.py` to filter
3. Move all files to `roundN/` folder
4. Update this tracker with statistics

### Important:
- Check for email duplicates across rounds before sending campaigns
- Keep deduplication logs for reference
- Document any issues or special cases

---

## Combined Data Across All Rounds:

### Total Unique Emails:
- **Round 1:** 97,235 (≥75% confidence)
- **Round 2:** TBD
- **Round 3:** TBD
- **Overall Total:** 97,235 (update after each round)

### Deduplication Notes:
- When combining multiple rounds, deduplicate by email to avoid sending duplicates
- Keep most recent data when same email appears in multiple rounds

---

*Last Updated: December 2, 2025*

