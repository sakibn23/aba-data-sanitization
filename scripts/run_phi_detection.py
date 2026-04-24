import argparse
import json
import os
import sys
from pathlib import Path

# scripts/ on path so package `detectors` resolves when run as python scripts/run_phi_detection.py
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPTS_DIR)

from detectors import create_detector, DETECTOR_CHOICES  # noqa: E402

_TYPE_MAP = {
    "US_DRIVER_LICENSE": "MEDICAID_ID",
    "DATE_TIME": "DATE",
    "PHONE_NUMBER": "PHONE",
}


def normalize_entity(entity):
    entity["type"] = _TYPE_MAP.get(entity["type"], entity["type"])
    return entity


def clean_entity_span(entity, text):

    start = entity["start"]
    end   = entity["end"]
    span  = entity["text"]

    # Strip leading non-alphanumeric characters
    i = 0
    while i < len(span) and not span[i].isalnum():
        i += 1
    if i > 0:
        start += i
        span = span[i:]

    # Strip trailing whitespace / newlines
    j = len(span)
    while j > 0 and span[j - 1] in " \t\n\r":
        j -= 1
    if j < len(span):
        span = span[:j]
        end = start + j

    # Only apply if the cleaned span is non-empty and matches the actual text
    if span and text[start:end] == span:
        entity["text"]  = span
        entity["start"] = start
        entity["end"]   = end

    return entity


def _note_id_from_filename(path: Path) -> int | None:
    """Extract the numeric note ID from a filename like note_0005_scenario.txt → 5."""
    import re
    m = re.match(r"note_(\d+)", path.stem)
    return int(m.group(1)) if m else None


def process_notes(input_dir, output_file, detector, test_ids=None):
    all_files  = sorted(Path(input_dir).glob("*.txt"))

    if test_ids is not None:
        # Keep only files whose 1-based sequence number is in test_ids.
        note_files = [
            f for idx, f in enumerate(all_files, start=1)
            if idx in test_ids
        ]
        mode_label = f"TEST-ONLY ({len(note_files)} of {len(all_files)} notes)"
    else:
        note_files = all_files
        mode_label = f"ALL ({len(note_files)} notes)"

    print(f"\n{'='*80}")
    print(f"PHI DETECTION RUNNER")
    print(f"{'='*80}\n")
    print(f"Detector: {detector.__class__.__name__}")
    print(f"Input directory: {input_dir}")
    print(f"Mode: {mode_label}\n")

    results = []

    for seq_idx, note_file in enumerate(note_files, start=1):
        with open(note_file, "r", encoding="utf-8") as f:
            text = f.read()
        note_id = _note_id_from_filename(note_file)
        if note_id is None:
            note_id = seq_idx

        entities = [
            clean_entity_span(normalize_entity(e), text)
            for e in detector.detect(text)
        ]

        results.append({"id": note_id, "entities": entities})

        if seq_idx % 100 == 0:
            print(f"  Processed {seq_idx}/{len(note_files)} notes...")

    out_dir = os.path.dirname(output_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*80}")
    print("PHI DETECTION COMPLETE!")
    print(f"{'='*80}\n")

    total_entities = sum(len(doc["entities"]) for doc in results)
    entity_counts = {}
    for doc in results:
        for entity in doc["entities"]:
            entity_type = entity["type"]
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1

    print("Summary:")
    print(f"  Total documents: {len(results)}")
    print(f"  Total detected PHI: {total_entities}")
    if results:
        print(f"  Average PHI per note: {total_entities / len(results):.1f}\n")
    else:
        print()

    print("Detected Entity Types:")
    if total_entities:
        for entity_type, count in sorted(entity_counts.items()):
            print(f"  {entity_type:15s}: {count:5d} ({count/total_entities*100:.1f}%)")
    else:
        print("  (none)")

    print(f"\n  Output saved to: {output_file}\n")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description="Run PHI detection on synthetic notes.")
    parser.add_argument(
        "--detector",
        choices=["spacy_regex", "presidio", "bert", "deberta", "ensemble"],
        default="spacy_regex",
        help="Detection backend (default: spacy_regex)",
    )
    parser.add_argument(
        "--input-dir",
        default="data/synthetic/raw",
        help="Directory of note_*.txt files",
    )
    parser.add_argument(
        "--output",
        default="outputs/detected_entities.json",
        help="Path for detected_entities JSON",
    )
    parser.add_argument(
        "--test-ids",
        default=None,
        help="Path to test_ids.json produced by train_ner.py. "
             "When given, only held-out test notes are processed.",
    )
    parser.add_argument(
        "--ensemble-model",
        choices=["bert", "deberta", "both"],
        default="bert",
        help="Transformer backend for ensemble detector: bert | deberta | both (default: bert)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input_dir):
        print(f"ERROR: Input directory not found: {args.input_dir}")
        sys.exit(1)

    test_ids = None
    if args.test_ids:
        if not os.path.exists(args.test_ids):
            print(f"ERROR: test IDs file not found: {args.test_ids}")
            print("  Run train_ner.py first — it creates this file automatically.")
            sys.exit(1)
        with open(args.test_ids, encoding="utf-8") as f:
            test_ids = set(json.load(f))
        print(f"Loaded {len(test_ids)} test note IDs from {args.test_ids}")

    detector = create_detector(args.detector, ensemble_model=args.ensemble_model)
    process_notes(args.input_dir, args.output, detector, test_ids=test_ids)

    print("PHI detection complete!")
    print("\nNext steps:")
    print(f"  1. Review detected entities in {args.output}")
    print("  2. Run evaluation: python scripts/run_evaluation_fixed.py")
    print("  3. Compare precision/recall/F1 vs. ground truth")


if __name__ == "__main__":
    main()
