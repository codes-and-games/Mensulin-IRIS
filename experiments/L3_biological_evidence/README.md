# L3_biological_evidence

| Field | Content |
| --- | --- |
| Purpose | Maintain the biological parameter sheet with verification status. |
| Hypothesis | n/a |
| Inputs | literature/biological_evidence.csv (PUBLISHED, S1). |
| Source / evidence class | COMPUTED |
| Procedure | Tabulate; flag unresolved and unverified parameters. |
| Variables | parameter |
| Controls | unresolved parameters never receive values |
| Metrics | usable_production/usable_provisional flags |
| Expected outputs | parameter_sheet |
| Interpretation | Values transcribed from the project document remain PENDING_VERIFY until a second reader checks the primary source. |
| Failure conditions | value used in production without verification |

Run: `python -m iris.tools.run_experiment L3_biological_evidence [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
