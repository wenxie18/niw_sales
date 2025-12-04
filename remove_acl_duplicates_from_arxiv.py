#!/usr/bin/env python3
"""
Remove emails from arXiv CSV that already exist in ACL CSV.
"""

import pandas as pd
from pathlib import Path

# File paths
ACL_FILE = "data/acl/acl_high_confidence.csv"
ARXIV_FILE = "data/arxiv/round1/arxiv_high_confidence_non_chinese.csv"
OUTPUT_FILE = "data/arxiv/round1/arxiv_high_confidence_non_chinese_no_acl.csv"

print("=" * 80)
print("REMOVING ACL DUPLICATES FROM ARXIV")
print("=" * 80)

# Load ACL emails
print(f"\n📂 Loading ACL file: {ACL_FILE}")
acl_df = pd.read_csv(ACL_FILE, encoding='utf-8')
acl_emails = set(acl_df['Email'].str.lower().str.strip())
print(f"   ✓ Loaded {len(acl_df):,} ACL records")
print(f"   ✓ Found {len(acl_emails):,} unique ACL emails")

# Load arXiv data
print(f"\n📂 Loading arXiv file: {ARXIV_FILE}")
arxiv_df = pd.read_csv(ARXIV_FILE, encoding='utf-8')
print(f"   ✓ Loaded {len(arxiv_df):,} arXiv records")

# Find duplicates
print(f"\n🔍 Checking for duplicates...")
arxiv_df['email_lower'] = arxiv_df['Email'].str.lower().str.strip()
duplicates_mask = arxiv_df['email_lower'].isin(acl_emails)
duplicates_count = duplicates_mask.sum()

print(f"   ⚠️  Found {duplicates_count:,} arXiv records with ACL email duplicates")

# Show some examples
if duplicates_count > 0:
    print(f"\n📋 Sample duplicate emails (first 10):")
    duplicate_emails = arxiv_df[duplicates_mask]['Email'].head(10).tolist()
    for i, email in enumerate(duplicate_emails, 1):
        print(f"   {i}. {email}")

# Remove duplicates
arxiv_clean_df = arxiv_df[~duplicates_mask].copy()
arxiv_clean_df = arxiv_clean_df.drop(columns=['email_lower'])

print(f"\n✅ Cleaned arXiv data:")
print(f"   Original records:  {len(arxiv_df):,}")
print(f"   Removed:           {duplicates_count:,}")
print(f"   Remaining:         {len(arxiv_clean_df):,}")

# Check unique emails
unique_emails_before = arxiv_df['Email'].nunique()
unique_emails_after = arxiv_clean_df['Email'].nunique()
print(f"\n📊 Unique emails:")
print(f"   Before: {unique_emails_before:,}")
print(f"   After:  {unique_emails_after:,}")

# Save cleaned file
print(f"\n💾 Saving cleaned file to: {OUTPUT_FILE}")
Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
arxiv_clean_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
print(f"   ✓ Saved successfully!")

print("\n" + "=" * 80)
print("COMPLETE!")
print("=" * 80)
print(f"\n✅ Use this file for sending emails: {OUTPUT_FILE}")
print(f"   (No ACL duplicates)")

