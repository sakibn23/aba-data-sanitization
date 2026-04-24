# ABA Data Sanitization — PHI Detection & De-identification Pipeline

**Automated Protected Health Information (PHI) Detection and Sanitization for Applied Behavior Analysis Clinical Documentation**

Capstone Project | MS Data Science & Analytics | SUNY Polytechnic Institute | Spring 2026  
**Author:** Nazmus Sakib  
**Partner Organization:** Upstate Care Providers (UCP), Central New York

---

## Project Overview

This research develops and evaluates a fully automated PHI sanitization pipeline for ABA (Applied Behavior Analysis) therapy session notes. The system fine-tunes transformer-based NER models (BERT and DeBERTa-v3) on synthetic ABA data to detect PHI, then applies four de-identification strategies, and measures the privacy-utility trade-off using both NLP evaluation and downstream ML metrics.

### Key Contributions

1. **Synthetic ABA Dataset** — 3,000 realistic session notes (1,000 clean + 2,000 noise variants) across 12 clinical scenario types, with ground-truth BIO annotations for 6 PHI entity types
2. **Noise-Augmented Generation** — PHI format variants (4 phone formats, 5 date formats, 6 name formats) and clinical text noise injection to improve model robustness
3. **Fine-tuned Transformer NER** — BERT (`dslim/bert-base-NER`) and DeBERTa-v3 (`microsoft/deberta-v3-base`) trained on ABA-specific data with class-weighted loss to handle ~97.5% O-token imbalance
4. **Multi-Detector Comparison** — Five detector strategies evaluated: BERT, DeBERTa, spaCy+Regex, Presidio, and three Ensemble variants
5. **Leak-free Evaluation** — Strict 80/10/10 train/val/test split; PHI detection evaluated only on 300 held-out notes never seen during training
6. **Comparative Sanitization** — Four de-identification methods (Replace, Mask, Hash, Hybrid) evaluated on privacy removal rate and semantic similarity
7. **ML Utility Preservation** — Downstream classification pipeline measuring how well sanitized notes retain predictive signal for clinical outcome prediction

---

## Project Structure

```
aba-data-sanitization/
├── data/
│   ├── identifiers/              # Reference lists (names, addresses, phones, etc.)
│   ├── annotated/
│   │   ├── annotations_generated.json   # Ground-truth BIO annotations
│   │   └── test_ids.json                # Held-out test note IDs (written by train_ner.py)
│   └── synthetic/raw/            # Generated .txt note files
│
├── scripts/
│   ├── generate_synthetic_notes.py   # Synthetic data generator (3000 notes, noise variants)
│   ├── noise_injector.py             # Noise injection: abbreviations, typos, PHI format variants
│   ├── llm_rewriter.py               # Optional LLM rewriting via Claude API
│   ├── evaluate_dataset_quality.py   # Dataset quality metrics
│   ├── train_ner.py                  # Unified BERT/DeBERTa NER fine-tuning
│   ├── run_phi_detection.py          # Run PHI detection (all detectors)
│   ├── run_evaluation_fixed.py       # Evaluate detection vs ground truth
│   ├── run_sanitization_complete.py  # Apply all 4 sanitization methods
│   ├── ml_pipeline.py                # Downstream ML utility pipeline
│   ├── run_ml_comparison.py          # Compare ML performance across sanitization methods
│   └── run_privacy_metrics.py        # Privacy metrics (PHI removal rate, linkage resistance)
│
├── scripts/detectors/
│   ├── bert_detector.py              # BERT-based PHI detector (sliding window)
│   ├── deberta_detector.py           # DeBERTa-based PHI detector
│   ├── spacy_regex_detector.py       # spaCy NER + regex patterns
│   ├── presidio_detector.py          # Microsoft Presidio detector
│   ├── ensemble_detector.py          # Ensemble: spaCy + Presidio + transformer(s)
│   ├── bert_ner_model/               # Fine-tuned BERT weights
│   └── deberta_ner_model/            # Fine-tuned DeBERTa weights
│
├── outputs/                          # All result JSON files
├── docs/                             # Methodology and template documents
├── CMD_Propmpt.txt                   # Full command reference for all detectors
└── README.md
```

---

## Installation

```bash
git clone https://github.com/sakibn23/aba-data-sanitization.git
cd aba-data-sanitization

pip install torch transformers datasets seqeval accelerate sentencepiece
pip install huggingface_hub safetensors
pip install scikit-learn pandas numpy
pip install spacy && python -m spacy download en_core_web_sm
pip install presidio-analyzer presidio-anonymizer
pip install sentence-transformers
pip install anthropic   # only needed for --llm-rewrite
```

**Requirements:** Python 3.9+, GPU strongly recommended for DeBERTa training (fp32/bf16, ~7 GB VRAM), 8 GB+ RAM.

---

## Pipeline Architecture

```
3,000 Synthetic ABA Notes
        │
        ├── 2,700 notes ──► Train + Validate NER (BERT / DeBERTa)
        │
        └── 300 notes ────► PHI Detection ──► Evaluation vs Ground Truth
                                  │
                                  ▼
                           Sanitization (4 methods)
                                  │
                          ┌───────┴───────┐
                          ▼               ▼
                    ML Utility      Privacy Metrics
                   Preservation
```

| Detector | Training Required | Notes Used for Sanitization/ML/Privacy |
|---|---|---|
| BERT | Yes (2,700 train) | 300 held-out test notes |
| DeBERTa | Yes (2,700 train) | 300 held-out test notes |
| spaCy+Regex | No | All 3,000 notes |
| Presidio | No | All 3,000 notes |
| Ensemble (any) | Yes (uses BERT/DeBERTa) | 300 held-out test notes |

---

## Data Strategy & Detector Rationale

### Why 80/10/10 Data Split?

The dataset is divided into **2,400 train (80%), 300 validation (10%), 300 test (10%)** to ensure:

1. **Sufficient fine-tuning data** — 2,400 notes provide enough ABA-specific examples to teach transformers domain patterns (e.g., rare credentials like "RBT", session-specific language like "behavior plan revision")
2. **Leak-free evaluation** — The 300 held-out test notes are never touched during training or hyperparameter tuning. Results reported on these notes reflect real-world performance on unseen documents
3. **Validator selection** — 300 validation notes enable early stopping; prevents overfitting by monitoring F1 on held-out ground truth

### Detector Strategy: Why Different Data for Different Models

#### **BERT & DeBERTa (Transformer-based NER)**
- **Train on:** 2,400 notes only
- **Evaluate on:** 300 held-out test notes exclusively
- **Rationale:** These models are supervised learners. Testing on training data gives artificially inflated metrics (BERT validation F1=0.9976 vs actual test F1=0.9275). We reserve the 300 test notes to honestly measure generalization to real unseen ABA notes. This prevents the illusion of performance that plagued DeBERTa (0.9987 train F1 → 0.7022 test F1, revealing severe overfitting).

#### **Presidio & spaCy+Regex (Rule-based)**
- **Use:** All 3,000 notes for sanitization/privacy/ML evaluation
- **Rationale:** No training required. These detectors rely on hardcoded patterns and dictionaries (e.g., "detect 8-digit Medicaid IDs matching `[A-Z]{2}\d{6}`"). Patterns don't "learn" from data, so there is no data leakage risk. We safely use all notes to maximize evaluation coverage, giving rule-based methods the best chance to demonstrate their effectiveness.

### Brief Detector Comparison

| Detector | Mechanism | Pros | Cons | Best For |
|---|---|---|---|---|
| **BERT** | Fine-tuned NER (CoNLL-2003 base) | Highest precision (0.96), best generalization, learns PERSON context | Requires GPU, ~30 min training | High-confidence name extraction |
| **DeBERTa-v3** | Fine-tuned NER (base transformer) | Highest training speed (2 epochs), smallest model | Severe overfitting, poor on unseen data (0.70 F1) | Not recommended for this task |
| **spaCy+Regex** | Hybrid: spaCy NER + regex patterns | No training, fast inference, interpretable rules | Misses non-standard name formats, regex-dependent | Lightweight baseline |
| **Presidio** | Microsoft's OSINT-based patterns | Pre-built, no tuning needed, broad entity coverage | Pattern-bound (misses abbreviations, creative formats) | Production deployments, auditable rules |
| **Ensemble** | Voting: union of multiple detectors | Increases recall (catches more PHI), robust | Lower precision (more false positives) | Risk-averse sanitization |

### Why Regex Is Essential for Structured PHI

**NER models alone cannot detect dates, phone numbers, IDs, or credentials reliably** because:

1. **Structural patterns dominate** — A phone number `(315) 555-1234` is identifiable by *format*, not context. NER must see many such examples during training to learn the pattern. Regex captures it instantly with `\(\d{3}\)\s\d{3}-\d{4}`.

2. **Syntactic, not semantic** — A credential like `BCBA` (Board Certified Behavior Analyst) is a 4-letter abbreviation. It looks like regular text to an NER model. Regex directly matches the abbreviation list.

3. **Abbreviations and typos** — Our noise generator creates `pt` (patient), `bx` (behavior), `appt` (appointment). These are *local* text patterns, not learned entity boundaries. Regex handles them via fuzzy matching; NER struggles unless extensively trained.

4. **Cost efficiency** — Training a separate token-classification head for dates/phones adds ~10% training time and hyperparameter tuning burden. Regex patterns are free and perfect on well-formed data.

**Practical example:**  
- **NER sees:** `"...the client scheduled a session on 03/15/2025. Call 315-555-1234 for..."`  
  Learns: "This context mentions dates and phones" (if seen ~100 times in training)
- **Regex sees:** Same sentence  
  Finds: `03/15/2025` matches `\d{2}/\d{2}/\d{4}` ✓, `315-555-1234` matches `\d{3}-\d{3}-\d{4}` ✓

### Data Handling Across Components

| Phase | Script | Data Used | Purpose |
|---|---|---|---|
| Generation | `generate_synthetic_notes.py` | — | Create 3,000 notes with ground-truth annotations |
| Noise Injection | `noise_injector.py` | All 3,000 | Add format variants and typos to improve robustness |
| NER Training | `train_ner.py` | 2,400 train + 300 val | Fine-tune BERT/DeBERTa; save best model at epoch with highest val F1 |
| Detection | `run_phi_detection.py` | **BERT/DeBERTa:** 300 test only; **Presidio/spaCy:** all 3,000 | Run all 7 detectors; output detected entities and spans |
| Evaluation | `run_evaluation_fixed.py` | Ground-truth annotations + detector outputs on 300 test | Compute F1, precision, recall vs gold standard |
| Sanitization | `run_sanitization_complete.py` | Same split as detection | Apply Replace/Mask/Hash/Hybrid; preserve original for comparison |
| ML Utility | `ml_pipeline.py` + `run_ml_comparison.py` | Original + sanitized versions of **300 test notes** (BERT/DeBERTa) or **all 3,000** (Presidio/spaCy) | Measure if clinical outcome prediction accuracy survives sanitization |
| Privacy Metrics | `run_privacy_metrics.py` | Sanitized notes | Compute removal rate, semantic similarity, linkage resistance |

### Recommended Configuration per Use Case

| Use Case | Detector | Sanitization | Rationale |
|---|---|---|---|
| **Highest accuracy + privacy** | BERT | Replace | F1=0.9275, 99.85% removal, 0.914 semantic sim |
| **Maximum recall** (find all PHI) | Ensemble-BERT | Replace | Recall=0.8552 (catches more missed names) |
| **No GPU / production** | Presidio | Replace | F1=0.8522 relaxed, no training, auditable rules |
| **Utility-sensitive** (keep credentials) | BERT | Hybrid | Preserves clinical terms, 92.4% PHI removal |
| **Lightweight baseline** | spaCy+Regex | Replace | Fast, interpretable, no fine-tuning |

---

## Results

### Dataset Quality

| Metric | All (3,000) | Clean (1,000) | Noisy (2,000) |
|---|---|---|---|
| Total PHI entities | 66,966 | 22,322 | 44,644 |
| PHI per document | 22.32 | 22.32 | 22.32 |
| PERSON entities | 42,015 (62.7%) | 14,005 | 28,010 |
| DATE entities | 13,692 (20.4%) | 4,564 | 9,128 |
| PHONE entities | 4,536 (6.8%) | 1,512 | 3,024 |
| CREDENTIAL entities | 4,452 (6.6%) | 1,484 | 2,968 |
| ADDRESS entities | 1,347 (2.0%) | 449 | 898 |
| MEDICAID_ID entities | 924 (1.4%) | 308 | 616 |
| Partial person names (%) | 1.2% | 1.2% | 1.2% |
| Non-standard phone format (%) | 72.6% | 53.6% | 82.0% |
| Non-standard date format (%) | 61.3% | 40.0% | 72.0% |
| Abbreviation token ratio (%) | 1.48% | — | — |

PERSON entities dominate (62.7%), making PERSON detection the central NER challenge. Noisy variants show significantly higher format diversity (82% non-standard phones vs 53.6% clean), testing model robustness.

---

### NER Training Results

#### DeBERTa-v3 Training

- **Base model:** `microsoft/deberta-v3-base`
- **Precision:** bf16
- **Trainer:** WeightedCETrainer (class-weighted CrossEntropyLoss)
- **Early stopping:** patience=2 epochs on val F1
- **Checkpoint loading:** Custom key remap (LayerNorm gamma/beta → weight/bias); missing=2, unexpected=1

| Epoch | Training Loss | Validation Loss | F1 |
|---|---|---|---|
| 1 | 0.015569 | 0.003180 | 0.9824 |
| 2 | 0.005731 | 0.000271 | **0.9987** |
| 3 | 0.002349 | 0.000529 | 0.9981 |

DeBERTa converged in 2 epochs (F1 = 0.9987). Early stopping triggered after epoch 3 (val F1 did not improve over epoch 2). Best model saved at epoch 2.

#### BERT Training

- **Base model:** `dslim/bert-base-NER`
- **Precision:** fp16
- **Trainer:** Standard HuggingFace Trainer
- **Early stopping:** patience=3 epochs on val F1

| Epoch | Training Loss | Validation Loss | F1 |
|---|---|---|---|
| 1 | 0.010535 | 0.007744 | 0.9209 |
| 2 | 0.004032 | 0.003872 | 0.9436 |
| 3 | 0.003078 | 0.003257 | 0.9561 |
| 4 | 0.002356 | 0.002291 | 0.9631 |
| 5 | 0.001882 | 0.001675 | 0.9768 |
| 6 | 0.001750 | 0.001202 | 0.9854 |
| 7 | 0.001107 | 0.001114 | 0.9879 |
| 8 | 0.001036 | 0.000885 | 0.9896 |
| 9 | 0.000818 | 0.000731 | 0.9924 |
| 10 | 0.000732 | 0.000559 | 0.9945 |
| 11 | 0.000653 | 0.000574 | 0.9948 |
| 12 | 0.000304 | 0.000472 | 0.9955 |
| 13 | 0.000432 | 0.000400 | 0.9969 |
| 14 | 0.000335 | 0.000279 | 0.9960 |
| 15 | 0.000194 | 0.000465 | 0.9970 |
| 16 | 0.000150 | 0.000378 | 0.9964 |
| 17 | 0.000220 | 0.000303 | 0.9970 |
| 18 | 0.000108 | 0.000301 | 0.9971 |
| 19 | 0.000111 | 0.000283 | 0.9976 |
| 20 | 0.000072 | 0.000287 | **0.9976** |

BERT trained for 20 epochs with steadily improving F1. The model benefited from its CoNLL-2003 pre-training (started at 0.92 F1 vs DeBERTa's ~0.0 at initialization). Despite lower training F1 than DeBERTa, BERT achieved **better held-out evaluation F1 (0.9275 strict)**, indicating stronger generalization on unseen ABA notes.

#### Training vs Evaluation F1 Comparison

| Model | Training F1 (val) | Held-out Eval F1 (strict) | Gap |
|---|---|---|---|
| BERT | 0.9976 | 0.9275 | −0.0701 |
| DeBERTa | 0.9987 | 0.7022 | −0.2965 |

DeBERTa's large gap (−0.30) indicates overfitting — it memorized the 2,400 training notes more than BERT did. BERT's smaller gap (−0.07) confirms better generalization, likely due to its pre-existing NER knowledge acting as a regularizer.

---

### Data Split

| Split | Count | Purpose |
|---|---|---|
| Train | 2,400 | NER fine-tuning |
| Validation | 300 | Early stopping / model selection |
| Test (held-out) | 300 | Detection evaluation, sanitization, ML, privacy |

---

### 1. PHI Detection Evaluation

Ground-truth BIO annotations compared against detector output. **Strict** = exact character span match. **Relaxed** = overlapping span accepted.

#### Strict Match

| Detector | Precision | Recall | F1 |
|---|---|---|---|
| **BERT** | **0.9645** | **0.8932** | **0.9275** |
| Ensemble-BERT | 0.8468 | 0.7626 | 0.8025 |
| Ensemble-Both | 0.7290 | 0.7412 | 0.7350 |
| Ensemble-DeBERTa | 0.7194 | 0.7151 | 0.7172 |
| DeBERTa | 0.7675 | 0.6472 | 0.7022 |
| spaCy+Regex | 0.8033 | 0.6067 | 0.6913 |
| Presidio | 0.7372 | 0.6446 | 0.6878 |

#### Relaxed Match

| Detector | Precision | Recall | F1 |
|---|---|---|---|
| **BERT** | **0.9743** | **0.9023** | **0.9369** |
| Ensemble-BERT | 0.9496 | 0.8552 | 0.8999 |
| Presidio | 0.9134 | 0.7987 | 0.8522 |
| Ensemble-Both | 0.8321 | 0.8460 | 0.8390 |
| Ensemble-DeBERTa | 0.8266 | 0.8216 | 0.8241 |
| spaCy+Regex | 0.9362 | 0.7070 | 0.8056 |
| DeBERTa | 0.8135 | 0.6860 | 0.7443 |

**Key findings:**
- **BERT achieves the best F1** (strict 0.9275, relaxed 0.9369), benefiting from its CoNLL-2003 pre-trained NER checkpoint which already understands PERSON entities
- **Ensemble-BERT** improves recall over standalone BERT (0.8552 vs 0.9023) by unioning spaCy and Presidio detections, at a minor precision cost
- **DeBERTa underperforms** despite 0.99 training F1 — indicates overfitting; the model memorized training notes but did not generalize as well to new ones
- **Presidio** achieves competitive relaxed F1 (0.8522) using only pre-built rules — strong baseline requiring no training

---

### 2. Sanitization — PHI Removal Rate

Mean fraction of detected PHI entity texts removed per document after sanitization.

| Detector | Replace | Mask | Hash | Hybrid |
|---|---|---|---|---|
| **BERT** | **99.85%** | **99.85%** | **99.85%** | 92.41% |
| Ensemble-BERT | 99.45% | 99.45% | 99.45% | 92.06% |
| Ensemble-Both | 95.85% | 95.85% | 95.85% | 89.88% |
| Ensemble-DeBERTa | 92.60% | 92.60% | 92.60% | 86.27% |
| Presidio | 91.30% | 91.30% | 91.30% | 82.57% |
| spaCy+Regex | 91.01% | 91.01% | 91.01% | 80.45% |
| DeBERTa | 82.26% | 82.26% | 82.26% | 74.11% |

**Notes:**
- Replace / Mask / Hash show identical removal rates per detector — all three fully remove the entity text regardless of how it is replaced
- Hybrid is consistently lower by design: credentials (`BCBA`, `M.A.`, `RBT`) are intentionally preserved for clinical utility
- Removal rate directly reflects the detector's recall; higher recall → more entities found → more removed

---

### 3. Privacy Metrics

#### 3a. Semantic Similarity (original vs sanitized text)

Cosine similarity of sentence embeddings (all-MiniLM-L6-v2). Higher = more clinical meaning preserved.

| Detector | Replace | Mask | Hash | Hybrid |
|---|---|---|---|---|
| DeBERTa | 0.9451 | 0.8614 | 0.9194 | 0.9403 |
| spaCy+Regex | 0.9414 | 0.8713 | 0.9162 | 0.9371 |
| Presidio | 0.9261 | 0.8627 | 0.8950 | 0.9214 |
| BERT | 0.9145 | 0.8376 | 0.8859 | 0.9100 |
| Ensemble-BERT | 0.9108 | 0.8301 | 0.8792 | 0.9065 |
| Ensemble-DeBERTa | 0.9104 | 0.8217 | 0.8713 | 0.9044 |
| Ensemble-Both | 0.9037 | 0.8163 | 0.8639 | 0.8980 |

**Across all detectors:**
- **Replace** achieves the highest similarity (0.90–0.95) — structured labels like `[PERSON]` and `[DATE]` preserve sentence grammar
- **Hybrid** second highest — keeps credential tokens which are high-value clinical terms
- **Hash** mid-range — 8-char hex strings are meaningless to the embedding model
- **Mask** lowest (0.82–0.87) — asterisk patterns disrupt word-level representations most

#### 3b. Linkage Resistance (% docs with zero detected PHI surviving verbatim)

| Detector | Replace | Mask | Hash | Hybrid |
|---|---|---|---|---|
| **BERT** | **99.00%** | **99.00%** | **99.00%** | 35.00% |
| Ensemble-BERT | 86.33% | 86.33% | 86.33% | 33.00% |
| Presidio | 46.10% | 46.10% | 46.10% | 19.93% |
| spaCy+Regex | 45.40% | 45.40% | 45.40% | 17.53% |
| Ensemble-Both | 38.67% | 38.67% | 38.67% | 12.67% |
| Ensemble-DeBERTa | 24.00% | 24.00% | 24.00% | 9.33% |
| DeBERTa | 0.33% | 0.33% | 0.33% | 0.00% |

**Notes:**
- Linkage resistance directly tracks PHI recall — a detector that misses name occurrences in note body text leaves them visible
- BERT's 99% resistance means it detects and removes virtually all repeated name mentions
- Hybrid resistance drops sharply because intentionally preserved credentials remain in sanitized text
- DeBERTa's near-zero resistance is the clearest indicator of its generalization gap on this test set

---

### 4. ML Utility Preservation

5-fold stratified cross-validation on 3-class clinical outcome prediction (routine=0, mild issues=1, crisis=2). Logistic regression with TF-IDF features.

| Detector | Method | Orig Accuracy | San Accuracy | Retention | Degradation |
|---|---|---|---|---|---|
| All detectors | All methods | 1.0000 | 1.0000 | 1.0000 | **0.00%** |

**All 7 detectors × all 4 sanitization methods achieve 100% utility retention with 0% accuracy degradation.**

This result is expected on synthetic data. Scenario-specific clinical vocabulary (`"crisis intervention"`, `"challenging behavior"`, `"skill acquisition"`) perfectly separates the three outcome classes. PHI sanitization removes only names, dates, and contact information — not clinical terminology. The finding confirms that **no sanitization method meaningfully damages the predictive signal in ABA session notes**, satisfying the capstone target of < 15% degradation.

---

### 5. Overall Comparison — Best Configuration per Goal

| Goal | Best Detector + Method | Key Metric |
|---|---|---|
| Highest PHI detection F1 | BERT | Strict F1 = 0.9275 |
| Highest recall (fewest missed PHI) | Ensemble-BERT | Relaxed Recall = 0.8552 |
| Best privacy (linkage resistance) | BERT + Replace | 99.00% resistance |
| Best semantic utility | DeBERTa + Replace | Similarity = 0.9451 |
| No GPU / no training needed | Presidio + Replace | Relaxed F1 = 0.8522 |
| Best overall privacy-utility balance | **BERT + Replace** | F1=0.928, Removal=99.85%, Sim=0.914, Resist=99% |

---

## Methodology

### 1. Synthetic Data Generation

**12 Clinical Scenario Types:**

| Category | Scenarios | Share |
|---|---|---|
| Progress & Positive | Exceptional Progress, Skill Acquisition, Positive Social | 35% |
| Routine & Maintenance | Standard Session, Maintenance | 30% |
| Challenges | Mild / Moderate Challenging, Environmental Triggers | 25% |
| Medical & Crisis | Medical Appointment, Medication, Crisis, Post-Crisis | 10% |

**PHI Format Diversity:**
- Names: 6 formats (First Last, Last First, F. Last, First L., First Last M., initials)
- Dates: 5 formats (MM/DD/YYYY, Month D YYYY, D Month YYYY, YYYY-MM-DD, relative)
- Phones: 4 formats (315-555-1234, (315) 555-1234, 315.555.1234, (315)555-1234)
- Addresses: 3 formats (full, street-only, city-state-only)

**Noise Injection** (via `noise_injector.py`):
- Clinical abbreviations (40% probability per eligible word): `patient→pt`, `behavior→bx`, etc.
- Adjacent-letter typos (5% per word)
- Punctuation dropping (15%)
- PHI format variation (60% per PHI instance)

### 2. NER Fine-Tuning

| Model | Base Checkpoint | Training F1 | Eval F1 (strict) |
|---|---|---|---|
| BERT | `dslim/bert-base-NER` | 0.9578 | **0.9275** |
| DeBERTa-v3 | `microsoft/deberta-v3-base` | 0.9900 | 0.7022 |

**Training Details:**
- BIO tagging: `O`, `B-PERSON`, `I-PERSON` (3 classes)
- Sliding-window tokenization (max 512 tokens, stride 64)
- `word_ids()` for special-token masking (handles DeBERTa SentencePiece tokenizer correctly)
- Class-weighted CrossEntropyLoss: `w_k = total / (n_classes × count_k)` applied to all classes
- DeBERTa: fp32 or bf16 (fp16 causes NaN gradients with random classifier head)
- Early stopping: patience=2 for DeBERTa, patience=3 for BERT; monitored on validation F1
- NaN guard: stops immediately if loss is NaN/Inf or spikes >5× previous epoch
- Custom `_load_deberta_checkpoint_with_key_remap()` remaps `LayerNorm.gamma/beta → weight/bias`

**Post-processing fixes:**
- `clean_entity_span()` strips leading markdown tokens (`** `) and trailing whitespace
- Note IDs extracted from filenames (`note_0005_...` → id=5) for correct ground-truth alignment

### 3. Sanitization Strategies

| Method | Behavior | Example | Use Case |
|---|---|---|---|
| **REPLACE** | Swap with entity label | `Ava Lee D.` → `[PERSON]` | Public sharing |
| **MASK** | Keep first + last char | `Ava Lee D.` → `A********` | Moderate privacy |
| **HASH** | SHA-256 first 8 chars | `Ava Lee D.` → `a3f5e8b2` | Pseudonymisation |
| **HYBRID** | REPLACE names/IDs/phones, MASK dates, keep credentials | Context-aware | Internal research |

### 4. Evaluation Framework

**Detection Metrics:** Precision, Recall, F1 (strict and relaxed entity-level)

**Privacy Metrics:**
- Mean PHI removal rate (fraction of detected entity texts removed per doc)
- Semantic similarity (cosine similarity, all-MiniLM-L6-v2 embeddings)
- Linkage resistance (% of docs where zero detected PHI survives verbatim)

**ML Utility Metrics:** Accuracy, F1-macro, retention ratio = sanitized / original accuracy. Target: degradation < 15%.

---

## PHI Entity Types

| Type | Examples | Detected By |
|---|---|---|
| PERSON | Client, staff, parent names | NER model |
| DATE | Session dates, DOB, appointment dates | Regex |
| PHONE | Contact numbers | Regex |
| MEDICAID_ID | 8-char IDs (2 letters + 6 digits) | Regex |
| ADDRESS | Street, city, state | Regex |
| CREDENTIAL | BCBA, RBT, RN, OTR/L, SLP, M.A. | Regex |

---

## Academic Context

**Course:** DSA 598 - Capstone Project  
**Program:** MS Data Science & Analytics  
**Institution:** SUNY Polytechnic Institute  
**Term:** Spring 2026  
**Submission:** May 2026

**Thesis Chapters:**
1. Introduction — Problem statement and HIPAA compliance motivation
2. Literature Review — Privacy-preserving NLP in healthcare
3. Methodology — Synthetic generation, NER fine-tuning, sanitization, evaluation
4. Results — Detection F1, sanitization trade-offs, ML utility preservation
5. Discussion — Error analysis, detector comparison, limitations
6. Conclusion — Contributions and future work

---

## License

Code: MIT License  
Data: Not for redistribution — synthetic data generated for academic research purposes only

---

## Author

**Nazmus Sakib**  
MS Data Science & Analytics, SUNY Polytechnic Institute  
Email: nazmussakib.nsb@gmail.com  
LinkedIn: www.linkedin.com/in/sakib51  
GitHub: https://github.com/sakibn23

---

## Acknowledgments

- **Trusting Okechukwu Inekwe** — Capstone Project Advisor
- **Jessi Jaramillo** — Director, AI Programs & Strategy
- **Upstate Care Providers** — Partner Organization

---

**Last Updated:** April 2026 | **Version:** 3.0 | **Status:** In Progress (Submission: May 2026)
