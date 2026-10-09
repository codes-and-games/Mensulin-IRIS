# 0002 - How stored potency draws are assigned to virtual individuals

Status: **OPEN - interpretation to be confirmed by the research owner.**

Implemented (iris.fusion.mc_engine): two explicit modes, recorded in every output.
- `shared`: individuals share the epistemic draw's potency (thermal uncertainty stays epistemic; the algebraic baseline equals the observed concentration exactly, so excess concentration is identically zero).
- `coupled`: individuals receive losses from the scenario's pooled draw distribution through a Gaussian copula with correlation r_PB to a rank-based biological score. r_PB = 0 is independent assignment. Here thermal variation is treated as BETWEEN-individual variation.
The theta evaluator (F5/F6/R*) always uses `coupled` so that r_PB acts.

BLOCKED SCIENTIFIC DECISION: is treating the pooled potency distribution as between-individual variation a legitimate reading of "thermal exposure varies across individuals' storage situations"?
OPTIONS: A. keep (current); B. restrict to scenarios whose histories are stochastic across individuals (S5, S6, S7) and hold deterministic scenarios in `shared` mode.
CURRENT RECOMMENDATION: B once S5 is unblocked. WORK THAT CAN CONTINUE: everything.

## Resolution (2026-10-07, technical lead, by delegation)
Option B is adopted **as the target design**: the pooled potency distribution mainly encodes *epistemic* uncertainty about kinetics, so treating it as between-individual variation is legitimate only for scenarios whose histories genuinely differ across individuals (S5, S6, S7). Deterministic scenarios should be evaluated in `shared` mode. **Not yet implemented:** the theta evaluator (F5/F6/R*) currently always uses `coupled`. Until that change is made and tested (task T-01, below), every F5/F6/R* result for deterministic scenarios must be labelled "between-individual reading (option A), conditional" and must not be used as a confirmatory conclusion about those scenarios.
