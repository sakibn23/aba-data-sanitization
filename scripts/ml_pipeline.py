"""ML classification pipeline for utility preservation analysis."""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC


LABEL_NAMES = {0: "routine", 1: "mild_issues", 2: "crisis"}
CV_FOLDS = 5

CLASSIFIERS = {
    "logistic_regression": LogisticRegression(
        max_iter=1000, C=1.0, class_weight="balanced", random_state=42
    ),
    "naive_bayes":   MultinomialNB(alpha=0.1),
    "linear_svc":    LinearSVC(max_iter=2000, C=1.0, random_state=42),
    "random_forest": RandomForestClassifier(
        n_estimators=100, class_weight="balanced", random_state=42, n_jobs=-1
    ),
}


# ── data loading ──────────────────────────────────────────────────────────────

def load_sanitized_data(method, sanitized_dir="outputs/sanitized"):
    """
    Load sanitized JSON for the given method.
    Returns (original_texts, sanitized_texts, labels).
    """
    path = Path(sanitized_dir) / method / f"{method}_sanitized.json"
    if not path.exists():
        print(f"  Error: {path} not found.")
        print("  Run sanitization first: python scripts/run_sanitization_complete.py")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        docs = json.load(f)

    orig_texts, san_texts, labels = [], [], []
    for doc in docs:
        if "label" not in doc:
            print(f"  Error: 'label' field missing in {path}.")
            print("  Re-run sanitization: python scripts/run_sanitization_complete.py")
            sys.exit(1)
        orig_texts.append(doc["original_text"])
        san_texts.append(doc["sanitized_text"])
        labels.append(doc["label"])

    return orig_texts, san_texts, labels

def _make_pipe(clf_name):
    """Return TF-IDF + classifier pipeline."""
    clf = {
        "logistic_regression": LogisticRegression(
            max_iter=1000, C=1.0, class_weight="balanced", random_state=42
        ),
        "naive_bayes":   MultinomialNB(alpha=0.1),
        "linear_svc":    LinearSVC(max_iter=2000, C=1.0, random_state=42),
        "random_forest": RandomForestClassifier(
            n_estimators=100, class_weight="balanced", random_state=42, n_jobs=-1
        ),
    }[clf_name]
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=10_000,
            sublinear_tf=True,
            min_df=2,
        )),
        ("clf", clf),
    ])

def _cv_scores(texts, labels, clf_name="logistic_regression"):
    """Run 5-fold stratified CV and return mean metrics."""
    skf = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=42)
    scoring = ["accuracy", "f1_macro", "f1_weighted"]
    cv_res = cross_validate(
        _make_pipe(clf_name), texts, labels, cv=skf, scoring=scoring
    )
    return {
        "accuracy":    round(float(np.mean(cv_res["test_accuracy"])),    4),
        "f1_macro":    round(float(np.mean(cv_res["test_f1_macro"])),    4),
        "f1_weighted": round(float(np.mean(cv_res["test_f1_weighted"])), 4),
    }


def evaluate_classifier(name, clf, texts, labels, cv=5):
    """Run stratified k-fold CV and return averaged metrics (multi-classifier)."""
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=20000,
        sublinear_tf=True,
    )
    pipe = Pipeline([("tfidf", vectorizer), ("clf", clf)])

    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
    scoring = ["accuracy", "f1_macro", "f1_weighted", "precision_macro", "recall_macro"]

    cv_results = cross_validate(pipe, texts, labels, cv=skf, scoring=scoring, n_jobs=-1)

    return {
        "accuracy":        round(float(np.mean(cv_results["test_accuracy"])),        4),
        "f1_macro":        round(float(np.mean(cv_results["test_f1_macro"])),        4),
        "f1_weighted":     round(float(np.mean(cv_results["test_f1_weighted"])),     4),
        "precision_macro": round(float(np.mean(cv_results["test_precision_macro"])), 4),
        "recall_macro":    round(float(np.mean(cv_results["test_recall_macro"])),    4),
    }


# ── feature analysis ─────────────────────────────────────────────────────────

def analyze_top_features(orig_texts, san_texts, labels,
                          top_n=15, output_path="outputs/ml/top_features.json"):
    """
    Train LR on original and sanitized text, extract top TF-IDF features per class.

    Shows WHICH words drive predictions — proving that clinical vocabulary
    (not PHI tokens) determines class membership.  If the top features are
    identical (or near-identical) between original and sanitized, it confirms
    that sanitization does not remove predictive signal.
    """
    from sklearn.model_selection import train_test_split

    result = {}

    for tag, texts in [("original", orig_texts), ("sanitized", san_texts)]:
        X_tr, _, y_tr, _ = train_test_split(
            texts, labels, test_size=0.2, stratify=labels, random_state=42
        )
        vec = TfidfVectorizer(ngram_range=(1, 2), max_features=10_000,
                              sublinear_tf=True, min_df=2)
        clf = LogisticRegression(max_iter=1000, C=1.0,
                                 class_weight="balanced", random_state=42,
                                 multi_class="ovr")
        X_vec = vec.fit_transform(X_tr)
        clf.fit(X_vec, y_tr)

        feature_names = vec.get_feature_names_out()
        per_class = {}
        for cls_idx, cls_name in LABEL_NAMES.items():
            coefs = clf.coef_[cls_idx]
            top_idx = coefs.argsort()[-top_n:][::-1]
            per_class[cls_name] = [
                {"feature": feature_names[i], "weight": round(float(coefs[i]), 4)}
                for i in top_idx
            ]
        result[tag] = per_class

    # Compare: which top features overlap between original and sanitized?
    overlap_summary = {}
    for cls_name in LABEL_NAMES.values():
        orig_feats = {f["feature"] for f in result["original"][cls_name]}
        san_feats  = {f["feature"] for f in result["sanitized"][cls_name]}
        shared = orig_feats & san_feats
        overlap_summary[cls_name] = {
            "shared_features":     sorted(shared),
            "overlap_pct":         round(len(shared) / top_n * 100, 1),
            "orig_only":           sorted(orig_feats - san_feats),
            "sanitized_only":      sorted(san_feats  - orig_feats),
        }
    result["feature_overlap"] = overlap_summary

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"\n  TOP FEATURES ANALYSIS (top {top_n} per class)")
    print(f"  {'Class':<14} {'Overlap%':>9}  Shared features (survive sanitization)")
    print(f"  {'-'*70}")
    for cls_name, ov in overlap_summary.items():
        shared_preview = ", ".join(ov["shared_features"][:6])
        print(f"  {cls_name:<14} {ov['overlap_pct']:>8.1f}%  {shared_preview}")
    print(f"\n  Full feature report saved to: {output_path}")

    return result


# ── utility preservation ──────────────────────────────────────────────────────

def run_utility_comparison(
    sanitized_dir="outputs/sanitized",
    methods=None,
    clf_name="logistic_regression",
    output_path="outputs/ml/utility_preservation.json",
    run_feature_analysis=False,
):
    """
    For each sanitization method compare original vs sanitized accuracy.
    The drop shows how much clinical utility each method sacrifices.

    Key metric from proposal: degradation = |orig - san| / orig * 100%
    Target: < 15% degradation.
    """
    if methods is None:
        methods = ["replace", "mask", "hash", "hybrid"]

    print(f"\n{'='*80}")
    print("ML UTILITY-PRESERVATION ANALYSIS")
    print(f"Classifier: {clf_name.upper()}")
    print("Compares classification accuracy: original vs sanitized text")
    print(f"{'='*80}\n")

    all_results = {}

    for method in methods:
        print(f"  Processing method: {method.upper()} ...", end=" ", flush=True)
        try:
            orig_texts, san_texts, labels = load_sanitized_data(method, sanitized_dir)
        except SystemExit:
            print(f"\n    SKIP: sanitized file not found for {method}\n")
            continue

        orig_scores = _cv_scores(orig_texts, labels, clf_name)
        san_scores  = _cv_scores(san_texts,  labels, clf_name)

        retention = {
            k: round(san_scores[k] / orig_scores[k], 4) if orig_scores[k] > 0 else None
            for k in orig_scores
        }
        degradation_pct = round(
            abs(orig_scores["accuracy"] - san_scores["accuracy"])
            / orig_scores["accuracy"] * 100, 2
        ) if orig_scores["accuracy"] > 0 else None

        all_results[method] = {
            "original":               orig_scores,
            "sanitized":              san_scores,
            "utility_retention_ratio": retention,
            "degradation_pct":        degradation_pct,
        }

        print(
            f"orig_acc={orig_scores['accuracy']:.4f}  "
            f"san_acc={san_scores['accuracy']:.4f}  "
            f"retention={retention['accuracy']:.4f}  "
            f"degradation={degradation_pct:.2f}%"
        )

    # summary table
    print(f"\n{'='*80}")
    print("UTILITY PRESERVATION SUMMARY  (5-fold CV, logistic regression)")
    print(f"{'='*80}")
    print(
        f"\n  {'Method':<10} {'Orig acc':>10} {'San acc':>10} "
        f"{'Retention':>10} {'Degradation%':>14} {'F1-macro(san)':>15}"
    )
    print(f"  {'-'*70}")
    for m, r in all_results.items():
        oa  = r["original"]["accuracy"]
        sa  = r["sanitized"]["accuracy"]
        ret = r["utility_retention_ratio"]["accuracy"]
        deg = r["degradation_pct"]
        f1  = r["sanitized"]["f1_macro"]
        meets = "PASS" if deg is not None and deg < 15 else "FAIL"
        print(
            f"  {m.upper():<10} {oa:>10.4f} {sa:>10.4f} "
            f"{ret:>10.4f} {deg:>13.2f}% {f1:>15.4f}  [{meets}]"
        )

    print(f"\n  NOTE: accuracy near 1.0 is expected on synthetic data.")
    print(f"  Key metric: 'Degradation%' — proposal target is < 15%.")
    print(f"  Retention=1.0 means zero utility loss.")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n  Results saved to: {output_path}")

    # Feature analysis on first available method
    if run_feature_analysis and all_results:
        first_method = next(iter(all_results))
        print(f"\n  Running feature analysis on '{first_method}' ...")
        orig_texts, san_texts, labels = load_sanitized_data(first_method, sanitized_dir)
        analyze_top_features(
            orig_texts, san_texts, labels,
            output_path="outputs/ml/top_features.json",
        )

    print(f"\n{'='*80}\n")
    return all_results


# ── single-method detailed pipeline ──────────────────────────────────────────

def run_pipeline(method, sanitized_dir="outputs/sanitized", cv=5):
    """Run all classifiers on a given sanitization method (sanitized text only)."""
    print(f"\n{'='*80}")
    print(f"ML PIPELINE  |  Method: {method.upper()}")
    print(f"{'='*80}\n")

    orig_texts, san_texts, labels = load_sanitized_data(method, sanitized_dir)

    label_dist = {}
    for lbl in labels:
        name = LABEL_NAMES.get(lbl, str(lbl))
        label_dist[name] = label_dist.get(name, 0) + 1

    print(f"  Loaded {len(san_texts)} documents")
    print(f"  Label distribution: {label_dist}")
    print(f"  Running {cv}-fold stratified CV (sanitized text)\n")

    results = {}

    for clf_name, clf in CLASSIFIERS.items():
        print(f"  Training {clf_name}...", end=" ", flush=True)
        metrics = evaluate_classifier(clf_name, clf, san_texts, labels, cv=cv)
        results[clf_name] = metrics
        print(
            f"  accuracy={metrics['accuracy']:.4f}  "
            f"f1_macro={metrics['f1_macro']:.4f}"
        )

    print(f"\n{'='*80}")
    print(f"RESULTS SUMMARY  |  {method.upper()}")
    print(f"{'='*80}")
    print(
        f"\n  {'Classifier':<22} {'Accuracy':>10} {'F1-Macro':>10} "
        f"{'F1-Weighted':>12} {'Precision':>10} {'Recall':>10}"
    )
    print(f"  {'-'*76}")
    for clf_name, m in results.items():
        print(
            f"  {clf_name:<22} {m['accuracy']:>10.4f} {m['f1_macro']:>10.4f} "
            f"{m['f1_weighted']:>12.4f} {m['precision_macro']:>10.4f} "
            f"{m['recall_macro']:>10.4f}"
        )
    print()

    return results


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=(
            "ML utility-preservation pipeline for sanitized ABA notes.\n"
            "Primary use: --compare (measures accuracy degradation per method)."
        )
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run utility-preservation comparison across all sanitization methods",
    )
    parser.add_argument(
        "--method",
        choices=["replace", "mask", "hash", "hybrid"],
        default="replace",
        help="Sanitization method for single-method mode (default: replace)",
    )
    parser.add_argument(
        "--methods",
        nargs="+",
        choices=["replace", "mask", "hash", "hybrid"],
        default=["replace", "mask", "hash", "hybrid"],
        help="Methods to compare in --compare mode (default: all four)",
    )
    parser.add_argument(
        "--clf",
        default="logistic_regression",
        choices=list(CLASSIFIERS.keys()),
        help="Classifier to use for utility comparison (default: logistic_regression)",
    )
    parser.add_argument(
        "--sanitized-dir",
        default="outputs/sanitized",
        help="Directory containing per-method sanitized outputs",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to save results JSON",
    )
    parser.add_argument(
        "--cv",
        type=int,
        default=5,
        help="Number of CV folds (default: 5)",
    )
    parser.add_argument(
        "--features",
        action="store_true",
        help="Also run top-feature analysis (shows which words drive predictions)",
    )
    args = parser.parse_args()

    if args.compare:
        output_path = args.output or "outputs/ml/utility_preservation.json"
        run_utility_comparison(
            sanitized_dir=args.sanitized_dir,
            methods=args.methods,
            clf_name=args.clf,
            output_path=output_path,
            run_feature_analysis=args.features,
        )
    else:
        output_path = args.output or f"outputs/ml/{args.method}_ml_results.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        results = run_pipeline(args.method, args.sanitized_dir, args.cv)
        payload = {"method": args.method, "cv_folds": args.cv, "classifiers": results}
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"  Results saved to: {output_path}")
        print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
