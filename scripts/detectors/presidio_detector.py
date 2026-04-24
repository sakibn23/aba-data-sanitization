"""
PHI detection using Microsoft Presidio AnalyzerEngine.

Only Presidio entity types that map to generator ground-truth labels are requested.
DATE_TIME is narrowed to calendar-style dates (same regex family as annotations); relative
phrases like "today", "24 hour", "48 hours" are dropped.

CREDENTIAL entities are not natively detected by Presidio, so they are added via
the shared regex patterns from phi_patterns after Presidio analysis.
PERSON entities receive the same post-processing (blocklist, title prefix, Last,First merge)
as the spacy_regex detector.
"""

from presidio_analyzer import AnalyzerEngine

from .base_detector import PHIDetector
from .phi_patterns import (
    extract_calendar_dates_in_span,
    GROUND_TRUTH_ENTITY_TYPES,
    CREDENTIAL_PATTERNS,
    apply_person_postprocessing,
)

# Presidio recognizers to run (subset — avoids EMAIL, URL, IP, SSN, etc.)
PRESIDIO_ENTITIES_REQUESTED = [
    "PERSON",
    "PHONE_NUMBER",
    "DATE_TIME",
    "LOCATION",
    "US_DRIVER_LICENSE",
]

# Map Presidio entity_type -> ground-truth label used in annotations_generated.json
PRESIDIO_TO_GROUND_TRUTH = {
    "PERSON": "PERSON",
    "PHONE_NUMBER": "PHONE",
    "DATE_TIME": "DATE",
    "LOCATION": "ADDRESS",
    "US_DRIVER_LICENSE": "MEDICAID_ID",
}


class PresidioDetector(PHIDetector):
    def __init__(self):
        print("Loading Presidio AnalyzerEngine...")
        self.analyzer = AnalyzerEngine()

    def detect(self, text):
        results = self.analyzer.analyze(
            text=text,
            language="en",
            entities=PRESIDIO_ENTITIES_REQUESTED,
        )

        raw_persons = []
        entities = []

        for res in results:
            gt_type = PRESIDIO_TO_GROUND_TRUTH.get(res.entity_type)
            if gt_type is None or gt_type not in GROUND_TRUTH_ENTITY_TYPES:
                continue

            if res.entity_type == "DATE_TIME":
                for sub in extract_calendar_dates_in_span(text, res.start, res.end):
                    entities.append({
                        "text": sub["text"],
                        "type": "DATE",
                        "start": sub["start"],
                        "end": sub["end"],
                        "score": res.score,
                        "source": "DATE_TIME",
                    })
                continue

            ent = {
                "text": text[res.start: res.end],
                "type": gt_type,
                "start": res.start,
                "end": res.end,
                "score": res.score,
            }

            if gt_type == "PERSON":
                raw_persons.append(ent)
            else:
                entities.append(ent)

        # Apply shared PERSON post-processing (blocklist, title prefix, Last,First merge)
        entities.extend(apply_person_postprocessing(text, raw_persons))

        # Add CREDENTIAL entities via regex (Presidio has no built-in credential recognizer)
        for pattern in CREDENTIAL_PATTERNS:
            for match in pattern.finditer(text):
                entities.append({
                    "text": match.group(),
                    "type": "CREDENTIAL",
                    "start": match.start(),
                    "end": match.end(),
                    "score": 1.0,
                    "source": "regex",
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
