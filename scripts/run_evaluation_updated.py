"""
Run Evaluation - Calculate Precision, Recall, F1

This script compares detected PHI vs ground truth annotations
and calculates performance metrics.

Uses both:
- Strict matching (exact start/end positions)
- Relaxed matching (overlapping spans)
"""

import json
import sys
from pathlib import Path


def load_json(path):
    """Load JSON file"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def overlap(span1, span2):
    """Check if two spans overlap"""
    return not (span1[1] <= span2[0] or span2[1] <= span1[0])


def strict_match(pred, true):
    """Strict matching: exact start, end, and type must match"""
    return (
        pred["start"] == true["start"] and
        pred["end"] == true["end"] and
        pred["type"] == true["type"]
    )


def relaxed_match(pred, true):
    """Relaxed matching: overlapping spans with same type"""
    return (
        overlap((pred["start"], pred["end"]), (true["start"], true["end"])) and
        pred["type"] == true["type"]
    )


def evaluate_doc(pred_entities, true_entities, mode="strict"):
    """
    Evaluate a single document
    
    Returns:
        TP, FP, FN counts
    """
    matched_true = set()
    TP = 0

    match_fn = strict_match if mode == "strict" else relaxed_match

    for p_idx, pred in enumerate(pred_entities):
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


def compute_metrics(TP, FP, FN):
    """Calculate precision, recall, F1"""
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0

    if precision + recall == 0:
        f1 = 0
    else:
        f1 = 2 * precision * recall / (precision + recall)

    return precision, recall, f1


def evaluate_all(pred_data, true_data, mode="strict"):
    """
    Evaluate all documents
    
    Args:
        pred_data: List of predicted documents (format: {"id": int, "entities": [...]})
        true_data: List of ground truth documents (format: {"doc_id": int, "entities": [...]})
        mode: "strict" or "relaxed"
    
    Returns:
        dict with metrics
    """
    total_TP, total_FP, total_FN = 0, 0, 0

    # Create mapping: doc_id -> entities
    true_map = {doc["doc_id"]: doc["entities"] for doc in true_data}

    for pred_doc in pred_data:
        doc_id = pred_doc["id"]

        pred_entities = pred_doc["entities"]
        true_entities = true_map.get(doc_id, [])

        TP, FP, FN = evaluate_doc(pred_entities, true_entities, mode)

        total_TP += TP
        total_FP += FP
        total_FN += FN

    precision, recall, f1 = compute_metrics(total_TP, total_FP, total_FN)

    return {
        "mode": mode,
        "TP": total_TP,
        "FP": total_FP,
        "FN": total_FN,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4)
    }


def print_results(results, title):
    """Print formatted results"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")
    
    print(f"Mode: {results['mode'].upper()}")
    print(f"\nConfusion Matrix:")
    print(f"  True Positives  (TP): {results['TP']:,}")
    print(f"  False Positives (FP): {results['FP']:,}")
    print(f"  False Negatives (FN): {results['FN']:,}")
    
    print(f"\nPerformance Metrics:")
    print(f"  Precision: {results['precision']:.2%} ({results['precision']:.4f})")
    print(f"  Recall:    {results['recall']:.2%} ({results['recall']:.4f})")
    print(f"  F1 Score:  {results['f1']:.2%} ({results['f1']:.4f})")


def main():
    print("\n" + "="*80)
    print("PHI DETECTION EVALUATION")
    print("="*80)
    
    # File paths
    pred_file = "outputs/detected_entities.json"
    true_file = "data/annotated/annotations_1000.json"
    
    # Check files exist
    if not Path(pred_file).exists():
        print(f"\n❌ Detected entities file not found: {pred_file}")
        print("   Run PHI detection first: python scripts/run_phi_detection.py")
        sys.exit(1)
    
    if not Path(true_file).exists():
        print(f"\n❌ Ground truth file not found: {true_file}")
        print("   Run ground truth generation first: python scripts/generate_ground_truth.py")
        sys.exit(1)
    
    # Load data
    print("\nLoading data...")
    pred_data = load_json(pred_file)
    true_data = load_json(true_file)
    
    print(f"  Detected entities: {len(pred_data)} documents")
    print(f"  Ground truth: {len(true_data)} documents")
    
    # Run evaluation
    print("\nRunning evaluation...")
    
    strict_results = evaluate_all(pred_data, true_data, mode="strict")
    relaxed_results = evaluate_all(pred_data, true_data, mode="relaxed")
    
    # Print results
    print_results(strict_results, "STRICT MATCHING (Exact Position + Type)")
    print_results(relaxed_results, "RELAXED MATCHING (Overlapping Spans + Type)")
    
    # Comparison with baseline
    print(f"\n{'='*80}")
    print("COMPARISON WITH BASELINE (150 notes, 68% recall)")
    print(f"{'='*80}\n")
    
    baseline_recall = 0.683
    improvement = (relaxed_results['recall'] - baseline_recall) / baseline_recall * 100
    
    print(f"Baseline Recall (150 notes, 4 scenarios): {baseline_recall:.2%}")
    print(f"Current Recall (1245 notes, 12 scenarios): {relaxed_results['recall']:.2%}")
    print(f"Improvement: {improvement:+.1f}%")
    
    # Save results
    output_file = "outputs/evaluation_results.json"
    results = {
        "strict": strict_results,
        "relaxed": relaxed_results,
        "baseline_comparison": {
            "baseline_recall": baseline_recall,
            "current_recall": relaxed_results['recall'],
            "improvement_percent": round(improvement, 2)
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: {output_file}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
