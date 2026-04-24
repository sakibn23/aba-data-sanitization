import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np


# ── helpers ───────────────────────────────────────────────────────────────────

def _load_sanitized(method: str, sanitized_dir: str) -> list[dict]:
    path = Path(sanitized_dir) / method / f"{method}_sanitized.json"
    if not path.exists():
        print(f"  ERROR: {path} not found.")
        print("  Run sanitization first: python scripts/run_sanitization_complete.py")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_detected_entities(detected_path: str) -> dict[int, list]:
    """Return {doc_id: [entity, ...]} from a detected_entities JSON."""
    if not os.path.exists(detected_path):
        return {}
    with open(detected_path, encoding="utf-8") as f:
        data = json.load(f)
    return {doc["id"]: doc["entities"] for doc in data}


# ── metric 1: PHI removal rate ────────────────────────────────────────────────

def compute_phi_reduction(docs: list[dict]) -> dict:
    """
    Aggregate PHI removal rate across all documents.

    Each doc already has 'phi_removal_rate' (fraction of detected entities
    removed).  This function returns mean, min, max, and the count of docs
    where ALL phi was removed (rate == 1.0).
    """
    rates = [d.get("phi_removal_rate", 0.0) for d in docs]
    if not rates:
        return {}
    return {
        "mean":          round(float(np.mean(rates)), 4),
        "min":           round(float(np.min(rates)),  4),
        "max":           round(float(np.max(rates)),  4),
        "fully_removed": int(sum(1 for r in rates if r >= 1.0)),
        "total_docs":    len(rates),
        "pct_fully_removed": round(sum(1 for r in rates if r >= 1.0) / len(rates) * 100, 2),
    }


# ── metric 2: semantic similarity ─────────────────────────────────────────────

def compute_similarity(docs: list[dict], batch_size: int = 64) -> dict:
    """
    Cosine similarity between sentence embeddings of original vs sanitized text.
    Uses sentence-transformers all-MiniLM-L6-v2 (fast, lightweight).

    Higher similarity = more clinical utility preserved.
    Target: > 0.85 (keeps clinical meaning while removing PHI).
    """
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        print("  WARNING: sentence-transformers not installed.")
        print("           pip install sentence-transformers")
        print("           Skipping semantic similarity.")
        return {}

    print("  Loading sentence-transformer model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    orig_texts = [d["original_text"] for d in docs]
    san_texts  = [d["sanitized_text"] for d in docs]

    print(f"  Encoding {len(docs)} document pairs in batches of {batch_size}...")
    orig_emb = model.encode(orig_texts, batch_size=batch_size, show_progress_bar=False)
    san_emb  = model.encode(san_texts,  batch_size=batch_size, show_progress_bar=False)

    scores = [
        float(cosine_similarity([o], [s])[0][0])
        for o, s in zip(orig_emb, san_emb)
    ]

    return {
        "mean":   round(float(np.mean(scores)),   4),
        "min":    round(float(np.min(scores)),    4),
        "max":    round(float(np.max(scores)),    4),
        "std":    round(float(np.std(scores)),    4),
        "pct_above_0.85": round(sum(1 for s in scores if s > 0.85) / len(scores) * 100, 2),
    }


# ── metric 3: linkage resistance ─────────────────────────────────────────────

def compute_linkage_resistance(docs: list[dict],
                                detected_map: dict[int, list]) -> dict:
    """
    For each doc, collect the text of all PHI entities detected in the original.
    Check how many of those tokens appear verbatim in the sanitized text.

    linkage_resistance = fraction of docs where ZERO original PHI tokens survive.
    Higher is better (more resistant to re-identification).
    """
    fully_resistant = 0
    partial_leak    = 0
    full_leak       = 0
    total           = 0

    for doc in docs:
        doc_id   = doc["id"]
        san_text = doc["sanitized_text"]
        entities = detected_map.get(doc_id, [])

        if not entities:
            fully_resistant += 1
            total += 1
            continue

        phi_tokens = [e["text"].strip() for e in entities if len(e["text"].strip()) > 2]
        if not phi_tokens:
            fully_resistant += 1
            total += 1
            continue

        leaked = [tok for tok in phi_tokens if tok in san_text]

        if not leaked:
            fully_resistant += 1
        elif len(leaked) < len(phi_tokens):
            partial_leak += 1
        else:
            full_leak += 1

        total += 1

    if total == 0:
        return {}

    return {
        "fully_resistant_pct": round(fully_resistant / total * 100, 2),
        "partial_leak_pct":    round(partial_leak    / total * 100, 2),
        "full_leak_pct":       round(full_leak       / total * 100, 2),
        "total_docs":          total,
    }


# ── metric 4: multi-system linkage (hash/hybrid only) ────────────────────────

def compute_multisystem_linkage(docs: list[dict]) -> dict:
    """
    Hash method replaces each PHI with a deterministic 8-char hex hash (sha256[:8]).
    The same person name always produces the same hash, so records CAN be
    re-linked across documents intentionally (pseudonymisation, not anonymisation).

    Counts how many unique hashes appear in more than one document.
    """
    import re
    # HASH method produces plain 8-char lowercase hex strings via sha256[:8]
    hash_pattern = re.compile(r"\b[0-9a-f]{8}\b")

    token_to_docs: dict[str, set] = {}
    for doc in docs:
        found = set(hash_pattern.findall(doc["sanitized_text"]))
        for tok in found:
            token_to_docs.setdefault(tok, set()).add(doc["id"])

    linkable = {tok: docs for tok, docs in token_to_docs.items() if len(docs) > 1}

    return {
        "unique_hashed_persons":  len(token_to_docs),
        "cross_doc_linkable":     len(linkable),
        "linkage_possible":       len(linkable) > 0,
        "note": (
            "cross_doc_linkable > 0 means the same pseudonym appears in multiple "
            "documents — intentional for record linkage while preserving privacy."
        ),
    }


# ── main report ───────────────────────────────────────────────────────────────

def run_privacy_metrics(
    methods: list[str],
    sanitized_dir: str = "outputs/sanitized",
    detected_path: str = "outputs/detected_entities.json",
    output_path:   str = "outputs/privacy_metrics.json",
    skip_similarity: bool = False,
) -> dict:

    detected_map = _load_detected_entities(detected_path)
    if not detected_map:
        print(f"  WARNING: No detected entities found at {detected_path}.")
        print("  Linkage resistance will be skipped.")

    all_results = {}

    for method in methods:
        print(f"\n{'='*70}")
        print(f"  Method: {method.upper()}")
        print(f"{'='*70}")

        docs = _load_sanitized(method, sanitized_dir)
        print(f"  Loaded {len(docs)} documents")

        result = {"method": method, "n_docs": len(docs)}

        # 1. PHI removal rate
        print("  Computing PHI removal rate...")
        result["phi_removal"] = compute_phi_reduction(docs)

        # 2. Semantic similarity
        if skip_similarity:
            print("  Skipping semantic similarity (--no-similarity)")
        else:
            print("  Computing semantic similarity...")
            result["semantic_similarity"] = compute_similarity(docs)

        # 3. Linkage resistance
        if detected_map:
            print("  Computing linkage resistance...")
            result["linkage_resistance"] = compute_linkage_resistance(docs, detected_map)
        else:
            result["linkage_resistance"] = {}

        # 4. Multi-system linkage (hash / hybrid only)
        if method in ("hash", "hybrid"):
            print("  Computing multi-system linkage (hash consistency)...")
            result["multisystem_linkage"] = compute_multisystem_linkage(docs)

        all_results[method] = result

    # ── summary table ────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("PRIVACY METRICS SUMMARY")
    print(f"{'='*70}")
    print(
        f"\n  {'Method':<10} {'Mean Removal%':>14} {'All Removed%':>13} "
        f"{'Semantic Sim':>13} {'Fully Resist%':>14} {'Partial Leak%':>14}"
    )
    print(f"  {'-'*80}")
    for m, r in all_results.items():
        phi_mean = r["phi_removal"].get("mean",              "N/A")
        phi_pct  = r["phi_removal"].get("pct_fully_removed", "N/A")
        sim_mean = r.get("semantic_similarity", {}).get("mean", "N/A")
        resist   = r["linkage_resistance"].get("fully_resistant_pct", "N/A")
        partial  = r["linkage_resistance"].get("partial_leak_pct",    "N/A")
        mean_str = f"{phi_mean*100:>7.2f}%" if isinstance(phi_mean, float) else phi_mean
        pct_str  = f"{phi_pct:>6.2f}%"     if isinstance(phi_pct,  float) else phi_pct
        sim_str  = f"{sim_mean:.4f}"        if isinstance(sim_mean, float) else sim_mean
        res_str  = f"{resist:>6.2f}%"       if isinstance(resist,   float) else resist
        par_str  = f"{partial:>6.2f}%"      if isinstance(partial,  float) else partial
        print(f"  {m.upper():<10} {mean_str:>14} {pct_str:>13} {sim_str:>13} {res_str:>14} {par_str:>14}")

    print(f"\n  Mean Removal% : avg fraction of detected PHI tokens removed per doc (primary metric)")
    print(f"  All Removed%  : % of docs where EVERY detected entity text was removed (strict)")
    print(f"  Semantic Sim  : cosine similarity of text embeddings (1.0 = identical meaning)")
    print(f"  Fully Resist% : % of docs with zero detected PHI surviving verbatim")
    print(f"  Partial Leak% : % of docs where SOME detected PHI tokens still visible")
    print(f"\n  NOTE: 'All Removed%' / 'Partial Leak%' are strict — they flag docs where")
    print(f"  a name appears in the body but was not re-detected there (NER recall < 1.0).")
    print(f"  HYBRID 'All Removed%'=0 is expected: credentials are intentionally preserved.\n")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"  Results saved to: {output_path}")
    print(f"\n{'='*70}\n")

    return all_results


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Privacy metrics for sanitized ABA session notes."
    )
    parser.add_argument(
        "--method",
        choices=["replace", "mask", "hash", "hybrid"],
        default=None,
        help="Single sanitization method to evaluate (default: all methods)",
    )
    parser.add_argument(
        "--methods",
        nargs="+",
        choices=["replace", "mask", "hash", "hybrid"],
        default=["replace", "mask", "hash", "hybrid"],
        help="Methods to evaluate (used when --method is not set)",
    )
    parser.add_argument(
        "--sanitized-dir",
        default="outputs/sanitized",
    )
    parser.add_argument(
        "--detected",
        default="outputs/detected_entities.json",
        help="Path to detected_entities.json for linkage resistance",
    )
    parser.add_argument(
        "--output",
        default="outputs/privacy_metrics.json",
    )
    parser.add_argument(
        "--no-similarity",
        action="store_true",
        help="Skip slow sentence-transformer similarity step",
    )
    args = parser.parse_args()

    methods = [args.method] if args.method else args.methods

    run_privacy_metrics(
        methods=methods,
        sanitized_dir=args.sanitized_dir,
        detected_path=args.detected,
        output_path=args.output,
        skip_similarity=args.no_similarity,
    )


if __name__ == "__main__":
    main()
