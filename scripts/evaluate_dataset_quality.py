"""
Dataset Quality Evaluator — PHI difficulty metrics and clean vs noisy comparison.

Computes three groups of metrics:

1. PHI Difficulty Score
   - % of PHI instances in partial/abbreviated format (Initial. Last, street-only, etc.)
   - % of PHONE instances in non-standard format (anything other than NXX-NXX-XXXX)
   - % of DATE instances in non-standard format (not MM/DD/YYYY)
   - Average PHI instances per note

2. Clean vs Noisy Dataset Comparison
   If both clean and noisy annotation files are available, compare their PHI
   difficulty scores side-by-side.

3. Token Noise Ratio
   Estimated fraction of words containing abbreviations or typos compared to
   a reference vocabulary of standard clinical words.

Output: console table + JSON saved to outputs/dataset_quality.json

Usage:
    # With noise variants generated
    python scripts/evaluate_dataset_quality.py

    # Explicit paths
    python scripts/evaluate_dataset_quality.py \
        --annotations data/annotated/annotations_generated.json \
        --notes-dir   data/synthetic/raw
"""

import argparse
import json
import re
from pathlib import Path

# ── reference patterns ───────────────────────────────────────────────────────

_STANDARD_DATE   = re.compile(r"^\d{2}/\d{2}/\d{4}$")          # MM/DD/YYYY
_STANDARD_PHONE  = re.compile(r"^\d{3}-\d{3}-\d{4}$")          # NXX-NXX-XXXX
_PARTIAL_NAME    = re.compile(r"^[A-Z]\.\s+\w+$")              # "E. Rodriguez"
_INITIAL_LAST    = re.compile(r"^[A-Z]\.\s+[A-Z][a-z]+$")
_ABBREV_TOKENS   = {
    "pt", "bx", "bxs", "w/", "w/o", "re:", "indep", "approx",
    "min", "sec", "rec", "recs", "tx", "intv", "comm", "freq",
    "dur", "sess", "f/u", "gl", "info", "asmt", "indep.",
}


# ── helpers ──────────────────────────────────────────────────────────────────

def load_annotations(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_notes(notes_dir: str) -> dict:
    """Return {doc_id: text} by reading note files in sorted order."""
    note_files = sorted(Path(notes_dir).glob("*.txt"))
    notes = {}
    for idx, nf in enumerate(note_files, start=1):
        notes[idx] = nf.read_text(encoding="utf-8")
    return notes


def phi_difficulty(annotations: list) -> dict:
    """
    Compute PHI difficulty metrics from annotation list.

    Returns
    -------
    dict with keys:
      total_docs, total_phi, phi_per_doc,
      partial_person_pct, nonstandard_phone_pct, nonstandard_date_pct,
      entity_type_counts
    """
    total_phi    = 0
    partial_name = 0
    nonstd_phone = 0
    nonstd_date  = 0
    type_counts: dict = {}

    for doc in annotations:
        for ent in doc.get("entities", []):
            total_phi += 1
            t = ent["type"]
            type_counts[t] = type_counts.get(t, 0) + 1
            text = ent["text"].strip()

            if t == "PERSON":
                if _PARTIAL_NAME.match(text) or _INITIAL_LAST.match(text):
                    partial_name += 1

            elif t == "PHONE":
                if not _STANDARD_PHONE.match(text):
                    nonstd_phone += 1

            elif t == "DATE":
                if not _STANDARD_DATE.match(text):
                    nonstd_date += 1

    n_docs = len(annotations)
    n_persons = type_counts.get("PERSON", 0)
    n_phones  = type_counts.get("PHONE", 0)
    n_dates   = type_counts.get("DATE", 0)

    return {
        "total_docs":            n_docs,
        "total_phi":             total_phi,
        "phi_per_doc":           round(total_phi / n_docs, 2) if n_docs else 0,
        "entity_type_counts":    type_counts,
        "partial_person_pct":    round(partial_name / n_persons * 100, 1) if n_persons else 0,
        "nonstandard_phone_pct": round(nonstd_phone / n_phones  * 100, 1) if n_phones  else 0,
        "nonstandard_date_pct":  round(nonstd_date  / n_dates   * 100, 1) if n_dates   else 0,
    }


def token_noise_ratio(notes: dict, annotations: list) -> float:
    """
    Estimate what fraction of non-PHI words look like abbreviations/typos.
    Returns a percentage.
    """
    ann_map = {doc["doc_id"]: doc["entities"] for doc in annotations}
    abbrev_count = 0
    total_words  = 0

    for doc_id, text in notes.items():
        entities = ann_map.get(doc_id, [])
        # Build set of PHI character ranges
        phi_ranges = {(e["start"], e["end"]) for e in entities}

        # Tokenise non-PHI regions
        prev_end = 0
        for ent in sorted(entities, key=lambda e: e["start"]):
            region = text[prev_end:ent["start"]]
            words = region.split()
            total_words += len(words)
            abbrev_count += sum(1 for w in words if w.lower().rstrip(".") in _ABBREV_TOKENS)
            prev_end = ent["end"]

        region = text[prev_end:]
        words = region.split()
        total_words += len(words)
        abbrev_count += sum(1 for w in words if w.lower().rstrip(".") in _ABBREV_TOKENS)

    return round(abbrev_count / total_words * 100, 2) if total_words else 0.0


# ── printing ─────────────────────────────────────────────────────────────────

def print_difficulty(label: str, m: dict) -> None:
    print(f"\n  [{label}]")
    print(f"    Total docs            : {m['total_docs']:,}")
    print(f"    Total PHI instances   : {m['total_phi']:,}")
    print(f"    PHI per note          : {m['phi_per_doc']}")
    print(f"    Partial PERSON (%)    : {m['partial_person_pct']}%")
    print(f"    Non-std PHONE  (%)    : {m['nonstandard_phone_pct']}%")
    print(f"    Non-std DATE   (%)    : {m['nonstandard_date_pct']}%")
    print(f"    Entity types          :")
    for t, c in sorted(m["entity_type_counts"].items()):
        print(f"      {t:<15}: {c:,}")


def print_comparison_table(clean: dict, noisy: dict) -> None:
    metrics = [
        ("PHI / note",         "phi_per_doc"),
        ("Partial PERSON (%)", "partial_person_pct"),
        ("Non-std PHONE (%)",  "nonstandard_phone_pct"),
        ("Non-std DATE (%)",   "nonstandard_date_pct"),
    ]
    col = 26
    print(f"\n  {'Metric':<{col}} {'Clean':>10} {'Noisy':>10}  {'Harder?':>8}")
    print(f"  {'-'*(col+32)}")
    for label, key in metrics:
        c_val = clean[key]
        n_val = noisy[key]
        harder = "yes" if n_val > c_val else "-"
        print(f"  {label:<{col}} {str(c_val):>10} {str(n_val):>10}  {harder:>8}")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Measure PHI difficulty and compare clean vs noisy datasets."
    )
    parser.add_argument(
        "--annotations",
        default="data/annotated/annotations_generated.json",
        help="Primary annotations file (may contain both clean and noisy docs)",
    )
    parser.add_argument(
        "--notes-dir", default="data/synthetic/raw",
        help="Directory with generated .txt note files",
    )
    parser.add_argument(
        "--output", default="outputs/dataset_quality.json",
    )
    args = parser.parse_args()

    print("\n" + "="*70)
    print("DATASET QUALITY EVALUATION")
    print("="*70)

    if not Path(args.annotations).exists():
        print(f"ERROR: annotations file not found: {args.annotations}")
        return

    annotations = load_annotations(args.annotations)
    notes = load_notes(args.notes_dir) if Path(args.notes_dir).exists() else {}

    # Split clean vs noisy by 'variant' field in documents.json if available
    doc_json = Path("data/raw/documents.json")
    clean_ids, noisy_ids = set(), set()
    if doc_json.exists():
        docs = json.loads(doc_json.read_text(encoding="utf-8"))
        for d in docs:
            if d.get("variant", "clean") == "clean":
                clean_ids.add(d["id"])
            else:
                noisy_ids.add(d["id"])

    all_metrics  = phi_difficulty(annotations)
    results = {"all": all_metrics}

    print("\nOverall PHI Difficulty")
    print_difficulty("ALL NOTES", all_metrics)

    if clean_ids and noisy_ids:
        clean_ann = [a for a in annotations if a["doc_id"] in clean_ids]
        noisy_ann = [a for a in annotations if a["doc_id"] in noisy_ids]
        clean_m = phi_difficulty(clean_ann)
        noisy_m = phi_difficulty(noisy_ann)
        results["clean"] = clean_m
        results["noisy"] = noisy_m

        print("\n\nClean vs Noisy Comparison")
        print_difficulty("CLEAN", clean_m)
        print_difficulty("NOISY", noisy_m)

        print("\n\nSummary Table")
        print_comparison_table(clean_m, noisy_m)

    if notes:
        ratio = token_noise_ratio(notes, annotations)
        results["abbrev_token_pct"] = ratio
        print(f"\n\n  Abbreviation token ratio: {ratio}%")
        print("  (fraction of non-PHI words that are clinical abbreviations)")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n  Saved to: {args.output}")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
