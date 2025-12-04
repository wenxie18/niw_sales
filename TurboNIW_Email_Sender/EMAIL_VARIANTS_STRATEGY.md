# Email Variants Strategy — Avoiding Spam Filters

## 🎯 Goal
**Avoid spam filters while maintaining authentic, helpful communication.**

---

## ⚠️ Why Email Variants Matter

### The Problem with Identical Emails
Sending the **exact same email** repeatedly triggers:

1. **Gmail/Outlook Spam Filters**
   - Detect mass mailing patterns
   - Lower sender reputation score
   - Move emails to spam folder

2. **Anti-Spam Algorithms**
   - Subject line fingerprinting
   - Body text similarity analysis
   - Link pattern detection

3. **User Perception**
   - Generic emails feel impersonal
   - "One-size-fits-all" approach reduces trust
   - Higher unsubscribe/report rates

---

## ✅ Our Solution: Multi-Variant Email System

### 1. **5 Subject Line Variants**
Each email randomly selects from 5 different subject lines:

| Variant | Subject Line |
|---------|-------------|
| 1 | "A resource for NIW green card applications (from a fellow researcher)" |
| 2 | "Quick NIW resource that might help your students/colleagues" |
| 3 | "Thought this might be useful — NIW DIY tool for researchers" |
| 4 | "Following up on your {venue} work — NIW resource to share" |
| 5 | "NIW green card resource (in case it's helpful)" |

**Why this helps:**
- ✅ Each recipient gets a different subject → breaks mass-mailing pattern
- ✅ Subjects are conversational, not salesy
- ✅ Includes context-specific variables (`{venue}`)

---

### 2. **5 Email Body Variants**
Each email body has the **same core message**, but different wording:

| Element | Variation Strategy |
|---------|-------------------|
| **Opening** | "Hi {name}, I hope you're doing well" / "Hi {name}, I hope this finds you well" / "Hi {name}, I hope you're having a good week" |
| **Context** | References their work at {venue}, mentions CET list, explains NIW relevance |
| **Personal Story** | Shares your PhD experience, immigration challenges, motivation for building TurboNIW |
| **Value Prop** | Explains cost savings, DIY empowerment, removes uncertainty |
| **Call-to-Action** | "Sharing purely as a resource" / "No pressure at all" / "In case it's helpful" |
| **Closing** | "Feel free to reach out" / "Happy to chat more" / "Always happy to discuss" |

**Why this helps:**
- ✅ Different structure/wording → avoids text fingerprinting
- ✅ All variants sound natural and authentic
- ✅ Same core message = consistent brand voice

---

### 3. **Dynamic Personalization**
Every email includes:
- **Recipient's first name** (extracted from full name)
- **Publication venue** (e.g., "ACL", "arXiv")
- **Randomized selection** of subject + body variant

**Example:**
```
Recipient: Dr. Jane Smith
Venue: ACL

Email A (Variant 2):
Subject: "Quick NIW resource that might help your students/colleagues"
Body: "Hi Jane, I hope you're doing well! I recently saw your work published at ACL..."

Email B (Variant 4):
Subject: "Following up on your ACL work — NIW resource to share"
Body: "Hi Jane, I wanted to reach out because I recently came across your work from ACL..."
```

---

## 🛡️ Anti-Spam Best Practices Implemented

### ✅ What We're Doing Right

| Practice | Implementation | Why It Matters |
|----------|----------------|----------------|
| **Unique content per email** | 5 subjects × 5 bodies = 25 combinations | Avoids mass-mailing fingerprints |
| **Personal tone** | "I'm Wen, former PhD student..." | Builds trust, not salesy |
| **Soft CTA** | "No pressure", "Purely sharing" | Reduces spam reports |
| **Rate limiting** | 3-second delay between sends | Respects Gmail quotas |
| **Account rotation** | Multiple sender accounts | Distributes sending load |
| **Authentic sender** | Real name + real email | Increases deliverability |
| **Minimal links** | Only 1 link (TurboNIW website) | Avoids link-spam filters |
| **No attachments** | Plain text email only | Reduces suspicious behavior |

---

## 📊 Expected Results

### Before (Single Template):
- ❌ Same subject line → flagged as mass mail
- ❌ Same body text → text similarity = spam
- ❌ 100 identical emails → Gmail detects pattern

### After (Multi-Variant System):
- ✅ 5 different subjects → looks like individual outreach
- ✅ 5 different bodies → no text fingerprinting
- ✅ 25 unique combinations → breaks spam patterns

---

## 🚀 How to Use

### Running the Email Sender
```bash
cd TurboNIW_Email_Sender
python3 send_emails_smtp.py --csv ../data/processed_emails/high_confidence_non_chinese_75.csv --test
```

The script will:
1. **Randomly select** a subject variant for each email
2. **Randomly select** a body variant for each email
3. **Personalize** with recipient's name and publication venue
4. **Send** via SMTP with 3-second delays

---

## 📝 Future Improvements (Optional)

1. **More Variants**
   - Add 2-3 more subject lines
   - Add 2-3 more body templates
   - = 49-64 unique combinations

2. **Advanced Personalization**
   - Reference specific paper titles (if data available)
   - Mention research keywords (NLP, CV, etc.)
   - Include year of publication

3. **A/B Testing**
   - Track which variants get highest response rates
   - Optimize based on open rates (if using Gmail API tracking)

4. **Time-Based Sending**
   - Send emails at different times of day
   - Avoid sending all at once (looks more natural)

---

## ⚡ Technical Details

### File Structure
```
TurboNIW_Email_Sender/
├── email_templates_variants.py   ← Multi-variant system (NEW)
├── email_template.py              ← Legacy single template (kept for reference)
├── send_emails_smtp.py            ← Uses variants
├── send_emails_gmail_api.py       ← Uses variants
└── config.json                    ← Subject line config (now dynamic)
```

### How Variants Are Selected
```python
import random
from email_templates_variants import format_email

# Each call returns a random (subject, body) pair
subject, body = format_email(
    name="Jane Smith",
    paper_title="...",
    publication_venue="ACL"
)
```

---

## 🎯 Summary

| Metric | Before | After |
|--------|--------|-------|
| **Subject lines** | 1 | 5 |
| **Body templates** | 1 | 5 |
| **Unique combinations** | 1 | 25 |
| **Spam risk** | High | Low |
| **Personalization** | Name only | Name + venue + variant |
| **Tone** | Fixed | Conversational + authentic |

---

**Bottom Line:**
✅ This system makes your outreach look like **genuine, individual emails** rather than mass marketing.
✅ You maintain **consistent messaging** while appearing **personalized and authentic**.
✅ Lower spam risk = **higher deliverability** = more people actually see your resource!

