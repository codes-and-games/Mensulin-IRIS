"""Scientific-claims lint: flags prohibited / misleading phrases in generated outputs.

IRIS-generated evidence is SIMULATED/COMPUTED/PROJECTED. It must never be described as
measured, observed in patients/participants, clinically safe, or as dosing advice.
Attribution of a measurement to an external source ("Smith et al. measured ...") is allowed
when the line also carries a citation marker (see ATTRIBUTION_MARKERS).
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from iris.common.exceptions import ClaimsViolation

PROHIBITED = {
    r"\bwe measured\b": "IRIS measures nothing; use 'computed from' / 'the model projects'",
    r"\bwe observed\b": "no observations are made by IRIS; use 'in simulation'",
    r"\bour (patients|participants|subjects)\b": "IRIS has no patients/participants/subjects; use 'virtual individuals'",
    r"\bpatients in the simulation\b": "use 'virtual individuals'",
    r"\bclinically safe\b": "IRIS makes no safety verdicts",
    r"\bsafe to use\b": "IRIS makes no safe-to-use verdicts",
    r"\brecommended dose\b": "IRIS never recommends doses",
    r"\bdose adjustment\b": "IRIS never recommends dose changes",
    r"\bincrease (your|the) (insulin )?dose\b": "IRIS never recommends dose changes",
    r"\breal-world risk\b": "outputs are PROJECTED, not real-world risk",
    r"\bwe (found|showed|discovered)\b": "fusion outputs are PROJECTED; avoid 'found/showed/discovered'",
    r"\bMEASURED\b": "MEASURED is not an IRIS evidence class",
}
ATTRIBUTION_MARKERS = ("et al", "[cite", "(cited)", "published", "reported by", "source:")
ENCOURAGED = ["the model projects", "in simulation", "published evidence reports", "computed from",
              "under the declared assumptions", "within the evaluated parameter set"]


@dataclass(frozen=True)
class Finding:
    line_no: int
    phrase: str
    advice: str
    text: str


def lint_text(text: str) -> list[Finding]:
    out: list[Finding] = []
    for i, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        # explicit opt-out used in documentation that quotes prohibited phrases
        if "claims-lint: ignore" in low:
            continue
        for pat, advice in PROHIBITED.items():
            flags = 0 if pat == r"\bMEASURED\b" else re.IGNORECASE
            m = re.search(pat, line, flags)
            if not m:
                continue
            if any(mark in low for mark in ATTRIBUTION_MARKERS):
                continue  # attributed to an external source
            out.append(Finding(i, m.group(0), advice, line.strip()))
    return out


def assert_clean(text: str, where: str = "text") -> None:
    f = lint_text(text)
    if f:
        detail = "; ".join(f"line {x.line_no}: '{x.phrase}' ({x.advice})" for x in f[:5])
        raise ClaimsViolation(f"claims lint failed for {where}: {detail}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    args = ap.parse_args(argv)
    bad = 0
    for fn in args.files:
        p = Path(fn)
        if not p.is_file():
            continue
        for f in lint_text(p.read_text(errors="ignore")):
            print(f"{fn}:{f.line_no}: '{f.phrase}' -> {f.advice}")
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
