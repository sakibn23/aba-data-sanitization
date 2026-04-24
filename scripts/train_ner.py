
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

try:
    _SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # __file__ is not defined (e.g., Colab)
    _SCRIPTS_DIR = os.getcwd()

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
sys.path.insert(0, _SCRIPTS_DIR)

try:
    import torch
    import torch.nn as nn
    from datasets import Dataset
    from transformers import (
        AutoConfig,
        AutoModelForTokenClassification,
        AutoTokenizer,
        DataCollatorForTokenClassification,
        EarlyStoppingCallback,
        Trainer,
        TrainerCallback,
        TrainingArguments,
        set_seed,
    )
    from seqeval.metrics import f1_score
except ImportError as e:
    print(f" Missing dependency: {e}")
    print("   pip install torch transformers datasets seqeval accelerate sentencepiece")
    sys.exit(1)


# ── NaN / loss-explosion guard ───────────────────────────────────────────────

class NaNStoppingCallback(TrainerCallback):
    """
    Stop training immediately if loss becomes NaN/Inf or spikes more than
    spike_factor× the previous epoch's loss.  Catches DeBERTa fp16/instability
    failures early rather than wasting epochs on broken gradients.
    """

    def __init__(self, spike_factor: float = 5.0):
        self._spike_factor = spike_factor
        self._prev_loss: float | None = None

    def on_log(self, args, state, control, logs=None, **kwargs):
        loss = (logs or {}).get("loss")
        if loss is None:
            return
        import math
        if math.isnan(loss) or math.isinf(loss):
            print(f"\n[NaNStopping] Loss is {loss} at step {state.global_step} — stopping training.")
            control.should_training_stop = True
            return
        if self._prev_loss is not None and loss > self._spike_factor * self._prev_loss:
            print(
                f"\n[NaNStopping] Loss spiked {loss:.4f} > {self._spike_factor}× "
                f"prev {self._prev_loss:.4f} at step {state.global_step} — stopping training."
            )
            control.should_training_stop = True
        self._prev_loss = loss


# ── class-weighted trainer ────────────────────────────────────────────────────

class WeightedCETrainer(Trainer):
    """
    Custom Trainer that applies class-weighted CrossEntropyLoss.

    DeBERTa starts with a randomly initialised classifier head (unlike BERT's
    dslim/bert-base-NER which already knows about PERSON).  With ~95 % O tokens
    the model collapses to predicting all-O and never learns PERSON.
    Upweighting B-PERSON / I-PERSON forces the model to pay attention to the
    minority class.

    Weights: O = 1.0,  B-PERSON = 15.0,  I-PERSON = 15.0
    """

    def __init__(self, class_weights=None, **kwargs):
        super().__init__(**kwargs)
        self._class_weights = class_weights or [1.0, 15.0, 15.0]

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        # Run model without labels so it doesn't compute its own unweighted loss
        model_inputs = {k: v for k, v in inputs.items() if k != "labels"}
        outputs = model(**model_inputs)
        logits  = outputs.logits

        weights  = torch.tensor(self._class_weights, dtype=logits.dtype, device=logits.device)
        loss_fct = nn.CrossEntropyLoss(weight=weights, ignore_index=IGNORE_INDEX)
        loss     = loss_fct(
            logits.view(-1, model.config.num_labels),
            labels.view(-1),
        )
        return (loss, outputs) if return_outputs else loss


# ── DeBERTa-v3 LayerNorm compatibility fix ────────────────────────────────────

def fix_deberta_layernorm(model):
    """
    DeBERTa-v3 checkpoints saved with older transformers used 'gamma'/'beta'
    for LayerNorm parameters; newer transformers expects 'weight'/'bias'.
    When names don't match, all LayerNorm weights are randomly re-initialised,
    hurting training stability.  This copies gamma->weight, beta->bias in-place.
    """
    fixed = 0
    for module in model.modules():
        if hasattr(module, "gamma") and isinstance(module.gamma, torch.nn.Parameter):
            if not (hasattr(module, "weight") and isinstance(getattr(module, "weight"), torch.nn.Parameter)):
                module.weight = module.gamma
            else:
                module.weight.data.copy_(module.gamma.data)
            fixed += 1
        if hasattr(module, "beta") and isinstance(module.beta, torch.nn.Parameter):
            if not (hasattr(module, "bias") and isinstance(getattr(module, "bias"), torch.nn.Parameter)):
                module.bias = module.beta
            else:
                module.bias.data.copy_(module.beta.data)
            fixed += 1
    if fixed:
        print(f"  Fixed {fixed} gamma/beta -> weight/bias LayerNorm params")


def _load_deberta_checkpoint_with_key_remap(base_model: str):
    """
    Build a token-classification DeBERTa model and load base encoder weights,
    remapping LayerNorm keys from gamma/beta -> weight/bias when needed.

    This avoids the common v3 checkpoint/key-format mismatch where most
    LayerNorm weights are otherwise dropped as "unexpected".
    """
    try:
        from huggingface_hub import hf_hub_download
    except Exception:
        hf_hub_download = None

    # 1) init architecture with our downstream label space
    config = AutoConfig.from_pretrained(
        base_model,
        num_labels=len(LABEL2ID),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    model = AutoModelForTokenClassification.from_config(config)

    # 2) fetch raw checkpoint state dict
    state_dict = None
    last_err = None

    if hf_hub_download is not None:
        # Prefer safetensors, then fallback to pytorch_model.bin
        for ckpt_name in ("model.safetensors", "pytorch_model.bin"):
            try:
                ckpt_path = hf_hub_download(repo_id=base_model, filename=ckpt_name)
                if ckpt_name.endswith(".safetensors"):
                    from safetensors.torch import load_file as safe_load_file
                    state_dict = safe_load_file(ckpt_path)
                else:
                    state_dict = torch.load(ckpt_path, map_location="cpu")
                break
            except Exception as e:
                last_err = e

    if state_dict is None:
        # Fallback: let transformers load however it can.
        print("  Warning: custom DeBERTa checkpoint loader unavailable; using from_pretrained fallback.")
        if last_err:
            print(f"  Loader detail: {last_err}")
        return AutoModelForTokenClassification.from_pretrained(
            base_model,
            num_labels=len(LABEL2ID),
            id2label=ID2LABEL,
            label2id=LABEL2ID,
            ignore_mismatched_sizes=True,
        )

    # 3) remap problematic keys and drop task-specific heads
    remapped = {}
    for k, v in state_dict.items():
        nk = k.replace("LayerNorm.gamma", "LayerNorm.weight").replace("LayerNorm.beta", "LayerNorm.bias")

        # Drop pretraining heads and old classifier head; keep encoder weights.
        if nk.startswith("lm_predictions.") or nk.startswith("mask_predictions."):
            continue
        if nk.startswith("classifier."):
            continue

        remapped[nk] = v

    missing, unexpected = model.load_state_dict(remapped, strict=False)
    ln_missing = [k for k in missing if "LayerNorm.weight" in k or "LayerNorm.bias" in k]
    print(f"  DeBERTa remap load → missing:{len(missing)} unexpected:{len(unexpected)}")
    if ln_missing:
        print(f"  Warning: still missing LayerNorm params: {len(ln_missing)}")

    return model


# ── per-model configuration ──────────────────────────────────────────────────

MODEL_CONFIGS = {
    "deberta": {
        "base_model":    "microsoft/deberta-v3-base",
        "output_dir":    "scripts/detectors/deberta_ner_model",
        "learning_rate": 3e-5,
        "note":          "requires sentencepiece — pip install sentencepiece",
    },
    "bert": {
        "base_model":    "dslim/bert-base-NER",
        "output_dir":    "scripts/detectors/bert_ner_model",
        "learning_rate": 2e-5,
        "note":          None,
    },
}

LABEL2ID     = {"O": 0, "B-PERSON": 1, "I-PERSON": 2}
ID2LABEL     = {v: k for k, v in LABEL2ID.items()}
MAX_LENGTH   = 512
STRIDE       = 64
IGNORE_INDEX = -100


# ── data helpers ─────────────────────────────────────────────────────────────

def load_examples(notes_dir: str, annotations_path: str):
    """Return list of {text, person_spans} dicts (one per note)."""
    with open(annotations_path, encoding="utf-8") as f:
        annotations = json.load(f)

    ann_map    = {doc["doc_id"]: doc["entities"] for doc in annotations}
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


def _align_labels(offsets, person_spans, word_ids=None):
    """
    Map token offsets to BIO label ids. Special tokens -> IGNORE_INDEX.

    word_ids: list returned by enc.word_ids(batch_index=i).
      None entries = special/padding tokens.
      Preferred over offset check because DeBERTa's SentencePiece tokenizer
      can assign (0, 0) offsets to valid continuation subwords, causing them
      to be silently skipped if we rely on tok_start == tok_end alone.
    """
    labels = []
    prev_in_person = False

    for i, (tok_start, tok_end) in enumerate(offsets):
        # Prefer word_ids-based check; fall back to offset check for BERT compat.
        is_special = (word_ids[i] is None) if word_ids is not None \
                     else (tok_start == tok_end)

        if is_special:
            labels.append(IGNORE_INDEX)
            prev_in_person = False
            continue

        # Offset-based overlap check (more robust than full containment for subwords):
        # token overlaps a PERSON span iff tok_start < pe and tok_end > ps.
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
            offsets  = enc["offset_mapping"][chunk_idx]
            word_ids = enc.word_ids(batch_index=chunk_idx)  # None = special token
            labels   = _align_labels(offsets, ex["person_spans"], word_ids)
            all_samples.append({
                "input_ids":      enc["input_ids"][chunk_idx],
                "attention_mask": enc["attention_mask"][chunk_idx],
                "labels":         labels,
            })

    return all_samples


# ── metrics ──────────────────────────────────────────────────────────────────

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
    parser = argparse.ArgumentParser(
        description="Fine-tune a transformer NER model for PERSON detection."
    )
    parser.add_argument(
        "--model",
        choices=list(MODEL_CONFIGS),
        default="deberta",
        help="Model to fine-tune: deberta (default) or bert",
    )
    parser.add_argument("--notes-dir",     default="data/synthetic/raw")
    parser.add_argument("--annotations",   default="data/annotated/annotations_generated.json")
    parser.add_argument("--output-dir",    default=None,
                        help="Override default output directory")
    parser.add_argument("--epochs",        type=int,   default=4)
    parser.add_argument("--batch-size",    type=int,   default=8)
    parser.add_argument("--learning-rate", type=float, default=None,
                        help="Override default LR for the selected model")
    parser.add_argument("--val-split",     type=float, default=0.1,
                        help="Fraction of non-test notes held out for validation during training")
    parser.add_argument("--test-split",    type=float, default=0.1,
                        help="Fraction of notes held out as a final test set (never trained on)")
    parser.add_argument("--test-ids-out",  default="data/annotated/test_ids.json",
                        help="Where to save the held-out test note IDs")
    parser.add_argument("--seed",          type=int,   default=42)
    parser.add_argument(
        "--patience",
        type=int,
        default=None,
        help="Early-stopping patience (epochs without val-F1 improvement). "
             "Default: 2 for DeBERTa, 3 for BERT.",
    )
    args = parser.parse_args()

    cfg = MODEL_CONFIGS[args.model]
    base_model  = cfg["base_model"]
    output_dir  = args.output_dir or cfg["output_dir"]
    lr          = args.learning_rate or cfg["learning_rate"]
    patience    = args.patience if args.patience is not None else (2 if args.model == "deberta" else 3)

    set_seed(args.seed)

    model_label = args.model.upper()
    print(f"\n{'='*80}")
    print(f"{model_label} NER FINE-TUNING  —  PERSON entity detection")
    print(f"{'='*80}\n")
    print(f"  Model       : {args.model}  ({base_model})")
    if cfg["note"]:
        print(f"  Note        : {cfg['note']}")
    print(f"  Notes dir   : {args.notes_dir}")
    print(f"  Annotations : {args.annotations}")
    print(f"  Output dir  : {output_dir}")
    print(f"  Epochs      : {args.epochs}")
    print(f"  Batch size  : {args.batch_size}")
    print(f"  LR          : {lr}\n")

    # ── load data ────────────────────────────────────────────────────────────
    print("Loading notes and annotations...")
    examples = load_examples(args.notes_dir, args.annotations)
    print(f"  {len(examples)} notes loaded")

    # 3-way split: test (never trained on) -> val (early stopping) -> train
    rng        = np.random.default_rng(args.seed)
    indices    = rng.permutation(len(examples))
    test_size  = max(1, int(len(examples) * args.test_split))
    val_size   = max(1, int(len(examples) * args.val_split))
    test_idx   = set(indices[:test_size].tolist())
    val_idx    = set(indices[test_size:test_size + val_size].tolist())
    train_ex   = [ex for i, ex in enumerate(examples) if i not in test_idx and i not in val_idx]
    val_ex     = [ex for i, ex in enumerate(examples) if i in val_idx]
    test_ex    = [ex for i, ex in enumerate(examples) if i in test_idx]

    # Save test note IDs (1-based, matching doc_id in annotations) so
    # run_phi_detection.py and run_evaluation_fixed.py can restrict to test-only.
    # The note at position i in the sorted file list has doc_id = i+1.
    note_files = sorted(Path(args.notes_dir).glob("*.txt"))
    test_note_ids = sorted([
        int(note_files[i].stem.split("_")[1])   # e.g. note_0001_... -> 1
        for i in test_idx
        if i < len(note_files)
    ])
    os.makedirs(os.path.dirname(args.test_ids_out) or ".", exist_ok=True)
    with open(args.test_ids_out, "w") as f:
        json.dump(test_note_ids, f)

    print(f"  Train: {len(train_ex)}   Val: {len(val_ex)}   Test (held-out): {len(test_ex)}")
    print(f"  Test IDs saved to: {args.test_ids_out}\n")

    # ── tokenizer ────────────────────────────────────────────────────────────
    print(f"Loading tokenizer from {base_model}...")
    tokenizer = AutoTokenizer.from_pretrained(base_model)

    print("Tokenizing training data...")
    train_samples = tokenize_dataset(train_ex, tokenizer)
    val_samples   = tokenize_dataset(val_ex,   tokenizer)
    print(f"  Train chunks: {len(train_samples)}   Val chunks: {len(val_samples)}\n")

    # Compute data-driven class weights using the full balanced formula.
    # Applying it to ALL classes (including O) keeps the relative ratios correct —
    # w_o comes out ~0.34 which makes the B/O effective ratio match the true
    # class imbalance (~65x), giving PERSON tokens ~60% of the gradient signal.
    if args.model == "deberta":
        from collections import Counter
        all_labels = [l for s in train_samples for l in s["labels"] if l != IGNORE_INDEX]
        cnt   = Counter(all_labels)
        total = sum(cnt.values())
        n_cls = len(LABEL2ID)
        w_o   = total / (n_cls * max(cnt[0], 1))
        w_b   = total / (n_cls * max(cnt[1], 1))
        w_i   = total / (n_cls * max(cnt[2], 1))
        print(f"  Class counts  → O:{cnt[0]:,}  B-PERSON:{cnt[1]:,}  I-PERSON:{cnt[2]:,}  (PERSON%={(cnt[1]+cnt[2])/total:.1%})")
        print(f"  Auto weights  → O:{w_o:.2f}  B-PERSON:{w_b:.1f}  I-PERSON:{w_i:.1f}\n")
        _deberta_weights = [w_o, w_b, w_i]
    else:
        _deberta_weights = None

    train_dataset = Dataset.from_list(train_samples)
    val_dataset   = Dataset.from_list(val_samples)

    # ── model ─────────────────────────────────────────────────────────────────
    print(f"Loading model from {base_model}...")
    if args.model == "deberta":
        model = _load_deberta_checkpoint_with_key_remap(base_model)
    else:
        model = AutoModelForTokenClassification.from_pretrained(
            base_model,
            num_labels=len(LABEL2ID),
            id2label=ID2LABEL,
            label2id=LABEL2ID,
            ignore_mismatched_sizes=True,
        )

    # DeBERTa-v3 checkpoints saved with older transformers use gamma/beta for
    # LayerNorm; newer transformers expects weight/bias.  Fix in-place so
    # pre-trained normalisation weights are not randomly re-initialised.
    if args.model == "deberta":
        fix_deberta_layernorm(model)

    data_collator = DataCollatorForTokenClassification(tokenizer, pad_to_multiple_of=8)

    steps_per_epoch = max(1, len(train_dataset) // args.batch_size)
    warmup_steps    = max(1, int(steps_per_epoch * args.epochs * 0.1))

    if args.model == "deberta":
        use_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
        use_fp16 = False  # DeBERTa-v3 cannot train with fp16
    else:
        use_bf16 = False
        use_fp16 = torch.cuda.is_available()

    # ── training ─────────────────────────────────────────────────────────────
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size * 2,
        learning_rate=lr,
        weight_decay=0.01,
        warmup_steps=warmup_steps,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        logging_steps=50,
        fp16=use_fp16,
        bf16=use_bf16,
        seed=args.seed,
        report_to="none",
    )

    # Use class-weighted loss for DeBERTa to overcome class imbalance:
    # ~95% O tokens causes the model to collapse to all-O with standard CE.
    # BERT avoids this because dslim/bert-base-NER already knows PERSON.
    TrainerClass = WeightedCETrainer if args.model == "deberta" else Trainer

    callbacks = [
        EarlyStoppingCallback(early_stopping_patience=patience),
        NaNStoppingCallback(spike_factor=5.0),
    ]

    trainer_kwargs = dict(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        callbacks=callbacks,
    )
    if args.model == "deberta":
        trainer_kwargs["class_weights"] = _deberta_weights

    trainer = TrainerClass(**trainer_kwargs)

    precision = "bf16" if use_bf16 else "fp16" if use_fp16 else "fp32"
    print(f"  Mixed precision : {precision}")
    print(f"  Trainer class   : {TrainerClass.__name__}")
    print(f"  Early stopping  : patience={patience} epochs (val F1)")
    print(f"  NaN guard       : stops on NaN loss or >5× spike")
    print("Starting training...\n")
    trainer.train()

    # ── save ──────────────────────────────────────────────────────────────────
    print(f"\nSaving model to {output_dir} ...")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    label_map_path = Path(output_dir) / "label_map.json"
    with open(label_map_path, "w") as f:
        json.dump({"label2id": LABEL2ID, "id2label": ID2LABEL}, f, indent=2)

    print(f"\n{'='*80}")
    print("Training complete!")
    print(f"{'='*80}")
    print(f"\nModel saved to: {output_dir}")
    print("\nNext step (evaluate on held-out test notes only):")
    print(f"  python scripts/run_phi_detection.py --detector {args.model} --test-ids {args.test_ids_out}")
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
