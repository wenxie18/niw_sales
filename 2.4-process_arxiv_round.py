#!/usr/bin/env python3
"""
Universal arXiv Round Processing Script

This script processes any round of arXiv email collection by:
1. Combining and post-processing email CSV files in the round folder
2. Removing duplicates from ACL and all prior rounds
3. Creating final output files ready for email campaigns

Usage:
    # Auto-detect round from config file (recommended)
    python3.9 2.4-process_arxiv_round.py
    
    # Manually specify round (overrides config)
    python3.9 2.4-process_arxiv_round.py --round 2
    
    # Process with custom confidence threshold (overrides config)
    python3.9 2.4-process_arxiv_round.py --round 3 --min-confidence 0.80

The script automatically:
- Finds all *_email.csv files in data/arxiv/round{N}/
- Combines, deduplicates, filters by confidence, removes Chinese emails
- Excludes emails from ACL (data/acl/acl_high_confidence.csv)
- Excludes emails from all prior rounds (round1, round2, ..., round{N-1})
- Creates final output: arxiv_high_confidence_non_chinese_no_acl_no_prior_rounds.csv
"""

import argparse
import csv
import glob
import logging
import json
import pandas as pd
import statistics
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Set

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chinese email domains to filter
CHINESE_DOMAINS = [
    '.edu.cn', '.ac.cn', '.org.cn', '.gov.cn', '.net.cn', '.com.cn', '.cn',
    '@163.com', '@126.com', '@qq.com', '@sina.com', '@sohu.com', 
    '@yeah.net', '@139.com', '@aliyun.com'
]

def is_chinese_email(email: str) -> bool:
    """Check if email is from a Chinese domain."""
    email_lower = email.lower().strip()
    return any(domain in email_lower for domain in CHINESE_DOMAINS)

def parse_confidence(conf_str: str) -> float:
    """Parse confidence string to float (e.g., '95%' -> 0.95)."""
    try:
        if isinstance(conf_str, str):
            return float(conf_str.strip('%')) / 100.0
        return float(conf_str)
    except:
        return 0.0

def extract_year_from_url(paper_url: str) -> int:
    """Extract year from arXiv paper URL or return 0 for non-arXiv."""
    if '/pdf/' in paper_url:
        arxiv_id = paper_url.split('/pdf/')[-1].replace('.pdf', '')
        if len(arxiv_id) >= 2 and arxiv_id[:2].isdigit():
            year_code = int(arxiv_id[:2])
            return 2000 + year_code
    return 0

def combine_csv_files(input_pattern: str, deduplicate: bool = True) -> List[Dict]:
    """Combine multiple CSV files matching the pattern."""
    logger.info(f"Finding files matching: {input_pattern}")
    
    csv_files = glob.glob(input_pattern, recursive=True)
    if not csv_files:
        logger.error(f"No files found matching pattern: {input_pattern}")
        return []
    
    logger.info(f"Found {len(csv_files)} CSV files:")
    for f in csv_files:
        logger.info(f"  • {f}")
    
    all_records = []
    email_to_record = {}  # For deduplication
    
    for csv_file in csv_files:
        logger.info(f"\nReading {csv_file}...")
        
        try:
            with open(csv_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read().replace('\x00', '')
                reader = csv.DictReader(content.splitlines())
                
                count = 0
                for row in reader:
                    count += 1
                    
                    if deduplicate:
                        email = row.get('Email', '').strip().lower()
                        if email:
                            paper_url = row.get('Paper URL', '')
                            year = extract_year_from_url(paper_url)
                            
                            # Keep record with most recent year
                            if email not in email_to_record:
                                email_to_record[email] = (year, row)
                            else:
                                existing_year = email_to_record[email][0]
                                if year > existing_year:
                                    email_to_record[email] = (year, row)
                    else:
                        all_records.append(row)
                
                logger.info(f"  Loaded {count:,} records")
                
        except Exception as e:
            logger.error(f"  Error reading {csv_file}: {e}")
            continue
    
    if deduplicate:
        all_records = [record for year, record in email_to_record.values()]
        logger.info(f"\n✓ Combined: {len(all_records):,} unique emails after deduplication")
    else:
        logger.info(f"\n✓ Combined: {len(all_records):,} total records (no deduplication)")
    
    return all_records

def filter_by_confidence(records: List[Dict], min_confidence: float) -> List[Dict]:
    """Filter records by minimum confidence threshold."""
    logger.info(f"\nFiltering by confidence >= {min_confidence:.0%}...")
    
    filtered = []
    for record in records:
        conf_str = record.get('Confidence', '0%')
        conf = parse_confidence(conf_str)
        
        if conf >= min_confidence:
            filtered.append(record)
    
    removed = len(records) - len(filtered)
    logger.info(f"  Kept: {len(filtered):,} records")
    logger.info(f"  Removed: {removed:,} records ({100*removed/len(records):.1f}%)")
    
    return filtered

def remove_chinese_emails(records: List[Dict]) -> List[Dict]:
    """Remove records with Chinese email domains."""
    logger.info(f"\nRemoving Chinese emails...")
    
    non_chinese = []
    chinese_count = 0
    
    for record in records:
        email = record.get('Email', '').strip()
        
        if is_chinese_email(email):
            chinese_count += 1
        else:
            non_chinese.append(record)
    
    logger.info(f"  Kept: {len(non_chinese):,} non-Chinese emails")
    logger.info(f"  Removed: {chinese_count:,} Chinese emails ({100*chinese_count/len(records):.1f}%)")
    
    return non_chinese

def load_prior_emails(round_num: int, base_dir: Path) -> Set[str]:
    """
    Load emails from ACL and all prior rounds.
    Returns a set of email addresses (lowercase, stripped).
    """
    prior_emails = set()
    
    # Load ACL emails
    acl_file = base_dir / 'acl' / 'acl_high_confidence.csv'
    if acl_file.exists():
        logger.info(f"\n📂 Loading ACL emails: {acl_file}")
        try:
            acl_df = pd.read_csv(acl_file, encoding='utf-8')
            acl_emails = set(acl_df['Email'].str.lower().str.strip())
            prior_emails.update(acl_emails)
            logger.info(f"   ✓ Loaded {len(acl_df):,} ACL records")
            logger.info(f"   ✓ Found {len(acl_emails):,} unique ACL emails")
        except Exception as e:
            logger.warning(f"   ⚠️  Error loading ACL file: {e}")
    else:
        logger.warning(f"   ⚠️  ACL file not found: {acl_file}")
    
    # Load emails from all prior rounds
    for prev_round in range(1, round_num):
        prev_round_dir = base_dir / 'arxiv' / f'round{prev_round}'
        
        # Try to find the final processed file from previous round
        # Priority order: new naming > old naming > intermediate
        possible_files = [
            prev_round_dir / 'arxiv_high_confidence_non_chinese_no_acl_no_prior_rounds.csv',
            prev_round_dir / 'arxiv_high_confidence_non_chinese_no_acl_no_round1.csv',  # Round 2 specific
            prev_round_dir / 'arxiv_high_confidence_non_chinese_no_acl.csv',  # Round 1 final
            prev_round_dir / 'arxiv_high_confidence_non_chinese.csv',  # Intermediate
        ]
        
        final_file = None
        for possible_file in possible_files:
            if possible_file.exists():
                final_file = possible_file
                break
        
        if final_file:
            logger.info(f"\n📂 Loading Round {prev_round} emails: {final_file}")
            try:
                prev_df = pd.read_csv(final_file, encoding='utf-8')
                prev_emails = set(prev_df['Email'].str.lower().str.strip())
                prior_emails.update(prev_emails)
                logger.info(f"   ✓ Loaded {len(prev_df):,} Round {prev_round} records")
                logger.info(f"   ✓ Found {len(prev_emails):,} unique Round {prev_round} emails")
            except Exception as e:
                logger.warning(f"   ⚠️  Error loading Round {prev_round} file: {e}")
        else:
            logger.warning(f"   ⚠️  Round {prev_round} final file not found in {prev_round_dir}")
    
    return prior_emails

def remove_prior_round_emails(records: List[Dict], prior_emails: Set[str]) -> List[Dict]:
    """Remove records with emails that exist in prior rounds."""
    logger.info(f"\n🔍 Removing emails from prior rounds...")
    
    prior_emails_lower = {email.lower().strip() for email in prior_emails}
    
    filtered = []
    removed = 0
    
    for record in records:
        email = record.get('Email', '').strip().lower()
        if email not in prior_emails_lower:
            filtered.append(record)
        else:
            removed += 1
    
    logger.info(f"  Kept: {len(filtered):,} new emails")
    logger.info(f"  Removed: {removed:,} duplicate emails from prior rounds ({100*removed/len(records):.1f}%)")
    
    return filtered

def generate_statistics(records: List[Dict]) -> Dict:
    """Generate comprehensive statistics."""
    logger.info(f"\nGenerating statistics...")
    
    if not records:
        return {}
    
    unique_emails = set()
    unique_papers = set()
    unique_authors = set()
    confidence_scores = []
    email_domains = Counter()
    year_stats = defaultdict(int)
    
    for record in records:
        email = record.get('Email', '').strip().lower()
        paper_url = record.get('Paper URL', '').strip()
        author = record.get('Author', '').strip()
        conf_str = record.get('Confidence', '0%')
        
        conf = parse_confidence(conf_str)
        confidence_scores.append(conf)
        
        if email:
            unique_emails.add(email)
            if '@' in email:
                domain = email.split('@')[1]
                email_domains[domain] += 1
        
        if paper_url:
            unique_papers.add(paper_url)
            year = extract_year_from_url(paper_url)
            if year > 0:
                year_stats[year] += 1
        
        if author:
            unique_authors.add(author)
    
    conf_sorted = sorted(confidence_scores)
    percentiles = {
        'min': min(confidence_scores) if confidence_scores else 0,
        'p25': conf_sorted[len(conf_sorted)//4] if conf_sorted else 0,
        'p50': conf_sorted[len(conf_sorted)//2] if conf_sorted else 0,
        'p75': conf_sorted[3*len(conf_sorted)//4] if conf_sorted else 0,
        'p90': conf_sorted[9*len(conf_sorted)//10] if conf_sorted else 0,
        'p95': conf_sorted[95*len(conf_sorted)//100] if conf_sorted else 0,
        'max': max(confidence_scores) if confidence_scores else 0,
        'mean': statistics.mean(confidence_scores) if confidence_scores else 0,
    }
    
    stats = {
        'total_records': len(records),
        'unique_emails': len(unique_emails),
        'unique_papers': len(unique_papers),
        'unique_authors': len(unique_authors),
        'confidence_percentiles': percentiles,
        'top_domains': email_domains.most_common(20),
        'year_distribution': dict(year_stats),
    }
    
    return stats

def save_csv(records: List[Dict], output_file: str):
    """Save records to CSV file."""
    if not records:
        logger.warning("No records to save")
        return
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = list(records[0].keys())
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record)
    
    logger.info(f"✓ Saved {len(records):,} records to {output_file}")

def save_summary(stats: Dict, output_file: str, round_num: int):
    """Save statistics summary to text file."""
    with open(output_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write(f"ROUND {round_num} EMAIL COLLECTION SUMMARY\n")
        f.write("="*80 + "\n\n")
        
        f.write("## OVERALL STATISTICS\n")
        f.write("-"*80 + "\n")
        f.write(f"Total Records:           {stats['total_records']:>15,}\n")
        f.write(f"Unique Emails:           {stats['unique_emails']:>15,}\n")
        f.write(f"Unique Papers:           {stats['unique_papers']:>15,}\n")
        f.write(f"Unique Authors:          {stats['unique_authors']:>15,}\n")
        f.write("\n")
        
        perc = stats['confidence_percentiles']
        f.write("## CONFIDENCE SCORE STATISTICS\n")
        f.write("-"*80 + "\n")
        f.write(f"Mean:                    {perc['mean']:>15.1%}\n")
        f.write(f"25th Percentile:         {perc['p25']:>15.1%}\n")
        f.write(f"50th Percentile:         {perc['p50']:>15.1%}\n")
        f.write(f"75th Percentile:         {perc['p75']:>15.1%}\n")
        f.write(f"95th Percentile:         {perc['p95']:>15.1%}\n")
        f.write("\n")
        
        if stats['year_distribution']:
            f.write("## YEAR DISTRIBUTION\n")
            f.write("-"*80 + "\n")
            for year in sorted(stats['year_distribution'].keys()):
                count = stats['year_distribution'][year]
                f.write(f"{year}:                    {count:>15,}\n")
            f.write("\n")
        
        f.write("## TOP 10 EMAIL DOMAINS\n")
        f.write("-"*80 + "\n")
        for i, (domain, count) in enumerate(stats['top_domains'][:10], 1):
            f.write(f"{i:2}. {domain:<40} {count:>10,}\n")
        f.write("\n")
        
        f.write("="*80 + "\n")
    
    logger.info(f"✓ Summary saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description='Universal arXiv Round Processing Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect round from config file (recommended)
  python3.9 2.4-process_arxiv_round.py
  
  # Manually specify round (overrides config)
  python3.9 2.4-process_arxiv_round.py --round 2
  
  # Process with custom confidence threshold (overrides config)
  python3.9 2.4-process_arxiv_round.py --round 3 --min-confidence 0.80
        """
    )
    
    parser.add_argument('--round', type=int, default=None,
                       help='Round number to process (if not specified, reads from config file)')
    parser.add_argument('--min-confidence', type=float, default=None,
                       help='Minimum confidence threshold (0-1, if not specified, reads from config)')
    parser.add_argument('--data-dir', type=str, default='data',
                       help='Base data directory (default: data)')
    parser.add_argument('--no-remove-chinese', action='store_true',
                       help='Do not remove Chinese email domains (default: remove)')
    parser.add_argument('--no-deduplicate', action='store_true',
                       help='Disable email deduplication (default: deduplicate)')
    
    args = parser.parse_args()
    
    # Load config file
    config_file = Path('arxiv_collection_config.json')
    config = None
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            logger.warning(f"Error loading config file: {e}")
    
    # Determine round number: command line > config > error
    if args.round is not None:
        round_num = args.round
        logger.info(f"📋 Using round {round_num} from command line")
    elif config and 'collection' in config:
        round_num = config['collection'].get('round', None)
        if round_num is None:
            logger.error("Round number not specified and not found in config file. Use --round N")
            return
        logger.info(f"📋 Using round {round_num} from config file")
    else:
        logger.error("Round number not specified and config file not found. Use --round N")
        return
    
    # Determine min_confidence: command line > config > default
    if args.min_confidence is not None:
        min_confidence = args.min_confidence
    elif config and 'post_processing' in config:
        min_confidence = config['post_processing'].get('min_confidence', 0.75)
    else:
        min_confidence = 0.75
    
    # Determine remove_chinese and deduplicate: command line flags > config > default
    if args.no_remove_chinese:
        remove_chinese = False
    elif config and 'post_processing' in config:
        remove_chinese = config['post_processing'].get('remove_chinese', True)
    else:
        remove_chinese = True
    
    if args.no_deduplicate:
        deduplicate = False
    elif config and 'post_processing' in config:
        deduplicate = config['post_processing'].get('deduplicate', True)
    else:
        deduplicate = True
    base_dir = Path(args.data_dir)
    round_dir = base_dir / 'arxiv' / f'round{round_num}'
    
    logger.info("="*80)
    logger.info(f"ARXIV ROUND {round_num} PROCESSING")
    logger.info("="*80)
    logger.info(f"Round directory: {round_dir}")
    logger.info(f"Min confidence: {min_confidence:.0%}")
    logger.info(f"Remove Chinese: {remove_chinese}")
    logger.info(f"Deduplicate: {deduplicate}")
    if config:
        logger.info(f"Config file: arxiv_collection_config.json")
    logger.info("="*80)
    
    # Check if round directory exists
    if not round_dir.exists():
        logger.error(f"Round directory does not exist: {round_dir}")
        return
    
    # Step 1: Combine and post-process email CSV files
    input_pattern = str(round_dir / '*_email.csv')
    records = combine_csv_files(input_pattern, deduplicate=deduplicate)
    
    if not records:
        logger.error("No records found!")
        return
    
    logger.info(f"\nStarting with {len(records):,} records")
    
    # Step 2: Filter by confidence
    records = filter_by_confidence(records, min_confidence)
    
    # Step 3: Remove Chinese emails (if requested)
    if remove_chinese:
        records = remove_chinese_emails(records)
    
    # Save intermediate file (before excluding prior rounds)
    intermediate_file = round_dir / 'arxiv_high_confidence_non_chinese.csv'
    save_csv(records, str(intermediate_file))
    logger.info(f"\n💾 Intermediate file saved: {intermediate_file}")
    
    # Step 4: Load emails from prior rounds (ACL + all previous rounds)
    prior_emails = load_prior_emails(round_num, base_dir)
    logger.info(f"\n📊 Total prior emails to exclude: {len(prior_emails):,}")
    
    # Step 5: Remove prior round emails
    records = remove_prior_round_emails(records, prior_emails)
    
    # Step 6: Generate statistics
    stats = generate_statistics(records)
    
    # Step 7: Save final outputs
    final_csv = round_dir / 'arxiv_high_confidence_non_chinese_no_acl_no_prior_rounds.csv'
    summary_txt = round_dir / f'ROUND{round_num}_EMAIL_SUMMARY.txt'
    
    save_csv(records, str(final_csv))
    save_summary(stats, str(summary_txt), round_num)
    
    # Final summary
    logger.info("\n" + "="*80)
    logger.info("PROCESSING COMPLETE!")
    logger.info("="*80)
    logger.info(f"Final records: {len(records):,}")
    logger.info(f"Unique emails: {stats['unique_emails']:,}")
    logger.info(f"Final CSV: {final_csv}")
    logger.info(f"Summary: {summary_txt}")
    logger.info("="*80)
    logger.info(f"\n✅ Use this file for email campaigns: {final_csv}")

if __name__ == "__main__":
    main()

