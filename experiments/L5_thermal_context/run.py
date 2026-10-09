"""L5: thermal-context parameter extraction table -> validated parameter sheet. Every extracted parameter needs source_id, citation, page/table, conditions, units."""
import pandas as pd

from iris.common.exceptions import ScientificBlocker
from iris.common.provenance import EvidenceClass, Provenance
from iris.tools import experiment_lib as xl

COLS = ["parameter", "context_id", "value", "unit", "source_id", "citation", "page_table_ref", "conditions", "extracted_by", "verified_by"]


def run(ctx):
    p = xl.repo(ctx) / "literature/thermal_context_parameters.csv"
    df = pd.read_csv(p) if p.exists() else pd.DataFrame(columns=COLS)
    if df.empty:
        raise ScientificBlocker("thermal_context_parameters", "no extracted context parameters", "extract C0-C5 parameters with source/page/conditions/units")
    bad = df[df[["source_id", "citation", "page_table_ref", "conditions", "unit"]].isna().any(axis=1)]
    ctx.save_table(df, "context_parameters", [Provenance(EvidenceClass.COMPUTED, "context_parameter_sheet", generated_by="experiments.L5", run_id=ctx.run_id)])
    if len(bad):
        ctx.log.warn(f"{len(bad)} extracted rows are missing source/citation/page/conditions/units and must not be used")
