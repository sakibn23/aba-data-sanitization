"""
Quick Review Script - Compare Ground Truth vs Detected PHI

This script provides a quick overview of:
1. Ground truth annotations
2. Detected entities
3. Side-by-side comparison for sample notes
"""

import json
from pathlib import Path


def load_json(filepath):
    """Load JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def print_summary(data, title):
    """Print summary statistics"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")
    
    total_docs = len(data)
    total_entities = sum(len(doc['entities']) for doc in data)
    avg_entities = total_entities / total_docs if total_docs > 0 else 0
    
    # Count by type
    entity_counts = {}
    for doc in data:
        for entity in doc['entities']:
            entity_type = entity['type']
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
    
    print(f"📊 Summary:")
    print(f"  Total documents: {total_docs}")
    print(f"  Total entities: {total_entities}")
    print(f"  Average per note: {avg_entities:.1f}\n")
    
    print(f"📋 Entity Type Distribution:")
    for entity_type, count in sorted(entity_counts.items()):
        percentage = (count / total_entities * 100) if total_entities > 0 else 0
        print(f"  {entity_type:15s}: {count:5d} ({percentage:5.1f}%)")
    
    return entity_counts


def compare_sample(ground_truth, detected, doc_id=1):
    """Compare ground truth vs detected for a sample document"""
    print(f"\n{'='*80}")
    print(f"SAMPLE COMPARISON - Document ID: {doc_id}")
    print(f"{'='*80}\n")
    
    # Find documents
    gt_doc = next((d for d in ground_truth if d['doc_id'] == doc_id), None)
    det_doc = next((d for d in detected if d['id'] == doc_id), None)
    
    if not gt_doc:
        print(f"❌ Ground truth for doc {doc_id} not found")
        return
    
    if not det_doc:
        print(f"❌ Detected entities for doc {doc_id} not found")
        return
    
    gt_entities = gt_doc['entities']
    det_entities = det_doc['entities']
    
    print(f"Ground Truth: {len(gt_entities)} entities")
    print(f"Detected:     {len(det_entities)} entities\n")
    
    print("Ground Truth Entities (first 10):")
    for i, ent in enumerate(gt_entities[:10], 1):
        print(f"  {i:2d}. {ent['type']:15s} | {ent['text']}")
    
    print(f"\nDetected Entities (first 10):")
    for i, ent in enumerate(det_entities[:10], 1):
        print(f"  {i:2d}. {ent['type']:15s} | {ent['text']}")


def main():
    print("\n" + "="*80)
    print("PHI DETECTION REVIEW TOOL")
    print("="*80)
    
    # Paths
    ground_truth_file = "data/annotated/annotations_1000.json"
    detected_file = "outputs/detected_entities.json"
    
    # Check files exist
    if not Path(ground_truth_file).exists():
        print(f"\n❌ Ground truth file not found: {ground_truth_file}")
        return
    
    if not Path(detected_file).exists():
        print(f"\n❌ Detected entities file not found: {detected_file}")
        print(f"   Run PHI detection first: python scripts/run_phi_detection.py")
        return
    
    # Load data
    print("\nLoading data...")
    ground_truth = load_json(ground_truth_file)
    detected = load_json(detected_file)
    
    # Print summaries
    gt_counts = print_summary(ground_truth, "GROUND TRUTH (What PHI Actually Exists)")
    det_counts = print_summary(detected, "DETECTED PHI (What Your System Found)")
    
    # High-level comparison
    print(f"\n{'='*80}")
    print("OVERALL COMPARISON")
    print(f"{'='*80}\n")
    
    all_types = set(gt_counts.keys()) | set(det_counts.keys())
    
    print(f"{'Entity Type':<15s} {'Ground Truth':>12s} {'Detected':>12s} {'Difference':>12s}")
    print("-" * 80)
    
    for entity_type in sorted(all_types):
        gt_count = gt_counts.get(entity_type, 0)
        det_count = det_counts.get(entity_type, 0)
        diff = det_count - gt_count
        diff_str = f"{diff:+d}" if diff != 0 else "0"
        
        print(f"{entity_type:<15s} {gt_count:>12d} {det_count:>12d} {diff_str:>12s}")
    
    # Sample comparison
    compare_sample(ground_truth, detected, doc_id=1)
    
    print(f"\n{'='*80}")
    print("NEXT STEPS")
    print(f"{'='*80}\n")
    print("1. Review the comparison above")
    print("2. Run full evaluation: python scripts/run_evaluation.py")
    print("3. Calculate precision, recall, F1 scores")
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
