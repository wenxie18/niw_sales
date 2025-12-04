#!/usr/bin/env python3
"""
Script to collect all ACL papers from 2019 to 2025.

Year formats:
- 2019: P19-{num}.pdf (starts from 1001)
- 2020: {year}.acl-main.{num}.pdf (starts from 1)
- 2021-2025: {year}.acl-{track}.{num}.pdf (short and long tracks, starts from 1)
- 2021-2025: {year}.findings-acl.{num}.pdf (findings track, starts from 1)
"""

import subprocess
import sys
import requests
from pathlib import Path

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
        # 2020: {year}.acl-main.{num}.pdf (no track differentiation)
        return f"https://aclanthology.org/{year}.acl-main.{paper_num}.pdf"
    elif year == 2019:
        # 2019: P19-{num}.pdf
        return f"https://aclanthology.org/P19-{paper_num}.pdf"
    else:
        return f"https://aclanthology.org/{year}.acl-{track}.{paper_num}.pdf"

def get_start_paper(year: int) -> int:
    """Get starting paper number based on year."""
    if year == 2019:
        return 1001  # 2019 starts from 1001 (P19-1001.pdf)
    else:
        return 1  # 2020-2025 start from 1

def auto_detect_max_paper(year: int, track: str = None) -> int:
    """Auto-detect the maximum paper number by scanning until 3 consecutive 404s."""
    start_num = get_start_paper(year)
    paper_num = start_num
    max_papers = 10000  # Safety limit
    consecutive_404s = 0
    last_found = 0
    
    track_display = track or ("main" if year == 2020 else "papers" if year == 2019 else "unknown")
    print(f"  Auto-detecting max paper for {year} {track_display} (starting from {start_num})...")
    
    while paper_num <= max_papers:
        # generate_url handles 2019 correctly (ignores track), so we can pass track or "main"
        url = generate_url(year, track or "main", paper_num)
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code == 404:
                consecutive_404s += 1
                # If we get 3 consecutive 404s, we've reached the end
                if consecutive_404s >= 3:
                    if last_found > 0:
                        print(f"  ✓ Found max paper: {last_found} (range: {start_num} to {last_found})")
                        return last_found
                    else:
                        print(f"  ✗ No papers found starting from {start_num}")
                        return start_num - 1  # Return value below start to indicate no papers
            else:
                consecutive_404s = 0
                last_found = paper_num
                # Print progress every 50 papers
                if paper_num % 50 == 0:
                    print(f"    Scanning... found papers up to {paper_num}", end='\r')
            paper_num += 1
        except Exception as e:
            print(f"    Warning: Error checking {url}: {e}")
            consecutive_404s += 1
            if consecutive_404s >= 3:
                break
            paper_num += 1
    
    # If we hit the safety limit, return what we found
    if last_found > 0:
        print(f"  ⚠ Reached safety limit, using last found: {last_found}")
        return last_found
    else:
        print(f"  ✗ No papers found")
        return start_num - 1

def collect_year(year: int, track: str = None, start_num: int = None, end_num: int = None, output_file: str = None, auto_detect: bool = True):
    """Collect papers for a specific year and track."""
    if output_file is None:
        # Create data/acl directory if it doesn't exist
        output_dir = Path("data/acl")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = f"data/acl/acl_{year}"
        if track and year >= 2021:  # Only add track for 2021+ (includes short, long, findings)
            output_file += f"_{track}"
        output_file += ".csv"
    
    # Determine start number
    if start_num is None:
        start_num = get_start_paper(year)
    
    # Auto-detect end number if not provided
    if end_num is None and auto_detect:
        end_num = auto_detect_max_paper(year, track)
        if end_num < start_num:
            print(f"  ✗ No papers found for {year} {track or 'papers'}, skipping...")
            return False
    elif end_num is None:
        # Fallback: use a reasonable upper bound if auto-detect is disabled
        if year == 2019:
            end_num = 5000
        elif year == 2020:
            end_num = 1000
        else:
            end_num = 500
    
    # Build command
    cmd = [
        sys.executable,
        "extract_acl_info_v2.py",
        "--range", str(start_num), str(end_num),
        "--year", str(year),
        "--output", output_file
    ]
    
    # Only add track for 2020+ (2020 uses "main", 2021+ uses "short"/"long")
    # 2019 doesn't use track parameter
    if track and year >= 2020:
        cmd.extend(["--track", track])
    
    track_display = track or ("papers" if year == 2019 else "main" if year == 2020 else "unknown")
    print(f"\n{'='*60}")
    print(f"Collecting {year} {track_display}: papers {start_num} to {end_num}")
    print(f"Output: {output_file}")
    print(f"{'='*60}\n")
    
    # Run the extraction
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        print(f"\n✓ Successfully collected {year} {track_display}")
        return True
    else:
        print(f"\n✗ Error collecting {year} {track_display}")
        return False

def main():
    """Main function to collect all papers from 2019 to 2025."""
    print("="*60)
    print("ACL Papers Collection Script (2019-2025)")
    print("="*60)
    
    # Configuration: year -> list of tracks
    # For 2019, we use "papers" but the URL format is P19-{num}
    # For 2020, we use "main"
    # For 2021-2025, we use "short", "long", and "findings" tracks
    
    years_config = {
        2019: [(None, None, None)],  # No track for 2019 (uses P19- format), start, end (None = auto)
        2020: [("main", None, None)],
        2021: [("short", None, None), ("long", None, None), ("findings", None, None)],
        2022: [("short", None, None), ("long", None, None), ("findings", None, None)],
        2023: [("short", None, None), ("long", None, None), ("findings", None, None)],
        2024: [("short", None, None), ("long", None, None), ("findings", None, None)],
        2025: [("short", None, None), ("long", None, None), ("findings", None, None)],
    }
    
    # You can also specify custom ranges if needed:
    # years_config = {
    #     2019: [("papers", 1001, 2000)],  # Custom range
    #     2020: [("main", 100, 500)],
    #     ...
    # }
    
    all_results = []
    
    for year in sorted(years_config.keys()):
        for track_info in years_config[year]:
            if len(track_info) == 3:
                track, start_num, end_num = track_info
            elif len(track_info) == 1:
                track = track_info[0]
                start_num = None
                end_num = None
            else:
                track = None
                start_num = None
                end_num = None
            
            success = collect_year(year, track, start_num, end_num)
            all_results.append((year, track, success))
    
    # Summary
    print("\n" + "="*60)
    print("COLLECTION SUMMARY")
    print("="*60)
    
    for year, track, success in all_results:
        status = "✓" if success else "✗"
        track_display = track or ("papers" if year == 2019 else "main" if year == 2020 else "unknown")
        print(f"{status} {year} {track_display}")
    
    successful = sum(1 for _, _, s in all_results if s)
    total = len(all_results)
    print(f"\nTotal: {successful}/{total} collections successful")
    
    # Optionally, combine all CSVs into one
    print("\n" + "="*60)
    print("To combine all CSVs into one file, you can use:")
    print("  python combine_csvs.py")
    print("="*60)

if __name__ == "__main__":
    main()

