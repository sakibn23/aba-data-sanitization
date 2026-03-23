# ABA Data Sanitization Research Project

> Comparative Evaluation of Data Sanitization Strategies for Applied Behavior Analysis and Intellectual/Developmental Disabilities Documentation

[!\[Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[!\[License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[!\[Code style: black](https://img.shields.io/badge/code%2520style-black-000000.svg)](https://github.com/psf/black)

\---

## 📋 Table of Contents

* [Overview](#overview)
* [Research Objectives](#research-objectives)
* [Quick Start](#quick-start)
* [Project Structure](#project-structure)
* [Key Components](#key-components)
* [Progress](#progress)
* [Documentation](#documentation)
* [Partner Organization](#partner-organization)
* [Contact](#contact)
* [License](#license)

\---

## 🎯 Overview

This research project evaluates **semantic redaction** and **cryptographic hashing** strategies for PHI (Protected Health Information) de-identification in ABA (Applied Behavior Analysis) clinical documentation.

**Partner:** Upstate Caring Partners (UCP) ,Utica, NY 13502
**Institution:** SUNY Polytechnic Institute  
**Program:** MS Data Science \& Analytics

### Key Principles

* **Safety First:** ≥95% PHI exposure reduction (non-negotiable)
* **Use Case Driven:** Multi-system care coordination + predictive analytics
* **Evidence-Based:** Rigorous quantitative evaluation with statistical validation
* **Partner-Aligned:** Directly addresses UCP's operational needs

\---

## 🔬 Research Objectives

### Primary Research Question

> Which data sanitization strategy (semantic redaction, cryptographic hashing, or hybrid) achieves ≥95% PHI exposure reduction while best enabling multi-system care coordination and predictive analytics?

### Specific Aims

1. **Develop custom PHI recognizers** for UCP-specific identifiers (First Name, Last Name, DOB, Address, Medicaid ID)
2. **Implement two sanitization strategies** (semantic redaction as primary, cryptographic hashing as secondary)
3. **Evaluate on synthetic ABA/IDD documentation** (\~110 records across multiple document types)
4. **Quantify privacy-utility tradeoffs** using PHI reduction metrics, semantic similarity, and use case performance
5. **Deliver actionable recommendations** with implementation guidance

\---

## 🚀 Quick Start

### Prerequisites

* Python 3.9 or higher
* pip (Python package manager)
* Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/sakibn23/aba-data-sanitization.git
cd aba-data-sanitization

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\\\\Scripts\\\\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download spaCy language model (required for Presidio)
python3 -m spacy download en\\\_core\\\_web\\\_lg

# 5. Verify installation
python scripts/validate\\\_installation.py
```

### Quick Test

```bash
# Generate sample identifiers
python scripts/generate\\\_identifiers.py

# Test PHI recognition on sample text
python src/recognizers/test\\\_recognizer.py
```

\---

## 📁 Project Structure

```
aba-data-sanitization/
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── .gitignore                 # Git ignore rules
│
├── docs/                      # 📚 Documentation
│   ├── proposal/             # Research proposal
│   ├── presentations/        # Slides
│   └── progress/             # Weekly updates
│
├── data/                      # 📊 Data files
│   ├── identifiers/          # Name lists, addresses, IDs
│   ├── templates/            # Note templates
│   ├── examples/             # Hand-written examples
│   ├── synthetic/            # Generated notes
│   └── evaluation/           # Test/validation sets
│
├── src/                       # 💻 Source code
│   ├── generators/           # Data generation
│   ├── recognizers/          # PHI recognition
│   ├── sanitizers/           # Sanitization strategies
│   ├── evaluation/           # Metrics \\\& evaluation
│   └── utils/                # Utilities
│
├── notebooks/                 # 📓 Jupyter notebooks
│   ├── 01\\\_data\\\_exploration.ipynb
│   ├── 02\\\_recognizer\\\_testing.ipynb
│   └── 03\\\_evaluation\\\_analysis.ipynb
│
├── scripts/                   # 🔧 Utility scripts
│   ├── setup\\\_project.sh
│   ├── generate\\\_synthetic\\\_data.py
│   └── run\\\_evaluation.py
│
├── tests/                     # ✅ Unit tests
│   ├── test\\\_recognizers.py
│   ├── test\\\_sanitizers.py
│   └── test\\\_evaluation.py
│
└── results/                   # 📈 Output results
    ├── metrics/
    ├── visualizations/
    └── reports/
```

\---

## 🔧 Key Components

### 1\. Custom PHI Recognizers

Built on Microsoft Presidio, extended for UCP-specific identifiers:

* **Name Recognition:** First/Last names with context awareness
* **DOB Recognition:** Multiple date formats (MM/DD/YYYY, MM-DD-YYYY)
* **Address Recognition:** Street, City, State, Zip (excluding site names)
* **Medicaid ID Recognition:** 8-character alphanumeric (2 letters + 6 digits)

**Target Performance:** ≥95% recall, ≥90% precision

### 2\. Sanitization Strategies

**Primary (80% effort): Semantic Redaction**

* Replace identifiers with semantic-preserving tokens
* Maintains document structure and clinical meaning
* Example: "Emma Rodriguez" → "\[CLIENT\_NAME]"

**Secondary (20% effort): Cryptographic Hashing**

* SHA-256 with salting for one-way transformation
* Enables cross-system linkage without exposing raw identifiers
* Example: "EM456789" → "7a8b9c..."

### 3\. Evaluation Framework

**Primary Metrics:**

* PHI Exposure Reduction Rate (target: ≥95%)
* Entity Recognition Precision/Recall

**Secondary Metrics:**

* Multi-system coordination linkage accuracy (target: ≥90%)
* Predictive analytics model performance degradation (target: <15%)
* Semantic similarity (cosine similarity on embeddings)

**Tertiary Metrics:**

* UCP QA team usability ratings
* Computational performance (processing time per document)

\---

## 📊 Progress

### Milestones

* \[x] **Proposal Phase** (Complete)

  * Research proposal submitted
  * UCP requirements integrated
  * Literature review complete
* \[ ] **Milestone 1: Foundation** (March 14-24)

  * \[ ] Generate 100-150 synthetic ABA notes
  * \[ ] Implement baseline PHI recognizers
  * \[ ] Create ground truth annotations
  * \[ ] Midterm presentation (March 24)
* \[ ] **Milestone 2: Implementation** (March 25 - April 7)

  * \[ ] Complete all recognizers
  * \[ ] Implement both sanitization strategies
  * \[ ] Run initial evaluations
* \[ ] **Milestone 3: Evaluation \& Delivery** (April 8 - May 5)

  * \[ ] Use case testing
  * \[ ] Statistical analysis
  * \[ ] Final report
  * \[ ] Deliverables to UCP

### Current Status

**Last Updated:** \[DATE]

**This Week:**

* Setting up project infrastructure
* Creating identifier databases
* Installing Presidio framework

**Next Week:**

* Generate synthetic data
* Implement custom recognizers
* Begin sanitization strategy development

See [weekly updates](docs/progress/weekly_updates.md) for detailed progress.

\---

## 📚 Documentation

### Research Documents

* [Research Proposal](docs/proposal/research_proposal.pdf) - Complete proposal with methodology
* [Executive Summary](docs/proposal/executive_summary.md) - 1-page overview
* [Literature Review](docs/proposal/literature_review.md) - Key references

### Technical Documentation

* [Setup Guide](docs/setup_guide.md) - Detailed installation instructions
* [API Documentation](docs/api_docs.md) - Code documentation
* [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

### Meeting Notes

* [UCP Meeting Feb 12, 2026](docs/meeting_notes/ucp_feb_12_2026.md) - Requirements discussion
* [Advisor Meetings](docs/meeting_notes/advisor_meetings.md) - Progress check-ins

\---

## 🤝 Partner Organization
            Upstate Caring Partners (UCP
            125 Business Park Drive
            Utica, NY 13502
### 

**Location:** Syracuse, New York  
**Services:** IDD/ABA services for individuals with intellectual and developmental disabilities

**Key Contacts:**

* Jessi Jaramillo - Director of Data Strategy \& AI Systems ,
                    Upstate Caring Partners (UCP
                    125 Business Park Drive
                    Utica, NY 13502

**Collaboration Focus:**

* Safety-first approach to AI deployment
* Privacy-preserving clinical documentation
* Multi-system care coordination
* Responsible AI in healthcare

## 👨‍💻 Author

**Nazmus Sakib**  
MS Data Science \& Analytics  
SUNY Poly  
Utica, New York

**Email:** \[sakibn@sunypoly.edu]  
**GitHub:** [@sakibn23](https://github.com/sakibn23)  
**LinkedIn:** www.linkedin.com/in/sakib51

**Academic Advisor:** Trusting Inekwe, PhD

&#x20;                 Postdoctoral Researcher, SUNY Poly 

Professional Mentor : Jessi Jaramillo ,MSC

&#x20;                     Director , AI Programs \& Strategy

&#x20;                     Upstate Caring Partners

&#x20;                     

\---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Citation

If you use this work, please cite:

```bibtex
@mastersthesis{sakib2026aba,
  title={Comparative Evaluation of Data Sanitization Strategies for Applied Behavior Analysis Documentation},
  author={Sakib, \\Nazmus Sakib},
  year={2026},
  school={SUNY Polytechnic Institute},
  type={MS Capstone Project}
}
```

\---

## 🙏 Acknowledgments

* **Upstate Care Providers (UCP)** for partnership and domain expertise



## 📞 Contact \& Support

**Questions about the research?**  
Email: sakibn@sunypoly.edu

**Issues with code?**  
Open an issue on GitHub: [Issues](https://github.com/sakibn23/aba-data-sanitization/issues)

**Want to collaborate?**  
Reach out via email or LinkedIn!

\---

**Last Updated:** March 18, 2026  
**Status:** Active Development 🚧

