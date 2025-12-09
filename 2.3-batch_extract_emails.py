#!/usr/bin/env python3
"""
Universal batch email extraction script.
Works for any round by automatically finding CSV files in the specified directory.

Usage:
    # Auto-detect round from config file (recommended)
    python3.9 2.3-batch_extract_emails.py
    
    # Manually specify round (overrides config)
    python3.9 2.3-batch_extract_emails.py --round 2
    
    # Custom directory (overrides round)
    python3.9 2.3-batch_extract_emails.py --input-dir data/arxiv/round2
"""

import subprocess
import logging
import time
import argparse
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config(config_file: str = 'arxiv_collection_config.json'):
    """Load configuration from JSON file."""
    config_path = Path(config_file)
    
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Error loading config file: {e}")
        return None

def extract_emails_for_file(input_csv: str, output_csv: str, log_file: str) -> tuple[bool, bool]:
    """
    Run email extraction for a single CSV file.
    
    Returns:
        (success, should_continue): 
            - success: True if processing completed successfully
            - should_continue: False if hit CAPTCHA/rate limit and should stop batch
    """
    category_name = Path(input_csv).stem
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Processing {category_name}...")
    logger.info(f"{'='*80}")
    logger.info(f"Input:  {input_csv}")
    logger.info(f"Output: {output_csv}")
    logger.info(f"Log:    {log_file}")
    
    cmd = [
        '/opt/homebrew/Caskroom/miniforge/base/bin/python3.9',
        '2.2-extract_emails_from_papers.py',
        '--input', input_csv,
        '--output', output_csv
    ]
    
    try:
        with open(log_file, 'w') as log_f:
            result = subprocess.run(
                cmd,
                stdout=log_f,
                stderr=subprocess.STDOUT,
                text=True,
                check=False
            )
        
        # Check log for CAPTCHA/rate limit errors
        with open(log_file, 'r') as log_f:
            log_content = log_f.read()
            if 'CAPTCHA DETECTED' in log_content or 'STOPPING: 5 consecutive' in log_content or '429' in log_content:
                logger.error(f"⚠️  CAPTCHA/Rate limit detected in {category_name}")
                logger.error(f"⚠️  STOPPING BATCH PROCESSING - refresh cookies and restart")
                logger.error(f"⚠️  Check log: {log_file}\n")
                return (False, False)  # Failed, and should stop batch
        
        if result.returncode == 0:
            logger.info(f"✓ {category_name} completed successfully")
            return (True, True)  # Success, continue
        else:
            logger.error(f"✗ {category_name} failed with exit code {result.returncode}")
            return (False, True)  # Failed, but can continue to next file
            
    except Exception as e:
        logger.error(f"✗ {category_name} error: {e}")
        logger.error(f"  Check log: {log_file}\n")
        return (False, True)  # Failed, but can continue to next file

def main():
    parser = argparse.ArgumentParser(
        description='Universal batch email extraction for arXiv papers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect round from config file (recommended)
  python3.9 2.3-batch_extract_emails.py
  
  # Manually specify round (overrides config)
  python3.9 2.3-batch_extract_emails.py --round 2
  
  # Custom directory (overrides round)
  python3.9 2.3-batch_extract_emails.py --input-dir data/arxiv/round2
        """
    )
    
    parser.add_argument('--round', type=int, default=None,
                       help='Round number (if not specified, reads from config file)')
    parser.add_argument('--input-dir', type=str, default=None,
                       help='Custom input directory (overrides --round)')
    
    args = parser.parse_args()
    
    # If round not specified, try to read from config
    if args.round is None and args.input_dir is None:
        config = load_config()
        if config and 'collection' in config:
            args.round = config['collection'].get('round', 1)
            logger.info(f"📋 Using round {args.round} from config file")
        else:
            args.round = 1
            logger.info(f"📋 No config found, using default round {args.round}")
    
    # Determine input directory
    if args.input_dir:
        input_dir = Path(args.input_dir)
    else:
        if args.round == 1:
            input_dir = Path('data/arxiv')
        else:
            input_dir = Path(f'data/arxiv/round{args.round}')
    
    logs_dir = Path('data/arxiv/logs')
    
    # Get all CSV files (excluding any _email.csv files)
    csv_files = sorted([f for f in input_dir.glob('*.csv') if '_email.csv' not in f.name])
    
    if not csv_files:
        logger.error(f"No CSV files found in {input_dir}")
        logger.error(f"Expected files like: {{category}}_{{year}}.csv")
        return
    
    logger.info("="*80)
    logger.info(f"BATCH EMAIL EXTRACTION - Round {args.round if not args.input_dir else 'Custom'}")
    logger.info("="*80)
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Found {len(csv_files)} files to process:")
    for f in csv_files:
        logger.info(f"  • {f.name}")
    logger.info("="*80)
    
    # Ensure logs directory exists
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each file
    total_files = len(csv_files)
    completed = 0
    failed = 0
    stopped_early = False
    
    start_time = time.time()
    
    for i, input_csv in enumerate(csv_files, 1):
        category_name = input_csv.stem
        output_csv = input_dir / f"{category_name}_email.csv"
        
        # Log file naming: include round number if not round 1
        if args.round == 1:
            log_file = logs_dir / f"{category_name}_processing.log"
        else:
            log_file = logs_dir / f"{category_name}_round{args.round}_processing.log"
        
        logger.info(f"\n[{i}/{total_files}] Processing {category_name}...")
        
        success, should_continue = extract_emails_for_file(str(input_csv), str(output_csv), str(log_file))
        
        if success:
            completed += 1
        else:
            failed += 1
        
        # If we hit CAPTCHA/rate limit, stop the entire batch
        if not should_continue:
            stopped_early = True
            logger.error("="*80)
            logger.error("⚠️  BATCH STOPPED DUE TO CAPTCHA/RATE LIMIT")
            logger.error("⚠️  To resume:")
            logger.error("⚠️  1. Export fresh cookies from browser")
            logger.error("⚠️  2. Save as arxiv.org_cookies.txt")
            logger.error(f"⚠️  3. Run: python3.9 2.3-batch_extract_emails.py --round {args.round}")
            logger.error("="*80)
            break
    
    # Summary
    elapsed_time = time.time() - start_time
    
    logger.info("\n" + "="*80)
    logger.info("BATCH PROCESSING COMPLETE")
    logger.info("="*80)
    logger.info(f"Total files:        {total_files}")
    logger.info(f"Completed:          {completed}")
    logger.info(f"Failed:             {failed}")
    logger.info(f"Time elapsed:       {elapsed_time/60:.1f} minutes")
    logger.info("="*80)
    
    if completed > 0:
        logger.info("\nOutput files:")
        for f in sorted(input_dir.glob('*_email.csv')):
            logger.info(f"  • {f.name}")
        
        logger.info("\nNext steps:")
        logger.info(f"1. Post-process emails: python3.9 2.4-process_arxiv_round.py --round {args.round}")

if __name__ == "__main__":
    main()
