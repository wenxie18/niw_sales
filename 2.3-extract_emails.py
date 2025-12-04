#!/usr/bin/env python3
"""
Extract emails from arXiv PDFs and match them to authors.
Reads CSV files with paper metadata (including authors from arXiv API),
downloads PDFs, extracts emails, matches them to authors, and outputs results.
"""

import csv
import logging
import fitz  # PyMuPDF
import re
import unicodedata
import requests
import time
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from http.cookiejar import MozillaCookieJar

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# Cookie Management
# ============================================================================

def load_cookies(cookie_file: str = "arxiv.org_cookies.txt") -> Optional[MozillaCookieJar]:
    """Load cookies from Netscape format cookie file."""
    cookie_path = Path(cookie_file)
    if not cookie_path.exists():
        logger.warning(f"Cookie file not found: {cookie_file}")
        return None
    
    try:
        jar = MozillaCookieJar(str(cookie_path))
        jar.load(ignore_discard=True, ignore_expires=True)
        logger.info(f"Loaded {len(jar)} cookies from {cookie_file}")
        return jar
    except Exception as e:
        logger.warning(f"Failed to load cookies: {e}")
        return None

# Load cookies once at module level
COOKIES = load_cookies()

# ============================================================================
# Email Extraction
# ============================================================================

def find_emails_in_text(text: str) -> List[str]:
    """Find all email addresses in text using regex."""
    emails = []
    
    # First, handle LaTeX multi-name format: {name1, name2}@domain.com
    # This represents multiple emails: name1@domain.com, name2@domain.com
    multi_name_pattern = r'\{([^}]+)\}@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
    for match in re.finditer(multi_name_pattern, text):
        names = match.group(1)  # e.g., "ashay, njk"
        domain = match.group(2)  # e.g., "mit.edu"
        
        # Split by comma and create individual emails
        for name in names.split(','):
            name = name.strip()
            if name:
                emails.append(f"{name}@{domain}")
    
    # Now clean up LaTeX artifacts for regular email detection
    text_cleaned = text.replace('{', ' ').replace('}', ' ').replace('\\', ' ')
    
    # Remove spaces around @ symbol (e.g., "name @domain.com" -> "name@domain.com")
    text_cleaned = re.sub(r'\s+@\s*', '@', text_cleaned)
    text_cleaned = re.sub(r'\s*@\s+', '@', text_cleaned)
    
    # Standard email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails.extend(re.findall(email_pattern, text_cleaned))
    
    return list(set(emails))  # Remove duplicates

def extract_emails_from_pdf(pdf_path: str) -> List[str]:
    """Extract all emails from the first page of a PDF."""
    try:
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            return []
        
        # Get text from first page
        first_page = doc[0]
        text = first_page.get_text("text")
        
        # Find all emails
        emails = find_emails_in_text(text)
        
        doc.close()
        return emails
    except Exception as e:
        logger.error(f"Error extracting emails from PDF: {e}")
        return []

# ============================================================================
# Email-Author Matching (Copied from ACL logic)
# ============================================================================

def normalize_text(text: str) -> str:
    """Normalize text by removing accents and converting to lowercase."""
    # Normalize unicode characters (e.g., é -> e)
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])
    return text.lower().strip()

def letter_match_score(name_part: str, email_username: str) -> float:
    """
    Calculate letter-level matching score (ignoring order).
    Returns score based on how many letters from name_part appear in email_username.
    """
    name_chars = set(name_part.lower())
    email_chars = set(email_username.lower())
    
    # Count matching characters
    matching_chars = name_chars.intersection(email_chars)
    if not matching_chars:
        return 0.0
    
    # Score based on coverage: how much of name_part is in email_username
    coverage = len(matching_chars) / len(name_chars) if name_chars else 0.0
    
    # Bonus if all characters match (anagram-like)
    if name_chars.issubset(email_chars):
        return 1.0 + coverage  # Strong match
    else:
        return coverage  # Partial match

def substring_match_score(name_combined: str, email_username: str) -> float:
    """
    Check if email_username is a substring of combined name.
    Returns high score if email is contained in name (e.g., "qtli" in "qintongli").
    """
    name_lower = name_combined.lower()
    email_lower = email_username.lower()
    
    if email_lower in name_lower:
        # Calculate how much of the email is covered
        coverage = len(email_lower) / len(name_lower) if name_lower else 0.0
        # Higher score for longer email matches relative to name
        return 5.0 + coverage * 2.0
    return 0.0

def match_score(author_name: str, email: str) -> Tuple[float, float]:
    """
    Calculate how well an author name matches an email (FULL ACL LOGIC).
    Returns (match_score, correctness_confidence) tuple.
    - match_score: Higher = better match (for ranking)
    - correctness_confidence: 0.0-1.0, how confident we are this is correct
    """
    author_parts = author_name.lower().split()
    if len(author_parts) < 2:
        return (0.0, 0.0)
    
    email_username = email.split('@')[0].lower()
    email_domain = email.split('@')[1].lower() if '@' in email else ''
    
    # Extract first name and last name
    # Handle hyphenated first names like "Marc-Alexandre" -> ["marc", "alexandre"]
    first_name_parts = author_parts[0].replace('-', ' ').split()
    first_name = author_parts[0]
    last_name = author_parts[-1]
    
    # Normalize names and email for matching
    first_name_norm = normalize_text(first_name)
    last_name_norm = normalize_text(last_name)
    email_username_norm = normalize_text(email_username)
    
    # SIMPLE CHECK FIRST: Is first name or last name in email username?
    first_in_email = False
    for part in first_name_parts:
        part_norm = normalize_text(part)
        if part_norm in email_username_norm:
            first_in_email = True
            break
    
    last_in_email = last_name_norm in email_username_norm
    
    if first_in_email or last_in_email:
        if first_in_email and last_in_email:
            return (10.0, 0.95)
        elif first_in_email:
            return (8.0, 0.85)
        else:
            # Only last name found – check if email also starts with first initial
            first_initial = first_name_norm[0] if first_name_norm else ''
            starts_with_initial = first_initial and email_username_norm.startswith(first_initial)
            if starts_with_initial:
                return (7.5, 0.82)
            return (6.5, 0.78)
    
    # Create name combinations
    first_last_full = normalize_text(''.join(author_parts).lower())
    first_last_simple = normalize_text((first_name_parts[0] + last_name).lower())
    first_initials = ''.join([part[0] for part in first_name_parts])
    first_initials_last = normalize_text((first_initials + last_name).lower())
    
    # Handle hyphenated last names
    last_name_parts = last_name.replace('-', ' ').split()
    if len(last_name_parts) > 1:
        last_initials = ''.join([part[0] for part in last_name_parts])
        first_initial_last_initials = normalize_text((first_name_parts[0][0] + last_initials).lower())
    else:
        last_initials = ""
        first_initial_last_initials = ""
    
    last_first = normalize_text((last_name + first_name).lower())
    email_username_normalized = normalize_text(email_username)
    
    # Strategy 1: EXACT MATCHES (Highest confidence: 0.95-1.0)
    name_combinations = [
        (first_last_full, 15.0),
        (first_last_simple, 15.0),
        (first_initials_last, 15.0),
        (last_first, 14.0),
    ]
    
    if last_initials:
        name_combinations.append((last_initials, 14.0))
        if first_initial_last_initials:
            name_combinations.append((first_initial_last_initials, 14.0))
    
    for name_combo, base_score in name_combinations:
        if email_username == name_combo or email_username_normalized == name_combo:
            return (base_score, 0.98)
    
    # Strategy 2: SUBSTRING MATCHES (High confidence: 0.85-0.95)
    for name_combo, base_score in name_combinations:
        substr_score = substring_match_score(name_combo, email_username_normalized)
        if substr_score == 0:
            substr_score = substring_match_score(name_combo, email_username)
        if substr_score > 0:
            return (substr_score, 0.90)
    
    # Strategy 3: HYPHENATED PATTERNS (e.g., "zhang-zx21")
    if '-' in email_username:
        parts = email_username.split('-')
        if len(parts) >= 2:
            email_last = parts[0]
            email_first_or_initials = parts[1]
            
            last_match = letter_match_score(last_name, email_last)
            if last_match >= 0.7:
                email_initials = ''.join([c for c in email_first_or_initials if c.isalpha()])
                
                if len(email_initials) >= 2:
                    author_first_letter = first_name[0]
                    author_second_letter = first_name[1] if len(first_name) > 1 else ''
                    
                    if email_initials == (author_first_letter + author_second_letter).lower():
                        return (12.0, 0.92)
                    if email_initials[0] == author_first_letter and email_initials[1] in first_name:
                        return (12.0, 0.90)
                    if email_initials[0] == author_first_letter:
                        return (11.0, 0.88)
                
                first_match = letter_match_score(first_name, email_first_or_initials)
                if first_match >= 0.5:
                    return (12.0, 0.92)
                elif first_match >= 0.3:
                    return (10.0, 0.85)
    
    # Strategy 4: CONTINUOUS LETTERS + FIRST LETTER
    # Try: first N letters of first name + first letter of last name
    for n in range(3, min(len(first_name_norm) + 1, 7)):
        first_part = first_name_norm[:n]
        last_initial = last_name_norm[0] if last_name_norm else ''
        candidate = first_part + last_initial
        if candidate == email_username_normalized:
            confidence = 0.75 + (n - 3) * 0.03
            return (8.0 + (n - 3) * 0.5, confidence)
    
    # Try: first N letters of last name + first letter of first name
    for n in range(3, min(len(last_name_norm) + 1, 7)):
        last_part = last_name_norm[:n]
        first_initial = first_name_norm[0] if first_name_norm else ''
        candidate = last_part + first_initial
        if candidate == email_username_normalized:
            confidence = 0.70 + (n - 3) * 0.03
            return (7.5 + (n - 3) * 0.5, confidence)
    
    # Strategy 5: EXACT FIRST/LAST NAME
    if email_username == first_name:
        return (9.0, 0.80)
    if email_username == last_name:
        return (8.0, 0.75)
    
    # Strategy 6: UNDERSCORE/DOT SEPARATED
    if '_' in email_username:
        parts = email_username.split('_')
        if len(parts) >= 2:
            first_match = letter_match_score(first_name, parts[0])
            last_match = letter_match_score(last_name, parts[1])
            if first_match >= 0.7 and last_match >= 0.7:
                return (7.5, 0.78)
            elif first_match >= 0.5 and last_match >= 0.5:
                return (6.0, 0.70)
    
    if '.' in email_username:
        parts = email_username.split('.')
        if len(parts) >= 2:
            last_match = letter_match_score(last_name, parts[0])
            first_match = letter_match_score(first_name, parts[1])
            if last_match >= 0.7 and first_match >= 0.7:
                return (7.5, 0.78)
            elif last_match >= 0.5 and first_match >= 0.5:
                return (6.0, 0.70)
    
    # Strategy 7: LETTER-LEVEL ANAGRAM MATCHES
    reversed_match = letter_match_score(last_first, email_username)
    normal_match = letter_match_score(first_last_full, email_username)
    
    if reversed_match >= 0.90:
        return (9.0, 0.85)
    if normal_match >= 0.90:
        return (8.5, 0.85)
    if reversed_match >= 0.80:
        return (7.5, 0.75)
    if normal_match >= 0.80:
        return (7.0, 0.75)
    
    # Strategy 8: PARTIAL MATCHES
    last_match = letter_match_score(last_name, email_username)
    first_match = letter_match_score(first_name, email_username)
    
    if last_match >= 0.7 and first_name[0] in email_username:
        return (5.5, 0.65)
    if first_match >= 0.7:
        return (4.5, 0.60)
    if last_match >= 0.7:
        return (3.5, 0.55)
    
    # No good match found
    return (0.0, 0.0)

def match_emails_to_authors(authors: List[str], emails: List[str]) -> List[Tuple[str, str, float]]:
    """
    Match emails to authors using scoring system.
    Returns list of (author, email, confidence) tuples.
    """
    if not authors or not emails:
        return []
    
    # Calculate all scores
    matches = []
    for email in emails:
        best_author = None
        best_score = 0.0
        best_confidence = 0.0
        
        for author in authors:
            score_val, confidence_val = match_score(author, email)
            if score_val > best_score:
                best_score = score_val
                best_confidence = confidence_val
                best_author = author
        
        if best_author and best_score > 0:
            # Convert confidence (0.0-1.0) to percentage (0-100)
            confidence_percent = best_confidence * 100
            matches.append((best_author, email, confidence_percent))
    
    # Filter: If one author matched to multiple emails, keep only the highest confidence
    author_to_best_match = {}
    for author, email, confidence in matches:
        if author not in author_to_best_match or confidence > author_to_best_match[author][1]:
            author_to_best_match[author] = (email, confidence)
    
    # Convert back to list
    filtered_matches = [(author, email, confidence) for author, (email, confidence) in author_to_best_match.items()]
    
    return filtered_matches

# ============================================================================
# Paper Processing
# ============================================================================

def download_pdf(url: str, output_path: str, max_retries: int = 3) -> Tuple[bool, bool]:
    """
    Download PDF from URL with rate limiting, cookies, and retries.
    
    Returns:
        (success, is_captcha): 
            - success: True if PDF downloaded successfully
            - is_captcha: True if CAPTCHA was detected (should stop immediately)
    """
    import time
    
    for attempt in range(max_retries):
        try:
            # Add delay to respect arXiv rate limits (3 seconds as per official policy)
            time.sleep(3.0)  # 3 seconds between requests as required by arXiv
            
            # Create session and use cookies if available
            session = requests.Session()
            if COOKIES:
                session.cookies = COOKIES
            
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check if we got a CAPTCHA page instead of a PDF
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type or b'<!DOCTYPE html>' in response.content[:200]:
                # Check for CAPTCHA indicators
                content_preview = response.content[:1000].decode('utf-8', errors='ignore')
                if 'reCAPTCHA' in content_preview or 'captcha' in content_preview.lower():
                    logger.error("❌ CAPTCHA DETECTED - arXiv is blocking automated requests!")
                    logger.error("   Cookies may have expired. Please refresh cookies.")
                    logger.error("   ⛔ STOPPING ALL PROCESSING IMMEDIATELY")
                    # Return (False, True) = failed + CAPTCHA detected
                    return (False, True)
                else:
                    logger.error(f"Received HTML instead of PDF from {url}")
                    return (False, False)
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return (True, False)  # Success, no CAPTCHA
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                wait_time = (attempt + 1) * 5  # Exponential backoff: 5s, 10s, 15s
                logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt+1}/{max_retries}")
                time.sleep(wait_time)
            else:
                logger.error(f"HTTP error downloading PDF: {e}")
                return (False, False)
        except Exception as e:
            # For other exceptions, only retry if not the last attempt
            if attempt < max_retries - 1:
                logger.warning(f"Error downloading, retrying ({attempt+1}/{max_retries}): {e}")
                time.sleep(2)
            else:
                logger.error(f"Error downloading PDF from {url}: {e}")
                return (False, False)
    
    return (False, False)  # Failed after all retries, not CAPTCHA

def clean_author_name(name: str) -> str:
    """Clean author name to Title Case."""
    # Split by spaces
    parts = name.split()
    # Capitalize first letter of each part, keep rest lowercase
    cleaned_parts = [p.capitalize() for p in parts]
    return ' '.join(cleaned_parts)

def process_paper(paper_data: dict, temp_dir: Path) -> Tuple[List[Dict], bool, bool]:
    """
    Process a single paper: download PDF, extract emails, match to authors.
    
    Returns:
        (results, pdf_success, is_captcha):
            - results: List of result dictionaries
            - pdf_success: True if PDF downloaded successfully
            - is_captcha: True if CAPTCHA detected (should stop immediately)
    """
    arxiv_id = paper_data['arxiv_id']
    pdf_url = paper_data['pdf_url']
    title = paper_data['title']
    authors_str = paper_data['authors']
    
    # Parse authors (semicolon-separated)
    authors = [a.strip() for a in authors_str.split(';') if a.strip()]
    
    if not authors:
        logger.warning(f"No authors found for {arxiv_id}")
        return ([], True, False)  # No authors, but not a download failure
    
    # Download PDF
    pdf_path = temp_dir / f"{arxiv_id}.pdf"
    pdf_downloaded, is_captcha = download_pdf(pdf_url, pdf_path)
    if not pdf_downloaded:
        return ([], False, is_captcha)  # PDF download FAILED, return CAPTCHA flag
    
    # Extract emails
    emails = extract_emails_from_pdf(pdf_path)
    
    # Clean up PDF
    pdf_path.unlink(missing_ok=True)
    
    if not emails:
        logger.warning(f"No emails found in {arxiv_id}")
        # Return authors without emails
        results = []
        for author in authors:
            results.append({
                'Paper URL': pdf_url,
                'Title': title,
                'Author': clean_author_name(author),
                'Email': '',
                'Confidence': '0%'
            })
        return (results, True, False)  # No emails, but PDF was downloaded successfully
    
    # Match emails to authors
    matches = match_emails_to_authors(authors, emails)
    
    # Create results
    results = []
    matched_authors = set()
    
    # Add matched authors
    for author, email, confidence in matches:
        results.append({
            'Paper URL': pdf_url,
            'Title': title,
            'Author': clean_author_name(author),
            'Email': email,
            'Confidence': f"{int(confidence)}%"
        })
        matched_authors.add(author)
    
    # Add unmatched authors (with empty email)
    for author in authors:
        if author not in matched_authors:
            results.append({
                'Paper URL': pdf_url,
                'Title': title,
                'Author': clean_author_name(author),
                'Email': '',
                'Confidence': '0%'
            })
    
    return (results, True, False)  # Successfully processed, no CAPTCHA

# ============================================================================
# Main Processing
# ============================================================================

def process_csv_file(input_csv: str, output_csv: str):
    """Process a CSV file of papers and extract email information."""
    logger.info(f"Processing {input_csv}...")
    
    # Create temp directory for PDFs
    temp_dir = Path('temp_pdfs')
    temp_dir.mkdir(exist_ok=True)
    
    # Read input CSV
    papers = []
    try:
        with open(input_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            papers = list(reader)
    except Exception as e:
        logger.error(f"Error reading {input_csv}: {e}")
        return
    
    logger.info(f"  Found {len(papers)} papers to process")
    
    # Check if output CSV already exists and read already-processed papers
    processed_urls = set()
    output_path = Path(output_csv)
    resume_mode = output_path.exists()
    
    if resume_mode:
        try:
            with open(output_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('Paper URL'):
                        processed_urls.add(row['Paper URL'])
            logger.info(f"  📁 RESUME MODE: Found {len(processed_urls)} already-processed paper URLs")
            logger.info(f"  📁 Will skip these and continue from where we left off")
        except Exception as e:
            logger.warning(f"  ⚠️  Could not read existing output file: {e}")
            logger.warning(f"  ⚠️  Starting from scratch")
            processed_urls = set()
            resume_mode = False
    
    # Open output CSV for writing (append if resume, overwrite if new)
    fieldnames = ['Paper URL', 'Title', 'Author', 'Email', 'Confidence']
    open_mode = 'a' if resume_mode else 'w'
    output_file = open(output_csv, open_mode, newline='', encoding='utf-8')
    writer = csv.DictWriter(output_file, fieldnames=fieldnames)
    if not resume_mode:
        writer.writeheader()
    output_file.flush()
    
    # Process each paper and write results immediately
    total_records = 0
    skipped_count = 0
    start_time = time.time()
    consecutive_failures = 0
    MAX_CONSECUTIVE_FAILURES = 5  # Stop if 5 PDFs fail in a row (likely rate limited)
    
    try:
        for i, paper in enumerate(papers, 1):
            # Skip if already processed
            paper_url = paper.get('pdf_url', '')
            if paper_url in processed_urls:
                skipped_count += 1
                continue
            
            # Show progress more frequently and with more details
            if (i - skipped_count) % 5 == 0:
                elapsed = time.time() - start_time
                processed_count = i - skipped_count
                speed = processed_count / elapsed if elapsed > 0 else 0
                remaining = len(papers) - i
                eta_seconds = remaining / speed if speed > 0 else 0
                eta_minutes = eta_seconds / 60
                logger.info(f"  [{i}/{len(papers)}] {i/len(papers)*100:.1f}% | Processed: {processed_count} | Skipped: {skipped_count} | Records: {total_records} | Speed: {speed:.1f} papers/s | ETA: {eta_minutes:.1f} min")
            
            results, pdf_success, is_captcha = process_paper(paper, temp_dir)
            
            # If CAPTCHA detected, stop IMMEDIATELY (don't wait for 5 failures)
            if is_captcha:
                logger.error(f"")
                logger.error(f"{'='*80}")
                logger.error(f"⛔ CAPTCHA DETECTED - STOPPING ALL PROCESSING IMMEDIATELY")
                logger.error(f"{'='*80}")
                logger.error(f"⚠️  Processed {i - skipped_count}/{len(papers)} papers (skipped {skipped_count})")
                logger.error(f"⚠️  Saved {total_records} records to {output_csv}")
                logger.error(f"")
                logger.error(f"📝 To resume:")
                logger.error(f"   1. Export fresh cookies from browser")
                logger.error(f"   2. Save as arxiv.org_cookies.txt")
                logger.error(f"   3. Press Ctrl+C to stop this script")
                logger.error(f"   4. Run the command again - it will auto-resume")
                logger.error(f"{'='*80}")
                break
            
            # Track consecutive PDF download failures (for non-CAPTCHA errors)
            if not pdf_success:
                consecutive_failures += 1
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    logger.error(f"⚠️  STOPPING: {consecutive_failures} consecutive PDF download failures - likely rate limited!")
                    logger.error(f"⚠️  Processed {i - skipped_count}/{len(papers)} papers (skipped {skipped_count}), saved {total_records} records")
                    logger.error(f"⚠️  Resume later or wait for rate limit to reset")
                    break
            else:
                consecutive_failures = 0  # Reset counter on successful download
            
            # Write results immediately
            if results:
                writer.writerows(results)
                output_file.flush()  # Force write to disk
                total_records += len(results)
    finally:
        output_file.close()
        elapsed = time.time() - start_time
        processed_count = len(papers) - skipped_count
        logger.info(f"✓ Completed: {len(papers)} papers in {elapsed/60:.1f} minutes")
        logger.info(f"   Processed: {processed_count} | Skipped: {skipped_count} | Records saved: {total_records}")
        logger.info(f"   Output: {output_csv}")
    
    # Clean up temp directory
    try:
        temp_dir.rmdir()
    except:
        pass  # Directory might not be empty if errors occurred

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract emails from arXiv PDFs and match to authors.')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file (from 2.1-query_arxiv_papers.py)')
    parser.add_argument('--output', type=str, required=True, help='Output CSV file')
    
    args = parser.parse_args()
    
    process_csv_file(args.input, args.output)

if __name__ == "__main__":
    main()

