"""make figures: draw figures for the latest run of each experiment from STORED tables; then write the data book."""
from __future__ import annotations

import sys
from pathlib import Path

from iris.common.exceptions import IrisError
from iris.report.databook import write_databook
from iris.report.figures import FIGURE_FUNCS

ROOT = Path(__file__).resolve().parents[3]


def main(argv=None) -> int:
    runs = sorted((ROOT / "results/runs").glob("*"))
    made = 0
    for d in runs:
        for table, fn in FIGURE_FUNCS.items():
            if (d / "tables" / f"{table}.parquet").exists() and not (d / "figures" / f"{fn.__name__ if fn.__name__ != 'sweep_plot' else 'dependence_sweeps'}.png").exists():
                try:
                    fn(d); made += 1
                except IrisError as exc:
                    print(f"[skip] {d.name}: {fn.__name__}: {exc}")
    print(f"made {made} figures; data book: {write_databook(ROOT)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
