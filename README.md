# ACL Paper Information Extractor

Extract paper information (title, authors, emails, institutions) from ACL Anthology PDFs for email outreach campaigns.

## Features

- ✅ Downloads and parses ACL PDFs from URLs
- ✅ Extracts paper titles (skips proceedings headers)
- ✅ Extracts author names with order tracking (first/last author marking)
- ✅ Extracts email addresses
- ✅ Extracts institutions based on superscript symbols/numbers
- ✅ Matches authors with their emails using intelligent heuristics
- ✅ Provides confidence scores for email matches
- ✅ Auto-detects paper range by trying papers until 404 error
- ✅ Exports to CSV format for easy email campaigns

## Installation

1. Install dependencies:
```bash
pip install -r requirements_acl.txt
```

Or install manually:
```bash
pip install PyPDF2 pdfplumber requests
```

## Quick Start

### Single Paper:
```bash
python extract_acl_info.py "https://aclanthology.org/2024.acl-long.1.pdf"
```

This will create `acl_papers_info.csv` with the extracted information.

### Auto-Detect Paper Range:
```bash
# Auto-detect all papers for 2024 long papers
python extract_acl_info.py --year 2024 --track long --auto-detect --output 2024-long.csv

# For 2020 (uses 'main' track, starts from paper 100)
python extract_acl_info.py --year 2020 --track main --auto-detect --output 2020-main.csv

# For 2019 (uses P19- format, starts from paper 1001)
python extract_acl_info.py --year 2019 --track long --auto-detect --output 2019-papers.csv
```

The script will:
- Automatically try papers until it encounters 3 consecutive 404 errors
- Show progress: `[1/100] Processing: ...` for each paper
- Save results in real-time after each paper (so you can see progress even if interrupted)

**URL Format by Year:**
- **2021-2024**: `{year}.acl-{track}.{num}.pdf` (e.g., `2024.acl-long.1.pdf`)
- **2020**: `{year}.acl-main.{num}.pdf` (e.g., `2020.acl-main.100.pdf`) - starts from 100
- **2019**: `P19-{num}.pdf` (e.g., `P19-1001.pdf`) - starts from 1001

### Range of Papers:
```bash
# Papers 1 to 10
python extract_acl_info.py --range 1 10

# Specific papers
python extract_acl_info.py --range 1 5 7 10
```

### Collect Multiple Years:
```bash
# Collect papers for specified years (edit collect_years.py to change years)
python collect_years.py
```

This will:
- Create separate CSV files based on year format:
  - 2021-2024: `YEAR-long.csv` (e.g., `2024-long.csv`)
  - 2020: `2020-main.csv`
  - 2019: `2019-papers.csv`
- Show real-time progress for each paper as it's processed
- Save results incrementally (so you can stop and resume if needed)
- Update `collection_log.json` with collection status

**Note**: Edit `collect_years.py` to specify which years to collect.

## Output Format

The script generates a CSV file with the following columns:

- **Paper URL**: The original PDF URL
- **Paper Title**: Extracted paper title
- **Author**: Author name
- **Author Order**: Position in author list (1, 2, 3, etc.)
- **First Author**: "Yes" if first author, empty otherwise
- **Last Author**: "Yes" if last author, empty otherwise
- **Email**: Author email (matched when possible)
- **Confidence**: Confidence score for email match (percentage)
- **Institution**: Author's institution(s) based on superscripts

Each author-email pair gets its own row, making it easy to:
- Import into email tools
- Personalize emails
- Track which authors you've contacted
- Filter by first/last authors

## Command Line Arguments

- `url` (positional): Single ACL PDF URL to process
- `--urls-file`: File containing list of URLs (one per line)
- `--range`: Range of paper numbers (e.g., `--range 1 10` or `--range 1 5 7 10`)
- `--year`: Conference year (default: 2024). Supports 2019-2024 with different URL formats
- `--track`: Paper track - `long`, `short`, or `main` (default: `long`)
  - For 2021-2024: `long` or `short`
  - For 2020, use `main` (no track differentiation)
  - For 2019, track doesn't matter (uses P19- format)
- `--auto-detect`: Auto-detect paper range by trying papers until 404 error
- `--output`: Output CSV filename (default: `acl_papers_info.csv`)
- `--append`: Append to existing CSV file
- `--json`: Also save results as JSON file

## How It Works

1. **Downloads PDF**: Fetches the PDF from the ACL Anthology URL
2. **Extracts Text**: Uses PyPDF2 or pdfplumber to extract text from first page only
3. **Finds Author Section**: Uses pattern detection (names with commas, symbols, emails) to locate author section
4. **Finds Title**: Identifies paper title (skips proceedings headers)
5. **Finds Authors**: Extracts author names using patterns (affiliation symbols, name patterns)
6. **Finds Institutions**: Maps superscript symbols/numbers to institutions
7. **Finds Emails**: Extracts all email addresses from author section
8. **Matches Authors-Emails**: Attempts to match authors with their emails using heuristics
9. **Exports Data**: Saves to CSV format for easy use in email campaigns

## Collection Status

See `COLLECTION_STATUS.md` for details on what papers have been collected.

## Notes

- The script focuses on the first page where title/author info is typically found
- Author-email matching is heuristic and may not always be perfect
- Some papers may have incomplete information (missing emails, etc.)
- The script handles common ACL formatting patterns (affiliation symbols, numbered affiliations, etc.)
- Paper numbering varies by year:
  - 2021-2024: starts from 1
  - 2020: starts from 100
  - 2019: starts from 1001
- Auto-detection stops after 3 consecutive 404 errors
- **Progress tracking**: The script shows `[X/Y] Processing: ...` for each paper and saves results in real-time
- **Real-time saving**: Results are saved after each paper, so you can stop and resume if needed

## Troubleshooting

1. **"Please install a PDF library"**: 
   - Install PyPDF2: `pip install PyPDF2`
   - Or pdfplumber: `pip install pdfplumber`

2. **Title extraction not working**:
   - Some PDFs may have unusual formatting
   - Check the PDF manually to verify structure

3. **Authors not extracted correctly**:
   - The script uses heuristics to identify authors
   - You may need to manually verify/correct some entries

4. **Emails not found**:
   - Some papers don't include emails in the PDF
   - Check the ACL Anthology website for contact information

5. **Institutions not extracted**:
   - Make sure superscripts are being detected correctly
   - Check if paper uses numbered affiliations (1, 2, 3) vs symbols (‡, §, etc.)
