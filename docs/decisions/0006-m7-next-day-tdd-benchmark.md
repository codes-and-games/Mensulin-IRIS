# D-22: M7 next-day TDD benchmark (first supervised ML on real data)

## Decision

Start supervised ML with a **non-cycle** target that the two registered open datasets can support: next-day observed total daily dose (TDD), predicted from information available before the day starts. Cycle estimation (M2/M3) stays blocked until a source supplies cycle labels.

## Rules fixed before any real M7 run

- Target: TDD(t) divided by the mean TDD of the previous 7 calendar days (at least 3 valid days); scored back in units/day.
- Features: past-only (`shift(1)` on a complete per-person calendar; a missing day stays missing) plus `is_weekend` of the target date. Same-day glucose summaries are never used. No cycle fields.
- A day's TDD is usable only if the day is included by ingest QC, TDD is finite and TDD > 0. TDD = 0 is treated as insulin not recorded (raw HUPA-UCM files for HUPA0011P, HUPA0015P, HUPA0018P have basal = bolus = 0 on every row while carbohydrates are recorded). Raw files are untouched; exclusions are counted in `cohort_flow` and the run log.
- Evaluation: participant-disjoint only. LeaveOneGroupOut is primary, GroupKFold(5) secondary. Fixed hyperparameters, no tuning.
- Baselines: M0 training mean, P1 persistence (yesterday), P7 trailing 7-day mean.
- Verdict: an ML model beats the better of P1/P7 only if the 95% person-clustered bootstrap CI of pooled-MAE skill is entirely above 0 **and** point skill >= 2% (`min_skill`, an ASSUMPTION declared here, not tuned).
- Controls: within-person shuffled-target placebo must show no skill (otherwise `FAILED_CONTROL`); feature audit drops any feature missing in more than 50% of eligible rows of any dataset.

## Interpretation limits

Run mode is provisional (S15/S17 sign-off open; timezone and end-of-interval semantics unverified). TDD under automated insulin delivery reflects controller behaviour as well as physiology. A model that does not beat a trailing mean is a reportable result. Nothing here supports a menstrual-cycle or thermal claim.
