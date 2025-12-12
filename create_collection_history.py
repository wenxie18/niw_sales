#!/usr/bin/env python3
"""
Create arXiv Collection History File

Scans existing round1 and round2 directories to create a simple history JSON file
that tracks which category+year combinations have already been collected.
Format: {category: {year: {stats}}}
"""

import csv
import json
from pathlib import Path
import re

def count_papers_and_authors(csv_file):
    """Count papers and authors in a CSV file."""
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            papers = list(reader)
            paper_count = len(papers)
            author_count = sum(int(p.get('num_authors', 0) or 0) for p in papers)
            return paper_count, author_count
    except Exception as e:
        print(f"  Error reading {csv_file}: {e}")
        return 0, 0

def count_emails(email_file):
    """Count emails in an email CSV file."""
    try:
        with open(email_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            emails = list(reader)
            return len(emails)
    except:
        return 0

def parse_filename(filename):
    """Parse category_short_year.csv format."""
    # Match pattern like cs_lg_2024.csv
    match = re.match(r'^([a-z_]+)_(\d{4})\.csv$', filename)
    if match:
        return match.group(1), int(match.group(2))
    return None, None

def main():
    history = {}
    
    # Process Round 1
    round1_dir = Path('data/arxiv/round1')
    if round1_dir.exists():
        print("Processing Round 1...")
        for csv_file in sorted(round1_dir.glob('*.csv')):
            if '_email' in csv_file.name or 'combined' in csv_file.name or 'high_confidence' in csv_file.name:
                continue
            
            category_short, year = parse_filename(csv_file.name)
            if not category_short or not year:
                continue
            
            print(f"  Found: {category_short} {year}")
            paper_count, author_count = count_papers_and_authors(csv_file)
            
            email_file = round1_dir / f'{category_short}_{year}_email.csv'
            email_count = count_emails(email_file)
            
            # Initialize category if needed
            if category_short not in history:
                history[category_short] = {}
            
            # Initialize year if needed
            year_str = str(year)
            if year_str not in history[category_short]:
                history[category_short][year_str] = {
                    'papers_collected': 0,
                    'authors_collected': 0,
                    'emails_collected': 0,
                    'rounds': [],
                    'last_collection_date': '2024-12-01T00:00:00'
                }
            
            # Add stats (sum them up)
            history[category_short][year_str]['papers_collected'] += paper_count
            history[category_short][year_str]['authors_collected'] += author_count
            history[category_short][year_str]['emails_collected'] = max(
                history[category_short][year_str]['emails_collected'],
                email_count  # Keep max email count
            )
            if 1 not in history[category_short][year_str]['rounds']:
                history[category_short][year_str]['rounds'].append(1)
    
    # Process Round 2
    round2_dir = Path('data/arxiv/round2')
    if round2_dir.exists():
        print("\nProcessing Round 2...")
        for csv_file in sorted(round2_dir.glob('*.csv')):
            if '_email' in csv_file.name or 'high_confidence' in csv_file.name:
                continue
            
            category_short, year = parse_filename(csv_file.name)
            if not category_short or not year:
                continue
            
            print(f"  Found: {category_short} {year}")
            paper_count, author_count = count_papers_and_authors(csv_file)
            
            email_file = round2_dir / f'{category_short}_{year}_email.csv'
            email_count = count_emails(email_file)
            
            # Initialize category if needed
            if category_short not in history:
                history[category_short] = {}
            
            # Initialize year if needed
            year_str = str(year)
            if year_str not in history[category_short]:
                history[category_short][year_str] = {
                    'papers_collected': 0,
                    'authors_collected': 0,
                    'emails_collected': 0,
                    'rounds': [],
                    'last_collection_date': '2024-12-10T00:00:00'
                }
            
            # Add stats (sum them up)
            history[category_short][year_str]['papers_collected'] += paper_count
            history[category_short][year_str]['authors_collected'] += author_count
            history[category_short][year_str]['emails_collected'] = max(
                history[category_short][year_str]['emails_collected'],
                email_count  # Keep max email count
            )
            if 2 not in history[category_short][year_str]['rounds']:
                history[category_short][year_str]['rounds'].append(2)
            history[category_short][year_str]['last_collection_date'] = '2024-12-10T00:00:00'
    
    # Add ACL as a category
    acl_dir = Path('data/acl')
    if acl_dir.exists():
        print("\nProcessing ACL data...")
        history['acl'] = {
            'all': {
                'papers_collected': 0,  # Can be calculated if needed
                'authors_collected': 0,
                'emails_collected': 0,
                'rounds': ['acl'],
                'last_collection_date': '2024-11-14T00:00:00',
                'note': 'ACL papers collected separately'
            }
        }
    
    # Save to JSON
    output_file = Path('arxiv_collection_history.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ History file created: {output_file}")
    print(f"  Total categories: {len(history)}")
    
    # Print summary
    print("\nSummary:")
    for category in sorted(history.keys()):
        if category == 'acl':
            print(f"  {category}: collected separately")
        else:
            years = sorted(history[category].keys())
            print(f"  {category}: {len(years)} years ({', '.join(years)})")

if __name__ == "__main__":
    main()
