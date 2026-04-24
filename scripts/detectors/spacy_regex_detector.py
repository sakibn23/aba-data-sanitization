"""Hybrid PHI detector: spaCy NER (PERSON) plus project regex patterns."""

import re
import sys

import spacy

from .base_detector import PHIDetector
from .phi_patterns import (
    CALENDAR_DATE_PATTERNS,
    CREDENTIAL_PATTERNS,
    apply_person_postprocessing,
)


class SpacyRegexDetector(PHIDetector):
    """spaCy NER for persons; regex for dates, IDs, phones, addresses, credentials."""

    def __init__(self):
        print("Loading spaCy model...")
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("❌ spaCy model 'en_core_web_sm' not found!")
            print("   Install it with: python -m spacy download en_core_web_sm")
            sys.exit(1)

        self.regex_patterns = self._get_regex_patterns()

    def _get_regex_patterns(self):
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

    def detect(self, text):
        entities = []

        # spaCy PERSON extraction with shared post-processing
        doc = self.nlp(text)
        raw_persons = [
            {"text": ent.text, "type": "PERSON", "start": ent.start_char, "end": ent.end_char}
            for ent in doc.ents
            if ent.label_ == "PERSON"
        ]
        entities.extend(apply_person_postprocessing(text, raw_persons))

        # regex-based entity extraction
        for entity_type, patterns in self.regex_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    entities.append({
                        "text": match.group(),
                        "type": entity_type,
                        "start": match.start(),
                        "end": match.end(),
                    })

        return self._remove_overlaps(entities)

    def _remove_overlaps(self, entities):
        if not entities:
            return []
        entities = sorted(entities, key=lambda x: (x["start"], -(x["end"] - x["start"])))
        final = []
        prev_end = -1
        for ent in entities:
            if ent["start"] >= prev_end:
                final.append(ent)
                prev_end = ent["end"]
        return final
