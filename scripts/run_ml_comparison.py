"""
ML Comparison Runner — compares all 4 sanitization methods across classifiers.

Runs ml_pipeline across replace / mask / hash / hybrid and produces a
side-by-side comparison table + combined JSON.

Usage:
  python scripts/run_ml_comparison.py
  python scripts/run_ml_comparison.py --cv 10 --output outputs/ml/comparison.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Allow `import ml_pipeline` when run as `python scripts/run_ml_comparison.py`
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPTS_DIR)

from ml_pipeline import run_pipeline, CLASSIFIERS  # noqa: E402

METHODS = ["replace", "mask", "hash", "hybrid"]


def run_comparison(sanitized_dir="outputs/sanitized", cv=5):
    """Run all classifiers on all sanitization methods and return nested results."""
    print(f"\n{'='*80}")
    print("ML COMPARISON RUNNER")
    print(f"{'='*80}")
    print(f"  Methods:    {', '.join(METHODS)}")
    print(f"  Classifiers:{', '.join(CLASSIFIERS.keys())}")
    print(f"  CV folds:   {cv}\n")

    all_results = {}

    for method in METHODS:
        results = run_pipeline(method, sanitized_dir=sanitized_dir, cv=cv)
        all_results[method] = results

    return all_results


def print_comparison_table(all_results, metric="f1_macro"):
    """Print a method × classifier comparison table for a single metric."""
    clf_names = list(CLASSIFIERS.keys())
    method_names = list(all_results.keys())

    col_w = 22
    print(f"\n{'='*80}")
    print(f"COMPARISON TABLE  |  metric: {metric}")
    print(f"{'='*80}")
    print(f"\n  {'Classifier':<{col_w}}", end="")
    for m in method_names:
        print(f"  {m.upper():>10}", end="")
    print()
    print(f"  {'-'*(col_w + len(method_names)*12)}")

    for clf in clf_names:
        print(f"  {clf:<{col_w}}", end="")
        for m in method_names:
            val = all_results[m][clf][metric]
            print(f"  {val:>10.4f}", end="")
        print()

    print()


def main():
    parser = argparse.ArgumentParser(description="Compare ML classifiers across sanitization methods.")
    parser.add_argument(
        "--sanitized-dir",
        default="outputs/sanitized",
        help="Directory with per-method sanitized outputs",
    )
    parser.add_argument(
        "--output",
        default="outputs/ml/comparison_results.json",
        help="Path to save comparison JSON",
    )
    parser.add_argument(
        "--cv",
        type=int,
        default=5,
        help="Number of CV folds (default: 5)",
    )
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    all_results = run_comparison(sanitized_dir=args.sanitized_dir, cv=args.cv)

    # Print comparison tables for key metrics
    for metric in ("accuracy", "f1_macro", "f1_weighted"):
        print_comparison_table(all_results, metric=metric)

    # Determine best method per classifier (by f1_macro)
    print(f"{'='*80}")
    print("BEST METHOD PER CLASSIFIER  |  by f1_macro")
    print(f"{'='*80}\n")
    for clf in CLASSIFIERS:
        best_method = max(all_results, key=lambda m: all_results[m][clf]["f1_macro"])
        best_score = all_results[best_method][clf]["f1_macro"]
        print(f"  {clf:<22}  best={best_method:<8}  f1_macro={best_score:.4f}")
    print()

    # Save
    payload = {"cv_folds": args.cv, "methods": all_results}
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"{'='*80}")
    print(f"  Comparison results saved to: {args.output}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
