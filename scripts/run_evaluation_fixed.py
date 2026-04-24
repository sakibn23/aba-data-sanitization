"""
PHI Detection Evaluation — Precision / Recall / F1

Compares detected PHI entities against ground-truth annotations.
Supports strict matching (exact span + type) and relaxed (overlapping span + type).

Usage (from aba-data-sanitization/):
    # Evaluate default detected_entities.json (spacy_regex)
    python scripts/run_evaluation_fixed.py

    # Evaluate a specific detector output
    python scripts/run_evaluation_fixed.py --detected outputs/detected_entities_bert.json --output outputs/evaluation_results_fixed_bert.json

    # Evaluate all detectors at once
    python scripts/run_evaluation_fixed.py --all-detectors
"""

import argparse
import json
import os
import sys
from pathlib import Path


# ── matching helpers ──────────────────────────────────────────────────────────

def _overlap(s1, s2):
    return not (s1[1] <= s2[0] or s2[1] <= s1[0])


def _strict_match(pred, true):
    return (pred["start"] == true["start"] and
            pred["end"]   == true["end"]   and
            pred["type"]  == true["type"])


def _relaxed_match(pred, true):
    return (_overlap((pred["start"], pred["end"]), (true["start"], true["end"])) and
            pred["type"] == true["type"])


# ── evaluation ────────────────────────────────────────────────────────────────

def evaluate_doc(pred_entities, true_entities, mode="strict"):
    matched_true = set()
    TP = 0
    match_fn = _strict_match if mode == "strict" else _relaxed_match
    for pred in pred_entities:
        for t_idx, true in enumerate(true_entities):
            if t_idx in matched_true:
                continue
            if match_fn(pred, true):
                TP += 1
                matched_true.add(t_idx)
                break
    FP = len(pred_entities) - TP
    FN = len(true_entities) - TP
    return TP, FP, FN


def _metrics(TP, FP, FN):
    p = TP / (TP + FP) if (TP + FP) > 0 else 0.0
    r = TP / (TP + FN) if (TP + FN) > 0 else 0.0
    f = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    return p, r, f


def evaluate_all(pred_data, true_data, mode="strict"):
    total_TP = total_FP = total_FN = 0
    true_map = {doc["doc_id"]: doc["entities"] for doc in true_data}
    for pred_doc in pred_data:
        tp, fp, fn = evaluate_doc(
            pred_doc["entities"],
            true_map.get(pred_doc["id"], []),
            mode,
        )
        total_TP += tp
        total_FP += fp
        total_FN += fn
    p, r, f = _metrics(total_TP, total_FP, total_FN)
    return {
        "mode":      mode,
        "TP":        total_TP,
        "FP":        total_FP,
        "FN":        total_FN,
        "precision": round(p, 4),
        "recall":    round(r, 4),
        "f1":        round(f, 4),
    }


# ── reporting ─────────────────────────────────────────────────────────────────

def _print_results(results, title):
    print(f"\n{'='*70}")
    print(title)
    print(f"{'='*70}\n")
    print(f"  Mode: {results['mode'].upper()}")
    print(f"\n  Confusion Matrix:")
    print(f"    TP: {results['TP']:,}   FP: {results['FP']:,}   FN: {results['FN']:,}")
    print(f"\n  Precision : {results['precision']:.4f}  ({results['precision']:.2%})")
    print(f"  Recall    : {results['recall']:.4f}  ({results['recall']:.2%})")
    print(f"  F1        : {results['f1']:.4f}  ({results['f1']:.2%})")


def run_evaluation(pred_file, true_file, output_file, label="", test_ids=None):
    if not Path(pred_file).exists():
        print(f"  ERROR: detected entities not found: {pred_file}")
        print("  Run detection first: python scripts/run_phi_detection.py")
        return None
    if not Path(true_file).exists():
        print(f"  ERROR: ground truth not found: {true_file}")
        print("  Run: python scripts/generate_synthetic_notes.py")
        return None

    pred_data = json.loads(Path(pred_file).read_text(encoding="utf-8"))
    true_data = json.loads(Path(true_file).read_text(encoding="utf-8"))

    if test_ids is not None:
        pred_data = [d for d in pred_data if d["id"] in test_ids]
        true_data = [d for d in true_data if d["doc_id"] in test_ids]
        scope = f"test-only ({len(pred_data)} docs)"
    else:
        scope = f"all ({len(pred_data)} docs)"

    print(f"\n  Detected entities : {scope}  ({pred_file})")
    print(f"  Ground truth      : {len(true_data)} docs  ({true_file})")

    strict  = evaluate_all(pred_data, true_data, "strict")
    relaxed = evaluate_all(pred_data, true_data, "relaxed")

    tag = f" [{label.upper()}]" if label else ""
    _print_results(strict,  f"STRICT MATCHING{tag}  (exact span + type)")
    _print_results(relaxed, f"RELAXED MATCHING{tag} (overlapping span + type)")

    results = {"strict": strict, "relaxed": relaxed}

    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    Path(output_file).write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n  Saved to: {output_file}")
    return results


# ── CLI ───────────────────────────────────────────────────────────────────────

_DETECTOR_FILES = {
    "spacy_regex": ("outputs/detected_entities.json",           "outputs/evaluation_results_fixed_spacy_regex.json"),
    "presidio":    ("outputs/detected_entities_presidio.json",  "outputs/evaluation_results_fixed_presidio.json"),
    "bert":        ("outputs/detected_entities_bert.json",      "outputs/evaluation_results_fixed_bert.json"),
    "deberta":     ("outputs/detected_entities_deberta.json",   "outputs/evaluation_results_fixed_deberta.json"),
    "ensemble":    ("outputs/detected_entities_ensemble.json",  "outputs/evaluation_results_fixed_ensemble.json"),
}

_DEFAULT_TRUE = "data/annotated/annotations_generated.json"


def main():
    parser = argparse.ArgumentParser(description="Evaluate PHI detection against ground truth.")
    parser.add_argument(
        "--detected",
        default="outputs/detected_entities.json",
        help="Path to detected_entities JSON (default: spacy_regex output)",
    )
    parser.add_argument(
        "--ground-truth",
        default=_DEFAULT_TRUE,
        help=f"Ground truth annotations JSON (default: {_DEFAULT_TRUE})",
    )
    parser.add_argument(
        "--output",
        default="outputs/evaluation_results_fixed.json",
        help="Where to save results JSON",
    )
    parser.add_argument(
        "--all-detectors",
        action="store_true",
        help="Evaluate all detectors using their standard output files",
    )
    parser.add_argument(
        "--test-ids",
        default=None,
        help="Path to test_ids.json from train_ner.py. "
             "When given, evaluation is restricted to held-out test notes only.",
    )
    args = parser.parse_args()

    test_ids = None
    if args.test_ids:
        if not Path(args.test_ids).exists():
            print(f"ERROR: test IDs file not found: {args.test_ids}")
            sys.exit(1)
        test_ids = set(json.loads(Path(args.test_ids).read_text(encoding="utf-8")))
        print(f"Restricting evaluation to {len(test_ids)} held-out test notes ({args.test_ids})")

    print("\n" + "="*70)
    print("PHI DETECTION EVALUATION")
    print("="*70)

    if args.all_detectors:
        summary = {}
        for det, (pred_f, out_f) in _DETECTOR_FILES.items():
            print(f"\n--- {det.upper()} ---")
            r = run_evaluation(pred_f, args.ground_truth, out_f, label=det, test_ids=test_ids)
            if r:
                summary[det] = {
                    "strict_f1":  r["strict"]["f1"],
                    "relaxed_f1": r["relaxed"]["f1"],
                    "strict_precision":  r["strict"]["precision"],
                    "strict_recall":     r["strict"]["recall"],
                    "relaxed_precision": r["relaxed"]["precision"],
                    "relaxed_recall":    r["relaxed"]["recall"],
                }

        print(f"\n{'='*70}")
        print("DETECTOR COMPARISON SUMMARY")
        print(f"{'='*70}")
        print(f"\n  {'Detector':<14} {'Strict F1':>10} {'Strict P':>10} {'Strict R':>10} {'Relaxed F1':>11}")
        print(f"  {'-'*58}")
        for det, m in summary.items():
            print(
                f"  {det.upper():<14} {m['strict_f1']:>10.4f} "
                f"{m['strict_precision']:>10.4f} {m['strict_recall']:>10.4f} "
                f"{m['relaxed_f1']:>11.4f}"
            )
        summary_path = "outputs/evaluation_summary.json"
        Path(summary_path).write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"\n  Summary saved to: {summary_path}")
    else:
        run_evaluation(args.detected, args.ground_truth, args.output, test_ids=test_ids)

    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
