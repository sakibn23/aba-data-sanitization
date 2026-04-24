"""
Ensemble PHI detector — combines spacy_regex, presidio, and a transformer NER model.

Strategy (per entity type):
  PERSON     → union of all sources, deduped by overlap removal.
               More detectors = higher recall; overlap removal keeps best span.
  DATE       → spacy_regex regex   (F1 ≈ 1.00 — no gain from others)
  MEDICAID_ID→ spacy_regex regex   (F1 = 1.00)
  PHONE      → spacy_regex regex   (F1 ≈ 1.00)
  CREDENTIAL → spacy_regex regex   (best F1 across detectors)
  ADDRESS    → spacy_regex regex   (Presidio LOCATION has F1 = 0.00 on this corpus)

Use --ensemble-model to select the transformer backend:
  bert    — fine-tuned BERT  (dslim/bert-base-NER)   [default]
  deberta — fine-tuned DeBERTa-v3
  both    — union of BERT + DeBERTa (maximum recall)

Usage:
    python scripts/run_phi_detection.py --detector ensemble
    python scripts/run_phi_detection.py --detector ensemble --ensemble-model deberta
    python scripts/run_phi_detection.py --detector ensemble --ensemble-model both
"""

import re
import sys

from .base_detector import PHIDetector
from .phi_patterns import (
    CALENDAR_DATE_PATTERNS,
    CREDENTIAL_PATTERNS,
    apply_person_postprocessing,
)


class EnsembleDetector(PHIDetector):
    """
    Combines spacy_regex, presidio, and one or both transformer NER models
    for maximum PERSON recall while keeping near-perfect precision on
    rule-based entity types.

    Args:
        transformer: "bert" | "deberta" | "both"  (default: "bert")
    """

    def __init__(self, transformer: str = "bert"):
        transformer = transformer.lower()
        if transformer not in ("bert", "deberta", "both"):
            raise ValueError(f"transformer must be 'bert', 'deberta', or 'both', got: {transformer!r}")
        self._transformer_choice = transformer

        # ── spaCy ─────────────────────────────────────────────────────────
        print("Ensemble: loading spaCy...")
        try:
            import spacy
            try:
                self._nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("  ERROR: spaCy model not found. Run: python -m spacy download en_core_web_sm")
                sys.exit(1)
        except ImportError:
            print("  ERROR: spaCy not installed: pip install spacy")
            sys.exit(1)

        # ── Presidio ──────────────────────────────────────────────────────
        print("Ensemble: loading Presidio...")
        try:
            from presidio_analyzer import AnalyzerEngine
            self._presidio = AnalyzerEngine()
        except ImportError:
            print("  WARNING: Presidio not installed — ensemble will skip Presidio PERSON.")
            self._presidio = None

        # ── Transformer NER models ─────────────────────────────────────────
        self._bert    = None
        self._deberta = None

        if transformer in ("bert", "both"):
            print("Ensemble: loading BERT NER...")
            try:
                from .bert_detector import BertDetector
                self._bert = BertDetector()
                print("  BERT loaded.")
            except Exception as e:
                print(f"  WARNING: Could not load BERT: {e}")

        if transformer in ("deberta", "both"):
            print("Ensemble: loading DeBERTa NER...")
            try:
                from .deberta_detector import DebertaDetector
                self._deberta = DebertaDetector()
                print("  DeBERTa loaded.")
            except Exception as e:
                print(f"  WARNING: Could not load DeBERTa: {e}")

        print(f"  Transformer(s) active: {transformer}")

        # ── shared regex patterns ─────────────────────────────────────────
        self._regex_patterns = self._build_regex_patterns()

    # ── regex patterns (all non-PERSON types) ────────────────────────────────

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

    # ── per-detector PERSON extraction ───────────────────────────────────────

    def _spacy_persons(self, text: str) -> list[dict]:
        doc = self._nlp(text)
        raw = [
            {"text": e.text, "type": "PERSON", "start": e.start_char, "end": e.end_char}
            for e in doc.ents if e.label_ == "PERSON"
        ]
        return apply_person_postprocessing(text, raw)

    def _presidio_persons(self, text: str) -> list[dict]:
        if self._presidio is None:
            return []
        results = self._presidio.analyze(text=text, language="en", entities=["PERSON"])
        raw = [
            {"text": text[r.start:r.end], "type": "PERSON",
             "start": r.start, "end": r.end, "score": r.score}
            for r in results
        ]
        return apply_person_postprocessing(text, raw)

    def _bert_persons(self, text: str) -> list[dict]:
        if self._bert is None:
            return []
        return [e for e in self._bert.detect(text) if e["type"] == "PERSON"]

    def _deberta_persons(self, text: str) -> list[dict]:
        if self._deberta is None:
            return []
        return [e for e in self._deberta.detect(text) if e["type"] == "PERSON"]

    # ── public detect() ───────────────────────────────────────────────────────

    def detect(self, text: str) -> list[dict]:
        entities: list[dict] = []

        # PERSON: union of all active sources
        all_persons = (
            self._spacy_persons(text)
            + self._presidio_persons(text)
            + self._bert_persons(text)
            + self._deberta_persons(text)
        )
        # Sort longest-first so overlap removal keeps the most complete span
        all_persons.sort(key=lambda e: (e["start"], -(e["end"] - e["start"])))
        entities.extend(self._remove_overlaps(all_persons))

        # Non-PERSON: reliable regex
        for entity_type, patterns in self._regex_patterns.items():
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
