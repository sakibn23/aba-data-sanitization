import argparse
import hashlib
import json
import os
import re
from pathlib import Path

import numpy as np


_SCENARIO_LABELS = {
    # routine / positive
    "exceptional_progress":  0,
    "skill_acquisition":     0,
    "positive_social":       0,
    "standard_session":      0,
    "maintenance":           0,
    # mild issues
    "mild_challenging":      1,
    "moderate_challenging":  1,
    "environmental_triggers":1,
    # crisis / severe
    "crisis":                2,
    "post_crisis":           2,
    "medical_appointment":   2,
    "medication":            2,
}

def label_from_filename(filename: str) -> int:
    """Extract label from filename scenario keyword."""
    stem = Path(filename).stem.lower()
    for keyword, lbl in _SCENARIO_LABELS.items():
        if keyword in stem:
            return lbl
    return 0

class Sanitizer:
    def __init__(self, method="replace"):
        self.method = method

    def replace(self, text, ent_type):
        return f"[{ent_type}]"

    def mask(self, text):
        if len(text) <= 2:
            return "*" * len(text)
        return text[0] + "*" * (len(text) - 2) + text[-1]

    def hash_text(self, text):
        return hashlib.sha256(text.encode()).hexdigest()[:8]

    def hybrid(self, text, ent_type):
        if ent_type in ("PERSON", "MEDICAID_ID", "PHONE", "ADDRESS"):
            return f"[{ent_type}]"
        elif ent_type == "DATE":
            return self.mask(text)
        elif ent_type == "CREDENTIAL":
            return text   # keep credentials for clinical context
        return text

    def sanitize(self, text, entities):
        for ent in sorted(entities, key=lambda x: x["start"], reverse=True):
            start, end = ent["start"], ent["end"]
            ent_type   = ent["type"]
            original   = text[start:end]
            if self.method == "replace":
                repl = self.replace(original, ent_type)
            elif self.method == "mask":
                repl = self.mask(original)
            elif self.method == "hash":
                repl = self.hash_text(original)
            elif self.method == "hybrid":
                repl = self.hybrid(original, ent_type)
            else:
                repl = original
            text = text[:start] + repl + text[end:]
        return text

def phi_removal_rate(entities, sanitized_text):
    if not entities:
        return 1.0
    removed = sum(1 for e in entities if e["text"] not in sanitized_text)
    return removed / len(entities)


def run_sanitization_pipeline(notes_dir, detection_file, output_dir):
    with open(detection_file, encoding="utf-8") as f:
        detections = json.load(f)

    entity_map = {d["id"]: d["entities"] for d in detections}
    detected_ids = set(entity_map.keys())

    # Build note lookup: note_id → {filename, text}
    all_files = sorted(Path(notes_dir).glob("*.txt"))
    note_lookup = {}
    for nf in all_files:
        m = re.match(r"note_(\d+)", nf.stem)
        if m:
            note_lookup[int(m.group(1))] = nf

    note_ids_to_process = sorted(detected_ids & set(note_lookup.keys()))

    methods = ["replace", "mask", "hash", "hybrid"]
    summary = {}

    for method in methods:
        sanitizer = Sanitizer(method=method)
        sanitized_docs = []
        removal_rates  = []

        for note_id in note_ids_to_process:
            nf           = note_lookup[note_id]
            original     = nf.read_text(encoding="utf-8")
            entities     = entity_map.get(note_id, [])
            sanitized    = sanitizer.sanitize(original, entities)
            removal      = phi_removal_rate(entities, sanitized)
            label        = label_from_filename(nf.name)

            removal_rates.append(removal)
            sanitized_docs.append({
                "id":               note_id,
                "filename":         nf.name,
                "label":            label,
                "original_text":    original,
                "sanitized_text":   sanitized,
                "num_entities":     len(entities),
                "phi_removal_rate": round(removal, 4),
            })

        avg_removal = float(np.mean(removal_rates)) if removal_rates else 0.0
        summary[method] = {
            "avg_phi_removal_rate": round(avg_removal, 4),
            "total_documents":      len(sanitized_docs),
        }
        method_dir = Path(output_dir) / method
        method_dir.mkdir(parents=True, exist_ok=True)
        out_json = method_dir / f"{method}_sanitized.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(sanitized_docs, f, indent=2)

        # Save individual text files
        txt_dir = method_dir / "notes"
        txt_dir.mkdir(exist_ok=True)
        for doc in sanitized_docs:
            (txt_dir / f"sanitized_{doc['filename']}").write_text(
                doc["sanitized_text"], encoding="utf-8"
            )
    summary_file = Path(output_dir) / "sanitization_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSanitization complete: {summary_file}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Apply sanitization methods to test notes.")
    parser.add_argument(
        "--detected",
        default="outputs/detected_entities_bert.json",
        help="Path to detected_entities JSON (default: bert)",
    )
    parser.add_argument(
        "--notes-dir",
        default="data/synthetic/raw",
        help="Directory of note .txt files",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/sanitized",
        help="Output directory for sanitized results",
    )
    args = parser.parse_args()

    if not Path(args.notes_dir).exists():
        print(f"ERROR: Notes directory not found: {args.notes_dir}")
        return
    if not Path(args.detected).exists():
        print(f"ERROR: Detection file not found: {args.detected}")
        return

    run_sanitization_pipeline(args.notes_dir, args.detected, args.output_dir)


if __name__ == "__main__":
    main()
