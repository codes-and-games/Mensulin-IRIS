# 0001 - Scenario design parameters not given numerically in the document

Status: **OPEN - research-owner confirmation requested.** Work continues with the declared values; every output lists them as assumptions.

BLOCKED SCIENTIFIC DECISION (not blocking other work):
the document defines S0, S6 and S7 qualitatively. Four design parameters have no numeric value in the document and are
declared `status: ASSUMPTION` in `configs/fusion/scenarios.yaml`:
- S0 thermostat cycling period (1 h), S4 hour of daily maximum (15:00), S6 episodes per week (3), S7 start of the transport window (24 h).

WHY IT MATTERS: they shape exposure histories (S6, S7 especially). OPTIONS: A. confirm/replace the values and record the source;
B. sweep them in R2 (supported by config). CURRENT RECOMMENDATION: B until a source is extracted.

## Resolution (2026-10-07, technical lead, by delegation from the research owner)
Option B adopted: the four design parameters stay declared `ASSUMPTION` (not evidence) and are **swept in R2**; no value is presented as sourced. If a primary source is later extracted, option A replaces the value with its citation. Reversible.
