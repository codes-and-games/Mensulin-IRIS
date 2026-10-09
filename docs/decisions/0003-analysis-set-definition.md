# 0003 - Operational definition of Theta_E and Theta_S

Status: **OPEN - confirm.** Theta_E holds each component at an evidence-supported level; where a component has no evidence-supported level it is held at a declared REFERENCE level and listed in `conditioned_on`, so every Theta_E conclusion is reported as conditional on those references. Theta_S frees all components over analyst-defined stress levels. Today almost every component has no evidence level (the document marks the tails, eta, dependence as unidentified), so Theta_E is a narrow set and its conclusions are explicitly conditional. The two sets are never pooled (`assert_single_set`).
Analyst-defined stress levels (eta grid, heterogeneity multipliers, R_B strength 0.5, mixture shift 3 SD, st grid, r_PB grid) are STRESS_TEST, never evidence.

## Resolution (2026-10-07, technical lead, by delegation)
Confirmed as written. Rationale: conditional reporting with declared reference levels is the honest treatment while most components are unidentified, and never pooling Theta_E with Theta_S prevents stress levels from being read as evidence. Reversible.
