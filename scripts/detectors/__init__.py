from .base_detector import PHIDetector
from .spacy_regex_detector import SpacyRegexDetector
from .presidio_detector import PresidioDetector

# BertDetector, DebertaDetector, and EnsembleDetector are imported lazily inside
# create_detector() so that missing torch/transformers doesn't break spacy_regex
# and presidio.

DETECTOR_CHOICES = {
    "spacy_regex": SpacyRegexDetector,
    "presidio":    PresidioDetector,
    # bert, deberta, and ensemble resolved lazily below
}


def create_detector(name: str, ensemble_model: str = "bert") -> PHIDetector:
    """
    Instantiate a detector by key.

    Available detectors
    -------------------
    spacy_regex  — spaCy NER (PERSON) + project regex          [default]
    presidio     — Microsoft Presidio + regex CREDENTIAL
    bert         — Fine-tuned BERT (PERSON) + regex             [train first]
    deberta      — Fine-tuned DeBERTa-v3 (PERSON) + regex      [train first]
    ensemble     — spaCy + Presidio + transformer(s) for PERSON + regex
                   ensemble_model: "bert" | "deberta" | "both"
    """
    key = (name or "spacy_regex").lower().strip()

    if key == "bert":
        from .bert_detector import BertDetector
        return BertDetector()

    if key == "deberta":
        from .deberta_detector import DebertaDetector
        return DebertaDetector()

    if key == "ensemble":
        from .ensemble_detector import EnsembleDetector
        return EnsembleDetector(transformer=ensemble_model)

    if key not in DETECTOR_CHOICES:
        raise ValueError(
            f"Unknown detector {name!r}. "
            f"Choose from: spacy_regex | presidio | bert | deberta | ensemble"
        )

    return DETECTOR_CHOICES[key]()


__all__ = [
    "PHIDetector",
    "SpacyRegexDetector",
    "PresidioDetector",
    "DETECTOR_CHOICES",
    "create_detector",
]
