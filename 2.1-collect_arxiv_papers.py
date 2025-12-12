#!/usr/bin/env python3
"""
arXiv Paper Collection Script

Collects papers from arXiv by category and year using monthly queries to bypass the 10,000 offset limit.
Configuration is loaded from arxiv_collection_config.json.

Usage:
    python3.9 2.1-collect_arxiv_papers.py

The script reads collection parameters from arxiv_collection_config.json:
- Round number
- Categories and years
- Output directory
- Batch size and rate limit delays
"""

import requests
import xml.etree.ElementTree as ET
import csv
import time
import logging
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_month_days(year: int, month: int) -> int:
    """Get the last day of a given month."""
    if month == 2:
        # Leap year check
        return 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28
    elif month in [4, 6, 9, 11]:
        return 30
    else:
        return 31

def query_month_papers(category: str, year: int, month: int, batch_size: int = 1000, rate_limit_delay: float = 3.0) -> List[Dict]:
    """
    Query arXiv API for all papers in a specific category/year/month.
    
    Args:
        category: arXiv category (e.g., 'cs.LG')
        year: Year to query
        month: Month (1-12)
        batch_size: Results per API call (max 2000, default 1000)
    
    Returns:
        List of papers for that month
    """
    papers = []
    start = 0
    
    # arXiv API namespace
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom',
        'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'
    }
    
    # Date range for the month
    last_day = get_month_days(year, month)
    date_start = f"{year}{month:02d}01"
    date_end = f"{year}{month:02d}{last_day}"
    
    query = f"cat:{category}+AND+submittedDate:[{date_start}+TO+{date_end}]"
    
    # First call to get total count
    url = f"http://export.arxiv.org/api/query?search_query={query}&start=0&max_results=1"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        
        total_elem = root.find('opensearch:totalResults', ns)
        total_available = int(total_elem.text) if total_elem is not None else 0
        
        if total_available == 0:
            return []
        
        logger.info(f"    Month {month:02d}/{year}: {total_available:,} papers to collect")
        
        # Warn if approaching limit
        if total_available > 9000:
            logger.warning(f"    ⚠️  Month has {total_available:,} papers (close to 10k limit!)")
        
    except Exception as e:
        logger.error(f"    Error getting count for month {month}: {e}")
        return []
    
    # Now collect all papers for this month
    consecutive_empty = 0
    max_consecutive_empty = 3
    
    while start < total_available:
        url = f"http://export.arxiv.org/api/query?search_query={query}&start={start}&max_results={batch_size}&sortBy=submittedDate&sortOrder=descending"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            
            entries = root.findall('atom:entry', ns)
            
            if not entries:
                consecutive_empty += 1
                if consecutive_empty >= max_consecutive_empty:
                    break
                start += batch_size
                time.sleep(3)
                continue
            
            consecutive_empty = 0
            
            for entry in entries:
                # Get paper ID
                paper_id_elem = entry.find('atom:id', ns)
                if paper_id_elem is None:
                    continue
                
                # Extract arXiv ID
                paper_url = paper_id_elem.text
                arxiv_id = paper_url.split('/')[-1]
                arxiv_id_clean = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id
                
                # Construct PDF URL
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id_clean}.pdf"
                
                # Get title
                title_elem = entry.find('atom:title', ns)
                title = title_elem.text.strip() if title_elem is not None else ""
                title = ' '.join(title.split())
                
                # Get authors
                author_elems = entry.findall('atom:author', ns)
                authors = []
                for author_elem in author_elems:
                    name_elem = author_elem.find('atom:name', ns)
                    if name_elem is not None:
                        authors.append(name_elem.text.strip())
                
                authors_str = '; '.join(authors)
                
                # Get publication info
                journal_ref_elem = entry.find('arxiv:journal_ref', ns)
                journal_ref = journal_ref_elem.text.strip() if journal_ref_elem is not None else ""
                
                doi_elem = entry.find('arxiv:doi', ns)
                doi = doi_elem.text.strip() if doi_elem is not None else ""
                
                comment_elem = entry.find('arxiv:comment', ns)
                comment = comment_elem.text.strip() if comment_elem is not None else ""
                
                papers.append({
                    'arxiv_id': arxiv_id_clean,
                    'pdf_url': pdf_url,
                    'title': title,
                    'authors': authors_str,
                    'journal_ref': journal_ref,
                    'doi': doi,
                    'comment': comment,
                    'category': category,
                    'year': year
                })
            
            # Move to next batch
            start += batch_size
            
            # Rate limiting (configurable delay per arXiv policy)
            time.sleep(rate_limit_delay)
            
        except Exception as e:
            logger.error(f"    Error at offset {start} for month {month}: {e}")
            consecutive_empty += 1
            if consecutive_empty >= max_consecutive_empty:
                break
            time.sleep(10)
            start += batch_size
            continue
    
    logger.info(f"    ✓ Month {month:02d}/{year}: Collected {len(papers):,} papers")
    return papers

def query_year_by_months(category: str, year: int, batch_size: int = 1000, rate_limit_delay: float = 3.0) -> List[Dict]:
    """
    Query all papers for a year by breaking into monthly queries.
    
    Args:
        category: arXiv category (e.g., 'cs.LG')
        year: Year to query
    
    Returns:
        List of all papers for that year
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Collecting {category} {year} (monthly queries)...")
    logger.info(f"{'='*80}")
    
    all_papers = []
    
    # Query each month
    for month in range(1, 13):
        month_papers = query_month_papers(category, year, month, batch_size, rate_limit_delay)
        all_papers.extend(month_papers)
        logger.info(f"    Progress: {len(all_papers):,} papers collected so far")
    
    logger.info(f"\n✓ Year complete: {category} {year} - {len(all_papers):,} total papers")
    return all_papers

def deduplicate_papers(papers: List[Dict]) -> List[Dict]:
    """Remove duplicate papers by arxiv_id, keeping the first occurrence."""
    seen_ids = set()
    unique_papers = []
    duplicates = 0
    
    for paper in papers:
        arxiv_id = paper['arxiv_id']
        if arxiv_id not in seen_ids:
            seen_ids.add(arxiv_id)
            unique_papers.append(paper)
        else:
            duplicates += 1
    
    if duplicates > 0:
        logger.info(f"  Removed {duplicates} duplicate papers")
    
    return unique_papers

def save_papers_to_csv(papers: List[Dict], output_file: str):
    """Save papers to CSV."""
    if not papers:
        logger.warning("No papers to save")
        return
    
    # Create output directory
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Deduplicate first
    logger.info(f"Deduplicating papers...")
    papers = deduplicate_papers(papers)
    
    # Write to CSV
    fieldnames = ['arxiv_id', 'pdf_url', 'title', 'authors', 'num_authors', 'journal_ref', 'doi', 'comment', 'category', 'year']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for paper in papers:
            # Count authors
            authors_str = paper.get('authors', '')
            num_authors = len([a for a in authors_str.split(';') if a.strip()]) if authors_str else 0
            paper['num_authors'] = num_authors
            writer.writerow(paper)
    
    logger.info(f"✓ Saved {len(papers):,} unique papers to {output_file}")

def load_collection_history(history_file: str = 'arxiv_collection_history.json'):
    """Load collection history to check what's already been collected."""
    history_path = Path(history_file)
    if not history_path.exists():
        return {}
    
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load history file: {e}")
        return {}

def is_already_collected(history: dict, category_short: str, year: int) -> bool:
    """Check if a category+year combination has already been collected."""
    if not history:
        return False
    
    if category_short not in history:
        return False
    
    year_str = str(year)
    if year_str not in history[category_short]:
        return False
    
    # If entry exists, it's already collected
    return True

def update_collection_history(history_file: str, category_short: str, year: int, 
                             round_num: int, paper_count: int, author_count: int, 
                             output_file: str, email_count: int = 0):
    """Update collection history after collecting a category+year.
    Adds stats to existing entry or creates new one.
    """
    history_path = Path(history_file)
    
    # Load existing history
    history = load_collection_history(history_file)
    
    # Ensure structure exists
    if category_short not in history:
        history[category_short] = {}
    
    year_str = str(year)
    if year_str not in history[category_short]:
        # New entry
        history[category_short][year_str] = {
            'papers_collected': 0,
            'authors_collected': 0,
            'emails_collected': 0,
            'rounds': [],
            'last_collection_date': datetime.now().isoformat()
        }
    
    # Add stats (sum them up for same category+year across rounds)
    history[category_short][year_str]['papers_collected'] += paper_count
    history[category_short][year_str]['authors_collected'] += author_count
    # Keep max email count (emails might be extracted later)
    history[category_short][year_str]['emails_collected'] = max(
        history[category_short][year_str]['emails_collected'],
        email_count
    )
    
    # Add round number if not already there
    if round_num not in history[category_short][year_str]['rounds']:
        history[category_short][year_str]['rounds'].append(round_num)
    
    # Update last collection date
    history[category_short][year_str]['last_collection_date'] = datetime.now().isoformat()
    
    # Save updated history
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✓ Updated collection history: {category_short} {year} (Round {round_num})")

def collect_category_year(category: str, category_short: str, year: int, output_dir: str, 
                         batch_size: int = 1000, rate_limit_delay: float = 3.0,
                         round_num: int = None, history_file: str = 'arxiv_collection_history.json'):
    """Collect all papers for a category/year using monthly queries."""
    
    # Check if already collected
    history = load_collection_history(history_file)
    if is_already_collected(history, category_short, year):
        logger.info(f"⏭️  SKIPPING {category} {year} - already collected in previous round(s)")
        logger.info(f"   To re-collect, remove entry from {history_file}")
        return 0
    
    output_file = f"{output_dir}/{category_short}_{year}.csv"
    
    # Query all papers month-by-month
    papers = query_year_by_months(category, year, batch_size, rate_limit_delay)
    
    # Save to CSV (with deduplication)
    if papers:
        save_papers_to_csv(papers, output_file)
        
        # Count authors
        author_count = sum(int(p.get('num_authors', 0) or 0) for p in papers)
        
        # Update history (always update if round_num is provided)
        if round_num is not None:
            update_collection_history(history_file, category_short, year, round_num, 
                                   len(papers), author_count, Path(output_file).name)
            logger.info(f"✓ History updated: {category_short} {year}")
        else:
            logger.warning(f"⚠️  round_num not provided - history not updated for {category_short} {year}")
    else:
        logger.warning(f"No papers collected for {category} {year}")
    
    return len(papers)

def load_config(config_file: str = 'arxiv_collection_config.json'):
    """Load configuration from JSON file."""
    import json
    config_path = Path(config_file)
    
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_file}, using defaults")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config file: {e}")
        return None

def main():
    """Main function for collection using monthly queries."""
    
    # Load configuration
    config = load_config()
    
    if config and 'collection' in config:
        coll_config = config['collection']
        output_dir = coll_config.get('output_dir', 'data/arxiv/round2')
        round_num = coll_config.get('round', 2)
        batch_size = coll_config.get('batch_size', 1000)
        
        # Build categories list from config
        CATEGORIES = []
        for cat_config in coll_config.get('categories', []):
            arxiv_cat = cat_config['arxiv_category']
            short_name = cat_config['short_name']
            for year in cat_config.get('years', []):
                CATEGORIES.append((arxiv_cat, short_name, year))
        
        if not CATEGORIES:
            logger.error("No categories configured in config file!")
            return
    else:
        # Default configuration (backward compatibility)
        logger.warning("Using default configuration (no config file found)")
    CATEGORIES = [
        ('cs.LG', 'cs_lg', 2024),
        ('cs.LG', 'cs_lg', 2025),
        ('cs.CV', 'cs_cv', 2024),
        ('cs.CV', 'cs_cv', 2025),
    ]
    output_dir = 'data/arxiv/round2'
        round_num = 2
        batch_size = 1000
    
    logger.info("="*80)
    logger.info(f"ROUND {round_num} PAPER COLLECTION (MONTHLY STRATEGY)")
    logger.info("="*80)
    
    # Show categories being collected
    unique_cats = set()
    years_set = set()
    for arxiv_cat, short_name, year in CATEGORIES:
        unique_cats.add(arxiv_cat)
        years_set.add(year)
    
    logger.info(f"Categories: {', '.join(sorted(unique_cats))}")
    logger.info(f"Years: {', '.join(map(str, sorted(years_set)))}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Strategy: Query month-by-month to bypass 10k offset limit")
    logger.info("="*80)
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    total_papers = 0
    
    rate_limit_delay = coll_config.get('rate_limit_delay_seconds', 3.0) if config and 'collection' in config else 3.0
    history_file = coll_config.get('history_file', 'arxiv_collection_history.json') if config and 'collection' in config else 'arxiv_collection_history.json'
    
    for category, category_short, year in CATEGORIES:
        papers_collected = collect_category_year(category, category_short, year, output_dir, 
                                                batch_size, rate_limit_delay, round_num, history_file)
        total_papers += papers_collected
        logger.info(f"\n{'='*80}")
        logger.info(f"Completed: {category} {year} - {papers_collected:,} papers")
        logger.info(f"{'='*80}\n")
    
    logger.info("\n" + "="*80)
    logger.info(f"ROUND {round_num} COLLECTION COMPLETE!")
    logger.info("="*80)
    logger.info(f"Total papers collected: {total_papers:,}")
    logger.info(f"Output location: {output_dir}/")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Review the CSV files for completeness")
    logger.info("2. Extract emails (when ready)")
    logger.info("3. Combine with Round 1 and deduplicate by email")
    logger.info("="*80)

if __name__ == "__main__":
    main()

