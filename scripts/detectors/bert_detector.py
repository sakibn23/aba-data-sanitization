"""BERT-based PHI detector. PERSON via fine-tuned BERT; other types via regex."""

import os
import re
import sys
from pathlib import Path

from .base_detector import PHIDetector
from .phi_patterns import (
    CALENDAR_DATE_PATTERNS,
    CREDENTIAL_PATTERNS,
    apply_person_postprocessing,
)

# Default location of the fine-tuned model (relative to this file's parent/parent)
_DEFAULT_MODEL_DIR = Path(__file__).parent / "bert_ner_model"


class BertDetector(PHIDetector):
    """PERSON via fine-tuned BERT; DATE/PHONE/etc via regex patterns."""

    # Base model to use when fine-tuned model isn't available yet
    _BASE_MODEL = "dslim/bert-base-NER"

    def __init__(self, model_dir: str | None = None):
        model_path = Path(model_dir) if model_dir else _DEFAULT_MODEL_DIR

        # Check that the directory exists AND contains a valid saved model
        _config = model_path / "config.json"
        if not model_path.exists() or not _config.exists():
            print(f"WARNING: Fine-tuned BERT model not found. Falling back to base model.")
            model_path = self._BASE_MODEL   # type: ignore[assignment]
        else:
            print(f"Loaded BERT model from {model_path}")
        try:
            import torch
            from transformers import AutoModelForTokenClassification, AutoTokenizer
        except ImportError:
            print("ERROR: transformers / torch not installed. Install with: pip install torch transformers")
            sys.exit(1)

        self.tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        self.model     = AutoModelForTokenClassification.from_pretrained(str(model_path))
        self.model.eval()

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        raw = self.model.config.id2label  # e.g. {0:'O', 1:'B-PER', 2:'I-PER', ...}
        self.id2label = {}
        for idx, lbl in raw.items():
            if lbl.startswith("B-") and "PER" in lbl.upper():
                self.id2label[idx] = "B-PERSON"
            elif lbl.startswith("I-") and "PER" in lbl.upper():
                self.id2label[idx] = "I-PERSON"
            else:
                self.id2label[idx] = "O"

        self.regex_patterns = self._build_regex_patterns()


    def _build_regex_patterns(self):
        return {
            "DATE": list(CALENDAR_DATE_PATTERNS),
            "MEDICAID_ID": [re.compile(r"\b[A-Z]{2}\d{6}\b")],
            "PHONE": [
                re.compile(r"\b\d{3}-\d{3}-\d{4}\b"),
                re.compile(r"\b\(\d{3}\)\s*\d{3}-\d{4}\b"),
            ],
            "ADDRESS": [
                re.compile(
                    r"\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+"
                    r"(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Court|Ct|Boulevard|Blvd)"
                    r",\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s+[A-Z]{2}\s+\d{5}"
                )
            ],
            "CREDENTIAL": list(CREDENTIAL_PATTERNS),
        }

    # ── BERT PERSON inference ────────────────────────────────────────────────

    def _predict_person_spans(self, text: str) -> list[dict]:
        """
        Run the fine-tuned model with a sliding window and return a list of
        PERSON entity dicts: {text, type, start, end}.
        """
        MAX_LENGTH = 512
        STRIDE     = 64
        torch = self._torch

        enc = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_LENGTH,
            stride=STRIDE,
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
            padding=True,
        )

        offset_mapping   = enc.pop("offset_mapping")
        overflow_mapping = enc.pop("overflow_to_sample_mapping")
        enc = {k: v.to(self.device) for k, v in enc.items()}

        with torch.no_grad():
            outputs = self.model(**enc)

        predictions = outputs.logits.argmax(dim=-1).cpu()

        # Aggregate per-character label decisions across all chunks.
        # Later chunks overwrite earlier ones only in the non-overlapping region
        # (stride), so the first chunk is authoritative for its stride-length
        # of tokens; subsequent chunks contribute only new tokens.
        char_label: dict[int, tuple[int, str]] = {}   # start → (end, label)

        for chunk_idx, offsets in enumerate(offset_mapping):
            pred_ids = predictions[chunk_idx]
            for tok_idx, (tok_start, tok_end) in enumerate(offsets.tolist()):
                if tok_start == tok_end:          # special token
                    continue
                label = self.id2label[pred_ids[tok_idx].item()]
                # Only write if not already filled (first-chunk priority in overlaps)
                if tok_start not in char_label:
                    char_label[tok_start] = (tok_end, label)

        # Convert token-level decisions to character-span entities.
        entities = []
        current: dict | None = None

        for tok_start in sorted(char_label):
            tok_end, label = char_label[tok_start]

            if label == "B-PERSON":
                if current:
                    entities.append(current)
                current = {"text": text[tok_start:tok_end], "type": "PERSON",
                           "start": tok_start, "end": tok_end}

            elif label == "I-PERSON" and current is not None:
                # Extend the current span (BERT tokenizer may add spaces via offsets)
                current["end"]  = tok_end
                current["text"] = text[current["start"]:tok_end]

            else:                                 # O tag
                if current:
                    entities.append(current)
                    current = None

        if current:
            entities.append(current)

        return entities

    # ── public detect() ──────────────────────────────────────────────────────

    def detect(self, text: str) -> list[dict]:
        entities: list[dict] = []

        # PERSON via BERT + post-processing
        raw_persons = self._predict_person_spans(text)
        entities.extend(apply_person_postprocessing(text, raw_persons))

        # Everything else via regex
        for entity_type, patterns in self.regex_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    entities.append({
                        "text":  match.group(),
                        "type":  entity_type,
                        "start": match.start(),
                        "end":   match.end(),
                    })

        return self._remove_overlaps(entities)

    def _remove_overlaps(self, entities: list[dict]) -> list[dict]:
        if not entities:
            return []
        entities = sorted(entities, key=lambda x: (x["start"], -(x["end"] - x["start"])))
        final, prev_end = [], -1
        for ent in entities:
            if ent["start"] >= prev_end:
                final.append(ent)
                prev_end = ent["end"]
        return final
