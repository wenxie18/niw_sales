# arXiv Organization and Collection Strategy

## How arXiv Papers are Organized

### 1. arXiv ID Format
- **Format**: `YYMM.NNNNN` (e.g., `2301.00001`)
  - `YY` = Year (last 2 digits)
  - `MM` = Month (01-12)
  - `NNNNN` = Sequential paper number (5 digits, zero-padded)
- **Example**: `2301.00001` = January 2023, paper #1
- **Note**: Unlike ACL, arXiv IDs are **not easily enumerable** - we need to use the API to discover papers

### 2. Categories (Subject Classifications)

arXiv organizes papers by **subject categories**. Each paper has:
- **Primary category** (required)
- **Secondary categories** (optional)

#### Engineering-Related Categories

**Computer Science (cs.*)**
- `cs.AI` - Artificial Intelligence
- `cs.CV` - Computer Vision and Pattern Recognition
- `cs.CL` - Computation and Language (NLP)
- `cs.LG` - Machine Learning
- `cs.NE` - Neural and Evolutionary Computing
- `cs.SY` - Systems and Control
- `cs.RO` - Robotics
- `cs.CE` - Computational Engineering, Finance, and Science

**Electrical Engineering (eess.*)**
- `eess.SP` - Signal Processing
- `eess.SY` - Systems and Control
- `eess.AS` - Audio and Speech Processing
- `eess.IV` - Image and Video Processing

**Physics (physics.*)**
- `physics.app-ph` - Applied Physics
- `physics.optics` - Optics

**Mathematics (math.*)**
- `math.OC` - Optimization and Control
- `math.NA` - Numerical Analysis

### 3. Querying by Year and Category

Unlike ACL which has sequential paper numbers, arXiv requires using their **API** to discover papers:

```python
import arxiv

# Query papers by category and year
search = arxiv.Search(
    query="cat:cs.AI AND submittedDate:[20230101 TO 20231231]",
    max_results=1000,
    sort_by=arxiv.SortCriterion.SubmittedDate
)

for result in search.results():
    arxiv_id = result.entry_id.split('/')[-1]  # Extract ID from URL
    # Then download PDF and extract info
```

### 4. Collection Strategy

**Step 1: Use arXiv API to Get Paper IDs**
- Query by category and date range
- Get list of arXiv IDs
- Example: All `cs.AI` papers from 2023

**Step 2: Download PDFs and Extract**
- For each arXiv ID, download PDF from `https://arxiv.org/pdf/{id}.pdf`
- Extract title, authors, emails using `2-arxiv_info.py`
- Similar to ACL extraction but handles variable formats

**Step 3: Organize Output**
- Save to CSV files organized by category and year
- Example: `data/arxiv/2023_cs_AI.csv`

## Comparison with ACL

| Feature | ACL | arXiv |
|---------|-----|-------|
| **Paper ID Format** | Sequential numbers (1, 2, 3...) | YYMM.NNNNN (not sequential) |
| **URL Pattern** | `{year}.acl-{track}.{num}.pdf` | `{id}.pdf` |
| **Discovery** | Enumerate numbers (1 to N) | Use API to query by category/date |
| **Organization** | By year and track | By category and year |
| **Email Rate** | ~90% | ~75% |
| **Format Consistency** | High (conference format) | Medium (varies by author) |

## Usage Example

### Single Paper
```bash
python 2-arxiv_info.py --arxiv-id 2301.00001 --output arxiv_test.csv
```

### Multiple Papers
```bash
python 2-arxiv_info.py --arxiv-ids 2301.00001 2301.00002 2301.00003 --output arxiv_test.csv
```

### Bulk Collection (Next Step)
We'll create `2.1-collect_arxiv.py` that:
1. Uses arXiv API to query by category and year
2. Gets list of paper IDs
3. Calls `2-arxiv_info.py` for each paper
4. Saves results to organized CSV files

## Next Steps

1. ✅ Create `2-arxiv_info.py` - **DONE**
2. ⏭️ Create `2.1-collect_arxiv.py` - Bulk collection script
3. ⏭️ Test on sample categories/years
4. ⏭️ Compare success rates with ACL

