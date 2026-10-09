"""Run logging with evidence-class counters."""
from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path


class RunLogger:
    def __init__(self, path: str | Path | None = None, name: str = "iris"):
        self.logger = logging.getLogger(f"{name}.{id(self)}")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        self.records: list[tuple[str, str]] = []
        self.evidence_counts: Counter = Counter()
        self.warnings: list[str] = []
        self.exclusions: list[str] = []
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(path)
            fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            self.logger.addHandler(fh)

    def info(self, msg: str):
        self.records.append(("INFO", msg)); self.logger.info(msg)

    def warn(self, msg: str):
        self.warnings.append(msg); self.records.append(("WARNING", msg)); self.logger.warning(msg)

    def exclude(self, msg: str):
        self.exclusions.append(msg); self.records.append(("EXCLUSION", msg)); self.logger.info("EXCLUSION " + msg)

    def count_evidence(self, evidence_class: str, n: int = 1):
        self.evidence_counts[str(evidence_class)] += n

    def close(self):
        for h in list(self.logger.handlers):
            h.close(); self.logger.removeHandler(h)
