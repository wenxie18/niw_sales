#!/usr/bin/env python3
"""
Extract paper information (title, authors, emails) from ACL Anthology PDFs.
VERSION 2: Uses font-size based title extraction (PyMuPDF).
Title = largest font size near top of page (within first few lines).
Author/email extraction logic unchanged (uses superscripts for matching).
"""

import requests
import re
from pathlib import Path
import json
import csv
from typing import List, Dict, Optional
import logging
import unicodedata
from io import BytesIO

# Prioritize PyMuPDF for font-size based title extraction
try:
    import fitz  # PyMuPDF
    PDF_LIB = 'pymupdf'
except ImportError:
    try:
        import PyPDF2
        PDF_LIB = 'PyPDF2'
    except ImportError:
        try:
            import pdfplumber
            PDF_LIB = 'pdfplumber'
        except ImportError:
            PDF_LIB = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF content (first page only).
    
    Note: This is a fallback method. PyMuPDF is preferred for font-size based extraction.
    """
    if PDF_LIB is None:
        raise ImportError("Please install PyMuPDF (recommended) or PyPDF2/pdfplumber: pip install pymupdf")
    
    if PDF_LIB == 'pymupdf':
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        if len(doc) > 0:
            page = doc[0]  # First page
            text = page.get_text()
            doc.close()
            return text
        return ""
    elif PDF_LIB == 'PyPDF2':
        pdf_file = BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        if len(pdf_reader.pages) > 0:
            return pdf_reader.pages[0].extract_text()
        return ""
    elif PDF_LIB == 'pdfplumber':
        pdf_file = BytesIO(pdf_content)
        with pdfplumber.open(pdf_file) as pdf:
            if len(pdf.pages) > 0:
                return pdf.pages[0].extract_text()
        return ""


def extract_text_with_layout(pdf_content: bytes) -> tuple[str, list]:
    """Extract text with layout information (font size, position) using PyMuPDF.
    
    This is the PRIMARY method - uses font size to identify titles.
    
    Returns:
        tuple: (plain_text, blocks_list) where blocks_list contains text blocks with font info
    """
    if PDF_LIB != 'pymupdf':
        # Should not happen if PyMuPDF is prioritized, but fallback just in case
        text = extract_text_from_pdf(pdf_content)
        return text, []
    
    try:
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        if len(doc) == 0:
            return "", []
        
        page = doc[0]  # First page
        text = page.get_text()
        
        # Get text blocks with font information
        blocks = page.get_text("dict")["blocks"]
        text_blocks = []
        
        for block in blocks:
            if "lines" in block:  # Text block
                block_text = ""
                max_font_size = 0
                for line in block["lines"]:
                    for span in line["spans"]:
                        block_text += span["text"] + " "
                        max_font_size = max(max_font_size, span.get("size", 0))
                
                if block_text.strip():
                    text_blocks.append({
                        'text': block_text.strip(),
                        'font_size': max_font_size,
                        'bbox': block.get("bbox", [0, 0, 0, 0])  # [x0, y0, x1, y1]
                    })
        
        doc.close()
        return text, text_blocks
    except Exception as e:
        logger.error(f"Failed to extract layout info: {e}")
        text = extract_text_from_pdf(pdf_content)
        return text, []


def find_author_section(lines: List[str], title: str = '') -> tuple[int, int]:
    """
    Find author section by pattern detection.
    
    Looks for patterns:
    - Names separated by commas
    - Names with special characters/superscripts (numbers, symbols: *, ‡, §, etc.)
    - Email addresses
    - Institution keywords
    - "and" connecting names
    
    Args:
        lines: List of text lines from PDF
        title: Paper title (if known) - used to skip title lines before looking for authors
    
    Returns: (start_line, end_line) indices
    """
    # Skip first 2 lines (proceedings header)
    start_idx = 2
    
    # If we have a title, skip past title lines to avoid false matches
    # Strategy: Find CONSECUTIVE lines that match title words, then start after those
    if title:
        title_words_set = set(word.lower() for word in title.split() if len(word) > 4)
        # Find first line containing title words
        title_start = None
        for i in range(start_idx, min(12, len(lines))):
            line_lower = lines[i].lower()
            if any(word in line_lower for word in title_words_set):
                title_start = i
                break
        
        # Find last CONSECUTIVE line containing title words (title may span multiple lines)
        if title_start is not None:
            title_end = title_start
            for i in range(title_start + 1, min(title_start + 5, len(lines))):
                line_lower = lines[i].lower()
                # Stop if we hit a line without title words
                if not any(word in line_lower for word in title_words_set):
                    break
                title_end = i
            # Start looking for authors after title ends
            start_idx = title_end + 1
    
    end_idx = min(30, len(lines))  # Check first 30 lines
    
    author_section_start = None
    author_section_end = None
    
    for i in range(start_idx, end_idx):
        line = lines[i].strip()
        if not line:
            continue
        
        # Check for author patterns:
        # 1. Names with commas (multiple authors separated by commas on same line)
        has_comma_separated_names = bool(re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+,\s*[A-Z][a-z]+', line))
        
        # 1b. Single name with comma (common pattern: one author per line, e.g., "Andrew Zhu,")
        has_single_name_with_comma = bool(re.search(r'^[A-Z][a-z]+(?:\s+[A-Z]\.)?\s+[A-Z][a-z]+(?:-[A-Z][a-z]+)?,?\s*$', line))
        
        # 2. Names with special characters/superscripts (numbers, symbols)
        has_name_with_symbols = bool(re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+\s*[0-9\*†‡§♭♮♠♣♦♡♢]', line))
        
        # 3. Email addresses
        has_email = '@' in line
        
        # 4. Institution keywords
        has_institution = any(kw in line.lower() for kw in ['university', 'laboratory', 'lab', 'school', 'institute', 'department'])
        
        # 5. "and" connecting names (e.g., "John Doe and Jane Smith")
        has_and_connector = bool(re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+\s+and\s+[A-Z][a-z]+', line))
        
        # If line has author signals, mark as start of author section
        if (has_comma_separated_names or has_single_name_with_comma or has_name_with_symbols or has_email or has_and_connector) and author_section_start is None:
            author_section_start = i
        
        # If we're in author section and hit abstract, stop
        if author_section_start is not None:
            if line.lower().startswith('abstract'):
                author_section_end = i
                break
            # If line has email, it's definitely part of author section
            if has_email:
                # Extend section to include this line
                author_section_end = i + 1
                continue
            # If we see content that's clearly not author-related, might be end
            if not (has_comma_separated_names or has_single_name_with_comma or has_name_with_symbols or has_email or has_institution or has_and_connector):
                # No author signals, might be end (but allow a few blank lines)
                # Don't stop if we haven't seen emails yet - emails might come after affiliations
                if line and len(line) > 50:  # Long line without author signals = probably content
                    # But check if there might be emails coming up (within next 3 lines)
                    has_emails_ahead = False
                    for j in range(i + 1, min(i + 4, len(lines))):
                        if '@' in lines[j]:
                            has_emails_ahead = True
                            break
                    if not has_emails_ahead:
                        author_section_end = i
                        break
    
    # If we found start but no end, use reasonable default (10 lines after start)
    if author_section_start is not None and author_section_end is None:
        author_section_end = min(author_section_start + 10, len(lines))
    
    # Fallback: if no author section found, use lines 2-20
    if author_section_start is None:
        return (2, 20)
    
    return (author_section_start, author_section_end)


def extract_emails(text: str, title: str = '') -> List[str]:
    """Extract email addresses from text.
    
    Strategy: Look for emails in the author section (pattern-based detection).
    """
    lines = text.split('\n')
    
    # Find author section using pattern detection (pass title to skip title lines)
    author_section_start, author_section_end = find_author_section(lines, title=title)
    
    # Extract text from author section only
    author_section_text = '\n'.join(lines[author_section_start:author_section_end])
    
    # Email regex pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, author_section_text)
    
    # Filter out placeholder/template emails
    placeholder_patterns = [
        'firstname.lastname@',
        'first.last@',
        'name.surname@',
        'firstname_lastname@',
        'firstlast@',
        'user@',
        'example@',
        'your.email@',
        'youremail@'
    ]
    emails = [e for e in emails if not any(p in e.lower() for p in placeholder_patterns)]
    
    # Also handle emails in curly braces: {email1,email2,email3}@domain.com
    # Pattern: {word1,word2,word3}@domain.com
    brace_pattern = r'\{([^}]+)\}@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
    brace_matches = re.findall(brace_pattern, author_section_text)
    for usernames, domain in brace_matches:
        # Split by comma and create full emails
        for username in usernames.split(','):
            username = username.strip()
            if username:
                emails.append(f"{username}@{domain}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_emails = []
    for email in emails:
        email_lower = email.lower()
        if email_lower not in seen:
            seen.add(email_lower)
            unique_emails.append(email)
    return unique_emails


def extract_title_from_layout(text_blocks: list) -> Optional[str]:
    """Extract title using layout information (font size, position).
    
    VERSION 2 STRATEGY:
    - Title = largest font size near top of page (within first 10 lines)
    - Location: First 10 lines of text (sorted by y-position)
    - After title line, before abstract line = author information
    
    This is much simpler and more reliable than text-based pattern matching.
    """
    if not text_blocks:
        return None
    
    # Sort all blocks by y-position (ascending) to get line order
    # Then take first 10 blocks (first 10 lines)
    sorted_by_position = sorted(
        text_blocks,
        key=lambda b: b.get('bbox', [0, 0, 0, 0])[1]  # Sort by y0 (top to bottom)
    )
    
    # Take first 10 blocks (first 10 lines)
    top_blocks = []
    for b in sorted_by_position[:10]:
        text = b.get('text', '').strip()
        if len(text) < 10:
            continue
        
        # Skip common header/footer patterns
        if any(skip in text.lower() for skip in [
            'proceedings', 'abstract', 'introduction', 'author', 'university',
            'august', 'pages', 'volume', 'edited by', '©', 'copyright'
        ]):
            continue
        
        # Skip if it looks like author names (commas, superscripts, etc.)
        comma_count = text.count(',')
        if comma_count >= 2 or is_author_line(text):
            continue
        
        top_blocks.append(b)
    
    if not top_blocks:
        return None
    
    # Sort by font size (descending) - title is the LARGEST font
    # Secondary sort by y-position (ascending) - title is at the top
    sorted_blocks = sorted(
        top_blocks,
        key=lambda b: (-b.get('font_size', 0), b.get('bbox', [0, 0, 0, 0])[1])
    )
    
    # The title is the block with the largest font size near the top
    title_block = sorted_blocks[0]
    title = title_block.get('text', '').strip()
    font_size = title_block.get('font_size', 0)
    y0 = title_block.get('bbox', [0, 0, 0, 0])[1]
    
    logger.info(f"  Title candidate: font_size={font_size:.1f}pt, y={y0:.1f}: {title[:60]}...")
    
    # Check if there are continuation blocks (multi-line titles)
    # Look for blocks with similar font size (within 2 points) and close y position
    title_parts = [title]
    for block in sorted_blocks[1:]:
        block_font = block.get('font_size', 0)
        block_y = block.get('bbox', [0, 0, 0, 0])[1]
        block_text = block.get('text', '').strip()
        
        # Title continuation: similar font size and close vertically
        font_diff = abs(block_font - font_size)
        y_diff = block_y - (y0 + 20)  # Allow space for line height
        
        # Check if this looks like an author line (name with trailing comma, or multiple comma-separated names)
        looks_like_author = (
            bool(re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+(?:-[A-Z][a-z]+)?)+,\s*$', block_text)) or  # "Andrew Zhu," pattern
            is_author_line(block_text)  # Other author patterns
        )
        
        if (font_diff <= 2.0 and  # Similar font size
            y_diff < 60 and  # Close vertically
            len(block_text) >= 10 and
            not looks_like_author and
            not any(skip in block_text.lower() for skip in [
                'author', 'university', '@', 'email', 'abstract', 'introduction'
            ])):
            title_parts.append(block_text)
            y0 = block_y
        elif font_size > 0 and block_font < font_size * 0.8:
            # Font size drops significantly - passed the title
            break
    
    full_title = ' '.join(title_parts)
    full_title = re.sub(r'\s+', ' ', full_title).strip()  # Normalize whitespace
    
    # Validation: Title must start with capital letter
    # Also check if it looks like author names (has multiple names pattern)
    if len(full_title) >= 10:
        # Check if first letter is capitalized
        if not full_title[0].isupper():
            return None  # Invalid title - doesn't start with capital
        
        # Double-check: Skip if it looks like author names (commas, superscripts, etc.)
        if full_title.count(',') >= 2 or is_author_line(full_title):
            return None  # This is author names, not title
        
        return full_title
    
    return None


def is_acl_footnote(line: str) -> bool:
    """Check if line is an ACL footnote/header."""
    line_lower = line.lower()
    if 'association for computational linguistics' in line_lower:
        return True
    if re.search(r'\bacl\b', line_lower):
        if len(line) < 50 or any(kw in line_lower for kw in ['proceedings', 'meeting', 'volume', 'pages', 'edited']):
            return True
    skip_patterns = [
        r'proceedings of', r'annual meeting', r'volume \d+', r'pages \d+',
        r'edited by', r'isbn', r'august \d+-\d+', r'©\d{4}', r'^\d{4} association',
    ]
    if any(re.search(pattern, line_lower) for pattern in skip_patterns):
        return True
    if re.search(r'©|copyright|^\d{4}\s', line, re.IGNORECASE):
        return True
    return False


def is_section_header(line: str) -> bool:
    """Check if line is a section header (Abstract, Introduction, etc.)."""
    line_lower = line.lower().strip()
    section_keywords = ['abstract', 'introduction', 'author', 'corresponding', 'email']
    for keyword in section_keywords:
        if line_lower == keyword or line_lower.startswith(keyword + ':'):
            return True
        if len(line) < 20 and keyword in line_lower:
            return True
    return False


def is_author_line(line: str) -> bool:
    """Check if line contains author names.
    
    ACL author lines use commas, not "and" connectors.
    Author lines are short (< 150 chars even with multiple authors).
    """
    line_stripped = line.strip()
    
    # Author lines are always short - titles are longer
    # Single author: ~10-30 chars, multiple authors with commas: ~50-120 chars
    if len(line_stripped) > 150:
        return False
    
    # Comma-separated names: "John Doe, Jane Smith"
    if re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+,\s*[A-Z][a-z]+', line_stripped):
        return True
    
    # Numbers after names (superscripts): "John Doe1" or "John Doe1,2"
    if re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+\d+', line_stripped):
        return True
    
    # Superscript symbols: †, ‡, *, etc.
    if re.search(r'[‡§♭♮♠♣♦♡♢\*†]', line_stripped):
        return True
    
    return False


def extract_title(text: str) -> Optional[str]:
    """Extract paper title from first page (handles multi-line titles).
    
    Follows EXTRACTION_LOGIC.md:
    1. Skip footnotes/headers (ACL-specific detection)
    2. Find title start (first capitalized line ≥ 15 chars, not author/email)
    3. Collect title lines until hitting authors/emails/institutions
    4. Validate and return
    """
    lines = text.split('\n')
    
    title_lines = []
    title_start_idx = None
    
    # Step 1: Find title start
    for i, line in enumerate(lines[:30]):
        line = line.strip()
        if not line:
            continue
        
        # Skip ACL footnotes
        if is_acl_footnote(line):
            continue
        
        # Skip section headers
        if is_section_header(line):
            continue
        
        # Skip emails
        if '@' in line:
            continue
        
        # Skip if just numbers/symbols
        if re.match(r'^[\d\s\W]+$', line):
            continue
        
        # Skip if only affiliation symbols
        if re.match(r'^[‡§♭♮\s]+$', line):
            continue
        
        # Good candidate: length ≥ 15, starts with capital
        # Strip leading special characters (like #, *, etc.) before checking capitalization
        # This handles markdown-style titles like "# Title Text"
        line_stripped_special = line.lstrip('#*-=_~`')
        first_letter = next((c for c in line_stripped_special if c.isalpha()), None)
        
        if len(line) >= 15 and first_letter and first_letter.isupper():
            # Not all caps (unless very short)
            if line.isupper() and len(line) > 50:
                continue
            
            # Not an author line
            if is_author_line(line):
                continue
            
            # Found title start
            title_start_idx = i
            break
    
    if title_start_idx is None:
        return None
    
    # Step 2: Collect title lines
    for i in range(title_start_idx, min(title_start_idx + 10, len(lines))):
        line = lines[i].strip()
        
        # Stop on section headers
        if is_section_header(line):
            break
        
        # Stop on emails
        if '@' in line:
                    break
                
        # Stop on author lines
        if is_author_line(line):
                break
        
        # Stop on institution keywords in short lines
        if any(kw in line.lower() for kw in ['university', 'laboratory', 'lab', 'school', 'institute', 'department']):
            if len(line) < 40:  # Short line with institution = likely affiliation
                break
            
        # Skip empty lines (but allow between title parts)
        if not line:
            # Check if next line is authors
            if title_lines and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and (is_author_line(next_line) or '@' in next_line):
                    break
            continue
        
        # Skip if just numbers/symbols
        if re.match(r'^[\d\s\W]+$', line):
            continue
        
        # Add to title
        title_lines.append(line)
        
    # Step 3: Validate and return
    if not title_lines:
        return None
    
    title = ' '.join(title_lines)
    title = re.sub(r'\s+', ' ', title).strip()
    
    # Remove leading special characters (markdown heading syntax, etc.)
    title = title.lstrip('#*-=_~` ')
    
    # Remove trailing punctuation (except ? and !)
    if title.endswith((',', ';')) and len(title) > 20:
        title = title.rstrip(',;')
    
    # Final validation
    if len(title) < 10:
        return None
    
    # Check if first letter (not first character) is uppercase
    first_letter = next((c for c in title if c.isalpha()), None)
    if not first_letter or not first_letter.isupper():
        return None
    
    return title


def extract_authors(text: str, title: str = '') -> List[str]:
    """Extract author names from text.
    
    Strategy: Find author section by pattern detection (names with commas, symbols, emails).
    """
    lines = text.split('\n')
    authors = []
    
    # Find author section using pattern detection (pass title to skip title lines)
    author_section_start, author_section_end = find_author_section(lines, title=title)
    
    # Limit search to author section only
    search_range = range(author_section_start, author_section_end)
    
    # Common false positives to exclude
    false_positives = {
        'abstract', 'introduction', 'university', 'laboratory', 
        'graduate', 'school', 'carnegie', 'mellon', 'tsinghua',
        'shenzhen', 'international', 'peng', 'cheng', 'proceedings',
        'association', 'computational', 'linguistics', 'meeting',
        'quantized', 'large', 'language', 'memory', 'efficient',
        'tuning', 'fast', 'side', 'technology', 'development', 'co',
        'ltd', 'department', 'computer', 'science', 'information',
        'engineering', 'key', 'laboratory', 'intelligent', 'systems',
        'state', 'hebei', 'jiangxi', 'nanchang', 'china', 'hong', 'kong',
        'science', 'connect', 'amazon', 'microsoft', 'research', 'asia',
        'palo', 'alto', 'usa', 'inc', 'guangzhou', 'shanghai', 'fudan',
        'aberdeen', 'georgia', 'institute', 'nvidia', 'nanyang',
        'image', 'text', 'mix', 'info', 'data', 'method', 'result',
        'figure', 'table', 'section', 'experiment', 'dataset', 'model',
        'college', 'center', 'centre', 'campus', 'technologies',
        'machine', 'learning', 'company', 'gmbh', 'dfki', 'csiro',
        'kensho', 'artificial', 'intelligence'
    }
    
    # Patterns that are definitely not author names
    non_author_patterns = [
        r'^image\s+info$',
        r'^text\s+info$',
        r'^mix\s+info$',
        r'^.*\s+info$',  # Anything ending with "Info" (capitalized)
        r'^.*\s+data$',
        r'^.*\s+method$',
        r'^.*\s+result$',
        r'^.*\s+llm$',  # Multi-modal LLM, etc.
        r'^.*\s+model$',
    ]
    
    # Words that should never appear in author names (as standalone words)
    non_author_words = {
        'info', 'data', 'method', 'result', 'image', 'text', 'mix',
        'model', 'llm', 'figure', 'table', 'section', 'experiment',
        'dataset', 'metric', 'score', 'accuracy', 'performance',
        'college', 'center', 'centre', 'campus', 'technologies',
        'machine', 'learning', 'company', 'gmbh'
    }
    institution_name_keywords = [
        'university', 'college', 'center', 'centre', 'campus', 'technologies',
        'technology', 'research', 'laboratory', 'lab', 'institute', 'company',
        'gmbh', 'inc', 'llc', 'ai', 'deepmind', 'google', 'amazon', 'microsoft',
        'kensho', 'data61', 'sorbonne', 'munich', 'academy', 'society'
    ]
    
    # Look for author lines - they typically contain:
    # 1. Names with superscript numbers (1, 2, 3) for affiliations
    # 2. Names with affiliation symbols (‡, §, ♭, ♮, ♠, ♣, ♦, ♡, ♢)
    # 3. Names followed by asterisks (*) for corresponding authors
    
    # Now extract authors from the author section only
    for i in search_range:
        if i >= len(lines):
            break
        line = lines[i].strip()
        if not line or len(line) < 5:
            continue
        
        # Skip if it's clearly not an author line
        line_lower = line.lower()
        if any(skip in line_lower for skip in ['abstract', 'introduction', 'proceedings', 'edited by']):
            continue
        
        # Skip footnote patterns (e.g., "Equally contributing authors", "Corresponding author")
        if any(pattern in line_lower for pattern in ['contributing author', 'corresponding author', 'equal contribution', 'work was done']):
            continue
        
        # Skip if line matches title words (to avoid extracting title fragments as authors)
        # Logic: if most significant words in line match title, it's a title fragment
        if title:
            title_words_set = set(word.lower() for word in title.split() if len(word) > 4)
            line_words = set(word.lower() for word in line.split() if len(word) > 4)
            if line_words:  # Only check if there are significant words
                common_words = title_words_set & line_words
                # If >=80% of line's significant words are in title, it's a title fragment
                match_ratio = len(common_words) / len(line_words)
                if match_ratio >= 0.8 or len(common_words) >= 3:
            continue
        
        # Skip if it's mostly institution text
        if sum(1 for word in line_lower.split() if word in false_positives) > 2:
            continue
        
        # Skip lines that are clearly institutions (block format issue)
        # Check if line has institution keywords and next line is an email
        if any(kw in line_lower for kw in ['university', 'institute', 'laboratory', 'nvidia', 'eth', 'college', 'academy']):
            # Check if next line is an email (indicates this is institution in block format)
            if i + 1 < len(lines) and '@' in lines[i + 1]:
                continue
        
        # Skip single-word institution names (like "NVIDIA", "ETH")
        if len(line.split()) == 1 and line.isupper():
            continue
        
        # Skip known institution patterns like "ETH Zürich"
        if re.match(r'^(ETH|MIT|UCLA|USC|NYU|CMU)\s+\w+$', line, re.IGNORECASE):
            continue
        
        # Pre-process: Insert commas after digits when followed by capital letter (author separator)
        # This handles cases like "Anni Li1 Junrui Wan1" → "Anni Li1, Junrui Wan1"
        # Pattern: digit/symbol followed by space and capital letter (start of new name)
        line = re.sub(r'([0-9†‡§♭♮♠♣♦♡♢\*])\s+([A-Z][a-z]+\s+[A-Z])', r'\1, \2', line)
        
        # First, try to split by comma and "and" to handle cases like:
        # "Yanzhi Xu∗, Yueying Hua∗, Shichen Li and Zhongqing Wang†"
        # Split the line by comma and "and" to get individual names
        name_segments = re.split(r',\s*|\s+and\s+', line)
        
        # Pattern 1: Names with superscript numbers/symbols (e.g., "Hanlei Zhang1, Hua Xu1∗")
        # Also handles names without superscripts (e.g., "Andrew Zhu, Alyssa Hwang")
        # Also handles middle initials (e.g., "Peter A. Beerel", "John Q. Public")
        # Match: Name followed by optional numbers, symbols, commas
        # Also handle hyphenated names like "Chao-Han Huck Yang" and hyphenated last names like "Callison-Burch"
        # Use \w instead of [a-z] to include accented characters (é, ô, etc.)
        # Allow hyphens in last name: "Chris Callison-Burch"
        # Allow middle initials with period: "A.", "B."
        name_pattern1 = r'\b([A-Z](?:\w+|\.)\s*(?:-[A-Z](?:\w+|\.))?(?:\s+[A-Z](?:\w+|\.)(?:-[A-Z](?:\w+|\.))?){1,3})\s*[0-9\*†‡§♭♮♠♣♦♡♢,]*'
        matches1 = re.findall(name_pattern1, line)
        
        # Also try extracting from each segment individually (for better handling of comma-separated names)
        for segment in name_segments:
            segment = segment.strip()
            if len(segment) < 5:
                continue
            # Extract name from segment (handles both with and without superscripts)
            segment_matches = re.findall(name_pattern1, segment)
            matches1.extend(segment_matches)
        
        for name in matches1:
            name_parts = set(name.lower().replace('-', ' ').split())
            # Check if any part is a non-author word
            if name_parts.intersection(non_author_words):
                continue
            if not name_parts.intersection(false_positives):
                if 2 <= len(name.split()) <= 5:  # Allow up to 5 words for names like "Chao-Han Huck Yang"
                    # Clean name (remove trailing punctuation, numbers, and superscript symbols)
                    # Remove numbers and superscript symbols that may have been captured
                    clean_name = re.sub(r'[,\*]+$', '', name).strip()  # Remove trailing commas/asterisks
                    clean_name = re.sub(r'\d+$', '', clean_name).strip()  # Remove trailing numbers (e.g., "Song1" -> "Song")
                    clean_name = re.sub(r'[†‡§♭♮♠♣♦♡♢]+$', '', clean_name).strip()  # Remove trailing symbols
                    clean_lower = clean_name.lower()
                    if any(keyword in clean_lower for keyword in institution_name_keywords):
                        continue
                    # Filter out if it's clearly a location (e.g., "Palo Alto")
                    if clean_name and clean_lower not in ['palo alto', 'nanchang', 'suzhou']:
                        # Check against non-author patterns
                        is_author = True
                        for pattern in non_author_patterns:
                            if re.match(pattern, clean_name, re.IGNORECASE):
                                is_author = False
                                break
                        # Check if any word in the name is a non-author word
                        clean_parts = set(clean_name.lower().split())
                        if clean_parts.intersection(non_author_words):
                            is_author = False
                        # Also check if it looks like a section header (all words capitalized, common words)
                        if is_author and clean_name.isupper() and len(clean_name.split()) <= 3:
                            # Could be a header, check if it contains common non-name words
                            if any(word in clean_name.lower() for word in ['info', 'data', 'method', 'result', 'image', 'text', 'mix']):
                                is_author = False
                        if is_author and clean_name not in authors:
                            authors.append(clean_name)
        
        # Pattern 2: Names with affiliation symbols (e.g., "Yafu Li♠♣∗")
        # Use \w instead of [a-z] to include accented characters
        name_pattern2 = r'\b([A-Z]\w+(?:\s+[A-Z]\w+){1,3})\s*[†‡§♭♮♠♣♦♡♢\*]+'
        matches2 = re.findall(name_pattern2, line)
        
        for name in matches2:
            name_parts = set(name.lower().split())
            # Check if any part is a non-author word
            if name_parts.intersection(non_author_words):
                continue
            if not name_parts.intersection(false_positives):
                if 2 <= len(name.split()) <= 4:
                    clean_name = re.sub(r'[‡§♭♮♠♣♦♡♢\*]+$', '', name).strip()
                    clean_lower = clean_name.lower()
                    if any(keyword in clean_lower for keyword in institution_name_keywords):
                        continue
                    # Check against non-author patterns
                    is_author = True
                    for pattern in non_author_patterns:
                        if re.match(pattern, clean_name, re.IGNORECASE):
                            is_author = False
                            break
                    # Check if any word in the name is a non-author word
                    clean_parts = set(clean_name.lower().split())
                    if clean_parts.intersection(non_author_words):
                        is_author = False
                    if is_author and clean_name and clean_name not in authors:
                        authors.append(clean_name)
        
        # Pattern 3: Simple name pattern (First Last) - fallback for cases without superscripts
        # This runs even if Pattern 1 found something, to catch simple comma-separated names
        # Example: "Andrew Zhu, Alyssa Hwang, Liam Dugan" (all from same affiliation, no superscripts)
        # Also handles hyphenated last names like "Callison-Burch"
        # Use \w instead of [a-z] to include accented characters and hyphens
        name_pattern3 = r'\b([A-Z]\w+\s+[A-Z]\w+(?:-[A-Z]\w+)?)\b'
        matches3 = re.findall(name_pattern3, line)
        
        # If Pattern 1 didn't find much, or if this line looks like simple comma-separated names,
        # use Pattern 3 to extract all names
        if not matches1 or (',' in line and not any(c in line for c in '0123456789*†‡§♭♮♠♣♦♡♢')):
            # Line has commas but no superscripts - likely simple comma-separated names
            for name in matches3:
                # Skip if this name is already included as part of a longer name from Pattern 1
                # Example: if "Marc-Alexandre Côté" is already found, skip "Alexandre Côté"
                is_duplicate = False
                for existing_author in authors:
                    # Check if this name is a substring of an existing author name
                    # or if existing author name contains this name
                    if name.lower() in existing_author.lower() and name != existing_author:
                        is_duplicate = True
                        break
                    if existing_author.lower() in name.lower() and name != existing_author:
                        # Existing is substring of this - remove existing and add this longer one
                        if existing_author in authors:
                            authors.remove(existing_author)
                        break
                
                if is_duplicate:
                    continue
                
                name_parts = set(name.lower().split())
                # Check if any part is a non-author word
                if name_parts.intersection(non_author_words):
                    continue
                if not name_parts.intersection(false_positives):
                    name_lower = name.lower()
                    if any(keyword in name_lower for keyword in institution_name_keywords):
                        continue
                    # Check against non-author patterns
                    is_author = True
                    for pattern in non_author_patterns:
                        if re.match(pattern, name, re.IGNORECASE):
                            is_author = False
                            break
                    # Check if any word in the name is a non-author word
                    if name_parts.intersection(non_author_words):
                        is_author = False
                    if is_author and name not in authors and 2 <= len(name.split()) <= 3:
                        authors.append(name)
    
    # If we found emails, try to extract names near them (backup method)
    # IMPORTANT: Only search within author section to avoid extracting title fragments
    emails = extract_emails(text)
    if emails and len(authors) == 0:  # Only if we failed to find any authors
        for email in emails:
            email_username = email.split('@')[0].lower()
            # Look for lines near email that might contain the author name
            # Limit search to author section range
            for i in range(author_section_start, min(author_section_end, len(lines))):
                line = lines[i]
                if email in line:
                    # Look backward for author name (check 2-8 lines before, but stay within author section)
                    for j in range(max(author_section_start, i-8), i):
                        name_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b', lines[j])
                        if name_match:
                            name = name_match.group(1)
                            name_parts = set(name.lower().split())
                            if not name_parts.intersection(false_positives | non_author_words):
                                if name not in authors and 2 <= len(name.split()) <= 4:
                                    authors.append(name)
                                    break
    
    # Remove duplicates while preserving order
    # Also remove shorter names that are substrings of longer names
    seen = set()
    unique_authors = []
    for author in authors:
        author_lower = author.lower()
        if author_lower not in seen:
            # Check if this author is a substring of an existing author
            is_substring = False
            for existing in unique_authors:
                existing_lower = existing.lower()
                # If this author is contained in existing (and not equal), skip it
                if author_lower in existing_lower and author_lower != existing_lower:
                    is_substring = True
                    break
                # If existing is contained in this (and not equal), remove existing and add this
                if existing_lower in author_lower and author_lower != existing_lower:
                    unique_authors.remove(existing)
                    seen.discard(existing_lower)
                    break
            
        if not is_substring:
            seen.add(author_lower)
            unique_authors.append(author)
    
    return unique_authors


def parse_acl_pdf(url: str) -> Dict[str, any]:
    """
    Download and parse ACL PDF to extract paper information.
    
    Args:
        url: URL to ACL PDF (e.g., https://aclanthology.org/2024.acl-long.1.pdf)
    
    Returns:
        Dictionary with title, authors, emails, and author_email_pairs, or None if 404
    """
    logger.info(f"Processing: {url}")
    
    # Download PDF
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 404:
            logger.info(f"Paper not found (404): {url}")
            return None
        response.raise_for_status()
        pdf_content = response.content
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.info(f"Paper not found (404): {url}")
            return None
        logger.error(f"Failed to download PDF: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to download PDF: {e}")
        return None
    
    # Extract text - PRIMARY METHOD: PyMuPDF with font-size based title extraction
    try:
        if PDF_LIB == 'pymupdf':
            # Use layout-based extraction (font size for title)
            text, text_blocks = extract_text_with_layout(pdf_content)
            
            # Extract title using font size: largest font near top (within first few lines) = title
            if text_blocks:
                title = extract_title_from_layout(text_blocks)
                # Validate: If font-size method extracted something that doesn't look like a title,
                # fall back to text-based method (which checks first letter capitalization)
                if title:
                    # Double-check: title should start with capital and not be author names
                    # Author patterns: multiple names with commas (e.g., "John Doe, Jane Smith, Bob Johnson")
                    looks_like_authors = bool(re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+\s*,\s*[A-Z][a-z]+\s+[A-Z][a-z]+', title))
                    if not title[0].isupper() or looks_like_authors:
                        logger.warning("  Font-size method extracted invalid title (looks like author names), using text-based fallback")
                        title = extract_title(text)
                    else:
                        logger.info(f"  Title extracted using font-size method: {title[:60]}...")
                else:
                    # Fallback to text-based if layout extraction fails
                    logger.warning("  Font-size based title extraction failed, using text-based fallback")
                    title = extract_title(text)
            else:
                title = extract_title(text)
        else:
            # Fallback to text-based extraction if PyMuPDF not available
            text = extract_text_from_pdf(pdf_content)
            title = extract_title(text)
            logger.warning("  PyMuPDF not available - install pymupdf for font-size based title extraction")
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        return None
    authors = extract_authors(text, title=title)
    emails = extract_emails(text, title=title)
    if not authors:
        logger.warning("  No authors extracted (likely block format). Skipping to avoid false positives.")
        return None
    
    # Extract affiliations and author-affiliation mapping
    # Work within author section only for better accuracy
    lines = text.split('\n')
    author_section_start, author_section_end = find_author_section(lines, title=title)
    if author_section_start is None or author_section_end is None:
        logger.warning("  Could not determine author section boundaries. Skipping.")
        return None
    extended_end = min(len(lines), author_section_end + 5)
    author_section_lines = lines[author_section_start:extended_end]
    
    # DYNAMIC SYMBOL DETECTION: Scan the entire author section (title to abstract) 
    # to detect ALL superscript symbols used in this paper
    # This ensures we catch any symbol used in any PDF, even ones we haven't seen before
    detected_symbols = set()
    
    # Strategy: Look for superscript patterns in the author section
    # 1. Symbols immediately after author names (e.g., "John Doe†")
    # 2. Symbols at start of affiliation lines (e.g., "†University of Arizona")
    # 3. Numbers used as superscripts (e.g., "John Doe1" or "1University")
    
    for line in author_section_lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        # Skip abstract/introduction lines
        if any(skip in line_stripped.lower() for skip in ['abstract', 'introduction']):
            break  # Stop at abstract
        
        # Pattern 1: Symbols immediately after author names
        # Look for: "FirstName LastName" followed by non-alphanumeric symbols (within 5 chars)
        # This catches patterns like "Ruoyao Wang†" or "Peter Clark♣"
        name_symbol_pattern = r'\b([A-Z]\w+(?:\s+[A-Z]\w+){1,3})\s*([^\w\s,]{1,5})'
        matches = re.finditer(name_symbol_pattern, line_stripped)
        for match in matches:
            name_part = match.group(1)
            symbols_part = match.group(2)
            
            # Extract each symbol character
            for char in symbols_part:
                # Skip common punctuation
                if char in [',', '.', ';', ':', ' ', '\t', '(', ')', '[', ']']:
                    continue
                # Include any non-alphanumeric symbol (these are likely superscripts)
                if not char.isalnum() and char not in [',', '.', ';', ':', ' ', '\t', '@', '(', ')', '[', ']']:
                    detected_symbols.add(char)
            
            # Also check for numbers immediately after names (e.g., "John Doe1,2")
            num_matches = re.findall(r'\d+', symbols_part)
            for num in num_matches:
                detected_symbols.add(num)
        
        # Pattern 1b: Numbers directly appended to names without non-alphanumeric separator (e.g., "Hongyi Yuan12")
        name_number_inline_pattern = r'\b([A-Z]\w+(?:\s+[A-Z]\w+){1,3})(\d{1,3}(?:,\d{1,3})*)'
        inline_matches = re.finditer(name_number_inline_pattern, line_stripped)
        for match in inline_matches:
            number_chunk = match.group(2)
            for num in re.findall(r'\d+', number_chunk):
                detected_symbols.add(num)
        
        # Pattern 2: Symbols at start of affiliation definition lines
        # Look for: "SymbolInstitution" or "Symbol Institution" at line start
        # This catches patterns like "†University of Arizona" or "‡ Carnegie Mellon"
        affiliation_start_pattern = r'^[\s]*([^\w\s,]{1,2})[\s]*([A-Z][^@,;]{10,})'
        matches = re.finditer(affiliation_start_pattern, line_stripped)
        for match in matches:
            symbol = match.group(1)
            # Skip if it's just punctuation
            if symbol not in [',', '.', ';', ':', ' ', '\t', '@', '(', ')', '[', ']']:
                detected_symbols.add(symbol)
        
        # Pattern 3: Numbered affiliations at line start
        # Look for: "1University" or "1 University" or "1. University"
        num_affiliation_pattern = r'^\s*(\d+)(?=[\s\.]*[A-Z])'
        num_match = re.match(num_affiliation_pattern, line_stripped)
        if num_match:
            detected_symbols.add(num_match.group(1))
        
        # Pattern 4: Symbols in the middle of lines (for cases like "Author1, Author2, ... 1Institution, 2Institution")
        # Look for patterns like "SymbolInstitution" anywhere in line (not just at start)
        # But only if line contains institution keywords
        if any(kw in line_stripped.lower() for kw in ['university', 'laboratory', 'lab', 'school', 'institute', 'department', 'research']):
            # Look for symbol followed by capital letter (likely start of institution name)
            symbol_institution_pattern = r'([^\w\s,]{1,2})([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            matches = re.finditer(symbol_institution_pattern, line_stripped)
            for match in matches:
                symbol = match.group(1)
                inst_part = match.group(2)
                # Only if institution part looks like an institution name (has common keywords or is reasonably long)
                if (any(kw in inst_part.lower() for kw in ['university', 'laboratory', 'lab', 'school', 'institute', 'research']) or 
                    len(inst_part) > 8):
                    if symbol not in [',', '.', ';', ':', ' ', '\t', '@', '(', ')', '[', ']']:
                        detected_symbols.add(symbol)
    
    # Convert to sorted lists for consistent processing
    # Keep numbers separate from symbols for easier handling
    all_symbols = sorted([s for s in detected_symbols if not s.isdigit()])
    all_numbers = sorted([s for s in detected_symbols if s.isdigit()], key=int)
    
    # Log detected symbols for debugging
    if all_symbols or all_numbers:
        logger.info(f"  Detected superscript symbols: {all_symbols}")
        if all_numbers:
            logger.info(f"  Detected superscript numbers: {all_numbers}")
    else:
        # No symbols detected means all authors are from the same institution
        # No need for superscripts to differentiate - this is fine
        logger.info("  No superscript symbols detected - all authors likely from same institution")
    
    # Combine for processing
    all_superscripts = all_symbols + all_numbers
    affiliation_map = {}  # Maps symbols/numbers to institution names
    
    # Step 1: Find affiliation definitions (usually after author names, before emails)
    # Look for patterns like: "‡Carnegie Mellon University" or "1State Key Laboratory"
    for line in author_section_lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        # Skip footnote lines (not institutions)
        if any(pattern in line_stripped.lower() for pattern in [
            'contributing author', 'corresponding author', 'equal contribution',
            'work was done', 'work was performed', 'equal author'
        ]):
            continue
        
        # Check for symbol-based affiliations (e.g., "‡Carnegie Mellon University" or "♠ Zhejiang University")
        # Handle both formats: SymbolInstitution and Symbol Institution
        for sym in all_superscripts:
            if sym in line_stripped:
                # Find all occurrences of this symbol in the line
                # Pattern: symbol followed by optional space, then institution name
                # Stop at next symbol, comma (if part of list), or email
                # Build pattern to stop at any detected symbol
                other_symbols = ''.join([re.escape(s) for s in all_superscripts if s != sym])
                pattern = re.escape(sym) + r'\s*([^' + other_symbols + r',@]+?)(?=[' + other_symbols + r',@]|$)'
                matches = re.finditer(pattern, line_stripped)
                for match in matches:
                    institution = match.group(1).strip()
                    # Clean up: remove trailing punctuation, stop at email or curly brace
                    institution = re.sub(r'[,;:]\s*$', '', institution)
                    if '@' in institution:
                        institution = institution.split('@')[0].strip()
                    if '{' in institution:
                        institution = institution.split('{')[0].strip()
                    # Remove any remaining symbols
                    symbols_escaped = ''.join([re.escape(s) for s in all_superscripts])
                    institution = re.sub(r'[' + symbols_escaped + r']', '', institution).strip()
                    if institution and len(institution) > 3:
                        # Normalize for deduplication check
                        inst_normalized = ' '.join(institution.lower().split())
                        # Only add if not already mapped to same normalized institution
                        existing_normalized = [' '.join(v.lower().split()) for v in affiliation_map.values() if v]
                        if inst_normalized not in existing_normalized:
                            affiliation_map[sym] = institution
                        break  # Only take first match per symbol per line
        
        # Check for numbered affiliations (e.g., "1State Key Laboratory" or "1 State Key Laboratory")
        # Handle multiple numbered institutions on same line (e.g., "1 USC, USA 2 Intel Labs, USA")
        remaining_line = line_stripped
        while remaining_line:
            # Try to match numbered institution at start of remaining text
            num_match = re.match(r'^\s*([0-9]+)[\s\.]+(.+)', remaining_line)
        if not num_match:
            # Try without space (number directly before text)
                num_match = re.match(r'^\s*([0-9]+)([A-Z].+)', remaining_line)
        
            if not num_match:
                break  # No more numbered institutions on this line
            
            num, institution = num_match.groups()
            institution = institution.strip()
            
            # Stop at next number pattern (e.g., "1Institution, 2Institution")
            # Look for space followed by digit and capital letter (start of next institution)
            next_num_match = re.search(r'\s+([0-9]+)\s*[A-Z]', institution)
            if next_num_match:
                pos = next_num_match.start()
                remaining_line = num_match.group(2)[pos:].strip()
                institution = institution[:pos].strip()
            else:
                remaining_line = ''  # No more institutions on this line
            
            # Clean up: remove trailing punctuation, stop at email or curly brace
            institution = re.sub(r'[,;:]\s*$', '', institution)
            if '@' in institution:
                institution = institution.split('@')[0].strip()
            if '{' in institution:
                institution = institution.split('{')[0].strip()
            # Also clean any remaining leading numbers
            institution = re.sub(r'^[0-9]+\s*', '', institution).strip()
            
            if institution and len(institution) > 3:
                # Normalize for deduplication
                inst_normalized = ' '.join(institution.lower().split())
                existing_normalized = [' '.join(v.lower().split()) for v in affiliation_map.values() if v]
                if inst_normalized not in existing_normalized:
                    affiliation_map[num] = institution
    
    # Step 2: Extract superscripts from each author name
    # First, clean author names to remove any trailing numbers/symbols that might have been included
    cleaned_authors = []
    for author in authors:
        # Remove trailing numbers and symbols from author names
        clean_author = re.sub(r'\d+$', '', author).strip()  # Remove trailing numbers
        clean_author = re.sub(r'[†‡§♭♮♠♣♦♡♢]+$', '', clean_author).strip()  # Remove trailing symbols
        if clean_author and clean_author not in cleaned_authors:
            cleaned_authors.append(clean_author)
    authors = cleaned_authors  # Update authors list with cleaned names
    
    # This is the key: author names have superscripts that directly match institution symbols
    author_superscripts = {}  # Maps author name to list of superscript symbols/numbers
    author_line_positions = {}
    
    for author in authors:
        author_superscripts[author] = []
        author_line_positions[author] = None
        
        # Find the author line (should be in author section, not affiliation line)
        for idx, line in enumerate(author_section_lines):
            # Skip affiliation definition lines (they have institution keywords)
            if any(kw in line.lower() for kw in ['university', 'laboratory', 'lab', 'school', 'institute', 'department']):
                continue
            
            # Check if this line contains the author name
            # Match clean author name in line (line may have numbers/symbols after name)
            author_parts = author.split()
            if len(author_parts) >= 2:
                # Match if first and last name appear in line (in order, allowing numbers/symbols after)
                first_name = author_parts[0]
                last_name = author_parts[-1]
                # Pattern: first name, then middle names/initials (like "A. "), then last name
                # Use (?:[A-Z]\.?\s+)* to match middle names/initials (non-greedy)
                # No trailing \b to allow numbers/symbols immediately after last name
                pattern = rf'\b{re.escape(first_name)}\s+(?:[A-Z]\.?\s+)*{re.escape(last_name)}'
                name_match = re.search(pattern, line, re.IGNORECASE)
                if name_match:
                    # Record which line contained this author (for institution fallback)
                    if author_line_positions[author] is None:
                        author_line_positions[author] = idx
                    # Find the position where the name ends (last name)
                    match = name_match
                    if match:
                        name_end_pos = match.end()
                        after_name = line[name_end_pos:name_end_pos + 20]
                        
                        # Extract ALL superscript symbols immediately after name
                        # Pattern: "Author Name‡§" or "Author Name*" (symbols can be adjacent)
                        for sym in all_superscripts:
                            if sym in after_name:
                                sym_pos = after_name.find(sym)
                                # Symbol should be very close to name (within 5 chars)
                                if sym_pos < 5:
                                    author_superscripts[author].append(sym)
                        
                        # Extract ALL superscript numbers immediately after name
                        # Pattern: "Author Name1,2,3" or "Author Name1 2 3" or "Author Name1∗"
                        # Look for numbers in first 15 chars after name (to catch comma-separated numbers)
                        num_pattern = r'([0-9]+)'
                        num_matches = re.finditer(num_pattern, after_name[:15])
                        for match in num_matches:
                            num = match.group(1)
                            num_pos = match.start()
                            # Number should be very close to name (within 10 chars to catch "1,2,3")
                            if num_pos < 10:
                                # Check if it's part of a comma-separated list or standalone
                                # Make sure it's not part of an email or other text
                                context_before = after_name[max(0, num_pos-2):num_pos]
                                context_after = after_name[num_pos+len(num):num_pos+len(num)+2]
                                # Should be preceded by name (or comma/space) and followed by comma, space, or symbol
                                # Check if followed by any detected symbol or common separators
                                valid_after = [',', ' ', ''] + list(all_symbols)
                                if (not context_before or context_before[-1] in [',', ' ', ''] or context_before[-1].isalpha()) and \
                                   (not context_after or context_after[0] in valid_after or context_after[0].isalpha()):
                                    if num in affiliation_map:
                                        author_superscripts[author].append(num)
                        
                        # Only process first occurrence of author name
                        break
            elif author in line:
                # Find exact position of author name
                author_pos = line.find(author)
                if author_pos != -1:
                    # Get text immediately after author name (first 20 chars)
                    after_name = line[author_pos + len(author):author_pos + len(author) + 20]
                    
                    # Extract ALL superscript symbols immediately after name
                    # Pattern: "Author Name‡§" or "Author Name*" (symbols can be adjacent)
                    for sym in all_superscripts:
                        if sym in after_name:
                            sym_pos = after_name.find(sym)
                            # Symbol should be very close to name (within 5 chars)
                            if sym_pos < 5:
                                author_superscripts[author].append(sym)
                    
                    # Extract ALL superscript numbers immediately after name
                    # Pattern: "Author Name1,2,3" or "Author Name1 2 3" or "Author Name1∗"
                    # Look for numbers in first 15 chars after name (to catch comma-separated numbers)
                    num_pattern = r'([0-9]+)'
                    num_matches = re.finditer(num_pattern, after_name[:15])
                    for match in num_matches:
                        num = match.group(1)
                        num_pos = match.start()
                        # Number should be very close to name (within 10 chars to catch "1,2,3")
                        if num_pos < 10:
                            # Check if it's part of a comma-separated list or standalone
                            # Make sure it's not part of an email or other text
                            context_before = after_name[max(0, num_pos-2):num_pos]
                            context_after = after_name[num_pos+len(num):num_pos+len(num)+2]
                            # Should be preceded by name (or comma/space) and followed by comma, space, or symbol
                            # Check if followed by any detected symbol or common separators
                            valid_after = [',', ' ', ''] + list(all_symbols)
                            if (not context_before or context_before[-1] in [',', ' ', ''] or context_before[-1].isalpha()) and \
                               (not context_after or context_after[0] in valid_after or context_after[0].isalpha()):
                                if num in affiliation_map:
                                    author_superscripts[author].append(num)
                
                # Only process first occurrence of author name
                break
    
    # Build shared institution candidate (lines between last author line and first email)
    shared_institution = ''
    author_line_indices = [pos for pos in author_line_positions.values() if pos is not None]
    last_author_idx = max(author_line_indices) if author_line_indices else None
    first_email_idx = None
    for idx, line in enumerate(author_section_lines):
        if '@' in line:
            first_email_idx = idx
            break
    if last_author_idx is not None and first_email_idx is not None and first_email_idx - last_author_idx <= 6:
        block_lines = []
        for idx in range(last_author_idx + 1, first_email_idx):
            candidate = author_section_lines[idx].strip()
            if not candidate:
                continue
            if any(kw in candidate.lower() for kw in ['abstract', 'corresponding author', 'contributing author']):
                continue
            candidate = re.sub(r'^[\d\*\†‡§♭♮♠♣♦♡♢]+\s*', '', candidate).strip()
            if candidate:
                block_lines.append(candidate)
        if block_lines:
            shared_institution = ', '.join(block_lines)
            shared_institution = re.sub(r'\s+', ' ', shared_institution).strip()
    # If still empty, look at lines immediately after the first email (common in block format)
    if not shared_institution and first_email_idx is not None:
        block_lines = []
        for idx in range(first_email_idx + 1, min(first_email_idx + 5, len(author_section_lines))):
            candidate = author_section_lines[idx].strip()
            if not candidate:
                continue
            if any(kw in candidate.lower() for kw in ['abstract', 'corresponding author', 'contributing author']):
                continue
            candidate = re.sub(r'^[\d\*\†‡§♭♮♠♣♦♡♢]+\s*', '', candidate).strip()
            if candidate:
                block_lines.append(candidate)
        if block_lines:
            shared_institution = ', '.join(block_lines)
            shared_institution = re.sub(r'\s+', ' ', shared_institution).strip()
    
    # Step 3: Map author superscripts to institutions (direct matching - simple logic)
    author_institutions = {}   # Maps author name to institution name(s)
    
    for author in authors:
        institutions = []
        seen_institutions = set()
        
        # Get superscripts for this author
        superscripts = author_superscripts.get(author, [])
        
        if superscripts and affiliation_map:
            # Author has superscripts AND we have affiliation definitions - map them
            for sup in superscripts:
                if sup in affiliation_map:
                    inst = affiliation_map[sup].strip()
                    # Skip empty institutions
                    if not inst:
                        continue
                    # Normalize for deduplication
                    inst_normalized = ' '.join(inst.lower().split())
                    if inst_normalized not in seen_institutions:
                        institutions.append(inst)
                        seen_institutions.add(inst_normalized)
            
        # If affiliation_map is empty, all authors are from the same institution
        # (Superscripts on author names in this case are footnotes, not affiliation markers)
        if not affiliation_map or not institutions:
                # Look for single institution in author section
            # When no superscripts, all authors are from the same institution
                for line in author_section_lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                
                # Skip if it's an author name or email
                if '@' in line_stripped or any(kw in line_stripped.lower() for kw in ['abstract', 'introduction']):
                    continue
                
                # Look for institution keywords
                if any(kw in line_stripped.lower() for kw in ['university', 'laboratory', 'lab', 'school', 'institute', 'department', 'research', 'college', 'center', 'centre', 'campus', 'technologies', 'company']):
                    # Extract potential institution name - more flexible pattern
                    # Pattern: Capture the full institution name including text after keyword
                    # Examples: "University of Pennsylvania", "Carnegie Mellon University", "MIT"
                    # Try pattern that captures from start to end of line (if reasonable length)
                    if len(line_stripped) > 5 and len(line_stripped) < 100:
                        # If the line itself looks like an institution name (reasonable length, has keyword)
                        # and doesn't contain email or author patterns, use the whole line
                        # Special case: Lines starting with "The University", "The Institute", etc. are institutions, not author names
                        starts_with_institution_word = any(line_stripped.lower().startswith(word) for word in ['the university', 'the institute', 'university', 'institute'])
                        looks_like_author = re.search(r'^[A-Z][a-z]+\s+[A-Z][a-z]+$', line_stripped) and not starts_with_institution_word
                        if not '@' in line_stripped and not looks_like_author:
                            inst = line_stripped.strip()
                            # Clean up: remove leading numbers, trailing punctuation
                            inst = re.sub(r'^[0-9]+\s*', '', inst).strip()
                            inst = re.sub(r'[,;:\.]\s*$', '', inst)
                            inst_normalized = ' '.join(inst.lower().split())
                            if inst_normalized not in seen_institutions and len(inst) > 5:
                                institutions.append(inst)
                                seen_institutions.add(inst_normalized)
                                break  # Found institution, stop looking
                    else:
                        # For longer lines, try to extract just the institution part
                        institution_match = re.search(
                            r'([A-Z][^@,;]{5,60}(?:University|Laboratory|Lab|School|Institute|Department|Research))',
                            line_stripped,
                            re.IGNORECASE
                        )
                        if institution_match:
                            inst = institution_match.group(1).strip()
                            # Clean up: remove leading numbers, trailing punctuation
                            inst = re.sub(r'^[0-9]+\s*', '', inst).strip()
                            inst = re.sub(r'[,;:\.]\s*$', '', inst)
                            inst_normalized = ' '.join(inst.lower().split())
                            if inst_normalized not in seen_institutions and len(inst) > 5:
                                institutions.append(inst)
                                seen_institutions.add(inst_normalized)
                                break  # Found institution, stop looking
        
        # Filter out empty institutions and clean up any email fragments (e.g., "{yewei.song")
        cleaned_institutions = []
        for inst in institutions:
            inst = inst.strip()
            # Skip empty, whitespace-only, or email fragments
            if inst and len(inst) > 0 and not inst.startswith('{') and '@' not in inst:
                cleaned_institutions.append(inst)
        
        # Final cleanup: remove any remaining empty strings and join
        final_institutions = [i for i in cleaned_institutions if i and i.strip()]
        if not final_institutions and shared_institution:
            final_institutions = [shared_institution]
        result = ', '.join(final_institutions) if final_institutions else ''
        # Post-process: remove any double commas and normalize spaces
        result = re.sub(r',\s*,+', ', ', result)  # Remove double commas
        result = re.sub(r'\s+', ' ', result)  # Normalize multiple spaces to single space
        result = re.sub(r'^,\s*|\s*,$', '', result).strip()  # Remove leading/trailing commas
        author_institutions[author] = result
    
    # Match authors with emails using intelligent heuristics
    author_email_pairs = []
    used_emails = set()
    
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
    
    def match_score(author_name: str, email: str) -> tuple[float, float]:
        """
        Calculate how well an author name matches an email.
        Returns (match_score, correctness_confidence) tuple.
        - match_score: Higher = better match (for ranking)
        - correctness_confidence: 0.0-1.0, how confident we are this is correct
        
        SIMPLIFIED LOGIC:
        1. First check if first name or last name is in email username
        2. If only one email matches, that's it (high confidence)
        3. If multiple emails match, use more complex logic
        """
        author_parts = author_name.lower().split()
        if len(author_parts) < 2:
            return (0.0, 0.0)
        
        email_username = email.split('@')[0].lower()
        email_domain = email.split('@')[1].lower() if '@' in email else ''
        
        # Extract first name and last name
        # Handle hyphenated first names like "Marc-Alexandre" -> ["marc", "alexandre"]
        first_name_parts = author_parts[0].replace('-', ' ').split()  # Split hyphenated names
        first_name = author_parts[0]  # Keep original for display
        last_name = author_parts[-1]
        
        # Normalize accented characters for matching (é->e, ô->o, etc.)
        def normalize_text(text):
            # Remove accents
            nfd = unicodedata.normalize('NFD', text)
            return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
        
        # Normalize names and email for matching
        first_name_norm = normalize_text(first_name)
        last_name_norm = normalize_text(last_name)
        email_username_norm = normalize_text(email_username)
        
        # SIMPLE CHECK FIRST: Is first name or last name in email username?
        # This catches most cases like "peterc" (peter + c) or "clark" in email
        # For hyphenated names, check each part
        first_in_email = False
        for part in first_name_parts:
            part_norm = normalize_text(part)
            if part_norm in email_username_norm:
                first_in_email = True
                break
        
        last_in_email = last_name_norm in email_username_norm
        
        # If either first or last name is in email, it's a potential match
        # Return a simple match indicator - the caller will check if only one email matches
        if first_in_email or last_in_email:
            if first_in_email and last_in_email:
                return (10.0, 0.95)  # Both names in email = very confident
            elif first_in_email:
                return (8.0, 0.85)  # First name in email = confident
            else:
                # Only last name found – check if email also starts with first initial (xzhang -> Xiangliang Zhang)
                first_initial = first_name_norm[0] if first_name_norm else ''
                starts_with_initial = first_initial and email_username_norm.startswith(first_initial)
                if starts_with_initial:
                    return (7.5, 0.82)  # Last name + first initial alignment
                return (6.5, 0.78)  # Last name only = weaker match
        
        # If simple check didn't work, try more complex patterns
        full_name = ''.join(author_parts)  # Combined name without spaces
        
        # Create name combinations (normalized for accented character matching)
        # For hyphenated names, try different combinations:
        # 1. Full first name + last name: "marcalexandre" + "cote" = "marcalexandrecote"
        # 2. First part + last name: "marc" + "cote" = "marccote"  
        # 3. First letters of each part + last name: "m" + "a" + "cote" = "macote"
        # 4. For hyphenated last names: "Callison-Burch" -> try "ccb" (first letters: C + C + B)
        first_last_full = normalize_text(''.join(author_parts).lower())  # Full: marcalexandrecote
        first_last_simple = normalize_text((first_name_parts[0] + last_name).lower())  # Simple: marccote
        # First letters pattern: first letter of each first name part + last name
        first_initials = ''.join([part[0] for part in first_name_parts])  # "ma" from "marc-alexandre"
        first_initials_last = normalize_text((first_initials + last_name).lower())  # "macote"
        
        # Handle hyphenated last names: "Callison-Burch" -> "ccb" (first letter of each part)
        last_name_parts = last_name.replace('-', ' ').split()
        if len(last_name_parts) > 1:
            last_initials = ''.join([part[0] for part in last_name_parts])  # "ccb" from "Callison-Burch"
            # Try first name initial + last name initials: "a" + "ccb" = "accb" (for "Andrew" + "Callison-Burch")
            first_initial_last_initials = normalize_text((first_name_parts[0][0] + last_initials).lower())
        else:
            last_initials = ""
            first_initial_last_initials = ""
        
        last_first = normalize_text((last_name + first_name).lower())  # clarkpeter
        email_username_normalized = normalize_text(email_username)  # Normalize email too
        
        # Check if email domain matches author's affiliation
        domain_bonus = 0.0
        # Get author's superscripts to find their affiliations for domain matching
        author_sups = author_superscripts.get(author_name, [])
        for sup in author_sups:
            institution = affiliation_map.get(sup, '').lower()
            if institution:
                # Check if domain matches institution keywords
                domain_keywords = {
                    'cmu': ['cmu', 'carnegie', 'mellon'],
                    'tsinghua': ['tsinghua', 'thu', 'mails.tsinghua'],
                    'peng cheng': ['peng', 'cheng'],
                    'shenzhen': ['shenzhen'],
                    'westlake': ['westlake'],
                    'tencent': ['tencent'],
                    'hku': ['hku', 'hong', 'kong', 'connect.hku'],
                    'sjtu': ['sjtu', 'jiao', 'tong'],
                    'microsoft': ['microsoft'],
                    'amazon': ['amazon']
                }
                for key, keywords in domain_keywords.items():
                    if any(kw in institution for kw in keywords):
                        if any(kw in email_domain for kw in keywords):
                            domain_bonus = 2.0  # Bonus for domain-affiliation match
                            break
        
        # Strategy 1: EXACT MATCHES (Highest confidence: 0.95-1.0)
        # Try all name combinations
        name_combinations = [
            (first_last_full, 15.0),      # Full name: marcalexandrecote
            (first_last_simple, 15.0),    # Simple: marccote
            (first_initials_last, 15.0),  # Initials: macote
            (last_first, 14.0),            # Last-first: cotealexandremarc
        ]
        
        # Add hyphenated last name patterns if applicable
        if last_initials:
            name_combinations.append((last_initials, 14.0))  # "ccb" from "Callison-Burch"
            if first_initial_last_initials:
                name_combinations.append((first_initial_last_initials, 14.0))  # "accb" from "Andrew" + "Callison-Burch"
        
        for name_combo, base_score in name_combinations:
            if email_username == name_combo:
                return (base_score + domain_bonus, 0.98)
            if email_username_normalized == name_combo:
                return (base_score + domain_bonus, 0.98)
        
        # Strategy 2: SUBSTRING MATCHES (High confidence: 0.85-0.95)
        # Check if email is contained in any name combination
        # Try normalized versions first (for accented characters)
        for name_combo, base_score in name_combinations:
            substr_score = substring_match_score(name_combo, email_username_normalized)
            if substr_score == 0:
                # Try non-normalized
                substr_score = substring_match_score(name_combo, email_username)
            if substr_score > 0:
                return (substr_score + domain_bonus, 0.90)
        
        # Strategy 3: HYPHENATED PATTERNS (High confidence: 0.85-0.95)
        # Pattern: lastname-firstname or lastname-initials (e.g., "zhang-zx21")
        if '-' in email_username:
            parts = email_username.split('-')
            if len(parts) >= 2:
                email_last = parts[0]
                email_first_or_initials = parts[1]
                
                # Check last name match (exact or letter-level)
                last_match = letter_match_score(last_name, email_last)
                if last_match >= 0.7:  # Good last name match
                    # Extract initials from email (e.g., "zx21" -> "zx")
                    email_initials = ''.join([c for c in email_first_or_initials if c.isalpha()])
                    
                    # Try to match initials - could be first 2 letters, or first+any letter from name
                    # For "Zhengxin" -> "zx": z (first) + x (appears in name)
                    author_first_letter = first_name[0]
                    author_second_letter = first_name[1] if len(first_name) > 1 else ''
                    
                    # Check if email initials match common patterns
                    if len(email_initials) >= 2:
                        # Pattern 1: First two letters (e.g., "zh" from "zhengxin")
                        if email_initials == (author_first_letter + author_second_letter).lower():
                            return (12.0 + domain_bonus, 0.92)
                        # Pattern 2: First letter + any letter from name (e.g., "zx" from "zhengxin")
                        if email_initials[0] == author_first_letter and email_initials[1] in first_name:
                            return (12.0 + domain_bonus, 0.90)
                        # Pattern 3: First letter matches and second is in name
                        if email_initials[0] == author_first_letter:
                            return (11.0 + domain_bonus, 0.88)
                    
                    # Check if first name or initials match (letter-level)
                    first_match = letter_match_score(first_name, email_first_or_initials)
                    if first_match >= 0.5:
                        return (12.0 + domain_bonus, 0.92)  # Strong match: lastname-initials
                    elif first_match >= 0.3:
                        return (10.0 + domain_bonus, 0.85)  # Good match with letter-level
        
        # Strategy 4: CONTINUOUS LETTERS + FIRST LETTER (Medium-high confidence: 0.70-0.85)
        # Pattern: Continuous sequence from first/last name + first letter of other name
        # Examples: "andrz" for "Andrew Zhu" = "andr" (first 4 of Andrew) + "z" (first of Zhu)
        #           "andz" for "Andrew Zhu" = "and" (first 3 of Andrew) + "z" (first of Zhu)
        first_name_norm = normalize_text(first_name)
        last_name_norm = normalize_text(last_name)
        
        # Try: first N letters of first name + first letter of last name
        for n in range(3, min(len(first_name_norm) + 1, 7)):  # Try 3 to 6 letters
            first_part = first_name_norm[:n]
            last_initial = last_name_norm[0] if last_name_norm else ''
            candidate = first_part + last_initial
            if candidate == email_username_normalized:
                # Longer match = higher confidence
                confidence = 0.75 + (n - 3) * 0.03  # 0.75 to 0.84
                return (8.0 + domain_bonus + (n - 3) * 0.5, confidence)
        
        # Try: first N letters of last name + first letter of first name
        for n in range(3, min(len(last_name_norm) + 1, 7)):  # Try 3 to 6 letters
            last_part = last_name_norm[:n]
            first_initial = first_name_norm[0] if first_name_norm else ''
            candidate = last_part + first_initial
            if candidate == email_username_normalized:
                # Longer match = higher confidence
                confidence = 0.70 + (n - 3) * 0.03  # 0.70 to 0.79
                return (7.5 + domain_bonus + (n - 3) * 0.5, confidence)
        
        # Strategy 5: EXACT FIRST/LAST NAME (Medium-high confidence: 0.75-0.85)
        if email_username == first_name:
            return (9.0 + domain_bonus, 0.80)  # Strong match: exact first name
        if email_username == last_name:
            return (8.0 + domain_bonus, 0.75)  # Less common but possible
        
        # Strategy 6: UNDERSCORE/DOT SEPARATED (Medium confidence: 0.70-0.80)
        if '_' in email_username:
            parts = email_username.split('_')
            if len(parts) >= 2:
                first_match = letter_match_score(first_name, parts[0])
                last_match = letter_match_score(last_name, parts[1])
                if first_match >= 0.7 and last_match >= 0.7:
                    return (7.5 + domain_bonus, 0.78)
                elif first_match >= 0.5 and last_match >= 0.5:
                    return (6.0 + domain_bonus, 0.70)
        
        if '.' in email_username:
            parts = email_username.split('.')
            if len(parts) >= 2:
                last_match = letter_match_score(last_name, parts[0])
                first_match = letter_match_score(first_name, parts[1])
                if last_match >= 0.7 and first_match >= 0.7:
                    return (7.5 + domain_bonus, 0.78)
                elif last_match >= 0.5 and first_match >= 0.5:
                    return (6.0 + domain_bonus, 0.70)
        
        # Strategy 7: LETTER-LEVEL ANAGRAM MATCHES (Medium confidence: 0.65-0.75)
        # Check if all letters from combined name appear in email (order-independent)
        reversed_match = letter_match_score(last_first, email_username)
        normal_match = letter_match_score(first_last_full, email_username)  # Use first_last_full instead
        
        if reversed_match >= 0.90:  # Very high for anagram-like
            return (9.0 + domain_bonus, 0.85)
        if normal_match >= 0.90:
            return (8.5 + domain_bonus, 0.85)
        if reversed_match >= 0.80:
            return (7.5 + domain_bonus, 0.75)
        if normal_match >= 0.80:
            return (7.0 + domain_bonus, 0.75)
        
        # Strategy 8: PARTIAL MATCHES (Lower confidence: 0.50-0.65)
        last_match = letter_match_score(last_name, email_username)
        first_match = letter_match_score(first_name, email_username)
        
        if last_match >= 0.7 and first_name[0] in email_username:
            return (5.5 + domain_bonus, 0.65)
        if first_match >= 0.7:
            return (4.5 + domain_bonus, 0.60)
        if last_match >= 0.7:
            return (3.5 + domain_bonus, 0.55)
        
        # Strategy 9: WEAK MATCHES (Low confidence: 0.30-0.50)
        full_match = letter_match_score(full_name, email_username)
        if full_match >= 0.5:
            return (2.0 + domain_bonus, 0.40)
        
        # Strategy 10: INITIAL COMBINATIONS (First + Last initials)
        first_initial_char = first_name_norm[0] if first_name_norm else ''
        last_initial_char = last_name_norm[0] if last_name_norm else ''
        if first_initial_char and last_initial_char:
            initials_combo = first_initial_char + last_initial_char
            reverse_combo = last_initial_char + first_initial_char
            letters_only = ''.join(ch for ch in email_username_normalized if ch.isalpha())
            if letters_only and (letters_only == initials_combo or letters_only == reverse_combo):
                return (8.2 + domain_bonus, 0.82)
            if email_username_normalized.startswith(initials_combo):
                return (7.8 + domain_bonus, 0.80)
            if email_username_normalized.startswith(reverse_combo):
                return (7.5 + domain_bonus, 0.78)
            if letters_only and len(letters_only) == 3:
                # Pattern: first initial + any letter from first name + last initial
                for mid_char in first_name_norm:
                    candidate = first_initial_char + mid_char + last_initial_char
                    if letters_only == candidate:
                        return (7.9 + domain_bonus, 0.82)
                # Pattern: first initial + any letter from last name + last initial
                for mid_char in last_name_norm:
                    candidate = first_initial_char + mid_char + last_initial_char
                    if letters_only == candidate:
                        return (7.7 + domain_bonus, 0.80)
        
        return (0.0, 0.0)
    
    # Match each author to the best email
    # IMPROVED LOGIC:
    # 1. First check if first name or last name is in email username
    # 2. If only one email matches, use it (high confidence)
    # 3. If multiple emails match, look at remaining letters (unmatched part) to disambiguate
    # 4. Use superscript hints: authors with same superscript should have similar email domains
    
    def normalize_text(text):
        """Normalize accented characters for matching."""
        nfd = unicodedata.normalize('NFD', text)
        return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
    
    def simple_name_match(author_name: str, email: str) -> tuple[bool, str, str]:
        """
        Check if first name or last name appears in email username.
        Returns: (matches, matched_part, remaining_part)
        - matched_part: which part matched ("first", "last", or "both")
        - remaining_part: the part of email username not covered by matched name
        """
        author_parts = author_name.lower().split()
        if len(author_parts) < 2:
            return (False, "", "")
        
        email_username = email.split('@')[0].lower()
        email_norm = normalize_text(email_username)
        
        # Check first name (handle hyphenated names)
        first_name_parts = author_parts[0].replace('-', ' ').split()
        first_matched = False
        matched_first_part = ""
        for part in first_name_parts:
            part_norm = normalize_text(part)
            if part_norm in email_norm:
                first_matched = True
                matched_first_part = part_norm
                break
        
        # Check last name (handle hyphenated last names like "Callison-Burch")
        last_name = author_parts[-1]
        last_name_parts = last_name.replace('-', ' ').split()  # Split hyphenated last name
        last_name_norm = normalize_text(last_name)
        last_matched = last_name_norm in email_norm
        
        # Also check if email matches first letters of hyphenated last name parts
        # Example: "ccb" matches "Callison-Burch" (C + C + B)
        if not last_matched and len(last_name_parts) > 1:
            # Try first letters of each part
            last_initials = ''.join([part[0].lower() for part in last_name_parts])
            if last_initials in email_norm:
                last_matched = True
                # For matching, treat as if last name matched
                last_name_norm = last_initials
        
        if first_matched and last_matched:
            # Both matched - remaining is what's left after removing both
            remaining = email_norm.replace(matched_first_part, '', 1).replace(last_name_norm, '', 1)
            return (True, "both", remaining)
        elif first_matched:
            # First name matched - remaining is email minus first name
            remaining = email_norm.replace(matched_first_part, '', 1)
            return (True, "first", remaining)
        elif last_matched:
            # Last name matched - remaining is email minus last name
            remaining = email_norm.replace(last_name_norm, '', 1)
            return (True, "last", remaining)
        
        # Also check if email is first letters of first name + first letters of last name parts
        # Example: "andrz" could be "a" (first of Andrew) + "n" + "d" + "r" + "z" (first of Zhu)
        # Or "ccb" could be first letters of "Callison-Burch" (C + C + B)
        if len(last_name_parts) > 1:
            last_initials = ''.join([part[0].lower() for part in last_name_parts])
            if last_initials in email_norm:
                # Email contains initials of hyphenated last name
                remaining = email_norm.replace(last_initials, '', 1)
                return (True, "last", remaining)
        
        return (False, "", "")
    
    def check_remaining_letters_match(remaining: str, author_name: str, matched_part: str) -> float:
        """
        Check if remaining letters in email match the other part of author name.
        Returns confidence score (0.0-1.0).
        """
        if not remaining:
            return 0.0
        
        author_parts = author_name.lower().split()
        first_name_parts = author_parts[0].replace('-', ' ').split()
        last_name = normalize_text(author_parts[-1])
        
        if matched_part == "first":
            # Remaining should match last name (or part of it)
            # Check if remaining letters are from last name
            remaining_chars = set(remaining)
            last_name_chars = set(last_name)
            if remaining_chars.issubset(last_name_chars):
                # All remaining letters are in last name
                coverage = len(remaining_chars) / len(last_name_chars) if last_name_chars else 0.0
                return coverage
            # Check if remaining is a substring of last name
            if remaining in last_name:
                return 0.9
        elif matched_part == "last":
            # Remaining should match first name (or part of it)
            for part in first_name_parts:
                part_norm = normalize_text(part)
                remaining_chars = set(remaining)
                part_chars = set(part_norm)
                if remaining_chars.issubset(part_chars):
                    coverage = len(remaining_chars) / len(part_chars) if part_chars else 0.0
                    return coverage
                if remaining in part_norm:
                    return 0.9
        
        return 0.0
    
    # Get author superscripts for domain matching
    # Authors with same superscript should have similar email domains
    superscript_to_domains = {}  # superscript -> set of email domains
    for author in authors:
        author_sups = author_superscripts.get(author, [])
        for sup in author_sups:
            if sup not in superscript_to_domains:
                superscript_to_domains[sup] = set()
    
    # EMAIL-CENTRIC APPROACH: For each email, find all matching authors and pick the best one
    # This ensures that when multiple authors match the same email, we pick the best match
    
    # Step 1: Build email_to_candidates: email -> list of (author, matched_part, remaining)
    email_to_candidates = {}  # email -> list of (author, matched_part, remaining)
    for email in emails:
        candidates = []
        for author in authors:
            matches, matched_part, remaining = simple_name_match(author, email)
            if matches:
                candidates.append((author, matched_part, remaining))
        if candidates:
            email_to_candidates[email] = candidates
    
    # Step 2: Detect ambiguous emails (multiple authors match only via first name)
    ambiguous_emails = set()
    for email, candidates in email_to_candidates.items():
        if len(candidates) > 1:
            # If none of the matches include last name information, we can't disambiguate
            if not any(part in ("last", "both") for _, part, _ in candidates):
                ambiguous_emails.add(email)
    
    # Step 3: Group authors by last name to detect conflicts
    authors_by_lastname = {}
    for author in authors:
        last_name = author.split()[-1].lower()
        if last_name not in authors_by_lastname:
            authors_by_lastname[last_name] = []
        authors_by_lastname[last_name].append(author)
    
    # Step 4: For each email, score all matching authors and assign to the best one
    author_to_email = {}
    email_to_author = {}
    email_confidence = {}
    
    def score_author_email_match(author: str, email: str, matched_part: str, remaining: str) -> tuple[float, float]:
        """Score how well an author matches an email. Returns (score, confidence)."""
        score = 0.0
        confidence = 0.0
        
        email_username = email.split('@')[0].lower()
        email_norm = normalize_text(email_username)
        
        # Base score based on what matched
        if matched_part == "both":
            score += 10.0  # Highest priority: both first and last name matched
            confidence = 0.88
        elif matched_part == "first":
            score += 5.0
            confidence = 0.75
        elif matched_part == "last":
            score += 3.0
            confidence = 0.70
            
            # For "last" only matches, check first initial alignment
            first_initial = normalize_text(author.split()[0][0].lower())
            if email_norm.startswith(first_initial):
                score += 2.0  # Bonus if email starts with first initial
                confidence = max(confidence, 0.80)
        else:
                score -= 5.0  # Penalty if first initial doesn't match
                confidence = max(confidence, 0.50)
                
                # Additional penalty if another author with same last name has matching initial
                last_name = author.split()[-1].lower()
                conflicting_authors = [a for a in authors_by_lastname.get(last_name, []) if a != author]
                for other_author in conflicting_authors:
                    other_matches, other_part, _ = simple_name_match(other_author, email)
                    if other_matches and other_part == "last":
                        other_first_initial = normalize_text(other_author.split()[0][0].lower())
                        if email_norm.startswith(other_first_initial):
                            score -= 20.0  # Strong penalty - another author matches better
                            break
        
        # Check remaining letters match (bonus)
        remaining_score = check_remaining_letters_match(remaining, author, matched_part)
        if remaining_score > 0:
            score += remaining_score * 10.0
            confidence = max(confidence, 0.85 + remaining_score * 0.1)
        
        # Check domain match (authors with same superscript should have similar domain)
        author_sups = author_superscripts.get(author, [])
        author_domains = set()
        for sup in author_sups:
                for other_author in authors:
                if other_author != author and other_author in author_to_email:
                    other_email = author_to_email[other_author]
                    other_sups = author_superscripts.get(other_author, [])
                    if sup in other_sups:
                        domain = other_email.split('@')[1] if '@' in other_email else ''
                        if domain:
                            author_domains.add(domain)
        
        email_domain = email.split('@')[1] if '@' in email else ''
        if email_domain in author_domains:
            score += 5.0  # Bonus for domain match
            confidence = max(confidence, 0.90)
        
        return (score, confidence)
    
    # Process emails in order, assigning each to the best matching author
    for email in emails:
        if email in ambiguous_emails:
            continue  # Skip ambiguous emails
        
        if email not in email_to_candidates:
            continue  # No simple matches, will use complex logic later
        
        candidates = email_to_candidates[email]
        
        # Score all candidates
        scored_candidates = []
        for author, matched_part, remaining in candidates:
            # Skip if author already has an email assigned
            if author in author_to_email:
                continue
            
            score, confidence = score_author_email_match(author, email, matched_part, remaining)
            scored_candidates.append((author, score, confidence, matched_part))
        
        if not scored_candidates:
            continue  # All candidates already have emails
        
        # Sort by score (highest first), then by confidence
        scored_candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        # Assign email to the best matching author
        best_author, best_score, best_confidence, _ = scored_candidates[0]
        
        # Only assign if score is positive (good match)
        if best_score > 0:
            author_to_email[best_author] = email
            email_to_author[email] = best_author
            email_confidence[email] = best_confidence
    
    # Third pass: For emails with no simple match, use complex logic (includes secondary rules)
    # This applies all strategies including continuous letters + first letter pattern
    # EMAIL-CENTRIC: For each unassigned email, find all matching authors and pick the best one
    for email in emails:
        if email in email_to_author or email in ambiguous_emails:
            continue  # Already assigned or ambiguous
        
        # Find all authors that match this email using complex matching
        email_candidates = []
        for author in authors:
            if author in author_to_email:
                continue  # Author already has an email
            
            score, confidence = match_score(author, email)
            if score > 0:
                email_candidates.append((author, score, confidence))
        
        if not email_candidates:
            continue  # No matches found
        
        # Sort by score (highest first), then by confidence
        email_candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        # Check for ambiguous cases (multiple authors with same first name and similar scores)
        best_author, best_score, best_confidence = email_candidates[0]
        best_first = best_author.split()[0].lower()
        
        is_ambiguous = False
        if len(email_candidates) > 1:
            second_author, second_score, second_conf = email_candidates[1]
            second_first = second_author.split()[0].lower()
            
            # Check if ambiguous: same first name and similar scores
            if best_first == second_first and abs(best_score - second_score) <= 2.0:
                is_ambiguous = True
            # Also check if any other candidate has same first name and similar score
            elif best_first == second_first:
                for other_author, other_score, other_conf in email_candidates[1:]:
                        other_first = other_author.split()[0].lower()
                    if other_first == best_first and abs(other_score - best_score) <= 2.0 and abs(other_conf - best_confidence) <= 0.15:
                        is_ambiguous = True
                        break
        
        if is_ambiguous:
                                ambiguous_emails.add(email)
        else:
            # Assign email to the best matching author
            author_to_email[best_author] = email
            email_to_author[email] = best_author
            email_confidence[email] = best_confidence
    
    # Create final pairs with confidence scores
    for author in authors:
        email = author_to_email.get(author, '')
        confidence = email_confidence.get(email, 0.0) if email else 0.0
        
        # Only include email if it's not ambiguous and has reasonable confidence
        # User prefers precision over recall - only high-confidence matches
        # Lowered threshold to 0.50 to catch more matches (can adjust based on results)
        if email in ambiguous_emails or confidence < 0.50:  # Lower threshold to catch more matches
            email = ''
            confidence = 0.0
        
        author_email_pairs.append({
            'author': author,
            'email': email,
            'confidence': confidence
        })
    
    # Don't add unmatched emails - we only want author-email pairs
    # If we can't match an email to an author, we skip it (precision over recall)
    
    # Identify first and last authors
    first_author = authors[0] if authors else None
    last_author = authors[-1] if authors else None
    
    result = {
        'url': url,
        'title': title or 'Unknown',
        'authors': authors,
        'emails': emails,
        'author_email_pairs': author_email_pairs,
        'author_institutions': author_institutions,  # Add institutions mapping
        'first_author': first_author,  # Track first author
        'last_author': last_author  # Track last author
    }
    
    logger.info(f"  Title: {title[:60] if title else 'Unknown'}...")
    logger.info(f"  Authors: {len(authors)}, Emails: {len(emails)}")
    
    return result


def save_results(results: List[Dict], output_file: str = 'acl_papers_info.csv', append: bool = False):
    """Save results to CSV file."""
    if not results:
        logger.warning("No results to save")
        return
    
    output_path = Path(output_file)
    
    # Prepare data for CSV
    rows = []
    for result in results:
        if not result:
            continue
        
        # Create one row per author-email pair
        authors_list = result.get('authors', [])
        first_author = result.get('first_author', '')
        last_author = result.get('last_author', '')
        
        if result['author_email_pairs']:
            for pair in result['author_email_pairs']:
                confidence = pair.get('confidence', 0.0)
                # Format confidence as percentage
                confidence_pct = f"{confidence * 100:.0f}%" if confidence > 0 else ""
                # Get institution for this author
                author = pair['author']
                institution = result.get('author_institutions', {}).get(author, '')
                
                # Get author order (1-based index)
                author_order = ''
                if author in authors_list:
                    author_order = str(authors_list.index(author) + 1)
                
                # Check if first or last author
                is_first_author = 'Yes' if author == first_author else ''
                is_last_author = 'Yes' if author == last_author else ''
                
                rows.append({
                    'Paper URL': result['url'],
                    'Paper Title': result['title'],
                    'Author': author,
                    'Author Order': author_order,
                    'First Author': is_first_author,
                    'Last Author': is_last_author,
                    'Email': pair['email'],
                    'Confidence': confidence_pct,  # Confidence for email match (our focus)
                    'Institution': institution
                })
        # Don't add unmatched authors or emails - we only want matched pairs
    
    # Write CSV
    if rows:
        mode = 'a' if append and output_path.exists() else 'w'
        with open(output_path, mode, newline='', encoding='utf-8') as f:
            fieldnames = ['Paper URL', 'Paper Title', 'Author', 'Author Order', 'First Author', 'Last Author', 'Email', 'Confidence', 'Institution']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if mode == 'w' or not append:  # Write header if new file or not appending
                writer.writeheader()
            writer.writerows(rows)
        
        action = "Appended" if append else "Saved"
        logger.info(f"{action} {len(rows)} rows to {output_path.absolute()}")
    else:
        logger.warning("No data to write to CSV")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extract information from ACL PDFs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single paper
  python extract_acl_info.py "https://aclanthology.org/2024.acl-long.1.pdf"
  
  # Range of papers (1 to 10)
  python extract_acl_info.py --range 1 10
  
  # Specific papers
  python extract_acl_info.py --range 1 5 7 10
  
  # From file
  python extract_acl_info.py --urls-file urls.txt
        """
    )
    parser.add_argument('url', nargs='?', help='ACL PDF URL to process')
    parser.add_argument('--urls-file', type=str, help='File with list of URLs (one per line)')
    parser.add_argument('--range', type=int, nargs='+', 
                       help='Range of paper numbers (e.g., --range 1 10 or --range 1 5 7 10)')
    parser.add_argument('--year', type=int, default=2024, help='Conference year (default: 2024)')
    parser.add_argument('--track', type=str, default='long', 
                       choices=['long', 'short', 'main', 'findings'],
                       help='Paper track (default: long). For 2020, use "main". For 2021-2025, can use "findings"')
    parser.add_argument('--output', type=str, default='acl_papers_info.csv', help='Output CSV file')
    parser.add_argument('--append', action='store_true', help='Append to existing CSV file')
    parser.add_argument('--json', type=str, help='Also save as JSON file')
    parser.add_argument('--auto-detect', action='store_true', 
                       help='Auto-detect paper range by trying papers until 404 error')
    
    args = parser.parse_args()
    
    # Check if PDF library is available
    if PDF_LIB is None:
        logger.error("Please install a PDF library:")
        logger.error("  pip install PyPDF2")
        logger.error("  or")
        logger.error("  pip install pdfplumber")
        return
    
    logger.info(f"Using PDF library: {PDF_LIB}")
    
    # Helper function to generate URL based on year format
    def generate_url(year: int, track: str, paper_num: int) -> str:
        """Generate ACL URL based on year format."""
        if year >= 2021:
            # 2021-2025: Handle both regular tracks and findings
            if track == "findings":
                # Findings track: {year}.findings-acl.{num}.pdf
                return f"https://aclanthology.org/{year}.findings-acl.{paper_num}.pdf"
            else:
                # Regular tracks: {year}.acl-{track}.{num}.pdf
            return f"https://aclanthology.org/{year}.acl-{track}.{paper_num}.pdf"
        elif year == 2020:
            # 2020: {year}.acl-main.{num}.pdf (no track differentiation, starts from 1)
            return f"https://aclanthology.org/{year}.acl-main.{paper_num}.pdf"
        elif year == 2019:
            # 2019: P19-{num}.pdf (starts from 1001)
            return f"https://aclanthology.org/P19-{paper_num}.pdf"
        else:
            # For older years, try the modern format
            return f"https://aclanthology.org/{year}.acl-{track}.{paper_num}.pdf"
    
    # Get starting paper number based on year
    def get_start_paper(year: int) -> int:
        """Get starting paper number for auto-detect based on year."""
        if year == 2020:
            return 100  # 2020 starts from 100
        elif year == 2019:
            return 1001  # 2019 starts from 1001
        else:
            return 1  # 2021-2024 start from 1
    
    # Get URLs to process
    urls = []
    
    if args.range:
        # Generate URLs from range
        if len(args.range) == 2:
            # Range: --range 1 10
            start, end = args.range
            # Get minimum start based on year
            min_start = get_start_paper(args.year)
            start = max(min_start, start)
            paper_numbers = range(start, end + 1)
        elif len(args.range) > 2:
            # Specific numbers: --range 1 5 7 10
            min_start = get_start_paper(args.year)
            paper_numbers = sorted(set([max(min_start, n) for n in args.range]))
        else:
            logger.error("--range requires at least 2 numbers")
            return
        
        for num in paper_numbers:
            urls.append(generate_url(args.year, args.track, num))
        logger.info(f"Generated {len(urls)} URLs from range")
    elif args.auto_detect:
        # Auto-detect paper range by trying papers until 404
        track_display = args.track if args.year >= 2021 else ("main" if args.year == 2020 else "P19-")
        print(f"Auto-detecting paper range for {args.year} ({track_display})...")
        
        paper_num = get_start_paper(args.year)
        max_papers = 10000  # Safety limit
        consecutive_404s = 0
        last_found = 0
        
        print("Scanning papers (this may take a while)...")
        while paper_num <= max_papers:
            url = generate_url(args.year, args.track, paper_num)
            try:
                response = requests.head(url, timeout=10, allow_redirects=True)
                if response.status_code == 404:
                    consecutive_404s += 1
                    # If we get 3 consecutive 404s, we've reached the end
                    if consecutive_404s >= 3:
                        start_num = get_start_paper(args.year)
                        print(f"\n✓ Reached end of papers at {last_found}")
                        print(f"  Found {len(urls)} papers total (range: {start_num} to {last_found})")
                        break
                else:
                    consecutive_404s = 0
                    urls.append(url)
                    last_found = paper_num
                    # Print progress every 10 papers
                    if paper_num % 10 == 0:
                        print(f"  Found papers up to {paper_num}...", end='\r')
                paper_num += 1
            except Exception as e:
                logger.warning(f"Error checking {url}: {e}")
                consecutive_404s += 1
                if consecutive_404s >= 3:
                    break
                paper_num += 1
        
        if not urls:
            print(f"\n✗ No papers found for {args.year}")
            return
        start_num = get_start_paper(args.year)
        print(f"\n✓ Auto-detected {len(urls)} papers (range: {start_num} to {last_found})")
        
    elif args.url:
        urls.append(args.url)
    elif args.urls_file:
        with open(args.urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    else:
        # Test with example URL
        test_url = "https://aclanthology.org/2024.acl-long.1.pdf"
        logger.info(f"No URL provided, using test URL: {test_url}")
        urls.append(test_url)
    
    # Process URLs with progress tracking and real-time saving
    results = []
    total_urls = len(urls)
    
    for idx, url in enumerate(urls, 1):
        # Print progress
        print(f"\n[{idx}/{total_urls}] Processing: {url}")
        
        result = parse_acl_pdf(url)
        if result:
            results.append(result)
            # Save incrementally after each paper
            # Append after first paper (idx > 0) or if --append flag is set
            save_results([result], args.output, append=(idx > 0 or args.append))
            print(f"  ✓ Saved to {args.output}")
        else:
            print(f"  ✗ Failed or not found (404)")
    
    # Final summary
    if results:
        print(f"\n{'='*60}")
        print(f"Summary: Processed {len(results)}/{total_urls} papers successfully")
        print(f"Results saved to: {args.output}")
        
        total_authors = sum(len(r['authors']) for r in results)
        total_emails = sum(len(r['emails']) for r in results)
        print(f"  Total authors: {total_authors}")
        print(f"  Total emails: {total_emails}")
        print("="*60)
        
        if args.json:
            with open(args.json, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"JSON saved to: {args.json}")
            logger.info(f"Also saved JSON to {args.json}")


if __name__ == "__main__":
    main()

