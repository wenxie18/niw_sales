#!/usr/bin/env python3
"""
Batch extract emails for Round 2 files (NEW papers only).
Uses the existing 2.3-extract_emails.py script for each file.
"""

import subprocess
import logging
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_emails_for_file(input_csv: str, output_csv: str, log_file: str) -> bool:
    """
    Run email extraction for a single CSV file.
    
    Returns True if successful, False otherwise.
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
        '2.3-extract_emails.py',
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
        
        # Check if the process completed successfully
        if result.returncode == 0:
            logger.info(f"✓ {category_name} completed successfully")
            return True
        else:
            logger.error(f"✗ {category_name} failed with exit code {result.returncode}")
            
            # Check log for CAPTCHA
            with open(log_file, 'r') as log_f:
                log_content = log_f.read()
                if 'CAPTCHA' in log_content or '429' in log_content:
                    logger.error("CAPTCHA detected! Stopping batch process.")
                    raise Exception("CAPTCHA block detected - stopping")
            
            return False
            
    except Exception as e:
        logger.error(f"✗ {category_name} error: {e}")
        raise

def main():
    """Main batch processing function for Round 2."""
    
    round2_dir = Path('data/arxiv/round2')
    logs_dir = Path('data/arxiv/logs')
    
    # Get all Round 2 CSV files (excluding any _email.csv files)
    csv_files = sorted([f for f in round2_dir.glob('*.csv') if '_email.csv' not in f.name])
    
    if not csv_files:
        logger.error(f"No CSV files found in {round2_dir}")
        return
    
    logger.info("="*80)
    logger.info("ROUND 2 EMAIL EXTRACTION - BATCH PROCESSING")
    logger.info("="*80)
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
    
    start_time = time.time()
    
    for i, input_csv in enumerate(csv_files, 1):
        category_name = input_csv.stem
        output_csv = round2_dir / f"{category_name}_email.csv"
        log_file = logs_dir / f"{category_name}_round2_processing.log"
        
        logger.info(f"\n[{i}/{total_files}] Processing {category_name}...")
        
        try:
            success = extract_emails_for_file(str(input_csv), str(output_csv), str(log_file))
            
            if success:
                completed += 1
            else:
                failed += 1
                
        except Exception as e:
            logger.error(f"Critical error: {e}")
            failed += 1
            logger.error("Stopping batch process due to error")
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
        for f in sorted(round2_dir.glob('*_email.csv')):
            logger.info(f"  • {f.name}")
        
        logger.info("\nNext steps:")
        logger.info("1. Combine Round 2 email results")
        logger.info("2. Merge with Round 1 results")
        logger.info("3. Deduplicate by email")
        logger.info("4. Filter by confidence threshold")

if __name__ == "__main__":
    main()

