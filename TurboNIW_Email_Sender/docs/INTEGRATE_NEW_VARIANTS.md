# How to Integrate New Email Variants

## Overview

I've created **10 additional email variants** (variants 6-15) in `email_templates_variants_new.py` to increase diversity and reduce Google's detection of repeated messages.

**Current**: 5 variants  
**After integration**: 15 variants total

## What's Included

### New Subject Lines (10 variants)
- Variants 6-15: Additional subject line options
- All follow the same empathetic, friendly tone
- No placeholders (matching current system)

### New Email Bodies (10 variants)
- Variants 6-15: Additional body text options
- Maintains empathetic, community-understanding tone
- Uses commas and natural breaks (no "---" separators)
- Varied sentence structures and phrasings

## Integration Steps

### Step 1: Backup Current File
```bash
cp email_templates_variants.py email_templates_variants.py.backup
```

### Step 2: Add New Subject Variants

In `email_templates_variants.py`, update `SUBJECT_VARIANTS`:

```python
SUBJECT_VARIANTS = [
    # Existing variants 1-5
    "Greetings from Wen, a resource you might find helpful",
    "Hi from Wen, sharing a helpful NIW resource",
    "Hello from Wen, a resource for NIW applications",
    "Quick hello and a resource to share",
    "Hi, Wen here, wanted to share something helpful",
    
    # New variants 6-15 (from email_templates_variants_new.py)
    "Hello, sharing something that might help",
    "Reaching out about your work and a resource",
    "Hi there, Wen here with a quick note",
    "A resource for researchers like us",
    "Hope you're doing well, wanted to share this",
    "Hi, thought this might be useful",
    "From one researcher to another",
    "Hello, sharing a resource you might find helpful",
    "Hi, hope this finds you well",
    "A helpful tool for the research community",
]
```

### Step 3: Add New Body Variants

In `email_templates_variants.py`, add the new body variants after the existing ones:

```python
# Add these after EMAIL_BODY_VARIANT_5
EMAIL_BODY_VARIANT_6 = """..."""
EMAIL_BODY_VARIANT_7 = """..."""
# ... etc (copy from email_templates_variants_new.py)
```

### Step 4: Update Variant Selection

In `get_random_email_body()`, update the variants list:

```python
def get_random_email_body(name, paper_title="", publication_venue="arXiv"):
    first_name = name.split()[0] if name and name.strip() else name
    
    variants = [
        EMAIL_BODY_VARIANT_1,
        EMAIL_BODY_VARIANT_2,
        EMAIL_BODY_VARIANT_3,
        EMAIL_BODY_VARIANT_4,
        EMAIL_BODY_VARIANT_5,
        EMAIL_BODY_VARIANT_6,  # New
        EMAIL_BODY_VARIANT_7,  # New
        EMAIL_BODY_VARIANT_8,  # New
        EMAIL_BODY_VARIANT_9,  # New
        EMAIL_BODY_VARIANT_10, # New
        EMAIL_BODY_VARIANT_11, # New
        EMAIL_BODY_VARIANT_12, # New
        EMAIL_BODY_VARIANT_13, # New
        EMAIL_BODY_VARIANT_14, # New
        EMAIL_BODY_VARIANT_15, # New
    ]
    
    template = random.choice(variants)
    return template.format(name=first_name, paper_title=paper_title)
```

## Key Features of New Variants

✅ **Maintains empathetic tone** - Same understanding, community-focused approach  
✅ **Natural language** - Uses commas and natural breaks, no "---" separators  
✅ **Varied structures** - Different sentence patterns and phrasings  
✅ **Same core message** - All convey the same helpful, non-pushy information  
✅ **Increased diversity** - 3x more variants to reduce repetition detection

## Testing

After integration, test by:
1. Running a few test emails to see variant selection
2. Checking that all variants format correctly
3. Verifying the tone matches your current emails

## When to Integrate

**Wait until your current sending session is complete** before making changes to avoid interrupting the running process.

## Notes

- All new variants use the same signature format
- No "---" separators (as requested)
- Natural, conversational tone maintained
- Varied phrasings for the same concepts to avoid detection

