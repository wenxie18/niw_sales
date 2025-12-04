#!/usr/bin/env python3
"""
Batch process all arXiv paper CSVs to extract emails and match to authors.
"""

import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Categories and years to process
CATEGORIES = ['cs_ro', 'eess_sy', 'eess_sp', 'cs_lg', 'cs_cv']
YEARS = [2024, 2025]

def process_file(input_file: str, output_file: str) -> tuple[bool, bool]:
    """
    Process a single CSV file to extract emails.
    
    Returns:
        (success, should_continue): 
            - success: True if processing completed successfully
            - should_continue: False if hit CAPTCHA/rate limit and should stop batch
    """
    file_base = Path(input_file).stem
    log_file = f"{file_base}_processing.log"
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Starting: {Path(input_file).name} -> {Path(output_file).name}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"{'='*80}\n")
    
    cmd = [
        '/opt/homebrew/Caskroom/miniforge/base/bin/python3.9',
        '2.3-extract_emails.py',
        '--input', input_file,
        '--output', output_file
    ]
    
    try:
        # Run with log file
        with open(log_file, 'w') as log:
            result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
        
        # Check log for CAPTCHA/rate limit errors
        with open(log_file, 'r') as log:
            log_content = log.read()
            if 'CAPTCHA DETECTED' in log_content or 'STOPPING: 5 consecutive' in log_content:
                logger.error(f"⚠️  CAPTCHA/Rate limit detected in {Path(input_file).name}")
                logger.error(f"⚠️  STOPPING BATCH PROCESSING - refresh cookies and restart")
                logger.error(f"⚠️  Check log: {log_file}\n")
                return (False, False)  # Failed, and should stop batch
        
        logger.info(f"✓ Completed: {Path(output_file).name}")
        logger.info(f"  Log saved to: {log_file}\n")
        return (True, True)  # Success, continue
    except Exception as e:
        logger.error(f"✗ Failed: {Path(input_file).name}")
        logger.error(f"  Error: {e}")
        logger.error(f"  Check log: {log_file}\n")
        return (False, True)  # Failed, but can continue to next file

def main():
    data_dir = Path('data/arxiv')
    
    total_jobs = len(CATEGORIES) * len(YEARS)
    completed = 0
    failed = 0
    stopped_early = False
    
    logger.info(f"Starting batch email extraction for {total_jobs} files...")
    logger.info("="*80)
    
    for category in CATEGORIES:
        for year in YEARS:
            input_file = data_dir / f"{category}_{year}.csv"
            output_file = data_dir / f"{category}_{year}_email.csv"
            
            if not input_file.exists():
                logger.warning(f"Input file not found: {input_file}")
                failed += 1
                continue
            
            success, should_continue = process_file(str(input_file), str(output_file))
            
            if success:
                completed += 1
            else:
                failed += 1
            
            # If we hit CAPTCHA/rate limit, stop the entire batch
            if not should_continue:
                stopped_early = True
                logger.info(f"Progress: {completed + failed}/{total_jobs} ({completed} completed, {failed} failed)")
                logger.info("-"*80)
                logger.error("="*80)
                logger.error("⚠️  BATCH STOPPED DUE TO CAPTCHA/RATE LIMIT")
                logger.error("⚠️  To resume:")
                logger.error("⚠️  1. Export fresh cookies from browser")
                logger.error("⚠️  2. Save as arxiv.org_cookies.txt")
                logger.error("⚠️  3. Run: python3.9 2.4-batch_extract_emails.py")
                logger.error("="*80)
                break
            
            logger.info(f"Progress: {completed + failed}/{total_jobs} ({completed} completed, {failed} failed)")
            logger.info("-"*80)
        
        # Break outer loop too if stopped early
        if stopped_early:
            break
    
    if not stopped_early:
        logger.info("="*80)
        logger.info(f"Batch email extraction complete!")
        logger.info(f"  Total jobs: {total_jobs}")
        logger.info(f"  Completed: {completed}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"  Output directory: {data_dir}")

if __name__ == "__main__":
    main()

