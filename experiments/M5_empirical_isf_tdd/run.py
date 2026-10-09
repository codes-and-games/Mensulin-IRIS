"""M5: empirical ISF x TDD (and ln-ln slope) on public data where pump ISF settings exist. ISF is a clinician-set parameter, NOT physiological sensitivity;
without such data the glucose-equivalent analysis stays model-conditional (BLOCKED here, infrastructure preserved)."""
import pandas as pd

from iris.common.provenance import EvidenceClass
from iris.evaluate.isf_tdd import isf_tdd_fit
from iris.tools import experiment_lib as xl


def run(ctx):
    raw, prov = xl.load_person_day(ctx, with_cycle_labels=False)
    res = isf_tdd_fit(raw)
    ctx.save_table(pd.DataFrame([res]), "isf_tdd_fit", [xl.derived_prov(ctx, prov[:1], EvidenceClass.COMPUTED, "isf_tdd_fit", "ln ISF ~ ln TDD (HC3)", "iris.evaluate.isf_tdd")])
