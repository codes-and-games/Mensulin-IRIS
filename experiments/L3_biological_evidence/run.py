"""L3: biological-evidence extraction table -> parameter sheet. Rows copied from the project document are status UNVERIFIED until a second reader checks the
primary source. The sheet lists which parameters are usable in which mode."""
import pandas as pd

from iris.common.exceptions import ScientificBlocker
from iris.common.provenance import EvidenceClass
from iris.tools import experiment_lib as xl

COLS = ["parameter", "value", "ci_low", "ci_high", "unit", "source_id", "page_table_ref", "population", "extracted_by", "verified_by", "status"]


def run(ctx):
    p = xl.repo(ctx) / "literature/biological_evidence.csv"
    if not p.exists():
        raise ScientificBlocker("biological_evidence", "table missing", "extract parameters with page/table references")
    df = pd.read_csv(p)
    miss = [c for c in COLS if c not in df.columns]
    if miss:
        raise ScientificBlocker("biological_evidence", f"columns missing {miss}", "use the documented schema")
    df["usable_production"] = df["verified_by"].notna() & (df["verified_by"].astype(str).str.strip() != "") & df["value"].notna()
    df["usable_provisional"] = df["value"].notna()
    df["unresolved"] = df["value"].isna()
    base = xl.source_prov(ctx, "S1") if ctx.mode.value != "test" else None
    from iris.common.provenance import Provenance
    prov = base.derive(evidence_class=EvidenceClass.COMPUTED, source_id="parameter_sheet", transformation="biological_evidence.csv status table", generated_by="experiments.L3", run_id=ctx.run_id) if base else \
        Provenance(EvidenceClass.COMPUTED, "parameter_sheet", generated_by="experiments.L3", run_id=ctx.run_id)
    ctx.save_table(df, "parameter_sheet", [prov])
    if not df["usable_production"].any():
        ctx.blockers.append(dict(part="production", reason="no biological parameter has a second-reader verification yet"))
