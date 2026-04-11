# Methodology Documentation

## Complete Workflow for ABA PHI Sanitization

This document provides detailed technical documentation of the complete research methodology.

---

## Phase 1: Synthetic Data Generation

### Purpose
Generate realistic synthetic ABA session notes that replicate UCP documentation patterns without containing actual patient information.

### Input Requirements
- Identifier files (names, addresses, IDs, etc.)
- UCP document templates
- Clinical scenario specifications

### Process

**Step 1: Load Identifier Files**
```python
# 9 identifier files loaded:
- first_names.txt (56 names)
- last_names.txt (98 surnames)  
- addresses.csv (49 addresses)
- medicaid_ids.txt (200 IDs)
- middle_initials.txt (18 letters)
- parent_first_names.txt (80 names)
- phone_numbers.txt (100 numbers)
- credentials.txt (20 credentials)
- provider_last_names.txt (106 surnames)
```

**Step 2: Generate Client Profiles**
```python
# For each note:
- Select random name (with format variation)
- Generate DOB (age 3-18)
- Assign Medicaid ID
- Select programs (residential + day)
- Add parent names (40% dual-parent)
- Add phone number(s)
- Add home address (30% frequency)
```

**Step 3: Generate Session Notes**
```python
# 12 scenario types with weighted distribution:
- Exceptional Progress (10%)
- Skill Acquisition (15%)
- Positive Social (10%)
- Standard Session (20%)
- Maintenance (10%)
- Mild Challenging (10%)
- Moderate Challenging (10%)
- Environmental Triggers (5%)
- Medical Appointment (5%)
- Medication Monitoring (5%)
- Crisis Intervention (3%)
- Post-Crisis Recovery (2%)
```

**Step 4: Insert PHI with Pattern Variation**
```python
# Name formats (4 variations):
- "Emma Rodriguez"
- "Rodriguez, Emma"
- "Rodriguez, Emma M."
- "Emma M. Rodriguez"

# Date formats (5 variations):
- "3/15/2025"
- "03/15/2025"
- "3/15/25"
- "March 15, 2025"
- "March 15 2025"
```

### Output
- 1,245 synthetic .txt files saved to `data/synthetic/raw/`
- Avg 17.9 PHI instances per note
- Total ~22,000 PHI instances across corpus

### Runtime
- ~10 minutes for 1,245 notes
- ~0.5 seconds per note

---

## Phase 2: Ground Truth Annotation

### Purpose
Extract all PHI entities from synthetic notes to create perfect ground truth for evaluation.

### Process

**Step 1: Define PHI Patterns**
```python
# Regex patterns for structured PHI:
- MEDICAID_ID: r'\b[A-Z]{2}\d{6}\b'
- PHONE: r'\b315-\d{3}-\d{4}\b'
- DATE: 5 format patterns
- ADDRESS: Full address pattern
- CREDENTIAL: 10+ professional titles
```

**Step 2: Extract Person Names**
```python
# Person name detection with filtering:
- Pattern: Capitalized First + Last
- Blacklist: 50+ non-person phrases
  * "Service Location", "Crisis Intervention"
  * "Physical Aggression", "Session Summary"
- Validation: 2-3 words, alphabetic, reasonable length
```

**Step 3: Remove Duplicates**
```python
# Deduplication logic:
- Same text at same position → remove
- Sort by start position
- Preserve entity type information
```

### Output
- `annotations_1000_fixed.json` (~8MB)
- 22,582 total PHI annotations
- Entity type distribution:
  * PERSON: 59.3%
  * DATE: 24.4%
  * PHONE: 6.9%
  * CREDENTIAL: 4.9%
  * ADDRESS: 2.1%
  * MEDICAID_ID: 2.4%

### Runtime
- ~2-3 minutes for 1,245 notes

---

## Phase 3: PHI Detection

### Purpose
Automatically detect PHI using hybrid spaCy NER + regex approach.

### Architecture

**Component 1: spaCy NER**
```python
# Model: en_core_web_sm
# Entities detected: PERSON
# Method: Contextual word embeddings
# Limitations: 
  - Over-detects (section headers, clinical terms)
  - General model (not ABA-specific)
```

**Component 2: Regex Patterns**
```python
# Exact match patterns for:
- MEDICAID_ID (100% precision)
- ADDRESS (100% precision)
- DATE (99.98% precision)
- PHONE (96.88% precision)
- CREDENTIAL (62.94% precision - needs expansion)
```

**Component 3: Overlap Removal**
```python
# Logic:
- Sort entities by start position (descending)
- Keep longer spans when overlapping
- Prevent duplicate annotations
```

### Process

```bash
# Command:
python scripts/run_phi_detection.py

# Flow:
1. Load 1,245 synthetic notes
2. For each note:
   a. Apply spaCy NER
   b. Apply regex patterns
   c. Remove overlaps
   d. Store detected entities
3. Save to detected_entities.json
```

### Output
- `detected_entities.json` (~7MB)
- 22,696 detected entities
- Entity type distribution

### Performance
- Precision: 68.32%
- Recall: 68.67%
- F1-Score: 68.49%

### Error Analysis

**High Performance (>95% recall):**
- MEDICAID_ID: 100% (regex perfect match)
- ADDRESS: 100% (regex perfect match)
- DATE: 99.98% (1 missed format variant)

**Moderate Performance (85-95% recall):**
- PHONE: 96.88% (48 missed numbers)

**Low Performance (<75% recall):**
- CREDENTIAL: 62.94% (401 missed - pattern gaps)
- PERSON: 106.40% (847 false positives - over-detection)

### Runtime
- ~5-10 minutes for 1,245 notes
- spaCy NER is the bottleneck

---

## Phase 4: Sanitization

### Purpose
Apply de-identification strategies to remove/replace detected PHI.

### Methods

**Method 1: REPLACE**
```python
# Logic: Replace with entity type label
# Example:
  "Emma Rodriguez" → "[PERSON]"
  "3/15/2025" → "[DATE]"
  "KV510348" → "[MEDICAID_ID]"

# Properties:
  - Maximizes privacy
  - Maintains document structure
  - Easy to understand
```

**Method 2: MASK**
```python
# Logic: Partial character masking
# Example:
  "Emma" → "E**a"
  "Rodriguez" → "R*******z"
  "3/15/2025" → "3/**/****"

# Properties:
  - Preserves character count
  - Retains some readability
  - Potential re-identification risk
```

**Method 3: HASH**
```python
# Logic: SHA-256 deterministic hashing
# Example:
  "Emma Rodriguez" → "a3f5e8b2"
  "3/15/2025" → "7c9d2f1a"

# Properties:
  - Same PHI → same hash (linkage)
  - No readable information
  - Cannot reverse
```

**Method 4: HYBRID**
```python
# Logic: Context-aware combination
# Example:
  PERSON → "[PERSON]" (replace)
  DATE → "3/**/****" (mask)
  MEDICAID_ID → "a3f5e8b2" (hash)
  CREDENTIAL → "BCBA" (preserve)

# Properties:
  - Balances privacy + utility
  - Preserves clinical context
  - Selective protection
```

### Evaluation Metrics

**Privacy: PHI Removal Rate**
```python
# Calculation:
removed_count = 0
for entity in detected_entities:
    if entity.text not in sanitized_text:
        removed_count += 1
removal_rate = removed_count / total_entities
```

**Utility: Semantic Similarity**
```python
# Method: SentenceTransformer cosine similarity
model = SentenceTransformer('all-MiniLM-L6-v2')
emb_original = model.encode(original_text)
emb_sanitized = model.encode(sanitized_text)
similarity = cosine_similarity(emb_original, emb_sanitized)
```

### Process

```bash
# Command:
python scripts/run_sanitization_complete.py

# Flow:
1. Load 1,245 notes + detected entities
2. For each method (replace, mask, hash, hybrid):
   a. Apply sanitization to all notes
   b. Calculate PHI removal rate
   c. Calculate similarity score
   d. Save sanitized notes
3. Generate comparison summary
```

### Output

**File Structure:**
```
outputs/sanitized/
├── replace/
│   ├── replace_sanitized.json
│   └── notes/ (1,245 .txt files)
├── mask/
│   ├── mask_sanitized.json
│   └── notes/
├── hash/
│   ├── hash_sanitized.json
│   └── notes/
├── hybrid/
│   ├── hybrid_sanitized.json
│   └── notes/
└── sanitization_summary.json
```

### Performance

| Method | PHI Removal | Similarity |
|--------|-------------|------------|
| REPLACE | 88.79% | 93.32% |
| MASK | 88.79% | 86.10% |
| HASH | 88.79% | 90.78% |
| HYBRID | 85.97% | 93.00% |

### Runtime
- ~10-15 minutes for all 4 methods
- SentenceTransformer similarity calculation is the bottleneck

---

## Phase 5: Evaluation

### Purpose
Compare detected PHI vs. ground truth to measure detection accuracy.

### Metrics

**Strict Matching**
```python
# Logic: Exact start, end, and type must match
# Example:
  Ground Truth: {text: "Emma Rodriguez", type: "PERSON", start: 54, end: 68}
  Detected:     {text: "Emma Rodriguez", type: "PERSON", start: 54, end: 68}
  Result: TRUE POSITIVE
```

**Relaxed Matching**
```python
# Logic: Overlapping spans + same type
# Example:
  Ground Truth: {text: "Emma Rodriguez", start: 54, end: 68}
  Detected:     {text: "Emma", start: 54, end: 58}
  Result: TRUE POSITIVE (partial overlap counts)
```

**Confusion Matrix**
```python
# Calculation:
TP = matched entities
FP = detected but not in ground truth
FN = in ground truth but not detected

precision = TP / (TP + FP)
recall = TP / (TP + FN)
f1 = 2 * (precision * recall) / (precision + recall)
```

### Process

```bash
# Command:
python scripts/run_evaluation_fixed.py

# Flow:
1. Load detected_entities.json
2. Load annotations_1000_fixed.json
3. For each document:
   a. Match detected vs. ground truth entities
   b. Count TP, FP, FN
4. Calculate aggregate metrics
5. Save results
```

### Output

**Strict Matching:**
- Precision: 64.18%
- Recall: 64.51%
- F1: 64.34%

**Relaxed Matching:**
- Precision: 68.32%
- Recall: 68.67%
- F1: 68.49%

**Performance by Entity Type:**
(See main results)

### Runtime
- ~10 seconds

---

## Complete Pipeline Runtime

| Phase | Script | Time |
|-------|--------|------|
| 1. Generation | generate_synthetic_notes.py | ~10 min |
| 2. Annotation | generate_ground_truth_fixed.py | ~3 min |
| 3. Detection | run_phi_detection.py | ~10 min |
| 4. Sanitization | run_sanitization_complete.py | ~15 min |
| 5. Evaluation | run_evaluation_fixed.py | ~10 sec |
| **Total** | | **~40 min** |

---

## Technical Requirements

**Hardware:**
- CPU: Modern multi-core processor
- RAM: 8GB+ recommended
- Disk: 2GB for models + generated data

**Software:**
- Python 3.8+
- spaCy 3.7+
- PyTorch 2.0+
- SentenceTransformers 2.5+

**Models:**
- spaCy: en_core_web_sm (~40MB)
- SentenceTransformers: all-MiniLM-L6-v2 (~80MB)

---

## Known Limitations

1. **Detection Recall (68.67%):**
   - CREDENTIAL under-detection (401 missed)
   - PERSON over-detection (847 false positives)
   - Solution: Expand regex patterns, improve filtering

2. **Synthetic Data Only:**
   - Not validated on real UCP notes yet
   - May not capture all real-world variability
   - Solution: Validate with 10-20 real notes

3. **Computational Requirements:**
   - spaCy NER requires significant RAM
   - SentenceTransformers requires GPU for faster processing
   - Solution: Use CPU with patience or cloud resources

---

## Future Improvements

1. **Detection Enhancement:**
   - Expand CREDENTIAL regex patterns
   - Implement PERSON name blacklist filtering
   - Fine-tune spaCy on ABA-specific corpus

2. **Evaluation Expansion:**
   - Real-world UCP data validation
   - Cross-institutional generalization testing
   - Statistical significance testing

3. **Sanitization Refinement:**
   - Adaptive HYBRID rules based on use case
   - Differential privacy guarantees
   - Utility preservation optimization

---

**Last Updated:** April 11, 2026  
**Version:** 1.0
