"""Abstract base for PHI detectors used by run_phi_detection.py."""

from abc import ABC, abstractmethod


class PHIDetector(ABC):
    """Each detector returns entity dicts with at least text, type, start, end."""

    @abstractmethod
    def detect(self, text):
        """
        Args:
            text: Full note text.

        Returns:
            list[dict]: Each dict has "text", "type", "start", "end".
            Implementations may add optional keys (e.g. "score").
        """
        raise NotImplementedError
