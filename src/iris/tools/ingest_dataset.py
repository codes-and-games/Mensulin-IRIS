"""python -m iris.tools.ingest_dataset <dataset> [--mode provisional|production] [--combine]
Ingests data/raw/<dataset>/ with configs/mappings/<dataset>.yaml -> data/processed/<dataset>/{events_grid,person_day}.parquet.
--combine rebuilds data/processed/person_day.parquet (the table every M/L experiment reads)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from iris.common.exceptions import ScientificBlocker
from iris.ingest.pipeline import combine_person_day, ingest_dataset

ROOT = Path(__file__).resolve().parents[3]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset"); ap.add_argument("--mode", default="provisional", choices=["provisional", "production"])
    ap.add_argument("--combine", action="store_true"); ap.add_argument("--root", default=str(ROOT))
    a = ap.parse_args(argv)
    try:
        rep = ingest_dataset(a.root, Path(a.root) / "configs/mappings" / f"{a.dataset}.yaml", a.mode)
        print(json.dumps(rep, indent=2))
        if a.combine:
            print("combined ->", combine_person_day(a.root, mode=a.mode))
    except ScientificBlocker as exc:
        print(f"BLOCKED: {exc}")
        return 3
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
