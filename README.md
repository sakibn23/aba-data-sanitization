# UCP ABA Data Sanitization Research Project

**Automated PHI Detection and Sanitization for Applied Behavior Analysis Clinical Documentation**

Capstone Project | MS Data Science \& Analytics | SUNY Polytechnic Institute | Spring 2026  
**Author:** Nazmus Sakib  
**Partner Organization:** Upstate Care Providers (UCP), Central New York

\---

## 📋 Project Overview

This research develops and evaluates an automated Protected Health Information (PHI) sanitization pipeline specifically designed for Applied Behavior Analysis (ABA) clinical documentation. The system enables privacy-preserving data utilization for quality improvement and research while maintaining HIPAA compliance.

### Key Contributions

1. **Synthetic ABA Data Generation**: Created 1,245 realistic synthetic session notes across 12 clinical scenario types
2. **Hybrid PHI Detection**: Implemented spaCy NER + regex-based detection achieving 68.67% recall
3. **Comparative Sanitization**: Evaluated 4 de-identification strategies (Replace, Mask, Hash, Hybrid)
4. **Performance Analysis**: Systematic evaluation across privacy protection and clinical utility dimensions

\---

## 🎯 Research Objectives

1. Develop realistic synthetic ABA session notes reflecting UCP documentation patterns
2. Implement and customize PHI detection for ABA-specific entities
3. Evaluate multiple sanitization strategies across privacy-utility trade-offs
4. Provide practical implementation guidance for community healthcare organizations

\---

## 📊 Key Results

### PHI Detection Performance

* **Precision:** 68.32%
* **Recall:** 68.67%
* **F1-Score:** 68.49%
* **Dataset:** 1,245 synthetic notes with 22,696 detected PHI instances

### Sanitization Performance

|Method|PHI Removal|Similarity|Recommended Use Case|
|-|-|-|-|
|**REPLACE**|88.79%|93.32%|Public data sharing|
|**MASK**|88.79%|86.10%|Moderate privacy needs|
|**HASH**|88.79%|90.78%|Record linkage|
|**HYBRID**|85.97%|93.00%|Internal research|

\---

## 🗂️ Project Structure

```
aba-data-sanitization/
├── data/
│   ├── identifiers/          # Reference data for synthetic generation
│   ├── annotated/            # Ground truth PHI annotations (not in repo)
│   └── synthetic/raw/        # Generated notes (not in repo)
│
├── scripts/
│   ├── generate\_synthetic\_notes.py      # Main data generator
│   ├── generate\_ground\_truth.py         # Annotation generator
│   ├── run\_phi\_detection.py             # PHI detection pipeline
│   ├── run\_sanitization\_complete.py     # Sanitization runner
│   └── run\_evaluation\_fixed.py          # Performance evaluation
│
├── docs/
│   ├── 12\_Scenario\_Templates\_Complete.md
│   ├── PHI\_Patterns\_Extracted\_from\_UCP\_Documents.md
│   └── methodology.md
│
├── examples/                 # Sample synthetic notes
├── outputs/                  # Results (not in repo)
└── README.md
```

**Note:** Large generated files (`data/synthetic/`, `outputs/`) are excluded from the repository. See **Reproduction Instructions** below to regenerate.

\---

## 🚀 Quick Start

### Prerequisites

* Python 3.8+
* 8GB+ RAM recommended
* \~2GB disk space for models and data

### Installation

```bash
# Clone repository
git clone https://github.com/\[your-username]/aba-data-sanitization.git
cd aba-data-sanitization

# Install dependencies
pip install -r requirements.txt

# Download spaCy English model
python -m spacy download en\_core\_web\_sm
```

### Complete Pipeline Execution

```bash
# Step 1: Generate synthetic notes (1,245 notes, \~10 minutes)
python scripts/generate\_synthetic\_notes.py

# Step 2: Generate ground truth annotations (\~2 minutes)
python scripts/generate\_ground\_truth\_fixed.py

# Step 3: Run PHI detection (\~5-10 minutes)
python scripts/run\_phi\_detection.py

# Step 4: Run sanitization (\~10-15 minutes)
python scripts/run\_sanitization\_complete.py

# Step 5: Evaluate performance (\~10 seconds)
python scripts/run\_evaluation\_fixed.py

# Step 6: Review results
python scripts/review\_phi\_results.py
```

\---

## 📈 Methodology

### 1\. Synthetic Data Generation

**12 Clinical Scenario Types:**

* **Progress \& Positive (35%):** Exceptional Progress, Skill Acquisition, Positive Social
* **Routine \& Maintenance (30%):** Standard Session, Maintenance
* **Challenges (25%):** Mild Challenging, Moderate Challenging, Environmental Triggers
* **Medical Integration (10%):** Medical Appointment, Medication Monitoring
* **Crisis \& Recovery (5%):** Crisis Intervention, Post-Crisis Recovery

**PHI Pattern Diversity:**

* 4 name format variations (First Last, Last First MI, etc.)
* 5 date format variations (MM/DD/YYYY, Month D YYYY, etc.)
* Parent names (40% dual-parent frequency)
* Phone numbers (315-XXX-XXXX Syracuse area)
* Professional credentials (BCBA, RN, OTR/L, etc.)

### 2\. PHI Detection Pipeline

**Hybrid Architecture:**

* **spaCy NER:** Person name detection using *en\_core\_web\_sm* model
* **Regex Patterns:** Structured PHI (dates, IDs, phones, addresses, credentials)

**Entity Types Detected:**

* PERSON, DATE, MEDICAID\_ID, PHONE, ADDRESS, CREDENTIAL

### 3\. Sanitization Strategies

* **REPLACE:** Complete replacement with entity labels `\[PERSON]`, `\[DATE]`
* **MASK:** Partial masking preserving first/last chars (`Emma` → `E\*\*a`)
* **HASH:** Deterministic SHA-256 hashing (enables linkage)
* **HYBRID:** Context-aware combination (credentials preserved)

### 4\. Evaluation Metrics

* **Detection:** Precision, Recall, F1-score (strict \& relaxed matching)
* **Privacy:** PHI removal rate (% detected entities removed)
* **Utility:** Semantic similarity (SentenceTransformer cosine similarity)

\---

## 📁 Data Files

### Included in Repository

✅ **Reference Data** (`data/identifiers/`)

* first\_names.txt (56 names)
* last\_names.txt (98 surnames)
* addresses.csv (49 Syracuse-area addresses)
* medicaid\_ids.txt (200 IDs)
* middle\_initials.txt (18 letters)
* parent\_first\_names.txt (80 names)
* phone\_numbers.txt (100 315- numbers)
* credentials.txt (20 professional titles)
* provider\_last\_names.txt (106 surnames)

✅ **Sample Notes** (`examples/`)

* 12 hand-crafted example notes (one per scenario type)

### Generated Locally (Not in Repository)

❌ **Synthetic Notes** (`data/synthetic/raw/`)

* 1,245 .txt files (\~60MB total)
* Regenerate with: `python scripts/generate\_synthetic\_notes.py`

❌ **Annotations** (`data/annotated/`)

* annotations\_1000\_fixed.json (\~8MB)
* Regenerate with: `python scripts/generate\_ground\_truth\_fixed.py`

❌ **Detection Results** (`outputs/`)

* detected\_entities.json (\~7MB)
* Regenerate with: `python scripts/run\_phi\_detection.py`

❌ **Sanitized Outputs** (`outputs/sanitized/`)

* 4 method folders with sanitized notes (\~200MB total)
* Regenerate with: `python scripts/run\_sanitization\_complete.py`

\---

## 🔬 Reproduction Instructions

To fully reproduce the research:

1. **Clone repository** and install dependencies (see Quick Start)
2. **Run complete pipeline** (see Complete Pipeline Execution)
3. **Review outputs** in `outputs/` directory
4. **Expected runtime:** \~40-50 minutes total

All results should match reported metrics within ±0.5% due to minor randomization in synthetic data generation.

\---

## 📊 Results Summary

### Detection Performance by Entity Type

|Entity Type|Precision|Recall|F1-Score|
|-|-|-|-|
|MEDICAID\_ID|100.0%|100.0%|100.0%|
|ADDRESS|100.0%|100.0%|100.0%|
|DATE|99.98%|99.98%|99.98%|
|PHONE|96.88%|96.88%|96.88%|
|CREDENTIAL|62.94%|62.94%|62.94%|
|PERSON|\~106%|\~106%|\~106%|

**Analysis:** Structured PHI (IDs, addresses, dates) achieved near-perfect detection. Unstructured entities (credentials, person names) show lower performance due to spaCy NER limitations and credential pattern variability.

### Sanitization Trade-offs

**REPLACE (Recommended):** Optimal balance of privacy (88.79%) and utility (93.32%)  
**HYBRID:** Highest utility (93.00%) with selective credential preservation  
**HASH:** Enables cross-document linkage while maintaining strong privacy

\---

## 🎓 Academic Context

**Course:** DSA 598 - Capstone Project  
**Program:** MS Data Science \& Analytics  
**Institution:** SUNY Polytechnic Institute  
**Term:** Spring 2026  
**Submission:** May 2026

**Thesis Chapters:**

1. Introduction - Problem statement and research objectives
2. Literature Review - Privacy-preserving healthcare data utilization
3. Methodology - Synthetic data generation, detection, sanitization
4. Results - Performance metrics and comparative analysis
5. Discussion - Error analysis, limitations, practical implications
6. Conclusion - Contributions and future work

\---

## 📄 License

This project is developed for academic research purposes in partnership with Upstate Care Providers.

**Code:** MIT License (scripts and tools)  
**Data:** Not for redistribution (synthetic data for research use only)

\---

## 👤 Author

**Nazmus Sakib**  
MS Data Science \& Analytics  
SUNY Polytechnic Institute  
Email: sakibn@sunypoly.edu  
LinkedIn: www.linkedin.com/in/sakib51  
GitHub: https://github.com/sakibn23

\---

## 🙏 Acknowledgments

* **Trusting Okechuwku Inekwe** - Capstone Project Advisor 
* **Jessi Jaramillo** - Director, AI Programs \& Strategy
* **Upstate Care Providers** - Partner Organization



\---

## 📮 Contact

For questions about this research or potential collaborations:

* Email: sakibn@sunypoly.edu
* GitHub Issues: \[Repository Issues Page]

\---

**Last Updated:** April 2026  
**Version:** 1.0  
**Status:** In Progress (Thesis Completion: May 2026)

