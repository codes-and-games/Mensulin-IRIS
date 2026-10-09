"""L1: novelty and evidence search. The search itself is human work recorded in literature/novelty_search_log.csv; this run validates the log, builds
the near-neighbour table, and FORCES a narrower novelty claim when a close prior study is logged. An empty log => BLOCKED (novelty not assessed)."""
import pandas as pd

from iris.common.exceptions import ScientificBlocker
from iris.common.provenance import EvidenceClass, Provenance
from iris.tools import experiment_lib as xl

COLS = ["date", "database", "query", "n_results", "screened", "closest_prior_study", "closeness", "notes", "searched_by"]


def run(ctx):
    p = xl.repo(ctx) / "literature/novelty_search_log.csv"
    df = pd.read_csv(p) if p.exists() else pd.DataFrame(columns=COLS)
    miss = [c for c in COLS if c not in df.columns]
    if miss:
        raise ScientificBlocker("novelty_search_log", f"columns missing {miss}", "use the documented schema")
    if df.empty:
        raise ScientificBlocker("novelty_search_log", "no searches logged: novelty has NOT been assessed", "perform and log the searches (database, query, date, result counts)")
    prov = Provenance(EvidenceClass.COMPUTED, "novelty_search_log", transformation="tabulate logged searches", generated_by="experiments.L1", run_id=ctx.run_id)
    close = df[df["closeness"].astype(str).str.lower().isin(["close", "very close", "near-identical"])]
    ctx.save_table(df, "search_log", [prov]); ctx.save_table(close, "near_neighbours", [prov])
    if len(close):
        ctx.log.warn(f"{len(close)} close prior study(ies) logged: the novelty claim MUST be narrowed; novelty is not assumed")
