#!/usr/bin/env python3
"""
Universal Email Post-Processing Pipeline
Works for ACL, arXiv, or any email collection CSV files.

Functions:
- Combine multiple email CSV files
- Deduplicate by email (keep most recent year)
- Filter by confidence threshold
- Remove Chinese email domains
- Generate summary statistics

Usage:
  # arXiv Round 1
  python email_postprocess.py --input "data/arxiv/round1/*_email.csv" --output data/arxiv/round1/processed --min-confidence 75 --remove-chinese
  
  # ACL
  python email_postprocess.py --input "data/acl/acl_*_email.csv" --output data/acl/processed --min-confidence 80
  
  # All combined
  python email_postprocess.py --input "data/**/*_email.csv" --output data/combined --min-confidence 75 --remove-chinese
"""

import argparse
import csv
import glob
import logging
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
    # arXiv format: https://arxiv.org/pdf/2501.00669.pdf
    if '/pdf/' in paper_url:
        arxiv_id = paper_url.split('/pdf/')[-1].replace('.pdf', '')
        if len(arxiv_id) >= 2 and arxiv_id[:2].isdigit():
            year_code = int(arxiv_id[:2])
            return 2000 + year_code
    # ACL or other formats - try to parse from title or URL
    # For now return 0 (will keep first occurrence)
    return 0

def combine_csv_files(input_pattern: str, deduplicate: bool = True) -> List[Dict]:
    """
    Combine multiple CSV files matching the pattern.
    If deduplicate=True, keep only one record per email (most recent year).
    """
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
                            # Get year
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
    
    # Calculate confidence percentiles
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

def save_summary(stats: Dict, output_file: str):
    """Save statistics summary to text file."""
    with open(output_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("EMAIL COLLECTION SUMMARY\n")
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

def main():
    parser = argparse.ArgumentParser(
        description='Universal Email Post-Processing Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # arXiv Round 1
  python email_postprocess.py --input "data/arxiv/round1/*_email.csv" --output data/arxiv/round1/processed --min-confidence 75 --remove-chinese
  
  # ACL
  python email_postprocess.py --input "data/acl/acl_*_email.csv" --output data/acl/processed --min-confidence 80
        """
    )
    
    parser.add_argument('--input', required=True,
                        help='Input CSV pattern (e.g., "data/arxiv/round1/*_email.csv")')
    parser.add_argument('--output', required=True,
                        help='Output directory')
    parser.add_argument('--min-confidence', type=float, default=0.75,
                        help='Minimum confidence threshold (0-1, default: 0.75)')
    parser.add_argument('--remove-chinese', action='store_true',
                        help='Remove Chinese email domains')
    parser.add_argument('--no-deduplicate', action='store_true',
                        help='Disable email deduplication (default: deduplicate)')
    parser.add_argument('--output-name', default='processed',
                        help='Output file prefix (default: processed)')
    
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("EMAIL POST-PROCESSING PIPELINE")
    logger.info("="*80)
    logger.info(f"Input pattern: {args.input}")
    logger.info(f"Output dir: {args.output}")
    logger.info(f"Min confidence: {args.min_confidence:.0%}")
    logger.info(f"Remove Chinese: {args.remove_chinese}")
    logger.info(f"Deduplicate: {not args.no_deduplicate}")
    logger.info("="*80)
    
    # Step 1: Combine CSV files
    records = combine_csv_files(args.input, deduplicate=not args.no_deduplicate)
    
    if not records:
        logger.error("No records found!")
        return
    
    logger.info(f"\nStarting with {len(records):,} records")
    
    # Step 2: Filter by confidence
    records = filter_by_confidence(records, args.min_confidence)
    
    # Step 3: Remove Chinese emails (if requested)
    if args.remove_chinese:
        records = remove_chinese_emails(records)
    
    # Step 4: Generate statistics
    stats = generate_statistics(records)
    
    # Step 5: Save outputs
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_csv = output_dir / f"{args.output_name}.csv"
    output_summary = output_dir / f"{args.output_name}_summary.txt"
    
    save_csv(records, str(output_csv))
    save_summary(stats, str(output_summary))
    
    # Final summary
    logger.info("\n" + "="*80)
    logger.info("PROCESSING COMPLETE!")
    logger.info("="*80)
    logger.info(f"Final records: {len(records):,}")
    logger.info(f"Unique emails: {stats['unique_emails']:,}")
    logger.info(f"Output CSV: {output_csv}")
    logger.info(f"Summary: {output_summary}")
    logger.info("="*80)

if __name__ == "__main__":
    main()

