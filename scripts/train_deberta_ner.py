"""
Fine-tune microsoft/deberta-v3-base on PERSON entities from the synthetic ABA notes.

DeBERTa (Decoding-enhanced BERT with Disentangled Attention) is Microsoft's
improved BERT architecture that uses disentangled attention on content and
position embeddings separately, typically outperforming BERT on NER tasks.

Only PERSON is trained — DATE / PHONE / MEDICAID_ID / CREDENTIAL / ADDRESS are
handled by the shared regex patterns in phi_patterns.py, where they are already
near-perfect (F1 ≥ 0.94).

Output: scripts/detectors/deberta_ner_model/   (saved tokenizer + model weights)

Requirements:
    pip install sentencepiece  (needed for DeBERTa's SentencePiece tokenizer)

Usage:
    python scripts/train_deberta_ner.py
    python scripts/train_deberta_ner.py --epochs 5 --batch-size 8 --output-dir scripts/detectors/deberta_ner_model
"""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

# ── ensure scripts/ is importable ──────────────────────────────────────────
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPTS_DIR)

try:
    import torch
    from datasets import Dataset
    from transformers import (
        AutoModelForTokenClassification,
        AutoTokenizer,
        DataCollatorForTokenClassification,
        Trainer,
        TrainingArguments,
        set_seed,
    )
    from seqeval.metrics import classification_report, f1_score
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("   Install with: pip install torch transformers datasets seqeval accelerate sentencepiece")
    sys.exit(1)

# ── constants ───────────────────────────────────────────────────────────────
BASE_MODEL   = "microsoft/deberta-v3-base"   # DeBERTa-v3 base model
LABEL2ID     = {"O": 0, "B-PERSON": 1, "I-PERSON": 2}
ID2LABEL     = {v: k for k, v in LABEL2ID.items()}
MAX_LENGTH   = 512
STRIDE       = 64
IGNORE_INDEX = -100


# ── data helpers ────────────────────────────────────────────────────────────

def load_examples(notes_dir: str, annotations_path: str):
    """Return list of {text, person_spans} dicts (one per note)."""
    with open(annotations_path, encoding="utf-8") as f:
        annotations = json.load(f)

    ann_map = {doc["doc_id"]: doc["entities"] for doc in annotations}
    note_files = sorted(Path(notes_dir).glob("*.txt"))

    examples = []
    for idx, nf in enumerate(note_files, start=1):
        text = nf.read_text(encoding="utf-8")
        person_spans = [
            (e["start"], e["end"])
            for e in ann_map.get(idx, [])
            if e["type"] == "PERSON"
        ]
        examples.append({"text": text, "person_spans": person_spans})

    return examples


def _align_labels(offsets, person_spans):
    """Map token offsets to BIO label ids. Special tokens → IGNORE_INDEX."""
    labels = []
    prev_in_person = False

    for tok_start, tok_end in offsets:
        if tok_start == tok_end:          # special / padding token
            labels.append(IGNORE_INDEX)
            prev_in_person = False
            continue

        # Offset-based overlap check (more robust than full containment for subwords)
        in_person = any((tok_start < pe) and (tok_end > ps) for ps, pe in person_spans)
        if in_person:
            # Begin if we just entered a PERSON span, or if a span boundary starts inside this token.
            is_begin = (not prev_in_person) or any((ps >= tok_start) and (ps < tok_end) for ps, _ in person_spans)
            labels.append(LABEL2ID["B-PERSON"] if is_begin else LABEL2ID["I-PERSON"])
        else:
            labels.append(LABEL2ID["O"])

        prev_in_person = in_person

    return labels


def tokenize_dataset(examples, tokenizer):
    """
    Tokenize with sliding-window chunking and align BIO labels.
    Returns a flat list of {input_ids, attention_mask, labels} dicts.

    Note: DeBERTa-v3's fast tokenizer (DebertaV2TokenizerFast) supports
    return_offsets_mapping. If only the slow tokenizer is available,
    install sentencepiece: pip install sentencepiece
    """
    all_samples = []

    for ex in examples:
        enc = tokenizer(
            ex["text"],
            truncation=True,
            max_length=MAX_LENGTH,
            stride=STRIDE,
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
            padding=False,
        )

        for chunk_idx in range(len(enc["input_ids"])):
            offsets = enc["offset_mapping"][chunk_idx]
            labels  = _align_labels(offsets, ex["person_spans"])

            all_samples.append({
                "input_ids":      enc["input_ids"][chunk_idx],
                "attention_mask": enc["attention_mask"][chunk_idx],
                "labels":         labels,
            })

    return all_samples


# ── metrics ─────────────────────────────────────────────────────────────────

def compute_metrics(eval_pred):
    logits, label_ids = eval_pred
    predictions = np.argmax(logits, axis=-1)

    true_labels, pred_labels = [], []
    for pred_seq, label_seq in zip(predictions, label_ids):
        true_row, pred_row = [], []
        for p, l in zip(pred_seq, label_seq):
            if l == IGNORE_INDEX:
                continue
            true_row.append(ID2LABEL[l])
            pred_row.append(ID2LABEL[p])
        true_labels.append(true_row)
        pred_labels.append(pred_row)

    return {"f1": f1_score(true_labels, pred_labels)}


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Fine-tune DeBERTa NER for PERSON detection.")
    parser.add_argument("--notes-dir",       default="data/synthetic/raw")
    parser.add_argument("--annotations",     default="data/annotated/annotations_generated.json")
    parser.add_argument("--output-dir",      default="scripts/detectors/deberta_ner_model")
    parser.add_argument("--epochs",          type=int,   default=4)
    parser.add_argument("--batch-size",      type=int,   default=8)
    parser.add_argument("--learning-rate",   type=float, default=1e-5,
                        help="DeBERTa typically benefits from a lower LR than BERT (default: 1e-5)")
    parser.add_argument("--val-split",       type=float, default=0.1,
                        help="Fraction of notes held out for validation")
    parser.add_argument("--seed",            type=int,   default=42)
    args = parser.parse_args()

    set_seed(args.seed)

    print(f"\n{'='*80}")
    print("DeBERTa NER FINE-TUNING  —  PERSON entity detection")
    print(f"{'='*80}\n")
    print(f"  Base model  : {BASE_MODEL}")
    print(f"  Notes dir   : {args.notes_dir}")
    print(f"  Annotations : {args.annotations}")
    print(f"  Output dir  : {args.output_dir}")
    print(f"  Epochs      : {args.epochs}")
    print(f"  Batch size  : {args.batch_size}")
    print(f"  LR          : {args.learning_rate}\n")

    # ── load data ───────────────────────────────────────────────────────────
    print("Loading notes and annotations...")
    examples = load_examples(args.notes_dir, args.annotations)
    print(f"  {len(examples)} notes loaded")

    # train / val split
    rng = np.random.default_rng(args.seed)
    indices = rng.permutation(len(examples))
    val_size  = max(1, int(len(examples) * args.val_split))
    val_idx   = set(indices[:val_size].tolist())
    train_ex  = [ex for i, ex in enumerate(examples) if i not in val_idx]
    val_ex    = [ex for i, ex in enumerate(examples) if i in val_idx]
    print(f"  Train: {len(train_ex)}   Val: {len(val_ex)}\n")

    # ── tokenizer ───────────────────────────────────────────────────────────
    print(f"Loading tokenizer from {BASE_MODEL}...")
    print("  (requires sentencepiece — pip install sentencepiece if not installed)")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    print("Tokenizing training data...")
    train_samples = tokenize_dataset(train_ex, tokenizer)
    val_samples   = tokenize_dataset(val_ex,   tokenizer)
    print(f"  Train chunks: {len(train_samples)}   Val chunks: {len(val_samples)}\n")

    train_dataset = Dataset.from_list(train_samples)
    val_dataset   = Dataset.from_list(val_samples)

    # ── model ────────────────────────────────────────────────────────────────
    print(f"Loading model from {BASE_MODEL}...")
    model = AutoModelForTokenClassification.from_pretrained(
        BASE_MODEL,
        num_labels=len(LABEL2ID),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        ignore_mismatched_sizes=True,
    )

    data_collator = DataCollatorForTokenClassification(tokenizer, pad_to_multiple_of=8)

    # warmup_steps: ~10% of total training steps
    steps_per_epoch = max(1, len(train_dataset) // args.batch_size)
    warmup_steps    = max(1, int(steps_per_epoch * args.epochs * 0.1))

    # ── training ─────────────────────────────────────────────────────────────
    # DeBERTa-v3 does not support fp16 on all hardware due to its disentangled
    # attention; use bf16 if available (Ampere+ GPU), otherwise fp32.
    use_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    use_fp16 = torch.cuda.is_available() and not use_bf16

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size * 2,
        learning_rate=args.learning_rate,
        weight_decay=0.01,
        warmup_steps=warmup_steps,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_steps=50,
        fp16=use_fp16,
        bf16=use_bf16,
        seed=args.seed,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    print(f"  Mixed precision: {'bf16' if use_bf16 else 'fp16' if use_fp16 else 'fp32'}")
    print("Starting training...\n")
    trainer.train()

    # ── save ─────────────────────────────────────────────────────────────────
    print(f"\nSaving model to {args.output_dir} ...")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    # save label map so deberta_detector can load it without the base model
    label_map_path = Path(args.output_dir) / "label_map.json"
    with open(label_map_path, "w") as f:
        json.dump({"label2id": LABEL2ID, "id2label": ID2LABEL}, f, indent=2)

    print(f"\n{'='*80}")
    print("Training complete!")
    print(f"{'='*80}")
    print(f"\nModel saved to: {args.output_dir}")
    print("\nNext step:")
    print("  python scripts/run_phi_detection.py --detector deberta")
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
