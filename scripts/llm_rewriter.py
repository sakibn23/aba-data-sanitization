"""
LLM Rewriter for synthetic ABA session notes.   [OPTIONAL]

Rewrites the non-PHI portions of a note to sound like messier, real clinical
documentation while guaranteeing that PHI text and spans remain unchanged.

Strategy — mask / rewrite / unmask
------------------------------------
1. Replace every PHI span with a numbered placeholder  [PHI_0], [PHI_1], ...
2. Send the masked text to Claude with a prompt asking for a clinical rewrite
3. Find each placeholder in the rewritten text and restore the original PHI
4. Recompute entity spans from the restored positions

This approach means the LLM never sees PHI and cannot change it.

Requirements
------------
  pip install anthropic
  export ANTHROPIC_API_KEY="sk-ant-..."

Usage
-----
  from llm_rewriter import LLMRewriter
  rewriter = LLMRewriter()
  new_text, new_entities = rewriter.rewrite(text, entities)

  # or from CLI for a quick test:
  python scripts/llm_rewriter.py

NOTE: Each call costs API credits (~1-2K tokens per note). Use sparingly or
batch with --llm-rewrite on a sample of notes rather than the full dataset.
"""

import os
import re
import sys
from copy import deepcopy
from typing import List, Dict, Tuple

# ── placeholder pattern ───────────────────────────────────────────────────────
_PLACEHOLDER_RE = re.compile(r"\[PHI_(\d+)\]")

_REWRITE_PROMPT = """\
You are a clinical documentation assistant. Rewrite the session note below to \
sound like a real, slightly messy ABA therapy note written by a busy clinician.

Rules:
- Keep the exact meaning and all clinical facts
- Use common clinical abbreviations (pt, bx, sess, indep, w/, re:, etc.)
- Vary sentence structure — some short, some run-on
- Occasionally omit articles or conjunctions as real notes do
- DO NOT change, remove, or reorder any [PHI_N] placeholders — they must \
appear exactly as-is in your output
- DO NOT add new information or change clinical outcomes

Note to rewrite:
---
{masked_text}
---

Return only the rewritten note. No commentary."""


class LLMRewriter:
    """
    Rewrite ABA session notes via Claude API using mask/unmask to preserve PHI.

    Parameters
    ----------
    model   : Claude model ID (default: claude-haiku-4-5-20251001 for speed/cost)
    max_tokens : max tokens in LLM response
    """

    def __init__(
        self,
        model: str = "claude-haiku-4-5-20251001",
        max_tokens: int = 2048,
    ):
        try:
            import anthropic
        except ImportError:
            print("ERROR: anthropic package not installed.")
            print("  pip install anthropic")
            sys.exit(1)

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
            sys.exit(1)

        self._client    = anthropic.Anthropic(api_key=api_key)
        self._model     = model
        self._max_tokens = max_tokens

    # ── public API ────────────────────────────────────────────────────────────

    def rewrite(
        self,
        text: str,
        entities: List[Dict],
    ) -> Tuple[str, List[Dict]]:
        """
        Rewrite *text* using the LLM, preserving all PHI spans exactly.

        Returns (rewritten_text, updated_entities).
        Falls back to original (text, entities) if rewriting fails or
        placeholders are missing from the LLM output.
        """
        sorted_ents = sorted(entities, key=lambda e: e["start"])

        # 1. Mask
        masked, originals = self._mask(text, sorted_ents)

        # 2. Rewrite
        try:
            rewritten_masked = self._call_llm(masked)
        except Exception as exc:
            print(f"  [llm_rewriter] LLM call failed: {exc} — returning original")
            return text, deepcopy(entities)

        # 3. Unmask — if any placeholder is missing, fall back
        try:
            new_text, new_entities = self._unmask(rewritten_masked, originals, sorted_ents)
        except ValueError as exc:
            print(f"  [llm_rewriter] unmask failed: {exc} — returning original")
            return text, deepcopy(entities)

        return new_text, new_entities

    # ── mask / unmask ─────────────────────────────────────────────────────────

    @staticmethod
    def _mask(
        text: str,
        sorted_ents: List[Dict],
    ) -> Tuple[str, List[str]]:
        """
        Replace each PHI span with [PHI_N].
        Returns (masked_text, list_of_original_phi_strings).
        """
        parts    = []
        originals: List[str] = []
        prev_end = 0

        for i, ent in enumerate(sorted_ents):
            parts.append(text[prev_end:ent["start"]])
            parts.append(f"[PHI_{i}]")
            originals.append(ent["text"])
            prev_end = ent["end"]

        parts.append(text[prev_end:])
        return "".join(parts), originals

    @staticmethod
    def _unmask(
        masked_rewrite: str,
        originals: List[str],
        sorted_ents: List[Dict],
    ) -> Tuple[str, List[Dict]]:
        """
        Restore PHI placeholders in the LLM output and recompute entity spans.

        Raises ValueError if any placeholder is missing.
        """
        # Verify all placeholders are present
        found = set(int(m.group(1)) for m in _PLACEHOLDER_RE.finditer(masked_rewrite))
        expected = set(range(len(originals)))
        missing = expected - found
        if missing:
            raise ValueError(f"Placeholders missing from LLM output: {sorted(missing)}")

        # Replace placeholders with original PHI and record new spans
        new_entities: List[Dict] = [None] * len(sorted_ents)  # type: ignore[list-item]
        result = []
        prev_end = 0
        current_pos = 0

        for m in sorted(_PLACEHOLDER_RE.finditer(masked_rewrite), key=lambda x: x.start()):
            idx = int(m.group(1))
            phi_text = originals[idx]

            result.append(masked_rewrite[prev_end:m.start()])
            current_pos = len("".join(result))

            result.append(phi_text)
            new_start = current_pos
            new_end   = new_start + len(phi_text)

            ent_copy = deepcopy(sorted_ents[idx])
            ent_copy["start"] = new_start
            ent_copy["end"]   = new_end
            ent_copy["text"]  = phi_text
            new_entities[idx] = ent_copy

            prev_end = m.end()

        result.append(masked_rewrite[prev_end:])
        new_text = "".join(result)

        return new_text, new_entities

    # ── LLM call ─────────────────────────────────────────────────────────────

    def _call_llm(self, masked_text: str) -> str:
        prompt = _REWRITE_PROMPT.format(masked_text=masked_text)
        message = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()


# ── CLI self-test ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sample_text = (
        "Patient Emma Rodriguez, DOB 03/05/2015, attended the session today. "
        "Staff Joseph Rogers, BCBA, conducted the assessment. "
        "Parent contacted at 315-555-1234 regarding progress."
    )
    sample_entities = [
        {"text": "Emma Rodriguez", "type": "PERSON",      "start": 8,   "end": 22},
        {"text": "03/05/2015",     "type": "DATE",         "start": 29,  "end": 39},
        {"text": "Joseph Rogers",  "type": "PERSON",      "start": 57,  "end": 70},
        {"text": "BCBA",           "type": "CREDENTIAL",  "start": 72,  "end": 76},
        {"text": "315-555-1234",   "type": "PHONE",        "start": 110, "end": 122},
    ]

    rewriter = LLMRewriter()
    new_text, new_ents = rewriter.rewrite(sample_text, sample_entities)

    print("=== ORIGINAL ===")
    print(sample_text)
    print("\n=== REWRITTEN ===")
    print(new_text)
    print("\n=== ENTITIES (updated spans) ===")
    for e in new_ents:
        actual = new_text[e["start"]:e["end"]]
        ok = "OK" if actual == e["text"] else f"MISMATCH (got {actual!r})"
        print(f"  [{e['type']}] {e['text']!r}  [{e['start']}:{e['end']}]  {ok}")
