"""L4: ISF-TDD relationship analysis. Same analysis as M5 under the literature-evidence framing; treat pump settings as clinician-set parameters.
If the necessary data are unavailable the infrastructure is preserved and the glucose-equivalent analysis stays model-conditional."""
import pandas as pd

from iris.common.provenance import EvidenceClass
from iris.evaluate.isf_tdd import isf_tdd_fit
from iris.tools import experiment_lib as xl


def run(ctx):
    raw, prov = xl.load_person_day(ctx, with_cycle_labels=False)
    res = isf_tdd_fit(raw)
    res["decision"] = "slope CI includes -1: ISF∝1/TDD not rejected as a SETTINGS rule" if res["consistent_with_minus_one"] else "slope CI excludes -1: settings do not follow ISF∝1/TDD in this data"
    ctx.save_table(pd.DataFrame([res]), "isf_tdd_between_person", [xl.derived_prov(ctx, prov[:1], EvidenceClass.COMPUTED, "isf_tdd_between_person", "between-person ln-ln fit", "iris.evaluate.isf_tdd")])
