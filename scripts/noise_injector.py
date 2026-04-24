"""Inject realistic clinical noise while preserving PHI entity spans."""

import random
import re
from copy import deepcopy
from typing import List, Dict, Tuple

# ── abbreviation table ────────────────────────────────────────────────────────
# Only safe non-PHI clinical abbreviations that preserve meaning.
_ABBREVS: List[Tuple[str, str]] = [
    (r"\bpatient\b",       "pt"),
    (r"\bassessment\b",    "asmt"),
    (r"\bbehavior\b",      "bx"),
    (r"\bbehaviors\b",     "bxs"),
    (r"\bwith\b",          "w/"),
    (r"\bwithout\b",       "w/o"),
    (r"\bregarding\b",     "re:"),
    (r"\bindependent\b",   "indep"),
    (r"\bindependently\b", "indep."),
    (r"\bapproximately\b", "approx"),
    (r"\bminutes\b",       "min"),
    (r"\bseconds\b",       "sec"),
    (r"\brecommendation\b","rec"),
    (r"\brecommendations\b","recs"),
    (r"\btherapist\b",     "tx"),
    (r"\btreatment\b",     "tx"),
    (r"\bintervention\b",  "intv"),
    (r"\bcommunication\b", "comm"),
    (r"\bfrequency\b",     "freq"),
    (r"\bduration\b",      "dur"),
    (r"\bsession\b",       "sess"),
    (r"\bfollowing\b",     "f/u"),
    (r"\boccupational\b",  "OT"),
    (r"\bphysical\b",      "PT"),
    (r"\bspeech\b",        "ST"),
    (r"\bgoal\b",          "gl"),
    (r"\binformation\b",   "info"),
]

# Pre-compile abbreviation patterns
_ABBREV_COMPILED = [
    (re.compile(pat, re.IGNORECASE), repl)
    for pat, repl in _ABBREVS
]

def _reformat_date(m: re.Match) -> str:
    """Return randomly chosen date format."""
    mo, d, y = int(m.group(1)), int(m.group(2)), m.group(3)
    yr4 = int(y) if len(y) == 4 else 2000 + int(y)
    yr2 = yr4 % 100
    original = m.group(0)
    options = [
        f"{mo}/{d}/{yr4}",                          # M/D/YYYY
        f"{mo:02d}/{d:02d}/{yr4}",                  # MM/DD/YYYY
        f"{mo}-{d}-{yr2:02d}",                      # M-D-YY
        f"{_MONTH_NAMES[mo-1]} {d}, {yr4}",         # Month D, YYYY
        f"{_MONTH_NAMES[mo-1][:3]} {d} {yr4}",      # Mon D YYYY
    ]
    choices = [o for o in options if o != original]
    return random.choice(choices) if choices else original

def _reformat_phone(m: re.Match) -> str:
    """Return randomly chosen phone format."""
    area, mid, last = m.group(1), m.group(2), m.group(3)
    original = m.group(0)
    options = [
        f"{area}-{mid}-{last}",          # 315-555-1234
        f"({area}){mid}-{last}",         # (315)555-1234
        f"({area}) {mid}-{last}",        # (315) 555-1234
        f"{area}.{mid}.{last}",          # 315.555.1234
        f"{area}{mid}{last}",            # 3155551234
    ]
    choices = [o for o in options if o != original]
    return random.choice(choices) if choices else original


# ── typo helpers ──────────────────────────────────────────────────────────────
def _maybe_typo(word: str, prob: float = 0.05) -> str:
    """Adjacent-letter swap with low probability. Only on alpha words ≥4 chars."""
    if random.random() > prob:
        return word
    if not word.isalpha() or len(word) < 4:
        return word
    # Pick a random interior position (not first or last)
    i = random.randint(1, len(word) - 2)
    lst = list(word)
    lst[i], lst[i + 1] = lst[i + 1], lst[i]
    return "".join(lst)


# ── punctuation helpers ───────────────────────────────────────────────────────
def _drop_punctuation(text: str, prob: float = 0.15) -> str:
    """Randomly drop commas and sentence-ending periods with given probability."""
    result = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "," and random.random() < prob:
            i += 1  # drop comma (and trailing space if any)
            continue
        if ch == "." and i + 1 < len(text) and text[i + 1] == "\n":
            # end-of-line period — occasionally drop
            if random.random() < prob / 2:
                i += 1
                continue
        result.append(ch)
        i += 1
    return "".join(result)

class NoiseInjector:
    """
    Inject realistic clinical-note noise while keeping PHI entity spans valid.

    Parameters
    ----------
    abbrev_prob   : probability of applying each abbreviation to any match  (0-1)
    typo_prob     : probability of a typo per eligible word                 (0-1)
    punct_prob    : probability of dropping a comma / sentence period       (0-1)
    phi_fmt_prob  : probability of reformatting a PHONE or DATE PHI span   (0-1)
    seed          : random seed for reproducibility (None = random)
    """

    def __init__(
        self,
        abbrev_prob:  float = 0.4,
        typo_prob:    float = 0.05,
        punct_prob:   float = 0.15,
        phi_fmt_prob: float = 0.6,
        seed: int | None = None,
    ):
        self.abbrev_prob  = abbrev_prob
        self.typo_prob    = typo_prob
        self.punct_prob   = punct_prob
        self.phi_fmt_prob = phi_fmt_prob
        if seed is not None:
            random.seed(seed)

    # ── public API ────────────────────────────────────────────────────────────

    def inject(
        self,
        text: str,
        entities: List[Dict],
    ) -> Tuple[str, List[Dict]]:
        """
        Apply noise to *text* and return (new_text, updated_entities).

        Entity spans in *entities* must be sorted and non-overlapping.
        The original list is not modified.
        """
        replacements: List[Tuple[int, int, str]] = []

        for ent in entities:
            new_phi = self._vary_phi_format(ent["text"], ent["type"])
            if new_phi != ent["text"]:
                replacements.append((ent["start"], ent["end"], new_phi))

        for reg_start, reg_end in self._non_phi_regions(text, entities):
            region = text[reg_start:reg_end]
            transformed = self._transform_region(region)
            if transformed != region:
                replacements.append((reg_start, reg_end, transformed))

        replacements = self._dedup(replacements)
        return self._apply(text, entities, replacements)

    # ── PHI format variation ──────────────────────────────────────────────────

    def _vary_phi_format(self, phi_text: str, phi_type: str) -> str:
        if random.random() > self.phi_fmt_prob:
            return phi_text

        if phi_type == "PHONE":
            m = _PHONE_RE.fullmatch(phi_text.strip())
            if m:
                return _reformat_phone(m)

        if phi_type == "DATE":
            m = _DATE_SLASHRE.fullmatch(phi_text.strip())
            if m:
                return _reformat_date(m)

        return phi_text

    # ── non-PHI region helpers ────────────────────────────────────────────────

    def _non_phi_regions(
        self,
        text: str,
        entities: List[Dict],
    ) -> List[Tuple[int, int]]:
        """Return character spans of text that are NOT covered by any entity."""
        regions = []
        prev_end = 0
        for ent in sorted(entities, key=lambda e: e["start"]):
            if ent["start"] > prev_end:
                regions.append((prev_end, ent["start"]))
            prev_end = max(prev_end, ent["end"])
        if prev_end < len(text):
            regions.append((prev_end, len(text)))
        return regions

    def _transform_region(self, text: str) -> str:
        """Apply abbreviations, typos, and punctuation noise to a non-PHI region."""
        text = self._apply_abbrevs(text)
        text = self._apply_typos(text)
        text = _drop_punctuation(text, self.punct_prob)
        return text

    def _apply_abbrevs(self, text: str) -> str:
        for pattern, repl in _ABBREV_COMPILED:
            if random.random() < self.abbrev_prob:
                text = pattern.sub(repl, text, count=1)
        return text

    def _apply_typos(self, text: str) -> str:
        tokens = text.split(" ")
        return " ".join(_maybe_typo(t, self.typo_prob) for t in tokens)

    # ── replacement application ───────────────────────────────────────────────

    @staticmethod
    def _dedup(
        replacements: List[Tuple[int, int, str]],
    ) -> List[Tuple[int, int, str]]:
        """Remove overlapping replacements, keeping first by start position."""
        replacements = sorted(replacements, key=lambda r: r[0])
        out, prev_end = [], -1
        for r in replacements:
            if r[0] >= prev_end:
                out.append(r)
                prev_end = r[1]
        return out

    @staticmethod
    def _build_position_map(
        orig_len: int,
        replacements: List[Tuple[int, int, str]],
    ) -> Dict[int, int]:
        """
        Map every original character position (0..orig_len inclusive) to its
        corresponding position in the new text after all replacements are applied.
        """
        pos_map: Dict[int, int] = {}
        offset = 0
        prev_end = 0

        for rs, re_, new_text in replacements:
            # Unchanged region before this replacement
            for i in range(prev_end, rs + 1):
                pos_map[i] = i + offset

            delta = len(new_text) - (re_ - rs)
            # End of replacement region maps to its new position
            pos_map[re_] = re_ + offset + delta

            offset += delta
            prev_end = re_

        # Positions after the last replacement
        for i in range(prev_end, orig_len + 1):
            pos_map[i] = i + offset

        return pos_map

    def _apply(
        self,
        text: str,
        entities: List[Dict],
        replacements: List[Tuple[int, int, str]],
    ) -> Tuple[str, List[Dict]]:
        """Build new text and recompute all entity spans via the position map."""
        if not replacements:
            return text, deepcopy(entities)

        # Build new text
        parts, prev_end = [], 0
        for rs, re_, new_text in replacements:
            parts.append(text[prev_end:rs])
            parts.append(new_text)
            prev_end = re_
        parts.append(text[prev_end:])
        new_text = "".join(parts)

        # Build position map and update entities
        pos_map = self._build_position_map(len(text), replacements)

        new_entities = []
        for ent in entities:
            e = deepcopy(ent)
            e["start"] = pos_map[ent["start"]]
            e["end"]   = pos_map[ent["end"]]
            e["text"]  = new_text[e["start"]:e["end"]]
            new_entities.append(e)

        return new_text, new_entities


# ── CLI self-test ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sample_text = (
        "Patient Emma Rodriguez, DOB 03/05/2015, was assessed today. "
        "Session conducted with the patient at 315-555-1234. "
        "Independent behavior observed following intervention."
    )
    sample_entities = [
        {"text": "Emma Rodriguez", "type": "PERSON",  "start": 8,  "end": 22},
        {"text": "03/05/2015",     "type": "DATE",    "start": 29, "end": 39},
        {"text": "315-555-1234",   "type": "PHONE",   "start": 72, "end": 84},
    ]

    inj = NoiseInjector(seed=42)
    new_text, new_ents = inj.inject(sample_text, sample_entities)

    print("=== ORIGINAL ===")
    print(sample_text)
    print("\n=== NOISY ===")
    print(new_text)
    print("\n=== ENTITIES (updated spans) ===")
    for e in new_ents:
        actual = new_text[e["start"]:e["end"]]
        ok = "OK" if actual == e["text"] else f"MISMATCH (got {actual!r})"
        print(f"  [{e['type']}] {e['text']!r}  span [{e['start']}:{e['end']}]  {ok}")
