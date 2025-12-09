# arXiv Collection Configuration

## Configuration File: `arxiv_collection_config.json`

This configuration file allows you to easily change collection parameters without editing Python scripts.

## Structure

```json
{
  "collection": {
    "round": 2,
    "output_dir": "data/arxiv/round2",
    "categories": [
      {
        "arxiv_category": "cs.LG",
        "short_name": "cs_lg",
        "years": [2024, 2025]
      }
    ],
    "batch_size": 1000,
    "rate_limit_delay_seconds": 3
  },
  
  "email_extraction": {
    "cookie_file": "arxiv.org_cookies.txt",
    "temp_dir": "temp_pdfs",
    "max_retries": 3,
    "rate_limit_delay_seconds": 3
  },
  
  "post_processing": {
    "min_confidence": 0.75,
    "remove_chinese": true,
    "deduplicate": true
  }
}
```

## Configuration Sections

### `collection`
Controls paper collection from arXiv API.

- **`round`**: Round number (1, 2, 3, etc.)
- **`output_dir`**: Where to save collected CSV files
- **`categories`**: List of categories to collect
  - **`arxiv_category`**: Official arXiv category (e.g., `cs.LG`, `cs.CV`)
  - **`short_name`**: Short name for file naming (e.g., `cs_lg`, `cs_cv`)
  - **`years`**: List of years to collect (e.g., `[2024, 2025]`)
- **`batch_size`**: Number of papers per API request (max 2000, default 1000)
- **`rate_limit_delay_seconds`**: Delay between API requests (default 3)

### `email_extraction`
Controls email extraction from PDFs.

- **`cookie_file`**: Path to arXiv cookies file
- **`temp_dir`**: Temporary directory for downloaded PDFs
- **`max_retries`**: Maximum retry attempts for failed downloads
- **`rate_limit_delay_seconds`**: Delay between PDF downloads

### `post_processing`
Controls final email processing.

- **`min_confidence`**: Minimum confidence threshold (0.0-1.0, default 0.75 = 75%)
- **`remove_chinese`**: Remove Chinese email domains (true/false)
- **`deduplicate`**: Deduplicate by email address (true/false)

## Usage Examples

### Example 1: Round 2 Collection

```json
{
  "collection": {
    "round": 2,
    "output_dir": "data/arxiv/round2",
    "categories": [
      {
        "arxiv_category": "cs.LG",
        "short_name": "cs_lg",
        "years": [2024, 2025]
      },
      {
        "arxiv_category": "cs.CV",
        "short_name": "cs_cv",
        "years": [2024, 2025]
      }
    ]
  }
}
```

### Example 2: Round 3 with Different Categories

```json
{
  "collection": {
    "round": 3,
    "output_dir": "data/arxiv/round3",
    "categories": [
      {
        "arxiv_category": "cs.RO",
        "short_name": "cs_ro",
        "years": [2025]
      },
      {
        "arxiv_category": "eess.SY",
        "short_name": "eess_sy",
        "years": [2025]
      }
    ]
  }
}
```

### Example 3: Higher Confidence Threshold

```json
{
  "post_processing": {
    "min_confidence": 0.80,
    "remove_chinese": true,
    "deduplicate": true
  }
}
```

## Script Behavior

### Scripts that use config file:

1. **`2.1-collect_arxiv_papers.py`**
   - Reads `collection` section
   - Uses categories, years, round, output_dir, batch_size, rate_limit_delay

2. **`2.2-extract_emails_from_papers.py`**
   - Reads `email_extraction` section
   - Uses cookie_file, temp_dir, max_retries, rate_limit_delay_seconds

3. **`2.3-batch_extract_emails.py`**
   - Reads `collection` section for round number
   - Auto-detects round from config if `--round` not specified

4. **`2.4-process_arxiv_round.py`**
   - Reads `collection` section for round number
   - Reads `post_processing` section for min_confidence, remove_chinese, deduplicate
   - Auto-detects round and settings from config if not specified
   - Command-line arguments override config file settings

### Command-line overrides:

You can still override config settings via command-line:

```bash
# Override confidence threshold
python3.9 2.4-process_arxiv_round.py --round 2 --min-confidence 0.80

# Override Chinese email removal
python3.9 2.4-process_arxiv_round.py --round 2 --no-remove-chinese
```

## Notes

- If config file doesn't exist, scripts use default values
- Command-line arguments always override config file settings
- Config file must be valid JSON
- Comments (lines starting with `_`) are ignored by JSON parser but help documentation

