"""Regex patterns for PHI detection (DATE, PHONE, MEDICAID_ID, CREDENTIAL, ADDRESS)."""

import re

CALENDAR_DATE_PATTERNS = [
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b"),
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2}\b"),
    re.compile(r"\b\d{1,2}-\d{1,2}-\d{4}\b"),
    re.compile(r"\b\d{1,2}-\d{1,2}-\d{2}\b"),
    re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*\d{4}\b",
        re.IGNORECASE,
    ),
]

GROUND_TRUTH_ENTITY_TYPES = frozenset(
    {"PERSON", "DATE", "MEDICAID_ID", "PHONE", "ADDRESS", "CREDENTIAL"}
)

CREDENTIAL_PATTERNS = [
    # compound credentials (longest first)
    re.compile(r"\bBCBA,\s*LBA\b"),
    re.compile(r"\bPhD,\s*BCBA\b"),
    re.compile(r"\bMS\s+CCC-SLP\b"),
    re.compile(r"\bSr\.\s*BCBA\b"),
    # job titles used as credentials
    re.compile(r"\bBehavior Specialist\s+II\b"),
    re.compile(r"\bBehavior Specialist\s+I\b"),
    re.compile(r"\bBehavior Specialist\b"),
    re.compile(r"\bDirect Support Professional\b"),
    # degree abbreviations — no trailing \b after '.' (that \b is unreachable)
    re.compile(r"\bM\.A\."),
    re.compile(r"\bM\.Ed\."),
    re.compile(r"\bEd\.M\."),
    re.compile(r"\bM\.S\."),
    re.compile(r"\bPh\.D\."),
    re.compile(r"\bPsy\.D\."),
    # individual credential abbreviations
    re.compile(r"\bBCBA\b"),
    re.compile(r"\bCCC-SLP\b"),
    re.compile(r"\bOTR/L\b"),
    re.compile(r"\bLCSW\b"),
    re.compile(r"\bLMFT\b"),
    re.compile(r"\bLMHC\b"),
    re.compile(r"\bMSW\b"),
    re.compile(r"\bCASAC\b"),
    re.compile(r"\bCNS\b"),
    re.compile(r"\bBSN\b"),
    re.compile(r"\bLPN\b"),
    re.compile(r"\bRBT\b"),
    re.compile(r"\bRN\b"),
    re.compile(r"\bDSP\b"),
]

# ---------------------------------------------------------------------------
# PERSON post-processing — shared by both detectors
# ---------------------------------------------------------------------------

# Strings spaCy / Presidio NER frequently mis-tags as PERSON.
PERSON_BLOCKLIST = frozenset({
    # UCP residential program names
    "Geiger", "Geiger ICF",
    "88 Geiger ICF", "92 Geiger ICF", "95 Geiger ICF", "96 Geiger ICF", "100 Geiger ICF",
    # Day program names
    "Cicero TEC", "Chadwicks TEC", "Liverpool TEC", "Baldwinsville TEC", "Syracuse TEC",
    "Chadwicks", "Liverpool", "Cicero",
    # ABA / clinical terms
    "SKILL", "MAINTENANCE", "DESCRIPTION", "Psychiatrist", "Trigger", "Calmer",
    "Speech Therapy", "Vocational", "Vocational Training", "Start",
    # Medications
    "Sertraline", "Clonidine", "Risperidone",
    # Credential abbreviations NER tags as names
    "LMHC", "LCSW", "BCBA", "RBT",
    # Miscellaneous ambiguous short tokens
    "Ed", "Client",
})

# Regex that matches a title immediately before a person name.
_TITLE_PREFIX_RE = re.compile(r"\b(?:Dr|Ms|Mr|Mrs|Prof)\.\s*$")


def _normalize_person_span(text, start, end):
    """
    Trim noisy edge characters from a predicted PERSON span and validate shape.

    This removes markdown artifacts (e.g. '**'), leading/trailing whitespace,
    and punctuation-only boundaries while preserving internal punctuation used
    in names (period, comma, apostrophe, hyphen).
    """
    if start >= end:
        return None

    # Trim leading non-name characters
    while start < end and not text[start].isalnum():
        start += 1
    # Trim trailing non-name characters, keep period for initials/credentials
    while end > start and not (text[end - 1].isalnum() or text[end - 1] == "."):
        end -= 1

    if start >= end:
        return None

    span_text = text[start:end]
    if "\n" in span_text:
        return None
    if not any(ch.isalpha() for ch in span_text):
        return None

    # Guardrail for DeBERTa over-merged chunks: names in this dataset are short.
    token_count = len(span_text.split())
    if token_count == 0 or token_count > 4:
        return None
    raw_tokens = span_text.split()
    for token in raw_tokens:
        stripped = token.strip(".,")
        if not stripped:
            return None
        # Keep initials like "K." and titles like "Dr."
        if len(stripped) == 1 and stripped.isalpha() and stripped.isupper():
            continue
        if stripped.lower() in {"dr", "mr", "ms", "mrs", "prof"}:
            continue
        # Name-like tokens should begin uppercase and be alphabetic after
        # removing common punctuation separators.
        cleaned = stripped.replace("-", "").replace("'", "")
        if not cleaned.isalpha():
            return None
        if not cleaned[0].isupper():
            return None
        if cleaned.isupper() and len(cleaned) > 3:
            return None

    return {
        "text": span_text,
        "type": "PERSON",
        "start": start,
        "end": end,
    }


def apply_person_postprocessing(text, person_entities):
    """
    Apply three fixes to a list of raw PERSON entity dicts:
      1. Drop blocklisted strings.
      2. Extend span backward to include an immediately preceding title (Dr., Ms., …).
      3. Merge adjacent 'Last, First' pairs separated by ', '.

    Each entity dict must have keys: text, type, start, end.
    Returns a new list (original list is not mutated).
    """
    # 1. Normalize raw spans first (trim markdown/noise)
    normalized = []
    for ent in person_entities:
        cleaned = _normalize_person_span(text, ent["start"], ent["end"])
        if cleaned:
            normalized.append(cleaned)

    # 2. Blocklist filter
    filtered = [e for e in normalized if e["text"] not in PERSON_BLOCKLIST]

    # 3. Title prefix extension
    extended = []
    for ent in filtered:
        preceding = text[: ent["start"]]
        m = _TITLE_PREFIX_RE.search(preceding)
        if m:
            new_start = m.start()
            normalized = _normalize_person_span(text, new_start, ent["end"])
            if normalized:
                extended.append(normalized)
        else:
            normalized = _normalize_person_span(text, ent["start"], ent["end"])
            if normalized:
                extended.append(normalized)

    # 4. Last, First merge
    sorted_ents = sorted(extended, key=lambda e: e["start"])
    merged = []
    i = 0
    while i < len(sorted_ents):
        ent = sorted_ents[i]
        if i + 1 < len(sorted_ents):
            nxt = sorted_ents[i + 1]
            between = text[ent["end"]: nxt["start"]]
            if between == ", " and ent["type"] == "PERSON" and nxt["type"] == "PERSON":
                merged.append({
                    "text": text[ent["start"]: nxt["end"]],
                    "type": "PERSON",
                    "start": ent["start"],
                    "end": nxt["end"],
                })
                i += 2
                continue
        merged.append(ent)
        i += 1

    return merged


def extract_calendar_dates_in_span(text, span_start, span_end):
    """
    Find all calendar-date substrings inside text[span_start:span_end].

    Returns:
        list of dicts: text, start, end (absolute offsets in full text)
    """
    if span_start >= span_end:
        return []
    chunk = text[span_start:span_end]
    seen = set()
    found = []
    for pat in CALENDAR_DATE_PATTERNS:
        for m in pat.finditer(chunk):
            a = span_start + m.start()
            b = span_start + m.end()
            key = (a, b)
            if key in seen:
                continue
            seen.add(key)
            found.append({"text": text[a:b], "start": a, "end": b})
    if not found:
        return []
    found.sort(key=lambda x: (x["start"], -(x["end"] - x["start"])))
    merged = []
    prev_end = -1
    for ent in found:
        if ent["start"] >= prev_end:
            merged.append(ent)
            prev_end = ent["end"]
    return merged
