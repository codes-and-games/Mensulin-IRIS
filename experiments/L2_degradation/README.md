# L2_degradation

| Field | Content |
| --- | --- |
| Purpose | Extract insulin degradation data, fit kinetics, evaluate leave-one-study-out. |
| Hypothesis | Kinetics are identifiable for at least some comparable studies. |
| Inputs | literature/degradation_literature.csv (PUBLISHED; verified rows only in production). |
| Source / evidence class | COMPUTED |
| Procedure | Per-study K1 posterior; LOSO prediction; model-set weights; identifiability diagnostics. |
| Variables | study, product, formulation |
| Controls | unlike products never pooled |
| Metrics | LOSO MAE, 95% coverage, corr(lnk,Ea) |
| Expected outputs | fit_diagnostics, loso_predictions, loso_summary, ensemble_weights |
| Interpretation | Fewer than 5 comparable studies: between-study variance is NOT estimable; model set is analyst-defined. |
| Failure conditions | pooled unlike products; unverified rows in production |

Run: `python -m iris.tools.run_experiment L2_degradation [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
